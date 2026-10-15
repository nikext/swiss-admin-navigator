from pathlib import Path

import pytest

from agents.navigator.config import PROFILES_DIR, Profile, ProfileError, load_profile

GOOD = """\
location: europe-west6
agent_model: model-a
judge_model: model-j
embedding_model: model-e
"""


@pytest.fixture
def profiles(tmp_path: Path) -> Path:
    (tmp_path / "default.yaml").write_text(GOOD)
    return tmp_path


def test_every_shipped_profile_loads() -> None:
    names = [p.stem for p in PROFILES_DIR.glob("*.yaml")]
    assert "default" in names
    for name in names:
        assert isinstance(load_profile(name, env={}), Profile)


def test_default_profile_is_regional() -> None:
    # ARCHITECTURE.md §5: use the regional endpoint, not `global`.
    assert load_profile(env={}).location == "europe-west6"


def test_name_resolution_order(profiles: Path) -> None:
    (profiles / "cheap.yaml").write_text(GOOD.replace("model-a", "model-cheap"))
    assert load_profile(env={}, profiles_dir=profiles).name == "default"
    env = {"NAV_PROFILE": "cheap"}
    assert load_profile(env=env, profiles_dir=profiles).agent_model == "model-cheap"
    assert load_profile("default", env=env, profiles_dir=profiles).agent_model == "model-a"


def test_env_overrides_single_fields(profiles: Path) -> None:
    p = load_profile(env={"AGENT_MODEL": "model-x", "JUDGE_MODEL": ""}, profiles_dir=profiles)
    assert p.agent_model == "model-x"
    assert p.judge_model == "model-j"  # empty env var does not override
    assert p.as_dict() == {
        "name": "default",
        "location": "europe-west6",
        "agent_model": "model-x",
        "judge_model": "model-j",
        "embedding_model": "model-e",
    }


def test_unknown_profile_lists_available(profiles: Path) -> None:
    with pytest.raises(ProfileError, match=r"unknown profile 'nope'.*\['default'\]"):
        load_profile("nope", env={}, profiles_dir=profiles)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (GOOD + "temperature: 0.2\n", "unknown keys \\['temperature'\\]"),
        (GOOD.replace("judge_model: model-j\n", ""), "missing \\['judge_model'\\]"),
        (GOOD.replace("model-e", "''"), "embedding_model must be a non-empty string"),
        (GOOD.replace("model-e", "3"), "embedding_model must be a non-empty string"),
        ("- a\n- b\n", "expected a mapping"),
    ],
)
def test_malformed_profiles_are_rejected(profiles: Path, content: str, message: str) -> None:
    (profiles / "default.yaml").write_text(content)
    with pytest.raises(ProfileError, match=message):
        load_profile(env={}, profiles_dir=profiles)
