"""The harness's own view of the law: an MCP client to the server the agent used.

The harness re-checks every final citation itself instead of trusting the
agent's verification record. `local_server()` starts `mcp_server` on a free
port with a relaxed rate limit, so eval runs neither hit the public server's
per-IP limit nor depend on it.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
from mcp import Client

from agents.navigator.citecheck import ArticleNotFoundError, FetchError


class LawClient:
    def __init__(self, url: str) -> None:
        self.url = url
        self._client: Client | None = None
        self._cache: dict[tuple[str, str, str], dict[str, Any] | Exception] = {}
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> LawClient:
        self._client = Client(self.url, read_timeout_seconds=30)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._client is not None:
            await self._client.__aexit__(None, None, None)

    async def get_article(self, sr: str, article: str, lang: str) -> dict[str, Any]:
        """`get_article`, cached. Raises ArticleNotFoundError / FetchError like the verifier."""
        key = (sr.strip(), article.strip(), lang)
        if key not in self._cache:
            if self._client is None:
                raise RuntimeError("use LawClient as an async context manager")
            try:
                async with self._lock:  # one request at a time on the shared session
                    result = await self._client.call_tool(
                        "get_article", {"sr": key[0], "article": key[1], "lang": lang}
                    )
            except Exception as exc:
                raise FetchError(f"{type(exc).__name__}: {exc}") from exc
            if result.is_error:
                text = " ".join(getattr(c, "text", "") for c in result.content)
                self._cache[key] = ArticleNotFoundError(text)
            else:
                self._cache[key] = result.structured_content or {}
        value = self._cache[key]
        if isinstance(value, Exception):
            raise value
        return value

    def health(self) -> dict[str, Any]:
        r = httpx.get(self.url.removesuffix("/mcp") + "/health", timeout=30)
        r.raise_for_status()
        return r.json()


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def local_server(log_path: Path, timeout_s: float = 60, port: int | None = None) -> Iterator[str]:
    """Run the MCP server from this checkout (needs data/index.sqlite); yields its URL."""
    port = port or _free_port()
    # The harness is the only client: lift the per-client limit and the embedding budget
    # (M10, ADR-033), which would otherwise turn bursts of searches into keyword-only ones.
    env = os.environ | {
        "SEARCH_RATE_PER_MIN": "6000", "SEARCH_BURST": "200",
        "EMBED_RATE_PER_MIN": "6000", "EMBED_BURST": "200",
    }  # fmt: skip
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w") as log:
        proc = subprocess.Popen(  # noqa: S603 (our own module, fixed args)
            [sys.executable, "-m", "mcp_server.server", "--http", "--port", str(port)],
            env=env, stdout=log, stderr=subprocess.STDOUT,
        )  # fmt: skip
        url = f"http://127.0.0.1:{port}/mcp"
        try:
            deadline = time.monotonic() + timeout_s
            while True:
                if proc.poll() is not None:
                    raise RuntimeError(f"MCP server exited ({proc.returncode}); see {log_path}")
                try:
                    if httpx.get(url.removesuffix("/mcp") + "/health", timeout=2).is_success:
                        break
                except httpx.HTTPError:
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError(
                        f"MCP server not healthy after {timeout_s} s; see {log_path}"
                    )
                time.sleep(0.3)
            yield url
        finally:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
