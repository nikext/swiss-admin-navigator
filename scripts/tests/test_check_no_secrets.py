import json
from pathlib import Path

import pytest

from scripts.check_no_secrets import main, problem


@pytest.mark.parametrize(
    "name",
    [
        ".env",
        ".env.local",
        ".env.production",
        "prod.env",
        "sa-key.json",
        "application_default_credentials.json",
        "gcp-credentials.json",
        "client_secret_123.json",
    ],
)
def test_blocked_filenames(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    path.write_text("{}")
    assert problem(path) is not None


@pytest.mark.parametrize(
    "content",
    [
        {"type": "service_account", "project_id": "p"},
        {"type": "authorized_user", "client_id": "x"},
        {"type": "external_account", "audience": "//iam..."},
        {"private_key": "redacted"},
        {"refresh_token": "1//abc"},
        {"installed": {"client_id": "x", "client_secret": "y"}},
        {"web": {"client_id": "x", "client_secret": "y"}},
    ],
)
def test_credential_json_with_innocent_name(tmp_path: Path, content: dict[str, object]) -> None:
    path = tmp_path / "notes.json"
    path.write_text(json.dumps(content))
    assert problem(path) is not None


@pytest.mark.parametrize(
    ("name", "content"),
    [
        (".env.example", "GOOGLE_CLOUD_PROJECT=\n"),
        ("manifest.lock.json", json.dumps({"acts": [{"sr": "220", "sha256": "ab"}]})),
        ("cases.json", json.dumps([{"type": "service_account"}])),  # not a top-level dict
        ("evalset.json", json.dumps({"type": "answerable", "question": "private_key?"})),
        ("broken.json", "{not json"),
        ("binary.json", b"\xff\xfe\x00"),
        ("README.md", "private_key"),
    ],
)
def test_allowed_files(tmp_path: Path, name: str, content: str | bytes) -> None:
    path = tmp_path / name
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content)
    assert problem(path) is None


def test_main_exit_code(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ok = tmp_path / "ok.json"
    ok.write_text("{}")
    bad = tmp_path / ".env"
    bad.write_text("HF_TOKEN=x")
    assert main([str(ok)]) == 0
    assert main([str(ok), str(bad)]) == 1
    assert ".env" in capsys.readouterr().err
