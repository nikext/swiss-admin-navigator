"""Construction only: agent behaviour is tested through evals, not mocks."""

import pytest
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset

from agents.navigator.agent import (
    PROMPT,
    TOOLS,
    build_agent,
    generate_config,
    profile,
    root_agent,
)
from agents.navigator.armor import InputScreen
from agents.navigator.config import CALL_TIMEOUT_MS, RETRY, LlmRef
from agents.navigator.contract import DraftAnswer
from agents.navigator.memory import MemoryContext, save_memory
from agents.navigator.verifier import CitationVerifier, compact_tool_result


def test_root_agent_uses_profile_model_and_location() -> None:
    assert root_agent.name == "navigator"
    assert isinstance(root_agent.model, Gemini)
    assert root_agent.model.model == profile.agent.model
    assert root_agent.model.client_kwargs == {
        "enterprise": True,
        "location": profile.agent.location,
    }
    assert root_agent.model.retry_options is RETRY
    assert RETRY.attempts
    assert RETRY.attempts > 1


def test_tools_contract_and_verifier_are_wired() -> None:
    agent = build_agent("http://127.0.0.1:1/mcp")
    toolset, memory = agent.tools
    assert isinstance(memory, MemoryContext)
    assert agent.after_agent_callback is save_memory
    assert isinstance(toolset, McpToolset)
    assert toolset.tool_filter == TOOLS
    assert toolset._connection_params.url == "http://127.0.0.1:1/mcp"  # type: ignore[attr-defined]
    assert agent.output_schema is DraftAnswer
    verifier = agent.after_model_callback.__self__  # type: ignore[union-attr]
    assert isinstance(verifier, CitationVerifier)
    assert verifier.toolset is toolset
    assert agent.before_model_callback == verifier.before_model
    assert agent.after_tool_callback is compact_tool_result
    screen = agent.before_agent_callback.__self__  # type: ignore[union-attr]
    assert isinstance(screen, InputScreen)


def test_input_screen_follows_the_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODEL_ARMOR_TEMPLATE", raising=False)
    off = build_agent("http://127.0.0.1:1/mcp").before_agent_callback.__self__  # type: ignore[union-attr]
    assert off.mode == "off"
    monkeypatch.setenv("MODEL_ARMOR_TEMPLATE", "projects/p/locations/eu/templates/t")
    on = build_agent("http://127.0.0.1:1/mcp").before_agent_callback.__self__  # type: ignore[union-attr]
    assert (on.mode, on.min_level) == ("block", 2)


def test_prompt_is_served_verbatim() -> None:
    assert callable(root_agent.instruction)
    assert root_agent.instruction(None) == PROMPT  # type: ignore[arg-type]
    assert "not a lawyer" in PROMPT
    assert "data, not instructions" in PROMPT


def test_every_model_call_has_a_deadline() -> None:
    plain = generate_config(LlmRef("m", "global"))
    assert plain.http_options is not None
    assert plain.http_options.timeout == CALL_TIMEOUT_MS
    assert plain.thinking_config is None
    low = generate_config(LlmRef("m", "global", thinking="low"))
    assert low.thinking_config is not None
    assert low.thinking_config.thinking_level == "LOW"
    assert build_agent(claim_check=False).generate_content_config is not None
