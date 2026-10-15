from __future__ import annotations

import sqlite3
from pathlib import Path

from evals.harness.cases import Case
from evals.harness.check_cases import (
    article_hash,
    case_files,
    citation_problems,
    duplicate_ids,
    label_problems,
    spread,
    stale_cases,
    text_hashes,
)


def case(cid: str, cites: tuple[tuple[str, str], ...] = (), **kw: object) -> Case:
    return Case.model_validate(
        {
            "id": cid,
            "lang": "de",
            "question": "?",
            "category": "answerable",
            "domain": "housing",
            "expected_citations": [{"sr": s, "eid": e} for s, e in cites],
        }
        | kw
    )


def test_case_files_order_and_presence(tmp_path: Path) -> None:
    (tmp_path / "drafts").mkdir()
    for name in ("golden.jsonl", "silver.jsonl", "drafts/batch-01.jsonl", "drafts/golden.jsonl"):
        (tmp_path / name).write_text("", encoding="utf-8")
    names = [str(p.relative_to(tmp_path)) for p in case_files(tmp_path)]
    assert names == ["golden.jsonl", "silver.jsonl", "drafts/batch-01.jsonl", "drafts/golden.jsonl"]


def test_duplicate_ids_across_files() -> None:
    files = {
        Path("a.jsonl"): [case("x-1"), case("x-2")],
        Path("b.jsonl"): [case("x-2"), case("x-3")],
    }
    assert duplicate_ids(files) == {"x-2": ["a.jsonl", "b.jsonl"]}


def test_citation_problems() -> None:
    table = {("220", "art_271_a"): "in_force", ("220", "art_255"): "repealed"}
    cases = [case("h-1", (("220", "art_271_a"), ("220", "art_255"), ("220", "art_271_z")))]
    assert citation_problems(cases, lambda sr, eid: table.get((sr, eid))) == [
        "h-1: SR 220 art_255 is repealed",
        "h-1: SR 220 art_271_z does not exist",
    ]


def test_spread_counts() -> None:
    out = spread([case("a", lang="fr"), case("b", category="out_of_scope", smoke=True)])
    assert "answerable 1, out_of_scope 1" in out
    assert "de 1, fr 1" in out
    assert "smoke 1, verified 0" in out


def test_label_problems() -> None:
    ok = [case("a"), case("b", category="needs_clarification", clarification_expected=True)]
    assert label_problems(ok) == []
    bad = [
        case("c", category="needs_clarification"),
        case("d", clarification_expected=True),
    ]
    assert label_problems(bad) == [
        "c: clarification_expected is False for category needs_clarification",
        "d: clarification_expected is True for category answerable",
    ]


def test_text_lock_flags_changed_articles(tmp_path: Path) -> None:
    db = sqlite3.connect(tmp_path / "i.sqlite")
    db.execute("CREATE TABLE articles (sr TEXT, eid TEXT, lang TEXT, status TEXT, text TEXT)")
    db.executemany(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?)",
        [
            ("220", "art_271_a", "de", "in_force", "1 Die Kündigung ist anfechtbar"),
            ("220", "art_271_a", "fr", "in_force", "1 Le congé est annulable"),
            ("220", "art_273", "de", "in_force", "1 innert 30 Tagen"),
        ],
    )
    cases = [case("h-1", (("220", "art_271_a"),)), case("h-2", (("220", "art_273"),))]
    locked = text_hashes(cases, db)
    assert set(locked) == {"220 art_271_a", "220 art_273"}
    assert stale_cases(cases, locked, text_hashes(cases, db)) == []
    db.execute("UPDATE articles SET text = '1 innert 60 Tagen' WHERE eid = 'art_273'")
    assert stale_cases(cases, locked, text_hashes(cases, db)) == [
        "h-2: cited text changed since verification (220 art_273); re-verify"
    ]
    assert stale_cases(cases, {}, locked)[0].startswith("h-1")  # not in the lock yet
    assert article_hash(db, "220", "art_999") is None
