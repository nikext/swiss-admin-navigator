"""Model profiles (ADR-008): model IDs live in `profiles/<name>.yaml`, never in code.

The profile is chosen by `NAV_PROFILE` (default: `default`). Individual fields can
be overridden per run with `AGENT_MODEL`, `JUDGE_MODEL`, `EMBEDDING_MODEL` and
`GOOGLE_CLOUD_LOCATION`, which is how eval experiments swap models. Eval reports
must record `Profile.as_dict()` so results stay reproducible.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import yaml

PROFILES_DIR = Path(__file__).parent / "profiles"

# profile field -> env var that overrides it
_ENV_OVERRIDES = {
    "location": "GOOGLE_CLOUD_LOCATION",
    "agent_model": "AGENT_MODEL",
    "judge_model": "JUDGE_MODEL",
    "embedding_model": "EMBEDDING_MODEL",
}


class ProfileError(ValueError):
    """A profile is missing, malformed, or has unknown or missing keys."""


@dataclass(frozen=True)
class Profile:
    name: str
    location: str
    agent_model: str
    judge_model: str
    embedding_model: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def load_profile(
    name: str | None = None,
    *,
    env: Mapping[str, str] | None = None,
    profiles_dir: Path = PROFILES_DIR,
) -> Profile:
    env = os.environ if env is None else env
    name = name or env.get("NAV_PROFILE") or "default"
    path = profiles_dir / f"{name}.yaml"
    if not path.is_file():
        available = sorted(p.stem for p in profiles_dir.glob("*.yaml"))
        raise ProfileError(f"unknown profile {name!r}; available: {available}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ProfileError(f"{path}: expected a mapping, got {type(raw).__name__}")

    expected = {f.name for f in fields(Profile)} - {"name"}
    unknown = raw.keys() - expected
    missing = expected - raw.keys()
    if unknown or missing:
        raise ProfileError(f"{path}: unknown keys {sorted(unknown)}, missing {sorted(missing)}")

    values: dict[str, str] = {}
    for key in sorted(expected):
        value = env.get(_ENV_OVERRIDES[key]) or raw[key]
        if not isinstance(value, str) or not value.strip():
            raise ProfileError(f"{path}: {key} must be a non-empty string")
        values[key] = value.strip()
    return Profile(name=name, **values)
