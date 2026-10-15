"""End-to-end eval cases (docs/EVALS.md §1, golden case schema).

Golden cases are verified by Nikola (`verified_by`); drafts in
`evals/datasets/drafts/` have the same schema with `verified_by` null and
never back a headline number. While the review is under way, the harness runs
golden plus every draft batch (`load_dataset("all")`), so the 20-case smoke
set stays complete wherever its cases live; reports say how many are verified.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal[
    "answerable", "needs_clarification", "cantonal_pointer", "out_of_scope", "adversarial"
]

DATASETS = Path("evals/datasets")
GOLDEN = DATASETS / "golden.jsonl"
DRAFTS = DATASETS / "drafts" / "golden.jsonl"  # the M3 drafts; later batches: drafts/batch-NN
REJECTED = DATASETS / "drafts" / "rejected.jsonl"
ADVERSARIAL = DATASETS / "adversarial.jsonl"


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


def draft_files(drafts_dir: Path = DRAFTS.parent) -> list[Path]:
    """Every pending drafts file: the M3 drafts first, then batch-NN in order."""
    files = [p for p in drafts_dir.glob("*.jsonl") if p.name != REJECTED.name]
    return sorted(files, key=lambda p: (p.name != DRAFTS.name, p.name))


@dataclass(frozen=True)
class Dataset:
    spec: str
    files: list[Path]
    cases: list[Case]

    @property
    def sha(self) -> str:
        h = hashlib.sha256()
        for f in self.files:
            h.update(f.read_bytes())
        return h.hexdigest()[:12]

    @property
    def verified(self) -> int:
        return sum(bool(c.verified_by) for c in self.cases)


def resolve_spec(spec: str, root: Path = DATASETS) -> list[Path]:
    """`all` = golden + every draft batch; `golden`; `adversarial`; or a path. `+` joins."""
    files: list[Path] = []
    for part in spec.split("+"):
        if part == "all":
            files += [root / GOLDEN.name, *draft_files(root / DRAFTS.parent.name)]
        elif part in ("golden", "adversarial"):
            files.append(root / f"{part}.jsonl")
        else:
            files.append(Path(part))
    return [f for f in files if f.is_file()]


def load_dataset(spec: str, root: Path = DATASETS) -> Dataset:
    files = resolve_spec(spec, root)
    cases = [c for f in files for c in load_cases(f)]
    ids = [c.id for c in cases]
    if dupes := sorted({i for i in ids if ids.count(i) > 1}):
        raise ValueError(f"{spec}: duplicate ids across files {dupes}")
    return Dataset(spec, files, cases)
