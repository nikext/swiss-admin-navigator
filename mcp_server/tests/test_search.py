from pathlib import Path

import numpy as np
import pytest

from mcp_server.search import (
    Index,
    SearchConfig,
    Searcher,
    fts_query,
    guess_lang,
    query_terms,
    served_config,
)
from mcp_server.tests.conftest import bow_vector


@pytest.fixture(scope="module")
def index(fixture_index_path: Path) -> Index:
    return Index(fixture_index_path)


def test_query_terms_drop_function_words_and_short_trigram_terms() -> None:
    assert query_terms("Darf mein Vermieter kündigen, weil ich Mängel habe?", "unicode61") == [
        "darf", "vermieter", "kündigen", "weil", "mängel",
    ]  # fmt: skip
    assert "ab" in query_terms("ab 18 Jahren", "unicode61")
    assert query_terms("ab 18 Jahren", "trigram") == ["jahren"]


def test_fts_query_quotes_terms_and_supports_prefix_and_body_only() -> None:
    assert fts_query('Mieter "Kündigung"', "unicode61") == '"mieter" OR "kündigung"'
    assert fts_query("Mieter", "unicode61", prefix=True) == '"mieter"*'
    assert fts_query("Mieter", "trigram", prefix=True) == '"mieter"'  # no prefix in trigram
    assert fts_query("Mieter", "unicode61", header=False) == 'body : ("mieter")'
    assert fts_query("der die das", "unicode61") is None


def test_bm25_finds_the_retaliation_article(index: Index) -> None:
    for tok in ("unicode61", "trigram"):
        s = Searcher(index, SearchConfig(mode="bm25", tokenizer=tok))
        hits = s.search("Kündigung durch den Vermieter Ansprüche Treu und Glauben", k=3)
        assert (hits[0].sr, hits[0].eid) == ("220", "art_271_a"), tok


def test_search_returns_in_force_articles_only(index: Index) -> None:
    s = Searcher(index, SearchConfig(mode="bm25", tokenizer="unicode61"))
    hits = s.search("Aufgehoben", k=20)  # repealed records have no chunks
    assert all(h.eid != "art_226_a_226_d" for h in hits)


def test_language_filter_and_cross_language_collapse(index: Index) -> None:
    s = Searcher(index, SearchConfig(mode="dense"))
    q = bow_vector("Kündigung durch den Vermieter résiliation bailleur")
    any_lang = s.search("", q, k=10)
    keys = [(h.sr, h.eid) for h in any_lang]
    assert len(keys) == len(set(keys))  # DE and FR versions collapse to one article
    fr = s.search("", q, lang="fr", k=10)
    assert fr
    assert all(h.lang == "fr" for h in fr)
    only_zgb = s.search("", q, srs=["210"], k=10)
    assert only_zgb
    assert all(h.sr == "210" for h in only_zgb)


def test_dense_truncation_renormalises(index: Index) -> None:
    rowids, m = index.space("bow", dims=16)
    assert m.shape[1] == 16
    np.testing.assert_allclose(np.linalg.norm(m, axis=1), 1.0, rtol=1e-5)
    assert len(rowids) == m.shape[0]


def test_hybrid_fuses_with_rrf_and_records_ranks(index: Index) -> None:
    q = "Kündigung durch den Vermieter"
    hybrid = Searcher(index, SearchConfig(mode="hybrid", tokenizer="unicode61"))
    hits = hybrid.search(q, bow_vector(q), k=5)
    top = hits[0]
    assert set(top.ranks) <= {"bm25", "dense"}
    expected = sum(1 / (60 + r) for r in top.ranks.values())
    assert top.score == pytest.approx(expected)
    assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)


def test_bm25_weight_scales_its_contribution(index: Index) -> None:
    q = "Kündigung durch den Vermieter"
    full = Searcher(index, SearchConfig(mode="hybrid", tokenizer="unicode61")).search(
        q, bow_vector(q), k=20
    )
    zero = Searcher(
        index, SearchConfig(mode="hybrid", tokenizer="unicode61", bm25_weight=0.0)
    ).search(q, bow_vector(q), k=20)
    dense = Searcher(index, SearchConfig(mode="dense")).search(q, bow_vector(q), k=20)
    assert [(h.sr, h.eid) for h in zero][: len(dense)] == [(h.sr, h.eid) for h in dense]
    assert any(h.ranks.get("bm25") for h in full)


def test_dense_needs_a_vector(index: Index) -> None:
    with pytest.raises(ValueError, match="needs a query vector"):
        Searcher(index, SearchConfig(mode="dense")).search("x")


def test_served_config_follows_index_default_and_env(index: Index) -> None:
    assert served_config(index).mode == "dense"
    assert served_config(index, {"SEARCH_MODE": "hybrid"}).mode == "hybrid"
    with pytest.raises(ValueError, match="SEARCH_MODE"):
        served_config(index, {"SEARCH_MODE": "magic"})


def test_missing_index_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="make index"):
        Index(tmp_path / "nope.sqlite")


@pytest.mark.parametrize(
    ("query", "lang"),
    [
        ("Wie viele Ferien habe ich pro Jahr?", "de"),
        ("Combien de temps dure le congé de paternité ?", "fr"),
        ("Posso cambiare cantone con un permesso B?", "it"),
        ("La Costituzione protegge la mia sfera privata?", "it"),
        ("Can my landlord evict me?", "en"),
        ("Mietkaution", None),  # no function words: no guess
    ],
)
def test_guess_lang(query: str, lang: str | None) -> None:
    assert guess_lang(query) == lang
