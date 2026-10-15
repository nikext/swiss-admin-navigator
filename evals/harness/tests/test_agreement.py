import pytest

from evals.harness.agreement import accuracy, bias, cohen_kappa, mae, spearman


def test_accuracy_skips_missing_pairs() -> None:
    assert accuracy(["a", "b", None, "a"], ["a", "a", "b", None]) == 0.5
    assert accuracy([None], ["a"]) is None
    with pytest.raises(ValueError, match="length mismatch"):
        accuracy(["a"], ["a", "b"])


def test_cohen_kappa_textbook_example() -> None:
    # 50 items: both yes 20, both no 15, A yes/B no 5, A no/B yes 10 -> kappa = 0.4
    a = ["y"] * 20 + ["n"] * 15 + ["y"] * 5 + ["n"] * 10
    b = ["y"] * 20 + ["n"] * 15 + ["n"] * 5 + ["y"] * 10
    assert cohen_kappa(a, b) == pytest.approx(0.4)


def test_cohen_kappa_edge_cases() -> None:
    assert cohen_kappa(["y", "y"], ["y", "y"]) == 1.0  # one shared label, full agreement
    assert cohen_kappa(["y", "n"], ["n", "y"]) == pytest.approx(-1.0)
    assert cohen_kappa([], []) is None


def test_mae_and_bias() -> None:
    judge, human = [1.0, 0.5, None, 0.0], [0.5, 0.5, 1.0, 0.5]
    assert mae(judge, human) == pytest.approx((0.5 + 0 + 0.5) / 3)
    assert bias(judge, human) == pytest.approx((0.5 + 0 - 0.5) / 3)


def test_spearman_with_ties() -> None:
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    # ties get average ranks: [1, 2.5, 2.5, 4] vs [1, 2, 3, 4]
    assert spearman([1.0, 0.5, 0.5, 0.0][::-1], [0.1, 0.2, 0.3, 0.4]) == pytest.approx(0.9486833)
    assert spearman([1, 1, 1], [1, 2, 3]) is None  # no variance
    assert spearman([1, 2], [1, 2]) is None  # too few points
