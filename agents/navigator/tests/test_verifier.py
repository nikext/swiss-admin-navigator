"""The verifier callbacks with a fake MCP toolset (no model, no network)."""

import json
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from agents.navigator.tests.test_citecheck import ART_271A, cite, draft
from agents.navigator.verifier import CHECK_TOOL, CitationVerifier, compact_tool_result


class FakeTool:
    name = "get_article"

    async def run_async(self, *, args: dict[str, Any], tool_context: Any) -> dict[str, Any]:
        if args["article"] != ART_271A["label"]:
            text = f"no article {args['article']!r} in SR {args['sr']}"
            return {"content": [{"type": "text", "text": text}], "isError": True}
        return {"content": [{"type": "text", "text": "..."}], "structuredContent": ART_271A}


class FakeToolset:
    async def get_tools(self, readonly_context: Any = None) -> list[FakeTool]:
        return [FakeTool()]


def text_response(text: str, partial: bool = False) -> LlmResponse:
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=text)]), partial=partial
    )


def verifier() -> CitationVerifier:
    return CitationVerifier(FakeToolset())  # type: ignore[arg-type]


def part(out: LlmResponse | None) -> types.Part:
    assert out is not None
    assert out.content
    assert out.content.parts
    return out.content.parts[0]


def final(out: LlmResponse | None) -> dict[str, Any]:
    text = part(out).text
    assert text
    return json.loads(text)


def check_call(out: LlmResponse | None) -> dict[str, Any]:
    call = part(out).function_call
    assert call is not None
    assert call.name == CHECK_TOOL
    assert call.args
    return call.args


async def test_good_answer_is_finalised(ctx: CallbackContext) -> None:
    out = await verifier().after_model(ctx, text_response(draft(cite()).model_dump_json()))
    answer = final(out)
    assert answer["verification"]["status"] == "passed"
    assert answer["citations"][0]["url"] == ART_271A["url"]
    assert answer["notice"].startswith("Unofficial")


async def test_bad_answer_is_sent_back_once_then_degraded(ctx: CallbackContext) -> None:
    v = verifier()
    bad = draft(cite(article="Art. 999")).model_dump_json()
    out = await v.after_model(ctx, text_response(bad))
    args = check_call(out)
    assert [p["kind"] for p in args["problems"]] == ["not_found"]
    assert args["draft"]["citations"][0]["article"] == "Art. 999"
    assert part(out).thought_signature  # a synthesized call must carry one

    out = await v.after_model(ctx, text_response(bad))  # the redraft is still wrong
    answer = final(out)
    assert answer["verification"]["status"] == "degraded"
    assert len(answer["verification"]["rounds"]) == 2
    assert answer["citations"] == []
    assert answer["confidence"] == "low"


async def test_fixed_redraft_passes_after_retry(ctx: CallbackContext) -> None:
    v = verifier()
    await v.after_model(ctx, text_response(draft(cite(article="Art. 999")).model_dump_json()))
    out = await v.after_model(ctx, text_response(draft(cite()).model_dump_json()))
    assert final(out)["verification"]["status"] == "passed_after_retry"


async def test_set_model_response_submission_is_checked(ctx: CallbackContext) -> None:
    call = types.FunctionCall(name="set_model_response", args=draft(cite()).model_dump())
    content = types.Content(role="model", parts=[types.Part(function_call=call)])
    out = await verifier().after_model(ctx, LlmResponse(content=content))
    assert part(out).function_call is None  # replaced by the final text
    assert final(out)["verification"]["status"] == "passed"


async def test_invalid_json_is_sent_back(ctx: CallbackContext) -> None:
    out = await verifier().after_model(ctx, text_response('{"language": "en"}'))
    assert check_call(out)["problems"][0]["kind"] == "parse"


async def test_ignored_responses(ctx: CallbackContext) -> None:
    v = verifier()
    assert await v.after_model(ctx, text_response("{", partial=True)) is None
    search = types.FunctionCall(name="search_law", args={"query": "x"})
    tool_call = LlmResponse(
        content=types.Content(role="model", parts=[types.Part(function_call=search)])
    )
    assert await v.after_model(ctx, tool_call) is None
    assert await v.after_model(ctx, LlmResponse()) is None


async def test_check_tool_is_executable_but_not_declared(ctx: CallbackContext) -> None:
    request = LlmRequest()
    assert await verifier().before_model(ctx, request) is None
    assert CHECK_TOOL in request.tools_dict
    assert not request.config.tools  # no declaration: the model cannot call it


async def test_redraft_after_a_parse_failure_can_only_submit(ctx: CallbackContext) -> None:
    v = verifier()

    def request() -> LlmRequest:
        decls = [types.FunctionDeclaration(name=n) for n in ("search_law", "set_model_response")]
        tools: types.ToolListUnion = [types.Tool(function_declarations=decls)]
        return LlmRequest(config=types.GenerateContentConfig(tools=tools))

    untouched = request()
    await v.before_model(ctx, untouched)
    assert untouched.config.tool_config is None
    await v.after_model(ctx, text_response('{"language": "en"}'))  # parse problem -> sent back
    forced = request()
    await v.before_model(ctx, forced)
    assert [d.name for t in forced.config.tools for d in t.function_declarations] == [  # type: ignore[union-attr]
        "set_model_response"
    ]
    await v.after_model(ctx, text_response('{"language": "en"}'))  # retries used up
    later = request()
    await v.before_model(ctx, later)
    assert later.config.tool_config is None  # no forcing beyond the requested redraft


def test_compact_tool_result() -> None:
    structured = {"results": [1]}
    mcp = {"content": [{"type": "text", "text": "{...}"}], "structuredContent": structured}
    assert compact_tool_result(None, {}, None, mcp) == structured  # type: ignore[arg-type]
    err = {"content": [{"type": "text", "text": "unknown act 'XY'"}], "isError": True}
    assert compact_tool_result(None, {}, None, err) == {"error": "unknown act 'XY'"}  # type: ignore[arg-type]
    assert compact_tool_result(None, {}, None, {"result": "x"}) is None  # type: ignore[arg-type]
