"""Find and resolve Swiss-style legal citations in free text (`resolve_citation`).

Swiss citations name the article first and the act last, with paragraph and
letter in between, in any of the official languages:

    Art. 271a Abs. 1 lit. a OR        art. 271a al. 1 let. a CO
    art. 30 cpv. 1 lett. a LStrI      Art. 329g bis OR     Art. 48bis BV
    Art. 335b f. OR    Art. 253–273c OR    Art. 1 SchlT ZGB    Art. 6 Anhang I FZA
    art. 30, al. 1, let. k, LEI   (Fedlex's own reference subheadings)
    Art. 271 und 271a OR          artt. 335b e 335c CO       OR Art. 336c

`parse_citations` is pure (text + abbreviation table -> citations) and is what
the unit tests pin down. `resolve` checks each one against the index: does the
article exist, is it in force, which paragraph eId, and the Fedlex deep link.
Nothing is guessed: an article that does not exist comes back `exists: false`.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from ingest.eid import ORDINALS, ArticleNumber, EidError, label_to_eid, parse_eid

_ORD = "|".join(sorted(ORDINALS, key=len, reverse=True))
# An ordinal ("bis") is not one when a number follows: "Art. 48 bis 50" is a range.
_ORD_SUFFIX = rf"(?:\s?(?:{_ORD})(?![a-z])(?!\s*\d))"
NUMBER = (
    rf"\d+(?:[a-z](?![a-z]){_ORD_SUFFIX}?"  # 271a, 329g bis
    rf"|\s[a-z]\s(?:{_ORD})(?![a-z])(?!\s*\d)"  # 329 g bis (a lone letter needs the ordinal)
    rf"|[a-z]?(?:{_ORD})(?![a-z])(?!\s*\d)"  # 48bis, 329gbis
    rf"|{_ORD_SUFFIX})?"  # 48 bis
)
_FLAGS = re.IGNORECASE | re.UNICODE

ARTICLE_KW = re.compile(
    r"(?<![\w.])(?P<kw>artikels?|articles?|articoli|articolo|artt?\.|art(?=\s*\d))\s*", _FLAGS
)
NUM_AT = re.compile(rf"(?P<n>{NUMBER})", _FLAGS)
# "Art. 12ff." needs its own rule: "12f" would otherwise read as a letter.
NUM_FF_AT = re.compile(r"(?P<n>\d+)(?=\s?ff\.)", _FLAGS)
RANGE_AT = re.compile(rf"\s*(?P<to>[–—-]|\bbis\b|\bà\b)\s*(?:art\.\s*)?(?P<n>{NUMBER})", _FLAGS)
RANGE_LANG = {"bis": "de", "à": "fr"}
# "Art. 271 und 271a": another article. After a component ("Abs. 2 und 3") a bare
# number continues the component, unless "Art." is repeated.
LIST_AT = re.compile(
    r"\s*(?:,|;|\bund\b|\bsowie\b|\bet\b|\be\b|\bed\b|\band\b)\s*"
    rf"(?P<kw>art(?:ikel|icle|icolo)?s?\.?\s*)?(?P<n>{NUMBER})(?!\s*[,.]?\s*\d)",
    _FLAGS,
)
FOLLOWING_AT = re.compile(r"\s?(?:ff\.?|f\.|(?:et\s+)?ss\.?|segg\.?|seg\.|et seq\.?)", _FLAGS)

# Component keyword -> (component, language hint)
_COMPONENTS: dict[str, tuple[str, str | None]] = {
    "abs.": ("paragraph", "de"), "absatz": ("paragraph", "de"), "al.": ("paragraph", "fr"),
    "alinéa": ("paragraph", "fr"), "cpv.": ("paragraph", "it"), "capoverso": ("paragraph", "it"),
    "para.": ("paragraph", "en"), "paragraph": ("paragraph", "en"), "para": ("paragraph", "en"),
    "abs": ("paragraph", "de"), "§": ("paragraph", None),
    "lit.": ("letter", "de"), "lit": ("letter", "de"), "litera": ("letter", "de"),
    "bst.": ("letter", "de"),
    "buchstabe": ("letter", "de"), "let.": ("letter", "fr"), "lettre": ("letter", "fr"),
    "lett.": ("letter", "it"), "lettera": ("letter", "it"), "letter": ("letter", "en"),
    "ziff.": ("number", "de"), "ziffer": ("number", "de"), "ch.": ("number", "fr"),
    "chiffre": ("number", "fr"), "n.": ("number", "it"), "numero": ("number", "it"),
    "no.": ("number", "en"), "number": ("number", "en"),
    "satz": ("sentence", "de"), "phrase": ("sentence", "fr"), "periodo": ("sentence", "it"),
    "sentence": ("sentence", "en"),
}  # fmt: skip
_COMPONENT_KW = "|".join(
    re.escape(k) + ("" if k.endswith((".", "§")) else r"\b")
    for k in sorted(_COMPONENTS, key=len, reverse=True)
)
COMPONENT_AT = re.compile(
    rf"\s*,?\s*(?P<kw>{_COMPONENT_KW})\s*(?P<v>\d+{_ORD_SUFFIX}?|[a-z](?:{_ORD})?(?![a-z]))",
    _FLAGS,
)
KW_LANG = {"artikel": "de", "artikels": "de", "articolo": "it", "articoli": "it", "artt.": "it"}

# Between the article and the act: "des", "du", "of the", commas, SR numbers, scopes.
FILLER_AT = re.compile(
    r"\s*,?\s*(?:(?:des|der|dem|du|de\s+la|de\s+l'|de|della|dello|dell'|del|of\s+the|of|the)\s+)?",
    _FLAGS,
)
SCOPE_AT = re.compile(
    r"(?:(?P<schlt>SchlT|Tit\.\s*fin\.|Schlusstitel)|"
    r"(?P<annex>Anhang|Anh\.|annexe|allegato|annex)\s+(?P<roman>[IVX]+)\b)\s*,?\s*"
    r"(?:(?:des|der|du|de\s+l'|de|del|dell'|to\s+the|of\s+the|of)\s+)?",
    _FLAGS,
)
SR_AT = re.compile(r"(?:SR|RS)\s*(?P<sr>\d+(?:\.\d+)*)\b")
ABBR_AT = re.compile(r"(?P<a>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ]*\.?)")
ABBR_BEFORE = re.compile(r"(?P<a>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ]*\.?)\s*,?\s*$")


def norm_abbr(abbr: str) -> str:
    """Case-, accent- and dot-insensitive key: `Cst.` -> `cst`, `BüG` -> `bug`.

    The index builder uses this too (abbreviation clash check), so the server
    and the index agree on keys.
    """
    s = unicodedata.normalize("NFKD", abbr)
    return "".join(c for c in s if c.isalnum()).lower()


@dataclass(frozen=True)
class Abbr:
    sr: str
    abbr: str
    langs: frozenset[str]


AbbrTable = Mapping[str, Abbr]


def abbreviation_table(rows: Iterable[tuple[str, str, str | None]]) -> dict[str, Abbr]:
    """(abbr, sr, lang) rows -> norm -> Abbr. One SR per abbreviation (checked at build)."""
    acc: dict[str, tuple[str, str, set[str]]] = {}
    for abbr, sr, lang in rows:
        _, _, langs = acc.setdefault(norm_abbr(abbr), (sr, abbr, set()))
        if lang:
            langs.add(lang)
    return {n: Abbr(sr, a, frozenset(langs)) for n, (sr, a, langs) in acc.items()}


@dataclass
class Citation:
    text: str
    start: int
    end: int
    sr: str | None
    abbr: str | None
    article: str  # label, "Art. 271a"
    eid: str | None  # computed eId (with scope), before checking the index
    range_end: str | None = None
    paragraph: str | None = None
    letter: str | None = None
    number: str | None = None
    following: bool = False  # "ff." / "et ss." / "segg."
    scope: str | None = None  # "disp_u1" (SchlT ZGB) or "annex_I"
    lang_hint: str | None = None
    resolution: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Parsed fields that are set, plus every resolution field (False included)."""
        parsed = {
            k: v for k, v in asdict(self).items() if k != "resolution" and v not in (None, False)
        }
        return parsed | {"exists": False} | self.resolution


