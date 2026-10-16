"""Memory Bank admin (M7, docs/AGENTS.md §5, ADR-029).

    uv run python -m scripts.memory_bank show    [--runtime ID]
    uv run python -m scripts.memory_bank apply   [--runtime ID] --variant profile [--dry-run]
    uv run python -m scripts.memory_bank create-eval --variant profile   # prints the new id
    uv run python -m scripts.memory_bank list    [--runtime ID] --user USER [--app APP]
    uv run python -m scripts.memory_bank purge   [--runtime ID] --user USER [--app APP]

The Memory Bank config lives in the Agent Runtime instance's
`context_spec.memory_bank_config` and is built by
`agents.navigator.memory.memory_bank_config`. `apply` updates only that field
(update mask `context_spec`, no rebuild); agent deploys don't touch it.
`create-eval` makes a memory-only instance (no code, no compute) for the
memory eval, so experiments never write into the served bank.
The runtime defaults to `AGENT_RUNTIME_ID` (the served agent).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from dotenv import load_dotenv

from agents.navigator.config import load_profile
from agents.navigator.memory import VARIANTS, memory_bank_config

EVAL_DISPLAY_NAME = "swiss-nav-memory-eval"
LABELS = {"app": "swiss-nav"}


def client(project: str, location: str) -> Any:
    from agentplatform._genai.client import Client  # see evals/harness/remote_run.py

    return Client(project=project, location=location)


def resource(project: str, location: str, runtime: str) -> str:
    if runtime.startswith("projects/"):
        return runtime
    return f"projects/{project}/locations/{location}/reasoningEngines/{runtime}"


def model_path(project: str, model: str, location: str) -> str:
    return f"projects/{project}/locations/{location}/publishers/google/models/{model}"


def config_for(variant: str, project: str) -> dict[str, Any]:
    """The bank config for `variant`, with the profile's memory model if it names one."""
    memory = load_profile().memory
    return memory_bank_config(
        variant,  # type: ignore[arg-type]
        generation_model=model_path(project, memory.model, memory.location) if memory else None,
    )


def scope_filter(app: str, user: str) -> str:
    return f'scope.app_name="{app}" AND scope.user_id="{user}"'


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("command", choices=["show", "apply", "create-eval", "list", "purge"])
    p.add_argument("--runtime", default=os.environ.get("AGENT_RUNTIME_ID", ""))
    p.add_argument("--variant", choices=VARIANTS)
    p.add_argument("--user")
    p.add_argument("--app", default="navigator")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west6")

    if args.command in ("apply", "create-eval"):
        if not args.variant:
            p.error(f"{args.command} needs --variant")
        spec = {"memory_bank_config": config_for(args.variant, project)}
        if args.dry_run:
            print(json.dumps(spec, indent=1, ensure_ascii=False))
            return 0
        c = client(project, location)
        if args.command == "create-eval":
            runtime = c.runtimes.create(
                config={
                    "display_name": EVAL_DISPLAY_NAME,
                    "description": "Memory Bank for the swiss-nav memory eval (no agent code).",
                    "labels": LABELS | {"variant": args.variant},
                    "context_spec": spec,
                }
            )
            name = runtime.api_resource.name
            print(f"created {name}")
            print(f"Put this in .env:  MEMORY_EVAL_RUNTIME_ID={name.rsplit('/', 1)[1]}")
            return 0
        name = resource(project, location, args.runtime)
        c.runtimes.update(name=name, config={"context_spec": spec})
        print(f"applied variant {args.variant} to {name}")
        return 0

    if not args.runtime:
        p.error("no runtime: pass --runtime or set AGENT_RUNTIME_ID")
    c = client(project, location)
    name = resource(project, location, args.runtime)
    if args.command == "show":
        res = c.runtimes.get(name=name).api_resource
        spec = res.context_spec.model_dump(exclude_none=True) if res.context_spec else {}
        print(
            json.dumps(
                {"name": res.name, "display_name": res.display_name, "context_spec": spec},
                indent=1,
                ensure_ascii=False,
                default=str,
            )
        )
        return 0
    if not args.user:
        p.error(f"{args.command} needs --user")
    flt = scope_filter(args.app, args.user)
    if args.command == "list":
        for m in c.memory_banks.memories.list(name=name, config={"filter": flt}):
            print(json.dumps(m.model_dump(exclude_none=True, mode="json"), ensure_ascii=False))
        return 0
    op = c.memory_banks.memories.purge(name=name, filter=flt, force=True)
    print(f"purged: {op.response or op}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
