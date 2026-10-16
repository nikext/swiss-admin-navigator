from typing import Any

import pytest

from evals.harness.memory_eval import (
    CASES,
    MemCase,
    StepObs,
    Stored,
    check_step,
    chf,
    leaks,
    load_cases,
    mapped_model,
    render,
    scope_filter,
    score_extract,
    summarize,
    validate,
)


def case(**kw: Any) -> MemCase:
    base: dict[str, Any] = {
        "id": "m",
        "kind": "extract",
        "lang": "en",
        "privacy": False,
        "turns": [{"role": "user", "text": "hi"}],
    }
    return MemCase.model_validate(base | kw)


def test_dataset_is_valid() -> None:
    cases = load_cases(CASES)
    assert len([c for c in cases if c.kind == "extract"]) == 20
    assert len([c for c in cases if c.kind == "e2e"]) == 6
    assert all(c.verified_by for c in cases)
    # Every sensitive-data case is a privacy case, and there are privacy e2e cases.
    assert all(c.privacy for c in cases if c.forbidden)
    assert sum(c.privacy for c in cases if c.kind == "e2e") >= 4


@pytest.mark.parametrize(
    ("kw", "problem"),
    [
        ({"expect": {"religion": "x"}}, "unknown profile field"),
        ({"expect": {"permit": "F"}}, "not a storable value"),
        ({"absent": ["health"]}, "unknown profile field"),
        ({"forbidden": ["x"]}, "privacy case"),
        ({"turns": []}, "without turns"),
    ],
)
def test_validate_rejects(kw: dict[str, Any], problem: str) -> None:
    assert any(problem in p for p in validate(case(**kw)))


def test_validate_e2e_steps() -> None:
    bad = case(kind="e2e", turns=[], steps=[{"message": "q", "check": {"nonsense": 1}}])
    assert any("unknown checks" in p for p in validate(bad))
    both = case(kind="e2e", turns=[], steps=[{"message": "q", "forget": True}])
    assert any("either sends a message or forgets" in p for p in validate(both))


def test_leaks_are_case_insensitive_over_profile_and_facts() -> None:
    stored = Stored(profile={"municipality": "Winterthur"}, facts=["The user has Diabetes."])
    assert leaks(stored, ["diabet", "Marko"]) == ["diabet"]
    assert leaks(Stored(), ["x"]) == []
    # A structured field's context is stored text as well.
    assert leaks(Stored(contexts=["The user mentioned diabetes."]), ["diabet"]) == ["diabet"]


def test_score_extract_profile() -> None:
    c = case(
        privacy=True,
        expect={"canton": "ZH", "permit": "B", "has_children": True},
        absent=["marital_status"],
        forbidden=["Marko"],
    )
    stored = Stored(
        profile={"canton": "ZH", "permit": "C", "marital_status": "married", "health": "x"}
    )
    s = score_extract(c, stored, None, [])
    assert (s["hits"], s["expected"]) == (1, 3)
    assert s["missing"] == ["has_children"]
    assert s["wrong"] == {"permit": "C"}
    assert s["absent_violations"] == ["marital_status"]
    assert s["off_whitelist"] == ["health"]
    assert s["privacy_pass"] is True


def test_score_extract_uses_judge_mapping_for_facts_and_flags() -> None:
    c = case(privacy=True, expect={"permit": "B"}, forbidden=["Marko"])
    stored = Stored(facts=["My first name is Marko.", "I hold a B permit."])
    s = score_extract(c, stored, {"permit": "B", "canton": "Zürich"}, ["My first name is Marko."])
    assert s["hits"] == 1
    assert s["leaks"] == ["Marko"]
    assert s["privacy_pass"] is False
    assert "canton" not in s["fields"]  # not a valid canton code, dropped by clean_profile


