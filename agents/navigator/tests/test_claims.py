"""The LLM claim checker's deterministic parts (payload, problems, claim removal) and its
place in the verifier, with a fake checker (no model)."""

from typing import Any

import pytest
from google.adk.agents.callback_context import CallbackContext

from agents.navigator.citecheck import check_citations, finalize, make_round, remove_claims
from agents.navigator.claims import payload, problems
from agents.navigator.contract import ClaimCheck, DraftAnswer, Round, TokenUsage
from agents.navigator.tests.test_citecheck import ART_271A, cite, draft, law
from agents.navigator.tests.test_verifier import (
    FakeToolset,
    check_call,
    final,
    text_response,
)
from agents.navigator.verifier import CitationVerifier

MD = (
    "Die Kündigung ist anfechtbar, wenn sie wegen Ansprüchen erfolgt [1]. Die Frist "
    "beträgt 30 Tage [2].\n\n"
    "- Der Vermieter muss gemäss Art. 271a OR das Formular verwenden [1].\n"
    "- Das Geld darf nicht auf das private Konto fliessen.\n"
    "- Drittens gilt etwas Wichtiges [1, 2].\n\n"
    "Weitere Infos beim Kanton."
)


def claim(text: str, supported: str = "no", refs: tuple[str, ...] = ("1",)) -> ClaimCheck:
    return ClaimCheck.model_validate(
        {"claim": text, "refs": list(refs), "supported": supported, "issue": "not in the text"}
    )


# --- remove_claims ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("claim_text", "expected"),
    [
        (
            "Die Frist beträgt 30 Tage",
            MD.replace(" Die Frist beträgt 30 Tage [2].", ""),
        ),
        (  # a list item left empty goes with its line
            "Das Geld darf nicht auf das private Konto fliessen",
            MD.replace("- Das Geld darf nicht auf das private Konto fliessen.\n", ""),
        ),
        (  # part of a sentence: the sentence goes; "Art. 271a" does not end a sentence
            "das Formular verwenden",
            MD.replace(
                "- Der Vermieter muss gemäss Art. 271a OR das Formular verwenden [1].\n", ""
            ),
        ),
        (  # markers in the claim are ignored
            "Drittens gilt etwas Wichtiges [1, 2]",
            MD.replace("- Drittens gilt etwas Wichtiges [1, 2].\n", ""),
        ),
        ("Weitere Infos beim Kanton", MD.removesuffix("\n\nWeitere Infos beim Kanton.")),
    ],
)
def test_remove_claims(claim_text: str, expected: str) -> None:
    assert remove_claims(MD, [claim_text]) == (expected, [claim_text])


def test_remove_claims_leaves_unlocatable_short_and_whole_text_alone() -> None:
    assert remove_claims(MD, ["steht nirgends im Text der Antwort"]) == (MD, [])
    assert remove_claims(MD, ["30 Tage"]) == (MD, [])  # too short to locate safely
    only = "Die Frist beträgt dreissig Tage [1]."
    assert remove_claims(only, ["Die Frist beträgt dreissig Tage"]) == (only, [])


# --- payload and problems -----------------------------------------------------------


async def test_payload_has_the_cited_text_once_per_article() -> None:
    d = draft(cite("1"), cite("2"), md="A [1]. B [2].")
    checked, _ = await check_citations(d, law(ART_271A))
    data = payload("Can my landlord evict me?", d, checked)
    assert data["question"] == "Can my landlord evict me?"
    assert data["draft"]["answer_markdown"] == "A [1]. B [2]."
    assert [c["ref"] for c in data["draft"]["citations"]] == ["1", "2"]
    assert data["draft"]["citations"][0]["abbr"] == "OR"
    assert data["cited_law"] == [
        {"refs": ["1", "2"], "act": "OR", "article": "Art. 271a", "lang": "de",
         "text": ART_271A["text"]}
    ]  # fmt: skip


def test_problems_only_for_partly_and_no() -> None:
    found = problems(
        [claim("A holds", "yes"), claim("B holds", "partly"), claim("C holds", "no", refs=())]
    )
    assert [(p.kind, p.ref) for p in found] == [("unsupported", "1"), ("unsupported", None)]
    assert '"B holds" ([1]) is only partly supported' in found[0].message
    assert "not in the text" in found[0].message
    assert "(no citation) is not supported" in found[1].message


