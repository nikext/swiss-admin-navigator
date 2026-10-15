"""Akoma Ntoso article eIds <-> display labels (docs/DATA.md §3).

    art_271_a              <-> Art. 271a
    art_329_g_bis          <-> Art. 329g bis
    art_48_bis             <-> Art. 48bis
    art_226_a_226_d        <-> Art. 226a–226d      (range; usually repealed together)
    disp_u2/art_1          ->  Art. 1              (scope prefix kept in the eId only)

Fedlex prints the same numbers as `<b>Art. 329</b><i>g</i><sup>bis</sup>`. The
label puts a space between a letter and a Latin ordinal (329g bis) for
readability; `label_to_eid` also accepts `329gbis`, `329 g bis`, `art. 329g bis`
and hyphen ranges, because citations in the wild are written all of those ways.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

ORDINALS = (
    "bis", "ter", "quater", "quinquies", "sexies", "septies", "octies", "novies",
    "decies", "undecies", "duodecies", "terdecies", "quaterdecies", "quinquiesdecies",
    "sexiesdecies", "septiesdecies",
)  # fmt: skip
_ORD = "|".join(sorted(ORDINALS, key=len, reverse=True))
_NUMBER = re.compile(rf"(\d+)\s*(?:({_ORD})|([a-z])\s*({_ORD})?)?(?![a-z])", re.IGNORECASE)
_LABEL = re.compile(
    rf"^\s*(?:art(?:\.|icle|icolo|ikel)?\s*)?(?P<a>\d+\s*[a-z]*(?:\s*(?:{_ORD}))?)"
    rf"(?:\s*[–-]\s*(?P<b>\d+\s*[a-z]*(?:\s*(?:{_ORD}))?))?\s*$",
    re.IGNORECASE,
)


class EidError(ValueError):
    pass


@dataclass(frozen=True)
class ArticleNumber:
    number: int
    letter: str | None = None
    ordinal: str | None = None

    def label(self) -> str:
        if self.letter:
            return f"{self.number}{self.letter}" + (f" {self.ordinal}" if self.ordinal else "")
        return f"{self.number}{self.ordinal or ''}"

    def eid_tokens(self) -> list[str]:
        return [str(self.number), *(t for t in (self.letter, self.ordinal) if t)]


def split_eid(eid: str) -> tuple[str | None, str]:
    """`disp_u2/art_1` -> (`disp_u2`, `art_1`); `art_1` -> (None, `art_1`)."""
    scope, _, last = eid.rpartition("/")
    return (scope or None), last


def parse_eid(eid: str) -> tuple[str | None, list[ArticleNumber]]:
    """Return (scope, [start] or [start, end]) for an article eId."""
    scope, last = split_eid(eid)
    if not last.startswith("art_"):
        raise EidError(f"not an article eId: {eid!r}")
    tokens = last[4:].split("_")
    numbers: list[ArticleNumber] = []
    i = 0
    while i < len(tokens):
        if not tokens[i].isdigit():
            raise EidError(f"unexpected token {tokens[i]!r} in {eid!r}")
        number, letter, ordinal = int(tokens[i]), None, None
        i += 1
        if i < len(tokens) and re.fullmatch(r"[a-z]", tokens[i]):
            letter, i = tokens[i], i + 1
        if i < len(tokens) and tokens[i] in ORDINALS:
            ordinal, i = tokens[i], i + 1
        numbers.append(ArticleNumber(number, letter, ordinal))
    if not 1 <= len(numbers) <= 2:
        raise EidError(f"expected one number or a range in {eid!r}")
    return scope, numbers


def eid_to_label(eid: str) -> str:
    _, numbers = parse_eid(eid)
    return "Art. " + "–".join(n.label() for n in numbers)


def _parse_number(text: str) -> ArticleNumber:
    m = _NUMBER.fullmatch(text.strip())
    if not m:
        raise EidError(f"cannot parse article number {text!r}")
    number, ord_only, letter, ordinal = m.groups()
    return ArticleNumber(
        int(number),
        letter.lower() if letter else None,
        (ord_only or ordinal or "").lower() or None,
    )


def label_to_eid(label: str, scope: str | None = None) -> str:
    """`Art. 329g bis` -> `art_329_g_bis`. `scope` re-attaches e.g. `disp_u2`."""
    m = _LABEL.match(label)
    if not m:
        raise EidError(f"cannot parse article label {label!r}")
    numbers = [_parse_number(m["a"])] + ([_parse_number(m["b"])] if m["b"] else [])
    eid = "art_" + "_".join(t for n in numbers for t in n.eid_tokens())
    return f"{scope}/{eid}" if scope else eid


_PRINTED_NUMBER = re.compile(rf"(\d+)(?:\s*({_ORD})|([a-z])(?:\s*({_ORD}))?)?", re.IGNORECASE)


def printed_numbers(printed: str) -> list[ArticleNumber]:
    """Article numbers in Fedlex's printed `<num>` text, e.g. "Art. 226a à 226d".

    Letters are attached to the digits in Fedlex's markup (`<b>226</b><i>a</i>`),
    so whatever follows a letter ("a", "à", "und", a dash) is a connector and
    ignored, even without a space ("Art. 92bund 92c", "Art. 80aa 80i").
    """
    out = []
    for m in _PRINTED_NUMBER.finditer(printed):
        number, ord_only, letter, ordinal = m.groups()
        out.append(
            ArticleNumber(
                int(number),
                letter.lower() if letter else None,
                (ord_only or ordinal or "").lower() or None,
            )
        )
    return out


def same_number(printed: str, eid: str) -> bool:
    """Does Fedlex's printed `<num>` text (notes stripped) denote this eId?"""
    return printed_numbers(printed) == parse_eid(eid)[1]
