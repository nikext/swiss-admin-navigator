"""Smoke-test the active model profile against Vertex AI with ADC (M0 "Done when").

Makes one tiny generate call per chat model and one embedding call, all in the
profile's region, and prints the resolved IDs, latency and token counts. Costs a
fraction of a cent.

Usage: uv run python -m scripts.smoke_gemini   (or `make smoke-gemini`)
"""

from __future__ import annotations

import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from agents.navigator.config import load_profile


def main() -> int:
    load_dotenv()
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        print("GOOGLE_CLOUD_PROJECT is not set (copy .env.example to .env).", file=sys.stderr)
        return 2
    profile = load_profile()
    print(f"project={project} profile={profile.as_dict()}")
    client = genai.Client(vertexai=True, project=project, location=profile.location)

    failures = 0
    for role, model in [("agent", profile.agent_model), ("judge", profile.judge_model)]:
        start = time.perf_counter()
        try:
            resp = client.models.generate_content(
                model=model,
                contents="Reply with the single word: OK",
                config=types.GenerateContentConfig(max_output_tokens=256),
            )
        except Exception as exc:  # report every model, then fail
            failures += 1
            print(f"FAIL {role:9} {model}: {exc}")
            continue
        usage = resp.usage_metadata
        tokens = (usage.prompt_token_count, usage.total_token_count) if usage else None
        print(
            f"ok   {role:9} {model} ({resp.model_version}) {time.perf_counter() - start:.2f}s "
            f"tokens(prompt,total)={tokens} text={(resp.text or '').strip()[:40]!r}"
        )

    start = time.perf_counter()
    try:
        emb = client.models.embed_content(
            model=profile.embedding_model, contents="Kündigungsschutz im Mietrecht"
        )
        dim = len(emb.embeddings[0].values or []) if emb.embeddings else 0
        print(
            f"ok   embedding {profile.embedding_model} {time.perf_counter() - start:.2f}s dim={dim}"
        )
    except Exception as exc:
        failures += 1
        print(f"FAIL embedding {profile.embedding_model}: {exc}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
