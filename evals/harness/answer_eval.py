"""End-to-end answer eval of navigator_v1 (docs/EVALS.md §2-3).

    uv run python -m evals.harness.answer_eval --smoke          # make eval-smoke
    uv run python -m evals.harness.answer_eval                  # golden + all draft batches
    uv run python -m evals.harness.answer_eval --dataset all+adversarial   # the full eval
    uv run python -m evals.harness.answer_eval --ids work-01,housing-02 --no-judge
    uv run python -m evals.harness.answer_eval --smoke --target remote   # make eval-smoke-remote
    uv run python -m evals.harness.answer_eval --dataset golden --from A.json --from B.json

Runs each case through the agent (the local ADK runner, or with `--target
remote` the deployed agent on Agent Runtime, `AGENT_RUNTIME_ID`), re-checks
every final citation against the law over MCP, asks the judge (profile `judge` role) for
groundedness, key facts, must_not and behaviour, and writes
`evals/reports/<date>-<sha>-<name>.{json,md}`. By default it starts its own
MCP server from this checkout (needs `data/index.sqlite`); `--mcp-url` uses a
running one instead. Costs money: model calls for the agent and the judge.

`--traces FILE` appends each finished case's trace to FILE (JSONL); rerunning
with the same FILE skips the cases stored there, so a run cut off by a crash or
shutdown resumes instead of starting over (the judge then grades every case).

`--from` re-scores stored reports instead (no model calls): rows are merged by
case id, later reports win (so a rerun of errored cases replaces them), and
only cases of `--dataset` (and the usual selection) are kept.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from agents.navigator.agent import TOOLS, build_agent, claim_check_enabled, new_toolset, profile
from agents.navigator.armor import InputScreen
from agents.navigator.claims import PROMPT_PATH as CLAIM_PROMPT
from agents.navigator.contact import answer_contact_details
from agents.navigator_v2.agent import PROMPTS as V2_PROMPTS
from agents.navigator_v2.agent import build_workflow
from agents.navigator_v2.routing import dispatch
from evals.harness.agent_run import (
    LocalAgent,
    RoundRecorder,
    Target,
    Trace,
    TraceLog,
    Usage,
    run_cases,
)
from evals.harness.answer_metrics import (
    CitationCheck,
    as_dicts,
    behaviour_ok,
    check_citations,
    citation_scores,
    cost_usd,
    detect_lang,
    mean,
    percentile,
    ratio_ci,
)
from evals.harness.cases import Case, Dataset, load_dataset
from evals.harness.judge import (
    Judge,
    Judgement,
    groundedness,
    key_fact_coverage,
    payload,
    prompt_sha,
)
from evals.harness.law import LawClient, local_server
from evals.harness.remote_run import RemoteAgent
from evals.harness.retrieval_eval import git_sha
from evals.harness.retrieval_metrics import bootstrap_ci

REPORTS = Path("evals/reports")
PRICING = Path("evals/pricing.yaml")
SYSTEM_PROMPT = Path("agents/navigator/prompts/system.md")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def tree_sha(root: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(root.rglob("*.md")):
        h.update(f.relative_to(root).as_posix().encode() + b"\0" + f.read_bytes())
    return h.hexdigest()[:12]


def claims_usage(rounds: list[dict[str, Any]]) -> Usage:
    """The claim checker's token usage over a verification record's rounds."""
    total = Usage()
    for r in rounds:
        u = r.get("claims_usage")
        if u:
            total.model_calls += u.get("model_calls", 0)
            total.prompt += u.get("prompt", 0)
            total.cached += u.get("cached", 0)
            total.output += u.get("output", 0)
            total.thoughts += u.get("thoughts", 0)
    return total


def run_cost_usd(
    trace: Trace, rounds: list[dict[str, Any]], pricing: dict[str, Any]
) -> float | None:
    """Agent + router + claim checker, each at its profile model's price."""
    parts = [
        (profile.agent.model, trace.usage),
        (profile.role("router").model, trace.router_usage),
        (profile.role("verifier").model, claims_usage(rounds)),
    ]
    total = 0.0
    for model, usage in parts:
        if usage.model_calls == 0:
            continue
        cost = cost_usd(model, usage, pricing)
        if cost is None:
            return None
        total += cost
    return total


