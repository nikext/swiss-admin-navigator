import math

import pytest

from evals.harness.retrieval_metrics import (
    bootstrap_ci,
    hit_at_k,
    paired_bootstrap_diff,
    recall_at_k,
    reciprocal_rank,
)

RANKED = [("220", "art_271"), ("220", "art_271_a"), ("220", "art_273"), ("220", "art_274")]


def test_recall_counts_share_of_expected_in_top_k() -> None:
    expected = [("220", "art_271_a"), ("220", "art_274")]
    assert recall_at_k(RANKED, expected, 2) == 0.5
    assert recall_at_k(RANKED, expected, 4) == 1.0
    assert recall_at_k(RANKED, expected, 1) == 0.0


def test_recall_ignores_duplicate_expected_items() -> None:
    assert recall_at_k(RANKED, [("220", "art_273"), ("220", "art_273")], 3) == 1.0


def test_recall_needs_expected_items() -> None:
    with pytest.raises(ValueError, match="at least one"):
        recall_at_k(RANKED, [], 8)


def test_hit_is_any_expected_in_top_k() -> None:
    assert hit_at_k(RANKED, [("220", "art_273"), ("1", "x")], 3) == 1.0
    assert hit_at_k(RANKED, [("220", "art_273")], 2) == 0.0


def test_reciprocal_rank_uses_first_expected_and_cutoff() -> None:
    assert reciprocal_rank(RANKED, [("220", "art_273"), ("220", "art_271_a")]) == 0.5
    assert reciprocal_rank(RANKED, [("220", "art_274")]) == 0.25
    assert reciprocal_rank(RANKED, [("220", "art_274")], k=3) == 0.0
    assert reciprocal_rank([], [("220", "art_274")]) == 0.0


def test_bootstrap_ci_brackets_the_mean_and_is_reproducible() -> None:
    values = [1.0] * 40 + [0.0] * 10
    lo, hi = bootstrap_ci(values)
    assert lo < 0.8 < hi
    assert (lo, hi) == bootstrap_ci(values)
    assert bootstrap_ci([1.0, 1.0]) == (1.0, 1.0)
    assert all(math.isnan(x) for x in bootstrap_ci([]))


def test_paired_diff_is_zero_for_identical_runs_and_checks_lengths() -> None:
    a = [1.0, 0.0, 1.0, 1.0]
    assert paired_bootstrap_diff(a, a) == (0.0, 0.0, 0.0)
    mean, lo, hi = paired_bootstrap_diff([1.0] * 10, [0.0] * 10)
    assert (mean, lo, hi) == (1.0, 1.0, 1.0)
    with pytest.raises(ValueError, match="same cases"):
        paired_bootstrap_diff([1.0], [1.0, 0.0])
