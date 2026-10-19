"""navigator_v1: one LlmAgent over the swiss-law MCP tools (docs/AGENTS.md §3).

The answer is structured (`contract.DraftAnswer` as `output_schema`; on Vertex
Gemini ADK sends it together with the tools, verified in M3) and every final
answer passes the deterministic citation verifier (`verifier.py`, ADR-018).
With the user's opt-in (session state set by the web BFF), remembered facts are
loaded into the instruction and each turn is sent to Memory Bank (`memory.py`,
M7, ADR-029); the memory service is the runner's (`agentengine://` on Agent
Runtime).

Config: `NAV_PROFILE` picks the model (profiles/, ADR-008);
`SWISS_LAW_MCP_URL` the MCP server (`make mcp-dev` locally, Cloud Run
otherwise); `NAV_CLAIM_CHECK=1` adds the LLM claim checker to the verifier
(M8, ADR-034; off unless set). The toolset is built synchronously here, as
Agent Runtime requires. navigator_v2 (M8) builds its specialists with
`build_agent` too.
"""

import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import BeforeToolCallback
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.genai import types

from .claims import ClaimChecker
from .config import CALL_TIMEOUT_MS, RETRY, LlmRef, load_profile
from .contract import DraftAnswer
from .memory import MemoryContext, save_memory
from .verifier import CitationVerifier, Observer, compact_tool_result

profile = load_profile()

MCP_URL = os.environ.get("SWISS_LAW_MCP_URL") or "http://127.0.0.1:8080/mcp"
TOOLS = ["search_law", "get_article", "resolve_citation", "list_acts", "get_toc"]
PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text(encoding="utf-8")


def claim_check_enabled(env: dict[str, str] | None = None) -> bool:
    value = (os.environ if env is None else env).get("NAV_CLAIM_CHECK", "")
    return value.strip().lower() in ("1", "true", "yes", "on")


def instruction_provider(prompt: str):
    # A provider, not a string: ADK would treat {braces} in a string as state variables.
    def instruction(_: ReadonlyContext) -> str:
        return prompt

    return instruction


def new_toolset(mcp_url: str) -> McpToolset:
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(url=mcp_url, timeout=15),
        tool_filter=TOOLS,
        # The server's tool list is static; don't re-list it before every model call.
        tool_list_cache_ttl_seconds=3600,
    )


def gemini(model: LlmRef) -> Gemini:
    # The endpoint location comes from the profile, not GOOGLE_CLOUD_LOCATION (ADR-013).
    return Gemini(
        model=model.model,
        client_kwargs={"enterprise": True, "location": model.location},
        retry_options=RETRY,
    )


def generate_config(model: LlmRef) -> types.GenerateContentConfig:
    """The per-call deadline and the profile's thinking level (unset = the model's default)."""
    # Per request: ADK builds the client's http_options itself; the client's RETRY still applies.
    config = types.GenerateContentConfig(http_options=types.HttpOptions(timeout=CALL_TIMEOUT_MS))
    if model.thinking is not None:
        level = types.ThinkingLevel(model.thinking.upper())
        config.thinking_config = types.ThinkingConfig(thinking_level=level)
    return config


def build_agent(
    mcp_url: str = MCP_URL,
    model: LlmRef = profile.agent,
    *,
    claim_check: bool | None = None,
    observer: Observer | None = None,
    name: str = "navigator",
    description: str = "Unofficial assistant for Swiss federal law. Not legal advice.",
    prompt: str = PROMPT,
    toolset: McpToolset | None = None,
    before_tool_callback: BeforeToolCallback | None = None,
) -> LlmAgent:
    """navigator_v1 against one MCP server. The eval harness builds its own.

    `claim_check` None follows `NAV_CLAIM_CHECK`; `observer` sees every verifier round
    (eval harness)."""
    toolset = toolset or new_toolset(mcp_url)
    if claim_check is None:
        claim_check = claim_check_enabled()
    checker = ClaimChecker(profile.role("verifier")) if claim_check else None
    verifier = CitationVerifier(toolset, claims=checker, observer=observer)
    return LlmAgent(
        name=name,
        description=description,
        model=gemini(model),
        instruction=instruction_provider(prompt),
        generate_content_config=generate_config(model),
        tools=[toolset, MemoryContext()],
        output_schema=DraftAnswer,
        before_model_callback=verifier.before_model,
        after_model_callback=verifier.after_model,
        before_tool_callback=before_tool_callback,
        after_tool_callback=compact_tool_result,
        after_agent_callback=save_memory,
    )


root_agent = build_agent()
