"""Deterministic parts of the answer eval: cases, metrics, cost, judge scoring."""

import json
from pathlib import Path
from typing import Any

import pytest

from agents.navigator.citecheck import ArticleNotFoundError, FetchError
from evals.harness.agent_run import Usage
from evals.harness.answer_metrics import (
    CitationCheck,
    behaviour_ok,
    check_citations,
    citation_scores,
    cost_usd,
    detect_lang,
    percentile,
    ratio_ci,
)
from evals.harness.cases import DRAFTS, Case, load_cases
from evals.harness.judge import (
    EXPECTED_BEHAVIOUR,
    ClaimVerdict,
    FactVerdict,
    Judgement,
    groundedness,
    key_fact_coverage,
    payload,
)

ART = {
    "sr": "220", "eid": "art_257_e", "label": "Art. 257e", "lang": "de", "status": "in_force",
    "text": "2 Bei der Miete von Wohnräumen darf der Vermieter höchstens drei Monatszinse als "
    "Sicherheit verlangen.",
}  # fmt: skip


def case(**kw: Any) -> Case:
    base = {"id": "x", "lang": "de", "question": "?", "category": "answerable", "domain": "housing"}
    return Case.model_validate(base | kw)


def cite(ref: str, article: str, quote: str | None, lang: str = "de") -> dict[str, Any]:
    return {"ref": ref, "sr": "220", "article": article, "quote_lang": lang, "quote": quote}


async def get_article(sr: str, article: str, lang: str) -> dict[str, Any]:
    if article == "down":
        raise FetchError("timeout")
    if article != "Art. 257e":
        raise ArticleNotFoundError(article)
    return ART if lang == "de" else ART | {"lang": "de", "fallback": f"no {lang}"}


async def test_check_citations_independently() -> None:
    answer = {
        "citations": [
            cite("1", "Art. 257e", "höchstens drei Monatszinse als Sicherheit verlangen"),
            cite("2", "Art. 257e", "höchstens vier Monatszinse"),
            cite("3", "Art. 9999", "x"),
            cite("4", "down", "y"),
            cite("5", "Art. 257e", None),
            cite("6", "Art. 257e", "höchstens drei Monatszinse als Sicherheit verlangen", "fr"),
        ]
    }
    checks = await check_citations(answer, get_article)
    assert [c.exists for c in checks] == [True, True, False, None, True, True]
    assert [c.verbatim for c in checks] == [True, False, None, None, None, False]
    assert checks[0].eid == "art_257_e"
    assert checks[0].text == ART["text"]
    assert checks[5].text is None  # served in another language: not the quoted text


def test_citation_scores() -> None:
    c = case(expected_citations=[
        {"sr": "220", "eid": "art_257_e"},
        {"sr": "220", "eid": "art_257_f", "required": False},
        {"sr": "220", "eid": "art_271_a"},
    ])  # fmt: skip
    checks = [
        CitationCheck("1", "220", "Art. 257e", "de", eid="art_257_e", exists=True),
        CitationCheck("2", "220", "Art. 1", "de", eid="art_1", exists=True),
        CitationCheck("3", "220", "Art. 9", "de", exists=False),
    ]
    assert citation_scores(c, checks) == {"required_recall": 0.5, "precision_expected": 0.5}
    assert citation_scores(case(), []) == {"required_recall": None, "precision_expected": None}


@pytest.mark.parametrize(
    ("category", "answer", "hallucinated", "ok"),
    [
        ("answerable", {"citations": [1]}, 0, True),
        ("answerable", {"citations": [1], "clarifying_question": "EU?"}, 0, False),
        ("answerable", {"citations": []}, 0, False),
        ("needs_clarification", {"clarifying_question": "EU or not?"}, 0, True),
        ("needs_clarification", {"clarifying_question": "  "}, 0, False),
        ("cantonal_pointer", {"cantonal_note": "Ask the commune."}, 0, True),
        ("cantonal_pointer", {"cantonal_note": None}, 0, False),
        ("out_of_scope", {"out_of_scope": True}, 0, True),
        ("out_of_scope", {"out_of_scope": False}, 0, False),
        ("adversarial", {}, 0, True),
        ("adversarial", {}, 1, False),
    ],
)
def test_behaviour_rules(category: str, answer: dict, hallucinated: int, ok: bool) -> None:
    assert behaviour_ok(case(category=category), answer, hallucinated) is ok


