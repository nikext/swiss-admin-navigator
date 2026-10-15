from pathlib import Path

import pytest

from agents.navigator.config import (
    PROFILES_DIR,
    ROLES,
    ModelRef,
    Profile,
    ProfileError,
    load_profile,
)

GOOD = """\
agent:
  model: model-a
  location: eu
judge:
  model: model-j
  location: global
embedding:
  model: model-e
  location: eu
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


def test_profile_location_ignores_infra_region() -> None:
    # GOOGLE_CLOUD_LOCATION is the infra region (europe-west6), where these
    # models are not served (ADR-013). It must not leak into model locations.
    profile = load_profile(env={"GOOGLE_CLOUD_LOCATION": "europe-west6"})
    assert profile.agent.location != "europe-west6"


def test_roles() -> None:
    assert ROLES == ("agent", "judge", "embedding")


def test_name_resolution_order(profiles: Path) -> None:
    (profiles / "cheap.yaml").write_text(GOOD.replace("model-a", "model-cheap"))
    assert load_profile(env={}, profiles_dir=profiles).name == "default"
    env = {"NAV_PROFILE": "cheap"}
    assert load_profile(env=env, profiles_dir=profiles).agent.model == "model-cheap"
    assert load_profile("default", env=env, profiles_dir=profiles).agent.model == "model-a"


def test_env_overrides_single_fields(profiles: Path) -> None:
    env = {"AGENT_MODEL": "model-x", "JUDGE_LOCATION": "eu", "EMBEDDING_MODEL": ""}
    p = load_profile(env=env, profiles_dir=profiles)
    assert p.agent == ModelRef(model="model-x", location="eu")
    assert p.judge == ModelRef(model="model-j", location="eu")
    assert p.embedding.model == "model-e"  # empty env var does not override
    assert p.as_dict() == {
        "name": "default",
        "agent": {"model": "model-x", "location": "eu"},
        "judge": {"model": "model-j", "location": "eu"},
        "embedding": {"model": "model-e", "location": "eu"},
    }


def test_unknown_profile_lists_available(profiles: Path) -> None:
    with pytest.raises(ProfileError, match=r"unknown profile 'nope'.*\['default'\]"):
        load_profile("nope", env={}, profiles_dir=profiles)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (GOOD + "temperature: 0.2\n", r"unknown keys \['temperature'\]"),
        (GOOD.split("embedding:")[0], r"missing \['embedding'\]"),
        (
            GOOD.replace("  location: global\n", ""),
            r"judge: unknown keys \[\], missing \['location'\]",
        ),
        (GOOD.replace("model: model-e", "model: model-e\n  tier: x"), r"embedding: unknown keys"),
        (GOOD.replace("model-e", "''"), r"embedding.model must be a non-empty string"),
        (GOOD.replace("model-e", "3"), r"embedding.model must be a non-empty string"),
        (GOOD.replace("judge:\n  model: model-j\n  location: global", "judge: x"), "judge must be"),
        ("- a\n- b\n", "expected a mapping"),
    ],
)
def test_malformed_profiles_are_rejected(profiles: Path, content: str, message: str) -> None:
    (profiles / "default.yaml").write_text(content)
    with pytest.raises(ProfileError, match=message):
        load_profile(env={}, profiles_dir=profiles)
