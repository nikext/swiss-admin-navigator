# Google Cloud setup, deploy and costs

> **Naming (as of 2026-10):** Vertex AI was rebranded **Gemini Enterprise
> Agent Platform** at Cloud Next '26 (April 2026). Agent Engine is now called
> **Agent Runtime** in the docs. The API is still `aiplatform.googleapis.com`,
> the CLI is still `adk deploy agent_engine`, and resources are still
> `…/reasoningEngines/<id>`. Use the new names in the README and CV, and the
> old ones where the tooling requires them.

## 1. Ground rules for the build agent

- **The user runs `gcloud auth login` and `gcloud auth application-default login`
  themselves.** Suggest `! gcloud auth login` in the Claude Code prompt.
  gcloud is installed user-local at `~/google-cloud-sdk`.
- **Ask before creating anything billable**: Agent Runtime deploys, GPU
  services, Model Garden endpoint deploys, Firestore, and anything with min
  instances above 0. Read-only `gcloud … list/describe` is fine.
- Every GPU or Model Garden *endpoint* deploy script must also **undeploy**:
  use a `trap` on exit, and print a loud reminder if the undeploy fails.
  Endpoints bill per hour while they exist, even when idle.
- Never commit keys. Locally, use ADC. In CI, use Workload Identity Federation.
  In the cloud, use per-service service accounts.

## 2. Project

- **Chosen (2026-10-15): `random-projects-509513`.** It already has billing
  and is **shared** with `zuri-sunny` and `epoch-war` (Cloud Run,
  europe-west6). Everything this project creates is prefixed `swiss-nav` and
  labelled `app=swiss-nav`, so it can be found and torn down without touching
  the other apps (ADR-012). A dedicated project was the cleaner option, but the
  user chose the existing one.
- Config lives in `.env` (gitignored). `.env.example` is committed.

```bash
export PROJECT_ID=…                 # set in .env
export REGION=europe-west6          # Zürich: agent, MCP, web
export GPU_REGION=europe-west4      # Cloud Run GPUs are not offered in europe-west6
```

## 3. One-time setup (`make gcp-setup` → `infra/setup.sh`, idempotent)

Ran on 2026-10-15; a second run reported every resource as existing.
`DRY_RUN=1 make gcp-setup` prints the commands without running them.

- **APIs:** aiplatform, cloudresourcemanager, run, artifactregistry,
  cloudbuild, secretmanager, firestore (API only, no database), cloudtrace,
  logging, monitoring, iamcredentials, sts, billingbudgets.
  `modelarmor.googleapis.com` is added in M10 (verify the service name then).
- **Artifact Registry:** `swiss-nav` (docker, europe-west6). The GPU repo
  `swiss-nav-gpu` (europe-west4) is added in M9.
- **Bucket:** `gs://$PROJECT_ID-swiss-nav` (europe-west6, uniform access,
  public access prevention enforced) for index builds, eval reports and
  staging.

### Service accounts (least privilege)

Names carry the `swiss-nav-` prefix because the project is shared (ADR-012).
All five exist since 2026-10-15.

| SA | Used by | Roles |
|---|---|---|
| `swiss-nav-mcp@` | Cloud Run MCP | `roles/aiplatform.user` (query embeddings only) |
| `swiss-nav-agent@` | Agent Runtime | `roles/aiplatform.user`, `roles/cloudtrace.agent`, `roles/logging.logWriter`. Verify which identity Agent Runtime runs as and whether a custom SA is supported. |
| `swiss-nav-web@` | Cloud Run web | `roles/aiplatform.user` (to call `reasoningEngines:streamQuery`), `roles/datastore.user` |
| `swiss-nav-ci@` | GitHub Actions via WIF | `roles/aiplatform.user`, `roles/storage.objectAdmin` on the bucket |
| `swiss-nav-apertus@` | Cloud Run GPU | none (no GCP API calls) |

### Budget guardrail (done in M0)

`make gcp-budget` (`infra/budget.sh`, idempotent by display name) created
**"swiss-nav monthly (random-projects-509513)"** on 2026-10-15: **USD 37/month
(≈ CHF 30)**, alerts at 50/90/100%, scoped to the project. The billing account
is billed in USD, so the amount can't be set in CHF. The project is shared, so
`zuri-sunny` and `epoch-war` spend counts towards it too. The billing account
also has two older account-wide budgets ($20 and $50) that this repo doesn't
manage. A public demo without a cap is the main financial risk.

## 4. Deploy recipes (verify the flags against current docs)

### MCP server → Cloud Run

```bash
# Image contains index.sqlite (built by `make index`), like zuri-sunny's baked DB.
gcloud run deploy swiss-law-mcp --source mcp_server --region $REGION \
  --service-account swiss-nav-mcp@$PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated --min-instances 0 --max-instances 2 \
  --memory 1Gi --cpu 1 --concurrency 40 --timeout 60
```

- Public and read-only by design (ADR-003). Rate-limit `search_law` in-app.
- The MCP endpoint path is `/mcp` (Streamable HTTP).

### Agent → Agent Runtime

```bash
adk deploy agent_engine \
  --project=$PROJECT_ID --region=$REGION \
  --display_name="swiss-admin-navigator" \
  agents/navigator
```

