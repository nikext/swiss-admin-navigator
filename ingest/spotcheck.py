"""Spot-check parsed articles against Fedlex's own HTML rendering (M1 "Done when").

For N random in-force records (fixed seed), this
1. fetches Fedlex's HTML manifestation of the same consolidation and language
   (an independent rendering in the filestore; cached under cache/html/),
2. checks that the record's `#eId` anchor exists there, which is the target of
   the deep link (www.fedlex.admin.ch is a JS app, so an HTTP 200 alone proves
   nothing), and that the deep-link page itself answers 200,
3. compares our text with the HTML article text, after dropping the heading,
   footnote markers and footnotes and normalising whitespace and table pipes.

Usage: uv run python -m ingest.spotcheck [--n 10] [--seed 20261015]
"""

from __future__ import annotations

import argparse
import difflib
import json
import random
import re
import sys
from pathlib import Path

from lxml import html

from ingest.download import PoliteClient, fetch
from ingest.manifest import LOCK_PATH, LockedAct, Manifest
from ingest.parse import OUT_PATH
from ingest.resolve import QUERIES, lang_code, render, sparql

HTML_CACHE = Path("cache/html")
HTML_FORMAT = "https://fedlex.data.admin.ch/vocabulary/user-format/html"


def comparable(text: str) -> str:
    text = text.replace("\xa0", " ").replace("|", " ")
    return re.sub(r"\s+", " ", text).strip()


def html_article_text(article: html.HtmlElement) -> str:
    for el in article.xpath(
        ".//h6 | .//div[@class='footnotes'] | .//sup[a[starts-with(@href, '#fn-')]]"
    ):
        el.drop_tree()
    # Fedlex's HTML has no whitespace between block elements (`</p><p>`).
    for el in article.iter("p", "dt", "dd", "div", "tr", "td", "th", "li"):
        el.tail = " " + (el.tail or "")
    return comparable(article.text_content())


def without_subheading(theirs: str, heading: str | None) -> str:
    """Fedlex's HTML prints a reference subheading such as "(art. 30, al. 1, let. k,
    LEI)" at the start of the body; we keep it at the end of `heading` instead."""
    m = re.match(r"\([^()]*(?:\([^()]*\)[^()]*)*\)\s*", theirs)
    if m and heading and comparable(heading).endswith(m.group(0).strip()):
        return theirs[m.end() :]
    return theirs


def html_url(client: PoliteClient, act: LockedAct, lang: str) -> str:
    template = (QUERIES / "consolidation_files.rq").read_text(encoding="utf-8")
    for row in sparql(client, render(template, CONSOLIDATION=act.consolidation)):
        if row["fmt"] == HTML_FORMAT and lang_code(row["lang"]) == lang:
            return row["file"]
    raise LookupError(f"no HTML manifestation for {act.consolidation} {lang}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Spot-check articles against Fedlex HTML.")
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20261015)
    args = parser.parse_args(argv)

    manifest = Manifest.load(LOCK_PATH)
    acts = {a.sr: a for a in manifest.acts}
    records = [json.loads(line) for line in OUT_PATH.open(encoding="utf-8")]
    sample = random.Random(args.seed).sample(  # noqa: S311 - reproducible sampling, not crypto
        [r for r in records if r["status"] == "in_force"], args.n
    )

    rows, failures = [], 0
    with PoliteClient() as client:
        for rec in sample:
            act = acts[rec["sr"]]
            dest = HTML_CACHE / act.sr / act.date / f"{rec['lang']}.html"
            if not dest.is_file():
                fetch(client, html_url(client, act, rec["lang"]), dest)
            page = html.fromstring(dest.read_bytes())
            hits = page.xpath("//*[@id=$eid]", eid=rec["eid"])
            found = (
                [h for h in hits if isinstance(h, html.HtmlElement)]
                if isinstance(hits, list)
                else []
            )
            anchor_ok = bool(found)
            page_status = client.get(rec["url"].split("#")[0]).status_code
            ratio, diff = 0.0, ""
            if anchor_ok:
                theirs, ours = html_article_text(found[0]), comparable(rec["text"])
                theirs = without_subheading(theirs, rec["heading"])
                ratio = difflib.SequenceMatcher(None, ours, theirs, autojunk=False).ratio()
                if ours != theirs:
                    diff = _first_difference(ours, theirs)
            ok = anchor_ok and page_status == 200 and ratio == 1.0
            failures += not ok
            rows.append(
                f"| {'✅' if ok else '❌'} | `{rec['id']}` | {rec['abbr']} {rec['label']} "
                f"| {'yes' if anchor_ok else 'NO'} | {page_status} | {ratio:.3f} | {diff} |"
            )
    print("| | record | article | anchor in Fedlex HTML | page | text match | first difference |")
    print("|---|---|---|---|---|---|---|")
    print("\n".join(rows))
    print(f"\n{args.n - failures}/{args.n} identical (seed {args.seed}).")
    return 1 if failures else 0


def _first_difference(ours: str, theirs: str) -> str:
    i = next((k for k, (a, b) in enumerate(zip(ours, theirs, strict=False)) if a != b), None)
    i = min(len(ours), len(theirs)) if i is None else i
    lo = max(0, i - 25)
    return f"ours `…{ours[lo : i + 25]}…` vs Fedlex `…{theirs[lo : i + 25]}…`"


if __name__ == "__main__":
    sys.exit(main())
