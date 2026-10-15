"""Human labels for the judge-agreement study (docs/EVALS.md §2, judge hygiene).

    make label-answers                       # the 30 answers of the M3 run
    make label-answers ARGS="--ids work-05,social-03"

For each stored answer it shows the question, the expected behaviour, the
answer with its citations, the full text of every cited article (local
index), and the case's key facts and must_not items. You then grade, without
seeing any judge's verdict:

- each legal claim (the reference judge's split, verdicts hidden):
  y = supported by the cited text, p = partly, n = not supported;
- how many unsupported legal claims the list missed (usually 0);
- each key fact: s = stated, m = missing, c = contradicted;
- each must_not item: y = violated, n = not violated;
- whether the behaviour fits the category (y/n), and an optional note.

Each answer is saved to `evals/datasets/judge_labels.jsonl` when finished;
q at any prompt quits without saving the current answer. Re-running skips
answers already labelled. `make judge-study` compares judges with these.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from evals.harness.cases import Case, load_dataset
from evals.harness.judge import EXPECTED_BEHAVIOUR
from evals.harness.judge_study import DEFAULT_REPORT, LABELS, answer_sha
from evals.harness.review import Style, article_lines, wrap_block

Ask = Callable[[str], str]


class QuitError(Exception):
    """q at a prompt: stop without saving the current answer."""


def ask_choice(ask: Ask, prompt: str, choices: dict[str, Any]) -> Any:
    keys = "/".join(choices)
    while True:
        key = ask(f"{prompt} [{keys}, q] > ").strip().lower()
        if key == "q":
            raise QuitError
        if key in choices:
            return choices[key]


def ask_int(ask: Ask, prompt: str) -> int:
    while True:
        raw = ask(f"{prompt} [number, enter = 0, q] > ").strip().lower()
        if raw == "q":
            raise QuitError
        if raw == "":
            return 0
        if raw.isdigit():
            return int(raw)


def collect_label(
    case: Case, row: dict[str, Any], ask: Ask, out: Callable[[str], None]
) -> dict[str, Any]:
    """The prompts for one answer; returns the label record (pure apart from ask/out)."""
    claims = []
    ref_claims = (row.get("judgement") or {}).get("claims", [])
    out(f"\nLegal claims ({len(ref_claims)}): is each supported by the article(s) it cites?")
    for n, c in enumerate(ref_claims, 1):
        cites = ", ".join(c["refs"]) or "nothing"
        out(f"\n  [{n}/{len(ref_claims)}] {c['claim']}  (cites {cites})")
        verdict = ask_choice(ask, "  supported", {"y": "yes", "p": "partly", "n": "no"})
        claims.append({"claim": c["claim"], "refs": c["refs"], "supported": verdict})
    missed = ask_int(ask, "\nUnsupported legal claims the list above missed")
    facts = []
    for n, f in enumerate(case.key_facts, 1):
        out(f"\n  key fact {n}: {f}")
        facts.append(ask_choice(ask, "  ", {"s": "stated", "m": "missing", "c": "contradicted"}))
    must_not = []
    for n, m in enumerate(case.must_not, 1):
        out(f"\n  must_not {n}: {m}")
        must_not.append(ask_choice(ask, "  violated", {"y": True, "n": False}))
    out(f"\nExpected behaviour ({case.category}): {EXPECTED_BEHAVIOUR[case.category]}")
    behaviour = ask_choice(ask, "behaviour ok", {"y": True, "n": False})
    note = ask("note (optional) > ").strip()
    return {
        "case_id": case.id,
        "claims": claims,
        "missed_unsupported": missed,
        "key_facts": facts,
        "key_fact_texts": case.key_facts,
        "must_not": must_not,
        "behaviour_ok": behaviour,
        "note": note or None,
    }


def render_answer(
    case: Case, row: dict[str, Any], get_article: Any, style: Style, width: int
) -> str:
    a = row["answer"]
    lines = [
        "",
        "═" * width,
        f"{style.bold(case.id)} · {case.lang} · {case.category} · verified: "
        f"{case.verified_by or style.warn('NOT YET (labels follow the current draft)')}",
        "",
        style.bold("Question"),
        *wrap_block(case.question, "  ", width),
        "",
        style.bold("Answer"),
        *wrap_block(a.get("answer_markdown") or "", "  ", width),
    ]
    for key in ("clarifying_question", "cantonal_note"):
        if a.get(key):
            lines += ["", style.bold(key), *wrap_block(a[key], "  ", width)]
    if a.get("out_of_scope"):
        lines += ["", style.bold("out_of_scope: true")]
    lines += ["", style.bold("Citations")]
    for c in a.get("citations") or []:
        pin = " ".join(
            x for x in (c.get("article"), c.get("paragraph") and f"para {c['paragraph']}") if x
        )
        lines.append(f"  [{c.get('ref')}] {c.get('abbr') or c.get('sr')} {pin}: «{c.get('quote')}»")
    lines += ["", style.bold("Cited law (full text)")]
    seen = set()
    for c in a.get("citations") or []:
        key = (c.get("sr"), c.get("article"), c.get("quote_lang"))
        if key in seen:
            continue
        seen.add(key)
        sr, article, lang = (str(x) for x in key)
        lines += article_lines(get_article, sr, article, lang, style, width)
    return "\n".join(lines)


def done_ids(path: Path, report: str) -> set[str]:
    if not path.is_file():
        return set()
    recs = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return {r["case_id"] for r in recs if r["report"] == report}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--out", type=Path, default=LABELS)
    ap.add_argument("--ids", default=None)
    ap.add_argument("--labeler", default="nikola")
    args = ap.parse_args(argv)

    from mcp_server.search import Index
    from mcp_server.tools import LawTools

    report = json.loads(args.report.read_text(encoding="utf-8"))
    cases = {c.id: c for c in load_dataset("all").cases}
    skip = done_ids(args.out, args.report.name)
    rows = [
        r
        for r in report["cases"]
        if r.get("answer")
        and r["id"] in cases
        and r["id"] not in skip
        and (not args.ids or r["id"] in args.ids.split(","))
    ]
    print(f"{len(rows)} answers to label ({len(skip)} already done)")
    law = LawTools(Index("data/index.sqlite"))
    style = Style(sys.stdout.isatty())
    width = min(shutil.get_terminal_size((100, 40)).columns, 110) - 2
    labelled = 0
    try:
        for row in rows:
            case = cases[row["id"]]
            print(render_answer(case, row, law.get_article, style, width))
            rec = collect_label(case, row, input, print)
            rec |= {
                "report": args.report.name,
                "answer_sha": answer_sha(row["answer"]),
                "labeled_by": args.labeler,
                "labeled_on": date.today().isoformat(),
            }
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            labelled += 1
    except (QuitError, KeyboardInterrupt, EOFError):
        print("\nstopped; the current answer was not saved")
    print(f"{labelled} labelled this session → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
