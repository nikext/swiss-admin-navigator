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
  cloudbuild, secretmanager, firestore (API only; the `swiss-nav` database comes from `make gcp-web`, M6), cloudtrace,
  logging, monitoring, iamcredentials, sts, billingbudgets.
  `modelarmor.googleapis.com` (verified name) is enabled by `make gcp-armor`
  (M10, 2026-10-19), not by this script.
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
| `swiss-nav-agent@` | Agent Runtime (runtime identity, `--service_account`; verified M5) | `roles/aiplatform.user`, `roles/logging.logWriter`, `roles/cloudtrace.agent`, and for the OTLP export to `telemetry.googleapis.com` `roles/telemetry.tracesWriter`, `roles/monitoring.metricWriter`, `roles/serviceusage.serviceUsageConsumer` (M5, ADR-027); `roles/modelarmor.user` (M10, ADR-032). Without a custom SA the agent runs as `service-<number>@gcp-sa-aiplatform-re.iam.gserviceaccount.com`. |
| `swiss-nav-web@` | Cloud Run web | `roles/aiplatform.user` (to call `reasoningEngines:streamQuery`), `roles/datastore.user` (Firestore database `swiss-nav`), `roles/secretmanager.secretAccessor` on the secret `swiss-nav-access-code` only (M6, `make gcp-web`) |
| `swiss-nav-ci@` | GitHub Actions via WIF | `roles/aiplatform.user`, `roles/storage.objectAdmin` on the bucket, `roles/modelarmor.user` (M10) |
| `swiss-nav-apertus@` | Cloud Run GPU | none (no GCP API calls) |

### CI: Workload Identity Federation and the published index (M4, ADR-021)

`make gcp-wif` (`infra/wif.sh`, idempotent, `DRY_RUN=1`) creates the pool
`swiss-nav-github` with an OIDC provider `github` that accepts only workflows
of `nikext/swiss-admin-navigator`, and lets that repository impersonate
`swiss-nav-ci@` (`roles/iam.workloadIdentityUser`). It prints the three
repository variables the eval workflows read: `GCP_PROJECT`,
`GCP_WIF_PROVIDER`, `GCP_CI_SA` (`gh variable set NAME --body VALUE`). Not run
yet as of 2026-10-15.

CI fetches the search index from `gs://$PROJECT_ID-swiss-nav/index/<sha256[:16]>/index.sqlite`
(`make publish-index` uploads it and rewrites the pointer `evals/ci_index.json`;
published 2026-10-15: `93a7652bc58106c8`, index as_of 2026-10-15, built from
c756c89). Re-publish in the PR that rebuilds the index.

### Claude in Model Garden (M4 judge candidate)

Model Garden lists `claude-opus-5-5`, `claude-sonnet-5-5` and `claude-haiku-5-5`
(`gcloud ai model-garden models list --model-filter=claude --billing-project …`),
called with the bare model id through `AnthropicVertex` on `global` (or `eu`).
On 2026-10-15 every call returned 429 `Quota exceeded for
aiplatform.googleapis.com/global_online_prediction_requests_per_base_model`:
the models must be enabled in the console (partner terms) and may need a quota
request. europe-west6 returns 404 for all of them. The quota request was
**refused** on 2026-10-16; on that day every Claude model (5.5 and 4.5) still
returned 429 on `global`, and europe-west1/-west4, us-east5, us-central1 and
asia-southeast1 returned 404 for the 5.5 models.

### Open models on MaaS (judge cross-check, M9 contenders)

