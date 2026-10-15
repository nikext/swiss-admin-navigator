"""Human review of drafted golden cases (docs/EVALS.md §1; CLAUDE.md: only Nikola verifies).

    make review-golden                      # every draft in drafts/*.jsonl, oldest file first
    make review-golden ARGS="--ids work-01,housing-02"

Shows each draft with the full text of its expected citations from the local
index (`data/index.sqlite`, no server needed), then waits for a key:

    a  accept: stamp verified_by/verified_on, move the case to golden.jsonl
    e  edit the case as JSON in $VISUAL/$EDITOR (validated; stays a draft)
    r  reject: move it to drafts/rejected.jsonl with a reason
    s  skip for now        t  show the article text in the next language
    q  quit (everything so far is saved; run again to continue)

Every decision is written immediately, so a review can stop and resume at any
point. The tool only moves a case on the reviewer's key press; drafting stays
with Claude, verification with the reviewer.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from evals.harness.cases import DRAFTS, GOLDEN, Case, load_cases

REJECTED = DRAFTS.parent / "rejected.jsonl"
LANGS = ("de", "fr", "it", "en")

GetArticle = Callable[[str, str, str], dict[str, Any]]


# --- files -------------------------------------------------------------------------


def dump(case: Case) -> str:
    return json.dumps(case.model_dump(), ensure_ascii=False)


def write_cases(path: Path, cases: list[Case]) -> None:
    """Atomic rewrite, so an interrupted review never truncates a dataset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(dump(c) + "\n" for c in cases), encoding="utf-8")
    tmp.replace(path)


def read_cases(path: Path) -> list[Case]:
    return load_cases(path) if path.is_file() else []


class Store:
    """The drafts file plus the two files a decision moves a case into."""

    def __init__(self, drafts: Path, golden: Path, rejected: Path) -> None:
        self.drafts, self.golden, self.rejected = drafts, golden, rejected

    def pending(self) -> list[Case]:
        return read_cases(self.drafts)

    def _move(self, case: Case, target: Path) -> None:
        done = read_cases(target)
        if any(c.id == case.id for c in done):
            raise ValueError(f"{case.id} is already in {target}")
        write_cases(target, [*done, case])
        write_cases(self.drafts, [c for c in self.pending() if c.id != case.id])

    def accept(self, case: Case, reviewer: str, on: date) -> Case:
        verified = case.model_copy(update={"verified_by": reviewer, "verified_on": on.isoformat()})
        self._move(verified, self.golden)
        return verified

    def reject(self, case: Case, reason: str) -> Case:
        note = f"Rejected in review: {reason.strip() or 'no reason given'}"
        rejected = case.model_copy(update={"notes": f"{case.notes} {note}" if case.notes else note})
        self._move(rejected, self.rejected)
        return rejected

    def replace(self, old_id: str, case: Case) -> None:
        cases = self.pending()
        if not any(c.id == old_id for c in cases):
            raise ValueError(f"{old_id} is not a pending draft")
        write_cases(self.drafts, [case if c.id == old_id else c for c in cases])


def parse_edit(text: str, original_id: str, taken: set[str]) -> Case:
    """The edited JSON as a Case; renaming onto an id that exists elsewhere is an error."""
    case = Case.model_validate(json.loads(text))
    if case.id != original_id and case.id in taken:
        raise ValueError(f"id {case.id!r} is already taken")
    return case


# --- rendering -----------------------------------------------------------------------


class Style:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def _wrap(self, code: str, s: str) -> str:
        return f"\033[{code}m{s}\033[0m" if self.enabled else s

    def bold(self, s: str) -> str:
        return self._wrap("1", s)

    def dim(self, s: str) -> str:
        return self._wrap("2", s)

    def warn(self, s: str) -> str:
        return self._wrap("1;31", s)


def _block(text: str, indent: str, width: int) -> list[str]:
    out = []
    for line in text.splitlines() or [""]:
        out += textwrap.wrap(
            line, width=width, initial_indent=indent, subsequent_indent=indent + "  "
        ) or [indent]
    return out


def article_lines(
    get_article: GetArticle, sr: str, eid: str, lang: str, style: Style, width: int
) -> list[str]:
    try:
        art = get_article(sr, eid, lang)
    except Exception as exc:  # the reviewer has to see a missing article, not a traceback
        return [style.warn(f"    NOT FOUND in the index: {exc}")]
    lines = [
        f"    {style.bold(art['abbr'] + ' ' + art['label'])} (SR {sr}, {art['lang'].upper()}) "
        f"— {art.get('heading') or ''}",
        style.dim("    " + " › ".join(art.get("heading_path") or [])),
    ]
    if art.get("fallback"):
        lines.append(style.warn(f"    {art['fallback']}"))
    if art.get("status") != "in_force":
        lines.append(style.warn(f"    status: {art.get('status')}"))
    lines += _block(art.get("text") or "", "    │ ", width)
    lines.append(style.dim(f"    {art.get('url')}  (as of {art.get('as_of')})"))
    return lines