- Python deployments don't include the ADK API server or web UI; Agent
  Runtime provides the API.
- Output contains `projects/…/locations/europe-west6/reasoningEngines/<RESOURCE_ID>`.
  Store the ID in `.env` as `AGENT_RUNTIME_ID`.
- Query endpoint:
  `https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/$REGION/reasoningEngines/$AGENT_RUNTIME_ID:query`
  (streaming: `:streamQuery`). Check the request body format at
  <https://adk.dev/deploy/agent-runtime/test/>.
- Alternative: the "Agents CLI" deployment path (CI/CD and IaC scaffolding) at
  <https://adk.dev/deploy/agent-runtime/agents-cli/>. Evaluate it in M5 and use
  it if it fits.
- Pass config (MCP URL, model IDs) through env vars on deploy. Verify how
  `adk deploy agent_engine` passes env vars (`.env` in the agent dir vs a
  flag).

### Web → Cloud Run

```bash
gcloud run deploy swiss-nav-web --source web --region $REGION \
  --service-account swiss-nav-web@$PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated --min-instances 0 --max-instances 2 \
  --set-env-vars AGENT_RUNTIME_ID=…,REGION=$REGION \
  --set-secrets ACCESS_CODE=swiss-nav-access-code:latest
```

### Apertus → Cloud Run GPU (M9)

```bash
# Cloud Run pulls from Artifact Registry/Docker Hub. Mirror the swiss-ai vLLM fork image:
docker pull ghcr.io/swiss-ai/vllm_apertus_1.5_release:latest-amd64
docker tag … $GPU_REGION-docker.pkg.dev/$PROJECT_ID/swiss-nav-gpu/vllm-apertus:<pinned-tag>
docker push …

gcloud run deploy apertus --image $GPU_REGION-docker.pkg.dev/…/vllm-apertus:<tag> \
  --region $GPU_REGION --gpu 1 --gpu-type nvidia-l4 --no-gpu-zonal-redundancy \
  --cpu 8 --memory 32Gi --min-instances 0 --max-instances 1 \
  --no-allow-unauthenticated --service-account swiss-nav-apertus@… \
  --set-secrets HF_TOKEN=hf-token:latest \
  --args="vllm,serve,swiss-ai/Apertus-v1.5-8B,--max-model-len,32768,--gpu-memory-utilization,0.90,--chat-template-content-format,string,--enable-auto-tool-choice,--tool-call-parser,apertus"
```

- **Feasibility spike first:** 9B parameters in bf16 ≈ 18 GB of weights on a
  24 GB L4, and the multimodal towers stay float32. It may not fit with a
  usable KV cache. Options, in order: (1) lower `--max-model-len` to 8–16k;
  (2) text-only loading if the fork supports it; (3) an FP8 quant;
  (4) RTX PRO 6000 (96 GB, preview, europe-west4). Record the result in
  DECISIONS.md.
- **Model Garden alternative:** first check whether Model Garden can deploy
  `swiss-ai/Apertus-v1.5-8B` from Hugging Face with the custom vLLM image. If
  it can, prefer it for the "Model Garden" story, but endpoints bill per hour,
  so undeploy after each eval run.
- Weights load from HF on each cold start (slow). Pre-bake them into the image
  or a GCS-mounted volume once the config works.
- Scale-to-zero: the GPU instance starts in under 5 s plus model load time.
  The eval runner should send a warm-up request and wait.
- Calls need an ID token (`--no-allow-unauthenticated`). LiteLLM gets
  `Authorization: Bearer $(gcloud auth print-identity-token --audiences=<url>)`
  for eval runs.

### Claude via Model Garden (MaaS, for E1 and cross-family judging)

- Enable the Claude model in the Model Garden console (needs the user's
  acceptance). Claude models are listed for European regions including
  europe-west6 (verify the exact model available there). Don't trust the
  locations page alone: Gemini is listed for "Europe" but isn't served in
  europe-west6 for this project (ADR-013). Probe it live, region by region.
- Call it through LiteLLM (`vertex_ai/claude-…`) in the eval harness, or
  through ADK's Claude support. Pay-per-token, so there's nothing to undeploy.

## 5. Cost model (estimates; verify against current pricing pages)

| Item | Driver | Expected monthly |
|---|---|---|
| Agent Runtime | vCPU/GB-hours; a no-cost tier exists (third-party sources cite 50 vCPU-h + 100 GB-h/month; verify) | ~0–10 CHF at demo traffic |
| Sessions + Memory Bank | billed per event since 2026-02 (third-party source: ~$0.25 / 1k events; verify) | < 5 CHF |
| Gemini Flash | tokens; an answer ≈ 4–6 LLM calls × 5–10k input tokens | ~0.5–2 Rp. per answer (verify pricing) |
| Embeddings | one-time corpus embed (~30k chunks) + per query | < 2 CHF build, negligible per query |
| Cloud Run (MCP, web) | scale to zero | ~0–3 CHF |
| Apertus GPU (L4) | per-second while running; scale to zero | ~1 CHF/h while active; eval runs only |
| Full eval matrix run | ~150 cases × 5 configs + judge | ~5–20 CHF per run |

Put the real numbers in `evals/pricing.yaml` with a "checked on" date, and let
eval reports compute CHF per answer.
