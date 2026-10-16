from __future__ import annotations

from typing import Any

import pytest

from agents.navigator.config import LlmRef
from evals.harness.judge import is_claude, is_maas, openapi_base_url
from evals.harness.judge_study import (
    agreement,
    answer_scores,
    human_groundedness,
    human_view,
    judge_view,
    parse_spec,
    render,
    score,
)


def claims(supported: list[str]) -> list[dict[str, Any]]:
    return [{"claim": f"c{i}", "refs": ["1"], "supported": s} for i, s in enumerate(supported)]


def judgement(supported: list[str], facts: list[str], must_not: list[bool], ok: bool) -> dict:
    return {
        "claims": claims(supported),
        "key_facts": [{"fact": f"f{i}", "verdict": v} for i, v in enumerate(facts)],
        "must_not": [{"item": f"m{i}", "violated": v} for i, v in enumerate(must_not)],
        "behaviour_ok": ok,
        "behaviour_note": "",
        "irrelevant_refs": [],
    }


def label(supported: list[str], facts: list[str], must_not: list[bool], ok: bool, missed=0) -> dict:
    return {
        "claims": claims(supported),
        "missed_unsupported": missed,
        "key_facts": facts,
        "must_not": must_not,
        "behaviour_ok": ok,
        "report": "r.json",
        "answer_sha": "sha-a",
    }


def test_parse_spec() -> None:
    assert parse_spec("claude-haiku-5-5@global:low") == LlmRef("claude-haiku-5-5", "global", "low")
    assert parse_spec(" gemini-3.8-flash@eu ") == LlmRef("gemini-3.8-flash", "eu", None)
    with pytest.raises(ValueError, match="expected model@location"):
        parse_spec("gemini-3.8-flash")
    with pytest.raises(ValueError, match="thinking must be one of"):
        parse_spec("gemini-3.8-flash@eu:max")
    ref = parse_spec("zai-org/glm-5.2-maas@global:low")
    assert ref == LlmRef("zai-org/glm-5.2-maas", "global", "low")


def test_provider_routing() -> None:
    models = ("openai/gpt-oss-120b-maas", "claude-sonnet-5-5", "gemini-3.8-flash")
    route = {m: (is_claude(m), is_maas(m)) for m in models}
    assert route == {
        "openai/gpt-oss-120b-maas": (False, True),
        "claude-sonnet-5-5": (True, False),
        "gemini-3.8-flash": (False, False),
    }
    assert openapi_base_url("p", "global") == (
        "https://aiplatform.googleapis.com/v1/projects/p/locations/global/endpoints/openapi"
    )
    assert openapi_base_url("p", "us-central1").startswith("https://us-central1-aiplatform.")


def test_human_groundedness_counts_missed_claims_as_unsupported() -> None:
    assert human_groundedness(label(["yes", "partly"], [], [], True)) == pytest.approx(0.75)
    assert human_groundedness(label(["yes", "yes"], [], [], True, missed=2)) == pytest.approx(0.5)
    assert human_groundedness(label([], [], [], True)) is None


def test_views_and_agreement() -> None:
    j = {
        "a": judge_view(judgement(["yes", "no"], ["stated", "missing"], [False], True)),
        "b": judge_view(judgement(["yes"], ["stated"], [True], False)),
        "c": judge_view(judgement(["yes"], ["stated"], [], True)),  # no human label
    }
    h = {
        "a": human_view(label(["yes", "yes"], ["stated", "stated"], [False], True)),
        "b": human_view(label(["yes"], ["stated"], [False], False)),
    }
    a = agreement(j, h)
    assert a["n"] == 2
    assert a["groundedness_mae"] == pytest.approx(0.25)  # |0.5-1| and |1-1|
    assert a["groundedness_bias"] == pytest.approx(-0.25)  # judge stricter
    assert a["fully_grounded_acc"] == pytest.approx(0.5)
    assert a["key_facts_acc"] == pytest.approx(2 / 3)
    assert a["key_facts_n"] == 3
    assert a["must_not_acc"] == pytest.approx(0.5)
    assert a["behaviour_acc"] == 1.0


def test_answer_scores() -> None:
    views = {
        "a": judge_view(judgement(["yes", "no"], ["stated", "missing"], [False], True)),
        "b": judge_view(judgement(["yes"], ["stated"], [True, True], False)),
    }
    s = answer_scores(views)
    assert s["groundedness"] == pytest.approx(0.75)  # mean of 0.5 and 1
    assert s["key_facts"] == pytest.approx(2 / 3)
    assert s["behaviour"] == 0.5
    assert s["must_not_violations"] == 2
    assert s["must_not_ids"] == ["b"]
    assert s["behaviour_fail_ids"] == ["b"]


def test_score_uses_only_labels_for_the_same_answer() -> None:
    run: dict[str, Any] = {
        "spec": "j@global",
        "cost_chf": 0.3,
        "latency_p50_s": 4.0,
        "errors": 0,
        "cases": {"a": {"judgement": judgement(["yes"], ["stated"], [False], True)}},
    }
    study = {
        "report": "r.json",
        "answer_shas": {"a": "sha-a"},
        "judge_prompt_sha": "x",
        "run_at": "t",
        "git_sha": "g",
        "judges": [run, run | {"spec": "k@eu"}],
    }
    good = {"a": label(["yes"], ["stated"], [False], True)}
    rows = score(study, good)
    assert rows[0]["vs_human"]["n"] == 1
    assert rows[0]["cost_chf_per_answer"] == pytest.approx(0.3)
    assert rows[1]["vs_reference"]["groundedness_mae"] == 0.0
    stale = {"a": good["a"] | {"answer_sha": "other"}}  # labelled a different answer
    assert score(study, stale)[0]["vs_human"]["n"] == 0
    md = render(study, rows)
    assert "| `j@global` | 0.3000 | 4.00 |" in md
