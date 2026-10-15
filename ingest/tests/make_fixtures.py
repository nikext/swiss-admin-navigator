"""Regenerate the XML fixtures from the cached corpus (run after `make ingest`).

Each fixture is a real Fedlex file pruned to a few articles: the articles keep
their full markup, their ancestors keep only `num`/`heading` (and annex
prefaces), and `meta` keeps FRBRWork for the abbreviations. So the tests run
against real markup, without committing 34 MB of XML.

Usage: uv run python -m ingest.tests.make_fixtures
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

from lxml import etree

from ingest.download import CACHE_DIR, cache_path
from ingest.manifest import LOCK_PATH, Manifest

AKN = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
FIXTURES = Path(__file__).parent / "fixtures"

# (sr, lang) -> eIds to keep. Chosen to cover every parsing rule in ingest/parse.py.
WANTED: dict[tuple[str, str], list[str]] = {
    ("220", "de"): [
        "art_1",  # plain paragraphs
        "art_271_a",  # nested blockList (lit. e, numbers 1-3), marginal levels
        "art_329_g_bis",  # letter + ordinal, footnote inside <num>
        "art_226_a_226_d",  # range, bare <num> + "Aufgehoben" footnote -> repealed
        "art_732_a",  # body text "Aufgehoben" -> repealed
        "disp_u2/art_1",  # transitional provision, "…" -> omitted
    ],
    ("220", "fr"): ["art_271_a", "art_329_g_bis", "art_226_a_226_d"],
    ("142.20", "de"): ["art_30", "art_120_a_120_c"],  # own <heading>, range
    ("142.201", "de"): ["art_1_a"],  # <subheading> reference
    ("210", "de"): ["art_1", "disp_u1/art_6_a"],  # book level, Schlusstitel
    ("210", "en"): ["art_255", "art_256", "art_258"],  # Fedlex eId shift (EN)
    ("0.142.112.681", "de"): ["annex_I/lvl_u1/lvl_II/art_6"],  # annex component
    ("642.11", "de"): ["art_36"],  # table
}


def prune(root: etree._Element, eids: list[str]) -> etree._Element:
    root = copy.deepcopy(root)
    keep: set[etree._Element] = set()
    for eid in eids:
        found = root.xpath("//a:article[@eId=$eid]", namespaces={"a": AKN}, eid=eid)
        hits = (
            [h for h in found if isinstance(h, etree._Element)] if isinstance(found, list) else []
        )
        if not hits:
            raise SystemExit(f"{eid} not found")
        for art in hits:
            keep.add(art)
            keep.update(art.iter())
            for anc in art.iterancestors():
                keep.add(anc)
                for child in anc:
                    if etree.QName(child).localname in ("num", "heading", "preface", "meta"):
                        keep.update(child.iter())
    for el in list(root.iter()):
        parent = el.getparent()
        if parent is not None and el not in keep and parent in keep:
            parent.remove(el)
    return root


def main() -> int:
    manifest = Manifest.load(LOCK_PATH)
    acts = {a.sr: a for a in manifest.acts}
    FIXTURES.mkdir(exist_ok=True)
    for (sr, lang), eids in WANTED.items():
        act = acts[sr]
        root = etree.parse(str(cache_path(sr, act.date, lang, CACHE_DIR))).getroot()
        pruned = prune(root, eids)
        name = f"{act.abbr['de'].lower()}_{lang}.xml"
        etree.ElementTree(pruned).write(
            str(FIXTURES / name), encoding="utf-8", xml_declaration=True
        )
        print(f"{name}: {len(eids)} articles from {act.consolidation}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
