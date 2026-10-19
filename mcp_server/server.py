"""swiss-law MCP server: read-only retrieval over Swiss federal law (ADR-003).

    uv run python -m mcp_server.server                 # stdio (local MCP clients)
    uv run python -m mcp_server.server --http          # Streamable HTTP on :8080/mcp
    K_SERVICE=… (Cloud Run)                            # HTTP on $PORT, JSON logs

Tools: search_law, get_article, get_toc, list_acts, resolve_citation.
The index (`INDEX_PATH`, default data/index.sqlite) is read-only and loaded at
startup; the only outbound call is the query embedding in `search_law`.

Limits (M10, ADR-032): `search_law` is rate-limited per client (the last
X-Forwarded-For hop, which Cloud Run's front end appends; IPv6 clients by /64),
`SEARCH_RATE_PER_MIN`/`SEARCH_BURST`. Embedding calls (cache misses) also have a
per-process budget, `EMBED_RATE_PER_MIN`/`EMBED_BURST`, across all clients:
past it, search falls back to keywords (`degraded`), so spreading requests over
many addresses can't run up the embedding bill. Request bodies over
`MAX_BODY_BYTES` get 413 before they are parsed.

Logs are one JSON object per line (Cloud Logging's structured format). They
carry the tool, latency and result counts, a salted hash instead of the client
IP, and no query text unless LOG_QUERIES=1: questions can be personal.
Rate-limit and budget hits are WARNING, so `severity>=WARNING` shows abuse.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import logging
import os
import secrets
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Any

import anyio
from dotenv import load_dotenv
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server import IMPORT_T0, STARTUP_PHASES
from mcp_server.embedding import QueryEmbedder
from mcp_server.search import Index, served_config
from mcp_server.tools import DOMAINS, NOTICE, LawTools, ToolInputError

log = logging.getLogger("swiss_law")
STARTED = time.perf_counter()

INSTRUCTIONS = f"""\
Swiss federal law (Fedlex, 23 acts on residence, work, social insurance, housing, tax,
mobility; DE/FR/IT, EN where Fedlex has it). {NOTICE}
- resolve_citation: turn references like "Art. 271a Abs. 1 lit. a OR" or "art. 30 al. 1
  let. a LEI" into checked eIds and Fedlex links. Use it for every explicit reference.
- search_law: hybrid keyword + semantic search; returns in-force articles only, one per
  article, in any language unless `lang` is set. Queries may be in EN/DE/FR/IT.
- get_article: the exact text. Fetch every article before quoting it; quote verbatim.
- get_toc / list_acts: browse an act's structure / see which acts exist.
DE, FR and IT texts are equally authoritative; EN is an unofficial translation.
"""

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        entry |= getattr(record, "fields", {})
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


class RateLimiter:
    """Token bucket per client: `rate` requests per minute, bursts up to `burst`."""

    def __init__(self, per_minute: float, burst: int, max_clients: int = 10_000) -> None:
        self.rate = per_minute / 60.0
        self.burst = float(burst)
        self.max_clients = max_clients
        self._buckets: dict[str, tuple[float, float]] = {}

    def allow(self, client: str, now: float | None = None) -> tuple[bool, float]:
        """(allowed, seconds until the next token)."""
        now = time.monotonic() if now is None else now
        tokens, last = self._buckets.get(client, (self.burst, now))
        tokens = min(self.burst, tokens + (now - last) * self.rate)
        if len(self._buckets) >= self.max_clients and client not in self._buckets:
            self._buckets.clear()  # crude bound on memory; buckets refill anyway
        if tokens >= 1.0:
            self._buckets[client] = (tokens - 1.0, now)
            return True, 0.0
        self._buckets[client] = (tokens, now)
        return False, (1.0 - tokens) / self.rate


def _request(ctx: Context | None) -> Request | None:
    try:
        request = ctx.request_context.request if ctx else None
    except ValueError:
        request = None
    return request if isinstance(request, Request) else None


def forwarded_hops(ctx: Context | None) -> list[str]:
    request = _request(ctx)
    header = request.headers.get("x-forwarded-for", "") if request else ""
    return [h.strip() for h in header.split(",") if h.strip()]


def client_ip(ctx: Context | None) -> str:
    """The last X-Forwarded-For hop, else the peer. Cloud Run's front end appends the
    address it saw; earlier hops come from the client and can be forged."""
    request = _request(ctx)
    if request is None:
        return "stdio"
    if hops := forwarded_hops(ctx):
        return hops[-1]
    return request.client.host if request.client else "unknown"


def rate_key(ip: str) -> str:
    """What a client is limited by: its IPv4 address, or its IPv6 /64 (one subscriber
    usually gets a whole /64, so per-address limits would be trivial to dodge)."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if isinstance(addr, ipaddress.IPv6Address):
        if addr.ipv4_mapped is not None:
            return str(addr.ipv4_mapped)
        return str(ipaddress.ip_network(f"{addr}/64", strict=False))
    return str(addr)


