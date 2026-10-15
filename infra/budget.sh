#!/usr/bin/env bash
# Monthly budget alert at 50/90/100% (docs/GCP.md §3). Idempotent by display name.
# The amount must be in the billing account's currency; the account linked to
# the project is billed in USD, so CHF 30 is expressed as BUDGET_AMOUNT=35USD
# by default (ADR-012). The budget covers the whole project, which is shared
# with other apps, so their spend counts towards it too.
#
# Usage: bash infra/budget.sh           (DRY_RUN=1 prints the command only)
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT in .env}"
GCLOUD="${GCLOUD:-$(command -v gcloud || echo "$HOME/google-cloud-sdk/bin/gcloud")}"
DRY_RUN="${DRY_RUN:-0}"
BUDGET_AMOUNT="${BUDGET_AMOUNT:-35USD}"
NAME="swiss-nav monthly (${PROJECT_ID})"

ACCOUNT="$("$GCLOUD" billing projects describe "$PROJECT_ID" --format='value(billingAccountName)')"
ACCOUNT="${ACCOUNT#billingAccounts/}"
echo "== billing account=$ACCOUNT amount=$BUDGET_AMOUNT dry_run=$DRY_RUN"

if "$GCLOUD" billing budgets list --billing-account "$ACCOUNT" \
    --format='value(displayName)' | grep -qxF "$NAME"; then
  echo "   budget '$NAME' exists; change it in the console or delete and re-run"
  exit 0
fi

cmd=("$GCLOUD" billing budgets create --billing-account "$ACCOUNT"
  --display-name "$NAME" --budget-amount "$BUDGET_AMOUNT"
  --filter-projects "projects/$PROJECT_ID" --calendar-period month
  --threshold-rule percent=0.5 --threshold-rule percent=0.9
  --threshold-rule percent=1.0)
echo "+ ${cmd[*]}"
if [[ "$DRY_RUN" != 1 ]]; then "${cmd[@]}"; fi
