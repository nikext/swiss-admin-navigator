"""Multi-turn eval with ADK user simulation (docs/EVALS.md §1-2, `adk eval`).

    make eval-multiturn                         # all 25 conversations (billable, ~CHF 3)
    make eval-multiturn ARGS="--ids mt-01,mt-22"

Runs `evals/datasets/multiturn.evalset.json` (ADK EvalSet; each case is a
ConversationScenario with per-case rubrics) through ADK's AgentEvaluator: an
LLM-backed user simulator plays the user, navigator_v1 answers over a local
MCP server, and `rubric_based_multi_turn_trajectory_quality_v1` judges the
whole conversation against the rubrics (binary per rubric, score = mean).

The EvalConfig is built here from the profile (ADR-008): the simulator uses
the agent model, the rubric judge the judge model. Both run on the judge's
endpoint location, set as GOOGLE_CLOUD_LOCATION for this process because ADK
builds them from model names; the agent keeps its own location (ADR-013).
Writes `evals/reports/<date>-<sha>-multiturn.{json,md}` with each rubric
verdict and its rationale, the transcript, and the agent's token usage.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import socket
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

MULTITURN = Path("evals/datasets/multiturn.evalset.json")
REPORTS = Path("evals/reports")
PRICING = Path("evals/pricing.yaml")
METRIC = "rubric_based_multi_turn_trajectory_quality_v1"
STATUS: dict[object, str] = {1: "passed", 2: "failed", 3: "not_evaluated"}  # ADK EvalStatus
APP = "navigator"


def eval_config(sim_model: str, judge_model: str, threshold: float, max_turns: int) -> Any:
    from google.adk.evaluation.eval_config import EvalConfig
    from google.adk.evaluation.eval_metrics import JudgeModelOptions, RubricsBasedCriterion
    from google.adk.evaluation.simulation.llm_backed_user_simulator import (
        LlmBackedUserSimulatorConfig,
    )
    from google.genai import types

    return EvalConfig(
        criteria={
            METRIC: RubricsBasedCriterion(
                threshold=threshold,
                judge_model_options=JudgeModelOptions(judge_model=judge_model, num_samples=1),
            )
        },
        user_simulator_config=LlmBackedUserSimulatorConfig(
            model=sim_model,
            model_configuration=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW)
            ),
            max_allowed_invocations=max_turns,
        ),
    )


def text_of(content: dict[str, Any] | None) -> str:
    parts = (content or {}).get("parts") or []
    return "".join(p.get("text") or "" for p in parts if not p.get("thought"))


def agent_reply(raw: str) -> str:
    """The user-facing part of a final answer (the agent replies in JSON)."""
    try:
        a = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if not isinstance(a, dict):
        return raw
    bits = [a.get("answer_markdown") or ""]
    if a.get("clarifying_question"):
        bits.append(f"[asks] {a['clarifying_question']}")
    if a.get("cantonal_note"):
        bits.append(f"[cantonal] {a['cantonal_note']}")
    refs = [f"{c.get('abbr') or c.get('sr')} {c.get('article')}" for c in a.get("citations") or []]
    if refs:
        bits.append("[cites] " + ", ".join(refs))
    return "\n".join(b for b in bits if b)


def summarize_case(case: dict[str, Any], rubrics: dict[str, str]) -> dict[str, Any]:
    """One EvalCaseResult (`model_dump()`, snake_case) → the report row."""
    overall = {m["metric_name"]: m for m in case.get("overall_eval_metric_results") or []}
    rubric_metric = overall.get(METRIC, {})
    per_inv = case.get("eval_metric_result_per_invocation") or []
    verdicts: list[dict[str, Any]] = []
    transcript, tokens = [], Counter()
    for inv in per_inv:
        actual = inv.get("actual_invocation") or {}
        transcript.append(
            {
                "user": text_of(actual.get("user_content")),
                "agent": agent_reply(text_of(actual.get("final_response"))),
            }
        )
        for m in inv.get("eval_metric_results") or []:
            details = m.get("details") or {}
            if m["metric_name"] == METRIC and details.get("rubric_scores"):
                verdicts = [
                    {
                        "rubric_id": r["rubric_id"],
                        "rubric": rubrics.get(r["rubric_id"], ""),
                        "score": r.get("score"),
                        "rationale": r.get("rationale"),
                    }
                    for r in details["rubric_scores"]
                ]
            if m["metric_name"] == "token_usage_v1" and details.get("token_usage_details"):
                tokens.update({k: v or 0 for k, v in details["token_usage_details"].items()})
    status = case.get("final_eval_status")
    return {
        "id": case["eval_id"],
        "status": STATUS.get(status, str(status)),
        "score": rubric_metric.get("score"),
        "turns": len(transcript),
        "rubrics": verdicts,
        "transcript": transcript,
        "tokens": dict(tokens),
    }


def agent_cost_chf(tokens: dict[str, int], model: str, pricing: dict[str, Any]) -> float | None:
    p = pricing["models"].get(model)
    if p is None or not tokens:
        return None
    prompt, cached = tokens.get("prompt_tokens", 0), tokens.get("cached_tokens", 0)
    output = tokens.get("candidates_tokens", 0) + tokens.get("reasoning_tokens", 0)
    usd = ((prompt - cached) * p["input"] + cached * p.get("cached_input", p["input"])) / 1e6
    return (usd + output * p["output"] / 1e6) * pricing["usd_to_chf"]


def render(report: dict[str, Any]) -> str:
    s, rows, agent = report["summary"], report["cases"], report["profile"]["agent"]
    lines = [
        "# Multi-turn eval (ADK user simulation)",
        "",
        f"- dataset: `{report['dataset']}` ({s['cases']} conversations; drafted by Claude, "
        "not human-verified: not a headline number)",
        f"- agent: `{agent['model']}@{agent['location']}`; "
        f"user simulator `{report['simulator']}`; rubric judge `{report['judge']}` "
        f"(`{METRIC}`, 1 sample, threshold {report['threshold']})",
        f"- run: {report['run_at']} at {report['git_sha']}; google-adk {report['adk']}",
        "",
        "## Summary",
        "",
        f"- passed: **{s['passed']}/{s['cases']}**; mean rubric score **{s['mean_score']:.2f}**; "
        f"rubrics met {s['rubrics_met']}/{s['rubrics']}",
        f"- turns per conversation (mean): {s['mean_turns']:.1f}; agent cost CHF "
        f"{s['agent_cost_chf']:.3f} (simulator and judge not included)",
        "",
        "| id | status | score | turns | rubrics not met |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        missed = [v["rubric_id"].rsplit("-", 1)[-1] for v in r["rubrics"] if v["score"] != 1.0]
        score = "–" if r["score"] is None else f"{r['score']:.2f}"
        lines.append(
            f"| {r['id']} | {r['status']} | {score} | {r['turns']} | {', '.join(missed) or '–'} |"
        )
    lines += ["", "## Rubrics not met", ""]
    for r in rows:
        for v in r["rubrics"]:
            if v["score"] != 1.0:
                lines.append(f"- `{v['rubric_id']}` {v['rubric']} — judge: {v['rationale']}")
    return "\n".join(lines) + "\n"


async def run(args: argparse.Namespace, url: str) -> dict[str, Any]:
    # Imported only now: importing agents.navigator builds root_agent from SWISS_LAW_MCP_URL.
    from google.adk.evaluation.agent_evaluator import AgentEvaluator
    from google.adk.evaluation.eval_result import EvalSetResult
    from google.adk.evaluation.eval_set import EvalSet
    from google.adk.evaluation.local_eval_set_results_manager import LocalEvalSetResultsManager

    from agents.navigator.config import load_profile

    profile = load_profile()
    # Simulator + judge are built by ADK from model names, on GOOGLE_CLOUD_LOCATION.
    os.environ["GOOGLE_CLOUD_LOCATION"] = profile.judge.location
    eval_set = EvalSet.model_validate_json(args.dataset.read_text(encoding="utf-8"))
    if args.ids:
        wanted = set(args.ids.split(","))
        eval_set.eval_cases = [c for c in eval_set.eval_cases if c.eval_id in wanted]
    if args.limit:
        eval_set.eval_cases = eval_set.eval_cases[: args.limit]
    rubrics = {
        r.rubric_id: r.rubric_content.text_property or ""
        for c in eval_set.eval_cases
        for r in c.rubrics or []
    }
    config = eval_config(profile.agent.model, profile.judge.model, args.threshold, args.max_turns)
    with tempfile.TemporaryDirectory() as tmp:
        print(f"running {len(eval_set.eval_cases)} simulated conversations against {url}")
        # Failed cases raise AssertionError; their results are saved all the same.
        with contextlib.suppress(AssertionError):
            await AgentEvaluator.evaluate_eval_set(
                agent_module="agents.navigator",
                eval_set=eval_set,
                eval_config=config,
                num_runs=1,
                print_detailed_results=False,
                eval_set_results_manager=LocalEvalSetResultsManager(agents_dir=tmp),
                app_name=APP,
            )
        files = sorted(Path(tmp).rglob("*.evalset_result.json"))
        if not files:
            raise SystemExit("ADK wrote no eval results")
        text = files[-1].read_text(encoding="utf-8")
        if text.startswith('"'):  # the results manager stores the JSON as a JSON string
            text = json.loads(text)
        result = EvalSetResult.model_validate_json(text).model_dump(mode="json")
    rows = [summarize_case(c, rubrics) for c in result["eval_case_results"]]
    rows.sort(key=lambda r: r["id"])
    return {"profile": profile.as_dict(), "rows": rows}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--dataset", type=Path, default=MULTITURN)
    ap.add_argument("--ids", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--threshold", type=float, default=0.75)
    ap.add_argument("--max-turns", type=int, default=5)
    ap.add_argument("--out", type=Path, default=REPORTS)
    args = ap.parse_args(argv)
    load_dotenv(".env")
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        raise SystemExit("GOOGLE_CLOUD_PROJECT is not set (copy .env.example to .env)")
    # Fix the MCP server's URL before anything imports the agent package: importing
    # agents.navigator (also indirectly, e.g. via law or retrieval_eval) builds root_agent.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    os.environ["SWISS_LAW_MCP_URL"] = f"http://127.0.0.1:{port}/mcp"

    from importlib.metadata import version

    from evals.harness.law import local_server
    from evals.harness.retrieval_eval import git_sha

    with local_server(Path("data/logs/multiturn-mcp-server.log"), port=port) as url:
        result = asyncio.run(run(args, url))
    rows, profile = result["rows"], result["profile"]
    pricing = yaml.safe_load(PRICING.read_text(encoding="utf-8"))
    costs = [agent_cost_chf(r["tokens"], profile["agent"]["model"], pricing) for r in rows]
    scores = [r["score"] for r in rows if r["score"] is not None]
    verdicts = [v for r in rows for v in r["rubrics"]]
    report = {
        "name": "multiturn",
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": git_sha(),
        "dataset": str(args.dataset),
        "adk": version("google-adk"),
        "profile": profile,
        "simulator": f"{profile['agent']['model']}@{profile['judge']['location']}",
        "judge": f"{profile['judge']['model']}@{profile['judge']['location']}",
        "threshold": args.threshold,
        "summary": {
            "cases": len(rows),
            "passed": sum(r["status"] == "passed" for r in rows),
            "mean_score": sum(scores) / len(scores) if scores else 0.0,
            "rubrics": len(verdicts),
            "rubrics_met": sum(v["score"] == 1.0 for v in verdicts),
            "mean_turns": sum(r["turns"] for r in rows) / max(len(rows), 1),
            "agent_cost_chf": sum(c for c in costs if c is not None),
        },
        "cases": rows,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.out / f"{datetime.now(UTC):%Y-%m-%d}-{report['git_sha']}-multiturn"
    stem.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    stem.with_suffix(".md").write_text(render(report), encoding="utf-8")
    s = report["summary"]
    print(f"passed {s['passed']}/{s['cases']}, mean score {s['mean_score']:.2f}")
    print(f"wrote {stem}.md/.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
