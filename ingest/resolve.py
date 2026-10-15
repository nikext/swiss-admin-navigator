"""Resolve acts.yaml against Fedlex SPARQL and write corpus/manifest.lock.json.

For each act: the in-force consolidation applicable on AS_OF, then every XML
file of that consolidation in our languages. Each file is fetched through the
cache to record its sha256, so a fresh lock always has a warm cache.

Usage: uv run python -m ingest.resolve [--as-of YYYY-MM-DD]   (or `make resolve`)
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from ingest.download import CACHE_DIR, PoliteClient, cache_path, fetch
from ingest.manifest import ACTS_PATH, LANGS, LOCK_PATH, Act, LockedAct, Manifest, load_acts

log = logging.getLogger(__name__)

SPARQL_URL = "https://fedlex.data.admin.ch/sparqlendpoint"
QUERIES = Path("corpus/queries")
XML_FORMAT = "https://fedlex.data.admin.ch/vocabulary/user-format/xml"
# Fedlex uses EU authority language URIs with ISO 639-2 codes.
ISO639_2 = {"deu": "de", "fra": "fr", "ita": "it", "eng": "en", "roh": "rm"}


class ResolveError(RuntimeError):
    pass


def render(template: str, **tokens: str) -> str:
    """Fill `{{TOKEN}}` placeholders; every placeholder must be supplied."""
    out = template
    for key, value in tokens.items():
        out = out.replace("{{" + key + "}}", value)
    leftover = re.findall(r"\{\{\w+\}\}", out)
    if leftover:
        raise ResolveError(f"unfilled template tokens: {sorted(set(leftover))}")
    return out


def lang_code(uri_or_code: str) -> str | None:
    """`…/language/DEU` or `deu` -> `de`; None for languages we don't know."""
    return ISO639_2.get(uri_or_code.rsplit("/", 1)[-1].lower())


def sparql(client: PoliteClient, query: str) -> list[dict[str, str]]:
    resp = client.post(
        SPARQL_URL,
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"},
    )
    rows = resp.json()["results"]["bindings"]
    return [{k: v["value"] for k, v in row.items()} for row in rows]


def latest_consolidations(
    client: PoliteClient, acts: Sequence[Act], as_of: str
) -> dict[str, dict[str, str]]:
    template = (QUERIES / "latest_consolidations.rq").read_text(encoding="utf-8")
    sr_list = " ".join(f'"{a.sr}"' for a in acts)
    rows = sparql(client, render(template, AS_OF=as_of, SR_LIST=sr_list))
    by_sr: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["sr"] in by_sr and by_sr[row["sr"]]["cons"] != row["cons"]:
            raise ResolveError(f"SR {row['sr']}: several in-force consolidations: {rows}")
        by_sr[row["sr"]] = row
    return by_sr


def xml_files(client: PoliteClient, consolidation: str) -> dict[str, str]:
    template = (QUERIES / "consolidation_files.rq").read_text(encoding="utf-8")
    rows = sparql(client, render(template, CONSOLIDATION=consolidation))
    files: dict[str, str] = {}
    for row in rows:
        lang = lang_code(row["lang"])
        if row["fmt"] != XML_FORMAT or lang not in LANGS:
            continue
        if lang in files and files[lang] != row["file"]:
            raise ResolveError(
                f"{consolidation}: two {lang} XML files: {files[lang]}, {row['file']}"
            )
        files[lang] = row["file"]
    return dict(sorted(files.items(), key=lambda kv: LANGS.index(kv[0])))


def check_resolution(acts: Sequence[Act], by_sr: dict[str, dict[str, str]]) -> list[str]:
    """Problems that must stop the build: missing acts, or an SR that now points elsewhere."""
    problems = []
    for act in acts:
        row = by_sr.get(act.sr)
        if row is None:
            problems.append(f"SR {act.sr} ({act.abbr['de']}): no in-force consolidation found")
        elif row["act"] != act.eli:
            problems.append(f"SR {act.sr}: Fedlex says {row['act']}, acts.yaml says {act.eli}")
    return problems


def resolve(
    client: PoliteClient, acts: Sequence[Act], as_of: str, cache_dir: Path = CACHE_DIR
) -> Manifest:
    by_sr = latest_consolidations(client, acts, as_of)
    problems = check_resolution(acts, by_sr)
    if problems:
        raise ResolveError("\n".join(problems))
    locked = []
    for act in acts:
        row = by_sr[act.sr]
        if row.get("abbr") and row["abbr"] != act.abbr["de"]:
            log.warning(
                "SR %s: Fedlex abbr %r != acts.yaml %r", act.sr, row["abbr"], act.abbr["de"]
            )
        entry = LockedAct(
            sr=act.sr,
            abbr=act.abbr,
            eli=act.eli,
            consolidation=row["cons"],
            date=row["date"],
            domain=list(act.domain),
        )
        for lang, url in xml_files(client, row["cons"]).items():
            entry.files[lang] = fetch(client, url, cache_path(act.sr, entry.date, lang, cache_dir))
        if "de" not in entry.files:
            raise ResolveError(f"SR {act.sr}: no German XML for {row['cons']}")
        log.info("%-14s %-5s %s %s", act.sr, act.abbr["de"], entry.date, " ".join(entry.files))
        locked.append(entry)
    return Manifest(as_of=as_of, acts=locked)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve acts.yaml into the lock.")
    parser.add_argument("--as-of", default=dt.date.today().isoformat())
    args = parser.parse_args(argv)
    dt.date.fromisoformat(args.as_of)  # validate
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    acts = load_acts(ACTS_PATH)
    with PoliteClient() as client:
        manifest = resolve(client, acts, args.as_of)
    manifest.save(LOCK_PATH)
    n_files = sum(len(a.files) for a in manifest.acts)
    print(f"wrote {LOCK_PATH}: {len(manifest.acts)} acts, {n_files} XML files, as_of {args.as_of}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
