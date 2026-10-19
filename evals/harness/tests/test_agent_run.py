"""Trace recording: the v2 router's events and the verifier's round snapshots."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from google.adk.events import Event
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from agents.navigator.contract import Round
from evals.harness.agent_run import RoundRecorder, Trace, TraceLog, record


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


def test_trace_log_resumes_finished_traces(tmp_path: Path) -> None:
    path = tmp_path / "t.jsonl"
    header = {"agent": "v1", "claim_check": True}
    log = TraceLog(path, header)
    trace = Trace("c1", answer={"answer_markdown": "x"}, latency_s=3.5)
    trace.usage.add_counts(prompt=100, output=7)
    trace.rounds_log.append({"round": {"status": "passed"}})
    log.append(trace)
    log.append(Trace("c2", error="timeout after 600 s"))
    with path.open("a", encoding="utf-8") as f:
        f.write('{"case_id": "c3", "ans')  # cut off when the process died

    again = TraceLog(path, header)
    assert set(again.done) == {"c1", "c2"}
    c1 = again.done["c1"]
    assert c1.answer == {"answer_markdown": "x"}
    assert c1.latency_s == 3.5
    assert (c1.usage.prompt, c1.usage.output, c1.usage.model_calls) == (100, 7, 1)
    assert c1.rounds_log == [{"round": {"status": "passed"}}]
    assert again.done["c2"].error == "timeout after 600 s"


def test_trace_log_refuses_another_setup(tmp_path: Path) -> None:
    path = tmp_path / "t.jsonl"
    TraceLog(path, {"agent": "v1"})
    with pytest.raises(ValueError, match="another run setup"):
        TraceLog(path, {"agent": "v2"})
