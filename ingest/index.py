"""articles.jsonl + acts.json -> index.sqlite (docs/DATA.md §4, ADR-002).

Usage:
    uv run python -m ingest.index                 # production index (make index)
    uv run python -m ingest.index --experiment    # E4: every tokenizer + vector space

The index is self-describing: `meta` records how every vector space was built
(model, location, input format, query template, dims, header on/off), and the
MCP server embeds queries from that record, so a server can never query an
index with the wrong model or format.

Tables
- `articles`: every record (all statuses), for `get_article`.
- `chunks`: retrieval units of in-force articles (ingest.chunk).
- `fts_<tokenizer>`: contentless FTS5 over (header, body), rowid = chunk rowid.
- `vector_spaces`: one row per space with the whole matrix as one float32 blob
  (rows aligned with the `rowids` blob): one read at startup, numpy at query
  time. ~17k chunks don't need an ANN index (ADR-016).
- `toc`: level/article tree per act and language, for `get_toc`.
- `acts`, `abbreviations`: for `list_acts` and `resolve_citation`.
- `meta`: as_of, build sha, chunking, defaults, spaces.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sqlite3
import subprocess
import sys
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from dotenv import load_dotenv

from agents.navigator.config import load_profile
from ingest.chunk import MAX_CHARS, Chunk, chunk_corpus
from ingest.embed import (
    DOC_TEMPLATE,
    QUERY_TEMPLATE,
    EmbedCache,
    Embedder,
    EmbedInput,
    truncate,
)
from ingest.manifest import ACTS_PATH, LOCK_PATH, Manifest
from ingest.parse import ACTS_OUT_PATH, OUT_PATH
from mcp_server.citations import norm_abbr

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1
INDEX_PATH = Path("data/index.sqlite")
EXPERIMENT_PATH = Path("data/index_e4.sqlite")
TOKENIZERS = {
    "unicode61": "unicode61 remove_diacritics 2",
    "trigram": "trigram remove_diacritics 1",
}
# Production defaults, chosen by experiment E4 (docs/DECISIONS.md ADR-016): dense
# retrieval with gemini-embedding-2 over chunks with contextual headers, 768 dims.
# BM25 (unicode61) is only the fallback when the query embedding fails.
DEFAULT_MODE = "dense"
DEFAULT_TOKENIZER = "unicode61"
DEFAULT_HEADER = True
DEFAULT_DIMS = 768
# Abbreviations in the product's languages; Romansh ones (DO, CCS, LEst) are left out.
ABBR_LANGS = ("de", "fr", "it", "en")


@dataclass(frozen=True)
class SpaceSpec:
    """A vector space: chunks embedded by one profile's model, with or without headers."""

    name: str
    profile: str
    header: bool
    dims: int | None = None  # None = keep full size

    @classmethod
    def parse(cls, spec: str) -> SpaceSpec:
        """`emb2-h=default:header[:768]` / `emb2-noh=default:noheader`."""
        name, _, rest = spec.partition("=")
        profile, _, tail = rest.partition(":")
        header_flag, _, dims = tail.partition(":")
        if not name or not profile or header_flag not in ("header", "noheader"):
            raise ValueError(f"bad space spec {spec!r}; want NAME=PROFILE:header|noheader[:DIMS]")
        return cls(name, profile, header_flag == "header", int(dims) if dims else None)


EXPERIMENT_SPACES = (
    "emb2-h=default:header",
    "emb2-noh=default:noheader",
    "emb001-h=e4-emb001:header",
)


# --- schema --------------------------------------------------------------------

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE acts (
  sr TEXT PRIMARY KEY, eli TEXT, consolidation_date TEXT, domain TEXT, langs TEXT,
  titles TEXT, abbrs TEXT, ord INTEGER);
CREATE TABLE abbreviations (
  norm TEXT NOT NULL, abbr TEXT NOT NULL, sr TEXT NOT NULL, lang TEXT, kind TEXT NOT NULL,
  PRIMARY KEY (norm, sr, lang));
