from __future__ import annotations

import pytest

from evals.harness.cases import Case
from evals.harness.label import QuitError, collect_label

CASE = Case.model_validate(
    {
        "id": "housing-01",
        "lang": "fr",
        "question": "?",
        "category": "answerable",
        "domain": "housing",
        "key_facts": ["fact one", "fact two"],
        "must_not": ["bad thing"],
    }
)
ROW = {
    "judgement": {
        "claims": [
            {"claim": "claim A", "refs": ["1"], "supported": "yes"},
            {"claim": "claim B", "refs": [], "supported": "no"},
        ]
    }
}


def scripted(*answers: str):
    it = iter(answers)
    return lambda _prompt: next(it)


def test_collect_label_maps_keys_and_reprompts_invalid() -> None:
    shown: list[str] = []
    ask = scripted("x", "y", "p", "", "s", "c", "n", "y", "looks fine")
    rec = collect_label(CASE, ROW, ask, shown.append)
    assert [c["supported"] for c in rec["claims"]] == ["yes", "partly"]
    assert rec["missed_unsupported"] == 0
    assert rec["key_facts"] == ["stated", "contradicted"]
    assert rec["key_fact_texts"] == ["fact one", "fact two"]
    assert rec["must_not"] == [False]
    assert rec["behaviour_ok"] is True
    assert rec["note"] == "looks fine"
    assert not any("yes" in s and "claim A" in s for s in shown)  # judge verdicts stay hidden


def test_collect_label_quit() -> None:
    with pytest.raises(QuitError):
        collect_label(CASE, ROW, scripted("y", "q"), lambda _s: None)
