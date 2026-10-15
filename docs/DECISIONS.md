# Decision log (ADRs)

Short ADRs. Add new ones at the bottom. When a decision is revisited, mark the
old one **Superseded by ADR-0xx**. Never delete.

---

### ADR-001: v1 corpus is Swiss federal law from Fedlex only
**Status:** accepted (2026-10-15)
**Context:** We need an authoritative, legally reusable, machine-readable
source. Fedlex offers SPARQL + Akoma Ntoso XML, and federal enactments are not
copyrighted (Art. 5 URG). ch.ch has no verified reuse terms. Cantonal law
(ZH-Lex) has no verified official API.
**Decision:** Ingest the 23 federal acts in `corpus/acts.yaml`. Cantonal and
communal questions get a pointer to the competent authority (curated link
list), never invented rules.
**Consequences:** The scope is honest and defensible. Answers to cantonal
questions are partial by design, which is measured as the `cantonal_pointer`
eval category.

### ADR-002: Retrieval index = SQLite (FTS5 + vectors) baked into the MCP image
**Status:** accepted
**Context:** ~30k article-language records. Vertex AI Vector Search and RAG
Engine carry a cost floor and ops overhead out of proportion for a corpus this
size.
**Decision:** Build `index.sqlite` offline with FTS5 for BM25, sqlite-vec or
numpy for dense vectors, and TOC tables. Bake it into the Cloud Run image (the
same pattern as `zuri-sunny`).
**Consequences:** No idle cost, reproducible builds, and fast cold starts.
Revisit if the corpus grows by 10× or needs live updates. Mention "why not
Vector Search" in the README; it shows judgment.

### ADR-003: The MCP server is the retrieval boundary, and it is public and read-only
**Status:** accepted
**Context:** We want retrieval reusable by any MCP client and testable
independently of the agent. MCP is the de facto tool protocol.
**Decision:** A standalone FastMCP server (Streamable HTTP) on Cloud Run,
unauthenticated, read-only, serving public-domain law text. `search_law` is
rate-limited per IP, and `max-instances` is capped.
**Consequences:** No auth plumbing between Agent Runtime and Cloud Run. Anyone
can plug Swiss federal law into Claude, which is a nice secondary artifact. The
risk is embedding-cost abuse, mitigated by rate limits, caching and the cap.

