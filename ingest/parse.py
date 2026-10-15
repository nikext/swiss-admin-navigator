"""Akoma Ntoso (Fedlex) -> one record per article per language (docs/DATA.md §3-4).

Usage: uv run python -m ingest.parse   (reads the lock + cache, writes
data/articles.jsonl, data/acts.json and corpus/stats.md)

Rules, all verified against the 2026-10-15 corpus:
- Footnotes (`authorialNote`) appear in article bodies *and* inside `<num>` and
  `<heading>` of articles and containers. They are removed from every text
  field and collected in `notes`.
- Articles live in `<body>` and, for treaties, in annex `<component>`s (FZA
  Annex I/II). eIds of transitional provisions and annexes are scoped
  (`disp_u2/art_1`, `annex_I/lvl_u1/lvl_II/art_6`).
- `status`: `repealed` (no operative text, or only "Aufgehoben"/"Abrogé"/...),
  `omitted` (text replaced by "…", e.g. spent amendment provisions), else
  `in_force`.
- The eId must agree with the printed number, or the record is dropped and
  reported. A citation system must never serve text under the wrong number.
  Fedlex's EN ZGB has a run of shifted eIds (`art_256` prints "Art. 255a"),
  and IT OR prints the range `art_697_l_697_m` as "Art. 697l".
"""

from __future__ import annotations

import json
import logging
import re
import sys
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

from lxml import etree

from ingest.download import CACHE_DIR, cache_path
from ingest.eid import EidError, eid_to_label, same_number
from ingest.manifest import LOCK_PATH, LockedAct, Manifest

log = logging.getLogger(__name__)

AKN = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
FEDLEX = "http://fedlex.admin.ch/"
OUT_PATH = Path("data/articles.jsonl")
ACTS_OUT_PATH = Path("data/acts.json")
STATS_PATH = Path("corpus/stats.md")

_REPEAL_WORD = r"(?:aufgehoben|abrog[ée]e?s?|abrogat[aoie]|repealed)"
_REPEALED = re.compile(rf"^{_REPEAL_WORD}\.?$", re.IGNORECASE)
_REPEALED_NOTE = re.compile(rf"\b{_REPEAL_WORD}\b", re.IGNORECASE)
_OMITTED = {"…", "...", "…."}
_WS = re.compile(r"\s+")


def q(tag: str) -> str:
    return f"{{{AKN}}}{tag}"


NOTE = q("authorialNote")
ARTICLE = q("article")
# Container elements whose num/heading form the heading path.
_SKIP_IN_PATH = {q("content"), q("mainBody"), q("doc"), q("components"), q("act"), q("body")}


@dataclass
class Paragraph:
    eid: str
    num: str | None
    text: str


@dataclass
class Article:
    id: str
    sr: str
    abbr: str
    lang: str
    eid: str
    label: str
    heading: str | None
    heading_path: list[str]
    heading_eids: list[str]  # container eIds parallel to heading_path (for get_toc)
    text: str
    paragraphs: list[Paragraph]
    notes: list[str]
    refs: list[str]
    status: str
    consolidation_date: str
    url: str
    domain: list[str]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


@dataclass
class FileStats:
    articles: int = 0
    by_status: Counter[str] = field(default_factory=Counter)
    dropped: list[str] = field(default_factory=list)
    unknown_blocks: Counter[str] = field(default_factory=Counter)


# --- text rendering -----------------------------------------------------------


def norm(text: str) -> str:
    return _WS.sub(" ", text).strip()


def _inline_parts(el: etree._Element) -> Iterator[str]:
    """Text of `el` in document order, skipping footnotes; `<br/>` becomes a space."""
    if el.tag == NOTE:
        return
    if el.tag == q("br"):
        yield " "
    elif el.text:
        yield el.text
    for child in el:
        if isinstance(child.tag, str):
            yield from _inline_parts(child)
        if child.tail:
            yield child.tail


def inline(el: etree._Element | None) -> str:
    return norm("".join(_inline_parts(el))) if el is not None else ""


def notes_in(el: etree._Element) -> list[str]:
    return [norm("".join(map(str, n.itertext()))) for n in el.iter(NOTE)]