def _clean_number(n: str) -> str:
    """'329gbis' / '329 g bis' / '48 bis' -> '329g bis' / '48bis' (eid.py label style)."""
    try:
        return parse_eid(label_to_eid(n))[1][0].label()
    except EidError:
        return n.strip()


def _find_abbr(text: str, pos: int, table: AbbrTable) -> tuple[Abbr | None, str | None, int]:
    """An act abbreviation (or SR number) starting at `pos`, after optional filler words."""
    m = FILLER_AT.match(text, pos)
    p = m.end() if m else pos
    if m_sr := SR_AT.match(text, p):
        sr = m_sr["sr"]
        for a in table.values():
            if a.sr == sr:
                return a, None, m_sr.end()
        return None, None, pos
    if m_ab := ABBR_AT.match(text, p):
        for cand in (m_ab["a"], m_ab["a"].split()[0]):
            a = table.get(norm_abbr(cand))
            if a and any(c.isupper() for c in cand):  # "or"/"co" in prose are not acts
                end = p + len(cand)
                return a, cand.strip(), end
    return None, None, pos


def _scope(m: re.Match[str] | None) -> str | None:
    if not m:
        return None
    return "disp_u1" if m["schlt"] else f"annex_{m['roman'].upper()}"


def parse_citations(text: str, table: AbbrTable) -> list[Citation]:
    """All article citations in `text`, in order. Pure function (no index access)."""
    out: list[Citation] = []
    pos = 0
    while m_kw := ARTICLE_KW.search(text, pos):
        start, p = m_kw.start(), m_kw.end()
        kw_lang = KW_LANG.get(m_kw["kw"].lower())
        m_n = NUM_FF_AT.match(text, p) or NUM_AT.match(text, p)
        if not m_n:
            pos = m_kw.end()
            continue
        groups: list[dict[str, Any]] = []
        hints: list[str] = [kw_lang] if kw_lang else []
        while True:  # one article number (+ range, components, ff.) per loop
            item: dict[str, Any] = {"n": m_n["n"]}
            p = m_n.end()
            if m_r := RANGE_AT.match(text, p):
                item["range_end"], p = m_r["n"], m_r.end()
                hints += [RANGE_LANG[m_r["to"].lower()]] if m_r["to"].lower() in RANGE_LANG else []
            while True:
                if m_c := COMPONENT_AT.match(text, p):
                    comp, hint = _COMPONENTS[m_c["kw"].lower()]
                    item.setdefault(comp, m_c["v"].replace(" ", ""))
                    hints += [hint] if hint else []
                    p = m_c.end()
                elif (
                    len(item) > 1
                    and (m_more := LIST_AT.match(text, p))
                    and not m_more["kw"]
                    and m_more["n"].isdigit()
                ):
                    p = m_more.end()  # "Abs. 2 und 3": more of the same component
                else:
                    break
            if m_f := FOLLOWING_AT.match(text, p):
                item["following"], p = True, m_f.end()
            groups.append(item)
            if (m_n := LIST_AT.match(text, p)) is None:
                break
        m_scope = SCOPE_AT.match(text, FILLER_AT.match(text, p).end())  # type: ignore[union-attr]
        scope = _scope(m_scope)
        abbr, written, end = _find_abbr(text, m_scope.end() if m_scope else p, table)
        if abbr is None and (m_b := ABBR_BEFORE.search(text, 0, start)):
            cand = m_b["a"]
            a = table.get(norm_abbr(cand))
            if a and any(c.isupper() for c in cand):
                abbr, written, start = a, cand.rstrip(","), m_b.start()
        if abbr is None:
            end = p
        lang = _lang(hints, abbr)
        for g in groups:
            number = _clean_number(g["n"])
            try:
                eid = label_to_eid(number)
                eid = f"{scope}/{eid}" if scope == "disp_u1" else eid
            except EidError:
                eid = None
            out.append(
                Citation(
                    text=text[start:end].strip(),
                    start=start,
                    end=end,
                    sr=abbr.sr if abbr else None,
                    abbr=written,
                    article="Art. " + number,
                    eid=eid,
                    range_end="Art. " + _clean_number(g["range_end"]) if "range_end" in g else None,
                    paragraph=g.get("paragraph"),
                    letter=g.get("letter", "").lower() or None,
                    number=g.get("number"),
                    following=g.get("following", False),
                    scope=scope,
                    lang_hint=lang,
                )
            )
        pos = max(end, m_kw.end())
    return out


