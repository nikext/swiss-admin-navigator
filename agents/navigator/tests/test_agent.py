"""Construction only: agent behaviour is tested through evals, not mocks."""

import pytest
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset

from agents.navigator.agent import (
    PROMPT,
    TOOLS,
    build_agent,
    generate_config,
    llm,
    profile,
    root_agent,
)
from agents.navigator.armor import InputScreen
from agents.navigator.budget import CallBudget
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
    budget, check = agent.before_model_callback  # type: ignore[misc]
    assert isinstance(budget.__self__, CallBudget)  # type: ignore[union-attr]
    assert check == verifier.before_model
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
    low = generate_config(LlmRef(profile.agent.model, "global", thinking="low"))  # a Gemini
    assert low.thinking_config is not None
    assert low.thinking_config.thinking_level == "LOW"
    assert build_agent(claim_check=False).generate_content_config is not None


def test_open_models_go_through_litellm_and_submit_through_a_tool() -> None:
    # M9 (E1): any non-Gemini profile model runs through LiteLLM on Vertex MaaS.
    from google.adk.models.lite_llm import LiteLlm

    ref = LlmRef("some-publisher/some-model-maas", "global", "medium")
    model = llm(ref)
    assert isinstance(model, LiteLlm)
    assert model.model == "vertex_ai/some-publisher/some-model-maas"
    assert model._additional_args["vertex_location"] == "global"
    assert model._additional_args["reasoning_effort"] == "medium"
    assert model._additional_args["num_retries"] == RETRY.attempts
    assert model.capabilities.output_schema_and_tools is False  # set_model_response, not JSON mode
    assert generate_config(ref).thinking_config is None
    agent = build_agent("http://127.0.0.1:1/mcp", ref)
    assert agent.model is not None
    assert not isinstance(agent.model, Gemini)


def test_a_url_location_is_a_vllm_server() -> None:
    model = llm(LlmRef("some-org/some-model", "http://127.0.0.1:8081/v1"))
    assert model.model == "hosted_vllm/some-org/some-model"
    assert model._additional_args["api_base"] == "http://127.0.0.1:8081/v1"  # type: ignore[attr-defined]
    assert "vertex_location" not in model._additional_args  # type: ignore[attr-defined]
    assert model.capabilities.output_schema_and_tools is False
