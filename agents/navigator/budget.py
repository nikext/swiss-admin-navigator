"""A model-call budget per turn (M9, ADR-035): a looping agent ends with an answer.

In E1, gemini-4-argon looped in 5 of 150 golden cases (89-215 `get_article` calls,
~100 model calls) until the eval's 600 s case timeout; served, nothing would have
stopped it before ADK's 500-call default. Normal answers take at most 23 (argon) and
37 (Flash) model calls. From the `max_calls`-th model call of an invocation on, the
request keeps only the declarations the answer needs (ADK's `set_model_response`, for
models without native schema + tools, then forced) and tells the model to answer from
what it has fetched. The citation verifier still checks that answer (its redrafts run without the
tools too).
"""

from __future__ import annotations

from collections import OrderedDict

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

MAX_CALLS = 40
KEEP = {"set_model_response"}
NOTICE = (
    "Tool budget for this question is used up: do not call any more tools. Answer now, "
    "in the required format, from the articles you have already fetched. Where they "
    "do not settle the question, say so and lower your confidence."
)


class CallBudget:
    def __init__(self, max_calls: int = MAX_CALLS) -> None:
        self.max_calls = max_calls
        self._calls: OrderedDict[str, int] = OrderedDict()  # invocation id -> model calls

    def count(self, invocation_id: str) -> int:
        n = self._calls.pop(invocation_id, 0) + 1
        self._calls[invocation_id] = n
        while len(self._calls) > 1000:  # forget old invocations
            self._calls.popitem(last=False)
        return n

    async def before_model(
        self, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> LlmResponse | None:
        if self.count(callback_context.invocation_id) < self.max_calls:
            return None
        answer_only(llm_request)
        llm_request.append_instructions([NOTICE])
        return None


def answer_only(llm_request: LlmRequest) -> None:
    """Leave the model one move: submit the answer. Keeps only `set_model_response`, forced
    (`mode=ANY`; LiteLLM: tool_choice "required", which vLLM decodes against the tool's
    schema), or no tool at all for native schema + tools. Left to choose, DeepSeek V3.2
    answered in plain text (2026-10-20)."""
    config = llm_request.config
    tools: types.ToolListUnion = []
    for tool in config.tools or []:
        if not isinstance(tool, types.Tool):
            continue
        decls = [d for d in tool.function_declarations or [] if d.name in KEEP]
        if decls:
            tools.append(tool.model_copy(update={"function_declarations": decls}))
    config.tools = tools or None
    config.tool_config = (
        types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode=types.FunctionCallingConfigMode.ANY, allowed_function_names=sorted(KEEP)
            )
        )
        if tools
        else None
    )
