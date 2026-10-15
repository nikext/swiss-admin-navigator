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
- Startup: the image compiles the stdlib (the base image ships 42 `.pyc` for
  686 modules, and the non-root user cannot write them) and records the ~760
  files the server imports; `python -m mcp_server.preload` reads them with 32
  threads before importing. On Cloud Run small files arrive lazily, one fetch
  each, while big sequential reads are fast (53 MB of vectors in 0.1 s).
- No `subscriptions/listen` (`MCPServer(subscriptions=False)`): the tool list
  never changes, and the listen stream kept instances awake (below).

**Measurements (2026-10-15).** gen1 rollout: 6.0 s to a passing probe (imports
4.5 s); gen2: 4.1 s. Cold starts on gen2 after scale-to-zero, server phases
from the `ready` log line, client times from `make mcp-coldstart` (from Zürich;
initialize = first MCP response):

| start (UTC) | image | instance -> probe OK | imports | initialize | first search result |
|---|---|---|---|---|---|
| 11:13 autoscale | baseline | 4.15 s | 3.58 s | 4.61 s | 5.49 s |
| 16:22 autoscale | + background embedding warm-up | 5.31 s | 4.49 s | 5.81 s | 6.84 s |
| 16:31 rollout | + stdlib `.pyc`, warm-up removed | 5.11 s | 4.18 s | | |
| 16:56 rollout | + preload | 2.53 s | 0.15 + 1.63 s | | |
| **17:15 autoscale** | **served (144d3c1)** | **2.07 s** | **0.14 + 1.47 s** | **2.64 s** | **3.89 s** |

The M2 target (cold start < 5 s) is met by the served image, from the
client's point of view and including the first search. What did not work:
the background warm-up of the embedding client (Cloud Run throttles CPU
outside requests, so it barely ran between the handshake and the first
search; removed), and the stdlib bytecode alone (0.83 -> 0.61 s imports in
the container locally, but within noise on Cloud Run). The first
`search_law` of an instance still pays ~0.9 s server-side for the embedding
client's first token and TLS connection (warm: 0.17 s).

**Claude Code kept the service awake.** On the 2026-07-28 protocol
`MCPServer` advertised `tools.listChanged` and served `subscriptions/listen`
by default. Each open Claude Code session held a listen POST until the 60 s
request timeout and then re-listened ("Truncated response body" in the logs,
every minute), so the service never scaled to zero while a session was open,
and an instance with a request in flight is billed in full (~USD 2.3/day).
Fixed with `subscriptions=False` (unit-tested: no `listChanged`); since then
idle instances shut down after ~15 min.

**Consequences:** Deploys need a local `data/index.sqlite` (rebuilt in
seconds from the embedding cache, or ~USD 0.8 cold). The image is 585 MB
uncompressed. `preload.txt` is regenerated at every build, so new imports are
covered automatically. Further levers if cold start matters again: drop
google-genai from the server for a plain REST call (fewer imports and a
cheaper first embedding call), or keep one warm instance (min 1, billed).

### ADR-018: navigator_v1 = one LlmAgent with output_schema; the citation verifier is an after_model_callback with one ADK-style retry
**Status:** accepted (2026-10-15, M3). Refines AGENTS.md §3 and ARCHITECTURE.md §4.
**Context:** The plan asked for `output_schema` "if it works with tools in the
pinned ADK" and a citation check "as an `after_agent_callback` … retry once with
feedback". Checked in the google-adk 2.12.0 source and live:
- **Schema + tools.** ADK sends `response_schema` together with the tools
  when the model reports `output_schema_and_tools`. For `Gemini` that is true
  when the model id starts with `gemini-` **and** `GOOGLE_GENAI_USE_ENTERPRISE`
  (or the deprecated `GOOGLE_GENAI_USE_VERTEXAI`) is set. Our client is always
  Vertex (`client_kwargs={"enterprise": True}`), but without the env var ADK
  falls back to a `set_model_response` tool. In that path, the final answer is
  produced by the tool, so it never passes `after_model_callback`. Both paths
  were run live. LiteLLM models (Apertus, Claude in M9) always take the
  fallback.
