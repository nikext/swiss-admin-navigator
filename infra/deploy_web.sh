#!/usr/bin/env bash
# Build the web UI + BFF image and deploy it to Cloud Run (M6, docs/GCP.md §4,
# ADR-028). Billable and public (behind the access code): ask before running.
#
# Usage: bash infra/deploy_web.sh        (DRY_RUN=1 prints the commands only)
# Needs infra/web_setup.sh (Firestore database + access-code secret), the deployed
# agent (AGENT_RUNTIME_ID in .env) and a clean git tree (the image tag is the commit;
# ALLOW_DIRTY=1 overrides). Quotas: USER_DAILY_QUOTA, GLOBAL_DAILY_CAP.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT in .env}"
REGION="${GOOGLE_CLOUD_LOCATION:-europe-west6}"
RUNTIME_ID="${AGENT_RUNTIME_ID:?set AGENT_RUNTIME_ID in .env (make deploy-agent prints it)}"
GCLOUD="${GCLOUD:-$(command -v gcloud || echo "$HOME/google-cloud-sdk/bin/gcloud")}"
DRY_RUN="${DRY_RUN:-0}"
SERVICE="swiss-nav-web"
SA="swiss-nav-web@${PROJECT_ID}.iam.gserviceaccount.com"
REGISTRY="${REGION}-docker.pkg.dev"
# One answer costs ~CHF 0.03-0.04 (ADR-027): the global cap bounds the worst case at
# ~CHF 0.7/day whatever happens to the access code.
USER_QUOTA="${USER_DAILY_QUOTA:-10}"
GLOBAL_CAP="${GLOBAL_DAILY_CAP:-20}"

run() { echo "+ $*" >&2; if [[ "$DRY_RUN" != 1 ]]; then "$@"; fi; }

if [[ -n "$(git status --porcelain)" && "${ALLOW_DIRTY:-0}" != 1 ]]; then
  echo "git tree is dirty; commit first (the image tag is the commit) or ALLOW_DIRTY=1" >&2
  exit 1
fi
SHA="$(git rev-parse --short HEAD)"
IMAGE="${REGISTRY}/${PROJECT_ID}/swiss-nav/${SERVICE}:${SHA}"
MCP_URL="${WEB_MCP_URL:-$("$GCLOUD" run services describe swiss-nav-mcp --project "$PROJECT_ID" \
  --region "$REGION" --format='value(status.url)')/mcp}"
echo "== project=$PROJECT_ID region=$REGION image=$IMAGE dry_run=$DRY_RUN"
echo "   agent=$RUNTIME_ID mcp=$MCP_URL quota=$USER_QUOTA/user/day cap=$GLOBAL_CAP/day"

echo "== build"
run docker build -t "$IMAGE" web

echo "== push (short-lived token; no docker credential helper is installed)"
if [[ "$DRY_RUN" != 1 ]]; then
  "$GCLOUD" auth print-access-token |
    docker login -u oauth2accesstoken --password-stdin "https://${REGISTRY}" >/dev/null
fi
run docker push "$IMAGE"
if [[ "$DRY_RUN" != 1 ]]; then docker logout "https://${REGISTRY}" >/dev/null; fi

echo "== deploy"
# Public URL, but every API route needs the access-code cookie. Scale to zero, at most
# 2 instances. --timeout 300: an answer streams for up to ~3 min (p95 115-180 s, ADR-027).
# Concurrency 40: a request mostly waits on the agent's stream.
run "$GCLOUD" run deploy "$SERVICE" --project "$PROJECT_ID" --region "$REGION" \
  --image "$IMAGE" \
  --service-account "$SA" \
  --allow-unauthenticated \
  --min-instances 0 --max-instances 2 \
  --cpu 1 --memory 512Mi --concurrency 40 --timeout 300 --cpu-boost \
  --execution-environment gen2 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},AGENT_RUNTIME_ID=${RUNTIME_ID},AGENT_LOCATION=${REGION},SWISS_LAW_MCP_URL=${MCP_URL},USER_DAILY_QUOTA=${USER_QUOTA},GLOBAL_DAILY_CAP=${GLOBAL_CAP},FIRESTORE_DATABASE=swiss-nav" \
  --set-secrets "ACCESS_CODE=swiss-nav-access-code:latest" \
  --labels "app=swiss-nav,commit=${SHA}" \
  --quiet

if [[ "$DRY_RUN" != 1 ]]; then
  URL="$("$GCLOUD" run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" \
    --format='value(status.url)')"
  echo "== smoke: $URL/api/health"
  curl -fsS "$URL/api/health"
  echo
  echo "== unauthenticated API must be refused"
  code="$(curl -s -o /dev/null -w '%{http_code}' "$URL/api/quota")"
  [[ "$code" == 401 ]] || { echo "expected 401 from /api/quota, got $code" >&2; exit 1; }
  echo "   /api/quota -> 401"
  echo "Web UI: $URL"
fi
