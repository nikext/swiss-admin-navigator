from pathlib import Path

import numpy as np
import pytest

from ingest.embed import (
    EmbedCache,
    EmbedInput,
    cache_key,
    normalize,
    to_request,
    truncate,
)
from ingest.index import SpaceSpec, abbreviation_rows, toc_rows


def rec(eid: str, path: list[tuple[str, str]], **kw: str) -> dict:
    return {
        "sr": "210", "lang": "de", "eid": eid, "label": kw.get("label", eid),
        "heading": kw.get("heading"), "heading_eids": [e for e, _ in path],
        "heading_path": [t for _, t in path],
    }  # fmt: skip


def test_toc_rows_build_a_tree_in_document_order() -> None:
    a = ("part_1", "Erster Teil")
    b = ("part_1/tit_1", "Erster Titel")
    rows = toc_rows([rec("art_1", [a, b]), rec("art_2", [a, b]), rec("art_3", [a])])
    by_node = {r[2]: r for r in rows}
    assert by_node["part_1"][3:6] == ("", 0, "level")
    assert by_node["part_1/tit_1"][3] == "part_1"
    assert [r[2] for r in rows if r[3] == "part_1/tit_1"] == ["art_1", "art_2"]
    assert by_node["art_3"][3:5] == ("part_1", 1)  # after the title, in order


def test_toc_rows_disambiguate_reused_container_eids() -> None:
    # ZGB Schlusstitel reuses `lvl_I_ter` for two different sections.
    s = ("disp_u1", "Schlusstitel")
    rows = toc_rows([
        rec("disp_u1/art_7", [s, ("disp_u1/lvl_I_ter", "Iter. Scheidung")]),
        rec("disp_u1/art_8", [s, ("disp_u1/lvl_I_ter", "Iter. Wirkungen der Ehe")]),
    ])  # fmt: skip
    levels = {r[2]: r[6] for r in rows if r[5] == "level"}
    assert levels["disp_u1/lvl_I_ter"] == "Iter. Scheidung"
    assert levels["disp_u1/lvl_I_ter~2"] == "Iter. Wirkungen der Ehe"


def test_abbreviation_rows_skip_romansh_add_aliases_and_reject_clashes() -> None:
    acts = [
        {"sr": "220", "abbrs": {"de": "OR", "fr": "CO", "it": "CO", "rm": "DO"}},
        {"sr": "142.20", "abbrs": {"de": "AIG", "fr": "LEI"}},
    ]
    rows = abbreviation_rows(acts, {"142.20": ["AuG"]})
    assert ("do", "DO", "220", "rm", "official") not in rows
    assert ("aug", "AuG", "142.20", None, "alias") in rows
    with pytest.raises(ValueError, match="shared by several acts"):
        abbreviation_rows([*acts, {"sr": "210", "abbrs": {"fr": "CO"}}], {})


def test_space_spec_parse() -> None:
    assert SpaceSpec.parse("emb2-h=default:header") == SpaceSpec("emb2-h", "default", True)
    assert SpaceSpec.parse("dense=x:noheader:768") == SpaceSpec("dense", "x", False, 768)
    with pytest.raises(ValueError, match="bad space spec"):
        SpaceSpec.parse("dense=x:sometimes")


def test_instruction_format_puts_the_task_in_the_text() -> None:
    doc = to_request(EmbedInput("document", "1 Text.", "OR Art. 1"), "instruction")
    assert (doc.content, doc.task_type, doc.title) == (
        "title: OR Art. 1 | text: 1 Text.",
        None,
        None,
    )
    bare = to_request(EmbedInput("document", "1 Text."), "instruction")
    assert bare.content == "title: none | text: 1 Text."
    q = to_request(EmbedInput("query", "Mietkaution?"), "instruction")
    assert q.content == "task: search result | query: Mietkaution?"


def test_task_type_format_uses_the_api_fields() -> None:
    doc = to_request(EmbedInput("document", "1 Text.", "OR Art. 1"), "task_type")
    assert (doc.content, doc.task_type, doc.title) == ("1 Text.", "RETRIEVAL_DOCUMENT", "OR Art. 1")
    q = to_request(EmbedInput("query", "Mietkaution?"), "task_type")
    assert (q.content, q.task_type) == ("Mietkaution?", "RETRIEVAL_QUERY")
    with pytest.raises(ValueError, match="unknown input_format"):
        to_request(EmbedInput("query", "x"), "prefix")


def test_cache_key_covers_model_format_kind_and_title() -> None:
    base = cache_key("m", "instruction", EmbedInput("document", "t", "h"))
    assert base != cache_key("m2", "instruction", EmbedInput("document", "t", "h"))
    assert base != cache_key("m", "task_type", EmbedInput("document", "t", "h"))
    assert base != cache_key("m", "instruction", EmbedInput("query", "t", "h"))
    assert base != cache_key("m", "instruction", EmbedInput("document", "t", None))
    assert base == cache_key("m", "instruction", EmbedInput("document", "t", "h"))


def test_embed_cache_round_trip(tmp_path: Path) -> None:
    cache = EmbedCache(tmp_path / "c.sqlite")
    v = np.arange(4, dtype=np.float32)
    cache.put_many([("k1", "m", None, v)])
    got = cache.get_many(["k1", "missing"])
    assert list(got) == ["k1"]
    np.testing.assert_array_equal(got["k1"], v)


def test_truncate_renormalises_matryoshka_prefix() -> None:
    m = normalize(np.array([[3.0, 4.0, 12.0], [1.0, 0.0, 0.0]]))
    t = truncate(m, 2)
    np.testing.assert_allclose(np.linalg.norm(t, axis=1), [1.0, 1.0], rtol=1e-6)
    np.testing.assert_allclose(t[0], [0.6, 0.8], rtol=1e-6)
    np.testing.assert_array_equal(normalize(np.zeros((1, 3))), np.zeros((1, 3)))
