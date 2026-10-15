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
