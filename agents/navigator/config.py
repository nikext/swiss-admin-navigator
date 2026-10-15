"""Model profiles (ADR-008): model IDs live in `profiles/<name>.yaml`, never in code.

Each role (agent, judge, embedding) names a model and the Agent Platform
endpoint location that serves it (`eu`, `global`, or a region; ADR-013). That
location is deliberately independent of `GOOGLE_CLOUD_LOCATION`, which is the
infrastructure region (Agent Runtime, Cloud Run).

The profile is chosen by `NAV_PROFILE` (default: `default`). Single fields can
be overridden per run with `<ROLE>_MODEL` / `<ROLE>_LOCATION` (e.g.
`AGENT_MODEL`, `JUDGE_LOCATION`), which is how eval experiments swap models.
Eval reports must record `Profile.as_dict()` so results stay reproducible.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

import yaml

PROFILES_DIR = Path(__file__).parent / "profiles"


class ProfileError(ValueError):
    """A profile is missing, malformed, or has unknown or missing keys."""


@dataclass(frozen=True)
class ModelRef:
    model: str
    location: str


@dataclass(frozen=True)
class Profile:
    name: str
    agent: ModelRef
    judge: ModelRef
    embedding: ModelRef

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


ROLES = tuple(f.name for f in fields(Profile) if f.name != "name")
_REF_KEYS = {f.name for f in fields(ModelRef)}


def _keys_check(where: str, raw: Mapping[str, Any], expected: set[str]) -> None:
    unknown, missing = raw.keys() - expected, expected - raw.keys()
    if unknown or missing:
        raise ProfileError(f"{where}: unknown keys {sorted(unknown)}, missing {sorted(missing)}")


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
    _keys_check(str(path), raw, set(ROLES))

    refs: dict[str, ModelRef] = {}
    for role in ROLES:
        section = raw[role]
        if not isinstance(section, dict):
            raise ProfileError(f"{path}: {role} must be a mapping with {sorted(_REF_KEYS)}")
        _keys_check(f"{path}: {role}", section, _REF_KEYS)
        values: dict[str, str] = {}
        for key in sorted(_REF_KEYS):
            value = env.get(f"{role}_{key}".upper()) or section[key]
            if not isinstance(value, str) or not value.strip():
                raise ProfileError(f"{path}: {role}.{key} must be a non-empty string")
            values[key] = value.strip()
        refs[role] = ModelRef(**values)
    return Profile(name=name, **refs)
