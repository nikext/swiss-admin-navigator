"""Downloader behaviour with a mock transport and a fake clock (no network, no sleeping)."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

from ingest.download import DownloadError, PoliteClient, cache_path, fetch, sha256_bytes


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def client(
    handler: Callable[[httpx.Request], httpx.Response], clock: FakeClock, **kw: Any
) -> PoliteClient:
    return PoliteClient(
        transport=httpx.MockTransport(handler), clock=clock, sleep=clock.sleep, **kw
    )


def test_requests_are_spaced_by_min_interval() -> None:
    clock = FakeClock()
    with client(lambda req: httpx.Response(200, content=b"x"), clock, min_interval=1.0) as c:
        c.get("https://example.test/a")
        clock.now += 0.25  # caller did 0.25 s of work in between
        c.get("https://example.test/b")
        c.get("https://example.test/c")
    assert clock.sleeps == [0.75, 1.0]


def test_retries_5xx_with_backoff_then_succeeds() -> None:
    clock = FakeClock()
    statuses = iter([503, 502, 200])
    with client(lambda req: httpx.Response(next(statuses)), clock, min_interval=0) as c:
        assert c.get("https://example.test/").status_code == 200
        assert c.requests == 3
    assert clock.sleeps == [2.0, 4.0]


def test_retry_after_header_wins_over_backoff() -> None:
    clock = FakeClock()
    responses = iter([httpx.Response(429, headers={"Retry-After": "7"}), httpx.Response(200)])
    with client(lambda req: next(responses), clock, min_interval=0) as c:
        c.get("https://example.test/")
    assert clock.sleeps == [7.0]


def test_transport_errors_are_retried_and_finally_raised() -> None:
    clock = FakeClock()

    def boom(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=req)

    with (
        client(boom, clock, min_interval=0, max_attempts=3) as c,
        pytest.raises(DownloadError, match="after 3 attempts: ConnectError"),
    ):
        c.get("https://example.test/")
    assert clock.sleeps == [2.0, 4.0]


def test_4xx_is_not_retried() -> None:
    clock = FakeClock()
    with client(lambda req: httpx.Response(404), clock, min_interval=0) as c:
        with pytest.raises(httpx.HTTPStatusError):
            c.get("https://example.test/missing")
        assert c.requests == 1


def test_cache_path_layout(tmp_path: Path) -> None:
    assert cache_path("220", "2026-10-01", "de", tmp_path) == tmp_path / "220/2026-10-01/de.xml"


def test_fetch_uses_cache_and_checks_sha(tmp_path: Path) -> None:
    clock = FakeClock()
    body = b"<akomaNtoso/>"
    dest = tmp_path / "220/2026-10-01/de.xml"
    with client(lambda req: httpx.Response(200, content=body), clock, min_interval=0) as c:
        entry = fetch(c, "https://example.test/de.xml", dest)
        assert entry.sha256 == sha256_bytes(body)
        assert entry.bytes == len(body)
        assert dest.read_bytes() == body
        fetch(c, "https://example.test/de.xml", dest, expected_sha256=entry.sha256)
        assert c.requests == 1  # second call served from cache
        assert not dest.with_suffix(".part").exists()


def test_fetch_refuses_when_upstream_changed(tmp_path: Path) -> None:
    clock = FakeClock()
    dest = tmp_path / "x.xml"
    with (
        client(lambda req: httpx.Response(200, content=b"new"), clock, min_interval=0) as c,
        pytest.raises(DownloadError, match="make resolve"),
    ):
        fetch(c, "https://example.test/x.xml", dest, expected_sha256=sha256_bytes(b"old"))
    assert not dest.exists()
