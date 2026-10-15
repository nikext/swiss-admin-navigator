import pytest

from ingest.eid import (
    ArticleNumber,
    EidError,
    eid_to_label,
    label_to_eid,
    parse_eid,
    printed_numbers,
    same_number,
)

ROUND_TRIP = [
    ("art_1", "Art. 1"),
    ("art_271_a", "Art. 271a"),
    ("art_329_g_bis", "Art. 329g bis"),
    ("art_48_bis", "Art. 48bis"),
    ("art_12_ter", "Art. 12ter"),
    ("art_64_c_bis", "Art. 64c bis"),
    ("art_72_z_bis", "Art. 72z bis"),
    ("art_226_a_226_d", "Art. 226a–226d"),
    ("art_274_274_g", "Art. 274–274g"),
    ("art_627_628", "Art. 627–628"),
    ("art_48_bis_48_sexies", "Art. 48bis–48sexies"),
]


@pytest.mark.parametrize(("eid", "label"), ROUND_TRIP)
def test_round_trip(eid: str, label: str) -> None:
    assert eid_to_label(eid) == label
    assert label_to_eid(label) == eid


@pytest.mark.parametrize(
    ("eid", "scope", "label"),
    [
        ("disp_u2/art_1", "disp_u2", "Art. 1"),
        ("disp_u1/art_6_a", "disp_u1", "Art. 6a"),
        ("annex_I/lvl_u1/lvl_II/art_6", "annex_I/lvl_u1/lvl_II", "Art. 6"),
    ],
)
def test_scoped_eids_keep_scope(eid: str, scope: str, label: str) -> None:
    assert eid_to_label(eid) == label
    assert parse_eid(eid)[0] == scope
    assert label_to_eid(label, scope) == eid


@pytest.mark.parametrize(
    ("written", "eid"),
    [
        ("Art. 329gbis", "art_329_g_bis"),
        ("art. 329 g bis", "art_329_g_bis"),
        ("329g bis", "art_329_g_bis"),
        ("Art. 48 bis", "art_48_bis"),
        ("Artikel 271a", "art_271_a"),
        ("article 5", "art_5"),
        ("articolo 30", "art_30"),
        ("Art. 226a-226d", "art_226_a_226_d"),
        ("ART. 271A", "art_271_a"),
    ],
)
def test_label_variants(written: str, eid: str) -> None:
    assert label_to_eid(written) == eid


@pytest.mark.parametrize("bad", ["Abs. 1", "Art.", "Art. a1", "§ 5", "Art. 5 Abs. 2"])
def test_unparseable_labels(bad: str) -> None:
    with pytest.raises(EidError):
        label_to_eid(bad)


@pytest.mark.parametrize("bad", ["para_1", "art_x", "art_1_2_3", "art_"])
def test_bad_eids(bad: str) -> None:
    with pytest.raises(EidError):
        parse_eid(bad)


def test_printed_numbers_ignore_connectors() -> None:
    assert printed_numbers("Art. 226a à 226d") == [ArticleNumber(226, "a"), ArticleNumber(226, "d")]


@pytest.mark.parametrize(
    ("printed", "eid"),
    [
        ("Art. 329gbis", "art_329_g_bis"),  # <b>329</b><i>g</i><sup>bis</sup>
        ("Art. 226a–226d", "art_226_a_226_d"),
        ("Art. 226a à 226d", "art_226_a_226_d"),  # FR
        ("Art. 226a a 226d", "art_226_a_226_d"),  # IT: connector "a" vs letter "a"
        ("Art. 663dà663h", "art_663_d_663_h"),
        ("Art. 92bund 92c", "art_92_b_92_c"),
        ("Art. 80aa 80i", "art_80_a_80_i"),
        ("Art. 38 und39", "art_38_39"),
        ("Art. 48bis–48sexies", "art_48_bis_48_sexies"),
    ],
)
def test_same_number_accepts_fedlex_formatting(printed: str, eid: str) -> None:
    assert same_number(printed, eid)


@pytest.mark.parametrize(
    ("printed", "eid"),
    [
        ("Art. 255a", "art_256"),  # EN ZGB eId shift
        ("Art. 697l", "art_697_l_697_m"),  # IT OR truncated range
        ("Art. 329g", "art_329_g_bis"),
        ("", "art_1"),
    ],
)
def test_same_number_rejects_disagreement(printed: str, eid: str) -> None:
    assert not same_number(printed, eid)