def _lang(hints: list[str], abbr: Abbr | None) -> str | None:
    """Language of the citation: from its keywords, else from an unambiguous abbreviation."""
    official = {lang for lang in (abbr.langs if abbr else ()) if lang != "en"}
    for h in hints:
        if not official or h in official or h == "en":
            return h
    if len(official) == 1:
        return next(iter(official))
    return None


# --- resolution against the index -------------------------------------------------


def _number_key(n: ArticleNumber) -> tuple[int, str, int]:
    return (n.number, n.letter or "", ORDINALS.index(n.ordinal) + 1 if n.ordinal else 0)


def _row(db: sqlite3.Connection, sr: str, eid: str, lang: str) -> sqlite3.Row | None:
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    return cur.execute(
        "SELECT eid, label, status, url, paragraphs, lang FROM articles "
        "WHERE sr = ? AND eid = ? AND lang = ?",
        (sr, eid, lang),
    ).fetchone()


def _find_eid(db: sqlite3.Connection, c: Citation) -> tuple[str | None, list[str], str | None]:
    """(eid, other candidates, note) for a parsed citation (sr and eid are set)."""
    if not c.sr or not c.eid:
        return None, [], None
    base = c.eid.rsplit("/", 1)[-1]
    if c.scope and c.scope.startswith("annex_"):
        rows = db.execute(
            "SELECT DISTINCT eid FROM articles WHERE sr = ? AND eid LIKE ? AND eid LIKE ?",
            (c.sr, f"{c.scope}/%", f"%/{base}"),
        ).fetchall()
        eids = [r[0] for r in rows]
        return (eids[0] if len(eids) == 1 else None), eids[1:] if len(eids) == 1 else eids, None
    if db.execute("SELECT 1 FROM articles WHERE sr = ? AND eid = ?", (c.sr, c.eid)).fetchone():
        scoped = db.execute(
            "SELECT DISTINCT eid FROM articles WHERE sr = ? AND eid LIKE ?", (c.sr, f"%/{base}")
        ).fetchall()
        return c.eid, [r[0] for r in scoped if r[0] != c.eid], None
    # Inside a range record ("Art. 226b" within "art_226_a_226_d")?
    target = _number_key(parse_eid(base)[1][0])
    for (eid,) in db.execute(
        "SELECT DISTINCT eid FROM articles WHERE sr = ? AND eid GLOB '*art_[0-9]*_[0-9]*'",
        (c.sr,),
    ):
        try:
            scope, numbers = parse_eid(eid)
        except EidError:
            continue
        if len(numbers) == 2 and (scope or None) == (c.scope if c.scope else None):
            lo, hi = map(_number_key, numbers)
            if lo <= target <= hi:
                return eid, [], f"part of the range {eid}"
    scoped = db.execute(
        "SELECT DISTINCT eid FROM articles WHERE sr = ? AND eid LIKE ?", (c.sr, f"%/{base}")
    ).fetchall()
    return None, [r[0] for r in scoped], None