async def test_finalize_drops_claims_still_rated_no() -> None:
    md = "Retaliation is challengeable [1]. Tenants always win in court [1]."
    d = draft(cite(), md=md)
    checked, answer_problems = await check_citations(d, law(ART_271A))
    last = make_round(checked, answer_problems)
    last.claims = [claim("Tenants always win in court"), claim("Partly so here", "partly")]
    last.problems += problems(last.claims)
    answer = finalize(d, checked, answer_problems, [last])
    assert answer.answer_markdown == "Retaliation is challengeable [1]."
    assert answer.verification.dropped_claims == ["Tenants always win in court"]
    assert answer.verification.status == "degraded"
    assert answer.confidence == "low"
    assert answer.citations[0].quote  # deterministic parts untouched


# --- in the verifier ----------------------------------------------------------------


class FakeChecker:
    """Returns the queued verdicts, one list per call."""

    def __init__(self, *verdicts: list[ClaimCheck] | Exception) -> None:
        self.verdicts = list(verdicts)
        self.questions: list[str] = []

    async def check(
        self, question: str, draft: DraftAnswer, checked: Any
    ) -> tuple[list[ClaimCheck], TokenUsage, float]:
        self.questions.append(question)
        v = self.verdicts.pop(0)
        if isinstance(v, Exception):
            raise v
        return v, TokenUsage(model_calls=1, prompt=100, output=10), 0.5


def verifier(checker: FakeChecker, observed: list | None = None) -> CitationVerifier:
    def observe(c: CallbackContext, text: str, r: Round, response: Any) -> None:
        if observed is not None:
            observed.append(r)

    return CitationVerifier(FakeToolset(), claims=checker, observer=observe)  # type: ignore[arg-type]


GOOD = draft(cite(), md="Retaliation is challengeable [1].").model_dump_json()


async def test_unsupported_claims_are_sent_back_then_pass(ctx: CallbackContext) -> None:
    observed: list[Round] = []
    checker = FakeChecker([claim("Retaliation is challengeable")], [claim("x" * 25, "yes")])
    v = verifier(checker, observed)
    assert v.max_retries == 2  # two redrafts with the claim checker
    args = check_call(await v.after_model(ctx, text_response(GOOD)))
    assert [p["kind"] for p in args["problems"]] == ["unsupported"]
    answer = final(await v.after_model(ctx, text_response(GOOD)))
    assert answer["verification"]["status"] == "passed_after_retry"
    rounds = answer["verification"]["rounds"]
    assert rounds[0]["claims"][0]["supported"] == "no"
    assert rounds[0]["claims_usage"]["prompt"] == 100
    assert rounds[0]["check_s"] is not None
    assert [len(r.problems) for r in observed] == [1, 0]


async def test_claims_are_dropped_after_the_last_round(ctx: CallbackContext) -> None:
    md = "Retaliation is challengeable [1]. Tenants always win in court [1]."
    text = draft(cite(), md=md).model_dump_json()
    bad = [claim("Tenants always win in court")]
    v = verifier(FakeChecker(bad, bad, bad))
    check_call(await v.after_model(ctx, text_response(text)))
    check_call(await v.after_model(ctx, text_response(text)))
    answer = final(await v.after_model(ctx, text_response(text)))
    assert answer["answer_markdown"] == "Retaliation is challengeable [1]."
    assert answer["verification"]["dropped_claims"] == ["Tenants always win in court"]
    assert len(answer["verification"]["rounds"]) == 3


async def test_checker_skipped_on_deterministic_problems_and_failures(
    ctx: CallbackContext,
) -> None:
    checker = FakeChecker(RuntimeError("model down"))
    v = verifier(checker)
    bad = draft(cite(article="Art. 999")).model_dump_json()
    args = check_call(await v.after_model(ctx, text_response(bad)))
    assert [p["kind"] for p in args["problems"]] == ["not_found"]
    assert checker.questions == []  # not run on a draft with deterministic problems
    answer = final(await v.after_model(ctx, text_response(GOOD)))
    assert answer["verification"]["status"] == "passed_after_retry"  # the failure is not a veto
    assert answer["verification"]["rounds"][1]["claims"] is None


async def test_no_citations_no_claim_check(ctx: CallbackContext) -> None:
    checker = FakeChecker()
    no_cites = draft(md="Which permit do you hold?").model_dump_json()
    answer = final(await verifier(checker).after_model(ctx, text_response(no_cites)))
    assert answer["verification"]["status"] == "passed"
    assert checker.questions == []
