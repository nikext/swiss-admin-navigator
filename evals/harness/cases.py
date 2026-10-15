"""End-to-end eval cases (docs/EVALS.md §1, golden case schema).

Golden cases are verified by Nikola (`verified_by`); drafts in
`evals/datasets/drafts/` have the same schema with `verified_by` null and
never back a headline number.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal[
    "answerable", "needs_clarification", "cantonal_pointer", "out_of_scope", "adversarial"
]

GOLDEN = Path("evals/datasets/golden.jsonl")
DRAFTS = Path("evals/datasets/drafts/golden.jsonl")


class ExpectedCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sr: str
    eid: str
    required: bool = True


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    lang: Literal["de", "fr", "it", "en"]
    question: str
    category: Category
    domain: str
    expected_citations: list[ExpectedCitation] = Field(default_factory=list)
    key_facts: list[str] = Field(default_factory=list)
    must_not: list[str] = Field(default_factory=list)
    clarification_expected: bool = False
    smoke: bool = False  # part of the 20-case smoke set (EVALS.md §3)
    verified_by: str | None = None
    verified_on: str | None = None
    as_of: str | None = None
    notes: str | None = None


def default_dataset() -> Path:
    """Golden once it exists; until then the drafts (reports say which)."""
    return GOLDEN if GOLDEN.is_file() and GOLDEN.stat().st_size else DRAFTS


def load_cases(path: Path) -> list[Case]:
    cases = []
    with path.open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    cases.append(Case.model_validate(json.loads(line)))
                except ValueError as exc:
                    raise ValueError(f"{path}:{n}: {exc}") from exc
    ids = [c.id for c in cases]
    if dupes := sorted({i for i in ids if ids.count(i) > 1}):
        raise ValueError(f"{path}: duplicate ids {dupes}")
    return cases
