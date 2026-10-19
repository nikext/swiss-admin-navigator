"""Score earlier-stopping verifier policies from one recorded run (M8, E6; ADR-034).

The verifier policies are nested: with the claim checker on, the agent behaves
exactly like the deterministic-only verifier until the claim checker first
sends a draft back, and that one behaves like no verifier at all until the
deterministic check first sends a draft back. Every model call before that
point gets the same input, so the prefix of a recorded trajectory *is* a
sample of the cheaper policy. The `RoundRecorder` logs each checked draft
with the agent's usage, the tool calls and the elapsed time at that moment,
so one run of the full policy also yields, paired case by case and without
extra agent calls:

- `none`: no verifier. The first draft as the model wrote it; cost and
  latency up to that draft (the check's own time is subtracted).
- `deterministic`: navigator_v1's verifier (ADR-018: one redraft). The first
  draft without deterministic problems, or else the second draft, finalised
  by the same `citecheck.finalize` as in the agent; the claim checker's
  verdicts, time and tokens are left out.

The derived answers are then re-checked and judged like any run; a derived
answer whose judged content equals the recorded final answer reuses its
judgement. `python -m evals.harness.derive --from <report.json> --policy none`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from contextlib import ExitStack
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from pydantic import ValidationError

from agents.navigator.agent import profile
from agents.navigator.citecheck import check_citations as agent_check
from agents.navigator.citecheck import finalize, normalize
from agents.navigator.contract import DraftAnswer, Round
from evals.harness.agent_run import Trace, Usage
from evals.harness.answer_eval import (
    PRICING,
    case_row,
    render_markdown,
    summarize,
)
from evals.harness.answer_metrics import check_citations, cost_usd
from evals.harness.cases import Case, load_dataset
from evals.harness.judge import Judge, Judgement, payload
from evals.harness.law import LawClient, local_server
from evals.harness.retrieval_eval import git_sha

Policy = Literal["none", "deterministic"]
POLICIES: tuple[Policy, ...] = ("none", "deterministic")
NOT_DETERMINISTIC = {"unsupported", "fetch"}  # claim-checker and infrastructure problems


def det_problems(entry: dict[str, Any]) -> list[dict[str, Any]]:
    return [p for p in entry["round"]["problems"] if p["kind"] not in NOT_DETERMINISTIC]


def stop_index(log: list[dict[str, Any]], policy: Policy) -> int | None:
    """The logged round at which `policy` would have answered; None if the recorded run
    ended before reaching it (an error or timeout the cheaper policy would have hit too)."""
    if not log:
        return None
    if policy == "none":
        return 0
    k = 0 if not det_problems(log[0]) else 1  # one redraft for deterministic problems
    return k if k < len(log) else None


def as_deterministic(entry: dict[str, Any]) -> Round:
    """A logged round as the deterministic-only verifier would have recorded it."""
    r = dict(entry["round"])
    r["problems"] = [p for p in r["problems"] if p["kind"] != "unsupported"]
    r.update(claims=None, claims_s=None, claims_usage=None)
    return Round(**r)


def latency_at(entry: dict[str, Any], policy: Policy) -> float:
    """Elapsed time when `policy` would have answered with this round's draft."""
    claims_s = entry["round"].get("claims_s") or 0.0
    check_s = entry["round"].get("check_s") or 0.0
    return entry["t_s"] - claims_s - (check_s if policy == "none" else 0.0)


def judged_content(answer: dict[str, Any] | None) -> Any:
    """What the judge sees, normalised as the quote check does (enrichment ignored)."""
    if not answer:
        return None
    keys = ("answer_markdown", "clarifying_question", "cantonal_note", "out_of_scope")
    cites = [
        (c.get("ref"), c.get("sr"), c.get("article"), c.get("paragraph"), c.get("letter"),
         normalize(c.get("quote") or ""), c.get("translation"))
        for c in answer.get("citations") or []
    ]  # fmt: skip
    return [answer.get(k) for k in keys], cites


async def derive_answer(
    log: list[dict[str, Any]], k: int, policy: Policy, law: LawClient
) -> tuple[dict[str, Any] | None, str | None]:
    """The answer `policy` would have given at round k, or an error."""
    text = log[k]["draft"]
    try:
        draft = DraftAnswer.model_validate_json(text)
    except ValidationError:
        if policy == "none":
            try:
                return json.loads(text), None  # what a client would have received
            except json.JSONDecodeError as exc:
                return None, f"final answer is not JSON: {exc}"
        return None, "final answer is not a valid DraftAnswer after the last round"
    if policy == "none":
        return draft.model_dump() | {"verification": None}, None
    checked, answer_problems = await agent_check(draft, law.get_article)
    rounds = [as_deterministic(e) for e in log[: k + 1]]
    return finalize(draft, checked, answer_problems, rounds).model_dump(), None


