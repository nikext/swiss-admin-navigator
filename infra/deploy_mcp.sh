#!/usr/bin/env bash
# Build the swiss-law MCP image (index baked in) and deploy it to Cloud Run
# (docs/GCP.md §4, ADR-003, ADR-017). Billable and public: ask before running.
#
# Usage: bash infra/deploy_mcp.sh        (DRY_RUN=1 prints the commands only)
# Needs data/index.sqlite (make index) and a clean git tree (the image tag is
# the commit; ALLOW_DIRTY=1 overrides). Reads GOOGLE_CLOUD_PROJECT from .env.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT in .env}"
REGION="${GOOGLE_CLOUD_LOCATION:-europe-west6}"
GCLOUD="${GCLOUD:-$(command -v gcloud || echo "$HOME/google-cloud-sdk/bin/gcloud")}"
DRY_RUN="${DRY_RUN:-0}"
SERVICE="swiss-nav-mcp"
SA="swiss-nav-mcp@${PROJECT_ID}.iam.gserviceaccount.com"
REGISTRY="${REGION}-docker.pkg.dev"
INDEX="data/index.sqlite"

run() { echo "+ $*" >&2; if [[ "$DRY_RUN" != 1 ]]; then "$@"; fi; }

[[ -f "$INDEX" ]] || { echo "no $INDEX: run make index" >&2; exit 1; }
if [[ -n "$(git status --porcelain)" && "${ALLOW_DIRTY:-0}" != 1 ]]; then
  echo "git tree is dirty; commit first (the image tag is the commit) or ALLOW_DIRTY=1" >&2
  exit 1
fi
SHA="$(git rev-parse --short HEAD)"
INDEX_SHA="$(python3 -I -c 'import json, sqlite3, sys
db = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
print(json.loads(db.execute("SELECT value FROM meta WHERE key = ?", ("git_sha",)).fetchone()[0]))' "$INDEX")"
if [[ "$INDEX_SHA" != "$SHA" ]]; then
  echo "note: $INDEX was built at $INDEX_SHA, HEAD is $SHA (fine if ingest/ is unchanged)" >&2
fi
IMAGE="${REGISTRY}/${PROJECT_ID}/swiss-nav/${SERVICE}:${SHA}"
echo "== project=$PROJECT_ID region=$REGION image=$IMAGE dry_run=$DRY_RUN"

echo "== build"
run docker build -f mcp_server/Dockerfile -t "$IMAGE" .

echo "== push (short-lived token; no docker credential helper is installed)"
if [[ "$DRY_RUN" != 1 ]]; then
  "$GCLOUD" auth print-access-token |
    docker login -u oauth2accesstoken --password-stdin "https://${REGISTRY}" >/dev/null
fi
run docker push "$IMAGE"
if [[ "$DRY_RUN" != 1 ]]; then docker logout "https://${REGISTRY}" >/dev/null; fi

echo "== deploy"
# Public and read-only by design (ADR-003). Scale to zero; at most 2 instances
# bound the embedding spend; in-app, search_law is rate-limited per client and
# paid query embeddings have a budget per instance (ADR-033).
# gen2: instance start 4.5 s vs 6.0 s on gen1, whose gVisor sandbox makes the
# ~2,000 small .pyc imports and the 135 MB index read slow (ADR-017).
run "$GCLOUD" run deploy "$SERVICE" --project "$PROJECT_ID" --region "$REGION" \
  --image "$IMAGE" \
  --service-account "$SA" \
  --allow-unauthenticated \
  --min-instances 0 --max-instances 2 \
  --cpu 1 --memory 1Gi --concurrency 40 --timeout 60 --cpu-boost \
  --execution-environment gen2 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --labels "app=swiss-nav,commit=${SHA}" \
  --quiet

if [[ "$DRY_RUN" != 1 ]]; then
  URL="$("$GCLOUD" run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" \
    --format='value(status.url)')"
  echo "== smoke: $URL/health"
  curl -fsS "$URL/health"
  echo
  echo "MCP endpoint: $URL/mcp"
  echo "Claude Code:  claude mcp add --transport http swiss-law $URL/mcp"
fi
