"""Shared fixtures for the navigator's unit tests."""

import pytest
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions import InMemorySessionService


@pytest.fixture
async def ctx() -> CallbackContext:
    service = InMemorySessionService()
    session = await service.create_session(app_name="t", user_id="u")
    ic = InvocationContext(
        session_service=service, invocation_id="i1", agent=LlmAgent(name="a"), session=session
    )
    return CallbackContext(ic)
