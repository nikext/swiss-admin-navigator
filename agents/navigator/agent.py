"""navigator_v1: one LlmAgent over the swiss-law MCP tools (docs/AGENTS.md §3).

The answer is structured (`contract.DraftAnswer` as `output_schema`; on Vertex
Gemini ADK sends it together with the tools, verified in M3) and every final
answer passes the deterministic citation verifier (`verifier.py`, ADR-018).
With the user's opt-in (session state set by the web BFF), remembered facts are
loaded into the instruction and each turn is sent to Memory Bank (`memory.py`,
M7, ADR-029); the memory service is the runner's (`agentengine://` on Agent
Runtime). With `MODEL_ARMOR_TEMPLATE` set, each user message is screened by Model
Armor before the first model call and obvious injections get a fixed refusal
(`armor.py`, M10, ADR-032).

Config: `NAV_PROFILE` picks the model (profiles/, ADR-008; a non-Gemini model runs
through LiteLLM, eval experiments only, M9);
`SWISS_LAW_MCP_URL` the MCP server (`make mcp-dev` locally, Cloud Run
otherwise); `NAV_CLAIM_CHECK=1` adds the LLM claim checker to the verifier
(M8, ADR-034; off unless set). The toolset is built synchronously here, as
Agent Runtime requires. navigator_v2 (M8) builds its specialists with
`build_agent` too.
"""

import os
from pathlib import Path
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import BeforeToolCallback
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models import BaseLlm, Gemini
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.genai import types

from .armor import InputScreen
from .budget import CallBudget
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


def new_toolset(mcp_url: str, tools: list[str] | None = None) -> McpToolset:
    """The swiss-law tools; `tools` narrows them for ablations (E3: without get_toc)."""
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(url=mcp_url, timeout=15),
        tool_filter=list(TOOLS if tools is None else tools),
        # The server's tool list is static; don't re-list it before every model call.
        tool_list_cache_ttl_seconds=3600,
    )


def is_gemini(model: LlmRef) -> bool:
    return model.model.startswith("gemini-")


def gemini(model: LlmRef) -> Gemini:
    # The endpoint location comes from the profile, not GOOGLE_CLOUD_LOCATION (ADR-013).
    return Gemini(
        model=model.model,
        client_kwargs={"enterprise": True, "location": model.location},
        retry_options=RETRY,
    )


# Profile thinking level → OpenAI-style `reasoning_effort` (no "minimal").
REASONING_EFFORT = {"minimal": "low", "low": "low", "medium": "medium", "high": "high"}


def open_model(model: LlmRef) -> BaseLlm:
    """A non-Gemini model through LiteLLM (M9, E1): open models on Model as a Service
    (`publisher/model-maas` on Vertex's OpenAI-compatible endpoint, ADC auth), or a vLLM server
    when the location is a URL. Eval runs only: litellm comes with the evals package, the
    deployed image does not have it."""
    from google.adk.models._capabilities import LlmCapabilities
    from google.adk.models.lite_llm import LiteLlm

    class ToolSubmitLiteLlm(LiteLlm):
        # LiteLLM reports a JSON schema mode for some of these (GLM-5.2), and ADK then sends
        # the schema with the tools: the first reply is forced to JSON and no tool is ever
        # called (2026-10-19). Submitting through ADK's set_model_response tool works for all.
        @property
        def capabilities(self) -> LlmCapabilities:
            return LlmCapabilities(output_schema_and_tools=False)

    kwargs: dict[str, Any] = {"num_retries": RETRY.attempts}
    if model.thinking is not None:
        kwargs["reasoning_effort"] = REASONING_EFFORT[model.thinking]
    if model.location.startswith(("http://", "https://")):
        # A self-hosted vLLM server's OpenAI API (Apertus on Cloud Run, ADR-006), reached
        # through `gcloud run services proxy`, which adds the identity token.
        kwargs |= {"api_base": model.location, "api_key": "unused"}
        return ToolSubmitLiteLlm(model=f"hosted_vllm/{model.model}", **kwargs)
    kwargs |= {
        "vertex_project": os.environ.get("GOOGLE_CLOUD_PROJECT"),
        "vertex_location": model.location,
    }
    return ToolSubmitLiteLlm(model=f"vertex_ai/{model.model}", **kwargs)


def llm(model: LlmRef) -> BaseLlm:
    return gemini(model) if is_gemini(model) else open_model(model)


def generate_config(model: LlmRef) -> types.GenerateContentConfig:
    """The per-call deadline and the profile's thinking level (unset = the model's default)."""
    # Per request: ADK builds the client's http_options itself; the client's RETRY still applies.
    config = types.GenerateContentConfig(http_options=types.HttpOptions(timeout=CALL_TIMEOUT_MS))
    if model.thinking is not None and is_gemini(model):  # LiteLLM: `reasoning_effort` instead
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
    screen: InputScreen | None = None,
) -> LlmAgent:
    """navigator_v1 against one MCP server. The eval harness builds its own.

    `claim_check` None follows `NAV_CLAIM_CHECK`; `observer` sees every verifier round
    (eval harness); `screen` None follows the MODEL_ARMOR_* env."""
    screen = screen or InputScreen.from_env()
    toolset = toolset or new_toolset(mcp_url)
    if claim_check is None:
        claim_check = claim_check_enabled()
    checker = ClaimChecker(profile.role("verifier")) if claim_check else None
    verifier = CitationVerifier(toolset, claims=checker, observer=observer)
    return LlmAgent(
        name=name,
        description=description,
        model=llm(model),
        instruction=instruction_provider(prompt),
        generate_content_config=generate_config(model),
        tools=[toolset, MemoryContext()],
        output_schema=DraftAnswer,
        before_agent_callback=screen.before_agent,
        # The call budget first: past it, the verifier's redrafts run without tools too.
        before_model_callback=[CallBudget().before_model, verifier.before_model],
        after_model_callback=verifier.after_model,
        before_tool_callback=before_tool_callback,
        after_tool_callback=compact_tool_result,
        after_agent_callback=save_memory,
    )


root_agent = build_agent()
