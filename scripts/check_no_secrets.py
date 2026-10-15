"""pre-commit guard: block `.env` files and GCP key / credential JSON.

Filenames are checked by pattern; `*.json` files are also checked by content,
because we do commit JSON (corpus/manifest.lock.json, eval datasets) and a key
file can have any name. Stdlib only, so pre-commit can run it in a bare env.

Usage: python scripts/check_no_secrets.py FILE...
"""

from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path

ALLOWED_NAMES = {".env.example"}
BLOCKED_NAME_PATTERNS = [
    ".env",
    ".env.*",
    "*.env",
    "*-key.json",
    "*credentials*.json",
    "client_secret*.json",
]
# Top-level keys that only appear in service-account keys, ADC / authorized-user
# files, OAuth client secrets and external-account (WIF) credential configs.
SECRET_JSON_KEYS = {"private_key", "private_key_id", "refresh_token", "client_secret"}
SECRET_JSON_TYPES = {"service_account", "authorized_user", "external_account"}


def problem(path: Path) -> str | None:
    """Return why `path` must not be committed, or None if it is fine."""
    name = path.name
    if name in ALLOWED_NAMES:
        return None
    for pattern in BLOCKED_NAME_PATTERNS:
        if fnmatch.fnmatch(name, pattern):
            return f"filename matches {pattern!r}"
    if path.suffix.lower() != ".json" or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if data.get("type") in SECRET_JSON_TYPES:
        return f"JSON credential of type {data['type']!r}"
    found = SECRET_JSON_KEYS & data.keys()
    if found:
        return f"JSON contains secret keys {sorted(found)}"
    for section in ("installed", "web"):
        inner = data.get(section)
        if isinstance(inner, dict) and "client_secret" in inner:
            return "OAuth client secret JSON"
    return None


def main(argv: list[str]) -> int:
    failures = [(arg, why) for arg in argv if (why := problem(Path(arg)))]
    for arg, why in failures:
        print(f"refusing to commit {arg}: {why}", file=sys.stderr)
    if failures:
        print("Secrets belong in .env (gitignored), ADC, or Secret Manager.", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
