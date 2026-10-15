#!/usr/bin/env bash
# GitHub Actions -> GCP via Workload Identity Federation (docs/GCP.md §3, EVALS.md §3).
# No JSON keys: the CI job exchanges its GitHub OIDC token for a short-lived
# token of swiss-nav-ci@. Only workflows of this one repository can do that
# (attribute condition), and only that SA can be impersonated. Idempotent;
# nothing here costs money.
#
# Usage: bash infra/wif.sh            (DRY_RUN=1 prints the commands only)
# Then set the printed values as GitHub repository variables (not secrets;
# they are identifiers, not credentials).
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT in .env}"
GCLOUD="${GCLOUD:-$(command -v gcloud || echo "$HOME/google-cloud-sdk/bin/gcloud")}"
DRY_RUN="${DRY_RUN:-0}"
REPO="${GITHUB_REPO:-nikext/swiss-admin-navigator}"
POOL="swiss-nav-github"
PROVIDER="github"
SA="swiss-nav-ci@${PROJECT_ID}.iam.gserviceaccount.com"

run() { echo "+ $*" >&2; if [[ "$DRY_RUN" != 1 ]]; then "$@"; fi; }
exists() { "$GCLOUD" "$@" --project "$PROJECT_ID" >/dev/null 2>&1; }
g() { run "$GCLOUD" "$@" --project "$PROJECT_ID"; }

echo "== project=$PROJECT_ID repo=$REPO dry_run=$DRY_RUN"
PROJECT_NUMBER="$("$GCLOUD" projects describe "$PROJECT_ID" --format 'value(projectNumber)')"

echo "== Workload identity pool"
if exists iam workload-identity-pools describe "$POOL" --location global; then
  echo "   $POOL exists"
else
  g iam workload-identity-pools create "$POOL" --location global \
    --display-name "swiss-nav GitHub Actions" \
    --description "GitHub Actions of $REPO (Swiss Admin Navigator CI)"
fi

echo "== OIDC provider (only $REPO)"
if exists iam workload-identity-pools providers describe "$PROVIDER" \
    --workload-identity-pool "$POOL" --location global; then
  echo "   $PROVIDER exists"
else
  g iam workload-identity-pools providers create-oidc "$PROVIDER" \
    --workload-identity-pool "$POOL" --location global \
    --issuer-uri "https://token.actions.githubusercontent.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref,attribute.event_name=assertion.event_name" \
    --attribute-condition "assertion.repository == '$REPO'"
fi

echo "== Let the repository impersonate $SA"
MEMBER="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${REPO}"
run "$GCLOUD" iam service-accounts add-iam-policy-binding "$SA" --project "$PROJECT_ID" \
  --role roles/iam.workloadIdentityUser --member "$MEMBER" --condition None >/dev/null

echo "== GitHub repository variables (gh variable set NAME --body VALUE)"
echo "GCP_PROJECT=$PROJECT_ID"
echo "GCP_WIF_PROVIDER=projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"
echo "GCP_CI_SA=$SA"
echo "== done"