- **Callbacks cannot retry.** Per adk.dev/callbacks, `after_agent_callback`
  can only append content. ADK 2.x points to graph/dynamic workflows instead
  of custom `BaseAgent`s, but a `Workflow` is a `BaseNode`, not a `BaseAgent`.
  Its fit with `adk eval`, Agent Runtime and Memory Bank is unverified, and
  its chat/isolation semantics are involved.
- ADK's own `ReflectAndRetryModelPlugin` retries inside an `LlmAgent`. Its
  `after_model_callback` replaces a bad response with a call to a reserved,
  undeclared tool, and that tool's response carries the guidance.
**Decision:**
- The root stays a plain `LlmAgent` (`agent.py`, `build_agent(mcp_url)`), with
  `DraftAnswer` as `output_schema` and all five MCP tools behind an explicit
  `tool_filter`.
- The contract is split. The model fills `DraftAnswer`. Code returns `Answer`
  (`contract.py`), which adds each citation's `abbr`, `url` and `as_of` from
  the fetched article, the exact source span as `quote`, a `verification`
  record, and the fixed `notice` (ADR-010). One new model field,
  `clarifying_question`, makes the clarification behaviour measurable.
- The verifier runs in `after_model_callback` (`verifier.py`). It treats any
  final submission as the answer: JSON text, or a `set_model_response` call,
  so both paths are covered and that tool never runs. It re-fetches every
  cited article over the agent's own MCP session and checks, deterministically
  (`citecheck.py`): the SR/article exists, it is in force, the quote language
  has text, the paragraph and letter exist, the quote is verbatim, and the
  quote sits in the cited paragraph. It also checks that every [n] marker has
  a citation. On a problem in the first draft, the answer is replaced by a call
  to the reserved `citation_check` tool, which carries the draft and the
  problems. That tool is registered in `before_model_callback` but never
  declared, and the call carries ADK's skip-thought-signature marker. The
  model then redrafts in the same invocation.
- After the last round (one retry), whatever is still wrong is degraded and
  recorded. Non-existent or repealed references are dropped together with
  their markers. Non-verbatim quotes are removed. A pinpoint that is off is
  moved to the paragraph that contains the quote. Confidence is set to `low`.
  Server errors never trigger a retry (`status: unavailable`).
- "Verbatim" means a substring match after normalising whitespace (any Unicode
  space), apostrophes (’ ‘ ʼ → ') and invisible characters (soft hyphen,
  zero-width). Fedlex FR/IT use ’, and models type '. An ellipsis splits the
  quote into parts that must appear in order. Quotes under 20 characters fail.
  The final quote is the exact source span.
- An `after_tool_callback` gives the model only `structuredContent`. MCP
  results carry the same JSON twice, so `get_article` OR 271a drops from
  9,577 to 4,573 characters. The toolset caches `tools/list` for an hour.
**Consequences:** It stays compatible with `adk web`, `adk eval`, Agent
Runtime and Memory Bank, and with the LiteLLM models of M9. The model sees one
call in its history that it did not make. Streaming clients see the draft
before the verified final answer, so the UI (M6) renders only the final event.
A retry is expensive: on the smoke baseline the one retried case cost
CHF 0.13 and took 152 s, against a mean of CHF 0.037. Measured on the 20-case
smoke baseline (7d081e6): first drafts had 72 citations with 2 problems in one
case (a paragraph on an unnumbered article and its misquote), which was fixed
after one retry. Nothing was dropped. The verifier cannot catch a true quote
that is attached to a claim it does not support; groundedness is the judge's
job (ADR-019).

