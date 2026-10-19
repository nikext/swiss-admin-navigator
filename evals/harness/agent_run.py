"""Run eval cases through the navigator and record what the metrics need.

Two targets yield the same ADK events: `LocalAgent` (an in-memory ADK runner,
M3; navigator_v1 or the navigator_v2 workflow, M8) and `RemoteAgent` (the
deployed agent on Agent Runtime, M5, in `remote_run.py`). Either way the trace
holds the final answer JSON, every tool call, the verifier's `citation_check`
rounds, per-model-call token usage and latency; for v2 also the router's route
and its token usage. Locally, a `RoundRecorder` (the verifier's observer)
adds every checked draft with the usage and time at that point, so policies
that stop earlier can be scored from the same run (`derive.py`, ADR-034).
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Protocol

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.adk.workflow import Workflow
from google.genai import types

from agents.navigator.contract import Round
from agents.navigator.verifier import CHECK_TOOL
from agents.navigator_v2.agent import ROUTER
from evals.harness.cases import Case

APP = "navigator-eval"


@dataclass
class Usage:
    model_calls: int = 0
    prompt: int = 0
    cached: int = 0
    output: int = 0  # candidates
    thoughts: int = 0

    def add(self, meta: types.GenerateContentResponseUsageMetadata) -> None:
        self.add_counts(
            prompt=meta.prompt_token_count or 0,
            cached=meta.cached_content_token_count or 0,
            output=meta.candidates_token_count or 0,
            thoughts=meta.thoughts_token_count or 0,
        )

    def add_counts(self, prompt: int, cached: int = 0, output: int = 0, thoughts: int = 0) -> None:
        self.model_calls += 1
        self.prompt += prompt
        self.cached += cached
        self.output += output
        self.thoughts += thoughts


@dataclass
class Trace:
    case_id: str
    answer: dict[str, Any] | None = None
    raw_final: str | None = None
    error: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    check_rounds: int = 0  # citation_check rejections
    usage: Usage = field(default_factory=Usage)  # the answering agent's model calls
    latency_s: float = 0.0
    route: dict[str, Any] | None = None  # navigator_v2's router output
    router_usage: Usage = field(default_factory=Usage)
    rounds_log: list[dict[str, Any]] = field(default_factory=list)  # RoundRecorder
    started: float = field(default_factory=time.perf_counter)


class Target(Protocol):
    """Where cases run: yields the agent's events for one question."""

    def events(self, case: Case, trace: Trace | None = None) -> AsyncIterator[Event]: ...

    async def close(self) -> None: ...


class RoundRecorder:
    """The verifier's observer: logs each checked draft into its case's trace, with the
    answering agent's usage and the elapsed time at that point (ADR-034)."""

    def __init__(self) -> None:
        self.traces: dict[str, Trace] = {}  # session id -> trace

    def __call__(
        self, ctx: CallbackContext, text: str, current: Round, response: LlmResponse
    ) -> None:
        trace = self.traces.get(ctx.session.id)
        if trace is None:
            return
        usage = replace(trace.usage)
        if response.usage_metadata:  # this call's event has not reached `record` yet
            usage.add(response.usage_metadata)
        trace.rounds_log.append(
            {
                "draft": text,
                "round": current.model_dump(),
                "t_s": round(time.perf_counter() - trace.started, 3),
                "usage": asdict(usage),
                "tool_calls": len(trace.tool_calls),
            }
        )


class LocalAgent:
    """The agent in this process (an LlmAgent or the v2 workflow), via ADK's in-memory runner."""

    def __init__(self, agent: LlmAgent | Workflow, recorder: RoundRecorder | None = None) -> None:
        if isinstance(agent, Workflow):
            self.runner = InMemoryRunner(node=agent, app_name=APP)
        else:
            self.runner = InMemoryRunner(agent=agent, app_name=APP)
        self.recorder = recorder

    async def events(self, case: Case, trace: Trace | None = None) -> AsyncIterator[Event]:
        session = await self.runner.session_service.create_session(
            app_name=APP, user_id="eval", session_id=f"{case.id}-{uuid.uuid4().hex[:8]}"
        )
        if self.recorder is not None and trace is not None:
            self.recorder.traces[session.id] = trace
        message = types.Content(role="user", parts=[types.Part(text=case.question)])
        async for event in self.runner.run_async(
            user_id="eval", session_id=session.id, new_message=message
        ):
            yield event

    async def close(self) -> None:
        await self.runner.close()