def claim_stats(rounds: list[dict[str, Any]]) -> dict[str, Any]:
    """What the claim checker said: verdicts of the first checked round, rounds it ran."""
    checked = [r for r in rounds if r.get("claims") is not None]
    first = checked[0]["claims"] if checked else []
    return {
        "rounds": len(checked),
        "first": dict(Counter(c["supported"] for c in first)),
        "sent_back": sum(
            any(p["kind"] == "unsupported" for p in r.get("problems", [])) for r in rounds[:-1]
        ),
    }


def select(cases: list[Case], args: argparse.Namespace) -> list[Case]:
    if args.ids:
        wanted = args.ids.split(",")
        missing = set(wanted) - {c.id for c in cases}
        if missing:
            raise SystemExit(f"unknown case ids: {sorted(missing)}")
        cases = [c for c in cases if c.id in wanted]
    if args.smoke:
        cases = [c for c in cases if c.smoke]
    if args.category:
        cases = [c for c in cases if c.category == args.category]
    return cases[: args.limit] if args.limit else cases


def case_row(
    case: Case,
    trace: Trace,
    checks: list[CitationCheck],
    judgement: Judgement | None,
    pricing: dict[str, Any],
) -> dict[str, Any]:
    answer = trace.answer or {}
    verification = answer.get("verification") or {}
    rounds = verification.get("rounds") or []
    first = rounds[0] if rounds else {}
    hallucinated = sum(c.exists is False for c in checks)
    det = behaviour_ok(case, answer, hallucinated) if trace.answer else False
    detected = detect_lang(answer.get("answer_markdown") or "") if trace.answer else None
    lang_ok = answer.get("language") == case.lang and detected == case.lang
    cost = run_cost_usd(trace, rounds, pricing)
    routed = dispatch(trace.route) if trace.route is not None else None
    row: dict[str, Any] = {
        "id": case.id, "lang": case.lang, "category": case.category, "domain": case.domain,
        "error": trace.error,
        "status": verification.get("status"),
        "rounds": len(rounds),
        "first_draft": {
            "citations": first.get("citations", 0),
            "quotes": first.get("quotes", 0),
            "problems": dict(Counter(p["kind"] for p in first.get("problems", []))),
        },
        "dropped": verification.get("dropped", []),
        "repairs": verification.get("repairs", []),
        "dropped_claims": verification.get("dropped_claims", []),
        "claim_check": claim_stats(rounds),
        "route": trace.route,
        "routed_to": routed,
        "route_ok": None if routed is None else routed == case.domain,
        "citations": len(checks),
        "quotes": sum(c.has_quote for c in checks),
        "verbatim": sum(c.verbatim is True for c in checks),
        "hallucinated": hallucinated,
        "not_in_force": sum(c.in_force is False for c in checks),
        "unchecked": sum(c.exists is None for c in checks),
        **citation_scores(case, checks),
        "behaviour_det": det,
        "contact_details": [f"{k}: {v}" for k, v in answer_contact_details(answer)],
        "detected_lang": detected,
        "lang_ok": lang_ok,
        "tool_calls": len(trace.tool_calls),
        "tools": dict(Counter(t["name"] for t in trace.tool_calls)),
        "usage": asdict(trace.usage),
        "router_usage": asdict(trace.router_usage),
        "claims_usage": asdict(claims_usage(rounds)),
        "latency_s": round(trace.latency_s, 2),
        "cost_usd": round(cost, 5) if cost is not None else None,
    }  # fmt: skip
    if judgement is not None:
        irrelevant = set(judgement.irrelevant_refs)
        expected = {(e.sr, e.eid) for e in case.expected_citations}
        real = [c for c in checks if c.exists]
        relevant = [c for c in real if (c.sr, c.eid) in expected or c.ref not in irrelevant]
        row |= {
            "groundedness": groundedness(judgement),
            "key_facts": key_fact_coverage(judgement),
            "must_not_violations": sum(m.violated for m in judgement.must_not),
            "behaviour_judge": judgement.behaviour_ok,
            "behaviour_ok": det and judgement.behaviour_ok,
            "precision_judged": len(relevant) / len(real) if real else None,
        }
    row |= {
        "answer": trace.answer,
        "raw_final": None if trace.answer else trace.raw_final,
        "tool_trace": trace.tool_calls,
        "rounds_log": trace.rounds_log,
        "citation_checks": as_dicts(checks),
        "judgement": judgement.model_dump() if judgement else None,
    }
    return row


