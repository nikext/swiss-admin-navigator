"""The MCP wiring, through an in-process MCP client (no network, no embeddings)."""

import json
import logging
from pathlib import Path

import pytest
from mcp import Client

from mcp_server.server import App, JsonFormatter, RateLimiter, build_server

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


def test_background_job_starts_with_the_app_and_does_not_block_startup() -> None:
    import asyncio

    from starlette.applications import Starlette
    from starlette.testclient import TestClient

    from mcp_server.server import run_in_background_on_startup

    started, release = [], asyncio.Event()

    async def job() -> None:
        started.append(True)
        await release.wait()  # never released: startup must not wait for it

    asgi = Starlette()
    run_in_background_on_startup(asgi, job)
    with TestClient(asgi):
        pass
    assert started == [True]
