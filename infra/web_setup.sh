#!/usr/bin/env bash
# What the web BFF needs besides the service account (M6, docs/GCP.md §3, ADR-028).
# Idempotent: safe to re-run. Creates billable (tiny) resources: ask before running.
#
#   - Firestore database `swiss-nav` (native, europe-west6) for the quota counters and
#     feedback, with a TTL policy on quota.expires (counters expire a week after their day).
#     A named database, not (default): the project is shared (ADR-012).
#   - Secret Manager secret `swiss-nav-access-code` (replicated in europe-west6 only).
#     The first version comes from WEB_ACCESS_CODE, else a random code that is printed
#     once. Rotate: ROTATE=1 (adds a version; the cookie key derives from the code, so
#     every visitor is signed out).
#   - swiss-nav-web@ may read that one secret (secretAccessor on the secret, not the project).
#
# Usage: bash infra/web_setup.sh        (DRY_RUN=1 prints the commands only)
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT in .env}"
REGION="${GOOGLE_CLOUD_LOCATION:-europe-west6}"
GCLOUD="${GCLOUD:-$(command -v gcloud || echo "$HOME/google-cloud-sdk/bin/gcloud")}"
DRY_RUN="${DRY_RUN:-0}"
DB="swiss-nav"
SECRET="swiss-nav-access-code"
WEB_SA="swiss-nav-web@${PROJECT_ID}.iam.gserviceaccount.com"

run() { echo "+ $*" >&2; if [[ "$DRY_RUN" != 1 ]]; then "$@"; fi; }
exists() { "$GCLOUD" "$@" --project "$PROJECT_ID" >/dev/null 2>&1; }
g() { run "$GCLOUD" "$@" --project "$PROJECT_ID"; }

echo "== project=$PROJECT_ID region=$REGION dry_run=$DRY_RUN"

echo "== Firestore database $DB"
if exists firestore databases describe --database "$DB"; then
  echo "   $DB exists"
else
  g firestore databases create --database "$DB" --location "$REGION" \
    --type firestore-native --delete-protection
fi
# TTL deletion runs within ~24 h after `expires`; it keeps the quota collection small.
g firestore fields ttls update expires --collection-group quota --enable-ttl \
  --database "$DB" --async --quiet

echo "== Secret $SECRET"
new_code() {
  if [[ -n "${WEB_ACCESS_CODE:-}" ]]; then printf '%s' "$WEB_ACCESS_CODE"; return; fi
  python3 -I -c 'import secrets; print(secrets.token_urlsafe(12), end="")'
}
if exists secrets describe "$SECRET"; then
  echo "   $SECRET exists"
  if [[ "${ROTATE:-0}" == 1 ]]; then
    code="$(new_code)"
    if [[ "$DRY_RUN" != 1 ]]; then
      printf '%s' "$code" | "$GCLOUD" secrets versions add "$SECRET" --data-file=- \
        --project "$PROJECT_ID" >/dev/null
    fi
    echo "   new access code: $code"
  fi
else
  g secrets create "$SECRET" --replication-policy user-managed --locations "$REGION" \
    --labels app=swiss-nav
  code="$(new_code)"
  if [[ "$DRY_RUN" != 1 ]]; then
    printf '%s' "$code" | "$GCLOUD" secrets versions add "$SECRET" --data-file=- \
      --project "$PROJECT_ID" >/dev/null
  fi
  echo "   access code (shown once; share it with testers): $code"
fi
g secrets add-iam-policy-binding "$SECRET" --member "serviceAccount:$WEB_SA" \
  --role roles/secretmanager.secretAccessor --quiet >/dev/null

echo "== done"