async def derive(
    report: dict[str, Any], cases: dict[str, Case], policy: Policy, url: str, judge: Judge | None
) -> list[dict[str, Any]]:
    pricing = yaml.safe_load(PRICING.read_text(encoding="utf-8"))
    sem = asyncio.Semaphore(4)
    async with LawClient(url) as law:

        async def one(row: dict[str, Any]) -> dict[str, Any]:
            case = cases[row["id"]]
            log = row.get("rounds_log") or []
            k = stop_index(log, policy)
            trace = Trace(case.id, route=row.get("route"))
            trace.router_usage = Usage(**row.get("router_usage") or {})
            if k is None:
                trace.error = row["error"] or "no recorded draft"
                trace.usage = Usage(**row["usage"])
                trace.latency_s = row["latency_s"]
            else:
                entry = log[k]
                trace.answer, trace.error = await derive_answer(log, k, policy, law)
                trace.usage = Usage(**entry["usage"])
                trace.latency_s = latency_at(entry, policy)
                trace.tool_calls = row["tool_trace"][: entry["tool_calls"]]
                trace.rounds_log = log[: k + 1]
            checks = await check_citations(trace.answer or {}, law.get_article)
            judgement = None
            reuse = bool(trace.answer) and same_judged_content(row, trace.answer)
            if reuse:
                judgement = Judgement(**row["judgement"])
            elif trace.answer and judge is not None:
                cited = [
                    {"ref": c.ref, "sr": c.sr, "article": c.article, "lang": c.quote_lang,
                     "text": c.text}
                    for c in checks
                    if c.text
                ]  # fmt: skip
                async with sem:
                    judgement = await judge.grade(payload(case, trace.answer, cited))
            out = case_row(case, trace, checks, judgement, pricing)
            rejudged = judgement is not None and not reuse
            out["derived"] = {"policy": policy, "stop_round": k, "rejudged": rejudged}
            return out

        return list(await asyncio.gather(*(one(r) for r in report["cases"])))


def same_judged_content(row: dict[str, Any], answer: dict[str, Any] | None) -> bool:
    """True when the recorded row was judged on the same content (its judgement holds)."""
    return bool(row.get("judgement")) and judged_content(answer) == judged_content(row["answer"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--from", dest="from_", type=Path, required=True, help="a recorded report")
    ap.add_argument("--policy", choices=POLICIES, required=True)
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--name", default=None)
    ap.add_argument("--out", type=Path, default=Path("evals/reports"))
    args = ap.parse_args(argv)
    load_dotenv(".env")
    report = json.loads(args.from_.read_text(encoding="utf-8"))
    if not any(r.get("rounds_log") for r in report["cases"]):
        raise SystemExit("the report has no rounds_log (recorded before M8, or a remote run)")
    dataset = load_dataset(report["meta"]["dataset"]["spec"])
    cases = {c.id: c for c in dataset.cases}
    judged = report["meta"]["judged"] and not args.no_judge
    judge = Judge(profile.judge, os.environ.get("GOOGLE_CLOUD_PROJECT", "")) if judged else None
    with ExitStack() as stack:
        url = stack.enter_context(local_server(Path("data/logs/derive-mcp-server.log")))
        rows = asyncio.run(derive(report, cases, args.policy, url, judge))
    pricing = yaml.safe_load(PRICING.read_text(encoding="utf-8"))
    summary = summarize(rows, judged, judge.usage if judge else Usage(), pricing)
    if judge is not None:
        summary["run_cost_chf"]["judge"] = (
            cost_usd(profile.judge.model, judge.usage, pricing) or 0.0
        ) * pricing["usd_to_chf"]
    meta = dict(report["meta"])
    meta["derived"] = {
        "from": args.from_.name,
        "policy": args.policy,
        "rejudged": sum(r["derived"]["rejudged"] for r in rows),
        "judge_usage": asdict(judge.usage) if judge else None,
    }
    meta["judged"] = judged
    name = args.name or f"{report['name']}-derived-{args.policy}"
    out = {
        "name": name,
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": git_sha(),
        "summary": summary,
        "cases": rows,
        "meta": meta,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.out / f"{datetime.now(UTC):%Y-%m-%d}-{out['git_sha']}-{name}"
    stem.with_suffix(".json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    stem.with_suffix(".md").write_text(render_markdown(out), encoding="utf-8")
    print(f"wrote {stem}.md/.json ({meta['derived']['rejudged']} answers re-judged)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