### ADR-004: Agent hosting = Agent Runtime in europe-west6
**Status:** accepted
**Context:** Options were Agent Runtime (managed), ADK on Cloud Run, or GKE.
The project's goal includes showcasing Gemini Enterprise Agent Platform.
Runtime, Sessions and Memory Bank are all available in europe-west6.
**Decision:** Agent Runtime, deployed with `adk deploy agent_engine` in
europe-west6, using regional Gemini endpoints. **The model-endpoint part is
superseded by ADR-013** (Gemini isn't served in europe-west6; we use `eu`).
**Consequences:** Managed Sessions, Memory Bank and tracing. Some lock-in.
Keep the agent code framework-standard so `adk api_server` on Cloud Run
remains a fallback.

### ADR-005: Baseline single agent first, multi-agent only if evals justify it
**Status:** accepted
**Decision:** `navigator_v1` (single `LlmAgent`) ships first.
`navigator_v2` (router + specialists + verifier) is built in M8 and adopted
only if it wins experiment E2.
**Consequences:** We avoid premature complexity and get a data-backed
architecture story.

### ADR-006: Apertus is self-hosted on Cloud Run GPU in europe-west4, after a Model Garden spike
**Status:** proposed (finalise in M9)
**Context:** There's a sovereignty angle (Swiss open model, Apache-2.0).
Cloud Run GPUs aren't offered in europe-west6. The model needs the swiss-ai
vLLM fork. Tool calling works only in non-thinking mode.
**Decision:** First try Model Garden HF deploy. Fall back to Cloud Run GPU (L4,
scale-to-zero) with the mirrored fork image. Use it only in eval experiments
and in an optional "sovereign mode" UI toggle.
**Consequences:** The write-up must state honestly that GPU inference runs in
the Netherlands.

### ADR-007: Memory is opt-in, minimal, inspectable, deletable
**Status:** accepted
**Decision:** Memory Bank stores only whitelisted profile facts (AGENTS.md
§5), and only after an explicit opt-in. The UI shows a "What I remember" panel
and a "Forget me" button.
**Consequences:** Trust and DSG-friendly design, which is a talking point.
Needs memory evals (`memory.jsonl`).

### ADR-008: Model IDs live in config, and eval reports record them
**Status:** accepted
**Context:** Gemini IDs change monthly (on 2026-10-15 the list included
`gemini-3.8-flash`, `gemini-3.1-pro-preview` and `gemini-4-argon`).
**Decision:** No model ID literals in agent code. Profiles are in
`agents/navigator/profiles/*.yaml`. Every eval report embeds the resolved IDs.

### ADR-009: Tooling = Python 3.12 + uv workspace, Next.js for web, Apache-2.0
**Status:** accepted
**Context:** ADK needs Python ≥ 3.11. The local machine has Python 3.14, and
the Agent Runtime supported versions are unverified, so pick a conservative
3.12 and let uv manage it. The user is fluent in Next.js/React/TypeScript.
**Decision:** A uv workspace with packages `ingest`, `mcp_server`,
`agents/navigator` and `evals`. `web/` is Next.js (App Router, TypeScript).
Lint with ruff, type-check with pyright, test with pytest. License is
Apache-2.0 (matches ADK and Apertus).

### ADR-010: Not affiliated, not official-looking
**Status:** accepted
**Decision:** No Swiss cross, coat of arms, admin.ch styling or "official"
wording. The UI, README and every answer carry "Unofficial. Not legal advice.
Sources: Fedlex." The app links users to official offices for decisions.
**Consequences:** No impersonation risk. This is a deliberate trust and safety
point in the write-up.

### ADR-011: Workspace members are virtual uv projects; code imports from the repo root
**Status:** accepted (2026-10-15, M0)
**Context:** ADR-009 calls for a uv workspace with `ingest`, `mcp_server`,
`agents/navigator` and `evals`. The deployable units must stay
self-contained directories: `adk deploy agent_engine agents/navigator`
uploads only that folder, `adk web agents` discovers apps by subdirectory,
and `gcloud run deploy --source mcp_server` builds from that folder. A
src-layout package per member (`ingest/src/ingest/…`) would fight the paths
the docs and the ADK tooling expect.
**Decision:** Each member has a `pyproject.toml` without a `[build-system]`,
so uv treats it as a virtual project. It declares that component's runtime
deps, all members share one lockfile and one `.venv`, and nothing is built or
installed. Code is imported from the repo root (`ingest.parse`,
`agents.navigator.config`; pytest uses `pythonpath = ["."]`). A deploy gets
its pinned requirements from `uv export --package <member> --no-dev`
(verified: 48 pins for the navigator, with no editable line for the member).
`agents/navigator` must not import from other repo dirs, because Agent
Runtime gets only that folder. `google-adk` is pinned to **2.12.0**, the
latest on PyPI on 2026-10-15, as the docs expected.
**Consequences:** One `uv sync --all-packages --locked` sets everything up,
and per-component dependency lists stay honest. Under `adk web`, the agent
package is imported as `navigator`; tests and scripts import it as
`agents.navigator`. Don't load both in one process.

### ADR-012: Shared GCP project, `swiss-nav` prefix, budget in USD
**Status:** accepted (2026-10-15, M0)
**Context:** The user chose the existing `random-projects-509513` over a new
project (GCP.md §2). It already runs `zuri-sunny` and `epoch-war`. Its
billing account is billed in USD, and budget filters cover a whole project,
not one app.
**Decision:** Every resource is named `swiss-nav*` and labelled
`app=swiss-nav`. That includes the service accounts (`swiss-nav-mcp@` and
so on instead of the generic `web@` in the first draft of GCP.md). The
CHF 30/month guardrail is a project-scoped budget of **USD 37** with alerts
at 50/90/100%.
**Consequences:** Teardown and cost attribution work by prefix or label. The
budget also counts the other apps' spend, so an alert doesn't necessarily
mean this project overspent. Check the billing report by label or service.
Revisit with a dedicated project if spend attribution becomes a problem.

### ADR-013: Model endpoints come from the profile: `eu` for agent + embeddings, `global` for the judge
**Status:** accepted (2026-10-15, M0). Supersedes the "regional Gemini
endpoints" part of ADR-004.
**Context:** The M0 smoke call with ADC returned 404 for every profile model
in europe-west6. A probe (2026-10-15) of `gemini-3.8-flash`,
`gemini-3.1-pro-preview`, `gemini-3.5-flash-lite`, `gemini-4-argon` and
`gemini-embedding-2` across europe-west6/3/4/1/9/8, `eu` and `global` found
**no single EU region serving any of them** to this project. Even
`gemini-2.5-flash` 404s in europe-west6; only `gemini-embedding-001` answers
there. All of them answer on `global`. All except `gemini-3.1-pro-preview`
answer on `eu`. The locations page groups models by continent ("Europe"),
not by city, so reading it as "listed for europe-west6" was wrong. The
data-residency page (updated 2026-10-15) says the `eu` endpoint keeps ML
processing within EU member states and **excludes Switzerland**, and its
Gemini table has no Zürich column.
**Decision:** Every profile role carries its own `{model, location}`. In the
default profile: agent `gemini-3.8-flash@eu`, embedding
`gemini-embedding-2@eu`, judge `gemini-3.1-pro-preview@global` (it only sees
eval data, never user questions). The agent passes the location explicitly
(`Gemini(client_kwargs={"enterprise": True, "location": …})`), so it doesn't
depend on `GOOGLE_CLOUD_LOCATION`, which stays the infrastructure region
(Agent Runtime, Cloud Run) and may be set by Agent Runtime itself. Verified
end to end: the ADK runner answered via `eu` with
`GOOGLE_CLOUD_LOCATION=europe-west6` set.
**Consequences:** The residency story becomes "agent in Zürich, model
processing in the EU", which is honest and still a talking point. `eu` may
lag `global` in model availability (e.g. the pro preview), so E1 contenders
must be checked per location. `gemini-embedding-001` is the only Zürich-served
option we found; E4 (M2) can weigh it if in-country query embedding matters.
Re-probe when Google adds europe-west6 serving.

### ADR-014: The corpus build is lock-driven and strict about article identity
**Status:** accepted (2026-10-15, M1)
**Context:** The plan had `make ingest` resolve, download and parse in one go.
That makes every build depend on what Fedlex serves that day, so the lock
file would only record what happened, not drive it. Parsing the full corpus
also showed that Fedlex's XML has real identity errors: EN ZGB has a run of
shifted eIds (`art_256` prints "Art. 255a"), and IT OR prints the range
`art_697_l_697_m` as "Art. 697l".
**Decision:**
1. `make resolve` is the only step that asks Fedlex what's current. It writes
   the lock with url and sha256 per file. `make ingest` builds from the
   committed lock only, and a sha mismatch is an error.
2. A record is emitted only when its eId agrees with its printed number
   (structural comparison, connectors ignored). Disagreements are dropped and
   listed in the committed `corpus/stats.md`, never repaired by guessing
   (a first heuristic "repair" would have mislabelled IT OR's truncated range).
3. Article status is three-way (`in_force`, `repealed`, `omitted`), because
   "…" placeholders for spent amendment provisions are not repeals.
4. Romansh is not ingested; DE/FR/IT/EN only.
**Consequences:** Builds are reproducible and diffable. A Fedlex fix to the EN
ZGB shows up as a stats diff on the next `make resolve`. We lose 10 of 18,406
records (9 unofficial EN, 1 repealed IT range), and every answer stays
citable to the right number. Verified by `make spotcheck` against Fedlex's
HTML manifestation (DATA.md §7).

### ADR-015: Embedding input formats come from the profile; vectors are cached at full size
**Status:** accepted (2026-10-15, M2)
**Context:** DATA.md assumed `task_type` (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY)
for the embedding model. A live probe (2026-10-15) showed that
`gemini-embedding-2@eu` **accepts `task_type` but ignores it** (identical
vectors), and that a request with several texts returns **one fused
vector**, not one per text. Google's docs for this model describe task
instructions in the text instead: `task: search result | query: …` for
queries and `title: … | text: …` for documents. `gemini-embedding-001`
(the only embedding model served in europe-west6) honours `task_type`,
batches, and returns unnormalised vectors below 3072 dims.
**Decision:** The profile's embedding role gets `input_format:
instruction | task_type` (default `instruction`; `EMBEDDING_INPUT_FORMAT`
overrides it). `ingest/embed.py` sends one text per request for
`instruction` models and batches `task_type` ones. Vectors are requested at
full size (3072), L2-normalised, and cached in `data/embed_cache.sqlite` by
sha256 of (model, format, kind, title, text). Smaller dimensions are
Matryoshka truncations made at index time; verified: truncating the 3072
vector to 768 and re-normalising equals the API's own 768-dim output
(cosine 1.000). Every vector space records model, location, input format,
query template and dims in the index `meta`, and the MCP server embeds
queries from that record, so it needs no model ID (ADR-008) and can never
query an index with the wrong model.
**Consequences:** Rebuilding an index from cached vectors costs nothing and
takes seconds (`make index`: 2 s). Costs measured for M2 (USD 0.20/1M
tokens for emb-2, 0.15 for emb-001, third-party price trackers; Google's
page did not render): emb-2 with headers 3.90M tokens, without headers
2.51M, emb-001 with headers 3.81M: about **USD 1.85** in total, 13 min.

### ADR-016: search_law is dense retrieval; BM25 is only the fallback (E4)
**Status:** accepted (2026-10-15, M2). Revises the "hybrid (BM25 + vectors)"
assumption in AGENTS.md §2 and the README.
**Context:** Experiment E4 (EVALS.md §4) on `retrieval.jsonl`: 102 queries
(55 everyday questions + 47 harder ones: long-tail articles, keyword style,
EN questions about acts without EN text), DE 29 / EN 32 / FR 23 / IT 18, 114
expected articles. Report: `evals/reports/2026-10-15-c756c89-e4-retrieval.md`.
Recall@8 (95% bootstrap CI) and MRR:

| config | R@8 | MRR |
|---|---|---|
| BM25 unicode61 / trigram (headers) | 48.5 / 51.0 | 0.35 / 0.33 |
| **dense gemini-embedding-2, headers, 768 dims** | **98.5 (96.1–100)** | **0.881** |
| dense emb-2, headers, 3072 dims | 99.0 | 0.890 |
| dense emb-2, no headers, 768 dims | 97.1 | 0.841 |
| dense gemini-embedding-001@europe-west6, 768 dims | 96.6 | 0.861 |
| hybrid RRF (equal weights) trigram + emb-2 768 | 84.8 | 0.541 |
| hybrid RRF, BM25 weight 0.25 | 96.6 | 0.709 |

Paired differences in recall@8: hybrid − dense **−13.7 (−20.6…−7.4)**;
3072 − 768 dims +0.5 (0…+1.5); headers on − off +1.5 (0…+3.4) dense, +6.9
(+2.9…+11.8) BM25 trigram; emb-2 − emb-001 +2.0 (0…+4.4); trigram −
unicode61 +2.5 (−1.0…+6.4). Uncached query-embedding latency from Zürich:
emb-2@eu p50 153 ms, emb-001@europe-west6 p50 151 ms.
**Decision:**
- `search_law` serves **dense** retrieval with gemini-embedding-2@eu over
  chunks with contextual headers, at **768 dims** (3072 buys +0.5 points for
  4× the vectors). Results are unique articles (chunks and language versions
  collapse).
- BM25 stays in the index (FTS5 **unicode61**, 82 MB vs 124 MB for trigram,
  1 ms vs 5 ms, no significant quality difference) as the **fallback** when
  the query embedding fails. `SEARCH_MODE=hybrid|bm25` remains for
  experiments (E3).
- Contextual headers stay on (they help every retriever).
- gemini-embedding-001 in Zürich is not worth the quality loss: the agent
  model already runs on `eu` (ADR-013), so in-country query embedding would
  not keep user questions in Switzerland, and it was not faster.
- The M2 target "recall@8 ≥ 0.85" is met with room; the CI gate becomes
  "recall@8 on retrieval.jsonl must not drop more than 2 points below the
  committed baseline (98.5)" (EVALS.md §3).
**Consequences:** Why hybrid lost here: questions are written in everyday
words while the law uses its own vocabulary, and English questions match
the unofficial EN ZGB/BV lexically, so the BM25 list is mostly noise that
equal-weight RRF lets displace good dense hits. Caveats, stated in the
report: the queries and their expected articles were drafted by the same
author (Claude), checked against article text but not by Nikola; dense is
near the ceiling, so the set must grow harder (target 200) before it can
separate dense variants. Re-run E4 (`make eval-retrieval E4=1`) when the
set grows or the embedding model changes.

### ADR-017: The MCP server ships as one image with the index, on Cloud Run gen2
**Status:** accepted (2026-10-15, M2)
**Context:** ADR-011 said `mcp_server/` would deploy with
`gcloud run deploy --source mcp_server`. But the server needs `ingest/eid.py`
(citation parsing) and the 135 MB `data/index.sqlite` (gitignored), and the
`mcp` SDK moved to 2.x (`FastMCP` → `MCPServer`; transport options moved to
`run()`/`streamable_http_app()`). First deploy on the default gen1 runtime:
the instance needed 6.0 s from "Starting new instance" to a passing startup
probe, 4.5 s of it in Python imports (~2,000 `.pyc` files; locally 1.0 s).
**Decision:**
- `mcp_server/Dockerfile` is built **from the repo root** with a whitelist
  `Dockerfile.dockerignore`; it copies `mcp_server/*.py`, `ingest/eid.py` and
  the index, installs only `uv export --package swiss-nav-mcp` pins into a
  venv with precompiled bytecode, base images pinned by digest, non-root user.
  `infra/deploy_mcp.sh` (`make deploy-mcp`) builds, tags with the commit,
  pushes with a short-lived token, deploys and smoke-tests `/health`.
- Cloud Run **gen2** execution environment, `--cpu-boost`, min 0 / max 2,
  1 vCPU / 1 GiB, concurrency 40, public (ADR-003).
- Streamable HTTP is **stateless with JSON responses**: no session affinity
  needed across two instances.
- Health is `/health`: Cloud Run itself answers `/healthz` with 404 (paths
  ending in "z" are reserved; verified on the deployed service).
- Resilience: the query embedder has a 5 s timeout and a 30 s circuit
  breaker; while open, `search_law` answers from BM25 in < 10 ms and says
  `degraded`. Privacy: JSON logs carry a salted per-process client hash, no
  IP and no query text by default.
**Measurements (2026-10-15):** gen1 deploy rollout 6.0 s (imports 4.5 s); gen2 4.1 s. A real scale-from-zero start on gen2 (log reason AUTOSCALING, 11:13 UTC): instance start -> probe OK **4.15 s** (imports 3.58, index + vectors 0.20, embedder 0.14); client-side first MCP response (initialize) **4.61 s**; first search_law +0.88 s (embedding client: token + TLS), total to the first search result 5.49 s. Second cold start (16:22 UTC, `make mcp-coldstart`, with a background embedding warm-up at startup): instance -> probe OK **5.31 s** (imports 4.49), initialize 5.81 s, first search_law +1.04 s (0.59 s server-side), first result **6.84 s**. Imports vary 3.6–4.5 s between instances. The warm-up did not help: Cloud Run throttles CPU outside requests, so it barely runs between the handshake and the first search. It was removed.

Two findings from that run:
- **The base image ships the stdlib without bytecode** (42 `.pyc` for 686 modules), and the non-root app user cannot write any, so every start recompiled asyncio, json, email, http… The Dockerfile now compiles the stdlib: server imports in the container drop from 0.83 s to 0.61 s (−27%; image +25 MB).
- **Claude Code kept the service awake.** On the 2026-07-28 protocol `MCPServer` advertises `tools.listChanged` and serves `subscriptions/listen`, so each open Claude Code session held a listen POST until the 60 s request timeout, then re-listened ("Truncated response body" in the logs, every minute). Instances never scaled to zero while a session was open, and under request-based billing an instance with a request in flight is billed in full (~USD 2.3/day). The tool list never changes, so the server now passes `subscriptions=False` (no `listChanged`, no listen stream; unit-tested).

COLDSTART_FINAL
**Consequences:** Deploys need a local `data/index.sqlite` (rebuilt in
seconds from the embedding cache, or ~USD 0.8 cold). The image is 560 MB
uncompressed. If cold start becomes a problem: drop google-genai from the
server (0.24 s of 0.99 s local import time) in favour of a plain REST call,
or keep one warm instance (min 1, billed).