def resolve(db: sqlite3.Connection, citations: list[Citation], default_lang: str = "de") -> None:
    """Fill `resolution` on each citation (in place)."""
    for c in citations:
        if not c.sr:
            c.resolution = {"exists": False, "error": "no act given or act not in the corpus"}
            continue
        if not c.eid:
            c.resolution = {"exists": False, "error": f"cannot read article number {c.article!r}"}
            continue
        eid, others, note = _find_eid(db, c)
        if eid is None:
            c.resolution = {"exists": False, "error": "no such article in this act"}
            if others:
                c.resolution |= {"candidates": others[:5], "error": "article number is ambiguous"}
            continue
        lang = c.lang_hint if c.lang_hint in ("de", "fr", "it", "en") else default_lang
        row = _row(db, c.sr, eid, lang) or _row(db, c.sr, eid, default_lang)
        if row is None:
            c.resolution = {"exists": False, "error": "no such article in this act"}
            continue
        res: dict[str, Any] = {
            "exists": True,
            "eid": eid,
            "label": row["label"],
            "status": row["status"],
            "url": row["url"],
            "lang": row["lang"],
        }
        if note:
            res["note"] = note
        if others:
            res["other_matches"] = others[:5]
        if c.paragraph:
            para_eid = f"{eid}/para_{label_to_eid(c.paragraph)[4:]}"
            paragraphs = json.loads(row["paragraphs"])
            match = next((p for p in paragraphs if p["eid"] == para_eid), None)
            res["paragraph_exists"] = match is not None
            if match:
                res["paragraph_eid"] = para_eid
                if c.letter:
                    res["letter_exists"] = bool(
                        re.search(rf"(?m)^{re.escape(c.letter)}\.\s", match["text"])
                    )
        c.resolution = res
