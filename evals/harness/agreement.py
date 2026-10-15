"""Agreement between a judge and human labels (docs/EVALS.md §2, judge hygiene).

Pure functions, unit-tested: accuracy and Cohen's kappa for categorical
labels, mean absolute error, bias and Spearman's rank correlation for scores.
`judge_study.py` applies them per judge on the human-labelled answers.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Hashable, Sequence


def _pairs[T](a: Sequence[T | None], b: Sequence[T | None]) -> list[tuple[T, T]]:
    if len(a) != len(b):
        raise ValueError(f"length mismatch: {len(a)} vs {len(b)}")
    return [(x, y) for x, y in zip(a, b, strict=True) if x is not None and y is not None]


def accuracy(a: Sequence[Hashable | None], b: Sequence[Hashable | None]) -> float | None:
    pairs = _pairs(a, b)
    return sum(x == y for x, y in pairs) / len(pairs) if pairs else None


def cohen_kappa(a: Sequence[Hashable | None], b: Sequence[Hashable | None]) -> float | None:
    """Chance-corrected agreement; 1.0 when both raters use one identical label."""
    pairs = _pairs(a, b)
    if not pairs:
        return None
    n = len(pairs)
    observed = sum(x == y for x, y in pairs) / n
    ca, cb = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    expected = sum(ca[k] * cb[k] for k in ca.keys() | cb.keys()) / (n * n)
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1 - expected)


def mae(a: Sequence[float | None], b: Sequence[float | None]) -> float | None:
    pairs = _pairs(a, b)
    return sum(abs(x - y) for x, y in pairs) / len(pairs) if pairs else None


def bias(judge: Sequence[float | None], human: Sequence[float | None]) -> float | None:
    """Mean of judge − human: positive means the judge is more lenient."""
    pairs = _pairs(judge, human)
    return sum(x - y for x, y in pairs) / len(pairs) if pairs else None


def _ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):  # ties share the average rank
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(a: Sequence[float | None], b: Sequence[float | None]) -> float | None:
    pairs = _pairs(a, b)
    if len(pairs) < 3:
        return None
    ra, rb = _ranks([x for x, _ in pairs]), _ranks([y for _, y in pairs])
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb, strict=True))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return cov / (va * vb) if va and vb else None