Called through the OpenAI-compatible endpoint
`https://aiplatform.googleapis.com/v1/projects/<project>/locations/global/endpoints/openapi`
with an ADC bearer token and ids like `qwen/qwen3-235b-a22b-instruct-2507-maas`
(`evals/harness/judge.py`). Pay per token, nothing to enable or undeploy.
Probed 2026-10-16: on `global`, `zai-org/glm-5.2-maas`, `zai-org/glm-5-maas`,
`deepseek-ai/deepseek-v4.1-flash-maas`, `deepseek-ai/deepseek-v3.2-maas`,
`qwen/qwen3-235b-a22b-instruct-2507-maas`, `qwen/qwen3-next-80b-a3b-instruct-maas`,
`openai/gpt-oss-120b-maas`, `moonshotai/kimi-k2-thinking-maas` and
`minimaxai/minimax-m2-maas` all answered; europe-west4 served none of them,
us-central1 only gpt-oss. List prices come from the Cloud Billing catalog
(service `C7E2-9256-1C43`), since the pricing page doesn't render for our
fetcher.

### Model Armor (M10, ADR-032)

`make gcp-armor` (`infra/model_armor.sh`, idempotent, `DRY_RUN=1`) ran on
2026-10-19: it enables the API, creates or updates the template
**`projects/$PROJECT_ID/locations/eu/templates/swiss-nav-input`** (label
`app=swiss-nav`) and grants `roles/modelarmor.user` to `swiss-nav-agent@` and
`swiss-nav-ci@` (project-level; there is no per-template IAM).

- **Location `eu`:** Model Armor has no europe-west6 (its Europe regions are
  europe-west1/2/3/4/9 and europe-southwest1, plus `eu`). Endpoint
  `https://modelarmor.eu.rep.googleapis.com/v1/<template>:sanitizeUserPrompt`.
- **Template:** prompt injection + jailbreak and the four RAI filters at
  LOW_AND_ABOVE, malicious URLs and SDP basic on. The agent applies its own
  threshold (`MODEL_ARMOR_MIN_LEVEL`). `logSanitizeOperations` is off: it
  would put user questions into Cloud Logging.
- **No floor settings and no `model_armor_config` on Gemini calls.** Floor
  settings apply to every Gemini call in the shared project. Per-request
  templates work only in europe-west1/2/3 (and two Asian regions), not on the
  `eu` endpoint the agent's model is served from (ADR-013).
- **Pricing (2026-10-19):** 2M tokens a month free, then USD 0.10 per 1M
  (standalone). Quota: 1,200 calls a minute per project.
- The agent reads `MODEL_ARMOR_TEMPLATE`, `MODEL_ARMOR_MODE`
  (block | log | off) and `MODEL_ARMOR_MIN_LEVEL` from `.env`, and
  `make deploy-agent` stages them into the Agent Runtime env.

### Budget guardrail (done in M0)

`make gcp-budget` (`infra/budget.sh`, idempotent by display name) created
**"swiss-nav monthly (random-projects-509513)"** on 2026-10-15: **USD 37/month
(≈ CHF 30)**, alerts at 50/90/100%, scoped to the project. The billing account
is billed in USD, so the amount can't be set in CHF. The project is shared, so
`zuri-sunny` and `epoch-war` spend counts towards it too. The billing account
also has two older account-wide budgets ($20 and $50) that this repo doesn't
manage. A public demo without a cap is the main financial risk.

## 4. Deploy recipes (verify the flags against current docs)

### MCP server → Cloud Run (done in M2)

```bash
make index        # data/index.sqlite (embeddings come from the cache when warm)
make deploy-mcp   # infra/deploy_mcp.sh: build, push, deploy, smoke /health (DRY_RUN=1)
```

`infra/deploy_mcp.sh` builds `mcp_server/Dockerfile` **from the repo root**
(the image needs `ingest/eid.py` and `data/index.sqlite`; a whitelist
`Dockerfile.dockerignore` keeps the context small), tags it with the commit,
pushes to `europe-west6-docker.pkg.dev/$PROJECT_ID/swiss-nav/swiss-nav-mcp`
with a short-lived token (no docker credential helper is installed; it logs
out after the push), then:

