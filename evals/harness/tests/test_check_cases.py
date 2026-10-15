from __future__ import annotations

from pathlib import Path

from evals.harness.cases import Case
from evals.harness.check_cases import case_files, citation_problems, duplicate_ids, spread


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
