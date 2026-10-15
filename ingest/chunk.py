"""Article records -> retrieval chunks with contextual headers (docs/DATA.md §4).

In law the article is the natural unit, and 99% of in-force articles are short
(p99 2,894 chars). An article becomes one chunk unless it is longer than
`MAX_CHARS`; then it is split at paragraph boundaries, and a single paragraph
that is still too long (BV Art. 197 is one 11k-char "paragraph" of numbered
transitional provisions) is split at line boundaries. Each piece keeps the eId
of the paragraph it starts in, so a hit points at the right paragraph.

Every chunk carries a contextual header: act abbreviation, article label and
heading, then the act title and the heading path. Whether the header helps is
measured in E4 (BM25 and dense, with and without it).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any

# ~1,200 tokens. Gemini tokenizers average ~4.5-5 chars per token on DE/FR/IT
# legal text (measured with gemini-embedding-001 statistics); 4 is conservative.
CHARS_PER_TOKEN = 4
MAX_TOKENS = 1200
MAX_CHARS = MAX_TOKENS * CHARS_PER_TOKEN


@dataclass(frozen=True)
class Chunk:
    id: str  # "<record id>#<part>", e.g. "220:art_271_a:de#0"
    article_id: str  # record id, "220:art_271_a:de"
    sr: str
    lang: str
    eid: str  # article eId (what citations and metrics use)
    anchor: str  # eId of the paragraph the chunk starts in (== eid when unsplit)
    part: int
    parts: int
    header: str
    text: str


def header_for(record: Mapping[str, Any], act_title: str | None) -> str:
    """`OR Art. 271a: Kündigung durch den Vermieter — <act title> › <path> › …`.

    One line, no "|": the embedding input format uses "|" as its separator.
    """
    head = f"{record['abbr']} {record['label']}"
    if record.get("heading"):
        head += f": {record['heading']}"
    trail = [t for t in (act_title, *record["heading_path"]) if t]
    line = f"{head} — {' › '.join(trail)}" if trail else head
    return line.replace("|", "/")


def _units(record: Mapping[str, Any]) -> list[tuple[str, str]]:
    """(paragraph eId, rendered text) per paragraph, as it appears in `text`."""
    units = []
    for p in record["paragraphs"]:
        text = f"{p['num']} {p['text']}" if p["num"] and p["text"] else (p["text"] or p["num"])
        if text:
            units.append((p["eid"], text))
    return units or [(record["eid"], record["text"])]


def _split_long(anchor: str, text: str, limit: int) -> Iterator[tuple[str, str]]:
    """Split one oversized paragraph at line breaks, then hard at `limit`."""
    buf: list[str] = []
    size = 0
    for line in text.split("\n"):
        while len(line) > limit:  # one giant line (not seen in the corpus; be safe)
            if buf:
                yield anchor, "\n".join(buf)
                buf, size = [], 0
            cut = line.rfind(" ", 0, limit)
            cut = cut if cut > limit // 2 else limit
            yield anchor, line[:cut].rstrip()
            line = line[cut:].lstrip()
        if buf and size + len(line) + 1 > limit:
            yield anchor, "\n".join(buf)
            buf, size = [], 0
        buf.append(line)
        size += len(line) + 1
    if buf:
        yield anchor, "\n".join(buf)


def split_text(record: Mapping[str, Any], limit: int = MAX_CHARS) -> list[tuple[str, str]]:
    """Greedy-pack paragraphs into pieces of at most `limit` chars."""
    if len(record["text"]) <= limit:
        return [(record["eid"], record["text"])]
    pieces: list[tuple[str, str]] = []
    for anchor, text in _units(record):
        pieces += _split_long(anchor, text, limit) if len(text) > limit else [(anchor, text)]
    packed: list[tuple[str, str]] = []
    for anchor, text in pieces:
        if packed and len(packed[-1][1]) + 1 + len(text) <= limit:
            packed[-1] = (packed[-1][0], f"{packed[-1][1]}\n{text}")
        else:
            packed.append((anchor, text))
    return packed


def chunk_record(
    record: Mapping[str, Any], act_title: str | None, limit: int = MAX_CHARS
) -> list[Chunk]:
    header = header_for(record, act_title)
    pieces = split_text(record, limit)
    return [
        Chunk(
            id=f"{record['id']}#{i}",
            article_id=record["id"],
            sr=record["sr"],
            lang=record["lang"],
            eid=record["eid"],
            anchor=anchor,
            part=i,
            parts=len(pieces),
            header=header,
            text=text,
        )
        for i, (anchor, text) in enumerate(pieces)
    ]


def chunk_corpus(
    records: Iterable[Mapping[str, Any]], titles: Mapping[tuple[str, str], str]
) -> list[Chunk]:
    """Chunks for in-force records only; `titles[(sr, lang)]` is the act title."""
    out: list[Chunk] = []
    for r in records:
        if r["status"] == "in_force":
            out += chunk_record(r, titles.get((r["sr"], r["lang"])))
    return out