def refs_in(el: etree._Element) -> list[str]:
    """Every href in the article. In practice these are the AS/BBl amendment
    publications cited in footnotes: the operative text references other
    articles in plain words ("Art. 18–29"), with only 2 hyperlinks corpus-wide."""
    return [href for ref in el.iter(q("ref")) if (href := ref.get("href"))]


def block_lines(el: etree._Element, stats: FileStats) -> list[str]:
    """Render a block-level element as lines: one per sentence block or list item."""
    tag = etree.QName(el).localname
    if tag in ("p", "listIntroduction", "listWrapUp", "subheading", "heading"):
        return [inline(el)]
    if tag in ("content", "blockContainer", "intro", "wrapUp", "subdivision"):
        lines = []
        for child in el:
            if isinstance(child.tag, str) and child.tag != NOTE:
                lines += block_lines(child, stats)
        return lines
    if tag == "blockList":
        lines = []
        for child in el:
            if child.tag == q("item"):
                lines += item_lines(child, stats)
            elif isinstance(child.tag, str) and child.tag != NOTE:
                lines += block_lines(child, stats)
        return lines
    if tag == "item":
        return item_lines(el, stats)
    if tag == "paragraph":
        num, lines = paragraph_lines(el, stats)
        return _prefix(num, lines)
    if tag == "table":
        rows = []
        for tr in el.iter(q("tr")):
            cells = [
                norm(" ".join(block_lines(td, stats))) for td in tr if td.tag in (q("td"), q("th"))
            ]
            rows.append(" | ".join(c for c in cells if c))  # empty cells carry no meaning in text
        return rows
    if tag in ("td", "th"):
        return [
            line for child in el if isinstance(child.tag, str) for line in block_lines(child, stats)
        ] or [inline(el)]
    stats.unknown_blocks[tag] += 1
    return [inline(el)]


def item_lines(item: etree._Element, stats: FileStats) -> list[str]:
    num = inline(item.find(q("num"))) or None
    lines: list[str] = []
    for child in item:
        if isinstance(child.tag, str) and child.tag not in (NOTE, q("num")):
            lines += block_lines(child, stats)
    return _prefix(num, lines)


def paragraph_lines(par: etree._Element, stats: FileStats) -> tuple[str | None, list[str]]:
    num = inline(par.find(q("num"))) or None
    lines: list[str] = []
    for child in par:
        if isinstance(child.tag, str) and child.tag not in (NOTE, q("num")):
            lines += block_lines(child, stats)
    return num, lines


def _prefix(num: str | None, lines: list[str]) -> list[str]:
    lines = [line for line in (norm(x) for x in lines) if line]
    if num and lines:
        return [f"{num} {lines[0]}", *lines[1:]]
    return [num] if num and not lines else lines


# --- structure ----------------------------------------------------------------


def heading_path(article: etree._Element) -> list[tuple[str, str]]:
    """(container eId, "num heading") for every labelled ancestor, outermost first.

    An annex `doc` has no eId of its own in Fedlex's XML; it gets the scope its
    articles carry (`annex_I` for `annex_I/lvl_u1/lvl_II/art_6`).
    """
    path = []
    for anc in reversed(list(article.iterancestors())):
        if anc.tag in _SKIP_IN_PATH:
            if anc.tag == q("doc"):  # annex component: "Anhang I"
                preface = anc.find(q("preface"))
                if preface is not None:
                    scope = (article.get("eId") or "").partition("/")[0]
                    path.append((anc.get("eId") or scope, preface_label(preface)))
            continue
        label = norm(f"{inline(anc.find(q('num')))} {inline(anc.find(q('heading')))}")
        if label:
            path.append((anc.get("eId") or "", label))
    return path


def preface_label(preface: etree._Element) -> str:
    """ "Anhang I" from `<preface><container><block name="num">Anhang I<note/>`."""
    for block in preface.iter(q("block"), q("p")):
        if not any(a.tag == NOTE for a in block.iterancestors()) and (text := inline(block)):
            return text
    return inline(preface)