def test_cost_usd() -> None:
    pricing = {"models": {"m": {"input": 1.0, "output": 10.0, "cached_input": 0.1}}}
    usage = Usage(model_calls=2, prompt=1_000_000, cached=500_000, output=100_000, thoughts=100_000)
    assert cost_usd("m", usage, pricing) == pytest.approx(0.5 + 0.05 + 2.0)
    assert cost_usd("unknown", usage, pricing) is None


def test_ratio_ci_and_percentile() -> None:
    ci = ratio_ci([1, 1, 0, 1], [1, 1, 1, 1])
    assert ci is not None
    assert 0 <= ci[0] <= 0.75 <= ci[1] <= 1
    assert ratio_ci([2, 2], [2, 2]) == (1.0, 1.0)
    assert ratio_ci([0], [0]) is None
    assert percentile([3, 1, 2], 0.5) == 2
    assert percentile([], 0.5) is None


@pytest.mark.parametrize(
    ("text", "lang"),
    [
        ("Die Kündigung ist anfechtbar, wenn sie gegen Treu und Glauben verstösst.", "de"),
        ("Le congé est annulable lorsqu'il contrevient aux règles de la bonne foi.", "fr"),
        ("La disdetta è contestabile se contraria alle regole della buona fede.", "it"),
        ("The termination can be challenged if it violates the principle of good faith.", "en"),
        ("", None),
    ],
)
def test_detect_lang(text: str, lang: str | None) -> None:
    assert detect_lang(text) == lang


def test_judge_scores_and_payload() -> None:
    j = Judgement(
        claims=[
            ClaimVerdict(claim="a", refs=["1"], supported="yes"),
            ClaimVerdict(claim="b", refs=[], supported="no"),
            ClaimVerdict(claim="c", refs=["1"], supported="partly"),
            ClaimVerdict(claim="d", refs=["1"], supported="yes"),
        ],
        key_facts=[
            FactVerdict(fact="f", verdict="stated"),
            FactVerdict(fact="g", verdict="missing"),
        ],
        must_not=[], behaviour_ok=True, behaviour_note="", irrelevant_refs=[],
    )  # fmt: skip
    assert groundedness(j) == pytest.approx(2.5 / 4)
    assert key_fact_coverage(j) == 0.5
    empty = j.model_copy(update={"claims": [], "key_facts": []})
    assert groundedness(empty) is None
    assert key_fact_coverage(empty) is None
    p = payload(case(), {"answer_markdown": "x", "citations": [cite("1", "Art. 1", "q")]}, [])
    assert p["expected_behaviour"] == EXPECTED_BEHAVIOUR["answerable"]
    assert p["answer"]["citations"][0]["quote"] == "q"
    assert set(EXPECTED_BEHAVIOUR) == set(Case.model_fields["category"].annotation.__args__)  # type: ignore[union-attr]


def test_cases_load_and_validate(tmp_path: Path) -> None:
    good = {"id": "a", "lang": "de", "question": "?", "category": "answerable", "domain": "work"}
    path = tmp_path / "c.jsonl"
    path.write_text(json.dumps(good) + "\n\n" + json.dumps(good | {"id": "b"}) + "\n")
    assert [c.id for c in load_cases(path)] == ["a", "b"]
    path.write_text(json.dumps(good) + "\n" + json.dumps(good) + "\n")
    with pytest.raises(ValueError, match="duplicate ids"):
        load_cases(path)
    path.write_text(json.dumps(good | {"colour": "red"}) + "\n")
    with pytest.raises(ValueError, match=r"c.jsonl:1"):
        load_cases(path)


def test_draft_dataset_is_valid_and_unverified() -> None:
    cases = load_cases(DRAFTS)
    assert len(cases) >= 30
    assert sum(c.smoke for c in cases) == 20
    assert all(c.verified_by is None for c in cases)  # only Nikola verifies (CLAUDE.md)
    assert {c.lang for c in cases} == {"de", "fr", "it", "en"}