def ci_mean(values: list[float | None]) -> dict[str, Any]:
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return {"mean": None, "ci95": None, "n": 0}
    return {"mean": statistics.fmean(vals), "ci95": list(bootstrap_ci(vals)), "n": len(vals)}


def summarize(rows: list[dict[str, Any]], judged: bool, judge_usage: Usage, pricing: dict) -> dict:
    ok = [r for r in rows if not r["error"]]
    rate = pricing["usd_to_chf"]
    s: dict[str, Any] = {"cases": len(rows), "errors": len(rows) - len(ok)}
    quotes, verbatim = [r["quotes"] for r in rows], [r["verbatim"] for r in rows]
    cites, halluc = [r["citations"] for r in rows], [r["hallucinated"] for r in rows]
    s["quote_fidelity"] = {
        "verbatim": sum(verbatim), "quotes": sum(quotes),
        "rate": sum(verbatim) / sum(quotes) if sum(quotes) else None,
        "ci95": ratio_ci(verbatim, quotes),
    }  # fmt: skip
    s["hallucinated_citations"] = {
        "count": sum(halluc), "citations": sum(cites),
        "rate": sum(halluc) / sum(cites) if sum(cites) else None,
        "ci95": ratio_ci(halluc, cites),
    }  # fmt: skip
    s["not_in_force_citations"] = sum(r["not_in_force"] for r in rows)
    s["unchecked_citations"] = sum(r["unchecked"] for r in rows)
    first_problems: Counter[str] = Counter()
    for r in rows:
        first_problems.update(r["first_draft"]["problems"])
    s["first_draft"] = {
        "citations": sum(r["first_draft"]["citations"] for r in rows),
        "quotes": sum(r["first_draft"]["quotes"] for r in rows),
        "problems": dict(first_problems),
        "cases_sent_back": sum(r["rounds"] > 1 for r in rows),
    }
    s["verification"] = dict(Counter(r["status"] or "none" for r in rows))
    s["dropped_citations"] = sum(len(r["dropped"]) for r in rows)
    cc = [r.get("claim_check") or {} for r in rows]
    first_verdicts: Counter[str] = Counter()
    for c in cc:
        first_verdicts.update(c.get("first", {}))
    s["claim_check"] = {
        "answers_checked": sum(bool(c.get("rounds")) for c in cc),
        "first_verdicts": dict(first_verdicts),
        "cases_sent_back": sum(bool(c.get("sent_back")) for c in cc),
        "dropped_claims": sum(len(r.get("dropped_claims") or []) for r in rows),
    }
    routed = [r for r in rows if r.get("routed_to") is not None]
    if routed:
        s["routing"] = {
            "accuracy": ci_mean([float(r["route_ok"]) for r in routed]),
            "to": dict(Counter(r["routed_to"] for r in routed)),
            "misses": sorted(
                f"{r['id']}: {r['domain']} -> {r['routed_to']}" for r in routed if not r["route_ok"]
            ),
        }
    s["required_recall"] = ci_mean([r["required_recall"] for r in ok])
    s["precision_expected"] = ci_mean([r["precision_expected"] for r in ok])
    s["behaviour_det"] = ci_mean([float(r["behaviour_det"]) for r in rows])
    s["contact_answers"] = sorted(r["id"] for r in ok if r.get("contact_details"))
    s["screened"] = sorted(r["id"] for r in ok if (r.get("answer") or {}).get("screening"))
    s["lang_match"] = ci_mean([float(r["lang_ok"]) for r in ok])
    if judged:
        s["groundedness"] = ci_mean([r.get("groundedness") for r in ok])
        s["key_facts"] = ci_mean([r.get("key_facts") for r in ok])
        s["must_not_violations"] = sum(r.get("must_not_violations", 0) for r in ok)
        s["behaviour"] = ci_mean([float(r.get("behaviour_ok", False)) for r in rows])
        s["precision_judged"] = ci_mean([r.get("precision_judged") for r in ok])
    lat = [r["latency_s"] for r in ok]
    costs = [r["cost_usd"] for r in ok if r["cost_usd"] is not None]
    s["latency_s"] = {"p50": percentile(lat, 0.5), "p95": percentile(lat, 0.95)}
    s["tool_calls_mean"] = mean([r["tool_calls"] for r in ok])
    s["model_calls_mean"] = mean([r["usage"]["model_calls"] for r in ok])
    s["tokens_mean"] = {
        k: mean([r["usage"][k] for r in ok]) for k in ("prompt", "cached", "output", "thoughts")
    }
    s["cost_per_answer"] = {
        "usd": mean(costs), "chf": (mean(costs) or 0) * rate,
        "p95_chf": (percentile(costs, 0.95) or 0) * rate,
    }  # fmt: skip
    s["run_cost_chf"] = {"agent": sum(costs) * rate}  # incl. router and claim checker
    s["usage_split"] = {
        k: mean([r.get(f"{k}_usage", {}).get("model_calls", 0) for r in ok])
        for k in ("router", "claims")
    }
    by: dict[str, Any] = {}
    for field in ("category", "lang"):
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            groups[r[field]].append(r)
        by[field] = {
            k: {
                "n": len(g),
                "behaviour": mean([float(r.get("behaviour_ok", r["behaviour_det"])) for r in g]),
                "groundedness": mean([r.get("groundedness") for r in g]),
                "key_facts": mean([r.get("key_facts") for r in g]),
                "lang_match": mean([float(r["lang_ok"]) for r in g]),
            }
            for k, g in sorted(groups.items())
        }
    s["by"] = by
    return s


