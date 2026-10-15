"""`corpus/acts.yaml` (what we want) and `corpus/manifest.lock.json` (what we got).

The lock pins, per act, the in-force consolidation applicable on `as_of` and,
per language, the XML file URL plus its sha256. Builds read only the lock, so
they are reproducible; `make resolve` refreshes it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

ACTS_PATH = Path("corpus/acts.yaml")
LOCK_PATH = Path("corpus/manifest.lock.json")

# Languages we ingest, in display order. Romansh (rm) exists for a few acts but
# is outside the product's DE/FR/IT/EN scope (docs/DATA.md §2).
LANGS = ("de", "fr", "it", "en")


@dataclass(frozen=True)
class Act:
    sr: str
    abbr: dict[str, str]
    title_de: str
    eli: str
    domain: tuple[str, ...]


@dataclass(frozen=True)
class FileEntry:
    url: str
    sha256: str
    bytes: int


@dataclass
class LockedAct:
    sr: str
    abbr: dict[str, str]
    eli: str
    consolidation: str
    date: str
    domain: list[str]
    files: dict[str, FileEntry] = field(default_factory=dict)

    @property
    def eli_path(self) -> str:
        """`cc/27/317_321_377` from the ELI URI, for www.fedlex.admin.ch deep links."""
        return self.eli.split("/eli/", 1)[1]


@dataclass
class Manifest:
    as_of: str
    acts: list[LockedAct]

    def to_json(self) -> str:
        data: dict[str, Any] = {"as_of": self.as_of, "acts": [asdict(a) for a in self.acts]}
        return json.dumps(data, ensure_ascii=False, indent=2) + "\n"

    def save(self, path: Path = LOCK_PATH) -> None:
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = LOCK_PATH) -> Manifest:
        data = json.loads(path.read_text(encoding="utf-8"))
        acts = [
            LockedAct(
                **{k: v for k, v in a.items() if k != "files"},
                files={lang: FileEntry(**f) for lang, f in a["files"].items()},
            )
            for a in data["acts"]
        ]
        return cls(as_of=data["as_of"], acts=acts)


def load_acts(path: Path = ACTS_PATH) -> list[Act]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    acts = []
    for a in raw["acts"]:
        domain = a["domain"] if isinstance(a["domain"], list) else [a["domain"]]
        acts.append(
            Act(
                sr=str(a["sr"]),
                abbr=dict(a["abbr"]),
                title_de=a["title_de"],
                eli=a["eli"],
                domain=tuple(domain),
            )
        )
    srs = [a.sr for a in acts]
    if len(set(srs)) != len(srs):
        raise ValueError(f"{path}: duplicate SR numbers")
    return acts
