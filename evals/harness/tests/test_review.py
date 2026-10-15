from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from evals.harness.cases import Case, load_cases
from evals.harness.review import Store, Style, draft_files, parse_edit, render, write_cases


def case(cid: str, **kw: Any) -> Case:
    base = {
        "id": cid,
        "lang": "fr",
        "question": "Mon bailleur peut-il résilier mon bail ?",
        "category": "answerable",
        "domain": "housing",
        "expected_citations": [{"sr": "220", "eid": "art_271_a", "required": True}],
        "key_facts": ["termination can be challenged"],
        "must_not": ["claims the termination is void"],
        "notes": "draft",
    }
    return Case.model_validate(base | kw)


@pytest.fixture
def store(tmp_path: Path) -> Store:
    drafts = tmp_path / "drafts" / "golden.jsonl"
    write_cases(drafts, [case("housing-01"), case("housing-02"), case("work-01")])
    return Store(drafts, tmp_path / "golden.jsonl", tmp_path / "drafts" / "rejected.jsonl")


def test_accept_moves_case_and_stamps_reviewer(store: Store) -> None:
    accepted = store.accept(case("housing-02"), "nikola", date(2026, 10, 16))
    assert [c.id for c in store.pending()] == ["housing-01", "work-01"]
    golden = load_cases(store.golden)
    assert golden == [accepted]
    assert (accepted.verified_by, accepted.verified_on) == ("nikola", "2026-10-16")


def test_accept_appends_in_order(store: Store) -> None:
    store.accept(case("work-01"), "nikola", date(2026, 10, 16))
    store.accept(case("housing-01"), "nikola", date(2026, 10, 17))
    assert [c.id for c in load_cases(store.golden)] == ["work-01", "housing-01"]


def test_accept_refuses_duplicate_in_golden(store: Store) -> None:
    write_cases(store.golden, [case("housing-01")])
    with pytest.raises(ValueError, match="already in"):
        store.accept(case("housing-01"), "nikola", date(2026, 10, 16))
    assert len(store.pending()) == 3  # nothing moved


def test_reject_keeps_reason_in_notes(store: Store) -> None:
    store.reject(case("work-01"), "  key fact 2 is wrong  ")
    (rejected,) = load_cases(store.rejected)
    assert rejected.notes == "draft Rejected in review: key fact 2 is wrong"
    assert rejected.verified_by is None
    assert "work-01" not in {c.id for c in store.pending()}


def test_replace_edits_in_place_and_allows_rename(store: Store) -> None:
    edited = case("housing-09", question="Changed?")
    store.replace("housing-02", edited)
    assert [c.id for c in store.pending()] == ["housing-01", "housing-09", "work-01"]
    assert store.pending()[1].question == "Changed?"
    with pytest.raises(ValueError, match="not a pending draft"):
        store.replace("nope", edited)


def test_files_are_valid_jsonl_without_temp_leftovers(store: Store) -> None:
    store.accept(case("housing-01"), "nikola", date(2026, 10, 16))
    for path in (store.drafts, store.golden):
        lines = path.read_text(encoding="utf-8").splitlines()
        assert all(json.loads(line)["id"] for line in lines)
    assert not list(store.drafts.parent.glob("*.tmp"))


def test_parse_edit_validates_schema_and_ids() -> None:
    good = json.dumps(case("work-01").model_dump())
    assert parse_edit(good, "work-01", {"work-01", "work-02"}).id == "work-01"
    renamed = json.dumps(case("work-02").model_dump())
    with pytest.raises(ValueError, match="already taken"):
        parse_edit(renamed, "work-01", {"work-01", "work-02"})
    with pytest.raises(ValueError, match="bogus"):
        parse_edit(json.dumps(case("work-01").model_dump() | {"bogus": 1}), "work-01", set())
    with pytest.raises(ValueError, match="Expecting property name"):
        parse_edit("{not json", "work-01", set())


def fake_article(sr: str, eid: str, lang: str) -> dict[str, Any]:
    if eid == "art_999_z":
        raise ValueError(f"no article {eid!r} in SR {sr}")
    return {
        "abbr": "CO",
        "label": "Art. 271a",
        "lang": lang,
        "heading": "Congé donné par le bailleur",
        "heading_path": ["Titre huitième: Du bail à loyer"],
        "status": "in_force",
        "text": "1 Le congé est annulable lorsqu'il est donné par le bailleur, notamment:\n"
        "a. parce que le locataire fait valoir de bonne foi des prétentions découlant du bail;",
        "url": "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr#art_271_a",
        "as_of": "2026-10-01",
    }


def test_render_shows_everything_the_reviewer_checks() -> None:
    c = case("housing-01", smoke=True, notes="DISPUTED (M3): agent disagreed. Drafted by Claude.")
    out = render(c, "[1/3]", fake_article, "fr", Style(False), width=80)
    for expected in (
        "[1/3]",
        "housing-01",
        "smoke",
        "Mon bailleur",
        "CO Art. 271a",
        "required",
        "│ 1 Le congé est annulable",
        "│ a. parce que",
        "fedlex.admin.ch",
        "1. termination can be challenged",
        "- claims the termination is void",
        "Clarification expected: no",
        "DISPUTED: an eval run disagreed",
    ):
        assert expected in out, expected
    assert "\033[" not in out  # no colour codes when not a tty


def test_render_flags_missing_article() -> None:
    c = case("adversarial-09", expected_citations=[{"sr": "220", "eid": "art_999_z"}])
    out = render(c, "[1/1]", fake_article, "de", Style(False))
    assert "NOT FOUND in the index" in out


def test_draft_files_skip_rejected_and_sort(tmp_path: Path) -> None:
    for name in ("batch-02.jsonl", "golden.jsonl", "rejected.jsonl", "batch-01.jsonl"):
        (tmp_path / name).write_text("", encoding="utf-8")
    files = draft_files(tmp_path, tmp_path / "rejected.jsonl")
    assert [f.name for f in files] == ["golden.jsonl", "batch-01.jsonl", "batch-02.jsonl"]