def model_label(ref: dict[str, Any]) -> str:
    """model@location, plus the thinking level when the profile sets one."""
    label = f"{ref['model']}@{ref['location']}"
    return label + (f", thinking {ref['thinking']}" if ref.get("thinking") else "")


def fmt(x: float | None, digits: int = 1) -> str:
    return "–" if x is None else f"{100 * x:.{digits}f}"


def num(x: float | None) -> str:
    return "–" if x is None else f"{x:.1f}"


def fmt_ci(m: dict[str, Any]) -> str:
    if m.get("mean") is None:
        return "–"
    lo, hi = m["ci95"]
    return f"**{fmt(m['mean'])}** ({fmt(lo)}–{fmt(hi)}, n={m['n']})"


def verified_by(ds: dict[str, Any]) -> str:
    who = ds.get("verified_by") or []
    return f" by {', '.join(who)}" if who else ""


def rescored_note(meta: dict[str, Any]) -> list[str]:
    src = meta.get("rescored_from")
    if not src:
        return []
    return [f"- re-scored without model calls from {', '.join(f'`{x}`' for x in src)}"]


def target_note(meta: dict[str, Any]) -> list[str]:
    deployed = (meta.get("target") or {}).get("deployed")
    if not deployed:
        return []
    return [
        f"- target: **deployed** `{deployed['name']}` (commit "
        f"{deployed['labels'].get('commit', '?')}, updated {deployed['update_time']}, agent MCP "
        f"{deployed['env'].get('SWISS_LAW_MCP_URL', '?')}); latency includes the network and "
        "session creation"
    ]


def screen_note(meta: dict[str, Any], s: dict[str, Any]) -> list[str]:
    screen = (meta.get("agent") or {}).get("screen")
    if not screen:
        return []
    blocked = s.get("screened") or []
    return [
        f"- input screen (M10): Model Armor `{screen['template'].rsplit('/', 1)[-1]}`, "
        f"{screen['mode']} at {screen['min_level']}; blocked {len(blocked)}"
        + (f" ({', '.join(blocked)})" if blocked else "")
    ]


