from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from evals.harness.silver import Generated, eligible, names_the_article, or_in_scope, plan, to_case


def test_or_scope_is_lease_and_employment() -> None:
    assert or_in_scope("art_271_a")
    assert or_in_scope("art_329_g_bis")
    assert or_in_scope("art_362")
    assert not or_in_scope("art_252")
    assert not or_in_scope("art_999")
    assert not or_in_scope("disp_u10/art_1")


@pytest.mark.parametrize(
    ("question", "named"),
    [
        ("Peut-on contester l'art. 271a du CO ?", True),
        ("Darf mein Vermieter laut OR kündigen?", True),
        ("Can my landlord end my lease because I complained?", False),
        ("Mein Artikel 27 Vertrag?", False),  # a different number
    ],
)
def test_names_the_article(question: str, named: bool) -> None:
    assert names_the_article(question, "OR", "Art. 271a") is named


def db(tmp_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(tmp_path / "i.sqlite")
    con.execute(
        "CREATE TABLE articles (sr TEXT, eid TEXT, lang TEXT, status TEXT, heading TEXT, text TEXT)"
    )
    long = "x" * 300
    rows = [
        ("220", "art_271_a", "de", "in_force", "Kündigung durch den Vermieter", long),
        ("220", "art_1", "de", "in_force", "Abschluss", long),  # outside the OR scope
        ("220", "art_272", "de", "in_force", "Anspruch", "short"),  # too short
        ("220", "art_270", "de", "repealed", "Anfangsmietzins", long),
        ("831.10", "art_1", "de", "in_force", "Zweck", long),  # purpose article
        ("831.10", "art_3", "de", "in_force", "Beitragspflicht", long),
        ("831.10", "disp_u1/art_1", "de", "in_force", "Übergang", long),
    ]
    con.executemany("INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?)", rows)
    return con


def test_eligible_filters(tmp_path: Path) -> None:
    con = db(tmp_path)
    assert [e for e, _ in eligible(con, "220")] == ["art_271_a"]
    assert [e for e, _ in eligible(con, "831.10")] == ["art_3"]


def test_plan_is_deterministic_and_rotates_languages(tmp_path: Path) -> None:
    con = db(tmp_path)
    p1, p2 = plan(con, seed=1), plan(con, seed=1)
    assert p1 == p2
    assert {p["eid"] for p in p1 if p["sr"] == "220"} == {"art_271_a"}
    assert [p["lang"] for p in p1][:2] == ["de", "fr"]


def test_to_case_shape() -> None:
    facts, wrong = ["a", "b", "c", "d"], ["x", "y"]
    g = Generated(skip=False, question=" Can I? ", key_facts=facts, must_not=wrong)
    art = {"abbr": "OR", "label": "Art. 271a"}
    case = to_case(7, {"sr": "220", "eid": "art_271_a", "lang": "en"}, art, g, "m, seed 0")
    assert case["id"] == "silver-0007"
    assert case["question"] == "Can I?"
    assert case["key_facts"] == ["a", "b", "c"]
    assert case["must_not"] == ["x"]
    assert case["expected_citations"] == [{"sr": "220", "eid": "art_271_a", "required": True}]
    assert "not verified" in case["notes"]
