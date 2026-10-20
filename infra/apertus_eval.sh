#!/usr/bin/env bash
# E1's Apertus arm (M9, ADR-006, docs/GCP.md §4): swiss-ai/Apertus-v1.5-8B on Cloud Run with
# one L4 in europe-west4, the answer eval against it, and teardown. Billable while the
# service exists (~USD 1.42/h: L4 + 8 vCPU + 32 GiB, instance-based): Nikola runs it.
#
# Usage: bash infra/apertus_eval.sh     (DRY_RUN=1 prints the commands only)
#   EVAL_ARGS   answer_eval arguments (default: --dataset golden)
#   GPU_TYPE    nvidia-l4 (default) or nvidia-rtx-pro-6000
#   VLLM_ARGS   extra vLLM flags (default: online FP8 weights so a 32k context fits on 24 GB)
#
# Needs HF_TOKEN in .env (the model is gated: accept its license on Hugging Face first) and
# `gcloud components install cloud-run-proxy` (the eval reaches the private service through
# `gcloud run services proxy`, which adds the identity token). The service is deleted on
# exit, whatever happens (trap); rerun to resume the eval from its traces file.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi
mkdir -p data/logs
exec > >(tee -a data/logs/apertus-eval.log) 2>&1  # a copy to follow from another shell

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT in .env}"
REGION="${GPU_REGION:-europe-west4}"
GCLOUD="${GCLOUD:-$(command -v gcloud || echo "$HOME/google-cloud-sdk/bin/gcloud")}"
DRY_RUN="${DRY_RUN:-0}"
LABELS="app=swiss-nav"
SERVICE="swiss-nav-apertus"
SA="swiss-nav-apertus@${PROJECT_ID}.iam.gserviceaccount.com"
SECRET="swiss-nav-hf-token"
MODEL="swiss-ai/Apertus-v1.5-8B"
# swiss-ai's vLLM fork (upstream vLLM can't serve Apertus 1.5 yet), pinned by digest
# (latest-amd64 on 2026-10-20), pulled through an Artifact Registry remote repo of ghcr.io.
REMOTE_REPO="swiss-nav-ghcr"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REMOTE_REPO}/swiss-ai/vllm_apertus_1.5_release@sha256:d85533f251c8272218ae2e519510836376e5a335b44f2204f193018e37753bc6"
GPU_TYPE="${GPU_TYPE:-nvidia-l4}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
VLLM_ARGS="${VLLM_ARGS:---quantization fp8}"
EVAL_ARGS="${EVAL_ARGS:---dataset golden}"
PORT=8081

run() { echo "+ $*" >&2; if [[ "$DRY_RUN" != 1 ]]; then "$@"; fi; }
exists() { "$GCLOUD" "$@" --project "$PROJECT_ID" >/dev/null 2>&1; }

if [[ "$DRY_RUN" != 1 ]]; then
  [[ -n "${HF_TOKEN:-}" ]] || { echo "set HF_TOKEN in .env (read token; accept the license on HF)" >&2; exit 1; }
  "$GCLOUD" components list --filter=id=cloud-run-proxy --format='value(state.name)' 2>/dev/null |
    grep -q Installed || { echo "run: gcloud components install cloud-run-proxy" >&2; exit 1; }
fi
echo "== project=$PROJECT_ID region=$REGION gpu=$GPU_TYPE dry_run=$DRY_RUN"

echo "== Artifact Registry remote repo for ghcr.io (caches the 8.9 GB image; delete after M9)"
if exists artifacts repositories describe "$REMOTE_REPO" --location "$REGION"; then
  echo "   $REMOTE_REPO exists"
else
  run "$GCLOUD" artifacts repositories create "$REMOTE_REPO" --project "$PROJECT_ID" \
    --location "$REGION" --repository-format=docker --mode=remote-repository \
    --remote-docker-repo=https://ghcr.io --labels "$LABELS" \
    --description "Swiss Admin Navigator: ghcr.io pull-through (Apertus vLLM fork, M9)"
fi

echo "== HF token -> Secret Manager ($SECRET), readable by $SA only"
if ! exists secrets describe "$SECRET"; then
  run "$GCLOUD" secrets create "$SECRET" --project "$PROJECT_ID" \
    --replication-policy=automatic --labels "$LABELS"
fi
if [[ "$DRY_RUN" != 1 ]]; then
  printf '%s' "$HF_TOKEN" | "$GCLOUD" secrets versions add "$SECRET" --project "$PROJECT_ID" \
    --data-file=- >/dev/null
