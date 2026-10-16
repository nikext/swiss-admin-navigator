"""The deployed navigator on Agent Runtime as an eval target (M5, docs/GCP.md §4).

`adk deploy agent_engine` serves ADK's `AdkApp` methods. Each case gets a fresh
Agent Platform session (`async_create_session`), streams `async_stream_query`
and deletes the session afterwards. The stream is one ADK `Event` per item, as a
dict in snake_case (verified against the deploy image locally, 2026-10-16), so
`Event.model_validate` gives back the same events the local runner yields and
`agent_run.record` scores both targets the same way.

The resource is `AGENT_RUNTIME_ID` (an id, or a full `projects/…` name); the
project and region come from `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import TYPE_CHECKING, Any

from google.adk.events import Event

from evals.harness.cases import Case

if TYPE_CHECKING:
    from evals.harness.agent_run import Trace

USER = "eval"


def resource_name(runtime: str, project: str, location: str) -> str:
    """`123` → `projects/<project>/locations/<location>/reasoningEngines/123`."""
    runtime = runtime.strip()
    if not runtime:
        raise ValueError("no Agent Runtime id: set AGENT_RUNTIME_ID (make deploy-agent prints it)")
    if runtime.startswith("projects/"):
        return runtime
    if "/" in runtime:
        raise ValueError(f"expected a resource id or projects/… name, got {runtime!r}")
    return f"projects/{project}/locations/{location}/reasoningEngines/{runtime}"


def to_event(item: Any) -> Event:
    """One streamed item → an ADK event; an error payload raises instead."""
    if not isinstance(item, Mapping):
        raise RuntimeError(f"unexpected stream item: {str(item)[:300]}")
    if "error" in item or ("code" in item and "message" in item and "author" not in item):
        raise RuntimeError(f"agent error: {str(item.get('error', item))[:300]}")
    return Event.model_validate(item)


class RemoteAgent:
    """Runs cases against a deployed Agent Runtime resource."""

    def __init__(self, runtime: str, project: str, location: str) -> None:
        # Only the remote target needs the Agent Platform SDK. `agentplatform.Client` is a
        # lazy export that type checkers can't follow, hence the private module.
        from agentplatform._genai.client import Client

        self.name = resource_name(runtime, project, location)
        self.client = Client(project=project, location=location)
        # Methods like async_stream_query are registered on the object at runtime.
        self.runtime: Any = self.client.runtimes.get(name=self.name)

    def describe(self) -> dict[str, Any]:
        """What was deployed, for the report: labels (commit) and the env it runs with."""
        res = self.runtime.api_resource
        spec = getattr(res, "spec", None)
        deployment = getattr(spec, "deployment_spec", None)
        env = {e.name: e.value for e in (getattr(deployment, "env", None) or [])}
        return {
            "name": self.name,
            "display_name": res.display_name,
            "update_time": str(res.update_time) if res.update_time else None,
            "labels": dict(res.labels or {}),
            "service_account": getattr(spec, "service_account", None),
            "scaling": {k: getattr(deployment, k, None) for k in SCALING},
            "env": {k: env[k] for k in sorted(env) if k in DESCRIBED_ENV},
        }

    async def events(self, case: Case, trace: Trace | None = None) -> AsyncIterator[Event]:
        session = await self.runtime.async_create_session(user_id=USER)
        try:
            async for item in self.runtime.async_stream_query(
                user_id=USER, session_id=session["id"], message=case.question
            ):
                yield to_event(item)
        finally:
            await self.runtime.async_delete_session(user_id=USER, session_id=session["id"])

    async def close(self) -> None:
        return None


SCALING = ("min_instances", "max_instances", "resource_limits", "container_concurrency")
# Deployment env worth recording (no secrets are set on the agent; ADR-027).
DESCRIBED_ENV = {"NAV_PROFILE", "SWISS_LAW_MCP_URL", "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"}
