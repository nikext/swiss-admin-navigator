"""The MCP wiring, through an in-process MCP client (no network, no embeddings)."""

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from mcp import Client
from starlette.requests import Request

from mcp_server.server import (
    App,
    BodyLimit,
    JsonFormatter,
    RateLimiter,
    build_server,
    client_ip,
    forwarded_hops,
    rate_key,
)
from mcp_server.tests.conftest import bow_vector

TOOLS = {"search_law", "get_article", "get_toc", "list_acts", "resolve_citation"}


@pytest.fixture
def app(fixture_index_path: Path) -> App:
    # No GOOGLE_CLOUD_PROJECT: no query embedder, so search_law runs keyword-only.
    return App({"INDEX_PATH": str(fixture_index_path), "SEARCH_RATE_PER_MIN": "60"})


async def test_lists_the_five_read_only_tools(app: App) -> None:
    async with Client(build_server(app)) as client:
        tools = (await client.list_tools()).tools
    assert {t.name for t in tools} == TOOLS
    for t in tools:
        assert t.annotations is not None
        assert t.annotations.read_only_hint is True
        assert t.description


async def test_tools_answer_over_mcp(app: App) -> None:
    async with Client(build_server(app)) as client:
        art = await client.call_tool("get_article", {"sr": "OR", "article": "271a"})
        assert not art.is_error
        assert art.structured_content is not None
        assert art.structured_content["eid"] == "art_271_a"

        res = await client.call_tool(
            "search_law", {"query": "Kündigung durch den Vermieter Treu und Glauben", "k": 2}
        )
        payload = res.structured_content or {}
        assert payload["mode"] == "bm25"
        assert payload["results"][0]["eid"] == "art_271_a"

        cites = await client.call_tool("resolve_citation", {"text": "Art. 271a Abs. 1 OR"})
        assert (cites.structured_content or {})["citations"][0]["exists"] is True


async def test_input_errors_come_back_as_tool_errors(app: App) -> None:
    async with Client(build_server(app)) as client:
        res = await client.call_tool("get_article", {"sr": "OR", "article": "999"})
    assert res.is_error
    assert "no article" in json.dumps([c.model_dump() for c in res.content])


async def test_search_is_rate_limited_per_client(fixture_index_path: Path) -> None:
    app = App(
        {"INDEX_PATH": str(fixture_index_path), "SEARCH_RATE_PER_MIN": "1", "SEARCH_BURST": "2"}
    )
    async with Client(build_server(app)) as client:
        results = [await client.call_tool("search_law", {"query": "Mieter"}) for _ in range(3)]
    assert [r.is_error for r in results] == [False, False, True]
    assert "rate limit" in json.dumps([c.model_dump() for c in results[2].content])


def test_rate_limiter_refills_over_time() -> None:
    rl = RateLimiter(per_minute=60, burst=2)
    assert rl.allow("a", now=0.0) == (True, 0.0)
    assert rl.allow("a", now=0.0)[0] is True
    allowed, wait = rl.allow("a", now=0.0)
    assert (allowed, round(wait, 3)) == (False, 1.0)
    assert rl.allow("b", now=0.0)[0] is True  # per client
    assert rl.allow("a", now=1.0)[0] is True  # one token per second


def test_health_reports_index_metadata(app: App) -> None:
    h = app.health()
    assert (h["status"], h["as_of"], h["embedding"]) == ("ok", "2026-10-15", None)


def test_json_log_lines_carry_fields_but_no_raw_ip(app: App) -> None:
    rec = logging.LogRecord("swiss_law", logging.INFO, __file__, 1, "search_law", (), None)
    rec.fields = {"tool": "search_law", "client": app.client_hash("203.0.113.9")}
    line = json.loads(JsonFormatter().format(rec))
    assert line["severity"] == "INFO"
    assert line["tool"] == "search_law"
    assert "203.0.113.9" not in json.dumps(line)
    assert len(line["client"]) == 12


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_no_list_changed_so_clients_open_no_listen_stream(app: App, mode: str) -> None:
    async with Client(build_server(app), mode=mode) as client:
        caps = client.server_capabilities
    assert caps.tools is not None
    assert not caps.tools.list_changed


