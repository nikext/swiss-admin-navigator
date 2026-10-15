"""Time a fresh MCP session against the swiss-law server: connect, then two searches.

Run it after the Cloud Run service has been idle long enough to scale to zero
(≥15 min) to measure a cold start as a client sees it (ADR-017): the
`initialize` handshake (which waits for the instance to start), the first
`search_law` (the first query embedding) and a second one for the warm
reference. Read the server's side from the `ready` log line (startup phases).

Usage: uv run python -m scripts.cold_start [URL]   (default: $SWISS_LAW_MCP_URL)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import UTC, datetime

from dotenv import load_dotenv
from mcp import Client

QUERIES = (
    "How long is the notice period in the first year of employment?",
    "Wie hoch darf die Mietkaution sein?",
)


async def measure(url: str) -> dict[str, object]:
    out: dict[str, object] = {"url": url, "utc": datetime.now(UTC).isoformat(timespec="seconds")}
    t0 = time.perf_counter()
    # legacy = the initialize handshake that Claude Code and ADK's McpToolset send.
    async with Client(url, mode="legacy", read_timeout_seconds=60) as client:
        out["connect_s"] = round(time.perf_counter() - t0, 2)
        for i, query in enumerate(QUERIES, 1):
            t = time.perf_counter()
            res = await client.call_tool("search_law", {"query": query, "k": 3})
            out[f"search{i}_s"] = round(time.perf_counter() - t, 2)
            data = res.structured_content or {}
            out[f"search{i}_mode"] = "error" if res.is_error else data.get("mode")
            if i == 1:
                out["first_result_s"] = round(time.perf_counter() - t0, 2)
    return out


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = sys.argv[1:] if argv is None else argv
    url = args[0] if args else os.environ.get("SWISS_LAW_MCP_URL", "")
    if not url:
        print("pass the MCP URL or set SWISS_LAW_MCP_URL", file=sys.stderr)
        return 2
    out = asyncio.run(measure(url))
    print(json.dumps(out))
    return 0 if out.get("search1_mode") == "dense" else 1


if __name__ == "__main__":
    sys.exit(main())