def article_heading(article: etree._Element) -> str | None:
    own = inline(article.find(q("heading")))
    sub = inline(article.find(q("subheading")))
    if own:
        return norm(f"{own} {sub}")
    for anc in article.iterancestors():
        if anc.get(f"{{{FEDLEX}}}role") == "marginal":
            return inline(anc.find(q("heading"))) or None
    return None


def article_status(text: str, notes: Iterable[str]) -> str:
    if text in _OMITTED:
        return "repealed" if any(_REPEALED_NOTE.search(n) for n in notes) else "omitted"
    if not text:
        return "repealed" if any(_REPEALED_NOTE.search(n) for n in notes) else "omitted"
    if _REPEALED.match(text):
        return "repealed"
    return "in_force"


def frbr_names(root: etree._Element, attr: str) -> dict[str, str]:
    """Per-language FRBRWork/FRBRname attribute: `shortForm` (abbreviation,
    authoritative) or `value` (full title). Every file lists all languages,
    including EN abbreviations of acts that have no EN text (AIG: "FNA")."""
    out = {}
    for name in root.iter(q("FRBRname")):
        lang = name.get("{http://www.w3.org/XML/1998/namespace}lang")
        if lang and name.get(attr):
            out[lang] = norm(name.get(attr, ""))
    return out


def short_forms(root: etree._Element) -> dict[str, str]:
    return frbr_names(root, "shortForm")


@dataclass
class ActInfo:
    """Per-act summary for the index (`list_acts`, chunk headers, abbreviations)."""

    sr: str
    eli: str
    consolidation_date: str
    domain: list[str]
    langs: list[str]  # languages with article text
    titles: dict[str, str]  # FRBRname/@value per language (de, fr, it, en, rm)
    abbrs: dict[str, str]  # FRBRname/@shortForm per language


def act_info(act: LockedAct, roots: dict[str, etree._Element]) -> ActInfo:
    titles: dict[str, str] = {}
    abbrs: dict[str, str] = {}
    # A language's own file wins for that language; the other files fill gaps.
    for lang, root in sorted(roots.items(), key=lambda kv: kv[0] != "de"):
        for target, attr in ((titles, "value"), (abbrs, "shortForm")):
            names = frbr_names(root, attr)
            target.update({k: v for k, v in names.items() if k not in target or k == lang})
    return ActInfo(
        sr=act.sr,
        eli=act.eli,
        consolidation_date=act.date,
        domain=act.domain,
        langs=list(roots),
        titles=titles,
        abbrs=abbrs,
    )


def keep_article(art: etree._Element, seen: set[str], stats: FileStats) -> bool:
    """Keep an article only if its eId is new and agrees with its printed number."""
    eid = art.get("eId") or ""
    printed = inline(art.find(q("num")))
    try:
        agrees = same_number(printed, eid)
    except EidError:
        agrees = False
    if not agrees:
        stats.dropped.append(f"{eid!r} printed {printed!r}: number disagrees with eId")
        return False
    if eid in seen:
        stats.dropped.append(f"{eid!r} printed {printed!r}: duplicate eId")
        return False
    seen.add(eid)
    return True


def parse_xml(data: bytes) -> etree._Element:
    return etree.fromstring(data, parser=etree.XMLParser(resolve_entities=False, no_network=True))


