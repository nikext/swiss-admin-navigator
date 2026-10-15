from typing import Any

from ingest.chunk import MAX_CHARS, chunk_corpus, chunk_record, header_for, split_text


def record(text: str, paragraphs: list[dict[str, Any]] | None = None, **kw: Any) -> dict[str, Any]:
    base = {
        "id": "220:art_1:de", "sr": "220", "abbr": "OR", "lang": "de", "eid": "art_1",
        "label": "Art. 1", "heading": "Abschluss des Vertrages",
        "heading_path": ["Erste Abteilung: Allgemeine Bestimmungen", "Erster Titel"],
        "text": text, "paragraphs": paragraphs or [], "status": "in_force",
    }  # fmt: skip
    return base | kw


def test_header_has_abbr_label_heading_title_and_path_on_one_line() -> None:
    h = header_for(record("x"), "Obligationenrecht")
    assert h == (
        "OR Art. 1: Abschluss des Vertrages — Obligationenrecht › "
        "Erste Abteilung: Allgemeine Bestimmungen › Erster Titel"
    )
    assert "\n" not in h
    assert header_for(record("x", heading=None, heading_path=[]), None) == "OR Art. 1"
    # "|" separates title and text in the embedding input format.
    assert "|" not in header_for(record("x", heading="a | b"), None)


def test_short_article_is_one_chunk_pointing_at_the_article() -> None:
    (c,) = chunk_record(record("1 Kurz."), "OR")
    assert (c.id, c.eid, c.anchor, c.part, c.parts) == ("220:art_1:de#0", "art_1", "art_1", 0, 1)
    assert c.text == "1 Kurz."


def test_long_article_splits_at_paragraphs_and_keeps_paragraph_anchors() -> None:
    paras = [
        {"eid": f"art_1/para_{i}", "num": str(i), "text": f"Satz {i} " + "x" * 50}
        for i in range(1, 6)
    ]
    text = "\n".join(f"{p['num']} {p['text']}" for p in paras)
    chunks = chunk_record(record(text, paras), None, limit=130)
    assert [c.anchor for c in chunks] == ["art_1/para_1", "art_1/para_3", "art_1/para_5"]
    assert all(len(c.text) <= 130 for c in chunks)
    assert "\n".join(c.text for c in chunks) == text  # nothing lost or reordered
    assert {c.parts for c in chunks} == {3}
    assert all(c.eid == "art_1" for c in chunks)


def test_one_huge_paragraph_splits_at_lines_then_words() -> None:
    lines = [f"{i}. Übergangsbestimmung " + "y" * 40 for i in range(10)]
    giant = "z " * 200
    para = [{"eid": "art_197/para_1", "num": None, "text": "\n".join([*lines, giant.strip()])}]
    rec = record(para[0]["text"], para, eid="art_197", id="101:art_197:de")
    pieces = split_text(rec, limit=150)
    assert all(len(t) <= 150 for _, t in pieces)
    assert {a for a, _ in pieces} == {"art_197/para_1"}
    assert " ".join(" ".join(t for _, t in pieces).split()) == " ".join(rec["text"].split())


def test_corpus_chunks_only_in_force_records() -> None:
    recs = [record("a"), record("", status="repealed", id="220:art_2:de", eid="art_2")]
    chunks = chunk_corpus(recs, {("220", "de"): "Obligationenrecht"})
    assert [c.article_id for c in chunks] == ["220:art_1:de"]
    assert "Obligationenrecht" in chunks[0].header


def test_default_limit_is_about_1200_tokens() -> None:
    assert 4000 <= MAX_CHARS <= 6000
