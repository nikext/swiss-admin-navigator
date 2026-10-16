#!/usr/bin/env bash
# One-time GCP setup (docs/GCP.md §3). Idempotent: safe to re-run.
# The project is shared with other apps, so everything here is prefixed
# `swiss-nav` and labelled app=swiss-nav. Nothing here costs money at rest.
#
# Usage: bash infra/setup.sh            (DRY_RUN=1 prints the commands only)
# Reads GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION from .env.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT in .env}"
REGION="${GOOGLE_CLOUD_LOCATION:-europe-west6}"
GCLOUD="${GCLOUD:-$(command -v gcloud || echo "$HOME/google-cloud-sdk/bin/gcloud")}"
DRY_RUN="${DRY_RUN:-0}"
LABELS="app=swiss-nav"
AR_REPO="swiss-nav"
BUCKET="gs://${PROJECT_ID}-swiss-nav"

run() { echo "+ $*" >&2; if [[ "$DRY_RUN" != 1 ]]; then "$@"; fi; }
exists() { "$GCLOUD" "$@" --project "$PROJECT_ID" >/dev/null 2>&1; }
g() { run "$GCLOUD" "$@" --project "$PROJECT_ID"; }

echo "== project=$PROJECT_ID region=$REGION dry_run=$DRY_RUN"

echo "== APIs"
# modelarmor (M10) and the GPU Artifact Registry repo (M9) are added in those milestones.
g services enable \
  aiplatform.googleapis.com cloudresourcemanager.googleapis.com \
  run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com \
  secretmanager.googleapis.com firestore.googleapis.com \
  cloudtrace.googleapis.com logging.googleapis.com monitoring.googleapis.com \
  iamcredentials.googleapis.com sts.googleapis.com billingbudgets.googleapis.com

echo "== Artifact Registry"
if exists artifacts repositories describe "$AR_REPO" --location "$REGION"; then
  echo "   $AR_REPO exists"
else
  g artifacts repositories create "$AR_REPO" --repository-format=docker \
    --location "$REGION" --labels "$LABELS" \
    --description "Swiss Admin Navigator images"
fi

echo "== Bucket"
if exists storage buckets describe "$BUCKET"; then
  echo "   $BUCKET exists"
else
  g storage buckets create "$BUCKET" --location "$REGION" \
    --uniform-bucket-level-access --public-access-prevention
  g storage buckets update "$BUCKET" --update-labels "$LABELS"
fi

echo "== Service accounts (least privilege, GCP.md §3)"
declare -A SA_ROLES=(
  [swiss-nav-mcp]="roles/aiplatform.user"
  # Agent Runtime identity (M5, ADR-027). `adk deploy --otel_to_cloud` exports OTLP spans and
  # metrics to telemetry.googleapis.com: tracesWriter + metricWriter, and serviceusage for
  # its quota project. cloudtrace.agent covers the legacy Cloud Trace exporter.
  [swiss-nav-agent]="roles/aiplatform.user roles/cloudtrace.agent roles/logging.logWriter roles/telemetry.tracesWriter roles/monitoring.metricWriter roles/serviceusage.serviceUsageConsumer"
  [swiss-nav-web]="roles/aiplatform.user roles/datastore.user"
  [swiss-nav-ci]="roles/aiplatform.user"
  [swiss-nav-apertus]=""
)
for sa in swiss-nav-mcp swiss-nav-agent swiss-nav-web swiss-nav-ci swiss-nav-apertus; do
  email="${sa}@${PROJECT_ID}.iam.gserviceaccount.com"
  if exists iam service-accounts describe "$email"; then
    echo "   $sa exists"
  else
    g iam service-accounts create "$sa" --display-name "Swiss Admin Navigator: ${sa#swiss-nav-}"
  fi
  for role in ${SA_ROLES[$sa]}; do
    run "$GCLOUD" projects add-iam-policy-binding "$PROJECT_ID" \
      --member "serviceAccount:$email" --role "$role" --condition None --quiet >/dev/null
  done
done
run "$GCLOUD" storage buckets add-iam-policy-binding "$BUCKET" \
  --member "serviceAccount:swiss-nav-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/storage.objectAdmin >/dev/null

echo "== done"
