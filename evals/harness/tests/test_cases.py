from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.harness.cases import load_dataset, resolve_spec


def write(path: Path, *ids: str, verified: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "id": i,
            "lang": "de",
            "question": "?",
            "category": "answerable",
            "domain": "housing",
            "verified_by": "nikola" if verified else None,
        }
        for i in ids
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


@pytest.fixture
def root(tmp_path: Path) -> Path:
    write(tmp_path / "golden.jsonl", "a-1", verified=True)
    write(tmp_path / "drafts" / "golden.jsonl", "a-2")
    write(tmp_path / "drafts" / "batch-01.jsonl", "a-3", "a-4")
    write(tmp_path / "drafts" / "rejected.jsonl", "a-9")
    write(tmp_path / "adversarial.jsonl", "x-1")
    return tmp_path


def test_all_is_golden_plus_draft_batches_without_rejected(root: Path) -> None:
    names = [str(p.relative_to(root)) for p in resolve_spec("all", root)]
    assert names == ["golden.jsonl", "drafts/golden.jsonl", "drafts/batch-01.jsonl"]
    ds = load_dataset("all", root)
    assert [c.id for c in ds.cases] == ["a-1", "a-2", "a-3", "a-4"]
    assert ds.verified == 1
    assert len(ds.sha) == 12


def test_specs_join_and_skip_missing(root: Path) -> None:
    assert [c.id for c in load_dataset("golden+adversarial", root).cases] == ["a-1", "x-1"]
    (root / "golden.jsonl").unlink()  # before the first accept there is no golden file
    assert [c.id for c in load_dataset("all", root).cases] == ["a-2", "a-3", "a-4"]


def test_duplicate_ids_across_files_are_an_error(root: Path) -> None:
    write(root / "drafts" / "batch-02.jsonl", "a-1")
    with pytest.raises(ValueError, match=r"duplicate ids across files \['a-1'\]"):
        load_dataset("all", root)
