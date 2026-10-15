import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from ingest.download import PoliteClient
from ingest.manifest import ACTS_PATH, LANGS, Act, FileEntry, LockedAct, Manifest, load_acts
from ingest.resolve import ResolveError, check_resolution, lang_code, render, xml_files

LANG = "http://publications.europa.eu/resource/authority/language/"
FMT = "https://fedlex.data.admin.ch/vocabulary/user-format/"


def test_render_fills_tokens_and_rejects_leftovers() -> None:
    assert render("a {{X}} b {{Y}}", X="1", Y="2") == "a 1 b 2"
    with pytest.raises(ResolveError, match=r"\{\{Y\}\}"):
        render("{{X}} {{Y}}", X="1")


@pytest.mark.parametrize(
    ("value", "code"),
    [(LANG + "DEU", "de"), (LANG + "FRA", "fr"), ("ita", "it"), ("eng", "en"), ("roh", "rm"),
     (LANG + "SPA", None)],
)  # fmt: skip
def test_lang_code(value: str, code: str | None) -> None:
    assert lang_code(value) == code


def test_shipped_queries_have_only_known_tokens() -> None:
    q = Path("corpus/queries")
    render((q / "latest_consolidations.rq").read_text(), AS_OF="2026-10-15", SR_LIST='"220"')
    render((q / "consolidation_files.rq").read_text(), CONSOLIDATION="https://x/1")


def test_acts_yaml_loads_23_unique_acts() -> None:
    acts = load_acts(ACTS_PATH)
    assert len(acts) == 23
    assert all({"de", "fr", "it"} <= a.abbr.keys() for a in acts)
    assert next(a for a in acts if a.sr == "220").domain == ("work", "housing")


def _act(sr: str, eli: str) -> Act:
    return Act(sr=sr, abbr={"de": "X"}, title_de="t", eli=eli, domain=("work",))


def test_check_resolution_flags_missing_and_reused_sr() -> None:
    acts = [_act("1", "eli/a"), _act("2", "eli/b"), _act("3", "eli/c")]
    rows = {"1": {"act": "eli/a"}, "2": {"act": "eli/OLD"}}
    problems = check_resolution(acts, rows)
    assert len(problems) == 2
    assert "SR 2: Fedlex says eli/OLD" in problems[0]
    assert "SR 3" in problems[1]


def test_xml_files_keeps_our_languages_in_order() -> None:
    rows = [
        (LANG + "ROH", "xml", "rm.xml"),
        (LANG + "ITA", "xml", "it.xml"),
        (LANG + "DEU", "html", "de.html"),
        (LANG + "DEU", "xml", "de-xml-3.xml"),
        (LANG + "ENG", "xml", "en.xml"),
    ]
    bindings = [
        {"lang": {"value": lang}, "fmt": {"value": FMT + fmt}, "file": {"value": f}}
        for lang, fmt, f in rows
    ]

    def handler(req: httpx.Request) -> httpx.Response:
        assert "CONSOLIDATION" not in parse_qs(req.content.decode())["query"][0]
        return httpx.Response(200, json={"results": {"bindings": bindings}})

    with PoliteClient(transport=httpx.MockTransport(handler), min_interval=0) as c:
        files = xml_files(c, "https://fedlex.data.admin.ch/eli/cc/x/20261001")
    assert list(files) == ["de", "it", "en"]
    assert files["de"] == "de-xml-3.xml"


def test_manifest_round_trip(tmp_path: Path) -> None:
    m = Manifest(
        as_of="2026-10-15",
        acts=[
            LockedAct(
                sr="220",
                abbr={"de": "OR"},
                eli="https://fedlex.data.admin.ch/eli/cc/27/317_321_377",
                consolidation="https://fedlex.data.admin.ch/eli/cc/27/317_321_377/20261001",
                date="2026-10-01",
                domain=["work"],
                files={"de": FileEntry(url="https://x/de.xml", sha256="ab" * 32, bytes=3)},
            )
        ],
    )
    path = tmp_path / "lock.json"
    m.save(path)
    assert Manifest.load(path) == m
    assert m.acts[0].eli_path == "cc/27/317_321_377"
    assert json.loads(path.read_text())["acts"][0]["files"]["de"]["bytes"] == 3


def test_committed_lock_is_consistent() -> None:
    m = Manifest.load()
    assert len(m.acts) == 23
    for act in m.acts:
        assert "de" in act.files
        assert set(act.files) <= set(LANGS)
        assert act.consolidation.startswith(act.eli + "/")
        assert act.date <= m.as_of
        assert all(len(f.sha256) == 64 and f.url.endswith(".xml") for f in act.files.values())
