"""Polite, cached downloads from Fedlex (docs/DATA.md §4 step 2).

- One request per `min_interval` seconds (default 1 s), serial.
- Retries with exponential backoff on transport errors, 429 and 5xx, honouring
  `Retry-After`.
- Files are cached under `cache/raw/<sr>/<date>/<lang>.xml` and checked against
  the sha256 in `corpus/manifest.lock.json`.

Usage: uv run python -m ingest.download   (downloads whatever the lock lists)
"""

from __future__ import annotations

import hashlib
import logging
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from ingest.manifest import LOCK_PATH, FileEntry, Manifest

log = logging.getLogger(__name__)

CACHE_DIR = Path("cache/raw")
USER_AGENT = "swiss-admin-navigator/0.1 (+https://github.com/nikext/swiss-admin-navigator)"
RETRY_STATUS = {429, 500, 502, 503, 504}


class DownloadError(RuntimeError):
    pass


class PoliteClient:
    """httpx wrapper: serial, rate-limited, retrying. Clock and sleep are injectable for tests."""

    def __init__(
        self,
        *,
        min_interval: float = 1.0,
        max_attempts: int = 5,
        backoff: float = 2.0,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
        )
        self.min_interval = min_interval
        self.max_attempts = max_attempts
        self.backoff = backoff
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None
        self.requests = 0

    def __enter__(self) -> PoliteClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self._client.close()

    def _throttle(self) -> None:
        if self._last is not None:
            wait = self.min_interval - (self._clock() - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        delay = self.backoff
        for attempt in range(1, self.max_attempts + 1):
            self._throttle()
            self.requests += 1
            try:
                resp = self._client.request(method, url, **kwargs)
            except httpx.TransportError as exc:
                problem: str = f"{type(exc).__name__}: {exc}"
                retry_after = None
            else:
                if resp.status_code not in RETRY_STATUS:
                    resp.raise_for_status()
                    return resp
                problem = f"HTTP {resp.status_code}"
                retry_after = _retry_after(resp)
            if attempt == self.max_attempts:
                raise DownloadError(f"{method} {url} failed after {attempt} attempts: {problem}")
            wait = retry_after if retry_after is not None else delay
            log.warning("%s %s: %s; retry %d in %.1fs", method, url, problem, attempt, wait)
            self._sleep(wait)
            delay *= 2
        raise AssertionError("unreachable")

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)


def _retry_after(resp: httpx.Response) -> float | None:
    value = resp.headers.get("Retry-After")
    try:
        return max(0.0, float(value)) if value is not None else None
    except ValueError:
        return None  # HTTP-date form: fall back to our own backoff


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cache_path(sr: str, date: str, lang: str, cache_dir: Path = CACHE_DIR) -> Path:
    return cache_dir / sr / date / f"{lang}.xml"


def fetch(
    client: PoliteClient, url: str, dest: Path, expected_sha256: str | None = None
) -> FileEntry:
    """Return the cached file's entry, downloading it if it is missing or stale.

    With `expected_sha256` (from the lock), a mismatch after download is an
    error: Fedlex changed the file behind a URL we pinned, so re-resolve.
    """
    if dest.is_file():
        data = dest.read_bytes()
        digest = sha256_bytes(data)
        if expected_sha256 in (None, digest):
            return FileEntry(url=url, sha256=digest, bytes=len(data))
        log.info("cached %s does not match the lock; re-downloading", dest)
    data = client.get(url).content
    digest = sha256_bytes(data)
    if expected_sha256 is not None and digest != expected_sha256:
        raise DownloadError(
            f"{url}: sha256 {digest[:12]}… does not match the lock ({expected_sha256[:12]}…). "
            "Fedlex changed the file; run `make resolve` to refresh the lock."
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return FileEntry(url=url, sha256=digest, bytes=len(data))


def download_all(manifest: Manifest, client: PoliteClient, cache_dir: Path = CACHE_DIR) -> int:
    """Make sure every file in the lock is cached and matches its sha256."""
    fetched = 0
    for act in manifest.acts:
        for lang, entry in act.files.items():
            dest = cache_path(act.sr, act.date, lang, cache_dir)
            before = client.requests
            fetch(client, entry.url, dest, expected_sha256=entry.sha256)
            fetched += client.requests > before
    return fetched


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    manifest = Manifest.load(LOCK_PATH)
    with PoliteClient() as client:
        fetched = download_all(manifest, client)
    total = sum(len(a.files) for a in manifest.acts)
    print(f"{total} files in the lock, {fetched} downloaded, {total - fetched} from cache")
    return 0


if __name__ == "__main__":
    sys.exit(main())
