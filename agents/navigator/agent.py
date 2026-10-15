"""navigator_v1: one LlmAgent over the swiss-law MCP tools (docs/AGENTS.md §3).

The answer is structured (`contract.DraftAnswer` as `output_schema`; on Vertex
Gemini ADK sends it together with the tools, verified in M3) and every final
answer passes the deterministic citation verifier (`verifier.py`, ADR-018).

Config: `NAV_PROFILE` picks the model (profiles/, ADR-008);
`SWISS_LAW_MCP_URL` the MCP server (`make mcp-dev` locally, Cloud Run
otherwise). The toolset is built synchronously here, as Agent Runtime requires.
"""

import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

from .config import ModelRef, load_profile
from .contract import DraftAnswer
from .verifier import CitationVerifier, compact_tool_result

profile = load_profile()

MCP_URL = os.environ.get("SWISS_LAW_MCP_URL") or "http://127.0.0.1:8080/mcp"
TOOLS = ["search_law", "get_article", "resolve_citation", "list_acts", "get_toc"]
PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text(encoding="utf-8")


def instruction(_: ReadonlyContext) -> str:
    # A provider, not a string: ADK would treat {braces} in a string as state variables.
    return PROMPT


def build_agent(mcp_url: str = MCP_URL, model: ModelRef = profile.agent) -> LlmAgent:
    """navigator_v1 against one MCP server. The eval harness builds its own."""
    toolset = McpToolset(
        connection_params=StreamableHTTPConnectionParams(url=mcp_url, timeout=15),
        tool_filter=TOOLS,
        # The server's tool list is static; don't re-list it before every model call.
        tool_list_cache_ttl_seconds=3600,
    )
    verifier = CitationVerifier(toolset)
    return LlmAgent(
        name="navigator",
        description="Unofficial assistant for Swiss federal law. Not legal advice.",
        # The endpoint location comes from the profile, not GOOGLE_CLOUD_LOCATION (ADR-013).
        model=Gemini(
            model=model.model, client_kwargs={"enterprise": True, "location": model.location}
        ),
        instruction=instruction,
        tools=[toolset],
        output_schema=DraftAnswer,
        before_model_callback=verifier.before_model,
        after_model_callback=verifier.after_model,
        after_tool_callback=compact_tool_result,
    )


root_agent = build_agent()
