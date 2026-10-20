"""The model-call budget: past it, only the answer's own declaration stays."""

from types import SimpleNamespace
from typing import Any

import pytest
from google.adk.models.llm_request import LlmRequest
from google.genai import types

from agents.navigator.budget import NOTICE, CallBudget


def request(*names: str) -> LlmRequest:
    decls = [types.FunctionDeclaration(name=n) for n in names]
    config = types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=decls)],
        tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig()),
    )
    return LlmRequest(config=config)


def ctx(invocation: str) -> Any:
    return SimpleNamespace(invocation_id=invocation)


def names(req: LlmRequest) -> list[str]:
    tools = [t for t in req.config.tools or [] if isinstance(t, types.Tool)]
    return [d.name or "" for t in tools for d in t.function_declarations or []]


@pytest.mark.asyncio
async def test_tools_stay_until_the_budget_then_only_the_answer_tool() -> None:
    budget = CallBudget(max_calls=3)
    for _ in range(2):
        req = request("search_law", "set_model_response")
        assert await budget.before_model(ctx("a"), req) is None
        assert names(req) == ["search_law", "set_model_response"]
    req = request("search_law", "get_article", "set_model_response")
    await budget.before_model(ctx("a"), req)
    assert names(req) == ["set_model_response"]
    assert NOTICE in str(req.config.system_instruction)
    other = request("search_law")
    await budget.before_model(ctx("b"), other)  # another turn has its own count
    assert names(other) == ["search_law"]


@pytest.mark.asyncio
async def test_native_schema_requests_lose_every_tool() -> None:
    budget = CallBudget(max_calls=1)
    req = request("search_law", "get_article")
    await budget.before_model(ctx("a"), req)
    assert req.config.tools is None
    assert req.config.tool_config is None


def test_old_invocations_are_forgotten() -> None:
    budget = CallBudget()
    for i in range(1005):
        budget.count(str(i))
    assert len(budget._calls) == 1000
    assert budget.count("1004") == 2
