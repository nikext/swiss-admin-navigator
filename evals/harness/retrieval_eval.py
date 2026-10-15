"""Retrieval eval over `retrieval.jsonl` (docs/EVALS.md §2) and experiment E4 (§4).

    uv run python -m evals.harness.retrieval_eval                    # served config
    uv run python -m evals.harness.retrieval_eval --e4 --index data/index_e4.sqlite

Search runs through `mcp_server.search.Searcher`, the code `search_law` serves.
Query vectors come from the model recorded for each vector space in the index,
cached by content (a re-run costs nothing). Reports go to
`evals/reports/<date>-<sha>-<name>.{json,md}`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv

from agents.navigator.config import load_profile
from evals.harness.retrieval_metrics import (
    bootstrap_ci,
    hit_at_k,
    paired_bootstrap_diff,
    recall_at_k,
    reciprocal_rank,
)
from ingest.embed import EmbedCache, Embedder, EmbedInput
from mcp_server.search import Index, SearchConfig, Searcher, served_config

DATASET = Path("evals/datasets/retrieval.jsonl")
REPORTS = Path("evals/reports")
KS = (1, 3, 5, 8, 20)
DEPTH = 20  # results fetched per query (>= max(KS))


@dataclass(frozen=True)
class Named:
    name: str
    config: SearchConfig


def e4_grid() -> list[Named]:
    """E4: BM25 vs dense vs hybrid; trigram vs unicode61; headers on/off; model; dims."""
    b, d, h = "bm25", "dense", "hybrid"
    grid = [
        Named("bm25 unicode61", SearchConfig(mode=b, tokenizer="unicode61")),
        Named(
            "bm25 unicode61 no-header", SearchConfig(mode=b, tokenizer="unicode61", header=False)
        ),
        Named("bm25 unicode61 prefix", SearchConfig(mode=b, tokenizer="unicode61", prefix=True)),
        Named("bm25 trigram", SearchConfig(mode=b, tokenizer="trigram")),
        Named("bm25 trigram no-header", SearchConfig(mode=b, tokenizer="trigram", header=False)),
    ]
    for dims in (3072, 1536, 768, 256):
        grid.append(Named(f"dense emb2 {dims}", SearchConfig(mode=d, space="emb2-h", dims=dims)))
    grid += [
        Named("dense emb2 no-header 768", SearchConfig(mode=d, space="emb2-noh", dims=768)),
        Named("dense emb2 no-header 3072", SearchConfig(mode=d, space="emb2-noh", dims=3072)),
        Named("dense emb001 768", SearchConfig(mode=d, space="emb001-h", dims=768)),
        Named("dense emb001 3072", SearchConfig(mode=d, space="emb001-h", dims=3072)),
    ]
    for tok in ("trigram", "unicode61"):
        for dims in (768, 3072):
            grid.append(
                Named(
                    f"hybrid {tok} + emb2 {dims}",
                    SearchConfig(mode=h, tokenizer=tok, space="emb2-h", dims=dims),
                )
            )
    grid += [
        Named(
            "hybrid trigram + emb2 no-header 768 (no headers anywhere)",
            SearchConfig(mode=h, tokenizer="trigram", header=False, space="emb2-noh", dims=768),
        ),
        Named(
            "hybrid unicode61 prefix + emb2 768",
            SearchConfig(mode=h, tokenizer="unicode61", prefix=True, space="emb2-h", dims=768),
        ),
        Named(
            "hybrid trigram + emb001 768",
            SearchConfig(mode=h, tokenizer="trigram", space="emb001-h", dims=768),
        ),
    ]
    for tok in ("trigram", "unicode61"):
        for w in (0.5, 0.25):
            grid.append(
                Named(
                    f"hybrid {tok} (w={w}) + emb2 768",
                    SearchConfig(mode=h, tokenizer=tok, space="emb2-h", dims=768, bm25_weight=w),
                )
            )
    return grid


def load_cases(path: Path = DATASET) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


async def query_vectors(
    index: Index, spaces: set[str], queries: Sequence[str], project: str
) -> tuple[dict[str, np.ndarray], dict[str, dict[str, Any]]]:
    """Full-size query vectors per space (cached), plus embedding usage per space."""
    cache = EmbedCache()
    out, usage = {}, {}
    for name in sorted(spaces):
        spec = index.space_spec(name)
        ref = load_profile(spec["profile"]).embedding
        if (ref.model, ref.input_format) != (spec["model"], spec["input_format"]):
            raise SystemExit(f"profile {spec['profile']!r} no longer matches space {name!r}")
        embedder = Embedder(spec["model"], spec["location"], spec["input_format"], project, cache)
        out[name] = await embedder.embed([EmbedInput("query", q) for q in queries])
        usage[name] = asdict(embedder.usage)
    return out, usage


async def embedding_latency(index: Index, space: str, queries: Sequence[str], project: str) -> dict:
    """Uncached single-query embedding latency from this machine (sequential)."""
    spec = index.space_spec(space)
    embedder = Embedder(spec["model"], spec["location"], spec["input_format"], project, None)
    times = []
    for q in queries:
        t = time.perf_counter()
        await embedder.embed([EmbedInput("query", q)])
        times.append((time.perf_counter() - t) * 1000)
    times.sort()
    return {
        "model": spec["model"],
        "location": spec["location"],
        "n": len(times),
        "p50_ms": round(statistics.median(times), 1),
        "p95_ms": round(times[int(0.95 * (len(times) - 1))], 1),
    }


def run_config(
    index: Index, named: Named, cases: Sequence[dict[str, Any]], qvecs: dict[str, np.ndarray]
) -> dict[str, Any]:
    cfg = named.config
    searcher = Searcher(index, replace(cfg, depth=max(cfg.depth, DEPTH)))
    space = index.space_spec(cfg.space)["name"] if cfg.mode != "bm25" else None
    per_case, latencies = [], []
    for i, case in enumerate(cases):
        qvec = qvecs[space][i] if space else None
        t = time.perf_counter()
        hits = searcher.search(case["query"], qvec, k=DEPTH)
        latencies.append((time.perf_counter() - t) * 1000)
        ranked = [(h.sr, h.eid) for h in hits]
        expected = [(e["sr"], e["eid"]) for e in case["expected"]]
        row = {
            "id": case["id"],
            "lang": case["lang"],
            "domain": case["domain"],
            "difficulty": case.get("difficulty", "base"),
        }
        row |= {f"recall@{k}": recall_at_k(ranked, expected, k) for k in KS}
        row |= {"hit@8": hit_at_k(ranked, expected, 8), "mrr": reciprocal_rank(ranked, expected)}
        row["top3"] = [f"{h.sr}:{h.eid}:{h.lang}" for h in hits[:3]]
        per_case.append(row)
    summary: dict[str, Any] = {}
    for metric in [*(f"recall@{k}" for k in KS), "hit@8", "mrr"]:
        values = [r[metric] for r in per_case]
        lo, hi = bootstrap_ci(values)
        summary[metric] = {"mean": statistics.fmean(values), "ci95": [lo, hi]}
    for field in ("lang", "difficulty"):
        groups: dict[str, list[float]] = defaultdict(list)
        for r in per_case:
            groups[r[field]].append(r["recall@8"])
        summary[f"recall@8_by_{field}"] = {
            k: statistics.fmean(v) for k, v in sorted(groups.items())
        }
    summary["search_ms_p50"] = round(statistics.median(latencies), 2)
    return {"name": named.name, "config": asdict(cfg), "summary": summary, "cases": per_case}


COMPARISONS = [
    ("bm25 trigram", "bm25 unicode61"),
    ("bm25 trigram", "bm25 trigram no-header"),
    ("bm25 unicode61", "bm25 unicode61 no-header"),
    ("dense emb2 768", "dense emb2 no-header 768"),
    ("dense emb2 3072", "dense emb2 768"),
    ("dense emb2 768", "dense emb001 768"),
    ("hybrid trigram + emb2 768", "dense emb2 768"),
    ("hybrid trigram + emb2 768", "bm25 trigram"),
    ("hybrid trigram + emb2 768", "hybrid unicode61 + emb2 768"),
    ("hybrid trigram + emb2 768", "hybrid trigram + emb2 no-header 768 (no headers anywhere)"),
    ("hybrid trigram (w=0.25) + emb2 768", "dense emb2 768"),
    ("hybrid unicode61 (w=0.25) + emb2 768", "dense emb2 768"),
]


def compare(results: dict[str, dict[str, Any]], metric: str = "recall@8") -> list[dict[str, Any]]:
    out = []
    for a, b in COMPARISONS:
        if a in results and b in results:
            va = [c[metric] for c in results[a]["cases"]]
            vb = [c[metric] for c in results[b]["cases"]]
            mean, lo, hi = paired_bootstrap_diff(va, vb)
            out.append({"a": a, "b": b, "metric": metric, "diff": mean, "ci95": [lo, hi]})
    return out


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],  # noqa: S607
            capture_output=True, text=True, check=True,
        ).stdout.strip()  # fmt: skip
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def pct(x: float) -> str:
    return f"{100 * x:.1f}"


def render_markdown(report: dict[str, Any]) -> str:
    langs = sorted({c["lang"] for r in report["results"] for c in r["cases"]})
    lines = [
        f"# Retrieval eval: {report['name']}",
        "",
        f"- dataset: `{report['dataset']}` ({report['n_cases']} queries, "
        f"{report['n_expected']} expected articles)",
        f"- index: `{report['index']['path']}` (as_of {report['index']['as_of']}, built "
        f"{report['index']['built_at']} from {report['index']['git_sha']})",
        f"- run: {report['run_at']} at {report['git_sha']}; 95% CIs are percentile bootstraps "
        "over queries (2,000 resamples, seed 0)",
        "",
        "| config | R@1 | R@3 | R@5 | **R@8** (95% CI) | R@20 | hit@8 | MRR | "
        + " | ".join(f"R@8 {lang}" for lang in langs)
        + " | R@8 hard | search ms |",
        "|---|---|---|---|---|---|---|---|" + "---|" * len(langs) + "---|---|",
    ]
    for r in report["results"]:
        s = r["summary"]
        ci = s["recall@8"]["ci95"]
        lines.append(
            f"| {r['name']} | {pct(s['recall@1']['mean'])} | {pct(s['recall@3']['mean'])} | "
            f"{pct(s['recall@5']['mean'])} | **{pct(s['recall@8']['mean'])}** "
            f"({pct(ci[0])}–{pct(ci[1])}) | {pct(s['recall@20']['mean'])} | "
            f"{pct(s['hit@8']['mean'])} | {s['mrr']['mean']:.3f} | "
            + " | ".join(pct(s["recall@8_by_lang"].get(lang, float("nan"))) for lang in langs)
            + f" | {pct(s['recall@8_by_difficulty'].get('hard', float('nan')))}"
            + f" | {s['search_ms_p50']} |"
        )
    if report.get("comparisons"):
        lines += ["", "## Paired differences (recall@8, a − b, points)", ""]
        lines += ["| a | b | diff | 95% CI |", "|---|---|---|---|"]
        for c in report["comparisons"]:
            lines.append(
                f"| {c['a']} | {c['b']} | {100 * c['diff']:+.1f} | "
                f"{100 * c['ci95'][0]:+.1f} … {100 * c['ci95'][1]:+.1f} |"
            )
    if report.get("embedding_latency"):
        lines += [
            "",
            "## Query embedding latency (uncached, sequential, from the build machine)",
            "",
        ]
        lines += ["| model@location | n | p50 ms | p95 ms |", "|---|---|---|---|"]
        for lat in report["embedding_latency"]:
            lines.append(
                f"| {lat['model']}@{lat['location']} | {lat['n']} | {lat['p50_ms']} | "
                f"{lat['p95_ms']} |"
            )
    lines += ["", "## Misses at k=8 (first config)", ""]
    first = report["results"][0]
    misses = [c for c in first["cases"] if c["recall@8"] < 1]
    lines += [f"- `{c['id']}` ({c['lang']}): top3 {', '.join(c['top3'])}" for c in misses] or [
        "None."
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--index", type=Path, default=Path("data/index.sqlite"))
    ap.add_argument("--dataset", type=Path, default=DATASET)
    ap.add_argument("--e4", action="store_true", help="run the E4 grid (needs the E4 index)")
    ap.add_argument("--latency", type=int, default=0, help="also time N uncached query embeddings")
    ap.add_argument("--name", default=None)
    ap.add_argument("--out", type=Path, default=REPORTS)
    args = ap.parse_args(argv)
    load_dotenv()
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")

    index = Index(args.index)
    cases = load_cases(args.dataset)
    grid = e4_grid() if args.e4 else [Named("served default", served_config(index))]
    spaces = {index.space_spec(n.config.space)["name"] for n in grid if n.config.mode != "bm25"}
    if spaces and not project:
        raise SystemExit("GOOGLE_CLOUD_PROJECT is not set (copy .env.example to .env)")
    qvecs, usage = asyncio.run(query_vectors(index, spaces, [c["query"] for c in cases], project))
    results = {n.name: run_config(index, n, cases, qvecs) for n in grid}
    latency = []
    if args.latency:
        sample = [c["query"] for c in cases[: args.latency]]
        one_per_model = {index.space_spec(s)["model"]: s for s in sorted(spaces)}
        latency = [
            asyncio.run(embedding_latency(index, s, sample, project))
            for s in one_per_model.values()
        ]

    name = args.name or ("e4-retrieval" if args.e4 else "retrieval")
    meta = index.meta
    report = {
        "name": name,
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": git_sha(),
        "dataset": str(args.dataset),
        "n_cases": len(cases),
        "n_expected": sum(len(c["expected"]) for c in cases),
        "index": {"path": str(args.index)}
        | {k: meta.get(k) for k in ("as_of", "built_at", "git_sha", "spaces", "tokenizers")},
        "query_embedding_usage": usage,
        "embedding_latency": latency,
        "results": list(results.values()),
        "comparisons": compare(results) if args.e4 else [],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.out / f"{datetime.now(UTC):%Y-%m-%d}-{report['git_sha']}-{name}"
    stem.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    stem.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    for r in report["results"]:
        s = r["summary"]
        print(f"{r['name']:<60} R@8 {pct(s['recall@8']['mean']):>5}  MRR {s['mrr']['mean']:.3f}")
    print(f"wrote {stem}.md/.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
