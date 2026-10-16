"""Trace recording: the v2 router's events and the verifier's round snapshots."""

from types import SimpleNamespace
from typing import Any

from google.adk.events import Event
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from agents.navigator.contract import Round
from evals.harness.agent_run import RoundRecorder, Trace, record


def event(author: str, text: str, prompt: int = 10) -> Event:
    return Event(
        author=author,
        content=types.Content(role="model", parts=[types.Part(text=text)]),
        usage_metadata=types.GenerateContentResponseUsageMetadata(prompt_token_count=prompt),
    )


def test_router_event_is_a_route_not_an_answer() -> None:
    trace = Trace("c1")
    record(trace, event("router", '{"language": "de", "domains": ["work"]}', prompt=7))
    assert trace.route == {"language": "de", "domains": ["work"]}
    assert trace.raw_final is None
    assert (trace.router_usage.model_calls, trace.router_usage.prompt) == (1, 7)
    assert trace.usage.model_calls == 0
    record(trace, event("work_specialist", '{"answer_markdown": "x"}'))
    assert trace.raw_final == '{"answer_markdown": "x"}'
    assert trace.usage.model_calls == 1


def test_round_recorder_snapshots_usage_including_the_current_call() -> None:
    recorder = RoundRecorder()
    trace = Trace("c1")
    trace.usage.add_counts(prompt=100)
    trace.tool_calls.append({"name": "get_article", "args": {}})
    recorder.traces["s1"] = trace
    ctx: Any = SimpleNamespace(session=SimpleNamespace(id="s1"))
    response = LlmResponse(
        usage_metadata=types.GenerateContentResponseUsageMetadata(prompt_token_count=50)
    )
    recorder(ctx, '{"a": 1}', Round(citations=1, quotes=1, problems=[]), response)
    (entry,) = trace.rounds_log
    assert entry["draft"] == '{"a": 1}'
    assert entry["usage"]["model_calls"] == 2
    assert entry["usage"]["prompt"] == 150
    assert entry["tool_calls"] == 1
    assert entry["t_s"] >= 0
    assert trace.usage.prompt == 100  # the trace itself is not changed
    recorder(SimpleNamespace(session=SimpleNamespace(id="other")), "{}", Round(  # type: ignore[arg-type]
        citations=0, quotes=0, problems=[]), response)  # fmt: skip
    assert len(trace.rounds_log) == 1
