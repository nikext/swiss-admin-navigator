"""The deterministic citation check (citecheck.py) against hand-made get_article results."""

from typing import Any

import pytest

from agents.navigator.citecheck import (
    ArticleNotFoundError,
    FetchError,
    check_citations,
    clean_num,
    finalize,
    find_quote,
    make_round,
    markers,
    normalize,
    strip_markers,
)
from agents.navigator.contract import DraftAnswer, DraftCitation

P1 = (
    "Die Kündigung durch den Vermieter ist insbesondere anfechtbar, wenn sie ausgesprochen "
    "wird:\na. weil der Mieter nach Treu und Glauben Ansprüche aus dem Mietverhältnis geltend "
    "macht;\nb. weil der Vermieter eine einseitige Vertragsänderung zu Lasten des Mieters "
    "durchsetzen will;"
)
P2 = "Absatz 1 Buchstabe e ist auch anwendbar, wenn der Mieter durch Schriftstücke nachweisen kann."
ART_271A = {
    "sr": "220", "abbr": "OR", "label": "Art. 271a", "eid": "art_271_a", "lang": "de",
    "status": "in_force", "text": f"1 {P1}\n2 {P2}",
    "paragraphs": [{"num": "1", "text": P1}, {"num": "2", "text": P2}],
    "url": "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_271_a",
    "as_of": "2026-10-01", "available_langs": ["de", "fr", "it"],
}  # fmt: skip
FR = "Il est possible de déroger aux conditions d’admission (art. 18 à 29) dans les buts suivants:"
ART_30_FR = {
    "sr": "142.20", "abbr": "LEI", "label": "Art. 30", "eid": "art_30", "lang": "fr",
    "status": "in_force", "text": FR, "paragraphs": [{"num": None, "text": FR}],
    "url": "https://www.fedlex.admin.ch/eli/cc/2007/758/fr#art_30", "as_of": "2026-06-12",
    "available_langs": ["de", "fr", "it"],
}  # fmt: skip


def law(*articles: dict[str, Any], missing: str = "") -> Any:
    calls: list[tuple[str, str, str]] = []

    async def fetch(sr: str, article: str, lang: str) -> dict[str, Any]:
        calls.append((sr, article, lang))
        if article == missing:
            raise ArticleNotFoundError(f"no article {article!r} in SR {sr}")
        if article == "down":
            raise FetchError("timeout")
        for a in articles:
            if a["sr"] == sr and a["label"] == article:
                if lang in a["available_langs"] and lang != a["lang"]:
                    return a | {"lang": lang}  # pretend the other language has the same text
                return a if lang == a["lang"] else a | {"fallback": f"no {lang}"}
        raise ArticleNotFoundError(f"no article {article!r} in SR {sr}")

    fetch.calls = calls  # type: ignore[attr-defined]
    return fetch


def cite(ref: str = "1", **kw: Any) -> DraftCitation:
    base = {"ref": ref, "sr": "220", "article": "Art. 271a", "paragraph": "1", "letter": "a",
            "quote_lang": "de", "quote": "weil der Mieter nach Treu und Glauben Ansprüche aus "
            "dem Mietverhältnis geltend macht"}  # fmt: skip
    return DraftCitation.model_validate(base | kw)


def draft(*citations: DraftCitation, md: str = "Retaliation is challengeable [1].") -> DraftAnswer:
    return DraftAnswer(
        language="en", answer_markdown=md, citations=list(citations), confidence="high",
        out_of_scope=False,
    )  # fmt: skip


# --- normalisation and matching ---------------------------------------------------


def test_normalize_whitespace_apostrophes_invisibles() -> None:
    assert normalize("  a\n b  c\t") == "a b c"
    assert normalize("d’admission ‘x’ ʼy") == "d'admission 'x' 'y"
    assert normalize("Kün­digung​") == "Kündigung"


def test_find_quote_returns_the_exact_source_span() -> None:
    assert find_quote("conditions d'admission (art. 18", FR) == "conditions d’admission (art. 18"
    assert find_quote("wird: a. weil der Mieter", P1) == "wird:\na. weil der Mieter"


def test_find_quote_ellipsis_parts_must_be_in_order() -> None:
    got = find_quote("… insbesondere anfechtbar, … geltend macht; …", P1)
    assert got == "… insbesondere anfechtbar, … geltend macht; …"
    got = find_quote("Die Kündigung ... Treu und Glauben", P1)
    assert got == "Die Kündigung … Treu und Glauben"
    assert find_quote("Treu und Glauben … Die Kündigung", P1) is None


@pytest.mark.parametrize(
    "quote",
    [
        "Die Kündigung durch den Mieter ist",  # changed word
        "die kündigung durch den Vermieter",  # case
        "insbesondere anfechtbar wenn sie",  # missing comma
        "",
    ],
)
def test_find_quote_is_strict_otherwise(quote: str) -> None:
    assert find_quote(quote, P1) is None


def test_clean_num_and_markers() -> None:
    assert [clean_num(x) for x in ("Abs. 1", "al. 2", "1 bis", "lit. a", "a.", "let. c", None)] == [
        "1", "2", "1bis", "a", "a", "c", None,
    ]  # fmt: skip
    assert markers("x [2] y [1, 3] z [2] [link](u) [a]") == ["2", "1", "3"]
    assert strip_markers("A [1]. B [1, 2]. C [3].", {"1", "3"}) == "A. B [2]. C."


# --- check_citations ---------------------------------------------------------------


