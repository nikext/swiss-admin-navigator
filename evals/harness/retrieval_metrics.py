"""Retrieval metrics (docs/EVALS.md §2): recall@k, hit@k, MRR, bootstrap CIs.

A key is whatever identifies a relevant item; for `search_law` it is the
article `(sr, eid)`, independent of language (the agent fetches the language
it needs with `get_article`).
"""

from __future__ import annotations

import random
from collections.abc import Collection, Hashable, Sequence
from statistics import fmean


def recall_at_k(ranked: Sequence[Hashable], expected: Collection[Hashable], k: int) -> float:
    """Share of expected items in the top k."""
    if not expected:
        raise ValueError("a retrieval case needs at least one expected item")
    top = set(ranked[:k])
    return sum(e in top for e in set(expected)) / len(set(expected))


def hit_at_k(ranked: Sequence[Hashable], expected: Collection[Hashable], k: int) -> float:
    """1.0 if any expected item is in the top k."""
    return float(any(r in set(expected) for r in ranked[:k]))


def reciprocal_rank(
    ranked: Sequence[Hashable], expected: Collection[Hashable], k: int | None = None
) -> float:
    """1 / rank of the first expected item (within k), else 0."""
    wanted = set(expected)
    for i, r in enumerate(ranked[:k] if k else ranked):
        if r in wanted:
            return 1.0 / (i + 1)
    return 0.0


def bootstrap_ci(
    values: Sequence[float], n: int = 2000, alpha: float = 0.05, seed: int = 0
) -> tuple[float, float]:
    """Percentile bootstrap CI of the mean (fixed seed: reports are reproducible)."""
    if not values:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)  # noqa: S311 (statistics, not security)
    m = len(values)
    means = sorted(fmean(rng.choices(values, k=m)) for _ in range(n))
    return means[int(n * alpha / 2)], means[min(n - 1, int(n * (1 - alpha / 2)))]


def paired_bootstrap_diff(
    a: Sequence[float], b: Sequence[float], n: int = 2000, alpha: float = 0.05, seed: int = 0
) -> tuple[float, float, float]:
    """Mean of a - b over the same cases, with a paired percentile CI."""
    if len(a) != len(b):
        raise ValueError("paired comparison needs the same cases")
    diffs = [x - y for x, y in zip(a, b, strict=True)]
    lo, hi = bootstrap_ci(diffs, n, alpha, seed)
    return fmean(diffs) if diffs else float("nan"), lo, hi