def render(
    case: Case,
    position: str,
    get_article: GetArticle,
    text_lang: str,
    style: Style,
    width: int = 100,
) -> str:
    tags = [case.lang, case.category, case.domain] + (["smoke"] if case.smoke else [])
    lines = [
        "",
        "═" * width,
        f"{position}  {style.bold(case.id)}  ·  " + " · ".join(tags),
        "",
        style.bold("Question"),
        *_block(case.question, "  ", width),
        "",
        style.bold(f"Expected citations (article text in {text_lang.upper()}; t = next language)"),
    ]
    if not case.expected_citations:
        lines.append("  (none)")
    for n, exp in enumerate(case.expected_citations, 1):
        lines.append(f"  [{n}] {'required' if exp.required else 'optional'}")
        lines += article_lines(get_article, exp.sr, exp.eid, text_lang, style, width)
    lines += ["", style.bold("Key facts (a complete answer states these)")]
    lines += [f"  {n}. {f}" for n, f in enumerate(case.key_facts, 1)] or ["  (none)"]
    lines += ["", style.bold("Must not")]
    lines += [f"  - {m}" for m in case.must_not] or ["  (none)"]
    clarify = "yes" if case.clarification_expected else "no"
    lines += ["", f"{style.bold('Clarification expected:')} {clarify}"]
    if case.notes:
        lines += ["", style.bold("Notes")]
        if "DISPUTED" in case.notes:
            lines.append(style.warn("  DISPUTED: an eval run disagreed with this label; see below"))
        lines += _block(case.notes, "  ", width)
    return "\n".join(lines)


# --- the loop ------------------------------------------------------------------------


def edit_in_editor(case: Case) -> str:
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nano"
    with tempfile.NamedTemporaryFile(
        "w", suffix=f"-{case.id}.json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(case.model_dump(), f, ensure_ascii=False, indent=2)
        path = f.name
    try:
        subprocess.run([*shlex.split(editor), path], check=False)  # noqa: S603 (the user's editor)
        return Path(path).read_text(encoding="utf-8")
    finally:
        Path(path).unlink()


def draft_files(drafts_dir: Path, rejected: Path) -> list[Path]:
    """Every drafts file: the M3 drafts (golden.jsonl), then batch-NN.jsonl in order.
    New batches are new files, so drafting never rewrites a file under review."""
    files = [p for p in drafts_dir.glob("*.jsonl") if p != rejected]
    return sorted(files, key=lambda p: (p.name != "golden.jsonl", p.name))


def review(
    items: list[tuple[Store, Case]], get_article: GetArticle, reviewer: str
) -> tuple[int, int]:
    style = Style(sys.stdout.isatty())
    width = min(shutil.get_terminal_size((100, 40)).columns, 110) - 2
    accepted = rejected = 0
    key = ""
    for i, (store, case) in enumerate(items, 1):
        text_lang = case.lang
        while True:
            where = f"[{i}/{len(items)}] {store.drafts.name}"
            print(render(case, where, get_article, text_lang, style, width))
            key = (
                input("\n[a]ccept  [e]dit  [r]eject  [s]kip  [t]ext language  [q]uit > ")
                .strip()
                .lower()
            )
            if key == "a":
                store.accept(case, reviewer, date.today())
                accepted += 1
                print(f"accepted {case.id} → {store.golden}")
                break
            if key == "e":
                text = edit_in_editor(case)
                taken = {c.id for c in read_cases(store.golden)}
                taken |= {c.id for s, _ in items for c in s.pending()}
                try:
                    edited = parse_edit(text, case.id, taken)
                except ValueError as exc:
                    print(style.warn(f"not saved: {exc}"))
                    input("enter to continue > ")
                    continue
                store.replace(case.id, edited)
                case = edited
                print("saved to drafts (review it again, then accept)")
                continue
            if key == "r":
                store.reject(case, input("reason > "))
                rejected += 1
                print(f"rejected {case.id} → {store.rejected}")
                break
            if key == "t":
                text_lang = LANGS[(LANGS.index(text_lang) + 1) % len(LANGS)]
                continue
            if key in ("s", "q"):
                break
        if key == "q":
            break
    return accepted, rejected


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument(
        "--drafts", type=Path, action="append", help="drafts file(s); default: all in drafts/"
    )
    ap.add_argument("--golden", type=Path, default=GOLDEN)
    ap.add_argument("--rejected", type=Path, default=REJECTED)
    ap.add_argument("--ids", default=None, help="comma-separated case ids")
    ap.add_argument("--reviewer", default="nikola")
    ap.add_argument("--index", type=Path, default=Path("data/index.sqlite"))
    args = ap.parse_args(argv)

    from mcp_server.search import Index  # the index loads only for a real review
    from mcp_server.tools import LawTools

    files = args.drafts or draft_files(DRAFTS.parent, args.rejected)
    stores = [Store(f, args.golden, args.rejected) for f in files]
    wanted = set(args.ids.split(",")) if args.ids else None
    items = [(s, c) for s in stores for c in s.pending() if wanted is None or c.id in wanted]
    if not items:
        print("no drafts to review")
        return 0
    law = LawTools(Index(args.index))
    try:
        accepted, rejected = review(items, law.get_article, args.reviewer)
    except (KeyboardInterrupt, EOFError):
        accepted = rejected = None
        print("\nstopped (decisions so far are saved)")
    left = sum(len(s.pending()) for s in stores)
    if accepted is not None:
        print(f"\n{accepted} accepted, {rejected} rejected this session; {left} drafts left")
    else:
        print(f"{left} drafts left")
    return 0


if __name__ == "__main__":
    sys.exit(main())