def record(trace: Trace, event: Event) -> None:
    """Add one event's usage, tool calls and final text to the trace."""
    if event.author == ROUTER:  # navigator_v2's router: its route, not an answer
        if event.usage_metadata:
            trace.router_usage.add(event.usage_metadata)
        parts = (event.content.parts if event.content else None) or []
        text = "".join(p.text for p in parts if p.text and not p.thought)
        if event.is_final_response() and text.strip():
            try:
                trace.route = json.loads(text)
            except json.JSONDecodeError:
                trace.route = {"raw": text[:500]}
        return
    if event.usage_metadata:
        trace.usage.add(event.usage_metadata)
    for call in event.get_function_calls():
        if call.name == CHECK_TOOL:
            trace.check_rounds += 1
        else:
            trace.tool_calls.append({"name": call.name, "args": call.args})
    if event.is_final_response() and event.content and event.content.parts:
        text = "".join(p.text for p in event.content.parts if p.text and not p.thought)
        if text.strip():
            trace.raw_final = text


async def run_case(target: Target, case: Case, timeout_s: float = 300) -> Trace:
    trace = Trace(case.id)
    start = trace.started

    async def consume() -> None:
        async for event in target.events(case, trace):
            record(trace, event)

    try:
        await asyncio.wait_for(consume(), timeout_s)
    except TimeoutError:
        trace.error = f"timeout after {timeout_s:.0f} s"
    except Exception as exc:  # one failing case must not end the run
        trace.error = f"{type(exc).__name__}: {exc}"[:500]
    trace.latency_s = time.perf_counter() - start
    if trace.raw_final and not trace.error:
        try:
            trace.answer = json.loads(trace.raw_final)
        except json.JSONDecodeError as exc:
            trace.error = f"final answer is not JSON: {exc}"
    elif not trace.error:
        trace.error = "no final answer"
    return trace


def trace_from_dict(d: dict[str, Any]) -> Trace:
    d = dict(d)
    d["usage"] = Usage(**d["usage"])
    d["router_usage"] = Usage(**d["router_usage"])
    return Trace(**d)


class TraceLog:
    """Finished traces as JSONL after a header line, so an interrupted run resumes with
    the cases it has not finished (`answer_eval --traces`). A stored trace is reused as
    is, errors included, so a resumed run scores like an uninterrupted one."""

    def __init__(self, path: Path, header: dict[str, Any]) -> None:
        self.path = path
        self.done: dict[str, Trace] = {}
        if path.exists() and path.stat().st_size:
            first, *rest = path.read_text(encoding="utf-8").splitlines()
            stored = json.loads(first)
            if stored != header:
                raise ValueError(f"{path} was written by another run setup: {stored} != {header}")
            for line in rest:
                try:
                    trace = trace_from_dict(json.loads(line))
                except (json.JSONDecodeError, TypeError, KeyError):
                    continue  # a line cut off when the process died
                self.done[trace.case_id] = trace
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(header) + "\n", encoding="utf-8")

    def append(self, trace: Trace) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(trace), ensure_ascii=False, default=str) + "\n")


async def run_cases(
    target: Target,
    cases: list[Case],
    concurrency: int,
    on_done: Any = None,
    timeout_s: float = 300,
) -> list[Trace]:
    sem = asyncio.Semaphore(concurrency)

    async def one(case: Case) -> Trace:
        async with sem:
            trace = await run_case(target, case, timeout_s)
        if on_done:
            on_done(case, trace)
        return trace

    try:
        return list(await asyncio.gather(*(one(c) for c in cases)))
    finally:
        await target.close()
