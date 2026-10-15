"""Parser rules against real Fedlex markup (fixtures cut by make_fixtures.py)."""

from pathlib import Path

import pytest

from ingest.manifest import LockedAct
from ingest.parse import Article, FileStats, article_status, parse_file

FIXTURES = Path(__file__).parent / "fixtures"

ACTS = {
    "or": LockedAct(
        sr="220",
        abbr={"de": "OR", "fr": "CO", "it": "CO"},
        eli="https://fedlex.data.admin.ch/eli/cc/27/317_321_377",
        consolidation="https://fedlex.data.admin.ch/eli/cc/27/317_321_377/20261001",
        date="2026-10-01",
        domain=["work", "housing"],
    ),
    "aig": LockedAct(
        sr="142.20",
        abbr={"de": "AIG", "fr": "LEI", "it": "LStrI"},
        eli="https://fedlex.data.admin.ch/eli/cc/2007/758",
        consolidation="https://fedlex.data.admin.ch/eli/cc/2007/758/20260612",
        date="2026-06-12",
        domain=["residence"],
    ),
    "vzae": LockedAct(
        sr="142.201",
        abbr={"de": "VZAE", "fr": "OASA", "it": "OASA"},
        eli="https://fedlex.data.admin.ch/eli/cc/2007/759",
        consolidation="https://fedlex.data.admin.ch/eli/cc/2007/759/20261001",
        date="2026-10-01",
        domain=["residence"],
    ),
    "zgb": LockedAct(
        sr="210",
        abbr={"de": "ZGB", "fr": "CC", "it": "CC"},
        eli="https://fedlex.data.admin.ch/eli/cc/24/233_245_233",
        consolidation="https://fedlex.data.admin.ch/eli/cc/24/233_245_233/20260701",
        date="2026-07-01",
        domain=["general"],
    ),
    "fza": LockedAct(
        sr="0.142.112.681",
        abbr={"de": "FZA", "fr": "ALCP", "it": "ALC"},
        eli="https://fedlex.data.admin.ch/eli/cc/2002/243",
        consolidation="https://fedlex.data.admin.ch/eli/cc/2002/243/20201215",
        date="2020-12-15",
        domain=["residence"],
    ),
    "dbg": LockedAct(
        sr="642.11",
        abbr={"de": "DBG", "fr": "LIFD", "it": "LIFD"},
        eli="https://fedlex.data.admin.ch/eli/cc/1991/1184_1184_1184",
        consolidation="https://fedlex.data.admin.ch/eli/cc/1991/1184_1184_1184/20260902",
        date="2026-09-02",
        domain=["tax"],
    ),
}


def parse(name: str, lang: str, stats: FileStats | None = None) -> dict[str, Article]:
    data = (FIXTURES / f"{name}_{lang}.xml").read_bytes()
    return {a.eid: a for a in parse_file(data, ACTS[name], lang, stats)}


@pytest.fixture(scope="module")
def or_de() -> dict[str, Article]:
    return parse("or", "de")


def test_record_identity_and_url(or_de: dict[str, Article]) -> None:
    a = or_de["art_271_a"]
    assert a.id == "220:art_271_a:de"
    assert (a.sr, a.abbr, a.lang, a.label) == ("220", "OR", "de", "Art. 271a")
    assert a.url == "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_271_a"
    assert a.consolidation_date == "2026-10-01"
    assert a.domain == ["work", "housing"]


def test_nested_lists_render_one_item_per_line(or_de: dict[str, Article]) -> None:
    para = or_de["art_271_a"].paragraphs[0]
    assert (para.eid, para.num) == ("art_271_a/para_1", "1")
    lines = para.text.split("\n")
    assert lines[0] == (
        "Die Kündigung durch den Vermieter ist insbesondere anfechtbar, "
        "wenn sie ausgesprochen wird:"
    )
    assert lines[1] == (
        "a. weil der Mieter nach Treu und Glauben Ansprüche aus dem Mietverhältnis geltend macht;"
    )
    assert any(line.startswith("e. vor Ablauf von drei Jahren") for line in lines)
    assert any(line.startswith("1. zu einem erheblichen Teil unterlegen ist;") for line in lines)
    assert or_de["art_271_a"].text.startswith("1 Die Kündigung durch den Vermieter")


def test_heading_path_and_marginal_heading(or_de: dict[str, Article]) -> None:
    a = or_de["art_271_a"]
    assert a.heading_path == [
        "Zweite Abteilung: Die einzelnen Vertragsverhältnisse",
        "Achter Titel: Die Miete",
        "Dritter Abschnitt: Kündigungsschutz bei der Miete von Wohn- und Geschäftsräumen",
        "A. Anfechtbarkeit der Kündigung",
        "II. Kündigung durch den Vermieter",
    ]
    assert a.heading == "Kündigung durch den Vermieter"
    assert a.heading_eids == [
        "part_2",
        "part_2/tit_8",
        "part_2/tit_8/chap_3",
        "part_2/tit_8/chap_3/lvl_A",
        "part_2/tit_8/chap_3/lvl_A/lvl_II",
    ]


