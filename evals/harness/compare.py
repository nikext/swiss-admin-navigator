"""Experiment tables from answer-eval reports (M8 E2/E6, docs/RESULTS.md).

`python -m evals.harness.compare --report v1=a.json --report v2=b.json [--subset golden]`
prints two Markdown tables: each configuration's metrics (with 95% bootstrap
CIs), and each configuration's difference to the first one, paired case by
case (same ids; percentile bootstrap of the mean difference, 2,000 resamples,
seed 0). Quality metrics pair the cases both runs answered; behaviour counts
an error as a failure, as the reports do.

`--study v1=study.json --judge qwen/…@global` replaces the judge's metrics of
a report with another judge's grades of the same answers (`make judge-study
ARGS="--report a.json" JUDGES=…`), for the cross-family check (EVALS.md §2).
Answers that judge did not grade lose their judge metrics.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from statistics import fmean
from typing import Any

from evals.harness.answer_metrics import percentile, ratio_ci
from evals.harness.judge import Judgement, groundedness, key_fact_coverage
from evals.harness.retrieval_metrics import bootstrap_ci, paired_bootstrap_diff

Row = dict[str, Any]
SUBSETS: dict[str, Callable[[Row], bool]] = {
    "all": lambda r: True,
    "golden": lambda r: not r["id"].startswith("adv-"),
    "adversarial": lambda r: r["id"].startswith("adv-"),
}


def ok(r: Row) -> bool:
    return not r.get("error")


def behaviour(r: Row) -> float:
    return float(bool(r.get("behaviour_ok", r.get("behaviour_det"))))


def cost_chf(r: Row, rate: float) -> float | None:
    return None if r.get("cost_usd") is None else r["cost_usd"] * rate


# Paired metrics: (label, value of a row or None, scale for display, needs an answer)
PAIRED: list[tuple[str, Callable[[Row, float], float | None], float, bool]] = [
    ("groundedness", lambda r, _: r.get("groundedness"), 100, True),
    ("key facts", lambda r, _: r.get("key_facts"), 100, True),
    ("behaviour", lambda r, _: behaviour(r), 100, False),
    ("must_not", lambda r, _: r.get("must_not_violations"), 1, True),
    ("CHF/answer", cost_chf, 1, True),
    ("latency s", lambda r, _: r.get("latency_s"), 1, True),
]


def paired(
    a: list[Row], b: list[Row], value: Callable[[Row], float | None], needs_answer: bool
) -> tuple[float, float, float, int] | None:
    """Mean of value(b) - value(a) over the ids both have values for, with a paired CI."""
    by_id = {r["id"]: r for r in a}
    xs, ys = [], []
    for rb in b:
        ra = by_id.get(rb["id"])
        if ra is None or (needs_answer and not (ok(ra) and ok(rb))):
            continue
        va, vb = value(ra), value(rb)
        if va is None or vb is None:
            continue
        xs.append(float(va))
        ys.append(float(vb))
    if not xs:
        return None
    mean, lo, hi = paired_bootstrap_diff(ys, xs)
    return mean, lo, hi, len(xs)


def fmt_mean_ci(values: list[float], scale: float, digits: int = 1) -> str:
    if not values:
        return "–"
    lo, hi = bootstrap_ci(values)
    return f"{scale * fmean(values):.{digits}f} ({scale * lo:.{digits}f}–{scale * hi:.{digits}f})"


def absolute_row(label: str, rows: list[Row], rate: float) -> str:
    good = [r for r in rows if ok(r)]
    quotes = [r["quotes"] for r in rows]
    verbatim = [r["verbatim"] for r in rows]
    qf = f"{100 * sum(verbatim) / sum(quotes):.1f}%" if sum(quotes) else "–"
    ci = ratio_ci(verbatim, quotes)
    if ci:
        qf += f" ({100 * ci[0]:.1f}–{100 * ci[1]:.1f})"
    costs = [c for c in (cost_chf(r, rate) for r in good) if c is not None]
    lat = [r["latency_s"] for r in good]
    calls = [r["usage"]["model_calls"] + (r.get("router_usage") or {}).get("model_calls", 0)
             + (r.get("claims_usage") or {}).get("model_calls", 0) for r in good]  # fmt: skip
    grounded = [r["groundedness"] for r in good if r.get("groundedness") is not None]
    facts = [r["key_facts"] for r in good if r.get("key_facts") is not None]
    req = [r["required_recall"] for r in good if r.get("required_recall") is not None]
    cells = [
        label,
        str(len(rows)),
        str(len(rows) - len(good)),
        qf,
        str(sum(r["hallucinated"] for r in rows)),
        fmt_mean_ci(grounded, 100),
        fmt_mean_ci(facts, 100),
        str(sum(r.get("must_not_violations") or 0 for r in good)),
        fmt_mean_ci([behaviour(r) for r in rows], 100),
        fmt_mean_ci(req, 100),
        f"{fmean(costs):.4f}" if costs else "–",
        f"{percentile(lat, 0.5):.0f} / {percentile(lat, 0.95):.0f}" if lat else "–",
        f"{fmean(calls):.1f}" if calls else "–",
    ]
    return "| " + " | ".join(cells) + " |"


def paired_row(label: str, base: list[Row], rows: list[Row], rate: float) -> str:
    cells = [label]
    for name, value, scale, needs in PAIRED:
        res = paired(base, rows, lambda r, v=value: v(r, rate), needs)
        if res is None:
            cells.append("–")
            continue
        mean, lo, hi, n = res
        digits = 4 if name == "CHF/answer" else 1
        cell = f"{scale * mean:+.{digits}f} ({scale * lo:+.{digits}f}…{scale * hi:+.{digits}f})"
        cells.append(cell + (f", n={n}" if name == "groundedness" else ""))
    return "| " + " | ".join(cells) + " |"


def overlay(rows: list[Row], study: dict[str, Any], spec: str) -> list[Row]:
    """Rows with the judge metrics of judge `spec` from a judge study of the same answers."""
    judge = next((j for j in study["judges"] if j["spec"] == spec), None)
    if judge is None:
        raise SystemExit(f"no judge {spec!r} in the study ({[j['spec'] for j in study['judges']]})")
    out = []
    for r in rows:
        graded = (judge["cases"].get(r["id"]) or {}).get("judgement")
        r = dict(r)
        if graded is None:
            for k in ("groundedness", "key_facts", "must_not_violations"):
                r[k] = None
            r["behaviour_ok"] = r.get("behaviour_det")
        else:
            j = Judgement(**graded)
            r["groundedness"] = groundedness(j)
            r["key_facts"] = key_fact_coverage(j)
            r["must_not_violations"] = sum(m.violated for m in j.must_not)
            r["behaviour_ok"] = bool(r.get("behaviour_det")) and j.behaviour_ok
        out.append(r)
    return out


def tables(reports: list[tuple[str, dict[str, Any]]], subset: str) -> str:
    keep = SUBSETS[subset]
    rate = reports[0][1]["meta"]["pricing"]["usd_to_chf"]
    rows = [(label, [r for r in rep["cases"] if keep(r)]) for label, rep in reports]
    head = (
        "| config | n | errors | quote fidelity | halluc. | groundedness | key facts | "
        "must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |"
    )
    lines = [head, "|" + "---|" * 13]
    lines += [absolute_row(label, rs, rate) for label, rs in rows]
    base_label, base = rows[0]
    lines += [
        "",
        f"Paired differences to **{base_label}** (mean, 95% CI):",
        "",
        "| config | " + " | ".join(f"Δ {m[0]}" for m in PAIRED) + " |",
        "|" + "---|" * (len(PAIRED) + 1),
    ]
    lines += [paired_row(label, base, rs, rate) for label, rs in rows[1:]]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--report", action="append", required=True, help="LABEL=path (first: base)")
    ap.add_argument("--subset", choices=tuple(SUBSETS), default="golden")
    ap.add_argument("--study", action="append", default=[], help="LABEL=judge-study.json")
    ap.add_argument("--judge", default=None, help="judge spec to take from the studies")
    args = ap.parse_args(argv)
    studies = {}
    for spec in args.study:
        label, _, path = spec.partition("=")
        studies[label] = json.loads(Path(path).read_text(encoding="utf-8"))
    if studies and not args.judge:
        ap.error("--study needs --judge")
    reports = []
    for spec in args.report:
        label, _, path = spec.partition("=")
        rep = json.loads(Path(path).read_text(encoding="utf-8"))
        if studies:
            if label not in studies:
                ap.error(f"no --study for {label!r}")
            rep = rep | {"cases": overlay(rep["cases"], studies[label], args.judge)}
        reports.append((label, rep))
    print(tables(reports, args.subset), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