```bash
gcloud run deploy swiss-nav-mcp --image … --region europe-west6 \
  --service-account swiss-nav-mcp@$PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated --min-instances 0 --max-instances 2 \
  --cpu 1 --memory 1Gi --concurrency 40 --timeout 60 --cpu-boost \
  --execution-environment gen2 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID --labels app=swiss-nav,commit=<sha>
```

- URL (2026-10-15): `https://swiss-nav-mcp-mdyqt5hgsq-oa.a.run.app`, MCP at
  `/mcp`, health at **`/health`**. Cloud Run answers `/healthz` itself with
  404 (paths ending in "z" are reserved; verified).
- Public and read-only by design (ADR-003). `search_law` is rate-limited per
  client in-app (30/min, burst 10; the last `X-Forwarded-For` hop, IPv6 per
  /64), paid query embeddings have a budget of 30/min per instance across
  all clients (then keyword search), bodies over 64 KiB get 413, and max 2
  instances caps the rest (M10, ADR-033). Rate-limit and budget hits are
  logged at WARNING.
- Logs are structured JSON; they carry a salted hash instead of the client
  IP and no query text (`LOG_QUERIES=1` to opt in for debugging).
- gen2, not the default gen1, and the image preloads the files it imports:
  cold start 2.1 s to ready, 3.9 s to a client's first search result
  (ADR-017).
- Claude Code: `claude mcp add --scope user --transport http swiss-law <url>/mcp`.

### Agent → Agent Runtime (done in M5, ADR-027)

```bash
DRY_RUN=1 make deploy-agent   # stage + Python 3.11 import check, print the deploy (free)
make deploy-agent             # infra/deploy_agent.sh (billable; Nikola runs it)
```

`adk deploy agent_engine` (ADK 2.12) uploads one folder and builds ADK's own
Dockerfile on Cloud Build: `python:3.11-slim`, `pip install -r
requirements.txt`, `adk api_server --a2a` with Sessions and Memory at
`agentengine://<itself>`. It reads `requirements.txt` and `.env` from the agent
folder and scaling/labels from an `.agent_engine_config.json`
(`--agent_engine_config_file`). `infra/deploy_agent.sh` therefore:

