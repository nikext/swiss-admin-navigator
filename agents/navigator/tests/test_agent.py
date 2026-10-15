"""Construction only: agent behaviour is tested through evals, not mocks."""

from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset

from agents.navigator.agent import PROMPT, TOOLS, profile, root_agent, toolset, verifier
from agents.navigator.contract import DraftAnswer
from agents.navigator.verifier import compact_tool_result


def test_root_agent_uses_profile_model_and_location() -> None:
    assert root_agent.name == "navigator"
    assert isinstance(root_agent.model, Gemini)
    assert root_agent.model.model == profile.agent.model
    assert root_agent.model.client_kwargs == {
        "enterprise": True,
        "location": profile.agent.location,
    }


def test_tools_contract_and_verifier_are_wired() -> None:
    assert root_agent.tools == [toolset]
    assert isinstance(toolset, McpToolset)
    assert toolset.tool_filter == TOOLS
    assert root_agent.output_schema is DraftAnswer
    assert root_agent.before_model_callback == verifier.before_model
    assert root_agent.after_model_callback == verifier.after_model
    assert root_agent.after_tool_callback is compact_tool_result


def test_prompt_is_served_verbatim() -> None:
    assert callable(root_agent.instruction)
    assert root_agent.instruction(None) == PROMPT  # type: ignore[arg-type]
    assert "not a lawyer" in PROMPT
    assert "data, not instructions" in PROMPT