fi
run "$GCLOUD" secrets add-iam-policy-binding "$SECRET" --project "$PROJECT_ID" \
  --member "serviceAccount:$SA" --role roles/secretmanager.secretAccessor --quiet >/dev/null

PROXY_PID=""
START=$(date +%s)
cleanup() {
  status=$?
  [[ -n "$PROXY_PID" ]] && kill "$PROXY_PID" 2>/dev/null || true
  echo "== teardown: delete $SERVICE (GPU up ~$(( ($(date +%s) - START) / 60 )) min)" >&2
  run "$GCLOUD" run services delete "$SERVICE" --project "$PROJECT_ID" --region "$REGION" \
    --quiet || true
  if [[ "$DRY_RUN" != 1 ]]; then
    "$GCLOUD" run services list --project "$PROJECT_ID" --region "$REGION" \
      --format='value(metadata.name)' | grep -x "$SERVICE" &&
      echo "!! $SERVICE still exists: delete it by hand" >&2
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

echo "== deploy (waits until vLLM has downloaded and loaded the model)"
# Weights come from HF on start into the in-memory filesystem (~18.5 GB of 32 GiB). One
# instance, never more; scale to zero is moot because the trap deletes the service.
# The first start (2026-10-20) reached vLLM's warm-up after ~27 min (image pull, weight
# download, load, compile), hence the 40-min probe window; at 0.92 GPU memory and the default
# 256 sequences, the sampler warm-up (131k vocab) ran out of memory: 0.88 and 8 sequences
# (the eval sends at most 2 conversations at a time).
# --async: the second start's revision was ready after 13 min, but the service had already
# reported "Resource readiness deadline exceeded" (and turned ready a second after the trap
# deleted it), so the script waits for vLLM itself below.
run "$GCLOUD" run deploy "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --async \
  --image "$IMAGE" --service-account "$SA" --no-allow-unauthenticated \
  --gpu 1 --gpu-type "$GPU_TYPE" --no-gpu-zonal-redundancy \
  --cpu 8 --memory 32Gi --no-cpu-throttling \
  --min-instances 0 --max-instances 1 --concurrency 16 --timeout 3600 \
  --port 8000 --set-secrets HF_TOKEN="$SECRET":latest --labels "$LABELS" \
  --startup-probe httpGet.path=/health,httpGet.port=8000,periodSeconds=20,timeoutSeconds=5,failureThreshold=120 \
  --command vllm \
  --args="^|^serve|${MODEL}|--host|0.0.0.0|--port|8000|--max-model-len|${MAX_MODEL_LEN}|--gpu-memory-utilization|0.88|--max-num-seqs|8|--chat-template-content-format|string|--enable-auto-tool-choice|--tool-call-parser|apertus|${VLLM_ARGS// /|}"

echo "== proxy on 127.0.0.1:$PORT; wait for vLLM (up to 45 min; ~13 min when the image is cached)"
if [[ "$DRY_RUN" != 1 ]]; then
  until "$GCLOUD" run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" \
    --format='value(status.url)' 2>/dev/null | grep -q .; do sleep 5; done
  "$GCLOUD" run services proxy "$SERVICE" --project "$PROJECT_ID" --region "$REGION" \
    --port "$PORT" >data/logs/apertus-proxy.log 2>&1 &
  PROXY_PID=$!
  deadline=$(( $(date +%s) + 45 * 60 ))
  until curl -sf --max-time 10 "http://127.0.0.1:$PORT/v1/models" >/dev/null; do
    # A revision that failed (container exit, probe timeout) won't come back: stop early.
    ready=$("$GCLOUD" run revisions list --service "$SERVICE" --project "$PROJECT_ID" \
      --region "$REGION" --format='value(status.conditions[0].status,status.conditions[0].message)' \
      2>/dev/null | head -1)
    if [[ "$ready" == False* ]]; then echo "revision failed: $ready" >&2; exit 1; fi
    if (( $(date +%s) > deadline )); then echo "vLLM not reachable after 45 min" >&2; exit 1; fi
    echo "   $(date +%H:%M:%S) waiting: ${ready:-starting}" | cut -c1-120
    sleep 30
  done
  echo "   vLLM up after $(( ($(date +%s) - START) / 60 )) min"
fi

echo "== eval (rerun to resume from data/logs/e1-apertus.traces.jsonl)"
export AGENT_MODEL="$MODEL" AGENT_LOCATION="http://127.0.0.1:${PORT}/v1"
# shellcheck disable=SC2086
run uv run python -m evals.harness.answer_eval $EVAL_ARGS --name e1-apertus \
  --concurrency 2 --case-timeout 900 --traces data/logs/e1-apertus.traces.jsonl