1. stages `agents/navigator` from the commit (tracked files, no tests) into a
   temp dir, with `requirements.txt` = `uv export --package swiss-nav-navigator`
   (the lock's pins) and a `.env` holding the agent's runtime env:
   `SWISS_LAW_MCP_URL` (the Cloud Run MCP server, looked up with
   `gcloud run services describe`, or `AGENT_MCP_URL`), `NAV_PROFILE`,
   `GOOGLE_GENAI_USE_ENTERPRISE=TRUE`. Nothing secret. **This is the env
   mechanism** (verified: the deployed spec carries exactly these plus
   `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`). The Dockerfile itself sets
   `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION=europe-west6`; model
   endpoints still come from the profile (ADR-013).
2. imports the staged agent under **Python 3.11** with exactly those pins
   (`uv run --isolated --python 3.11 --with-requirements`): the image is 3.11
   while the workspace is 3.12, and the shared venv once hid a missing `mcp`
   dependency;
3. deploys with `infra/agent_runtime.json` + a `commit` label,
   `--service_account swiss-nav-agent@…`, `--otel_to_cloud`, `--display_name`
   (ADK otherwise replaces the config's with the folder name), and
   `--agent_engine_id $AGENT_RUNTIME_ID` when set (update in place).

- **Instance (2026-10-16):** `projects/random-projects-509513/locations/europe-west6/reasoningEngines/5798067860890714112`
  (`AGENT_RUNTIME_ID` in `.env`). Build + deploy took about 5 minutes.
- **Scaling (cost):** the SDK default is `min_instances` 1 at 4 vCPU / 4 GiB,
  always on: about USD 270/month at list price. `agent_runtime.json` sets
  `min_instances` 0, `max_instances` 2, 1 vCPU / 2 GiB, concurrency 8. Cold
  start: first streamed event after 9.8 s (container start + first model call).
- **Query:** `make query-remote Q="…"` (`scripts/query_remote.py`, streams
  `async_stream_query` through the `agentplatform` SDK; `ARGS=--traces` then
  shows the run's Cloud Trace spans). REST equivalent:
  `POST https://europe-west6-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/europe-west6/reasoningEngines/$AGENT_RUNTIME_ID:query`
  with `{"class_method": "async_create_session", "input": {"user_id": "u"}}`,
  then `…:streamQuery?alt=sse` with `{"class_method": "async_stream_query",
  "input": {"user_id": "u", "session_id": "<id>", "message": "…"}}`. Each
  streamed item is one ADK `Event` as a snake_case dict.
- **Eval:** `make eval-smoke-remote` (`--target remote`).
- **Tracing:** `--otel_to_cloud` exports spans over OTLP to
  `telemetry.googleapis.com` (not the legacy Cloud Trace API): `invoke_agent`,
  `call_llm`, `generate_content <model>`, `execute_tool <tool>` and the MCP
  client spans. Message content is not captured
  (`ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`, ADK's default with that flag;
  the GenAI log records show `<elided>`). Cloud Trace's `traces.list` does
  not return these traces (verified 2026-10-16); `traces.get` does, and the
  trace ids are on the agent's log entries.
- The "Agents CLI" path (<https://adk.dev/deploy/agent-runtime/agents-cli/>)
  was not adopted: `adk deploy` plus a 100-line script covers what we need.
- Delete with the SDK (`client.runtimes.delete(name=…, force=True)`, which also
  removes sessions) if the instance is ever retired.
- **Memory Bank (M7, ADR-029):** lives in the same instance's
  `context_spec.memory_bank_config`; `make memory-bank ARGS="apply --variant
  profile"` sets it (structured profile, natural-language memories and
  revisions off, TTL 30 days, extraction model from the profile's `memory`
  role). `ARGS=show` prints it; `list|purge --user web-…` inspects or deletes a
  visitor's memories. Agent deploys don't change it.
- **Memory eval instance:** `swiss-nav-memory-eval`
  (`…/reasoningEngines/5494074886043205632`, `MEMORY_EVAL_RUNTIME_ID` in
  `.env`), created by `make memory-bank ARGS="create-eval --variant profile"`:
  no code, no compute, only a Memory Bank for `make eval-memory`. Costs
  nothing while idle.

### Web → Cloud Run (M6, ADR-028)

```bash
DRY_RUN=1 make gcp-web     # Firestore database + TTL, access-code secret, IAM (preview)
make gcp-web               # once (billable, tiny; Nikola runs it). Prints the access code once.
DRY_RUN=1 make deploy-web  # preview
make deploy-web            # infra/deploy_web.sh (billable, public behind the code; Nikola runs it)
```

- `infra/web_setup.sh` (idempotent): Firestore database **`swiss-nav`**
  (native, europe-west6, delete protection; a named database because the
  project is shared) with a TTL policy on `quota.expires`; secret
  **`swiss-nav-access-code`** (replicated in europe-west6 only; first version
  from `WEB_ACCESS_CODE` or random, `ROTATE=1` adds a version and signs
  everyone out); `secretAccessor` for `swiss-nav-web@` on that secret.
- `infra/deploy_web.sh` builds `web/Dockerfile` (Node 22 slim, Next.js
  standalone output) tagged with the commit, pushes it like the MCP image, and:

```bash
gcloud run deploy swiss-nav-web --image … --region europe-west6 \
  --service-account swiss-nav-web@$PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated --min-instances 0 --max-instances 2 \
  --cpu 1 --memory 512Mi --concurrency 40 --timeout 300 --cpu-boost \
  --execution-environment gen2 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=…,AGENT_RUNTIME_ID=…,AGENT_LOCATION=europe-west6,SWISS_LAW_MCP_URL=<mcp>/mcp,USER_DAILY_QUOTA=10,GLOBAL_DAILY_CAP=20,FIRESTORE_DATABASE=swiss-nav \
  --set-secrets ACCESS_CODE=swiss-nav-access-code:latest --labels app=swiss-nav,commit=<sha>
```

  then checks `/api/health` and that `/api/quota` answers 401 without the
  cookie.
- **Service (2026-10-16):** https://swiss-nav-web-mdyqt5hgsq-oa.a.run.app
  (also `https://swiss-nav-web-286937397059.europe-west6.run.app`).
- **Timeout 300 s:** answers take 30–90 s and up to ~3 min at p95.
- **Cost guard:** `GLOBAL_DAILY_CAP` (default 20 questions per Zürich day,
  ~CHF 0.7/day of model calls at most) and `USER_DAILY_QUOTA` (10). Firestore
  and Cloud Run stay in the free tiers at demo traffic.
- **Memory (M7):** `/api/memory` GET (switch + remembered profile), POST
  (switch; cookie `nav_memory` holds the visitor's own id, so a new identity
  never inherits it) and DELETE (Forget me). Memories are listed and purged
  through Memory Bank REST (`v1beta1/…/memories`, filter
  `scope.user_id="web-…"`); the visitor's sessions are listed and deleted
  through the Sessions REST API (`v1beta1/…/sessions`, filter
  `user_id="web-…"`), which needs no agent container: `async_list_sessions`
  through `:query` took 23 s from idle, REST 0.25 s. REST delete doesn't
  check the owner, so only ids from that filtered list go there; "New
  conversation" keeps ADK's `async_delete_session`. The SA's
  `roles/aiplatform.user` covers both.
- **Local:** `make web-install`, then `make web-dev` (Next.js dev server on
  :3000 against `AGENT_RUNTIME_ID` with ADC; quotas in memory; access code
  `WEB_ACCESS_CODE` or `local-dev-code`). `make web-check` = what CI runs.
- **npm:** the lock is made by npm 11.6.2 (npm 10 can't resolve it, ADR-028).
  To add or bump a package, change `web/package.json`, delete the lock and run
  `npx -y npm@11.6.2 install --before=<date two weeks ago>`; incremental
  installs have left the lock inconsistent.

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

Quota refused on 2026-10-16 (§ above, ADR-026); kept for reference.

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
| Agent Runtime | Billing catalog (2026-10-16, `global` SKUs): "Agent Platform Compute" first 50 vCPU-h/month free, then USD 0.085/vCPU-h; "Agent Platform Memory" first 100 GiB-h free, then USD 0.009/GiB-h. Scale to zero at 1 vCPU / 2 GiB (ADR-027) | ~0 CHF at eval/demo traffic; ~USD 70/month if one instance stayed up |
| Sessions + Memory Bank | pricing PDF (2026-09): USD 0.25 per 1k memories stored per month, 0.50 per 1k retrieved, storage USD 0.30/GiB-month; plus the extraction model's tokens (~1 small Flash call per opted-in turn); verify | < 1 CHF at demo traffic |
| Gemini Flash | tokens; an answer ≈ 4–6 LLM calls × 5–10k input tokens | ~0.5–2 Rp. per answer (verify pricing) |
| Embeddings | one-time corpus embed (~30k chunks) + per query | < 2 CHF build, negligible per query |
| Cloud Run (MCP, web) | scale to zero | ~0–3 CHF |
| Model Armor | ~150 tokens per screened question; 2M tokens/month free, then USD 0.10/1M (2026-10-19) | 0 CHF at demo traffic; the E7 eval used ~245k tokens |
| Apertus GPU (L4) | per-second while running; scale to zero | ~1 CHF/h while active; eval runs only |
| Full eval matrix run | ~150 cases × 5 configs + judge | ~5–20 CHF per run |

Put the real numbers in `evals/pricing.yaml` with a "checked on" date, and let
eval reports compute CHF per answer.
