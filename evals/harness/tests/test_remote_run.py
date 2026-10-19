"""The remote eval target: resource names, stream items, and one real streamed run.

`fixtures/remote_stream.jsonl` is what `async_stream_query` streamed for "Wie
lange ist die Probezeit im Arbeitsvertrag?" from the Agent Runtime image run
locally (2026-10-16), with thought signatures and tool results elided.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from google.adk.events import Event

from evals.harness.agent_run import Trace, record, run_case, run_cases
from evals.harness.cases import Case
from evals.harness.remote_run import resource_name, to_event

STREAM = Path(__file__).parent / "fixtures" / "remote_stream.jsonl"


def stream_items() -> list[dict]:
    return [json.loads(line) for line in STREAM.read_text(encoding="utf-8").splitlines()]


def case(question: str = "q") -> Case:
    return Case(id="c1", lang="de", question=question, category="answerable", domain="work")


class Replay:
    """A target that yields stored events (optionally failing midway)."""

    def __init__(self, items: list[dict], fail_after: int | None = None) -> None:
        self.items, self.fail_after, self.closed = items, fail_after, False

    async def events(self, case: Case, trace: object = None) -> AsyncIterator[Event]:
        for i, item in enumerate(self.items):
            if i == self.fail_after:
                raise RuntimeError("stream broke")
            yield to_event(item)

    async def close(self) -> None:
        self.closed = True


def test_resource_name() -> None:
    full = "projects/p/locations/europe-west6/reasoningEngines/123"
    assert resource_name("123", "p", "europe-west6") == full
    assert resource_name(f" {full} ", "x", "y") == full
    with pytest.raises(ValueError, match="AGENT_RUNTIME_ID"):
        resource_name("", "p", "europe-west6")
    with pytest.raises(ValueError, match="resource id"):
        resource_name("reasoningEngines/123", "p", "europe-west6")


def test_to_event_rejects_errors() -> None:
    with pytest.raises(RuntimeError, match="agent error"):
        to_event({"error": "500 boom"})
    with pytest.raises(RuntimeError, match="agent error"):
        to_event({"code": 429, "message": "Resource exhausted"})
    with pytest.raises(RuntimeError, match="unexpected"):
        to_event("not a dict")
    assert to_event(stream_items()[0]).author == "navigator"


def test_streamed_run_is_scored_like_a_local_one() -> None:
    trace = Trace("c1")
    for item in stream_items():
        record(trace, to_event(item))
    assert [c["name"] for c in trace.tool_calls] == ["search_law", "get_article", "get_article"]
    assert trace.tool_calls[1]["args"]["article"] == "335b"
    assert trace.check_rounds == 0
    assert trace.usage.model_calls == 4
    assert trace.usage.prompt == 3419 + 5217 + 5843 + 6674
    assert trace.usage.cached == 3405 + 3401
    assert trace.usage.thoughts == 53 + 19 + 86 + 2097
    answer = json.loads(trace.raw_final or "")
    assert answer["verification"]["status"] == "passed"
    assert {c["article"] for c in answer["citations"]} == {"Art. 335b", "Art. 344a"}


def test_run_case_over_a_target() -> None:
    trace = asyncio.run(run_case(Replay(stream_items()), case()))
    assert trace.error is None
    assert trace.answer is not None
    assert trace.answer["language"] == "de"

    broken = asyncio.run(run_case(Replay(stream_items(), fail_after=2), case()))
    assert broken.answer is None
    assert broken.error == "RuntimeError: stream broke"
    assert len(broken.tool_calls) == 1  # what arrived before the break is kept

    no_final = asyncio.run(run_case(Replay(stream_items()[:-1]), case()))
    assert no_final.error == "no final answer"


def test_run_cases_closes_the_target() -> None:
    target = Replay(stream_items())
    done: list[str] = []
    traces = asyncio.run(
        run_cases(target, [case(), case()], concurrency=2, on_done=lambda c, t: done.append(c.id))
    )
    assert len(traces) == 2
    assert all(t.answer for t in traces)
    assert done == ["c1", "c1"]
    assert target.closed