def render_markdown(report: dict[str, Any]) -> str:
    s, meta = report["summary"], report["meta"]
    qf, hc = s["quote_fidelity"], s["hallucinated_citations"]
    ds = meta["dataset"]
    lines = [
        f"# Answer eval: {report['name']}",
        "",
        f"- dataset: `{ds['spec']}` ({s['cases']} cases selected, "
        f"{ds['verified_cases']} verified{verified_by(ds)}; sha {ds['sha']} over "
        f"{', '.join(Path(f).name for f in ds['files'])})"
        + ("" if ds["verified"] else " — **includes drafts: not a headline number**"),
        *rescored_note(meta),
        f"- agent: `{model_label(meta['profile']['agent'])}`, "
        f"prompt sha {meta['system_prompt_sha']}, google-adk {meta['adk']}, structured output "
        f"{meta['output_mode']}",
        f"- judge: `{model_label(meta['profile']['judge'])}`, prompt sha {meta['judge_prompt_sha']}"
        if meta["judged"]
        else "- judge: off",
        *target_note(meta),
        *screen_note(meta, s),
        f"- law: {meta['mcp']['url']} (index as_of {meta['mcp']['health'].get('as_of')}, "
        f"built from {meta['mcp']['health'].get('index_sha')})",
        f"- run: {report['run_at']} at {report['git_sha']}; CIs are 95% percentile bootstraps "
        "over cases (2,000 resamples, seed 0)",
        "",
        "## Headline",
        "",
        "| metric | value |",
        "|---|---|",
        f"| quote fidelity (final answers) | **{fmt(qf['rate'])}%** "
        f"({qf['verbatim']}/{qf['quotes']}"
        + (f"; CI {fmt(qf['ci95'][0])}–{fmt(qf['ci95'][1])}" if qf["ci95"] else "")
        + ") |",
        f"| hallucinated citations | **{hc['count']}** of {hc['citations']} |",
        f"| required-citation recall | {fmt_ci(s['required_recall'])} |",
        f"| citation precision (expected only) | {fmt_ci(s['precision_expected'])} |",
    ]
    if meta["judged"]:
        lines += [
            "| citation precision (expected or judged relevant) | "
            f"{fmt_ci(s['precision_judged'])} |",
            f"| groundedness (judge, claim level) | {fmt_ci(s['groundedness'])} |",
            f"| key-fact coverage (judge) | {fmt_ci(s['key_facts'])} |",
            f"| must_not violations (judge) | **{s['must_not_violations']}** |",
            f"| behaviour accuracy (rule + judge) | {fmt_ci(s['behaviour'])} |",
        ]
    fd = s["first_draft"]
    lines += [
        f"| behaviour (rule only) | {fmt_ci(s['behaviour_det'])} |",
        "| answers with contact details (rule: address, postcode, phone, web) | "
        f"{len(s.get('contact_answers', []))}"
        f"{' (' + ', '.join(s['contact_answers']) + ')' if s.get('contact_answers') else ''} |",
        f"| language match | {fmt_ci(s['lang_match'])} |",
        f"| errors | {s['errors']} |",
        "",
        "## Verifier",
        "",
        f"- first drafts: {fd['citations']} citations, {fd['quotes']} quotes; problems "
        f"{fd['problems'] or 'none'}; {fd['cases_sent_back']} cases sent back once",
        f"- final status: {s['verification']}; citations dropped: {s['dropped_citations']}; "
        f"not in force: {s['not_in_force_citations']}; unchecked: {s['unchecked_citations']}",
        "",
        "## Cost and latency (agent only)",
        "",
        f"- per answer: CHF {s['cost_per_answer']['chf']:.4f} mean, "
        f"{s['cost_per_answer']['p95_chf']:.4f} p95 (USD→CHF {meta['pricing']['usd_to_chf']}, "
        f"prices as of {meta['pricing']['as_of']}); run: agent CHF "
        f"{s['run_cost_chf']['agent']:.3f}, judge CHF {s['run_cost_chf'].get('judge', 0):.3f}",
        f"- latency p50 {num(s['latency_s']['p50'])} s, p95 {num(s['latency_s']['p95'])} s; "
        f"{num(s['model_calls_mean'])} model calls and {num(s['tool_calls_mean'])} tool calls per "
        f"answer; tokens per answer (mean): "
        + ", ".join(f"{k} {v:,.0f}" for k, v in s["tokens_mean"].items() if v is not None),
        "",
        "## By category and language",
        "",
        "| group | n | behaviour | groundedness | key facts | language |",
        "|---|---|---|---|---|---|",
    ]
    for field, groups in s["by"].items():
        for k, g in groups.items():
            lines.append(
                f"| {field}: {k} | {g['n']} | {fmt(g['behaviour'], 0)} | "
                f"{fmt(g['groundedness'], 0)} | {fmt(g['key_facts'], 0)} | "
                f"{fmt(g['lang_match'], 0)} |"
            )
    lines += [
        "",
        "## Cases",
        "",
        "| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | "
        "behaviour | lang | s | CHF |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    rate = meta["pricing"]["usd_to_chf"]
    for r in report["cases"]:
        beh = r.get("behaviour_ok", r["behaviour_det"])
        lines.append(
            f"| {r['id']} | {r['error'] or r['status']} | {r['citations']} | "
            f"{r['verbatim']}/{r['quotes']} | {r['hallucinated']} | "
            f"{fmt(r['required_recall'], 0)} | "
            f"{fmt(r.get('groundedness'), 0)} | {fmt(r.get('key_facts'), 0)} | "
            f"{'ok' if beh else '**no**'} | {r['detected_lang']}{'' if r['lang_ok'] else ' ✗'} | "
            f"{r['latency_s']:.0f} | {(r['cost_usd'] or 0) * rate:.4f} |"
        )
    notes = []
    for r in report["cases"]:
        j = r.get("judgement") or {}
        issues = [f"behaviour: {j['behaviour_note']}"] if j and not r.get("behaviour_ok") else []
        issues += [
            f"unsupported: {c['claim']}" for c in j.get("claims", []) if c["supported"] == "no"
        ]
        issues += [
            f"missing fact: {f['fact']}" for f in j.get("key_facts", []) if f["verdict"] != "stated"
        ]
        issues += [
            f"must_not violated: {m['item']}" for m in j.get("must_not", []) if m["violated"]
        ]
        issues += [f"verifier: {x}" for x in r["repairs"]]
        if r["error"]:
            issues.insert(0, f"error: {r['error']}")
        if issues:
            notes.append(f"- `{r['id']}`: " + "; ".join(issues))
    lines += ["", "## Findings per case", "", *(notes or ["None."])]
    return "\n".join(lines) + "\n"


async def evaluate(
    args: argparse.Namespace, dataset: Dataset, cases: list[Case], url: str
) -> dict[str, Any]:
    pricing = yaml.safe_load(PRICING.read_text(encoding="utf-8"))
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    if not project:
        raise SystemExit("GOOGLE_CLOUD_PROJECT is not set (copy .env.example to .env)")

    target: Target
    if args.target == "remote":
        # The deployed agent uses its own MCP server (its env); `url` only serves the re-check.
        remote = RemoteAgent(
            args.agent_runtime or os.environ.get("AGENT_RUNTIME_ID", ""),
            project,
            os.environ.get("GOOGLE_CLOUD_LOCATION") or "europe-west6",
        )
        deployed = remote.describe()
        deployed_profile = deployed["env"].get("NAV_PROFILE") or "default"
        if deployed_profile != profile.name:  # cost and the report's model come from `profile`
            raise SystemExit(
                f"the deployed agent runs profile {deployed_profile!r}, this run {profile.name!r}"
            )
        target, where, output_mode = remote, remote.name, "deployed (not introspected)"
    else:
        recorder = RoundRecorder()
        probe = build_agent(url, claim_check=False)
        output_mode = (
            "native schema + tools"
            if probe.canonical_model.capabilities.output_schema_and_tools
            else "set_model_response tool"
        )
        tools = [t for t in TOOLS if t not in args.without_tool]
        root: Any = (
            build_workflow(url, claim_check=args.claim_check, observer=recorder)
            if args.agent == "v2"
            else build_agent(
                url,
                claim_check=args.claim_check,
                observer=recorder,
                toolset=new_toolset(url, tools) if args.without_tool else None,
            )
        )
        target, where, deployed = LocalAgent(root, recorder), url, None

    log = None
    if args.traces:
        setup = {
            "target": args.target,
            "agent": args.agent,
            "claim_check": bool(args.claim_check),
            "profile": profile.name,
            "case_timeout_s": args.case_timeout,
        }
        if args.without_tool:
            setup["without_tools"] = sorted(args.without_tool)
        if screen := InputScreen.from_env().as_dict():
            setup["screen"] = screen
        try:
            log = TraceLog(args.traces, setup)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    stored = {c.id: log.done[c.id] for c in cases if log and c.id in log.done}
    todo = [c for c in cases if c.id not in stored]

    def progress(case: Case, trace: Trace) -> None:
        status = (trace.answer or {}).get("verification", {}).get("status")
        print(f"  {case.id:<28} {trace.error or status:<20} {trace.latency_s:5.1f}s", flush=True)
        if log:
            log.append(trace)

    resumed = f", {len(stored)} resumed from {args.traces}" if stored else ""
    print(f"running {len(todo)} cases (concurrency {args.concurrency}) against {where}{resumed}")
    fresh = await run_cases(target, todo, args.concurrency, progress, args.case_timeout)
    by_id = stored | {t.case_id: t for t in fresh}
    traces = [by_id[c.id] for c in cases]

    judge = None if args.no_judge else Judge(profile.judge, project)
    sem = asyncio.Semaphore(args.concurrency)
    async with LawClient(url) as law:
        health = law.health()

        async def assess(case: Case, trace: Trace) -> dict[str, Any]:
            checks = await check_citations(trace.answer or {}, law.get_article)
            judgement = None
            if judge is not None and trace.answer:
                cited = [
                    {
                        "ref": c.ref,
                        "sr": c.sr,
                        "article": c.article,
                        "lang": c.quote_lang,
                        "text": c.text,
                    }
                    for c in checks
                    if c.text
                ]
                async with sem:
                    judgement = await judge.grade(payload(case, trace.answer, cited))
            return case_row(case, trace, checks, judgement, pricing)

        rows = list(
            await asyncio.gather(*(assess(c, t) for c, t in zip(cases, traces, strict=True)))
        )

    summary = summarize(rows, judge is not None, judge.usage if judge else Usage(), pricing)
    if judge is not None:
        judge_cost = cost_usd(profile.judge.model, judge.usage, pricing) or 0.0
        summary["run_cost_chf"]["judge"] = judge_cost * pricing["usd_to_chf"]
    return {
        "summary": summary,
        "cases": rows,
        "meta": {
            "dataset": {
                "spec": dataset.spec,
                "files": [str(f) for f in dataset.files],
                "sha": dataset.sha,
                "verified": all(c.verified_by for c in cases),
                "verified_cases": sum(bool(c.verified_by) for c in cases),
                "verified_by": sorted({c.verified_by for c in cases if c.verified_by}),
            },
            "case_timeout_s": args.case_timeout,
            "resumed_traces": len(stored),
            "selection": {
                "smoke": args.smoke,
                "ids": args.ids,
                "limit": args.limit,
                "category": args.category,
            },
            "profile": profile.as_dict(),
            "agent": {
                "variant": args.agent,
                "claim_check": bool(args.claim_check),
                "without_tools": sorted(args.without_tool),
                "router": asdict(profile.role("router")) if args.agent == "v2" else None,
                "verifier": asdict(profile.role("verifier")) if args.claim_check else None,
                "v2_prompts_sha": tree_sha(V2_PROMPTS) if args.agent == "v2" else None,
                "claim_prompt_sha": sha(CLAIM_PROMPT) if args.claim_check else None,
                "screen": InputScreen.from_env().as_dict() if args.target == "local" else None,
            },
            "system_prompt_sha": sha(SYSTEM_PROMPT),
            "judge_prompt_sha": prompt_sha(),
            "judged": judge is not None,
            "adk": version("google-adk"),
            "output_mode": output_mode,
            "target": {"kind": args.target, "deployed": deployed},
            "mcp": {
                "url": url if args.mcp_url else "local (started by the harness)",
                "health": health,
            },
            "pricing": {k: pricing[k] for k in ("as_of", "usd_to_chf")},
            "judge_usage": asdict(judge.usage) if judge else None,
        },
    }


def rescore(
    reports: list[dict[str, Any]], names: list[str], dataset: Dataset, cases: list[Case]
) -> dict[str, Any]:
    """A report over `cases` from stored rows; later reports override earlier ones by id."""
    rows: dict[str, dict[str, Any]] = {}
    origin: dict[str, int] = {}
    for i, rep in enumerate(reports):
        for row in rep["cases"]:
            rows[row["id"]] = row
            origin[row["id"]] = i
    missing = [c.id for c in cases if c.id not in rows]
    if missing:
        raise SystemExit(f"no stored row for {len(missing)} cases, e.g. {missing[:5]}")
    kept = [rows[c.id] for c in cases]
    pricing = yaml.safe_load(PRICING.read_text(encoding="utf-8"))
    judged = all(r["meta"]["judged"] for r in reports)
    summary = summarize(kept, judged, Usage(), pricing)
    if judged:  # judge cost is only stored per run: prorate by the rows taken from each
        share = Counter(origin[c.id] for c in cases)
        summary["run_cost_chf"]["judge"] = sum(
            (rep["summary"]["run_cost_chf"].get("judge") or 0) * share[i] / len(rep["cases"])
            for i, rep in enumerate(reports)
        )
    meta = dict(reports[-1]["meta"])
    meta["dataset"] = {
        "spec": dataset.spec,
        "files": [str(f) for f in dataset.files],
        "sha": dataset.sha,
        "verified": all(c.verified_by for c in cases),
        "verified_cases": sum(bool(c.verified_by) for c in cases),
        "verified_by": sorted({c.verified_by for c in cases if c.verified_by}),
    }
    meta["rescored_from"] = names
    return {"summary": summary, "cases": kept, "meta": meta}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument(
        "--dataset",
        default="all",
        help="all (golden + draft batches), golden, adversarial, a path; join with +",
    )
    ap.add_argument("--smoke", action="store_true", help="only cases marked smoke")
    ap.add_argument("--ids", default=None, help="comma-separated case ids")
    ap.add_argument("--category", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--case-timeout", type=float, default=300, help="seconds per case")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--mcp-url", default=None, help="use this MCP server instead of a local one")
    ap.add_argument(
        "--target",
        choices=("local", "remote"),
        default="local",
        help="local: ADK runner in this process; remote: the agent deployed on Agent Runtime",
    )
    ap.add_argument(
        "--agent-runtime", default=None, help="Agent Runtime id or name (default: AGENT_RUNTIME_ID)"
    )
    ap.add_argument(
        "--agent",
        choices=("v1", "v2"),
        default="v1",
        help="local target: navigator_v1 (one agent) or navigator_v2 (router + specialists, M8)",
    )
    ap.add_argument(
        "--claim-check",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="local target: add the LLM claim checker to the verifier (default: NAV_CLAIM_CHECK)",
    )
    ap.add_argument(
        "--without-tool",
        action="append",
        default=[],
        choices=TOOLS,
        help="local v1: leave this MCP tool out (ablation; repeatable)",
    )
    ap.add_argument("--name", default=None)
    ap.add_argument(
        "--traces",
        type=Path,
        default=None,
        help="append each finished trace here; rerun with the same file to resume",
    )
    ap.add_argument("--out", type=Path, default=REPORTS)
    ap.add_argument(
        "--from", dest="from_", type=Path, action="append", help="re-score stored reports"
    )
    args = ap.parse_args(argv)
    load_dotenv(".env")
    if args.claim_check is None:
        args.claim_check = claim_check_enabled()
    if args.target == "remote" and args.agent != "v1":
        raise SystemExit("--agent v2 runs locally only (it is not deployed)")
    if args.without_tool and (args.target == "remote" or args.agent != "v1"):
        raise SystemExit("--without-tool applies to the local navigator_v1 only")
    dataset = load_dataset(args.dataset)
    cases = select(dataset.cases, args)
    if not cases:
        raise SystemExit("no cases selected")

    if args.from_:
        stored = [json.loads(f.read_text(encoding="utf-8")) for f in args.from_]
        report = rescore(stored, [f.name for f in args.from_], dataset, cases)
    else:
        with ExitStack() as stack:
            url = args.mcp_url or stack.enter_context(
                local_server(Path("data/logs/eval-mcp-server.log"))
            )
            report = asyncio.run(evaluate(args, dataset, cases, url))

    name = args.name or ("smoke" if args.smoke else "answers")
    if args.target == "remote" and not args.name:
        name += "-remote"
    if not report["meta"]["dataset"]["verified"]:
        name += "-drafts"
    report = {
        "name": name,
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": git_sha(),
    } | report
    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.out / f"{datetime.now(UTC):%Y-%m-%d}-{report['git_sha']}-{name}"
    stem.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    stem.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    s = report["summary"]
    print(
        f"quote fidelity {fmt(s['quote_fidelity']['rate'])}%, hallucinated "
        f"{s['hallucinated_citations']['count']}, errors {s['errors']}, "
        f"CHF {s['cost_per_answer']['chf']:.4f}/answer"
    )
    print(f"wrote {stem}.md/.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
