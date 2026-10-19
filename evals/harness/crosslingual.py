"""E5 tables: the same questions in DE, EN, FR and IT (M9, docs/RESULTS.md).

`python -m evals.harness.crosslingual --report e5.json --original golden.json`

`--report` holds the translated cases (`evals/datasets/crosslingual.jsonl`, ids
`<golden id>-<lang>`), `--original` a golden run with the same agent, which
supplies each question in its original language. Every question then has an
answer in all four languages. Tables: each language's metrics (95% bootstrap
CIs over questions), differences to German paired by question, original vs
translated wording, and the languages the answers quote the law in.
Behaviour counts an error as a failure; quality metrics pair answered cases.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from statistics import fmean
from typing import Any

from evals.harness.compare import behaviour, fmt_mean_ci, ok
from evals.harness.retrieval_metrics import paired_bootstrap_diff

Row = dict[str, Any]
LANGS = ("de", "en", "fr", "it")


def question_id(row: Row) -> str:
    """The golden id a row answers: `housing-02-en` -> `housing-02`."""
    base, _, lang = row["id"].rpartition("-")
    return base if lang in LANGS and base else row["id"]


def grid(translated: list[Row], original: list[Row]) -> dict[str, dict[str, Row]]:
    """question id -> language -> row, for the questions answered in all four languages."""
    out: dict[str, dict[str, Row]] = {}
    for r in translated:
        out.setdefault(question_id(r), {})[r["lang"]] = r | {"translated": True}
    for r in original:
        if r["id"] in out:
            out[r["id"]][r["lang"]] = r | {"translated": False}
    return {q: by for q, by in sorted(out.items()) if set(by) == set(LANGS)}


Metric = tuple[str, Callable[[Row], float | None], bool]  # label, value, needs an answer
METRICS: list[Metric] = [
    ("groundedness", lambda r: r.get("groundedness"), True),
    ("key facts", lambda r: r.get("key_facts"), True),
    ("behaviour", behaviour, False),
    ("req. recall", lambda r: r.get("required_recall"), True),
    ("language", lambda r: float(bool(r.get("lang_ok"))), True),
]


def values(rows: list[Row], value: Callable[[Row], float | None], needs: bool) -> list[float]:
    out = []
    for r in rows:
        v = value(r) if ok(r) or not needs else None
        if v is not None:
            out.append(float(v))
    return out


def pairs(
    a: list[Row], b: list[Row], value: Callable[[Row], float | None], needs: bool
) -> tuple[list[float], list[float]]:
    xs, ys = [], []
    for ra, rb in zip(a, b, strict=True):
        if needs and not (ok(ra) and ok(rb)):
            continue
        va, vb = value(ra), value(rb)
        if va is not None and vb is not None:
            xs.append(float(va))
            ys.append(float(vb))
    return xs, ys


def fmt_diff(xs: list[float], ys: list[float]) -> str:
    if not xs:
        return "–"
    mean, lo, hi = paired_bootstrap_diff(ys, xs)
    return f"{100 * mean:+.1f} ({100 * lo:+.1f}…{100 * hi:+.1f})"


def quote_langs(rows: list[Row]) -> str:
    langs: Counter[str] = Counter()
    for r in rows:
        for c in (r.get("answer") or {}).get("citations") or []:
            if c.get("quote"):
                langs[c.get("quote_lang") or "?"] += 1
    total = sum(langs.values())
    return ", ".join(f"{k} {100 * n / total:.0f}%" for k, n in langs.most_common()) or "–"


def tables(g: dict[str, dict[str, Row]]) -> str:
    by_lang = {lang: [g[q][lang] for q in g] for lang in LANGS}
    head = "| language | n | errors | " + " | ".join(m[0] for m in METRICS) + " | quotes in |"
    lines = [f"{len(g)} questions, each answered in all four languages.", "", head]
    lines.append("|" + "---|" * (len(METRICS) + 4))
    for lang, rows in by_lang.items():
        cells = [lang.upper(), str(len(rows)), str(sum(not ok(r) for r in rows))]
        cells += [fmt_mean_ci(values(rows, v, needs), 100) for _, v, needs in METRICS]
        lines.append("| " + " | ".join([*cells, quote_langs(rows)]) + " |")

    lines += ["", "Paired differences to **DE** (mean, 95% CI):", ""]
    lines += ["| language | " + " | ".join(f"Δ {m[0]}" for m in METRICS) + " |"]
    lines.append("|" + "---|" * (len(METRICS) + 1))
    for lang in LANGS[1:]:
        cells = [fmt_diff(*pairs(by_lang["de"], by_lang[lang], v, n)) for _, v, n in METRICS]
        lines.append(f"| {lang.upper()} | " + " | ".join(cells) + " |")

    # Original wording vs the mean of its three translations, question by question.
    lines += ["", "Original wording vs translations (paired by question, mean, 95% CI):", ""]
    lines += [
        "| metric | original | translations | Δ translations − original |",
        "|---|---|---|---|",
    ]
    for label, value, needs in METRICS:
        xs, ys = [], []
        for by in g.values():
            orig = next(r for r in by.values() if not r["translated"])
            trans = [value(r) for r in by.values() if r["translated"] and (ok(r) or not needs)]
            vo = value(orig) if ok(orig) or not needs else None
            trans = [t for t in trans if t is not None]
            if vo is None or not trans:
                continue
            xs.append(float(vo))
            ys.append(fmean(float(t) for t in trans))
        lines.append(
            f"| {label} | {100 * fmean(xs):.1f} | {100 * fmean(ys):.1f} | {fmt_diff(xs, ys)} |"
            if xs
            else f"| {label} | – | – | – |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--report", type=Path, required=True, help="run of crosslingual.jsonl")
    ap.add_argument("--original", type=Path, required=True, help="golden run, same agent")
    args = ap.parse_args(argv)
    translated = json.loads(args.report.read_text(encoding="utf-8"))["cases"]
    original = json.loads(args.original.read_text(encoding="utf-8"))["cases"]
    print(tables(grid(translated, original)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
