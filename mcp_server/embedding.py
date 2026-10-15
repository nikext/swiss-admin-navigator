"""Query embeddings for `search_law`, configured by the index itself.

The index's `meta` records how its vector space was built (model, endpoint
location, input format, query template, dims; see ingest/index.py), so the
server embeds queries exactly the way the documents were embedded and needs no
model ID of its own (ADR-008). `EMBEDDING_LOCATION` may move the endpoint;
`EMBEDDING_MODEL`, if set, must match the index or the server refuses to start.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any

import numpy as np
from google import genai
from google.genai import errors, types

log = logging.getLogger(__name__)


class EmbeddingConfigError(RuntimeError):
    pass


class EmbeddingUnavailableError(RuntimeError):
    """The breaker is open after a recent failure; callers fall back to keywords."""


class QueryEmbedder:
    def __init__(
        self,
        space: Mapping[str, Any],
        project: str,
        env: Mapping[str, str],
        cache_size: int = 2048,
        timeout_s: float = 5.0,
        cooldown_s: float = 30.0,
    ) -> None:
        wanted = env.get("EMBEDDING_MODEL")
        if wanted and wanted != space["model"]:
            raise EmbeddingConfigError(
                f"EMBEDDING_MODEL={wanted!r} but the index was built with {space['model']!r}"
            )
        self.model: str = space["model"]
        self.location: str = env.get("EMBEDDING_LOCATION") or space["location"]
        self.input_format: str = space["input_format"]
        self.template: str | None = space.get("query_template")
        self.task_type: str | None = space.get("query_task_type")
        self.dims: int = int(space["dims"])
        if self.input_format == "instruction" and not self.template:
            raise EmbeddingConfigError("index meta lacks the query template")
        # Keep the client referenced: it closes its HTTP session when collected.
        self.client = genai.Client(vertexai=True, project=project, location=self.location)
        self.timeout_s = timeout_s
        # Circuit breaker: after a failure, skip the endpoint for `cooldown_s` so an
        # outage costs one slow request, not a timeout on every search.
        self.cooldown_s = cooldown_s
        self._down_until = 0.0
        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._cache_size = cache_size

    def describe(self) -> dict[str, Any]:
        return {"model": self.model, "location": self.location, "dims": self.dims}

    async def embed(self, query: str) -> np.ndarray:
        key = " ".join(query.split())
        if (hit := self._cache.get(key)) is not None:
            self._cache.move_to_end(key)
            return hit
        if time.monotonic() < self._down_until:
            raise EmbeddingUnavailableError("embedding endpoint failed recently; cooling down")
        try:
            v = await self._embed(key)
        except Exception:
            self._down_until = time.monotonic() + self.cooldown_s
            raise
        self._cache[key] = v
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
        return v

    async def warm(self) -> None:
        """Fetch the access token and open the TLS connection before the first real query.

        On a cold Cloud Run instance this takes ~0.9 s; run as a background task at
        startup it overlaps with the client's MCP handshake. Best effort: a failure
        neither trips the breaker nor caches anything. Costs ~3 tokens per start.
        """
        try:
            await self._embed("Art. 1")
        except Exception as exc:
            log.warning("embedding warm-up failed: %r", exc)

    async def _embed(self, key: str) -> np.ndarray:
        if self.input_format == "instruction":
            content, config = (
                (self.template or "{text}").format(text=key),
                types.EmbedContentConfig(output_dimensionality=self.dims),
            )
        else:
            content, config = (
                key,
                types.EmbedContentConfig(task_type=self.task_type, output_dimensionality=self.dims),
            )
        call = self.client.aio.models.embed_content
        try:
            resp = await asyncio.wait_for(
                call(model=self.model, contents=[content], config=config), self.timeout_s
            )
        except errors.APIError as exc:  # one quick retry on throttling / transient errors
            if exc.code not in (429, 500, 503):
                raise
            await asyncio.sleep(0.5)
            resp = await asyncio.wait_for(
                call(model=self.model, contents=[content], config=config), self.timeout_s
            )
        values = (resp.embeddings or [types.ContentEmbedding()])[0].values or []
        v = np.asarray(values, dtype=np.float32)
        if v.size != self.dims:
            raise RuntimeError(f"expected a {self.dims}-dim embedding, got {v.size}")
        return v / (np.linalg.norm(v) or 1.0)