### ADR-019: Answer eval harness v0: local runner, independent re-check, profile judge, draft cases
**Status:** accepted (2026-10-15, M3)
**Context:** EVALS.md asks for an end-to-end harness that parses the JSON
answer, computes the deterministic metrics, calls a judge, and writes JSON +
Markdown reports, with ADK's `adk eval` reserved for multi-turn sets (M4). The
30 starting cases can only be drafts: golden cases need Nikola's verification
(CLAUDE.md).
**Decision:**
- `evals/harness/answer_eval.py` (`make eval-smoke`, `make eval-full`) runs
  each case through `build_agent(url)` with ADK's `InMemoryRunner`, 4 at a
  time. By default it starts its own MCP server from the checkout on a free
  port with a relaxed rate limit (`law.local_server`), so runs neither hit the
  public server's per-IP limit (30/min) nor depend on its deploy;
  `--mcp-url` points at any other server.
- The harness does not trust the agent's verification record. It re-fetches
  every final citation over its own MCP client and applies the same
  "verbatim" definition (`citecheck.find_quote`). Quote fidelity and the
  hallucination rate are pooled over citations, with CIs that resample cases.
- The judge is the profile's `judge` role (`gemini-3.1-pro-preview@global`,
  temperature 0, structured output). It gets the full text of every cited
  article and grades claim-level groundedness (yes 1 / partly 0.5 / no 0),
  key facts, `must_not` and behaviour. The prompt (`prompts/judge.md`) is
  pinned by sha in every report. Behaviour accuracy = the deterministic rule
  for the category AND the judge's verdict. Citation precision is reported
  twice: against `expected_citations` only, and "expected or judged
  relevant".
- Language match = `language` field and `langdetect` (seeded) both equal the
  case language. Cost = tokens × `evals/pricing.yaml` (list prices from
  ai.google.dev, 2026-10-15; Vertex's page does not render; USD→CHF 0.82,
  approximate).
- Cases: `evals/datasets/drafts/golden.jsonl`, 30 drafts (DE 8, EN 8, FR 7,
  IT 7; 20 answerable, 3 clarification, 3 cantonal, 2 out of scope,
  2 adversarial; 20 tagged `smoke`, 5 per language). They were written from
  the article text and are `verified_by: null`. The harness uses `golden.jsonl`
  once it exists and marks every report built on drafts as "not a headline
  number".
**Results (drafts, not headline numbers).** Smoke baseline, prompt v1
(`7d081e6`): quote fidelity 72/72, hallucinated 0, groundedness 78.0
(70.6–84.8), key facts 98.3, behaviour 20/20, CHF 0.037/answer, p50 51 s.
All 30 cases, prompt v2 (`3e7e603`): quote fidelity **108/108**,
hallucinated citations **0**, required-citation recall 100 (n=23),
groundedness 80.7 (70.0–90.2), key facts 100, `must_not` 0, behaviour 93.3
(83.3–100), language match 100. Per answer: CHF 0.036 mean, CHF 0.13 p95,
p50 35 s, p95 129 s, 7.2 model calls, 67.7k prompt tokens (56% implicitly
cached), 4.0k thinking tokens. One case was sent back by the verifier and
passed after the retry. Prompt v2 against v1, paired on the 20 smoke cases:
groundedness −2.0 (−19.5…+11.5), key facts +1.7 (0…+5.0), cost −USD 0.003
(−0.020…+0.014). That is **no measurable effect on groundedness at n=20**.
The targeted fix did work: the clarification case that researched every branch
went from USD 0.163 to 0.031, and residence-02 no longer presents an
unverified settlement agreement as fact.
**Consequences:**
- The M3 targets (quote fidelity 100%, hallucinated citations 0) hold on all
  30 drafts. Groundedness (~80) is the weakest metric. The verifier cannot see
  it (true quotes, unsupported prose). That makes it the target for the M8
  LLM verifier and for E6.
