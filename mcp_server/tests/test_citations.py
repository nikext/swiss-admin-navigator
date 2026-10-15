"""resolve_citation: Swiss citation styles in DE/FR/IT/EN (docs/AGENTS.md §2)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from ingest.index import load_aliases
from ingest.manifest import load_acts
from mcp_server.citations import (
    Citation,
    abbreviation_table,
    norm_abbr,
    parse_citations,
    resolve,
)

# Corpus abbreviations (acts.yaml de/fr/it + aliases) and the EN ones Fedlex lists.
ROWS = [(a, act.sr, lang) for act in load_acts() for lang, a in act.abbr.items()]
ROWS += [(alias, sr, None) for sr, aliases in load_aliases().items() for alias in aliases]
ROWS += [("Cst.", "101", "en"), ("CC", "210", "en"), ("CO", "220", "en"), ("FADP", "235.1", "en")]
TABLE = abbreviation_table(ROWS)


def one(text: str) -> Citation:
    found = parse_citations(text, TABLE)
    assert len(found) == 1, found
    return found[0]


def fields(c: Citation, *names: str) -> tuple[Any, ...]:
    return tuple(getattr(c, n) for n in names)


# (text, sr, article, eid, paragraph, letter, lang_hint)
SINGLE = [
    # German
    ("Art. 271a Abs. 1 lit. a OR", "220", "Art. 271a", "art_271_a", "1", "a", "de"),
    ("Art. 271a Abs. 1 Bst. a OR", "220", "Art. 271a", "art_271_a", "1", "a", "de"),
    ("Artikel 271a OR", "220", "Art. 271a", "art_271_a", None, None, "de"),
    ("Art. 329g bis OR", "220", "Art. 329g bis", "art_329_g_bis", None, None, "de"),
    ("Art. 329gbis OR", "220", "Art. 329g bis", "art_329_g_bis", None, None, "de"),
    ("Art. 329 g bis OR", "220", "Art. 329g bis", "art_329_g_bis", None, None, "de"),
    ("Art. 48bis BV", "101", "Art. 48bis", "art_48_bis", None, None, "de"),
    ("Art. 8 BV", "101", "Art. 8", "art_8", None, None, "de"),
    ("Art. 8 Abs. 2 und 3 BV", "101", "Art. 8", "art_8", "2", None, "de"),
    ("Art. 64 Abs. 1bis KVG", "832.10", "Art. 64", "art_64", "1bis", None, "de"),
    ("Art. 34 Abs. 2 Bst. a AIG", "142.20", "Art. 34", "art_34", "2", "a", "de"),
    ("Art. 9 Abs. 1 lit. a BüG", "141.0", "Art. 9", "art_9", "1", "a", "de"),
    ("Art. 336c Abs. 1 lit. b OR", "220", "Art. 336c", "art_336_c", "1", "b", "de"),
    ("OR Art. 336c", "220", "Art. 336c", "art_336_c", None, None, "de"),
    ("Art. 34 AuG", "142.20", "Art. 34", "art_34", None, None, None),
    ("Art. 25 nDSG", "235.1", "Art. 25", "art_25", None, None, None),
    ("Art. 83 DBG", "642.11", "Art. 83", "art_83", None, None, "de"),
    # French
    ("art. 271a al. 1 let. a CO", "220", "Art. 271a", "art_271_a", "1", "a", "fr"),
    ("art. 30, al. 1, let. k, LEI", "142.20", "Art. 30", "art_30", "1", "k", "fr"),
    ("art. 9 al. 1 let. b LN", "141.0", "Art. 9", "art_9", "1", "b", "fr"),
    ("art. 34 LEtr", "142.20", "Art. 34", "art_34", None, None, None),
    ("art. 83 LIFD", "642.11", "Art. 83", "art_83", None, None, None),
    ("art. 3 LAMal", "832.10", "Art. 3", "art_3", None, None, None),
    ("art. 336c al. 1 let. c du CO", "220", "Art. 336c", "art_336_c", "1", "c", "fr"),
    ("article 271a CO", "220", "Art. 271a", "art_271_a", None, None, None),
    # Italian
    ("art. 30 cpv. 1 lett. a LStrI", "142.20", "Art. 30", "art_30", "1", "a", "it"),
    ("articolo 271a CO", "220", "Art. 271a", "art_271_a", None, None, "it"),
    ("art. 336c cpv. 1 lett. c CO", "220", "Art. 336c", "art_336_c", "1", "c", "it"),
    ("art. 8 cpv. 1 Cost.", "101", "Art. 8", "art_8", "1", None, "it"),
    ("art. 6 cpv. 2 LADI", "837.0", "Art. 6", "art_6", "2", None, "it"),
    # English (unofficial abbreviations Fedlex lists, plus FNIA)
    ("Art. 8 para. 1 Cst.", "101", "Art. 8", "art_8", "1", None, "en"),
    ("Article 25 FADP", "235.1", "Art. 25", "art_25", None, None, None),
    ("Art. 271a para. 1 let. a of the CO", "220", "Art. 271a", "art_271_a", "1", "a", "en"),
    ("Art. 34 FNIA", "142.20", "Art. 34", "art_34", None, None, None),
]


@pytest.mark.parametrize(("text", "sr", "article", "eid", "para", "letter", "lang"), SINGLE)
def test_single_citations(
    text: str,
    sr: str,
    article: str,
    eid: str,
    para: str | None,
    letter: str | None,
    lang: str | None,
) -> None:
    c = one(text)
    assert fields(c, "sr", "article", "eid", "paragraph", "letter") == (
        sr, article, eid, para, letter,
    )  # fmt: skip
    assert c.lang_hint == lang


def test_a_spaced_letter_needs_an_ordinal() -> None:
    # "Art. 5 e 6" is Italian for "Art. 5 and 6", not "Art. 5e".
    assert [c.eid for c in parse_citations("artt. 5 e 6 CO", TABLE)] == ["art_5", "art_6"]


def test_lists_yield_one_citation_per_article() -> None:
    found = parse_citations("Art. 271 und 271a OR", TABLE)
    assert [c.eid for c in found] == ["art_271", "art_271_a"]
    assert all(c.sr == "220" for c in found)
    found = parse_citations("artt. 335b e 335c CO", TABLE)
    assert [c.eid for c in found] == ["art_335_b", "art_335_c"]
    assert found[0].lang_hint == "it"
    found = parse_citations("Art. 18, 19 und 20 OR", TABLE)
    assert [c.eid for c in found] == ["art_18", "art_19", "art_20"]


def test_repeated_article_keyword_starts_a_new_article_after_components() -> None:
    found = parse_citations("Art. 335b Abs. 1 und Art. 336c Abs. 1 lit. b OR", TABLE)
    assert [(c.eid, c.paragraph, c.letter) for c in found] == [
        ("art_335_b", "1", None),
        ("art_336_c", "1", "b"),
    ]


@pytest.mark.parametrize(
    ("text", "start", "end", "lang"),
    [
        ("Art. 253–273c OR", "Art. 253", "Art. 273c", "de"),
        ("Art. 253-273c OR", "Art. 253", "Art. 273c", "de"),
        ("art. 253 à 273c CO", "Art. 253", "Art. 273c", "fr"),
        ("Art. 48 bis 50 BV", "Art. 48", "Art. 50", "de"),
    ],
)
def test_ranges(text: str, start: str, end: str, lang: str) -> None:
    c = one(text)
    assert (c.article, c.range_end) == (start, end)
    assert c.lang_hint == lang


@pytest.mark.parametrize(
    ("text", "eid"),
    [
        ("Art. 335b f. OR", "art_335_b"),
        ("Art. 12ff. ArG", "art_12"),
        ("Art. 12 ff. ArG", "art_12"),
        ("art. 271 ss. CO", "art_271"),
        ("art. 271 et ss. CO", "art_271"),
        ("art. 271 segg. CO", "art_271"),
    ],
)
def test_following_articles(text: str, eid: str) -> None:
    c = one(text)
    assert (c.eid, c.following, c.sr is not None) == (eid, True, True)


@pytest.mark.parametrize(
    ("text", "sr", "eid", "scope"),
    [
        ("Art. 1 SchlT ZGB", "210", "disp_u1/art_1", "disp_u1"),
        ("art. 1 Tit. fin. CC", "210", "disp_u1/art_1", "disp_u1"),
        ("Art. 6 Anhang I FZA", "0.142.112.681", "art_6", "annex_I"),
        ("art. 6 annexe I ALCP", "0.142.112.681", "art_6", "annex_I"),
        ("art. 6 allegato I ALC", "0.142.112.681", "art_6", "annex_I"),
    ],
)
def test_scoped_citations(text: str, sr: str, eid: str, scope: str) -> None:
    c = one(text)
    assert (c.sr, c.eid, c.scope) == (sr, eid, scope)


def test_several_citations_in_prose_keep_their_own_acts() -> None:
    text = (
        "Nach Art. 13 Abs. 1 ArG und Art. 321c OR gilt …; vgl. auch art. 30 cpv. 1 lett. a "
        "LStrI sowie Art. 61 Abs. 2 AIG; Art. 34 AIG."
    )
    found = parse_citations(text, TABLE)
    assert [(c.sr, c.eid) for c in found] == [
        ("822.11", "art_13"),
        ("220", "art_321_c"),
        ("142.20", "art_30"),
        ("142.20", "art_61"),
        ("142.20", "art_34"),
    ]
    assert text[found[1].start : found[1].end] == "Art. 321c OR"


def test_prose_words_are_not_acts() -> None:
    # Lower-case "or"/"co" in prose are not the OR/CO; "art" needs a number.
    assert one("see art. 271a or the next one").sr is None
    assert parse_citations("Startpunkt 5 and the state of the art in 2024", TABLE) == []
    assert one("Art. 2 des Obligationenrechts").sr is None


def test_citation_without_act_is_reported_not_guessed() -> None:
    c = one("Art. 271a Abs. 1")
    assert (c.sr, c.eid, c.paragraph) == (None, "art_271_a", "1")


def test_norm_abbr_ignores_case_accents_and_dots() -> None:
    assert norm_abbr("Cst.") == norm_abbr("CST") == "cst"
    assert norm_abbr("BüG") == "bug"


# --- resolution against a real (fixture) index --------------------------------


@pytest.fixture(scope="module")
def db(fixture_index_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(fixture_index_path)


def resolved(db: sqlite3.Connection, text: str) -> list[dict[str, Any]]:
    found = parse_citations(text, TABLE)
    resolve(db, found)
    return [c.as_dict() for c in found]


def test_resolve_existing_article_paragraph_and_letter(db: sqlite3.Connection) -> None:
    (r,) = resolved(db, "Art. 271a Abs. 1 lit. a OR")
    assert r["exists"] is True
    assert r["status"] == "in_force"
    assert r["paragraph_eid"] == "art_271_a/para_1"
    assert r["letter_exists"] is True
    assert r["url"] == "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_271_a"


def test_resolve_uses_the_citation_language_for_the_link(db: sqlite3.Connection) -> None:
    (r,) = resolved(db, "art. 271a al. 1 let. a CO")
    assert r["url"].endswith("/fr#art_271_a")
    assert r["lang"] == "fr"


def test_resolve_falls_back_to_german_when_language_missing(db: sqlite3.Connection) -> None:
    (r,) = resolved(db, "art. 271a cpv. 1 lett. a CO")  # no IT OR in the fixtures
    assert r["exists"] is True
    assert r["url"].endswith("/de#art_271_a")


def test_resolve_reports_missing_articles_and_paragraphs(db: sqlite3.Connection) -> None:
    (r,) = resolved(db, "Art. 999 OR")
    assert r["exists"] is False
    assert "no such article" in r["error"]
    (r,) = resolved(db, "Art. 271a Abs. 9 OR")
    assert (r["exists"], r["paragraph_exists"]) == (True, False)
    (r,) = resolved(db, "Art. 271a Abs. 1 lit. z OR")
    assert r["letter_exists"] is False


def test_resolve_article_inside_a_repealed_range(db: sqlite3.Connection) -> None:
    (r,) = resolved(db, "Art. 226b OR")
    assert r["eid"] == "art_226_a_226_d"
    assert r["status"] == "repealed"
    assert "range" in r["note"]


def test_resolve_lists_scoped_namesakes(db: sqlite3.Connection) -> None:
    (r,) = resolved(db, "Art. 1 OR")
    assert r["eid"] == "art_1"
    assert "disp_u2/art_1" in r["other_matches"]


def test_resolve_scoped_articles(db: sqlite3.Connection) -> None:
    (r,) = resolved(db, "Art. 6a SchlT ZGB")
    assert (r["exists"], r["eid"]) == (True, "disp_u1/art_6_a")
    (r,) = resolved(db, "Art. 6 Anhang I FZA")
    assert (r["exists"], r["eid"]) == (True, "annex_I/lvl_u1/lvl_II/art_6")


def test_resolve_without_act(db: sqlite3.Connection) -> None:
    (r,) = resolved(db, "Art. 271a Abs. 1")
    assert r["exists"] is False
    assert "no act" in r["error"]
