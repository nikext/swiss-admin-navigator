"""Experiment tables: pairing and subsets."""

from typing import Any

from evals.harness.compare import SUBSETS, overlay, paired, tables


def row(id_: str, g: float | None = 0.8, error: str | None = None, **kw: Any) -> dict[str, Any]:
    return {
        "id": id_, "error": error, "groundedness": g, "key_facts": 1.0, "behaviour_ok": True,
        "must_not_violations": 0, "cost_usd": 0.05, "latency_s": 30.0, "quotes": 2,
        "verbatim": 2, "hallucinated": 0, "required_recall": 1.0,
        "usage": {"model_calls": 5}, **kw,
    }  # fmt: skip


def test_paired_uses_common_answered_ids() -> None:
    a = [row("x", 0.5), row("y", 0.5), row("z", 0.5)]
    b = [row("x", 1.0), row("y", None), row("z", 0.9, error="timeout"), row("w", 1.0)]
    res = paired(a, b, lambda r: r.get("groundedness"), needs_answer=True)
    assert res is not None
    mean, lo, hi, n = res
    assert (mean, lo, hi, n) == (0.5, 0.5, 0.5, 1)
    beh = paired(a, b[:3], lambda r: float(not r["error"]), needs_answer=False)
    assert beh is not None
    assert beh[3] == 3  # errors count for behaviour


def test_subsets_and_tables() -> None:
    assert SUBSETS["adversarial"]({"id": "adv-01"})
    assert not SUBSETS["golden"]({"id": "adv-01"})
    rep = {"meta": {"pricing": {"usd_to_chf": 0.8}}, "cases": [row("a-1"), row("adv-01")]}
    out = tables([("v1", rep), ("v2", rep)], "golden")
    assert "| v1 | 1 | 0 | 100.0% (100.0–100.0) | 0 | 80.0 (80.0–80.0) |" in out
    assert "| v2 | +0.0 (+0.0…+0.0), n=1 |" in out


def test_overlay_takes_the_other_judges_grades() -> None:
    judgement = {
        "claims": [{"claim": "c", "refs": ["1"], "supported": "partly"}],
        "key_facts": [{"fact": "f", "verdict": "missing"}],
        "must_not": [{"item": "m", "violated": True}],
        "behaviour_ok": False, "behaviour_note": "n", "irrelevant_refs": [],
    }  # fmt: skip
    study = {"judges": [{"spec": "q@global", "cases": {"x": {"judgement": judgement}}}]}
    rows = overlay([row("x", behaviour_det=True), row("y", behaviour_det=True)], study, "q@global")
    assert (rows[0]["groundedness"], rows[0]["key_facts"]) == (0.5, 0.0)
    assert rows[0]["must_not_violations"] == 1
    assert rows[0]["behaviour_ok"] is False
    assert rows[1]["groundedness"] is None
    assert rows[1]["behaviour_ok"] is True
