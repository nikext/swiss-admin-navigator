"""Ask the deployed navigator one question and stream what it does (M5, docs/GCP.md §4).

    uv run python -m scripts.query_remote "Wie hoch darf das Mietzinsdepot sein?"
    uv run python -m scripts.query_remote --traces "..."   # then look the run up in Cloud Trace

Prints every tool call as its event arrives, then the answer, its citations and
the verifier's verdict. `--traces` waits for the exporter and shows the spans
Cloud Trace recorded for the run: the M5 check that model and tool spans are
visible. Cloud Trace's `traces.list` doesn't return OTLP-ingested traces (it
found none of them on 2026-10-16, while `traces.get` returned all 19 spans), so
the trace ids come from the agent's OTel log records in Cloud Logging, which
carry them. The agent is `AGENT_RUNTIME_ID` (or `--runtime`). One answer
costs about CHF 0.04 in model calls.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

import google.auth
import google.auth.transport.requests
import httpx
from dotenv import load_dotenv

from agents.navigator.verifier import CHECK_TOOL
from evals.harness.agent_run import Trace, record
from evals.harness.cases import Case
from evals.harness.remote_run import RemoteAgent

TRACE_API = "https://cloudtrace.googleapis.com/v1/projects/{project}/traces/{trace_id}"
LOGS_API = "https://logging.googleapis.com/v2/entries:list"


def span_kind(name: str) -> str:
    """Group ADK's OpenTelemetry span names ("execute_tool get_article", "call_llm", …)."""
    return name.split(" ", 1)[0]


def _headers(project: str) -> dict[str, str]:
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return {"Authorization": f"Bearer {creds.token}", "x-goog-user-project": project}


def trace_ids(project: str, runtime_id: str, start: datetime) -> list[str]:
    """Trace ids of the agent's log entries since `start` (newest first)."""
    since = start.isoformat().replace("+00:00", "Z")
    body = {
        "resourceNames": [f"projects/{project}"],
        "filter": (
            'resource.type="aiplatform.googleapis.com/ReasoningEngine" '
            f'resource.labels.reasoning_engine_id="{runtime_id}" '
            f'timestamp>="{since}" trace:*'
        ),
        "orderBy": "timestamp desc",
        "pageSize": 200,
    }
    resp = httpx.post(LOGS_API, json=body, headers=_headers(project), timeout=30)
    resp.raise_for_status()
    ids = [e["trace"].rsplit("/", 1)[-1] for e in resp.json().get("entries", [])]
    return list(dict.fromkeys(ids))


def get_spans(project: str, trace_id: str) -> list[dict[str, Any]]:
    url = TRACE_API.format(project=project, trace_id=trace_id)
    resp = httpx.get(url, headers=_headers(project), timeout=30)
    if resp.status_code == 404:  # not exported (yet)
        return []
    resp.raise_for_status()
    return resp.json().get("spans", [])


async def ask(agent: RemoteAgent, question: str) -> Trace:
    trace = Trace("query")
    start = time.perf_counter()
    first: float | None = None
    # Targets only read the question; the other fields are placeholders.
    case = Case(id="query", lang="en", question=question, category="answerable", domain="-")
    async for event in agent.events(case):
        first = first or time.perf_counter() - start
        before = len(trace.tool_calls), trace.check_rounds
        record(trace, event)
        for call in trace.tool_calls[before[0] :]:
            args = json.dumps(call["args"], ensure_ascii=False)
            print(f"  [{time.perf_counter() - start:5.1f}s] {call['name']} {args[:120]}")
        if trace.check_rounds > before[1]:
            print(f"  [{time.perf_counter() - start:5.1f}s] {CHECK_TOOL} (verifier sent it back)")
    trace.latency_s = time.perf_counter() - start
    print(f"first event after {first or 0:.1f} s, done after {trace.latency_s:.1f} s")
    if trace.raw_final:
        trace.answer = json.loads(trace.raw_final)
    return trace


def show(answer: dict[str, Any]) -> None:
    print()
    print(answer.get("answer_markdown", ""))
    for c in answer.get("citations", []):
        pin = "".join(f" {k} {c[k]}" for k in ("paragraph", "letter") if c.get(k))
        print(f"  [{c.get('ref')}] {c.get('abbr')} {c.get('article')}{pin}  {c.get('url')}")
    v = answer.get("verification", {})
    print(f"verification: {v.get('status')}, dropped {v.get('dropped')}, ", end="")
    print(f"repairs {v.get('repairs')}")
    print(answer.get("notice", ""))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("question")
    ap.add_argument("--runtime", default=None, help="Agent Runtime id (default AGENT_RUNTIME_ID)")
    ap.add_argument("--json", action="store_true", help="print the raw answer JSON")
    ap.add_argument("--traces", action="store_true", help="then list the run's Cloud Trace spans")
    ap.add_argument("--trace-wait", type=float, default=45, help="seconds to wait for the export")
    args = ap.parse_args(argv)
    load_dotenv(".env")
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or "europe-west6"
    agent = RemoteAgent(args.runtime or os.environ.get("AGENT_RUNTIME_ID", ""), project, location)
    deployed = agent.describe()
    print(f"{deployed['name']} (commit {deployed['labels'].get('commit', '?')})")

    started = datetime.now(UTC)
    trace = asyncio.run(ask(agent, args.question))
    if trace.answer is None:
        print("no final answer", file=sys.stderr)
        return 1
    print(json.dumps(trace.answer, ensure_ascii=False, indent=1) if args.json else "", end="")
    show(trace.answer)

    if args.traces:
        print(f"\nwaiting {args.trace_wait:.0f} s for the trace export ...", flush=True)
        time.sleep(args.trace_wait)
        runtime_id = agent.name.rsplit("/", 1)[-1]
        ids = trace_ids(project, runtime_id, started - timedelta(seconds=5))
        found = 0
        for tid in ids:
            spans = get_spans(project, tid)
            if not any(s["name"].startswith("invoke_agent") for s in spans):
                continue  # session calls etc.; the agent run is the trace with invoke_agent
            found += 1
            kinds = Counter(span_kind(s["name"]) for s in spans)
            tools = Counter(
                s["name"].split(" ", 1)[1] for s in spans if s["name"].startswith("execute_tool ")
            )
            print(f"trace {tid}: {len(spans)} spans {dict(kinds)}")
            print(f"  tool spans: {dict(tools)}")
            print(
                f"  https://console.cloud.google.com/traces/explorer;traceId={tid}?project={project}"
            )
        if not found:
            print(
                f"no agent trace found ({len(ids)} trace ids in the logs; exporter, IAM or delay?)"
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
