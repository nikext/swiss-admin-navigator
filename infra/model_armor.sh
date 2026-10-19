#!/usr/bin/env bash
# Model Armor for the navigator (M10, docs/GCP.md §3, ADR-031).
# Idempotent: safe to re-run. Billable (tiny): ask before running.
#
#   - enables modelarmor.googleapis.com
#   - template `swiss-nav-input` in the `eu` multi-region (Model Armor has no
#     europe-west6; the agent's model calls are processed in the EU too, ADR-013):
#     prompt injection + jailbreak and the four RAI filters at LOW_AND_ABOVE, so every
#     detection comes back with its confidence and the code applies its own threshold
#     (agents/navigator/armor.py); malicious URLs and SDP basic on (measured, not
#     blocked on). Sanitize operations are NOT logged: the request would put the user's
#     question into Cloud Logging, and questions can be personal (ADR-028).
#   - roles/modelarmor.user for swiss-nav-agent@ (the deployed agent screens) and
#     swiss-nav-ci@ (CI evals). Project-level: Model Armor has no per-template IAM.
#
# No floor settings: they apply to every Gemini call in the project, which is shared
# with other apps (ADR-012).
#
# Usage: make gcp-armor   (= bash infra/model_armor.sh; DRY_RUN=1 prints the commands only)
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT in .env}"
GCLOUD="${GCLOUD:-$(command -v gcloud || echo "$HOME/google-cloud-sdk/bin/gcloud")}"
DRY_RUN="${DRY_RUN:-0}"
LOCATION="${MODEL_ARMOR_LOCATION:-eu}"
TEMPLATE="swiss-nav-input"
NAME="projects/$PROJECT_ID/locations/$LOCATION/templates/$TEMPLATE"
API="https://modelarmor.$LOCATION.rep.googleapis.com/v1"

run() { echo "+ $*" >&2; if [[ "$DRY_RUN" != 1 ]]; then "$@"; fi; }
g() { run "$GCLOUD" "$@" --project "$PROJECT_ID"; }

# Every detection at its confidence; the threshold lives in code (MODEL_ARMOR_MIN_CONFIDENCE).
CONFIG=$(cat <<'JSON'
{
  "filterConfig": {
    "piAndJailbreakFilterSettings": {"filterEnforcement": "ENABLED", "confidenceLevel": "LOW_AND_ABOVE"},
    "raiSettings": {"raiFilters": [
      {"filterType": "DANGEROUS", "confidenceLevel": "LOW_AND_ABOVE"},
      {"filterType": "HARASSMENT", "confidenceLevel": "LOW_AND_ABOVE"},
      {"filterType": "HATE_SPEECH", "confidenceLevel": "LOW_AND_ABOVE"},
      {"filterType": "SEXUALLY_EXPLICIT", "confidenceLevel": "LOW_AND_ABOVE"}
    ]},
    "maliciousUriFilterSettings": {"filterEnforcement": "ENABLED"},
    "sdpSettings": {"basicConfig": {"filterEnforcement": "ENABLED"}}
  },
  "templateMetadata": {"logTemplateOperations": true, "logSanitizeOperations": false},
  "labels": {"app": "swiss-nav"}
}
JSON
)

echo "== project=$PROJECT_ID location=$LOCATION dry_run=$DRY_RUN"

echo "== API"
g services enable modelarmor.googleapis.com

echo "== template $TEMPLATE"
curl_api() {
  local method=$1 url=$2
  echo "+ curl -X $method $url" >&2
  if [[ "$DRY_RUN" == 1 ]]; then return 0; fi
  curl -sS --fail-with-body -X "$method" -H "Content-Type: application/json" \
    -H "Authorization: Bearer $("$GCLOUD" auth print-access-token)" \
    -H "X-Goog-User-Project: $PROJECT_ID" --data "$CONFIG" "$url"
  echo
}
if [[ "$DRY_RUN" != 1 ]] && curl -sS --fail -o /dev/null \
  -H "Authorization: Bearer $("$GCLOUD" auth print-access-token)" "$API/$NAME" 2>/dev/null; then
  curl_api PATCH "$API/$NAME?updateMask=filterConfig,templateMetadata,labels"
else
  curl_api POST "$API/projects/$PROJECT_ID/locations/$LOCATION/templates?templateId=$TEMPLATE"
fi
[[ "$DRY_RUN" == 1 ]] && echo "$CONFIG" >&2

echo "== IAM"
for sa in swiss-nav-agent swiss-nav-ci; do
  g projects add-iam-policy-binding "$PROJECT_ID" \
    --member "serviceAccount:$sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role roles/modelarmor.user --condition None --quiet >/dev/null
done

echo "== done: MODEL_ARMOR_TEMPLATE=$NAME"
