import hashlib
import json
import sqlite3
from pathlib import Path

from scripts.ci_index import index_meta, pointer, sha256


def test_sha256_matches_hashlib(tmp_path: Path) -> None:
    f = tmp_path / "x.bin"
    f.write_bytes(b"swiss-nav" * 300_000)  # > 1 MiB block
    assert sha256(f) == hashlib.sha256(f.read_bytes()).hexdigest()


def test_index_meta_and_pointer(tmp_path: Path) -> None:
    db_path = tmp_path / "index.sqlite"
    db = sqlite3.connect(db_path)
    db.execute("CREATE TABLE meta (key TEXT, value TEXT)")
    rows = {"as_of": "2026-10-15", "git_sha": "c756c89", "records": 18396, "other": 1}
    db.executemany("INSERT INTO meta VALUES (?, ?)", [(k, json.dumps(v)) for k, v in rows.items()])
    db.commit()
    db.close()
    meta = index_meta(db_path)
    assert meta["as_of"] == "2026-10-15"
    assert meta["records"] == 18396
    assert "other" not in meta
    uri = "gs://b/index/abc/index.sqlite"
    assert pointer(uri, "abc", 10, meta) == {
        "uri": uri,
        "sha256": "abc",
        "bytes": 10,
        "index": meta,
    }
