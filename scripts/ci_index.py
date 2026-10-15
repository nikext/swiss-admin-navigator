"""The search index CI evaluates against (EVALS.md §3): publish once, fetch per run.

    uv run python -m scripts.ci_index publish   # make publish-index (needs gcloud auth)
    uv run python -m scripts.ci_index fetch     # CI: download + verify sha256

`data/index.sqlite` is a build artefact (never committed). `publish` uploads
it to the project bucket under its own sha256 and writes the pointer
`evals/ci_index.json`, which is committed; `fetch` downloads exactly that file
and refuses it if the hash differs. Re-publish after `make index` whenever
the index changes, in the same PR as the change.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

POINTER = Path("evals/ci_index.json")
INDEX = Path("data/index.sqlite")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def index_meta(path: Path) -> dict[str, object]:
    db = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    meta = {k: json.loads(v) for k, v in db.execute("SELECT key, value FROM meta")}
    return {k: meta.get(k) for k in ("as_of", "git_sha", "records", "chunks", "default_space")}


def pointer(uri: str, digest: str, size: int, meta: dict[str, object]) -> dict[str, object]:
    return {"uri": uri, "sha256": digest, "bytes": size, "index": meta}


def gcloud() -> str:
    return shutil.which("gcloud") or str(Path.home() / "google-cloud-sdk/bin/gcloud")


def publish(index: Path, bucket: str) -> dict[str, object]:
    digest = sha256(index)
    uri = f"{bucket}/index/{digest[:16]}/index.sqlite"
    exists = subprocess.run(  # noqa: S603 (fixed gcloud invocation)
        [gcloud(), "storage", "ls", uri], capture_output=True, check=False
    )
    if exists.returncode != 0:
        subprocess.run([gcloud(), "storage", "cp", str(index), uri], check=True)  # noqa: S603
    else:
        print(f"{uri} already published")
    data = pointer(uri, digest, index.stat().st_size, index_meta(index))
    data["published"] = datetime.now(UTC).isoformat(timespec="seconds")
    POINTER.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    return data


def fetch(dest: Path) -> None:
    data = json.loads(POINTER.read_text(encoding="utf-8"))
    if dest.is_file() and sha256(dest) == data["sha256"]:
        print(f"{dest} is already the published index")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([gcloud(), "storage", "cp", data["uri"], str(dest)], check=True)  # noqa: S603
    got = sha256(dest)
    if got != data["sha256"]:
        dest.unlink()
        raise SystemExit(f"sha256 mismatch for {data['uri']}: {got} != {data['sha256']}")
    print(f"fetched {data['uri']} ({data['bytes']:,} bytes, index as_of {data['index']['as_of']})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("action", choices=["publish", "fetch"])
    ap.add_argument("--index", type=Path, default=INDEX)
    args = ap.parse_args(argv)
    load_dotenv(".env")
    if args.action == "publish":
        project = os.environ.get("GOOGLE_CLOUD_PROJECT") or sys.exit("GOOGLE_CLOUD_PROJECT unset")
        print(json.dumps(publish(args.index, f"gs://{project}-swiss-nav"), indent=1))
    else:
        fetch(args.index)
    return 0


if __name__ == "__main__":
    sys.exit(main())