def test_footnotes_are_stripped_and_kept_separately(or_de: dict[str, Article]) -> None:
    a = or_de["art_329_g_bis"]
    assert a.label == "Art. 329g bis"
    assert "Eingefügt" not in a.text
    assert a.text.startswith("1 Stirbt die Mutter am Tag der Niederkunft")
    assert a.notes[0].startswith("Eingefügt durch Anhang Ziff. 1 des BG vom 17. März 2023")
    assert "https://fedlex.data.admin.ch/eli/oc/2023/680" in a.refs
    # Footnotes inside container <num> (e.g. "Achter Titel: <note>Fassung gemäss…")
    assert all("Fassung gemäss" not in h for h in or_de["art_271_a"].heading_path)


@pytest.mark.parametrize(
    ("eid", "status"),
    [
        ("art_1", "in_force"),
        ("art_226_a_226_d", "repealed"),  # bare <num> + "Aufgehoben durch …" note
        ("art_732_a", "repealed"),  # body text "Aufgehoben"
        (
            "disp_u2/art_1",
            "omitted",
        ),  # "…" + "Die Änderungen können unter AS … konsultiert werden."
    ],
)
def test_status(or_de: dict[str, Article], eid: str, status: str) -> None:
    assert or_de[eid].status == status


def test_range_and_transitional_labels(or_de: dict[str, Article]) -> None:
    assert or_de["art_226_a_226_d"].label == "Art. 226a–226d"
    assert or_de["art_226_a_226_d"].text == ""
    t = or_de["disp_u2/art_1"]
    assert t.label == "Art. 1"
    assert t.heading_path[0] == "Schlussbestimmungen der Änderung vom 23. März 1962"
    assert t.heading_eids[0] == "disp_u2"


def test_french_uses_french_abbreviation_and_repeal_words() -> None:
    fr = parse("or", "fr")
    assert fr["art_271_a"].abbr == "CO"
    assert fr["art_271_a"].url.endswith("/fr#art_271_a")
    assert fr["art_226_a_226_d"].status == "repealed"  # "Abrogés par …" (plural)


def test_own_heading_and_subheading() -> None:
    vzae = parse("vzae", "de")
    assert vzae["art_1_a"].heading == "Unselbstständige Erwerbstätigkeit (Art. 11 Abs. 2 AIG)"
    aig = parse("aig", "de")
    # No own heading and no marginal level: the section heading stays in the path only.
    assert aig["art_30"].heading is None
    assert aig["art_30"].heading_path[-1] == (
        "3. Abschnitt: Abweichungen von den Zulassungsvoraussetzungen"
    )
    assert aig["art_120_a_120_c"].label == "Art. 120a–120c"


def test_annex_articles_are_ingested_with_scoped_eids() -> None:
    fza = parse("fza", "de")
    a = fza["annex_I/lvl_u1/lvl_II/art_6"]
    assert a.label == "Art. 6"
    assert a.heading == "Aufenthaltsregelung"
    assert a.heading_path == ["Anhang I", "Freizügigkeit", "II. Arbeitnehmer"]
    assert a.heading_eids == ["annex_I", "annex_I/lvl_u1", "annex_I/lvl_u1/lvl_II"]
    assert a.paragraphs[0].num == "(1)"
    assert a.url.endswith("/de#annex_I/lvl_u1/lvl_II/art_6")


def test_tables_render_as_rows_without_empty_cells() -> None:
    text = parse("dbg", "de")["art_36"].text
    assert "für | 33 200 Franken Einkommen | 138.60" in text
    assert "  " not in text
    assert "| |" not in text


def test_articles_whose_number_disagrees_with_eid_are_dropped() -> None:
    stats = FileStats()
    en = parse("zgb", "en", stats)
    # Fedlex EN ZGB: eId art_256 prints "Art. 255a", one of two art_258 prints "Art. 256".
    assert "art_256" not in en
    assert "art_255" in en
    assert en["art_258"].text  # the art_258 that really is Art. 258 survives
    assert len(stats.dropped) == 2
    assert all("disagrees" in d for d in stats.dropped)


def test_zgb_schlusstitel_and_books() -> None:
    zgb = parse("zgb", "de")
    assert zgb["art_1"].heading_path[0].startswith("Einleitung")
    assert zgb["disp_u1/art_6_a"].label == "Art. 6a"


@pytest.mark.parametrize(
    ("text", "notes", "status"),
    [
        ("", ["Aufgehoben durch Ziff. I des BG vom …"], "repealed"),
        ("", ["Abrogés par le ch. II …"], "repealed"),
        ("", ["Abrogati dalla cifra I …"], "repealed"),
        ("", [], "omitted"),
        ("…", ["Die Änderungen können unter AS 1962 1047 konsultiert werden."], "omitted"),
        ("...", ["Abrogato dal n. I …"], "repealed"),
        ("Aufgehoben", [], "repealed"),
        ("Abrogé", [], "repealed"),
        ("Abrogées.", [], "repealed"),
        ("Repealed", [], "repealed"),
        ("Artikel 37 gilt sinngemäss.", [], "in_force"),
        ("Aufgehoben ist nur Abs. 2.", [], "in_force"),
    ],
)
def test_article_status_rules(text: str, notes: list[str], status: str) -> None:
    assert article_status(text, notes) == status
