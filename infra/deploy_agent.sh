#!/usr/bin/env bash
# Deploy navigator_v1 to Agent Runtime in europe-west6 (docs/GCP.md §4, ADR-027).
# Billable: ask before running. Updates AGENT_RUNTIME_ID in place when it is set in .env,
# otherwise creates a new instance and prints its id.
#
# Usage: bash infra/deploy_agent.sh      (DRY_RUN=1: stage + import check, print the deploy)
#
# `adk deploy agent_engine` uploads one folder and builds ADK's own Dockerfile
# (python:3.11-slim, `adk api_server --a2a`, Sessions at agentengine://<itself>).
# So this script stages that folder from the commit (tracked files only, no tests), with
#  - requirements.txt: the navigator's pins from uv.lock (ADR-011),
#  - .env: the agent's runtime config (Cloud Run MCP URL, profile); nothing secret,
# checks that the staged agent imports under Python 3.11 with exactly those pins, and
# deploys with infra/agent_runtime.json (scale to zero, 1 vCPU / 2 GiB: the SDK default of
# one always-on 4 vCPU / 4 GiB instance would cost ~USD 270/month), the swiss-nav-agent@
# identity and OpenTelemetry export to Cloud Trace.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT in .env}"
REGION="${GOOGLE_CLOUD_LOCATION:-europe-west6}"
GCLOUD="${GCLOUD:-$(command -v gcloud || echo "$HOME/google-cloud-sdk/bin/gcloud")}"
UV="${UV:-$(command -v uv || echo "$HOME/.local/bin/uv")}"
DRY_RUN="${DRY_RUN:-0}"
SA="swiss-nav-agent@${PROJECT_ID}.iam.gserviceaccount.com"
RUNTIME_ID="${AGENT_RUNTIME_ID:-}"
PROFILE="${NAV_PROFILE:-default}"

if [[ -n "$(git status --porcelain)" && "${ALLOW_DIRTY:-0}" != 1 ]]; then
  echo "git tree is dirty; commit first (the deploy is labelled with the commit) or ALLOW_DIRTY=1" >&2
  exit 1
fi
SHA="$(git rev-parse --short HEAD)"

# The deployed agent talks to the Cloud Run MCP server, never to a local one.
MCP_URL="${AGENT_MCP_URL:-}"
if [[ -z "$MCP_URL" ]]; then
  MCP_URL="$("$GCLOUD" run services describe swiss-nav-mcp --project "$PROJECT_ID" \
    --region "$REGION" --format='value(status.url)')/mcp"
fi
[[ "$MCP_URL" == https://* ]] || { echo "MCP URL must be https, got $MCP_URL" >&2; exit 1; }
echo "== project=$PROJECT_ID region=$REGION commit=$SHA runtime=${RUNTIME_ID:-<new>} dry_run=$DRY_RUN"
echo "   mcp=$MCP_URL profile=$PROFILE sa=$SA"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
AGENT="$STAGE/navigator"

echo "== stage agents/navigator at $SHA"
git ls-files -z agents/navigator | while IFS= read -r -d '' f; do
  [[ "$f" == agents/navigator/tests/* ]] && continue
  dest="$AGENT/${f#agents/navigator/}"
  mkdir -p "$(dirname "$dest")"
  git show "HEAD:$f" >"$dest"
done
"$UV" export --package swiss-nav-navigator --no-dev --no-hashes --no-emit-project \
  --no-emit-workspace --frozen --quiet -o "$AGENT/requirements.txt"
cat >"$AGENT/.env" <<EOF
# Written by infra/deploy_agent.sh at $SHA. Becomes the Agent Runtime env (no secrets).
SWISS_LAW_MCP_URL=$MCP_URL
NAV_PROFILE=$PROFILE
GOOGLE_GENAI_USE_ENTERPRISE=TRUE
EOF
python3 -I - "infra/agent_runtime.json" "$STAGE/agent_runtime.json" "$SHA" <<'EOF'
import json, sys
src, dst, sha = sys.argv[1:]
config = json.load(open(src, encoding="utf-8"))
config["labels"] = config.get("labels", {}) | {"commit": sha}
json.dump(config, open(dst, "w", encoding="utf-8"), indent=1)
EOF
echo "   $(grep -c '==' "$AGENT/requirements.txt") pinned requirements, $(find "$AGENT" -type f | wc -l) files"

if [[ "${SKIP_IMPORT_CHECK:-0}" != 1 ]]; then
  echo "== import check: Python 3.11 (the deploy image's base) with exactly the staged pins"
  (cd "$STAGE" && env -i HOME="$HOME" PATH="$PATH" SWISS_LAW_MCP_URL="$MCP_URL" \
    "$UV" run --quiet --isolated --no-project --python 3.11 \
    --with-requirements navigator/requirements.txt \
    python -c 'import sys, navigator.agent as a; print("  ", sys.version.split()[0], a.root_agent.name, a.profile.agent)')
fi

DEPLOY=("$UV" run adk deploy agent_engine
  --project "$PROJECT_ID" --region "$REGION"
  --service_account "$SA"
  --otel_to_cloud
  --agent_engine_config_file "$STAGE/agent_runtime.json")
if [[ -n "$RUNTIME_ID" ]]; then DEPLOY+=(--agent_engine_id "$RUNTIME_ID"); fi
DEPLOY+=("$AGENT")

echo "== deploy"
echo "+ ${DEPLOY[*]}" >&2
if [[ "$DRY_RUN" == 1 ]]; then exit 0; fi
"${DEPLOY[@]}" 2>&1 | tee "$STAGE/deploy.log"

NAME="$(grep -oE 'projects/[^ ]+/reasoningEngines/[0-9]+' "$STAGE/deploy.log" | tail -1 || true)"
[[ -n "$NAME" ]] || { echo "deploy output has no reasoningEngines resource; see above" >&2; exit 1; }
NEW_ID="${NAME##*/}"
echo
echo "Agent Runtime: $NAME"
if [[ "$NEW_ID" != "$RUNTIME_ID" ]]; then
  echo "New instance. Put this in .env:  AGENT_RUNTIME_ID=$NEW_ID"
fi
echo "Smoke:  uv run python -m scripts.query_remote --runtime $NEW_ID --traces \"Wie hoch darf das Mietzinsdepot sein?\""