class BodyLimit:
    """ASGI middleware: 413 for HTTP request bodies over `max_bytes`, declared or streamed.

    Cloud Run accepts up to 32 MiB; an MCP tool call is a few hundred bytes, and a
    parsed 32 MiB JSON body per concurrent request would exhaust a 1 GiB instance. The
    body is read here (at most `max_bytes`) and replayed to the app, so an oversized
    one never reaches it, chunked or not."""

    def __init__(self, app: Any, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        length = dict(scope.get("headers") or []).get(b"content-length")
        if length is not None and (not length.isdigit() or int(length) > self.max_bytes):
            await self._reject(send)
            return
        parts, seen = [], 0
        while True:
            message = await receive()
            if message["type"] != "http.request":  # the client went away
                return
            seen += len(message.get("body", b""))
            if seen > self.max_bytes:
                await self._reject(send)
                return
            parts.append(message.get("body", b""))
            if not message.get("more_body"):
                break
        replayed = False

        async def replay() -> dict[str, Any]:
            nonlocal replayed
            if replayed:
                return await receive()  # later calls: disconnect notices
            replayed = True
            return {"type": "http.request", "body": b"".join(parts), "more_body": False}

        await self.app(scope, replay, send)

    async def _reject(self, send: Any) -> None:
        log.warning("request body too large", extra={"fields": {"max_bytes": self.max_bytes}})
        response = JSONResponse({"error": "request body too large"}, status_code=413)
        await response({"type": "http"}, _no_body, send)


async def _no_body() -> dict[str, Any]:
    return {"type": "http.request", "body": b"", "more_body": False}


class App:
    """Index, tools, embedder and limits for one server process."""

    def __init__(self, env: Mapping[str, str]) -> None:
        # Startup phases in seconds, logged in the "ready" line (cold-start budget).
        # "imports": third-party + app imports. Interpreter start is not included;
        # Cloud Run's "Starting new instance" -> probe log lines give the full picture.
        self.phases: dict[str, float] = {
            **STARTUP_PHASES,
            "imports": round(time.perf_counter() - IMPORT_T0, 3),
        }
        t = time.perf_counter()

        def phase(name: str) -> None:
            nonlocal t
            now = time.perf_counter()
            self.phases[name] = round(now - t, 3)
            t = now

        index_path = Path(env.get("INDEX_PATH") or "data/index.sqlite")
        self.index = Index(index_path)
        phase("index")
        self.tools = LawTools(self.index, served_config(self.index, dict(env)))
        phase("tools")
        self.space = self.index.space_spec() if self.index.meta.get("default_space") else None
        if self.space:
            self.index.space(self.space["name"])  # load vectors now, not on the first query
        phase("vectors")
        project = env.get("GOOGLE_CLOUD_PROJECT", "")
        self.embedder = QueryEmbedder(self.space, project, env) if self.space and project else None
        phase("embedder")
        self.limiter = RateLimiter(
            float(env.get("SEARCH_RATE_PER_MIN", "30")), int(env.get("SEARCH_BURST", "10"))
        )
        # One bucket for all clients: at most 30 paid embeddings a minute per instance.
        # Worst case, a flood all day over both instances: 2 x 43,200 queries x <= 300
        # tokens x USD 0.20 per 1M = USD 5/day, instead of no bound at all.
        self.embed_budget = RateLimiter(
            float(env.get("EMBED_RATE_PER_MIN", "30")), int(env.get("EMBED_BURST", "30"))
        )
        self.max_body = int(env.get("MAX_BODY_BYTES", str(64 * 1024)))
        self.log_queries = env.get("LOG_QUERIES") == "1"
        self._salt = secrets.token_bytes(16)  # per process: hashes can't be joined across days

    def client_hash(self, ip: str) -> str:
        return hashlib.sha256(self._salt + ip.encode()).hexdigest()[:12]

    def health(self) -> dict[str, Any]:
        meta = self.index.meta
        return {
            "status": "ok",
            "as_of": meta.get("as_of"),
            "index_built": meta.get("built_at"),
            "index_sha": meta.get("git_sha"),
            "records": meta.get("records"),
            "chunks": meta.get("chunks"),
            "embedding": self.embedder.describe() if self.embedder else None,
            "uptime_s": round(time.perf_counter() - STARTED, 1),
        }


def build_server(app: App) -> MCPServer:
    mcp = MCPServer(
        name="swiss-law",
        title="Swiss federal law (unofficial)",
        instructions=INSTRUCTIONS,
        version="0.2.0",
        website_url="https://github.com/nikext/swiss-admin-navigator",
        # The tool list never changes, so serve no `subscriptions/listen`: on Cloud Run
        # every open client session held one until the 60 s timeout and re-listened,
        # keeping an instance up and billed (ADR-017).
        subscriptions=False,
    )

    def logged(
        tool: str, start: float, ctx: Context | None, level: int = logging.INFO, **fields: Any
    ) -> None:
        fields = {
            "tool": tool,
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            "client": app.client_hash(rate_key(client_ip(ctx))),
            **fields,
        }
        if (hops := len(forwarded_hops(ctx))) > 1:
            fields["forwarded_hops"] = hops  # the client sent its own X-Forwarded-For
        log.log(level, tool, extra={"fields": fields})

    async def call(tool: str, ctx: Context | None, fn: Any, *args: Any, **log_fields: Any) -> Any:
        start = time.perf_counter()
        try:
            result = await anyio.to_thread.run_sync(fn, *args)
        except ToolInputError as exc:
            logged(tool, start, ctx, error="input", **log_fields)
            raise ToolError(str(exc)) from exc
        logged(tool, start, ctx, **log_fields)
        return result

    @mcp.tool(annotations=READ_ONLY)
    async def search_law(
        query: Annotated[str, Field(description="Question or keywords, any of EN/DE/FR/IT")],
        lang: Annotated[
            str | None,
            Field(description="Only return text in this language (de, fr, it, en); null = any"),
        ] = None,
        sr: Annotated[
            list[str] | None,
            Field(description='Restrict to acts, by SR number or abbreviation, e.g. ["220"]'),
        ] = None,
        k: Annotated[int, Field(ge=1, le=20, description="Number of articles")] = 8,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Search in-force Swiss federal law; returns the k best articles with snippets and
        Fedlex links. Fetch an article with get_article before quoting it."""
        start = time.perf_counter()
        allowed, wait = app.limiter.allow(rate_key(client_ip(ctx)))
        if not allowed:
            logged("search_law", start, ctx, logging.WARNING, error="rate_limited")
            raise ToolError(f"rate limit exceeded; retry in {wait:.0f} s")
        qvec, degraded = None, None
        t_embed = time.perf_counter()
        if app.embedder is not None:
            qvec = app.embedder.cached(query)
            if qvec is None and not app.embed_budget.allow("*")[0]:
                degraded = "semantic search is over this server's budget; keyword only"
                logged("search_law", start, ctx, logging.WARNING, error="embed_budget")
            elif qvec is None:
                try:
                    qvec = await app.embedder.embed(query)
                except Exception as exc:  # degrade to keyword search, never fail the call
                    degraded = f"semantic search unavailable ({type(exc).__name__}); keyword only"
                    log.warning("embedding failed", extra={"fields": {"error": repr(exc)[:300]}})
        fields: dict[str, Any] = {
            "lang": lang,
            "k": k,
            "query_chars": len(query),
            "embed_ms": round((time.perf_counter() - t_embed) * 1000, 1),
            "degraded": bool(degraded),
        }
        if app.log_queries:
            fields["query"] = query
        result = await call("search_law", ctx, app.tools.search, query, qvec, lang, sr, k, **fields)
        if degraded:
            result["degraded"] = degraded
        return result

    @mcp.tool(annotations=READ_ONLY)
    async def get_article(
        sr: Annotated[str, Field(description='SR number or abbreviation: "220", "OR", "CO"')],
        article: Annotated[
            str, Field(description='"271a", "Art. 329g bis" or an eId like "art_271_a"')
        ],
        lang: Annotated[str, Field(description="de, fr, it or en (falls back to de)")] = "de",
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """The full text of one article (paragraphs, footnotes, status, Fedlex link, as-of
        date). Quote only from this text."""
        return await call("get_article", ctx, app.tools.get_article, sr, article, lang)

    @mcp.tool(annotations=READ_ONLY)
    async def get_toc(
        sr: Annotated[str, Field(description='SR number or abbreviation, e.g. "220" or "AIG"')],
        lang: Annotated[str, Field(description="de, fr, it or en")] = "de",
        path: Annotated[
            str | None, Field(description="A node's `path` from a previous call; null = top")
        ] = None,
        depth: Annotated[int, Field(ge=1, le=3, description="Levels to expand")] = 1,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Browse an act's table of contents (parts, titles, chapters, articles)."""
        return await call("get_toc", ctx, app.tools.get_toc, sr, lang, path, depth)

    @mcp.tool(annotations=READ_ONLY)
    async def list_acts(
        domain: Annotated[
            str | None, Field(description=f"Filter: one of {', '.join(DOMAINS)}; null = all")
        ] = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """The acts in the corpus with SR numbers, abbreviations, titles, languages and the
        consolidation date (as of)."""
        return await call("list_acts", ctx, app.tools.list_acts, domain)

    @mcp.tool(annotations=READ_ONLY)
    async def resolve_citation(
        text: Annotated[
            str, Field(description='Text with citations, e.g. "Art. 271a Abs. 1 lit. a OR"')
        ],
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Find Swiss-style citations (DE/FR/IT/EN) in text and check each one: does the
        article exist, is it in force, its eId and Fedlex link."""
        return await call("resolve_citation", ctx, app.tools.resolve_citation, text)

    async def health(_: Request) -> JSONResponse:
        return JSONResponse(app.health())

    # Cloud Run reportedly reserves paths ending in "z"; /health is the fallback (ADR-017).
    mcp.custom_route("/healthz", methods=["GET"])(health)
    mcp.custom_route("/health", methods=["GET"])(health)
    return mcp


def configure_logging(json_logs: bool) -> None:
    # stderr always: in stdio mode stdout is the MCP channel, and Cloud Run parses
    # structured JSON from stderr as well.
    handler = logging.StreamHandler(sys.stderr)
    if json_logs:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)
    for noisy in ("httpx", "google_genai", "mcp", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--http", action="store_true", help="Streamable HTTP instead of stdio")
    ap.add_argument("--host", default=None)
    ap.add_argument("--port", type=int, default=None)
    args = ap.parse_args(argv)
    load_dotenv()
    on_cloud_run = bool(os.environ.get("K_SERVICE"))
    http = args.http or on_cloud_run
    configure_logging(json_logs=on_cloud_run or os.environ.get("LOG_JSON") == "1")

    app = App(os.environ)
    mcp = build_server(app)
    ready = {"transport": "http" if http else "stdio", "phases": app.phases}
    log.info("ready", extra={"fields": app.health() | ready})
    if not http:
        mcp.run("stdio")
        return 0

    import uvicorn

    host = args.host or ("0.0.0.0" if on_cloud_run else "127.0.0.1")  # noqa: S104
    port = args.port or int(os.environ.get("PORT", "8080"))
    # Stateless + JSON responses: any instance can answer any request (no session
    # affinity needed with max-instances 2), and responses are plain JSON.
    asgi = mcp.streamable_http_app(stateless_http=True, json_response=True, host=host)
    asgi = BodyLimit(asgi, app.max_body)
    uvicorn.run(asgi, host=host, port=port, log_config=None, access_log=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