- **Smoke cost:** a 20-case run costs about CHF 1.4 (agent 0.75, judge
  0.66), well above EVALS.md's CHF 0.50 goal. M4 must choose: a cheaper CI
  judge (with agreement measured on the human-labelled subset), a lower
  thinking level (thinking tokens are ~40% of agent cost), or fewer CI cases.
- **Latency** (p50 35–51 s, ~7 model calls with thinking) is far from chat
  speed. It matters for M6. Levers to measure: thinking level, trimming
  `get_article` output (it repeats `text` in `paragraphs`), fewer
  `resolve_citation` round trips.
- Known judge limits, for the M4 agreement study: it counts "Art. 271z OR
  does not exist" as an unsupported claim (adversarial-01 groundedness 17),
  and single-run groundedness has wide CIs.
- Draft labels the run disputes, for Nikola's review: social-05
  (clarification expected, but the agent gave a useful branching answer) and
  adversarial-01. Its first draft used Art. 999 OR, which exists (bill of
  exchange law). The agent said so and quoted it; the case now uses
  Art. 271z OR.

### ADR-020: Golden set: Claude drafts in batches, Nikola verifies in a CLI; adversarial and silver stay unverified
**Status:** accepted (2026-10-15, M4)
**Context:** M4 needs 150 human-verified golden cases (EVALS.md §1), and
only Nikola may verify them (CLAUDE.md). Agreed on 2026-10-15: all 150 are
verified before M4 closes, through a local review tool.
**Decision:**
- Claude drafts every case from the article text read from the index
  (`ingest`-built SQLite), never from memory, in topic batches of 24
  (`evals/datasets/drafts/batch-NN.jsonl`, 6 per language). New batches are new
  files, so drafting never rewrites a file that is under review.
- `make check-cases` validates schema, ids unique across all case files,
  expected citations that exist and are in force, and
  `clarification_expected` matching the category (it caught housing-20).
- `make review-golden` shows each draft with the full text of every expected
  citation (any language on `t`), key facts, must_not and notes (M3 disputes
  are flagged); `a` stamps `verified_by`/`verified_on` and moves the case to
  `golden.jsonl`, `e` edits it as JSON with validation, `r` moves it to
  `drafts/rejected.jsonl` with the reason. Every decision is an atomic write.
- Until all are verified the harness runs golden + all draft batches
  (`--dataset all`); the 20 smoke cases stay complete wherever they live, and
  reports say how many cases are verified.
- `golden.lock.json` pins a hash of every cited article's text; check-cases
  flags golden cases whose law changed (EVALS.md §1 step 5).
- `adversarial.jsonl` (50) and `silver.jsonl` (352, LLM-generated, spot-checked
  30/30) use the same schema but are not verified and never back headline
  numbers; the full eval runs adversarial next to golden.
