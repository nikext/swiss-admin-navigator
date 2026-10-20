"""CI gates over eval reports (docs/EVALS.md §3).

    uv run python -m evals.harness.gate --retrieval R.json --answers A.json

Checks the reports against `evals/baselines.yaml`:
- retrieval: recall@8 of the served config may drop at most `max_drop_pts`
  points below the committed baseline;
- answers (smoke): quote fidelity at least `quote_fidelity_min` (100%), at most
  `hallucinated_max` hallucinated citations (0), at most `errors_max` agent
  errors, and at least one quote checked (an all-error run must not pass).

Prints a Markdown summary (also appended to $GITHUB_STEP_SUMMARY when set),
including cost, and exits 1 if any gate fails.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

BASELINES = Path("evals/baselines.yaml")


@dataclass
class Check:
    name: str
    value: str
    limit: str
    ok: bool


def retrieval_checks(report: dict[str, Any], base: dict[str, Any]) -> list[Check]:
    served = report["results"][0]
    recall = served["summary"]["recall@8"]["mean"]
    floor = base["recall_at_8"] - base["max_drop_pts"] / 100
    limit = (
        f"≥ {100 * floor:.1f} (baseline {100 * base['recall_at_8']:.1f} − {base['max_drop_pts']})"
    )
    return [
        Check(
            f"retrieval recall@8 ({report['n_cases']} queries)",
            f"{100 * recall:.1f}",
            limit,
            recall >= floor - 1e-9,
        )
    ]


def answer_checks(report: dict[str, Any], base: dict[str, Any]) -> list[Check]:
    s = report["summary"]
    qf, hc = s["quote_fidelity"], s["hallucinated_citations"]
    rate = qf["rate"]
    return [
        Check(
            "quote fidelity",
            "–" if rate is None else f"{100 * rate:.1f}% ({qf['verbatim']}/{qf['quotes']})",
            f"≥ {100 * base['quote_fidelity_min']:.0f}%, at least one quote",
            rate is not None and qf["quotes"] > 0 and rate >= base["quote_fidelity_min"],
        ),
        Check(
            "hallucinated citations",
            f"{hc['count']} of {hc['citations']}",
            f"≤ {base['hallucinated_max']}",
            hc["count"] <= base["hallucinated_max"],
        ),
        Check(
            f"agent errors ({s['cases']} cases)",
            str(s["errors"]),
            f"≤ {base['errors_max']}",
            s["errors"] <= base["errors_max"],
        ),
    ]


def cost_line(report: dict[str, Any]) -> str:
    s = report["summary"]
    run = s["run_cost_chf"]
    agent, judge = run.get("agent") or 0.0, run.get("judge") or 0.0
    per, p50 = s["cost_per_answer"]["chf"], s["latency_s"]["p50"]  # None when every case errored
    return (
        f"cost: CHF {agent + judge:.3f} (agent {agent:.3f}, judge {judge:.3f}); "
        f"CHF {'–' if per is None else f'{per:.4f}'} per answer; "
        f"latency p50 {'–' if p50 is None else f'{p50:.0f}'} s"
    )


def render(checks: list[Check], notes: list[str]) -> str:
    lines = ["## Eval gates", "", "| gate | value | limit | |", "|---|---|---|---|"]
    lines += [f"| {c.name} | {c.value} | {c.limit} | {'✅' if c.ok else '❌'} |" for c in checks]
    return "\n".join(lines + [""] + [f"- {n}" for n in notes]) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--retrieval", type=Path)
    ap.add_argument("--answers", type=Path)
    ap.add_argument("--baselines", type=Path, default=BASELINES)
    args = ap.parse_args(argv)
    if not (args.retrieval or args.answers):
        ap.error("give --retrieval and/or --answers")
    base = yaml.safe_load(args.baselines.read_text(encoding="utf-8"))
    checks: list[Check] = []
    notes: list[str] = []
    if args.retrieval:
        checks += retrieval_checks(json.loads(args.retrieval.read_text()), base["retrieval"])
    if args.answers:
        report = json.loads(args.answers.read_text())
        checks += answer_checks(report, base["answers"])
        notes.append(cost_line(report))
        if not report["meta"]["dataset"]["verified"]:
            notes.append("dataset includes unverified drafts: not a headline number")
    out = render(checks, notes)
    print(out)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a", encoding="utf-8") as f:
            f.write(out)
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