def parse_file(
    data: bytes | etree._Element, act: LockedAct, lang: str, stats: FileStats | None = None
) -> list[Article]:
    stats = stats if stats is not None else FileStats()
    root = parse_xml(data) if isinstance(data, bytes) else data
    abbr = short_forms(root).get(lang) or act.abbr.get(lang) or act.abbr["de"]
    seen: set[str] = set()
    out = []
    for art in root.iter(ARTICLE):
        if not keep_article(art, seen, stats):
            continue
        eid = art.get("eId", "")
        paragraphs: list[Paragraph] = []
        loose: list[str] = []
        for child in art:
            if not isinstance(child.tag, str) or child.tag in (
                NOTE, q("num"), q("heading"), q("subheading"),
            ):  # fmt: skip
                continue
            if child.tag == q("paragraph"):
                num, lines = paragraph_lines(child, stats)
                paragraphs.append(Paragraph(child.get("eId") or eid, num, "\n".join(lines)))
            else:
                loose += block_lines(child, stats)
        if loose:
            paragraphs.insert(0, Paragraph(eid, None, "\n".join(_prefix(None, loose))))
        text = "\n".join(
            f"{p.num} {p.text}" if p.num and p.text else (p.text or p.num or "") for p in paragraphs
        ).strip()
        notes = notes_in(art)
        path = heading_path(art)
        status = article_status(norm(text), notes)
        stats.articles += 1
        stats.by_status[status] += 1
        out.append(
            Article(
                id=f"{act.sr}:{eid}:{lang}",
                sr=act.sr,
                abbr=abbr,
                lang=lang,
                eid=eid,
                label=eid_to_label(eid),
                heading=article_heading(art),
                heading_path=[label for _, label in path],
                heading_eids=[container for container, _ in path],
                text=text,
                paragraphs=paragraphs,
                notes=list(dict.fromkeys(notes)),
                refs=list(dict.fromkeys(refs_in(art))),
                status=status,
                consolidation_date=act.date,
                url=f"https://www.fedlex.admin.ch/eli/{act.eli_path}/{lang}#{eid}",
                domain=act.domain,
            )
        )
    return out


# --- corpus run ---------------------------------------------------------------


def parse_corpus(
    manifest: Manifest, cache_dir: Path = CACHE_DIR
) -> tuple[list[Article], list[ActInfo], dict[tuple[str, str], FileStats]]:
    articles: list[Article] = []
    acts: list[ActInfo] = []
    stats: dict[tuple[str, str], FileStats] = {}
    for act in manifest.acts:
        roots = {
            lang: parse_xml(cache_path(act.sr, act.date, lang, cache_dir).read_bytes())
            for lang in act.files
        }
        for lang, root in roots.items():
            fs = stats[(act.sr, lang)] = FileStats()
            articles += parse_file(root, act, lang, fs)
        acts.append(act_info(act, roots))
    return articles, acts, stats


def render_stats(manifest: Manifest, stats: dict[tuple[str, str], FileStats]) -> str:
    langs = ["de", "fr", "it", "en"]
    lines = [
        "# Corpus stats",
        "",
        f"Generated by `make ingest` from `manifest.lock.json` (as_of {manifest.as_of}). "
        "Counts are article records per language; in-force / repealed / omitted in brackets.",
        "",
        "| SR | Act | Consolidation | " + " | ".join(langs) + " |",
        "|---|---|---|" + "---|" * len(langs),
    ]
    totals: Counter[str] = Counter()
    for act in manifest.acts:
        cells = []
        for lang in langs:
            fs = stats.get((act.sr, lang))
            if fs is None:
                cells.append("–")
                continue
            s = fs.by_status
            totals[lang] += fs.articles
            cells.append(f"{fs.articles} ({s['in_force']}/{s['repealed']}/{s['omitted']})")
        lines.append(f"| {act.sr} | {act.abbr['de']} | {act.date} | " + " | ".join(cells) + " |")
    lines.append("| | **Total** | | " + " | ".join(str(totals[x]) for x in langs) + " |")
    issues = []
    for (sr, lang), fs in stats.items():
        issues += [f"- {sr} {lang}: dropped {x}" for x in fs.dropped]
        issues += [f"- {sr} {lang}: unknown block <{t}> ×{n}" for t, n in fs.unknown_blocks.items()]
    lines += ["", "## Data issues", "", *(issues or ["None."]), ""]
    return "\n".join(lines)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    manifest = Manifest.load(LOCK_PATH)
    articles, acts, stats = parse_corpus(manifest)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for a in articles:
            f.write(a.to_json() + "\n")
    ACTS_OUT_PATH.write_text(
        json.dumps([asdict(a) for a in acts], ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    STATS_PATH.write_text(render_stats(manifest, stats), encoding="utf-8")
    ids = Counter(a.id for a in articles)
    dupes = [i for i, n in ids.items() if n > 1]
    if dupes:
        log.error("duplicate record ids: %s", dupes[:10])
        return 1
    print(f"wrote {len(articles)} records to {OUT_PATH}; stats in {STATS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
