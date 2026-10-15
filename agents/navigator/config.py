"""Model profiles (ADR-008): model IDs live in `profiles/<name>.yaml`, never in code.

Each role (agent, judge, embedding) names a model and the Agent Platform
endpoint location that serves it (`eu`, `global`, or a region; ADR-013). That
location is deliberately independent of `GOOGLE_CLOUD_LOCATION`, which is the
infrastructure region (Agent Runtime, Cloud Run).

The embedding role also says how the model takes the query/document hint
(`input_format`): `instruction` puts it in the text ("task: search result |
query: ..."; gemini-embedding-2 ignores `task_type` and fuses a multi-text
request into one vector), `task_type` passes RETRIEVAL_QUERY/RETRIEVAL_DOCUMENT
(gemini-embedding-001). Verified live on 2026-10-15, see ADR-015.

The profile is chosen by `NAV_PROFILE` (default: `default`). Single fields can
be overridden per run with `<ROLE>_<FIELD>` (e.g. `AGENT_MODEL`,
`JUDGE_LOCATION`, `EMBEDDING_INPUT_FORMAT`), which is how eval experiments swap
models. Eval reports must record `Profile.as_dict()` so results stay
reproducible.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Set
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


INPUT_FORMATS = ("instruction", "task_type")


@dataclass(frozen=True)
class EmbeddingRef(ModelRef):
    input_format: str = "instruction"


@dataclass(frozen=True)
class Profile:
    name: str
    agent: ModelRef
    judge: ModelRef
    embedding: EmbeddingRef

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


ROLES = tuple(f.name for f in fields(Profile) if f.name != "name")
_REF_KEYS = {f.name for f in fields(ModelRef)}
# Optional keys per role, with the dataclass default when absent.
_OPTIONAL_KEYS = {"embedding": {"input_format"}}
_REF_TYPES: dict[str, type[ModelRef]] = {"embedding": EmbeddingRef}


def _keys_check(
    where: str, raw: Mapping[str, Any], expected: set[str], optional: Set[str] = frozenset()
) -> None:
    unknown, missing = raw.keys() - expected - optional, expected - raw.keys()
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

    refs: dict[str, Any] = {}
    for role in ROLES:
        section = raw[role]
        if not isinstance(section, dict):
            raise ProfileError(f"{path}: {role} must be a mapping with {sorted(_REF_KEYS)}")
        optional = _OPTIONAL_KEYS.get(role, set())
        _keys_check(f"{path}: {role}", section, _REF_KEYS, optional)
        values: dict[str, str] = {}
        for key in sorted(_REF_KEYS | optional):
            value = env.get(f"{role}_{key}".upper()) or section.get(key)
            if value is None and key in optional:
                continue
            if not isinstance(value, str) or not value.strip():
                raise ProfileError(f"{path}: {role}.{key} must be a non-empty string")
            values[key] = value.strip()
        refs[role] = _REF_TYPES.get(role, ModelRef)(**values)
    if refs["embedding"].input_format not in INPUT_FORMATS:
        raise ProfileError(f"{path}: embedding.input_format must be one of {INPUT_FORMATS}")
    return Profile(name=name, **refs)