def test_check_step() -> None:
    obs = StepObs(
        writes=1,
        reads=2,
        facts_loaded=3,
        answer={
            "answer_markdown": "With your B permit you may change jobs.",
            "clarifying_question": None,
        },
        stored=Stored(profile={"permit": "B"}),
    )
    assert (
        check_step(
            {
                "stored": {"permit": "B"},
                "saved": True,
                "memory_read": True,
                "memory_used": True,
                "no_clarification": True,
                "mentions_any": ["b permit"],
                "forbidden": ["epilep"],
            },
            obs,
        )
        == []
    )
    fails = check_step(
        {"stored_empty": True, "saved": False, "memory_read": False, "facts_loaded": 0}, obs
    )
    assert len(fails) == 4


def test_check_step_stored_accepts_a_natural_language_fact() -> None:
    obs = StepObs(stored=Stored(facts=["The user holds a B permit."]))
    assert check_step({"stored": {"permit": "B"}}, obs) == []
    assert check_step({"stored": {"permit": "C"}}, obs) != []


def test_check_step_clarification() -> None:
    obs = StepObs(answer={"answer_markdown": "", "clarifying_question": "Which permit?"})
    assert check_step({"no_clarification": True}, obs) == ["asked: 'Which permit?'"]


def test_scope_filter() -> None:
    assert scope_filter({"user_id": "u", "app_name": "a"}) == (
        'scope.app_name="a" AND scope.user_id="u"'
    )


def test_mapped_model_accepts_whitelist_only() -> None:
    model = mapped_model()
    ok = model.model_validate({"profile": {"canton": "ZH", "has_children": True}, "sensitive": []})
    assert ok.model_dump()["profile"]["canton"] == "ZH"
    with pytest.raises(ValueError, match="canton"):
        model.model_validate({"profile": {"canton": "Zürich"}, "sensitive": []})


def test_chf() -> None:
    pricing = {
        "usd_to_chf": 1.0,
        "models": {"m": {"input": 1.0, "output": 2.0, "cached_input": 0.1}},
    }
    usage = {"prompt": 1_000_000, "cached": 500_000, "output": 250_000, "thoughts": 250_000}
    assert chf(usage, "m", pricing) == pytest.approx(0.5 + 0.05 + 1.0)
    assert chf(usage, "unknown", pricing) is None


def test_summarize_and_render() -> None:
    rows = [
        {
            "id": "a",
            "kind": "extract",
            "privacy": True,
            "expected": 2,
            "hits": 1,
            "missing": ["permit"],
            "wrong": {},
            "absent_violations": [],
            "extra": [],
            "off_whitelist": [],
            "leaks": [],
            "flagged_sensitive": [],
            "privacy_pass": True,
            "generate_s": 4.0,
            "stored": {"profile": {"canton": "ZH"}, "facts": []},
        },
        {"id": "b", "kind": "extract", "privacy": False, "error": "boom", "privacy_pass": False},
        {
            "id": "c",
            "kind": "e2e",
            "privacy": True,
            "pass": False,
            "privacy_pass": False,
            "steps": [
                {
                    "step": 0,
                    "forget": False,
                    "opt_in": False,
                    "writes": 1,
                    "reads": 0,
                    "facts_loaded": 0,
                    "fails": ["saved=True, want False"],
                },
            ],
        },
    ]
    s = summarize(rows)
    assert s["extract"]["field_recall"] == 50.0
    assert s["extract"]["errors"] == 1
    assert s["privacy"] == {"cases": 2, "passed": 1, "failed": ["c"]}
    assert s["e2e"] == {"cases": 1, "passed": 0}
    report = {
        "run_at": "2026-10-16T00:00:00+00:00",
        "git_sha": "abc",
        "meta": {
            "variant": "profile",
            "dataset": "d",
            "verified": "model-verified",
            "cases": 3,
            "runtime": "1",
            "generation_model": None,
            "auditor": "j",
            "agent": "a",
            "cost_chf": {"total": 0.1, "agent": 0.08, "auditor": 0.02},
        },
        "summary": s,
        "rows": rows,
    }
    md = render(report)
    assert "**Privacy cases: 1/2 passed** (failed: c)" in md
    assert "saved=True, want False" in md
    assert "error: boom" in md
