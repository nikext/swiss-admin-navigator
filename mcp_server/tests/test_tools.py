from pathlib import Path

import pytest

from mcp_server.search import Index
from mcp_server.tests.conftest import bow_vector
from mcp_server.tools import LawTools, ToolInputError, snippet


@pytest.fixture(scope="module")
def tools(fixture_index_path: Path) -> LawTools:
    return LawTools(Index(fixture_index_path))


def test_act_lookup_accepts_sr_numbers_and_abbreviations(tools: LawTools) -> None:
    assert tools.act_sr("220") == tools.act_sr("OR") == tools.act_sr("co") == "220"
    assert tools.act_sr("SR 142.20") == tools.act_sr("AuG") == "142.20"
    with pytest.raises(ToolInputError, match="unknown act 'XYZ'; known acts: 220 \\(OR\\)"):
        tools.act_sr("XYZ")


def test_search_renders_hits_with_links_and_notice(tools: LawTools) -> None:
    q = "Kündigung durch den Vermieter"
    out = tools.search(q, bow_vector(q), lang="de", k=3)
    assert out["mode"] == "dense"
    assert "Not legal advice" in out["notice"]
    hit = out["results"][0]
    assert set(hit) >= {"sr", "abbr", "label", "eid", "lang", "snippet", "url", "as_of", "score"}
    assert hit["url"].startswith("https://www.fedlex.admin.ch/eli/cc/")
    assert all(r["lang"] == "de" for r in out["results"])


def test_search_without_vector_degrades_to_keywords(tools: LawTools) -> None:
    out = tools.search("Kündigung durch den Vermieter Treu und Glauben", None, k=2)
    assert out["mode"] == "bm25"
    assert out["results"][0]["eid"] == "art_271_a"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"query": " "}, "must not be empty"),
        ({"query": "x" * 1001}, "longer than"),
        ({"query": "x", "lang": "rm"}, "lang must be one of"),
        ({"query": "x", "sr": ["NOPE"]}, "unknown act"),
    ],
)
def test_search_input_errors(tools: LawTools, kwargs: dict, message: str) -> None:
    with pytest.raises(ToolInputError, match=message):
        tools.search(qvec=None, **kwargs)


def test_search_clamps_k(tools: LawTools) -> None:
    q = "Vermieter"
    assert len(tools.search(q, bow_vector(q), k=0)["results"]) == 1
    assert len(tools.search(q, bow_vector(q), k=500)["results"]) <= 20


@pytest.mark.parametrize("article", ["271a", "Art. 271a", "art. 271 a", "art_271_a"])
def test_get_article_accepts_label_spellings(tools: LawTools, article: str) -> None:
    a = tools.get_article("OR", article)
    assert (a["sr"], a["eid"], a["label"], a["lang"]) == ("220", "art_271_a", "Art. 271a", "de")
    assert a["text"].startswith("1 Die Kündigung durch den Vermieter")
    assert a["available_langs"] == ["de", "fr"]
    assert a["paragraphs"][0]["eid"] == "art_271_a/para_1"


def test_get_article_language_fallback_and_status(tools: LawTools) -> None:
    fr = tools.get_article("220", "271a", "fr")
    assert fr["lang"] == "fr"
    assert fr["abbr"] == "CO"
    it = tools.get_article("220", "271a", "it")
    assert it["lang"] == "de"
    assert "no IT text" in it["fallback"]
    repealed = tools.get_article("220", "226a–226d")
    assert repealed["status"] == "repealed"
    assert "status_note" in repealed


def test_get_article_scoped_and_english(tools: LawTools) -> None:
    one = tools.get_article("220", "1")
    assert "disp_u2/art_1" in one["other_matches"]
    assert tools.get_article("220", "disp_u2/art_1")["status"] == "omitted"
    en = tools.get_article("ZGB", "255", "en")
    assert en["lang"] == "en"
    assert "unofficial translation" in en["translation_note"]
    with pytest.raises(ToolInputError, match="only in scoped parts"):
        tools.get_article("210", "6a")  # exists only as disp_u1/art_6_a


def test_get_article_errors(tools: LawTools) -> None:
    with pytest.raises(ToolInputError, match="no article '999'"):
        tools.get_article("220", "999")
    with pytest.raises(ToolInputError, match="cannot read article"):
        tools.get_article("220", "Kündigung")


def test_get_toc_browses_down_to_articles(tools: LawTools) -> None:
    root = tools.get_toc("OR")
    assert root["path"] is None
    assert root["children"][0]["kind"] == "level"
    # Follow first children the way an agent would: OR Art. 1 is six levels deep.
    node, seen = root, []
    while node["children"][0]["kind"] == "level":
        path = node["children"][0]["path"]
        seen.append(path)
        node = tools.get_toc("OR", path=path)
    assert seen[0] == "part_1"
    assert node["children"][0] == {
        "path": "art_1", "kind": "article", "title": node["children"][0]["title"],
        "label": "Art. 1",
    }  # fmt: skip
    deep = tools.get_toc("OR", path="part_1", depth=3)
    grandchild = deep["children"][0]["children"][0]
    assert "children" in grandchild  # expanded to the requested depth
    assert "children" not in grandchild["children"][0]  # and no further
    with pytest.raises(ToolInputError, match="no TOC node"):
        tools.get_toc("OR", path="nope")


def test_get_toc_falls_back_when_the_act_lacks_the_language(tools: LawTools) -> None:
    toc = tools.get_toc("AIG", "en")
    assert toc["lang"] == "de"
    assert "fallback" in toc


def test_list_acts_filters_by_domain(tools: LawTools) -> None:
    all_acts = tools.list_acts()["acts"]
    assert {a["sr"] for a in all_acts} == {"220", "210", "0.142.112.681", "142.20"}
    residence = tools.list_acts("residence")["acts"]
    assert {a["sr"] for a in residence} == {"0.142.112.681", "142.20"}
    assert residence[0]["abbr"]["de"] in {"FZA", "AIG"}
    with pytest.raises(ToolInputError, match="domain must be one of"):
        tools.list_acts("crime")


def test_resolve_citation_tool(tools: LawTools) -> None:
    out = tools.resolve_citation("Gemäss Art. 271a Abs. 1 lit. a OR und Art. 999 OR")
    first, second = out["citations"]
    assert (first["exists"], first["eid"], first["paragraph_eid"]) == (
        True, "art_271_a", "art_271_a/para_1",
    )  # fmt: skip
    assert second["exists"] is False
    with pytest.raises(ToolInputError):
        tools.resolve_citation("")


def test_snippet_cuts_at_a_word() -> None:
    assert snippet("kurz") == "kurz"
    s = snippet("wort " * 100, limit=22)
    assert s.endswith(" …")
    assert len(s) <= 24


def test_hits_are_shown_in_the_question_language_when_available(tools: LawTools) -> None:
    # The vector matches the German wording; the question is French.
    q = "Kündigung durch den Vermieter Treu und Glauben"
    de = tools.search(q, bow_vector(q), k=1)["results"][0]
    fr = tools.search("Le bailleur peut-il résilier le bail ?", bow_vector(q), k=1)["results"][0]
    assert (de["eid"], de["lang"]) == ("art_271_a", "de")
    assert (fr["eid"], fr["lang"]) == ("art_271_a", "fr")
    assert fr["url"].endswith("/fr#art_271_a")
    # An explicit lang filter is never overridden.
    only_de = tools.search("Le bailleur peut-il résilier le bail ?", bow_vector(q), lang="de", k=1)
    assert only_de["results"][0]["lang"] == "de"
