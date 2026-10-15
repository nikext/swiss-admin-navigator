"""Judge study: grade stored answers with candidate judges, compare with human labels.

    make judge-study JUDGES="gemini-3.1-pro-preview@global,claude-haiku-5-5@global:low"
    make judge-study ARGS="--from evals/reports/<date>-<sha>-judge-study.json"   # re-score, free

Takes the answers of an existing answer-eval report (default: the 30-case M3
run), rebuilds each judge input from the *current* case (golden or draft) and
the full article text from the local index, and grades it with every judge
spec (`model@location[:thinking]`; the same spec twice measures test-retest
noise). Judgements, cost and latency are saved, so agreement with the human
labels (`evals/datasets/judge_labels.jsonl`, `make label-answers`) can be
recomputed later with `--from` without calling any model again.

Agreement per judge, on the human-labelled answers: groundedness MAE, bias
and Spearman against the human score; "fully grounded" (every claim
supported) accuracy and kappa; key facts (stated vs not) accuracy and kappa;
must_not and behaviour accuracy. Costs money unless `--from` is used.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from agents.navigator.citecheck import ArticleNotFoundError
from agents.navigator.config import THINKING_LEVELS, LlmRef
from evals.harness.agreement import accuracy, bias, cohen_kappa, mae, spearman
from evals.harness.answer_metrics import GetArticle, check_citations, cost_usd
from evals.harness.cases import Case, load_dataset
from evals.harness.judge import Judge, Judgement, groundedness, payload, prompt_sha
from evals.harness.retrieval_eval import git_sha

REPORTS = Path("evals/reports")
DEFAULT_REPORT = REPORTS / "2026-10-15-3e7e603-answers-drafts.json"
LABELS = Path("evals/datasets/judge_labels.jsonl")
PRICING = Path("evals/pricing.yaml")
SCORE = {"yes": 1.0, "partly": 0.5, "no": 0.0}


def parse_spec(spec: str) -> LlmRef:
    """`model@location[:thinking]` → LlmRef."""
    model, _, rest = spec.strip().partition("@")
    location, _, thinking = rest.partition(":")
    if not model or not location:
        raise ValueError(f"judge spec {spec!r}: expected model@location[:thinking]")
    if thinking and thinking not in THINKING_LEVELS:
        raise ValueError(f"judge spec {spec!r}: thinking must be one of {THINKING_LEVELS}")
    return LlmRef(model=model, location=location, thinking=thinking or None)


def answer_sha(answer: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(answer, sort_keys=True).encode()).hexdigest()[:12]


def human_groundedness(label: dict[str, Any]) -> float | None:
    """Claim-level support as the judge computes it, plus claims the split missed (as `no`)."""
    claims = [SCORE[c["supported"]] for c in label["claims"]]
    claims += [0.0] * int(label.get("missed_unsupported", 0))
    return sum(claims) / len(claims) if claims else None


def judge_view(j: dict[str, Any]) -> dict[str, Any]:
    """The comparable parts of one stored judgement."""
    jd = Judgement.model_validate(j)
    return {
        "groundedness": groundedness(jd),
        "fully_grounded": None if not jd.claims else all(c.supported == "yes" for c in jd.claims),
        "key_facts": [f.verdict == "stated" for f in jd.key_facts],
        "must_not": [m.violated for m in jd.must_not],
        "behaviour_ok": jd.behaviour_ok,
    }


def human_view(label: dict[str, Any]) -> dict[str, Any]:
    g = human_groundedness(label)
    return {
        "groundedness": g,
        "fully_grounded": None if g is None else g == 1.0,
        "key_facts": [v == "stated" for v in label["key_facts"]],
        "must_not": list(label["must_not"]),
        "behaviour_ok": label["behaviour_ok"],
    }


Views = dict[str, dict[str, Any]]


def agreement(judged: Views, human: Views) -> dict[str, Any]:
    """Judge vs human over the case ids both have (views from judge_view/human_view)."""
    ids = sorted(judged.keys() & human.keys())

    def col(views: Views, key: str) -> list[Any]:
        return [views[i][key] for i in ids]

    def items(key: str) -> tuple[list[Any], list[Any]]:
        a, b = [], []
        for i in ids:  # per-item lists only line up when both cover the same items
            ja, hb = judged[i][key], human[i][key]
            if len(ja) == len(hb):
                a += ja
                b += hb
        return a, b

    gj, gh = col(judged, "groundedness"), col(human, "groundedness")
    fj, fh = col(judged, "fully_grounded"), col(human, "fully_grounded")
    kj, kh = items("key_facts")
    mj, mh = items("must_not")
    bj, bh = col(judged, "behaviour_ok"), col(human, "behaviour_ok")
    return {
        "n": len(ids),
        "groundedness_mae": mae(gj, gh),
        "groundedness_bias": bias(gj, gh),
        "groundedness_spearman": spearman(gj, gh),
        "fully_grounded_acc": accuracy(fj, fh),
        "fully_grounded_kappa": cohen_kappa(fj, fh),
        "key_facts_acc": accuracy(kj, kh),
        "key_facts_kappa": cohen_kappa(kj, kh),
        "key_facts_n": len(kj),
        "must_not_acc": accuracy(mj, mh),
        "behaviour_acc": accuracy(bj, bh),
        "behaviour_kappa": cohen_kappa(bj, bh),
    }


def load_labels(path: Path, report_name: str) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            if rec["report"] == report_name:
                out[rec["case_id"]] = rec
    return out


def local_getter() -> GetArticle:
    from mcp_server.search import Index
    from mcp_server.tools import LawTools, ToolInputError

    law = LawTools(Index("data/index.sqlite"))

    async def get(sr: str, article: str, lang: str) -> dict[str, Any]:
        try:
            return law.get_article(sr, article, lang)
        except ToolInputError as exc:
            raise ArticleNotFoundError(str(exc)) from exc

    return get


async def build_inputs(rows: list[dict[str, Any]], cases: dict[str, Case]) -> dict[str, Any]:
    get = local_getter()
    inputs = {}
    for row in rows:
        answer, case = row.get("answer"), cases.get(row["id"])
        if not answer or case is None:
            continue
        checks = await check_citations(answer, get)
        cited = [
            {"ref": c.ref, "sr": c.sr, "article": c.article, "lang": c.quote_lang, "text": c.text}
            for c in checks
            if c.text
        ]
        inputs[row["id"]] = payload(case, answer, cited)
    return inputs


async def run_judge(
    spec: str, inputs: dict[str, Any], project: str, pricing: dict[str, Any], concurrency: int
) -> dict[str, Any]:
    ref = parse_spec(spec)
    judge = Judge(ref, project)
    sem = asyncio.Semaphore(concurrency)
    out: dict[str, Any] = {}

    async def one(cid: str, data: dict[str, Any]) -> None:
        async with sem:
            start = time.perf_counter()
            try:
                j = await judge.grade(data)
                out[cid] = {"judgement": j.model_dump(), "latency_s": time.perf_counter() - start}
            except Exception as exc:
                out[cid] = {"error": f"{type(exc).__name__}: {exc}"[:300]}

    await asyncio.gather(*(one(cid, d) for cid, d in inputs.items()))
    cost = cost_usd(ref.model, judge.usage, pricing)
    lat = sorted(v["latency_s"] for v in out.values() if "latency_s" in v)
    return {
        "spec": spec,
        "ref": {"model": ref.model, "location": ref.location, "thinking": ref.thinking},
        "cases": dict(sorted(out.items())),
        "usage": vars(judge.usage),
        "cost_chf": None if cost is None else cost * pricing["usd_to_chf"],
        "latency_p50_s": lat[len(lat) // 2] if lat else None,
        "errors": sum("error" in v for v in out.values()),
    }


def score(study: dict[str, Any], labels: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    human = {
        cid: human_view(lab)
        for cid, lab in labels.items()
        if lab.get("answer_sha") == study["answer_shas"].get(cid)
    }
    reference: Views | None = None
    rows = []
    for run in study["judges"]:
        views = {
            cid: judge_view(v["judgement"]) for cid, v in run["cases"].items() if "judgement" in v
        }
        if reference is None:
            reference = views
        per_answer = None if run["cost_chf"] is None else run["cost_chf"] / max(len(views), 1)
        rows.append(
            {
                "spec": run["spec"],
                "cost_chf_per_answer": per_answer,
                "latency_p50_s": run["latency_p50_s"],
                "errors": run["errors"],
                "vs_human": agreement(views, human),
                "vs_reference": agreement(views, reference),
            }
        )
    return rows


def fmt(x: float | None, pct: bool = False) -> str:
    if x is None:
        return "–"
    return f"{100 * x:.0f}" if pct else f"{x:.2f}"


def render(study: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    n_h = rows[0]["vs_human"]["n"] if rows else 0
    lines = [
        "# Judge study",
        "",
        f"- answers: `{study['report']}` ({len(study['answer_shas'])} answers); judge prompt "
        f"sha {study['judge_prompt_sha']}; run {study['run_at']} at {study['git_sha']}",
        f"- human labels: {n_h} answers (`{LABELS}`); reference judge: `{rows[0]['spec']}`"
        if rows
        else "- no judges",
        "",
        "## Agreement with human labels",
        "",
        "| judge | CHF/answer | p50 s | grounded MAE | bias | ρ | fully-grounded acc / κ "
        "| key facts acc / κ (n) | must_not acc | behaviour acc / κ |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        h = r["vs_human"]
        lines.append(
            f"| `{r['spec']}` | {cost(r['cost_chf_per_answer'])} | {fmt(r['latency_p50_s'])} "
            f"| {fmt(h['groundedness_mae'])} | {fmt(h['groundedness_bias'])} "
            f"| {fmt(h['groundedness_spearman'])} "
            f"| {fmt(h['fully_grounded_acc'], True)} / {fmt(h['fully_grounded_kappa'])} "
            f"| {fmt(h['key_facts_acc'], True)} / {fmt(h['key_facts_kappa'])} ({h['key_facts_n']}) "
            f"| {fmt(h['must_not_acc'], True)} "
            f"| {fmt(h['behaviour_acc'], True)} / {fmt(h['behaviour_kappa'])} |"
        )
    lines += [
        "",
        "## Agreement with the reference judge (all answers)",
        "",
        "| judge | n | grounded MAE | bias | ρ | key facts acc | behaviour acc | errors |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        ref = r["vs_reference"]
        lines.append(
            f"| `{r['spec']}` | {ref['n']} | {fmt(ref['groundedness_mae'])} "
            f"| {fmt(ref['groundedness_bias'])} | {fmt(ref['groundedness_spearman'])} "
            f"| {fmt(ref['key_facts_acc'], True)} | {fmt(ref['behaviour_acc'], True)} "
            f"| {r['errors']} |"
        )
    lines += [
        "",
        "MAE/bias are on the 0–1 groundedness scale (bias > 0: judge more lenient than the "
        "reference). κ is Cohen's kappa. With n≈30 answers, differences of a few points are "
        "noise (EVALS.md §4).",
    ]
    return "\n".join(lines) + "\n"


def cost(x: float | None) -> str:
    return "–" if x is None else f"{x:.4f}"


async def collect(args: argparse.Namespace) -> dict[str, Any]:
    report = json.loads(args.report.read_text(encoding="utf-8"))
    rows = [r for r in report["cases"] if r.get("answer")]
    if args.ids:
        rows = [r for r in rows if r["id"] in args.ids.split(",")]
    cases = {c.id: c for c in load_dataset("all").cases}
    missing = sorted({r["id"] for r in rows} - cases.keys())
    if missing:
        print(f"warning: no current case for {missing}; skipped")
    inputs = await build_inputs(rows, cases)
    pricing = yaml.safe_load(PRICING.read_text(encoding="utf-8"))
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or sys.exit("GOOGLE_CLOUD_PROJECT unset")
    judges = []
    for spec in args.judges.split(","):
        print(f"judging {len(inputs)} answers with {spec} ...", flush=True)
        judges.append(await run_judge(spec, inputs, project, pricing, args.concurrency))
        print(f"  cost CHF {judges[-1]['cost_chf'] or 0:.3f}, errors {judges[-1]['errors']}")
    return {
        "report": args.report.name,
        "answer_shas": {r["id"]: answer_sha(r["answer"]) for r in rows if r["id"] in inputs},
        "case_shas": {
            cid: hashlib.sha256(cases[cid].model_dump_json().encode()).hexdigest()[:12]
            for cid in inputs
        },
        "judge_prompt_sha": prompt_sha(),
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": git_sha(),
        "judges": judges,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="answers to judge")
    ap.add_argument("--judges", default="", help="comma-separated model@location[:thinking]")
    ap.add_argument("--from", dest="from_", type=Path, help="re-score a saved study (no calls)")
    ap.add_argument("--labels", type=Path, default=LABELS)
    ap.add_argument("--ids", default=None)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--out", type=Path, default=REPORTS)
    args = ap.parse_args(argv)
    load_dotenv(".env")
    if args.from_:
        study = json.loads(args.from_.read_text(encoding="utf-8"))
        stem = args.from_.with_suffix("")
    else:
        if not args.judges:
            ap.error("give --judges or --from")
        study = asyncio.run(collect(args))
        stem = args.out / f"{datetime.now(UTC):%Y-%m-%d}-{study['git_sha']}-judge-study"
        args.out.mkdir(parents=True, exist_ok=True)
    rows = score(study, load_labels(args.labels, study["report"]))
    study["agreement"] = rows
    stem.with_suffix(".json").write_text(
        json.dumps(study, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    stem.with_suffix(".md").write_text(render(study, rows), encoding="utf-8")
    print(f"wrote {stem}.md/.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
