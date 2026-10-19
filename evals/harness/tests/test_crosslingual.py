"""E5 tables: questions across languages."""

from typing import Any

from evals.harness.crosslingual import grid, question_id, tables


def row(id_: str, lang: str, g: float = 0.8, error: str | None = None) -> dict[str, Any]:
    return {
        "id": id_, "lang": lang, "error": error, "groundedness": g, "key_facts": 1.0,
        "behaviour_ok": error is None, "required_recall": 1.0, "lang_ok": True,
        "answer": {"citations": [{"quote": "q", "quote_lang": "de"}]},
    }  # fmt: skip


def test_question_id_strips_only_a_language_suffix() -> None:
    assert question_id({"id": "housing-02-en"}) == "housing-02"
    assert question_id({"id": "housing-02"}) == "housing-02"
    assert question_id({"id": "social-11-de"}) == "social-11"


def test_grid_keeps_questions_answered_in_all_languages() -> None:
    translated = [
        row("q-1-en", "en"),
        row("q-1-fr", "fr"),
        row("q-1-it", "it"),
        row("q-2-en", "en"),
    ]
    original = [row("q-1", "de"), row("q-2", "fr"), row("other", "de")]
    g = grid(translated, original)
    assert list(g) == ["q-1"]
    assert not g["q-1"]["de"]["translated"]
    assert g["q-1"]["en"]["translated"]


def test_tables_pair_by_question() -> None:
    translated = [row("q-1-en", "en", 0.5), row("q-1-fr", "fr"), row("q-1-it", "it", error="x")]
    g = grid(translated, [row("q-1", "de", 1.0)])
    out = tables(g)
    assert "| DE | 1 | 0 | 100.0 (100.0–100.0) |" in out
    assert "| EN | -50.0 (-50.0…-50.0) |" in out
    assert "| IT | – | – | -100.0 (-100.0…-100.0) |" in out  # an error: no quality, a failure
    assert "| behaviour | 100.0 | 66.7 |" in out
    assert "de 100%" in out
