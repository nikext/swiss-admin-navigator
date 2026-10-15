"""Construction only: agent behaviour is tested through evals, not mocks."""

from google.adk.models import Gemini

from agents.navigator.agent import profile, root_agent


def test_root_agent_uses_profile_model_and_location() -> None:
    assert root_agent.name == "navigator"
    assert isinstance(root_agent.model, Gemini)
    assert root_agent.model.model == profile.agent.model
    assert root_agent.model.client_kwargs == {
        "enterprise": True,
        "location": profile.agent.location,
    }
    assert "Not legal advice" in str(root_agent.instruction)
