"""Static checks over every end-to-end case file (docs/EVALS.md §1).

    make check-cases            # golden, adversarial, silver and all drafts

- each file validates against the case schema (`cases.py`);
- case ids are unique across all files (a case moves between files, it is
  never copied);
- every expected citation exists in the index and is in force;
- `clarification_expected` is true exactly for `needs_clarification` cases;
- prints the spread by category, language and domain per file, so the M4
  targets (EVALS.md §1 step 4) are easy to follow.

No model calls; needs `data/index.sqlite` for the citation check.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Callable, Iterable
from pathlib import Path

from evals.harness.cases import DRAFTS, Case, load_cases

DATASETS = Path("evals/datasets")
# Article status by (sr, eid): "in_force", "repealed", ... or None when the article is unknown.
Status = Callable[[str, str], str | None]


def case_files(root: Path = DATASETS) -> list[Path]:
    """Every case file: golden/adversarial/silver at the top, plus all drafts."""
    top = [root / n for n in ("golden.jsonl", "adversarial.jsonl", "silver.jsonl")]
    return [p for p in top if p.is_file()] + sorted((root / DRAFTS.parent.name).glob("*.jsonl"))


def duplicate_ids(files: dict[Path, list[Case]]) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for path, cases in files.items():
        for c in cases:
            seen.setdefault(c.id, []).append(path.name)
    return {i: where for i, where in seen.items() if len(where) > 1}


def citation_problems(cases: Iterable[Case], status: Status) -> list[str]:
    out = []
    for c in cases:
        for e in c.expected_citations:
            st = status(e.sr, e.eid)
            if st is None:
                out.append(f"{c.id}: SR {e.sr} {e.eid} does not exist")
            elif st != "in_force":
                out.append(f"{c.id}: SR {e.sr} {e.eid} is {st}")
    return out


def label_problems(cases: Iterable[Case]) -> list[str]:
    return [
        f"{c.id}: clarification_expected is {c.clarification_expected} for category {c.category}"
        for c in cases
        if c.clarification_expected != (c.category == "needs_clarification")
    ]


def spread(cases: list[Case]) -> str:
    def fmt(counter: Counter[str]) -> str:
        return ", ".join(f"{k} {v}" for k, v in sorted(counter.items()))

    return (
        f"  category: {fmt(Counter(c.category for c in cases))}\n"
        f"  lang:     {fmt(Counter(c.lang for c in cases))}\n"
        f"  domain:   {fmt(Counter(c.domain for c in cases))}\n"
        f"  smoke {sum(c.smoke for c in cases)}, verified {sum(bool(c.verified_by) for c in cases)}"
    )


def index_status(index_path: Path) -> Status:
    import sqlite3

    db = sqlite3.connect(f"file:{index_path.resolve()}?mode=ro", uri=True)

    def status(sr: str, eid: str) -> str | None:
        row = db.execute(
            "SELECT status FROM articles WHERE sr = ? AND eid = ? ORDER BY lang LIMIT 1", (sr, eid)
        ).fetchone()
        return row[0] if row else None

    return status


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path, help="default: every case file")
    ap.add_argument("--index", type=Path, default=Path("data/index.sqlite"))
    args = ap.parse_args(argv)

    errors: list[str] = []
    files: dict[Path, list[Case]] = {}
    for path in args.files or case_files():
        try:
            files[path] = load_cases(path)
        except ValueError as exc:
            errors.append(str(exc))
    for cases in files.values():
        errors += label_problems(cases)
    if not args.files:  # ids are unique across the whole dataset tree
        errors += [f"duplicate id {i} in {w}" for i, w in duplicate_ids(files).items()]
    if args.index.is_file():
        status = index_status(args.index)
        for cases in files.values():
            errors += citation_problems(cases, status)
    else:
        print(f"note: {args.index} not found, expected citations not checked")
    for path, cases in files.items():
        print(f"{path} ({len(cases)} cases)\n{spread(cases)}" if cases else f"{path} (empty)")
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
