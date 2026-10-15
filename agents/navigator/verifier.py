"""The citation verifier as ADK model callbacks (ADR-018).

`after_model_callback` sees every model response. When it is the final answer
(text, no function calls), the draft is parsed and every citation is checked
against the law (`citecheck.py`, articles re-fetched over the agent's own MCP
session). If something is wrong and the draft has not been sent back yet, the
answer is replaced by a call to the reserved tool `citation_check`, whose
response lists the problems, so the model redrafts in the same invocation.
This is the pattern of ADK's own `ReflectAndRetryModelPlugin`: the model never
sees `citation_check` as a declared tool and cannot call it itself. After the
last round the answer is finalised: verified fields filled in by code, the
verification record attached, unverifiable parts dropped (`citecheck.finalize`).

`compact_tool_result` is an `after_tool_callback`: MCP results carry the same
JSON twice (pretty-printed text + `structuredContent`); the model gets one copy.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools import BaseTool, FunctionTool, ToolContext
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.set_model_response_tool import SetModelResponseTool
from google.adk.utils.content_utils import SKIP_THOUGHT_SIGNATURE_VALIDATOR
from google.genai import types
from pydantic import ValidationError

from .citecheck import (
    ArticleNotFoundError,
    FetchError,
    check_citations,
    finalize,
    make_round,
)
from .contract import DraftAnswer, Problem, Round

log = logging.getLogger(__name__)

CHECK_TOOL = "citation_check"
ROUNDS_KEY = "temp:citation_rounds"  # per invocation: the rounds checked so far
FIX = (
    "Your answer was not sent to the user. Fix every problem listed (re-fetch articles with "
    "get_article and copy quotes character for character, correct or drop the claims that "
    "the law text does not support), then give the complete corrected answer in the same "
    "JSON format."
)


def citation_check(draft: dict[str, Any], problems: list[dict[str, Any]]) -> dict[str, Any]:
    """Reserved for the verifier: returns the problems found in a draft answer."""
    return {"result": "rejected", "problems": problems, "instructions": FIX}


def _text_of(text_like: Any) -> str:
    parts = text_like.get("content") or []
    return " ".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()


def compact_tool_result(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext, tool_response: Any
) -> dict[str, Any] | None:
    """Give the model one copy of an MCP result: the structured one, or the error text."""
    if not isinstance(tool_response, dict) or "content" not in tool_response:
        return None
    if tool_response.get("isError"):
        return {"error": _text_of(tool_response)}
    structured = tool_response.get("structuredContent")
    return structured if isinstance(structured, dict) else None


class CitationVerifier:
    def __init__(self, toolset: McpToolset, max_retries: int = 1) -> None:
        self.toolset = toolset
        self.max_retries = max_retries
        self._check_tool = FunctionTool(func=citation_check)

    async def before_model(
        self, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> LlmResponse | None:
        # Executable but undeclared: the model cannot call it on its own.
        llm_request.tools_dict[CHECK_TOOL] = self._check_tool
        return None

    async def _fetch(self, ctx: CallbackContext, sr: str, article: str, lang: str) -> dict:
        tools = {t.name: t for t in await self.toolset.get_tools(ctx)}
        if "get_article" not in tools:
            raise FetchError("get_article is not available")
        args = {"sr": sr, "article": article, "lang": lang}
        result = await tools["get_article"].run_async(args=args, tool_context=ctx)
        if not isinstance(result, dict) or ("error" in result and "content" not in result):
            raise FetchError(str(result)[:200])
        if result.get("isError"):
            raise ArticleNotFoundError(_text_of(result))
        return result["structuredContent"]

    async def after_model(
        self, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> LlmResponse | None:
        content = llm_response.content
        if llm_response.partial or not content or not content.parts:
            return None
        calls = [p.function_call for p in content.parts if p.function_call]
        if calls:
            # Models without native schema + tools submit through ADK's set_model_response
            # tool (e.g. via LiteLLM). Check the submission the same way; the tool never runs.
            if not all(c.name == SetModelResponseTool.NAME for c in calls):
                return None
            text = json.dumps(calls[-1].args or {}, ensure_ascii=False)
        else:
            text = "".join(p.text for p in content.parts if p.text and not p.thought).strip()
        if not text:
            return None

        rounds = [Round(**r) for r in callback_context.state.get(ROUNDS_KEY) or []]
        try:
            draft = DraftAnswer.model_validate_json(text)
        except ValidationError as exc:
            problem = Problem(ref=None, kind="parse", message=f"not a valid answer: {exc}"[:500])
            rounds.append(Round(citations=0, quotes=0, problems=[problem]))
            if len(rounds) <= self.max_retries:
                return self._reject(callback_context, rounds, {"raw": text[:4000]})
            log.warning("final answer is not valid JSON after %d rounds", len(rounds))
            return None

        async def fetch(sr: str, article: str, lang: str) -> dict:
            return await self._fetch(callback_context, sr, article, lang)

        checked, answer_problems = await check_citations(draft, fetch)
        rounds.append(make_round(checked, answer_problems))
        model_problems = [p for p in rounds[-1].problems if p.kind != "fetch"]
        if model_problems and len(rounds) <= self.max_retries:
            return self._reject(callback_context, rounds, draft.model_dump())

        answer = finalize(draft, checked, answer_problems, rounds)
        callback_context.state[ROUNDS_KEY] = []
        log.info(
            "citation check",
            extra={"fields": {"status": answer.verification.status, "rounds": len(rounds)}},
        )
        return LlmResponse(
            content=types.Content(
                role="model", parts=[types.Part(text=answer.model_dump_json(exclude_none=False))]
            )
        )

    def _reject(
        self, ctx: CallbackContext, rounds: list[Round], draft: dict[str, Any]
    ) -> LlmResponse:
        ctx.state[ROUNDS_KEY] = [r.model_dump() for r in rounds]
        problems = [p.model_dump() for p in rounds[-1].problems if p.kind != "fetch"]
        call = types.FunctionCall(
            id=f"{CHECK_TOOL}_{uuid.uuid4()}",
            name=CHECK_TOOL,
            args={"draft": draft, "problems": problems},
        )
        part = types.Part(function_call=call, thought_signature=SKIP_THOUGHT_SIGNATURE_VALIDATOR)
        return LlmResponse(content=types.Content(role="model", parts=[part]))
