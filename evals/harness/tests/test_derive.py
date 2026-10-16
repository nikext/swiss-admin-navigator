"""Deriving cheaper verifier policies from a recorded run (pure parts)."""

from typing import Any

import pytest

from evals.harness.derive import (
    as_deterministic,
    judged_content,
    latency_at,
    same_judged_content,
    stop_index,
)


def entry(*kinds: str, t: float = 10.0, check_s: float = 1.0, claims_s: float | None = None):
    problems = [{"ref": "1", "kind": k, "message": "m"} for k in kinds]
    claims = [{"claim": "c", "refs": ["1"], "supported": "no", "issue": None}] if claims_s else None
    return {
        "draft": "{}",
        "round": {"citations": 1, "quotes": 1, "problems": problems, "check_s": check_s,
                  "claims": claims, "claims_s": claims_s,
                  "claims_usage": {"model_calls": 1} if claims_s else None},
        "t_s": t, "usage": {"model_calls": 3}, "tool_calls": 2,
    }  # fmt: skip


@pytest.mark.parametrize(
    ("kinds", "policy", "expected"),
    [
        ([()], "none", 0),
        ([("quote",), ()], "none", 0),
        ([()], "deterministic", 0),
        ([("unsupported",), ()], "deterministic", 0),  # the checker's rejection: v1 stops
        ([("fetch",), ()], "deterministic", 0),  # infrastructure: no retry in v1 either
        ([("quote",), ("unsupported",), ()], "deterministic", 1),
        ([("quote",), ("quote",), ()], "deterministic", 1),  # v1 finalises the second draft
        ([("quote",)], "deterministic", None),  # the run ended before v1's answer
        ([], "none", None),
    ],
)
def test_stop_index(kinds: list[tuple[str, ...]], policy: Any, expected: int | None) -> None:
    assert stop_index([entry(*k) for k in kinds], policy) == expected


def test_as_deterministic_strips_the_checker() -> None:
    r = as_deterministic(entry("quote", "unsupported", claims_s=2.0))
    assert [p.kind for p in r.problems] == ["quote"]
    assert (r.claims, r.claims_s, r.claims_usage) == (None, None, None)


def test_latency_at_subtracts_checks_the_policy_does_not_run() -> None:
    e = entry(t=40.0, check_s=3.0, claims_s=7.0)
    assert latency_at(e, "deterministic") == 33.0
    assert latency_at(e, "none") == 30.0


def test_judged_content_ignores_enrichment_and_quote_normalisation() -> None:
    quote = "l'affaire  du bail"  # typed apostrophe, double space
    draft = {"answer_markdown": "A [1].", "out_of_scope": False, "citations": [
        {"ref": "1", "sr": "220", "article": "Art. 271a", "quote": quote}]}  # fmt: skip
    final = draft | {"citations": [draft["citations"][0] | {
        "quote": "l’affaire du bail", "abbr": "CO", "url": "u"}], "verification": {}}  # fmt: skip
    assert judged_content(draft) == judged_content(final)
    assert same_judged_content({"judgement": {"x": 1}, "answer": final}, draft)
    assert not same_judged_content({"judgement": None, "answer": final}, draft)
    assert not same_judged_content(
        {"judgement": {"x": 1}, "answer": final}, draft | {"answer_markdown": "B [1]."}
    )
    assert judged_content(None) is None
