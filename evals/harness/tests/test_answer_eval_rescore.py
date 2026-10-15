"""answer_eval --from: re-scoring stored reports without model calls."""

from typing import Any

import pytest

from evals.harness.answer_eval import rescore
from evals.harness.cases import Case, Dataset


def row(cid: str, *, error: str | None = None, grounded: float = 1.0) -> dict[str, Any]:
    return {
        "id": cid, "lang": "de", "category": "answerable", "error": error,
        "status": None if error else "passed", "rounds": 1,
        "first_draft": {"citations": 1, "quotes": 1, "problems": []},
        "dropped": [], "citations": 1, "quotes": 1, "verbatim": 1, "hallucinated": 0,
        "not_in_force": 0, "unchecked": 0, "required_recall": 1.0, "precision_expected": 1.0,
        "behaviour_det": True, "lang_ok": True, "tool_calls": 3, "latency_s": 10.0,
        "cost_usd": 0.01, "groundedness": grounded, "key_facts": 1.0,
        "must_not_violations": 0, "behaviour_ok": True, "precision_judged": 1.0,
        "usage": {"model_calls": 2, "prompt": 100, "cached": 0, "output": 10, "thoughts": 5},
    }  # fmt: skip


def report(rows: list[dict[str, Any]], judge_chf: float) -> dict[str, Any]:
    return {
        "cases": rows,
        "summary": {"run_cost_chf": {"agent": 0.0, "judge": judge_chf}},
        "meta": {"judged": True, "dataset": {}},
    }


def case(cid: str, verified_by: str | None = "claude-opus-5-5") -> Case:
    return Case.model_validate(
        {"id": cid, "lang": "de", "question": "?", "category": "answerable",
         "domain": "work", "verified_by": verified_by}
    )  # fmt: skip


def test_rescore_filters_to_dataset_and_later_reports_win() -> None:
    first = report([row("a"), row("b", error="timeout"), row("adv-1", grounded=0.0)], 3.0)
    rerun = report([row("b", grounded=0.5)], 1.0)
    cases = [case("a"), case("b")]
    dataset = Dataset("golden", [], cases)

    out = rescore([first, rerun], ["first.json", "rerun.json"], dataset, cases)

    assert [r["id"] for r in out["cases"]] == ["a", "b"]
    s = out["summary"]
    assert s["errors"] == 0
    assert s["groundedness"]["mean"] == pytest.approx(0.75)
    assert s["run_cost_chf"]["judge"] == pytest.approx(3.0 / 3 + 1.0)  # a from first, b rerun
    ds = out["meta"]["dataset"]
    assert ds["verified"]
    assert ds["verified_by"] == ["claude-opus-5-5"]
    assert out["meta"]["rescored_from"] == ["first.json", "rerun.json"]


def test_rescore_refuses_cases_without_a_stored_row() -> None:
    cases = [case("a"), case("zzz")]
    with pytest.raises(SystemExit, match="no stored row"):
        rescore([report([row("a")], 1.0)], ["r.json"], Dataset("golden", [], cases), cases)