def request_ctx(xff: str | None = None, peer: str = "10.0.0.9") -> Any:
    headers = [(b"x-forwarded-for", xff.encode())] if xff is not None else []
    scope = {"type": "http", "headers": headers, "client": (peer, 1234)}
    return SimpleNamespace(request_context=SimpleNamespace(request=Request(scope)))


def test_client_ip_is_the_hop_cloud_run_appended() -> None:
    assert client_ip(request_ctx("203.0.113.7")) == "203.0.113.7"
    # A client-supplied header comes first; Cloud Run's front end appends the real address.
    assert client_ip(request_ctx("1.2.3.4, 203.0.113.7")) == "203.0.113.7"
    assert client_ip(request_ctx()) == "10.0.0.9"
    assert client_ip(None) == "stdio"
    assert forwarded_hops(request_ctx("1.2.3.4,  203.0.113.7")) == ["1.2.3.4", "203.0.113.7"]


def test_rate_key_groups_ipv6_by_slash_64() -> None:
    assert rate_key("203.0.113.7") == "203.0.113.7"
    assert rate_key("2001:db8:1:2:aaaa::1") == rate_key("2001:db8:1:2:ffff::9")
    assert rate_key("2001:db8:1:2::1") == "2001:db8:1:2::/64"
    assert rate_key("2001:db8:1:3::1") != rate_key("2001:db8:1:2::1")
    assert rate_key("::ffff:203.0.113.7") == "203.0.113.7"
    assert rate_key("stdio") == "stdio"


class FakeEmbedder:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.cache: dict[str, Any] = {}

    def cached(self, query: str) -> Any:
        return self.cache.get(query)

    async def embed(self, query: str) -> Any:
        self.calls.append(query)
        self.cache[query] = bow_vector(query)
        return self.cache[query]

    def describe(self) -> dict[str, Any]:
        return {}


async def test_embedding_budget_degrades_to_keywords(app: App) -> None:
    fake = FakeEmbedder()
    app.embedder = fake  # type: ignore[assignment]
    app.embed_budget = RateLimiter(per_minute=0.001, burst=1)
    async with Client(build_server(app)) as client:
        first = await client.call_tool("search_law", {"query": "Kündigung Vermieter"})
        second = await client.call_tool("search_law", {"query": "Mietzins Erhöhung"})
        again = await client.call_tool("search_law", {"query": "Kündigung Vermieter"})
    assert fake.calls == ["Kündigung Vermieter"]  # the cache hit costs no budget
    assert "degraded" not in (first.structured_content or {})
    assert (second.structured_content or {})["mode"] == "bm25"
    assert "budget" in (second.structured_content or {})["degraded"]
    assert "degraded" not in (again.structured_content or {})


async def asgi_call(app: Any, body: bytes, chunked: bool = False) -> tuple[int, bytes]:
    headers = [] if chunked else [(b"content-length", str(len(body)).encode())]
    scope = {"type": "http", "method": "POST", "path": "/mcp", "headers": headers}
    chunks = [body[i : i + 1000] for i in range(0, len(body), 1000)] or [b""]
    queue = [{"type": "http.request", "body": c, "more_body": i < len(chunks) - 1}
             for i, c in enumerate(chunks)]  # fmt: skip
    sent: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return queue.pop(0)

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    await app(scope, receive, send)
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    return status, b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")


async def echo_app(scope: Any, receive: Any, send: Any) -> None:
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if not message.get("more_body"):
            break
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": str(len(body)).encode()})


async def test_body_limit() -> None:
    limited = BodyLimit(echo_app, max_bytes=4096)
    assert await asgi_call(limited, b"x" * 4096) == (200, b"4096")
    status, body = await asgi_call(limited, b"x" * 4097)
    assert status == 413
    assert b"too large" in body
    # No Content-Length (chunked): counted while streaming.
    assert (await asgi_call(limited, b"x" * 5000, chunked=True))[0] == 413
    assert await asgi_call(limited, b"x" * 3000, chunked=True) == (200, b"3000")
