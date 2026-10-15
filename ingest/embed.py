"""Embed chunks (and eval queries) with the profile's embedding model, cached by content.

Two input formats, verified live on 2026-10-15 (ADR-015):

- `instruction` (gemini-embedding-2): the task hint is part of the text,
  `title: <header> | text: <chunk>` for documents and
  `task: search result | query: <q>` for queries. The model ignores
  `task_type`, and a request with several texts returns ONE fused vector, so
  every text is its own request.
- `task_type` (gemini-embedding-001): RETRIEVAL_DOCUMENT (with `title`) /
  RETRIEVAL_QUERY, and a request may carry many texts.

Vectors are requested at the model's full size (3072) and stored L2-normalised;
smaller sizes are Matryoshka truncations made at index time. The cache key
covers model, input format, kind, title and text, so a rebuild re-embeds only
what changed.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import sqlite3
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
from google import genai
from google.genai import errors, types

log = logging.getLogger(__name__)

CACHE_PATH = Path("data/embed_cache.sqlite")
DOC_TEMPLATE = "title: {title} | text: {text}"
QUERY_TEMPLATE = "task: search result | query: {text}"
RETRYABLE = {408, 429, 500, 502, 503, 504}

Kind = Literal["document", "query"]


@dataclass(frozen=True)
class EmbedInput:
    kind: Kind
    text: str
    title: str | None = None  # contextual header (documents only)


@dataclass(frozen=True)
class Request:
    """What goes over the wire for one input."""

    content: str
    task_type: str | None
    title: str | None


def to_request(item: EmbedInput, input_format: str) -> Request:
    if input_format == "instruction":
        if item.kind == "query":
            return Request(QUERY_TEMPLATE.format(text=item.text), None, None)
        return Request(DOC_TEMPLATE.format(title=item.title or "none", text=item.text), None, None)
    if input_format == "task_type":
        if item.kind == "query":
            return Request(item.text, "RETRIEVAL_QUERY", None)
        return Request(item.text, "RETRIEVAL_DOCUMENT", item.title)
    raise ValueError(f"unknown input_format {input_format!r}")


def cache_key(model: str, input_format: str, item: EmbedInput) -> str:
    raw = json.dumps([model, input_format, item.kind, item.title, item.text], ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def normalize(m: np.ndarray) -> np.ndarray:
    m = np.asarray(m, dtype=np.float32)
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(norms == 0, 1, norms)


def truncate(m: np.ndarray, dims: int) -> np.ndarray:
    """Matryoshka truncation: keep the first `dims` components, re-normalise."""
    return normalize(m[..., :dims])


class EmbedCache:
    """key -> float32 vector, in a local SQLite file (gitignored under data/)."""

    def __init__(self, path: Path = CACHE_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS vec (key TEXT PRIMARY KEY, model TEXT, tokens INTEGER, "
            "vec BLOB NOT NULL)"
        )

    def get_many(self, keys: Sequence[str]) -> dict[str, np.ndarray]:
        out: dict[str, np.ndarray] = {}
        for i in range(0, len(keys), 900):  # SQLite parameter limit
            batch = keys[i : i + 900]
            rows = self.db.execute(
                f"SELECT key, vec FROM vec WHERE key IN ({','.join('?' * len(batch))})",  # noqa: S608
                batch,
            )
            out.update({k: np.frombuffer(v, dtype=np.float32) for k, v in rows})
        return out

    def put_many(self, rows: Sequence[tuple[str, str, int | None, np.ndarray]]) -> None:
        self.db.executemany(
            "INSERT OR REPLACE INTO vec VALUES (?, ?, ?, ?)",
            [(k, m, t, np.asarray(v, dtype=np.float32).tobytes()) for k, m, t, v in rows],
        )
        self.db.commit()


@dataclass
class Usage:
    requests: int = 0
    embedded: int = 0
    cached: int = 0
    tokens: int = 0
    retries: int = 0
    seconds: float = 0.0
    errors: list[str] = field(default_factory=list)


class Embedder:
    def __init__(
        self,
        model: str,
        location: str,
        input_format: str,
        project: str,
        cache: EmbedCache | None = None,
        concurrency: int = 16,
        batch_size: int = 50,
    ) -> None:
        if input_format not in ("instruction", "task_type"):
            raise ValueError(f"unknown input_format {input_format!r}")
        self.model, self.location, self.input_format = model, location, input_format
        # Keep the client referenced: it closes its HTTP session when collected.
        self.client = genai.Client(vertexai=True, project=project, location=location)
        self.cache = cache
        self.concurrency = concurrency
        # gemini-embedding-2 fuses multi-text requests into one vector: never batch it.
        self.batch_size = batch_size if input_format == "task_type" else 1
        self.usage = Usage()

    async def _call(self, reqs: Sequence[Request]) -> tuple[list[list[float]], int]:
        r0 = reqs[0]
        config = types.EmbedContentConfig(task_type=r0.task_type, title=r0.title)
        if len(reqs) > 1 and any(r.title for r in reqs):  # titles are per text: send singly
            raise ValueError("batched requests must not carry titles")
        for attempt in range(8):
            try:
                self.usage.requests += 1
                resp = await self.client.aio.models.embed_content(
                    model=self.model, contents=[r.content for r in reqs], config=config
                )
                embs = resp.embeddings or []
                if len(embs) != len(reqs):
                    raise RuntimeError(f"asked for {len(reqs)} embeddings, got {len(embs)}")
                tokens = sum(
                    int(e.statistics.token_count or 0) for e in embs if e.statistics is not None
                )
                return [list(e.values or []) for e in embs], tokens
            except (errors.APIError, TimeoutError, OSError) as exc:
                code = getattr(exc, "code", None)
                if isinstance(exc, errors.APIError) and code not in RETRYABLE:
                    raise
                self.usage.retries += 1
                delay = min(60.0, 2**attempt) * (0.5 + random.random())  # noqa: S311
                log.warning("embed retry %d in %.1fs (%s)", attempt + 1, delay, code or exc)
                await asyncio.sleep(delay)
        raise RuntimeError("embedding failed after 8 attempts")

    async def embed(self, items: Sequence[EmbedInput]) -> np.ndarray:
        """Normalised full-size vectors for `items`, in order."""
        start = time.perf_counter()
        keys = [cache_key(self.model, self.input_format, it) for it in items]
        have = self.cache.get_many(keys) if self.cache else {}
        self.usage.cached += sum(k in have for k in keys)
        todo = [i for i, k in enumerate(keys) if k not in have]
        reqs = [to_request(items[i], self.input_format) for i in todo]

        # Batch only title-less requests; titled ones (task_type documents) go singly.
        groups: list[list[int]] = []
        for j, r in enumerate(reqs):
            if r.title is None and groups and len(groups[-1]) < self.batch_size:
                last = reqs[groups[-1][0]]
                if last.title is None and last.task_type == r.task_type:
                    groups[-1].append(j)
                    continue
            groups.append([j])

        sem = asyncio.Semaphore(self.concurrency)
        pending: list[tuple[str, str, int | None, np.ndarray]] = []
        done = 0

        async def run(group: list[int]) -> None:
            nonlocal done
            async with sem:
                vectors, tokens = await self._call([reqs[j] for j in group])
            self.usage.tokens += tokens
            for j, v in zip(group, vectors, strict=True):
                vec = normalize(np.asarray(v, dtype=np.float32))
                have[keys[todo[j]]] = vec
                pending.append((keys[todo[j]], self.model, None, vec))
            done += len(group)
            if self.cache and len(pending) >= 500:
                self.cache.put_many(pending)
                pending.clear()
            if done % 1000 < len(group):
                log.info(
                    "embedded %d/%d (%s@%s, %d tokens so far)",
                    done, len(reqs), self.model, self.location, self.usage.tokens,
                )  # fmt: skip

        try:
            await asyncio.gather(*(run(g) for g in groups))
        finally:
            if self.cache and pending:
                self.cache.put_many(pending)
        self.usage.embedded += len(reqs)
        self.usage.seconds += time.perf_counter() - start
        return np.stack([have[k] for k in keys]) if keys else np.zeros((0, 0), np.float32)
