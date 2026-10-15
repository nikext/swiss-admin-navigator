"""A small but real index.sqlite built from the committed Fedlex XML fixtures.

Built with the production code (`ingest.parse`, `ingest.chunk`,
`ingest.index.write_tables`), plus one vector space of deterministic
hashed bag-of-words vectors, so search and fusion can be tested offline.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest

from ingest.chunk import chunk_corpus
from ingest.index import load_aliases, write_tables
from ingest.parse import act_info, parse_file, parse_xml
from ingest.tests.test_parse import ACTS, FIXTURES

FILES = [("or", "de"), ("or", "fr"), ("zgb", "de"), ("zgb", "en"), ("fza", "de"), ("aig", "de")]
DIMS = 64


def bow_vector(text: str, dims: int = DIMS) -> np.ndarray:
    """Hashed bag of lowercased words, L2-normalised (a stand-in for an embedding)."""
    v = np.zeros(dims, dtype=np.float32)
    for w in re.findall(r"\w+", text.lower()):
        v[int(hashlib.md5(w.encode()).hexdigest(), 16) % dims] += 1.0  # noqa: S324
    n = np.linalg.norm(v)
    return v / n if n else v


def build_fixture_index(path: Path) -> Path:
    records, acts = [], []
    roots: dict[str, dict] = {}
    for name, lang in FILES:
        root = parse_xml((FIXTURES / f"{name}_{lang}.xml").read_bytes())
        roots.setdefault(name, {})[lang] = root
        records += [asdict(a) for a in parse_file(root, ACTS[name], lang)]
    for name, by_lang in roots.items():
        info = asdict(act_info(ACTS[name], by_lang))
        # Fixture XML is cut down; keep the abbreviations of the corpus' acts.yaml.
        info["abbrs"] = {**ACTS[name].abbr, **info["abbrs"]}
        acts.append(info)
    titles = {(a["sr"], lang): t for a in acts for lang, t in a["titles"].items()}
    chunks = chunk_corpus(records, titles)
    db = sqlite3.connect(path)
    write_tables(db, records, acts, chunks, ["trigram", "unicode61"], load_aliases())
    matrix = np.stack([bow_vector(f"{c.header} {c.text}") for c in chunks])
    rowids = np.arange(1, len(chunks) + 1, dtype=np.int32)
    spec = {"name": "bow", "profile": "test", "model": "bow", "location": "local",
            "input_format": "instruction", "header": True, "dims": DIMS}  # fmt: skip
    db.execute(
        "INSERT INTO vector_spaces VALUES (?, ?, ?, ?, ?, ?)",
        ("bow", json.dumps(spec), len(chunks), DIMS, rowids.tobytes(), matrix.tobytes()),
    )
    meta = {
        "schema_version": 1,
        "as_of": "2026-10-15",
        "tokenizers": ["trigram", "unicode61"],
        "default_tokenizer": "trigram",
        "spaces": [spec],
        "default_space": "bow",
        "records": len(records),
        "chunks": len(chunks),
        "notice": "Unofficial copy of Swiss federal law from Fedlex. Not legal advice.",
    }
    db.executemany("INSERT INTO meta VALUES (?, ?)", [(k, json.dumps(v)) for k, v in meta.items()])
    db.commit()
    db.close()
    return path


@pytest.fixture(scope="session")
def fixture_index_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_fixture_index(tmp_path_factory.mktemp("index") / "index.sqlite")
