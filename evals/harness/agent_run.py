"""Run one eval case through navigator_v1 with the local ADK runner (M3 target).

Records what the metrics need: the final answer JSON, every tool call, the
verifier's `citation_check` rounds, per-model-call token usage and latency.
M5 adds a target for the deployed agent; this module is the local one.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.navigator.verifier import CHECK_TOOL
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
    usage: Usage = field(default_factory=Usage)
    latency_s: float = 0.0


async def run_case(runner: InMemoryRunner, case: Case, timeout_s: float = 300) -> Trace:
    trace = Trace(case.id)
    session = await runner.session_service.create_session(
        app_name=APP, user_id="eval", session_id=f"{case.id}-{uuid.uuid4().hex[:8]}"
    )
    message = types.Content(role="user", parts=[types.Part(text=case.question)])
    start = time.perf_counter()

    async def consume() -> None:
        async for event in runner.run_async(
            user_id="eval", session_id=session.id, new_message=message
        ):
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


async def run_cases(
    agent: LlmAgent, cases: list[Case], concurrency: int, on_done: Any = None
) -> list[Trace]:
    runner = InMemoryRunner(agent=agent, app_name=APP)
    sem = asyncio.Semaphore(concurrency)

    async def one(case: Case) -> Trace:
        async with sem:
            trace = await run_case(runner, case)
        if on_done:
            on_done(case, trace)
        return trace

    try:
        return list(await asyncio.gather(*(one(c) for c in cases)))
    finally:
        await runner.close()
