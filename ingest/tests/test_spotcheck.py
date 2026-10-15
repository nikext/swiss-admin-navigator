import pytest
from lxml import html

from ingest.spotcheck import comparable, html_article_text, without_subheading


def test_html_article_text_drops_heading_and_footnotes_and_separates_blocks() -> None:
    page = html.fromstring(
        '<article id="art_1"><h6><a>Art. 1</a><sup><a href="#fn-1">7</a></sup></h6>'
        "<div><p><sup>1</sup>\xa0Erster Satz.</p><p><sup>2</sup>\xa0Zweiter"
        '<sup><a href="#fn-2">8</a></sup> Satz.</p>'
        '<div class="footnotes"><p>7 Eingefügt durch …</p></div></div></article>'
    )
    assert html_article_text(page) == "1 Erster Satz. 2 Zweiter Satz."


def test_comparable_ignores_table_pipes_and_nbsp() -> None:
    assert comparable("für | 33 200\xa0Franken\n| 138.60") == "für 33 200 Franken 138.60"


@pytest.mark.parametrize(
    ("theirs", "heading", "expected"),
    [
        (
            "(art. 30, al. 1, let. k, LEI) 1 Les",
            "Réadmission (art. 30, al. 1, let. k, LEI)",
            "1 Les",
        ),
        ("(Art. 6 Abs. 6 (Anhang I) FZA) 1 Die", "Titel (Art. 6 Abs. 6 (Anhang I) FZA)", "1 Die"),
        ("(art. 30 LEI) 1 Les", "Autre titre", "(art. 30 LEI) 1 Les"),  # not our subheading
        ("(art. 30 LEI) 1 Les", None, "(art. 30 LEI) 1 Les"),
    ],
)
def test_without_subheading(theirs: str, heading: str | None, expected: str) -> None:
    assert without_subheading(theirs, heading) == expected