**Consequences:** The 150 drafts hit the target spread exactly (90/22/15/13/10;
38/38/37/37). Headline numbers wait for the review (~8-12 h of Nikola's time).
Clarification cases are the contested label (social-05): the review decides
whether a complete branching answer counts as good behaviour.

### ADR-021: CI eval gates: WIF, a published index, deterministic gates, smoke only on ready PRs
**Status:** accepted (2026-10-15, M4); active once `make gcp-wif` has run and the
`GCP_*` repository variables are set.
**Context:** EVALS.md §3 asks for retrieval + a 20-case smoke on every PR with
gates on recall, quote fidelity and hallucinated citations, and a full eval on
a label. CI has no index (gitignored build artefact, 135 MB), no keys, and a
CHF 0.50 per-run goal against CHF 0.70 measured for the agent alone.
**Decision:**
- Auth by Workload Identity Federation (`infra/wif.sh`): pool
  `swiss-nav-github`, OIDC provider limited to `nikext/swiss-admin-navigator`,
  allowed to impersonate `swiss-nav-ci@` only.
- The index is published to `gs://<project>-swiss-nav/index/<sha256[:16]>/`
  (`make publish-index`); the committed pointer `evals/ci_index.json` carries
  the full sha256, and CI refuses a file that does not match.
- `eval-smoke.yml`: check-cases, retrieval eval, 20-case answer smoke, then
  `evals/harness/gate.py` against `evals/baselines.yaml`: recall@8 at most 2
  points below 98.5, quote fidelity 100 % with at least one quote, 0
  hallucinated citations, at most 1 agent error. Cost and p50 latency go to the
  job summary. It runs on non-draft PRs that touch agent, MCP, ingest or eval
  code, and skips until WIF is configured.
- The gates are deterministic, so the CI smoke can run without the judge
  (`SMOKE_ARGS` repo variable); judge scores at n=20 are too noisy to gate.
- `eval-full.yml` on the `full-eval` label: golden + drafts + adversarial,
  report above the per-case table as a PR comment, label removed afterwards.
**Consequences:** About CHF 0.70 per smoke run at the served (default) thinking
level, above the 0.50 goal; low thinking would cost 0.46 but changes the agent
under test (EVALS.md §3 table), so it is decided on golden, not for CI's sake.
Docs-only and draft PRs cost nothing. A new index needs `make publish-index` in
the same PR.

### ADR-022: Multi-turn eval through ADK AgentEvaluator with a rubric judge
**Status:** accepted (2026-10-15, M4)
**Context:** EVALS.md asks for `adk eval` with user simulation on
`multiturn.evalset.json`. Checked in google-adk 2.12.0: the `multi_turn_*_v1`
metrics delegate to the managed Vertex evaluation service (needs
`google-cloud-aiplatform[evaluation]` and a supported region);
`rubric_based_multi_turn_trajectory_quality_v1` is an ADK LLM judge; both the
user simulator and ADK's judges are built from model names on
`GOOGLE_CLOUD_LOCATION`, which is europe-west6 here (no Gemini, ADR-013).
**Decision:**
- `google-adk[eval]` in the evals package only (the agent package stays lean).
- `evals/harness/multiturn.py` builds the EvalConfig from the profile: simulator
  = agent model (thinking low), rubric judge = judge model, 1 sample, both on
  the judge's location set for this process; the agent keeps its own location.
- Per-case rubrics in the evalset; they must have type `TRAJECTORY_QUALITY`
  (ADK filters case rubrics by the evaluator's type, silently).
- The MCP URL is fixed before anything imports `agents.navigator`, because the
  package builds `root_agent` at import (two failed trial runs taught this).
- Results come from ADK's own results manager (`EvalSetResult`), and the
  report keeps every rubric verdict with the judge's rationale and transcript.
**Consequences:** Trial on mt-01 and mt-22: 2/2 passed, 7/7 rubrics, 3 turns each,
agent CHF 0.07 per conversation (simulator and judge extra). The `multi_turn_*`
metrics stay unused until there is a reason to pay for the managed service.

### ADR-023: Judge choice for CI and the baseline (proposed, pending the agreement study)
**Status:** proposed (2026-10-15, M4)
**Context:** The M3 judge (`gemini-3.1-pro-preview@global`) costs about
CHF 0.03 per answer and is the same family as the agent. Claude in Model
Garden was agreed as a candidate on 2026-10-15, but the project has zero quota
for every Claude model (`429 global_online_prediction_requests_per_base_model`,
base model anthropic-claude-haiku) until the models are enabled.
**Plan:** Nikola labels the 30 M3 answers; `make judge-study` grades them with
Gemini Pro (twice, for test-retest noise), 3.8 Flash and 3.5 Flash-Lite and,
once enabled, Claude Haiku 5.5 and Sonnet 5.5. Pick the cheapest judge whose
agreement with the human labels is not materially worse than the best one
(groundedness MAE, kappa on behaviour and key facts), prefer a different
family at equal agreement, record the numbers here, and set it in the profile.