async def test_a_correct_citation_passes_and_gets_derived_fields() -> None:
    fetch = law(ART_271A)
    checked, problems = await check_citations(draft(cite()), fetch)
    assert problems == []
    assert checked[0].problems == []
    c = checked[0].citation
    assert (c.abbr, c.url, c.as_of) == ("OR", ART_271A["url"], "2026-10-01")
    assert c.quote == cite().quote


async def test_same_article_is_fetched_once() -> None:
    fetch = law(ART_271A)
    md = "A [1]. B [2]."
    second = cite("2", paragraph="2", letter=None, quote=P2[:40])
    checked, _ = await check_citations(draft(cite(), second, md=md), fetch)
    assert fetch.calls == [("220", "Art. 271a", "de")]
    assert all(not ch.problems for ch in checked)


@pytest.mark.parametrize(
    ("kw", "kind"),
    [
        ({"article": "Art. 999"}, "not_found"),
        ({"article": "down"}, "fetch"),
        ({"quote": "weil der Mieter nach Treu und Glauben Ansprüche geltend macht"}, "quote"),
        ({"quote": "weil der Mieter"}, "quote"),  # too short
        ({"paragraph": "4"}, "paragraph"),
        ({"letter": "f"}, "letter"),
        ({"paragraph": "2", "letter": None}, "pinpoint"),
        ({"quote_lang": "en"}, "lang"),
    ],
)
async def test_problems(kw: dict[str, Any], kind: str) -> None:
    checked, _ = await check_citations(draft(cite(**kw)), law(ART_271A, missing="Art. 999"))
    assert [p.kind for p in checked[0].problems] == [kind]
    assert checked[0].problems[0].ref == "1"


async def test_repealed_article_is_a_problem() -> None:
    repealed = ART_271A | {"status": "repealed"}
    checked, _ = await check_citations(draft(cite()), law(repealed))
    assert "not_in_force" in [p.kind for p in checked[0].problems]


async def test_unnumbered_paragraph_and_typographic_apostrophe() -> None:
    c = cite(sr="142.20", article="Art. 30", paragraph=None, letter=None, quote_lang="fr",
             quote="Il est possible de déroger aux conditions d'admission")  # fmt: skip
    checked, _ = await check_citations(draft(c), law(ART_30_FR))
    assert checked[0].problems == []
    assert checked[0].citation.quote == "Il est possible de déroger aux conditions d’admission"
    bad = c.model_copy(update={"paragraph": "1"})
    checked, _ = await check_citations(draft(bad), law(ART_30_FR))
    assert [p.kind for p in checked[0].problems] == ["paragraph"]
    assert "no numbered paragraphs" in checked[0].problems[0].message


async def test_marker_problems() -> None:
    _, problems = await check_citations(draft(cite(), md="A [1]. B [2]."), law(ART_271A))
    assert [(p.kind, p.ref) for p in problems] == [("marker", "2")]
    _, problems = await check_citations(draft(cite(), cite(), md="A [1]."), law(ART_271A))
    assert [(p.kind, p.ref) for p in problems] == [("marker", "1")]


async def test_contact_details_are_answer_problems() -> None:
    d = draft(cite()).model_copy(update={"cantonal_note": "Office, Via Chicherio 20, Camorino."})
    checked, problems = await check_citations(d, law(ART_271A))
    assert [(p.kind, p.ref) for p in problems] == [("contact", None)]
    assert "Via Chicherio 20" in problems[0].message
    answer = finalize(d, checked, problems, [make_round(checked, problems)])
    assert answer.verification.status == "degraded"
    assert answer.cantonal_note == "Office, Via Chicherio 20, Camorino."  # flagged, not edited
    assert answer.verification.repairs == [
        "1 contact detail(s) written from memory left in the answer"
    ]


# --- finalize --------------------------------------------------------------------------


async def test_finalize_passed_and_passed_after_retry() -> None:
    d = draft(cite())
    checked, ap = await check_citations(d, law(ART_271A))
    r = make_round(checked, ap)
    answer = finalize(d, checked, ap, [r])
    assert answer.verification.status == "passed"
    assert answer.notice.startswith("Unofficial. Not legal advice.")
    assert answer.confidence == "high"
    failed = r.model_copy(update={"problems": []})
    assert finalize(d, checked, ap, [failed, r]).verification.status == "passed_after_retry"


async def test_finalize_degrades_with_a_record_of_every_change() -> None:
    md = "Real [1]. Invented [2]. Misquoted [3]. Wrong paragraph [4]."
    d = draft(
        cite("1"),
        cite("2", article="Art. 999"),
        cite("3", quote="weil der Mieter nach Treu und Glauben irgendwas geltend macht"),
        cite("4", paragraph="2", letter="a"),
        md=md,
    )
    checked, ap = await check_citations(d, law(ART_271A, missing="Art. 999"))
    answer = finalize(d, checked, ap, [make_round(checked, ap)])
    v = answer.verification
    assert v.status == "degraded"
    assert answer.confidence == "low"
    assert v.dropped == ["2"]
    assert [c.ref for c in answer.citations] == ["1", "3", "4"]
    by_ref = {c.ref: c for c in answer.citations}
    assert by_ref["3"].quote is None
    assert (by_ref["4"].paragraph, by_ref["4"].letter) == ("1", "a")  # where the quote is
    assert answer.answer_markdown == "Real [1]. Invented. Misquoted [3]. Wrong paragraph [4]."
    assert len(v.repairs) == 3


async def test_finalize_infra_failure_is_unavailable_not_degraded() -> None:
    d = draft(cite(article="down"))
    checked, ap = await check_citations(d, law(ART_271A))
    answer = finalize(d, checked, ap, [make_round(checked, ap)])
    assert answer.verification.status == "unavailable"
    assert [c.ref for c in answer.citations] == ["1"]  # kept: we could not check it