CREATE TABLE articles (
  rowid INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, sr TEXT, abbr TEXT, lang TEXT,
  eid TEXT, label TEXT, heading TEXT, heading_path TEXT, heading_eids TEXT, text TEXT,
  paragraphs TEXT, notes TEXT, refs TEXT, status TEXT, consolidation_date TEXT, url TEXT,
  domain TEXT);
CREATE INDEX articles_lookup ON articles (sr, eid, lang);
CREATE TABLE chunks (
  rowid INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, article_rowid INTEGER NOT NULL,
  sr TEXT, lang TEXT, eid TEXT, anchor TEXT, part INTEGER, parts INTEGER, header TEXT,
  text TEXT);
CREATE TABLE toc (
  sr TEXT, lang TEXT, node TEXT, parent TEXT, ord INTEGER, kind TEXT, title TEXT,
  label TEXT, PRIMARY KEY (sr, lang, node));
CREATE INDEX toc_children ON toc (sr, lang, parent, ord);
CREATE TABLE vector_spaces (
  name TEXT PRIMARY KEY, spec TEXT NOT NULL, n INTEGER, dims INTEGER, rowids BLOB, matrix BLOB);
"""


def abbreviation_rows(
    acts: Sequence[Mapping[str, Any]], aliases: Mapping[str, Sequence[str]]
) -> list[tuple[str, str, str, str | None, str]]:
    rows: dict[tuple[str, str, str | None], tuple[str, str, str, str | None, str]] = {}
    for act in acts:
        for lang, abbr in act["abbrs"].items():
            if lang in ABBR_LANGS:
                rows[(norm_abbr(abbr), act["sr"], lang)] = (
                    norm_abbr(abbr), abbr, act["sr"], lang, "official",
                )  # fmt: skip
        for alias in aliases.get(act["sr"], ()):
            key = (norm_abbr(alias), act["sr"], None)
            rows.setdefault(key, (norm_abbr(alias), alias, act["sr"], None, "alias"))
    out = sorted(rows.values())
    owners: dict[str, set[str]] = {}
    for n, _, sr, _, _ in out:
        owners.setdefault(n, set()).add(sr)
    clashes = {n: s for n, s in owners.items() if len(s) > 1}
    if clashes:
        raise ValueError(f"abbreviations shared by several acts: {clashes}")
    return out


def load_aliases(path: Path = ACTS_PATH) -> dict[str, list[str]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {str(a["sr"]): list(a.get("aliases", [])) for a in raw["acts"]}


def toc_rows(records: Iterable[Mapping[str, Any]]) -> list[tuple[Any, ...]]:
    """Tree rows (sr, lang, node, parent, ord, kind, title, label) in document order.

    Container eIds are mostly unique, but Fedlex reuses a few (ZGB Schlusstitel
    has two `lvl_I_ter`; EN ZGB has shifted ones). A reused eId under another
    label becomes `<eid>~2`, so every node stays addressable.
    """
    rows: list[tuple[Any, ...]] = []
    nodes: dict[tuple[str, str, str, str, str], str] = {}  # (sr, lang, parent, eid, title)
    used: dict[tuple[str, str], set[str]] = {}
    order: dict[tuple[str, str, str], int] = {}

    def add(sr: str, lang: str, node: str, parent: str, kind: str, title: str, label: str | None):
        ord_ = order.get((sr, lang, parent), 0)
        order[(sr, lang, parent)] = ord_ + 1
        rows.append((sr, lang, node, parent, ord_, kind, title, label))

    for r in records:
        sr, lang = r["sr"], r["lang"]
        taken = used.setdefault((sr, lang), set())
        parent = ""
        for eid, title in zip(r["heading_eids"], r["heading_path"], strict=True):
            key = (sr, lang, parent, eid, title)
            if key not in nodes:
                node, n = eid, 1
                while node in taken:
                    n += 1
                    node = f"{eid}~{n}"
                taken.add(node)
                nodes[key] = node
                add(sr, lang, node, parent, "level", title, None)
            parent = nodes[key]
        node = r["eid"] if r["eid"] not in taken else f"{r['eid']}~a"
        taken.add(node)
        add(sr, lang, node, parent, "article", r.get("heading") or "", r["label"])
    return rows


# --- build ---------------------------------------------------------------------


def git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],  # noqa: S607
            capture_output=True, text=True, check=True,
        )  # fmt: skip
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)  # noqa: S607
        return out.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_tables(
    db: sqlite3.Connection,
    records: Sequence[Mapping[str, Any]],
    acts: Sequence[Mapping[str, Any]],
    chunks: Sequence[Chunk],
    tokenizers: Sequence[str],
    aliases: Mapping[str, Sequence[str]],
) -> None:
    db.executescript(SCHEMA)
    db.executemany(
        "INSERT INTO acts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                a["sr"], a["eli"], a["consolidation_date"], json.dumps(a["domain"]),
                json.dumps(a["langs"]), json.dumps(a["titles"], ensure_ascii=False),
                json.dumps(a["abbrs"], ensure_ascii=False), i,
            )
            for i, a in enumerate(acts)
        ],
    )  # fmt: skip
    db.executemany(
        "INSERT INTO abbreviations VALUES (?, ?, ?, ?, ?)", abbreviation_rows(acts, aliases)
    )
    cols = [
        "id",
        "sr",
        "abbr",
        "lang",
        "eid",
        "label",
        "heading",
        "heading_path",
        "heading_eids",
        "text",
        "paragraphs",
        "notes",
        "refs",
        "status",
        "consolidation_date",
        "url",
        "domain",
    ]
    as_json = {"heading_path", "heading_eids", "paragraphs", "notes", "refs", "domain"}
    db.executemany(
        f"INSERT INTO articles ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",  # noqa: S608
        [
            tuple(json.dumps(r[c], ensure_ascii=False) if c in as_json else r[c] for c in cols)
            for r in records
        ],
    )
    rowid_of = dict(db.execute("SELECT id, rowid FROM articles"))
    db.executemany(
        "INSERT INTO chunks (rowid, id, article_rowid, sr, lang, eid, anchor, part, parts, "
        "header, text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (i + 1, c.id, rowid_of[c.article_id], c.sr, c.lang, c.eid, c.anchor, c.part,
             c.parts, c.header, c.text)
            for i, c in enumerate(chunks)
        ],
    )  # fmt: skip
    for name in tokenizers:
        db.execute(
            f"CREATE VIRTUAL TABLE fts_{name} USING fts5(header, body, content='', "
            f"tokenize='{TOKENIZERS[name]}')"
        )
        db.executemany(
            f"INSERT INTO fts_{name} (rowid, header, body) VALUES (?, ?, ?)",  # noqa: S608
            [(i + 1, c.header, c.text) for i, c in enumerate(chunks)],
        )
    db.executemany("INSERT INTO toc VALUES (?, ?, ?, ?, ?, ?, ?, ?)", toc_rows(records))


async def embed_space(
    spec: SpaceSpec, chunks: Sequence[Chunk], project: str, cache: EmbedCache, concurrency: int
) -> tuple[np.ndarray, dict[str, Any]]:
    ref = load_profile(spec.profile).embedding
    embedder = Embedder(ref.model, ref.location, ref.input_format, project, cache, concurrency)
    items = [EmbedInput("document", c.text, c.header if spec.header else None) for c in chunks]
    matrix = await embedder.embed(items)
    if spec.dims:
        matrix = truncate(matrix, spec.dims)
    u = embedder.usage
    log.info(
        "space %s: %d vectors x %d dims; %d embedded (%d tokens, %d requests, %d retries) "
        "+ %d cached in %.0fs",
        spec.name, len(matrix), matrix.shape[1], u.embedded, u.tokens, u.requests, u.retries,
        u.cached, u.seconds,
    )  # fmt: skip
    info = {
        "name": spec.name,
        "profile": spec.profile,
        "model": ref.model,
        "location": ref.location,
        "input_format": ref.input_format,
        "header": spec.header,
        "dims": int(matrix.shape[1]),
        "query_template": QUERY_TEMPLATE if ref.input_format == "instruction" else None,
        "doc_template": DOC_TEMPLATE if ref.input_format == "instruction" else None,
        "query_task_type": "RETRIEVAL_QUERY" if ref.input_format == "task_type" else None,
        "tokens_embedded": u.tokens,
    }
    return matrix, info


def build(
    out: Path,
    tokenizers: Sequence[str],
    spaces: Sequence[SpaceSpec],
    concurrency: int = 16,
    records_path: Path = OUT_PATH,
    acts_path: Path = ACTS_OUT_PATH,
) -> dict[str, Any]:
    load_dotenv()
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    if spaces and not project:
        raise SystemExit("GOOGLE_CLOUD_PROJECT is not set (copy .env.example to .env)")
    start = time.perf_counter()
    with records_path.open(encoding="utf-8") as f:
        records = [json.loads(line) for line in f]
    acts = json.loads(acts_path.read_text(encoding="utf-8"))
    titles = {(a["sr"], lang): t for a in acts for lang, t in a["titles"].items()}
    chunks = chunk_corpus(records, titles)
    log.info("%d records, %d in-force chunks", len(records), len(chunks))

    tmp = out.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    db = sqlite3.connect(tmp)
    db.execute("PRAGMA journal_mode = OFF")
    db.execute("PRAGMA synchronous = OFF")
    write_tables(db, records, acts, chunks, tokenizers, load_aliases())

    cache = EmbedCache()
    space_info = []
    rowids = np.arange(1, len(chunks) + 1, dtype=np.int32)
    for spec in spaces:
        matrix, info = asyncio.run(embed_space(spec, chunks, project, cache, concurrency))
        db.execute(
            "INSERT INTO vector_spaces VALUES (?, ?, ?, ?, ?, ?)",
            (spec.name, json.dumps(info), len(matrix), info["dims"], rowids.tobytes(),
             np.ascontiguousarray(matrix, dtype=np.float32).tobytes()),
        )  # fmt: skip
        space_info.append(info)

    manifest = Manifest.load(LOCK_PATH)
    meta = {
        "schema_version": SCHEMA_VERSION,
        "as_of": manifest.as_of,
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": git_sha(),
        "records": len(records),
        "chunks": len(chunks),
        "chunk_max_chars": MAX_CHARS,
        "tokenizers": list(tokenizers),
        "default_tokenizer": tokenizers[0] if tokenizers else None,
        "default_mode": DEFAULT_MODE if space_info else "bm25",
        "spaces": space_info,
        "default_space": space_info[0]["name"] if space_info else None,
        "notice": "Unofficial copy of Swiss federal law from Fedlex. Not legal advice.",
    }
    db.executemany("INSERT INTO meta VALUES (?, ?)", [(k, json.dumps(v)) for k, v in meta.items()])
    db.commit()
    db.execute("VACUUM")
    db.close()
    tmp.replace(out)
    log.info(
        "wrote %s (%.0f MB) in %.0fs", out, out.stat().st_size / 1e6, time.perf_counter() - start
    )
    return meta


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--experiment", action="store_true", help="E4 index: all tokenizers + spaces")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--tokenizer", action="append", choices=sorted(TOKENIZERS))
    ap.add_argument("--space", action="append", help="NAME=PROFILE:header|noheader[:DIMS]")
    ap.add_argument("--no-vectors", action="store_true", help="FTS only (no embedding calls)")
    ap.add_argument("--concurrency", type=int, default=16)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.experiment:
        out = args.out or EXPERIMENT_PATH
        tokenizers = args.tokenizer or sorted(TOKENIZERS)
        specs = args.space or list(EXPERIMENT_SPACES)
    else:
        out = args.out or INDEX_PATH
        tokenizers = args.tokenizer or [DEFAULT_TOKENIZER]
        header = "header" if DEFAULT_HEADER else "noheader"
        default_profile = os.environ.get("NAV_PROFILE") or "default"
        specs = args.space or [f"dense={default_profile}:{header}:{DEFAULT_DIMS}"]
    spaces = [] if args.no_vectors else [SpaceSpec.parse(s) for s in specs]
    meta = build(out, tokenizers, spaces, args.concurrency)
    print(json.dumps({k: meta[k] for k in ("as_of", "records", "chunks", "default_space")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
