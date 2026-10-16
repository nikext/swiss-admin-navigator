from __future__ import annotations

import pytest

from agents.navigator.contact import answer_contact_details, contact_details


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # the mobility-09 baseline answer (issue #7)
        (
            "Sezione della circolazione (Via Chicherio 20, 6512 Giubiasco / Camorino), "
            "vedi ti.ch/circolazione.",
            [
                ("street address", "Via Chicherio 20"),
                ("postcode", "6512 Giubiasco"),
                ("web address", "ti.ch/circolazione"),
            ],
        ),
        ("Bezirksgericht, Badenerstrasse 90, 8004 Zürich", [
            ("street address", "Badenerstrasse 90"), ("postcode", "8004 Zürich")]),
        ("Rue de la Gare 12, CH-2000 Neuchâtel", [
            ("street address", "Rue de la Gare 12"), ("postcode", "CH-2000 Neuchâtel")]),
        ("Tel. +41 58 123 45 67 oder 044 412 31 31", [
            ("phone number", "+41 58 123 45 67"), ("phone number", "044 412 31 31")]),
        ("online via job-room.ch or https://www.vd.ch/themes", [
            ("web address", "job-room.ch"), ("web address", "https://www.vd.ch/themes")]),
    ],
)  # fmt: skip
def test_finds_contact_details(text: str, expected: list[tuple[str, str]]) -> None:
    assert contact_details(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "Art. 271a Abs. 1 lit. a OR, innert 30 Tagen nach Empfang der Kündigung.",
        "Seit dem 1. Januar 2025 gilt ein Mindestlohn von CHF 4000 pro Monat.",
        "ab CHF 120 000 Bruttolohn, 2 bis 5 Jahre im Kanton, 260 Taggelder",
        "Siehe https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_271_a",
        "the cantonal migration office (Office cantonal de la population et des migrations)",
        "La strada 2 corsie",
    ],
)
def test_ignores_law_text_numbers_and_fedlex(text: str) -> None:
    assert contact_details(text) == []


def test_answer_fields() -> None:
    answer = {"answer_markdown": "See [1].", "cantonal_note": "www.zh.ch", "citations": ["x.ch"]}
    assert answer_contact_details(answer) == [("web address", "www.zh.ch")]
