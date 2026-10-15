"""Construction only: agent behaviour is tested through evals, not mocks."""

from agents.navigator.agent import profile, root_agent


def test_root_agent_uses_profile_model() -> None:
    assert root_agent.name == "navigator"
    assert root_agent.model == profile.agent_model
    assert "Not legal advice" in str(root_agent.instruction)
