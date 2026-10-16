"""Deterministic citation check (docs/ARCHITECTURE.md §4 rules 1-2, ADR-018).

Pure logic: articles come from an injected `fetch(sr, article, lang)` that
returns the `get_article` result, so the verifier callback (MCP session of the
agent) and the eval harness (its own MCP client) share one definition of
"verbatim".

Verbatim means: the quote occurs in the article text after normalising
whitespace (any run of Unicode whitespace is one space), apostrophes (’ ‘ ʼ
are ') and invisible characters (soft hyphen, zero-width space). An ellipsis
(… or ...) splits a quote into parts that must occur in order. Nothing else
is forgiven: a changed word, letter case or punctuation mark is a mismatch.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from .contact import answer_contact_details
from .contract import Answer, Citation, DraftAnswer, DraftCitation, Problem, Round, Verification

Fetch = Callable[[str, str, str], Awaitable[dict[str, Any]]]

MIN_QUOTE_CHARS = 20  # shorter quotes prove nothing (and would be easy to "fix" by trimming)
MARKER = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
_ELLIPSIS = re.compile(r"\s*(?:…|\.\.\.)\s*")
_EQUIV = {"’": "'", "‘": "'", "ʼ": "'", "­": "", "​": "", "⁠": "", "﻿": ""}
_PREFIX = re.compile(
    r"^(?:abs(?:atz)?|al(?:inéa)?|cpv|capoverso|para(?:graph)?|lit(?:era)?|let(?:tre)?|lett(?:era)?)"
    r"\.?\s*",
    re.IGNORECASE,
)


class ArticleNotFoundError(LookupError):
    """The law server says this SR/article does not exist (the model's error)."""


class FetchError(RuntimeError):
    """The law server could not be asked (infrastructure, not the model's error)."""


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Normalised text plus, per normalised character, its index in `text`."""
    out: list[str] = []
    idx: list[int] = []
    space_at: int | None = None
    for i, ch in enumerate(text):
        ch = _EQUIV.get(ch, ch)
        if not ch:
            continue
        if ch.isspace():
            if out and space_at is None:
                space_at = i
            continue
        if space_at is not None:
            out.append(" ")
            idx.append(space_at)
            space_at = None
        out.append(ch)
        idx.append(i)
    return "".join(out), idx


def normalize(text: str) -> str:
    return normalize_with_map(text)[0]


def quote_parts(quote: str) -> list[str]:
    """The quote's parts between ellipses, normalised, empty parts dropped."""
    return [p for p in (normalize(s) for s in _ELLIPSIS.split(quote)) if p]


def find_quote(quote: str, source: str) -> str | None:
    """The exact source text the quote matches (parts joined by " … "), or None."""
    parts = quote_parts(quote)
    if not parts:
        return None
    norm, idx = normalize_with_map(source)
    pos, spans = 0, []
    for part in parts:
        j = norm.find(part, pos)
        if j < 0:
            return None
        spans.append(source[idx[j] : idx[j + len(part) - 1] + 1])
        pos = j + len(part)
    text = " … ".join(spans)
    stripped = quote.strip()
    if stripped.startswith(("…", "...")):
        text = "… " + text
    if stripped.endswith(("…", "...")):
        text += " …"
    return text


def clean_num(value: str | None) -> str | None:
    """'Abs. 1' / '1 bis' / 'lit. a' / 'a.' -> '1' / '1bis' / 'a' / 'a'."""
    if value is None:
        return None
    v = _PREFIX.sub("", value.strip()).rstrip(".").replace(" ", "")
    return v or None


def markers(markdown: str) -> list[str]:
    """Citation refs used in the answer text, in order of first use."""
    seen: dict[str, None] = {}
    for m in MARKER.finditer(markdown):
        for ref in m.group(1).split(","):
            seen.setdefault(ref.strip(), None)
    return list(seen)


@dataclass
class Checked:
    """One draft citation after the check: the enriched citation and its problems."""

    citation: Citation
    problems: list[Problem]
    article: dict[str, Any] | None = None
    quote_found_in: str | None = None  # paragraph num ("" for an unnumbered one) on pinpoint


def _letter_in(letter: str, text: str) -> bool:
    return re.search(rf"(?m)^{re.escape(letter)}\.\s", text) is not None


def _check_one(draft_citation: DraftCitation, article: dict[str, Any] | Exception) -> Checked:
    c = Citation(**draft_citation.model_dump())
    ref = c.ref
    label = f"SR {c.sr} {c.article}"
    if isinstance(article, ArticleNotFoundError):
        msg = f"{label} does not exist ({article}). Cite only articles you fetched."
        return Checked(c, [Problem(ref=ref, kind="not_found", message=msg)])
    if isinstance(article, Exception):
        msg = f"could not fetch {label}: {type(article).__name__}"
        return Checked(c, [Problem(ref=ref, kind="fetch", message=msg)])

    problems: list[Problem] = []
    c.abbr, c.url, c.as_of = article.get("abbr"), article.get("url"), article.get("as_of")
    c.article = article.get("label") or c.article
    if article.get("status") != "in_force":
        msg = f"{label} is {article.get('status')}; it has no operative text."
        problems.append(Problem(ref=ref, kind="not_in_force", message=msg))
    if article.get("lang") != c.quote_lang:
        msg = (
            f"{label} has no {c.quote_lang.upper()} text (available: "
            f"{article.get('available_langs')}); quote one of those and set quote_lang."
        )
        problems.append(Problem(ref=ref, kind="lang", message=msg))
        return Checked(c, problems, article)

    paragraphs = article.get("paragraphs") or []
    nums = [p.get("num") for p in paragraphs if p.get("num")]
    para = None
    c.paragraph, c.letter = clean_num(c.paragraph), clean_num(c.letter)
    if c.paragraph:
        para = next((p for p in paragraphs if p.get("num") == c.paragraph), None)
        if para is None:
            have = f"paragraphs {nums}" if nums else "no numbered paragraphs (omit paragraph)"
            msg = f"{label} has no paragraph {c.paragraph}; it has {have}."
            problems.append(Problem(ref=ref, kind="paragraph", message=msg))
    if c.letter and not _letter_in(c.letter, para["text"] if para else article.get("text", "")):
        where = f"paragraph {c.paragraph}" if para else "the article"
        msg = f"{label}: {where} has no letter {c.letter}."
        problems.append(Problem(ref=ref, kind="letter", message=msg))

    checked = Checked(c, problems, article)
    quote = draft_citation.quote
    if len("".join(quote_parts(quote))) < MIN_QUOTE_CHARS:
        msg = f"[{ref}] quote is too short to support a claim; quote the sentence that does."
        problems.append(Problem(ref=ref, kind="quote", message=msg))
        return checked
    exact = find_quote(quote, para["text"]) if para else None
    if exact is None:
        exact = find_quote(quote, article.get("text", ""))
        if exact is not None and para is not None:
            home = next(
                (p.get("num") or "" for p in paragraphs if find_quote(quote, p["text"])), None
            )
            checked.quote_found_in = home
            where = f"paragraph {home}" if home else "another part of the article"
            msg = (
                f"[{ref}] the quote is from {where} of {label}, not paragraph {c.paragraph}; "
                "fix the paragraph or the quote."
            )
            problems.append(Problem(ref=ref, kind="pinpoint", message=msg))
    if exact is None:
        msg = (
            f"[{ref}] the quote is not verbatim in the {c.quote_lang.upper()} text of {label}. "
            "Copy it character for character from get_article (mark omissions with …), or drop "
            "the claim."
        )
        problems.append(Problem(ref=ref, kind="quote", message=msg))
    else:
        c.quote = exact
    return checked


async def check_citations(draft: DraftAnswer, fetch: Fetch) -> tuple[list[Checked], list[Problem]]:
    """Check every citation of a draft. Returns per-citation results and answer-level problems."""
    answer_problems: list[Problem] = []
    refs = [c.ref for c in draft.citations]
    for ref in sorted({r for r in refs if refs.count(r) > 1}):
        msg = f"two citations use ref {ref}; give each its own number."
        answer_problems.append(Problem(ref=ref, kind="marker", message=msg))
    for ref in markers(draft.answer_markdown):
        if ref not in refs:
            msg = f"[{ref}] is used in answer_markdown but no citation has ref {ref}."
            answer_problems.append(Problem(ref=ref, kind="marker", message=msg))
    for kind, found in answer_contact_details(draft.model_dump()):
        msg = (
            f"the answer gives a {kind} ({found!r}) that no tool returned. Name the kind of "
            "authority instead (e.g. the cantonal migration office) and leave out addresses, "
            "postcodes, phone numbers and web addresses."
        )
        answer_problems.append(Problem(ref=None, kind="contact", message=msg))

    keys = sorted({(c.sr.strip(), c.article.strip(), c.quote_lang) for c in draft.citations})

    async def get(key: tuple[str, str, str]) -> dict[str, Any] | Exception:
        try:
            return await fetch(*key)
        except (ArticleNotFoundError, FetchError) as exc:
            return exc

    fetched = dict(zip(keys, await asyncio.gather(*(get(k) for k in keys)), strict=True))
    checked = [
        _check_one(c, fetched[(c.sr.strip(), c.article.strip(), c.quote_lang)])
        for c in draft.citations
    ]
    return checked, answer_problems


def strip_markers(markdown: str, refs: set[str]) -> str:
    """Remove the given refs from [n] / [n, m] markers (a marker left empty disappears)."""

    def keep(m: re.Match[str]) -> str:
        left = [r.strip() for r in m.group(2).split(",") if r.strip() not in refs]
        return f"{m.group(1)}[{', '.join(left)}]" if left else ""

    return re.sub(r"(\s?)" + MARKER.pattern, keep, markdown)


# A sentence ends at . ! ? before a capital letter, a quote or the end of the line, so
# "Art. 271a", "Abs. 1" and "lit. a" do not end one.
_SENTENCE_END = re.compile(r"[.!?](?=\s+[A-ZÄÖÜÀ-Ý«\"*(]|\s*$)")
_LIST_ITEM = re.compile(r"[ \t]*(?:[-*+]|\d+[.)])[ \t]+|[ \t]*")
_TRAILING_MARKERS = re.compile(r"(?:\s*" + MARKER.pattern + r")+[.;,]?")


def _locate(claim: str, text: str) -> tuple[int, int] | None:
    """Span of `claim` in `text`, ignoring whitespace and [n] markers in the claim."""
    want = normalize(MARKER.sub("", claim)).strip().rstrip(".;")
    if len(want) < MIN_QUOTE_CHARS:
        return None
    norm, idx = normalize_with_map(text)
    j = norm.find(want)
    if j < 0:
        return None
    return idx[j], idx[j + len(want) - 1] + 1


def _remove_one(text: str, a: int, b: int) -> str:
    """`text` without the sentence around [a, b), its markers, and a list item left empty."""
    ls = text.rfind("\n", 0, a) + 1
    le = text.find("\n", b)
    le = len(text) if le < 0 else le
    line, a, b = text[ls:le], a - ls, b - ls
    prefix = _LIST_ITEM.match(line)
    prefix_end = prefix.end() if prefix else 0
    start = max([prefix_end, *(m.end() for m in _SENTENCE_END.finditer(line, 0, a))])
    end_m = _SENTENCE_END.search(line, b)
    end = end_m.end() if end_m else len(line)
    if m := _TRAILING_MARKERS.match(line, end):
        end = m.end()
    left, right = line[:start], line[end:].lstrip()
    if start > prefix_end:
        left = left.rstrip() + (" " if right else "")
    new_line = left + right
    if not new_line[prefix_end:].strip():  # nothing left on the line: drop the line
        return (text[:ls] + text[le + 1 :]).rstrip("\n") if le < len(text) else text[:ls].rstrip()
    return text[:ls] + new_line + text[le:]


def remove_claims(text: str, claims: list[str]) -> tuple[str, list[str]]:
    """Remove each claim's whole sentence (with its markers) from `text`.

    A claim may be part of a sentence; the sentence goes, since what is left of
    it would no longer say what the user reads it to say. A list item left empty
    goes too. Claims that cannot be located are left alone, and the text is
    never emptied. Returns the new text and the claims removed."""
    removed: list[str] = []
    for claim in claims:
        span = _locate(claim, text)
        if span is None:
            continue
        new = re.sub(r"\n{3,}", "\n\n", _remove_one(text, *span)).strip()
        if not new:
            continue
        text = new
        removed.append(claim)
    return text, removed


def make_round(checked: list[Checked], answer_problems: list[Problem]) -> Round:
    return Round(
        citations=len(checked),
        quotes=sum(1 for ch in checked if ch.citation.quote),
        problems=answer_problems + [p for ch in checked for p in ch.problems],
    )


DROP = {"not_found", "not_in_force"}  # the reference itself is wrong: remove it


def finalize(
    draft: DraftAnswer, checked: list[Checked], answer_problems: list[Problem], rounds: list[Round]
) -> Answer:
    """The final answer. A draft with problems left after the last round is degraded:
    wrong references are dropped, wrong quotes removed, wrong pinpoints repaired or
    removed, and confidence set to low. Every change is recorded."""
    problems = rounds[-1].problems
    fields = draft.model_dump(exclude={"citations"})
    if not problems:
        status = "passed" if len(rounds) == 1 else "passed_after_retry"
        return Answer(
            **fields,
            citations=[ch.citation for ch in checked],
            verification=Verification(status=status, rounds=rounds),
        )

    dropped: list[str] = []
    repairs: list[str] = []
    citations: list[Citation] = []
    for ch in checked:
        c, kinds = ch.citation, {p.kind for p in ch.problems}
        if kinds & DROP:
            dropped.append(c.ref)
            continue
        if kinds & {"quote", "lang"}:
            c.quote = None
            repairs.append(f"[{c.ref}] quote removed (not verbatim)")
        if "pinpoint" in kinds:
            c.paragraph = ch.quote_found_in or None
            repairs.append(f"[{c.ref}] paragraph set to {c.paragraph} (where the quote is)")
        if "paragraph" in kinds:
            c.paragraph, c.letter = None, None
            repairs.append(f"[{c.ref}] non-existent paragraph removed")
        if c.letter and ch.article and ("letter" in kinds or "pinpoint" in kinds):
            paras = {p.get("num"): p["text"] for p in ch.article.get("paragraphs") or []}
            scope = paras.get(c.paragraph) if c.paragraph else ch.article.get("text", "")
            if not scope or not _letter_in(c.letter, scope):
                c.letter = None
                repairs.append(f"[{c.ref}] non-existent letter removed")
        citations.append(c)

    kept = {c.ref for c in citations}
    dangling = {r for r in markers(draft.answer_markdown) if r not in kept}
    if dangling:
        fields["answer_markdown"] = strip_markers(draft.answer_markdown, dangling)
        repairs.append(f"markers {sorted(dangling)} removed from the answer")
    unsupported = [c.claim for c in rounds[-1].claims or [] if c.supported == "no"]
    dropped_claims: list[str] = []
    if unsupported:
        for key in ("answer_markdown", "cantonal_note"):
            if fields.get(key):
                fields[key], gone = remove_claims(fields[key], unsupported)
                dropped_claims += gone
                unsupported = [c for c in unsupported if c not in gone]
        if unsupported:
            repairs.append(f"{len(unsupported)} unsupported claim(s) could not be located")
    contact = [p for p in problems if p.kind == "contact"]
    if contact:  # left as written, but flagged: removing words could change the meaning
        repairs.append(f"{len(contact)} contact detail(s) written from memory left in the answer")
    only_infra = all(p.kind == "fetch" for p in problems)
    fields["confidence"] = "low"
    return Answer(
        **fields,
        citations=citations,
        verification=Verification(
            status="unavailable" if only_infra else "degraded",
            rounds=rounds,
            dropped=dropped,
            repairs=repairs,
            dropped_claims=dropped_claims,
        ),
    )
