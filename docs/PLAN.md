# Build plan

Work top to bottom. Each milestone ends in a merged PR whose description lists
what was verified. Update the status table in the same PR.

## Status

| # | Milestone | Status | PR / notes |
|---|---|---|---|
| M0 | Bootstrap: tooling, CI, GCP project | ✅ done | [#1](https://github.com/nikext/swiss-admin-navigator/pull/1). Gemini isn't served in europe-west6, so model endpoints are `eu`/`global` (ADR-013) |
| M1 | Corpus pipeline: Fedlex → `articles.jsonl` | ✅ done | #2. 23 acts, 18,396 records; spot-check vs Fedlex HTML 10/10 + 100/100 (DATA.md §6–7, ADR-014) |
| M2 | Index + swiss-law MCP server (local → Cloud Run) | ✅ done | #3. E4: dense R@8 98.5 on 102 queries, hybrid −13.7 (ADR-016); public at https://swiss-nav-mcp-mdyqt5hgsq-oa.a.run.app/mcp; cold start 2.07 s instance / 2.64 s first response / 3.89 s first search result (ADR-017) |
| M3 | `navigator_v1` single agent (local) + eval harness v0 | ✅ done | #4. On 30 **draft** cases: quote fidelity 108/108, hallucinated citations 0, groundedness 80.7, behaviour 93.3, CHF 0.036 and p50 35 s per answer (ADR-018/019). Drafts await Nikola's verification → golden |
| M4 | Golden set (150) + CI eval gates | ✅ done | #5. Golden 150 (model-verified by Claude at Nikola's request, ADR-024): quote fidelity 99.4% (539/542, misses = treaty-annex citation bug #6), hallucinated 0, req. recall 96.5, groundedness 78.6, key facts 95.5, behaviour 98.0, CHF 0.038 and p50 41 s per answer. Adversarial 50: fidelity 100%, behaviour 96. Multi-turn 25/25 (0.97). Judge `gemini-3.8-flash@global` (ADR-023), thinking stays default (ADR-025). CI eval-smoke live via WIF (CHF 0.67/run). M4 spend ≈ CHF 20 of 25 (incl. the ADR-026 judge study and the #7 fix with its CI runs) |
|  | *Follow-ups from M4* | | Nikola spot-checks ~20 golden cases (ADR-024); Claude quota refused, so open models were studied instead and Flash stays (ADR-026, cross-family check on golden: 1 must_not violation the judge missed, #7, fixed: prompt rule + verifier contact check, cantonal re-run clean); human judge labels would make agreement independent of every model family; only 6 clarification cases, draft more; fix annex citations (#6); agent client retries on 429/503 (CI flake).
| M5 | Deploy to Agent Runtime + Sessions + tracing | ✅ done | #10. `make deploy-agent` (staged folder, Python 3.11 import check, scale to zero at 1 vCPU / 2 GiB: the default would cost ~USD 270/month), instance `5798067860890714112` in europe-west6 as `swiss-nav-agent@`. Deployed vs local smoke: fidelity 61/61 vs 70/70, 0 hallucinated, groundedness 78.5 vs 84.8 (CIs overlap), behaviour 95 both, p50 66 vs 69 s, CHF 0.030 vs 0.034. Traces: `invoke_agent` → `call_llm`/`generate_content` + `execute_tool` spans in Cloud Trace. Cold start 9.8 s to first event (ADR-027) |
|  | *Follow-ups from M5* | | Model client retries on 429/503 (a Gemini `eu` 503 ended one remote case); redeploy once to apply `--display_name` (instance still shows "navigator"); CLAUDE.md's command list still marks `deploy-agent` as todo and lacks `eval-smoke-remote`/`query-remote` (Nikola edits CLAUDE.md). |
| M6 | Web UI + BFF on Cloud Run | ✅ done | #11 (ADR-028). https://swiss-nav-web-mdyqt5hgsq-oa.a.run.app behind an access code (Secret Manager); Next.js BFF relays Agent Runtime as SSE progress + answer; Firestore quotas 10/visitor and 20/day overall (≈ CHF 0.7/day max). Phone Q&A on Cloud Run: 70.7 s, 4 citations, verification passed, counted in Firestore. Unauthenticated API → 401. Lighthouse a11y 100, axe 0 violations, 40 unit tests |
|  | *Follow-ups from M6* | | Model client retries on 429/503 still open (M4/M5); CLAUDE.md command list lacks `web-*`, `gcp-web`, `deploy-web` (Nikola edits CLAUDE.md); `roles/datastore.user` is project-wide on a shared project (could be conditioned on the `swiss-nav` database); admin trace link from the UI (ARCHITECTURE §2) not built. |
| M7 | Memory Bank (opt-in) + memory evals | ✅ done | #12 (ADR-029). Structured profile whose schema is the whitelist (NL memories, revisions off, TTL 30 d); opt-in = session state set by the BFF. E8 on `memory.jsonl` (20 extract + 6 e2e, model-verified): Memory Bank defaults pass **2/13** privacy cases (stored diagnoses, a conviction, names, religion); custom topics 39/39 and structured profile **39/39** over 3 runs (recall 97–99% vs 100%), profile chosen for structural guarantees. E2E 6/6, privacy 4/4 (no opt-in → 0 writes/0 reads; Forget me → empty). Extraction model gemini-3.8-flash@global: ~10 s vs 281–360 s default. Web: switch, "What I remember", Forget me (also on sign-out); axe 0 violations light/dark at phone width. Agent deployed at 64d6e77: live, an opted-in turn's profile was in the served bank after ~30 s (scope `app_name: navigator`, no diabetes), the next session used it without asking, purge left nothing. CI smoke unchanged (fidelity 56/56, p50 44 s, CHF 0.032). Web deployed at 4afb9a1 (revision 00003): `/api/memory` GET/POST/DELETE answer 401 without the session cookie, also with a forged `nav_memory` cookie. M7 spend ≈ CHF 1.6 of 10 |
|  | *Follow-ups from M7* | | Live check done by Nikola (2026-10-16): "I live in canton St. Gallen" was stored as `canton: SG` and a new conversation used it. Whitelist gap he found: residence duration ("6 years in CH") is not storable, yet it decides C permit and naturalisation; add an arrival-year field (not "years", which goes stale) with new memory cases (need Nikola's go-ahead to model-verify), re-apply the config, redeploy agent + web; Nikola adds the M7 agreements (eval instance, CHF 10 cap, model-verified memory cases) to CLAUDE.md's session settings and `eval-memory`/`memory-bank` to its command list; decide whether to commit or ignore `web/AGENTS.md`/`web/CLAUDE.md` that `next dev` writes; employment from salary mentions is missed (mem-06); answer latency spiked to p50 232 s on the `eu` endpoint during the final e2e run (CI smoke an hour later: p50 44 s; transient). |
| M8 | `navigator_v2` multi-agent + verifier, A/B (E2) | 🔄 in progress | |
|  | *Next up (2026-10-19)* | | E2/E6 arms running on golden + adversarial (200 cases each): `e2-v1-claims` and `e2-v2-claims` (`answer_eval --agent v1|v2 --claim-check --case-timeout 600 --traces data/logs/<name>.traces.jsonl`, all locations `global`). The 2026-10-16 runs were lost to a shutdown, hence `--traces`: if cut off again, rerun the same command and it resumes. Then derive the no-verifier and v1-verifier arms (`derive.py`), cross-grade with Qwen3, write RESULTS.md + ADR-034. M8 model spend cap CHF 30, agreed with Nikola 2026-10-19 (re-run ≈ CHF 25). |
| M9 | Model comparison incl. Apertus + Claude via Model Garden (E1) | ⬜ todo | |
| M10 | Security hardening: Model Armor, injection evals, limits | ⬜ todo | From M6: the MCP server rate-limits on the *first* `X-Forwarded-For` hop, which a client can forge (Cloud Run appends the real IP last; the web BFF uses the last hop). |
| M11 | Showcase: README results, demo video, write-up | ⬜ todo | |

Legend: ⬜ todo · 🟨 in progress · ✅ done · ⏭️ skipped (say why)

---

## M0: Bootstrap

**Goal:** an empty but working skeleton. CI is green and GCP is reachable.

Tasks
- Install `uv` user-local if missing (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
  It is not installed on the machine as of 2026-10-15.
- Create the uv workspace (Python 3.12) with members `ingest/`, `mcp_server/`,
  `agents/navigator/` and `evals/`, plus shared dev deps (ruff, pyright, pytest,
  pytest-asyncio).
- Pin `google-adk` (latest 2.x; 2.12.0 as of 2026-10-13) and record it in
  DECISIONS.md if it differs.
- `Makefile` targets: `setup`, `lint`, `test`, `ingest`, `index`, `mcp-dev`,
  `agent-dev` (`adk web`), `eval-smoke`, `eval-full`, and `deploy-*`.
- pre-commit: ruff, ruff-format, end-of-file and trailing-whitespace hooks,
  and a check that no `.env` or `*.json` key files get committed.
- GitHub Actions `ci.yml`: lint + typecheck + unit tests on PRs.
- GCP (**with the user**): choose the project (GCP.md §2), run
  `infra/setup.sh` (APIs, Artifact Registry, bucket, SAs), and set a budget
  alert at CHF 30/month.
- Re-verify the model IDs on the Agent Platform locations page and update
  `profiles/default.yaml`.

Done when: `make lint test` passes locally and in CI, and `gcloud ai models list`
(or an equivalent smoke call to Gemini in europe-west6) works with ADC.

## M1: Corpus pipeline

**Goal:** `make ingest` produces `data/articles.jsonl` for all 23 acts in all
available languages, plus a committed `corpus/manifest.lock.json`.

Tasks (details in DATA.md)
- `ingest/resolve.py`: run `latest_consolidations.rq` with AS_OF=today and
  `consolidation_files.rq` per act, then write the lock file with URLs and
  sha256.
- `ingest/download.py`: cached, polite (1 request/s), retries with backoff.
- `ingest/parse.py`: Akoma Ntoso → article records (eId ↔ label mapping,
  heading path, footnotes split out, repealed flag, refs, deep-link URL).
- Fixtures: commit small XML excerpts (a few articles each from OR, AIG and
  ZGB, including `art_271_a` and `art_329_g_bis`, a repealed article, and a
  blockList) under `ingest/tests/fixtures/`.
- Unit tests: label ↔ eId round trip, footnote stripping, heading path,
  repealed detection, and URL format.
- Stats report: article counts per act and language. Compare them against
  Fedlex as a sanity check (OR has 1,685 `<article>` elements in DE).

Done when: tests pass, the counts look sane, ten random articles are spot-checked
against fedlex.admin.ch (text and URL), and the lock file is committed.

## M2: Index + MCP server

**Goal:** a public MCP server with the five tools (AGENTS.md §2), running
locally and on Cloud Run, usable from Claude Code as a sanity client.

Tasks
- `ingest/index.py`: contextual chunk headers, embeddings (batch, cached by
  hash), and SQLite (`articles`, FTS5, vectors, `toc`, `abbreviations`,
  `meta`).
- Build `evals/datasets/retrieval.jsonl` (start with 50 queries, grow to 200)
  and run **experiment E4** (BM25 vs dense vs hybrid; tokenizers; chunk
  headers). Pick the default by measurement and record the numbers in
  DECISIONS.md.
- `mcp_server/`: `MCPServer` (the `mcp` 2.x name for FastMCP), stateless
  Streamable HTTP at `/mcp`, stdio for local, an in-app per-IP rate limit on
  `search_law`, structured JSON logs, and `/health` (Cloud Run reserves
  `/healthz`; ADR-017).
- `resolve_citation`: a parser for DE/FR/IT citation styles with ≥ 40
  unit-test cases ("Art. 271a Abs. 1 lit. a OR", "art. 271a al. 1 let. a CO",
  "art. 30 cpv. 1 lett. a LStrI", "Art. 329g bis OR").
- Dockerfile with the index baked in (built from the repo root). Deploy to
  Cloud Run gen2 with `make deploy-mcp` (GCP.md §4, ask first).
- Add the server to Claude Code (`claude mcp add --transport http swiss-law <url>/mcp`)
  and test a few questions by hand.

Done when: retrieval recall@8 ≥ 0.85 on `retrieval.jsonl` (adjust the target
after the first measurement and document why), the Cloud Run URL works from
Claude Code, and cold start is under 5 s.

## M3: `navigator_v1` + eval harness v0

**Goal:** a single ADK agent that answers with the JSON contract, running
locally in `adk web`. First numbers.

Tasks
- `agents/navigator/agent.py`: `LlmAgent` with a synchronous `McpToolset`
  (`StreamableHTTPConnectionParams` → local or Cloud Run MCP) and
  `tool_filter`. The prompt lives in `prompts/system.md`. Model from the
  profile.
- Answer contract: structured output (verify that tools and output_schema can
  be combined in the pinned ADK version) or a final formatting step.
- Deterministic citation check as an `after_agent_callback`: re-fetch the
  cited articles and substring-check the quotes. On failure, retry once with
  feedback.
- `evals/harness/`: run cases against the agent (local runner first),
  parse the JSON, compute the deterministic metrics, call the judge for
  groundedness and key facts, and write a JSON + Markdown report.
- 30 hand-written golden cases across domains and languages to start.

Done when: `make eval-smoke` runs end to end and produces a report, quote
fidelity is 100%, and hallucinated citations are 0 on the 30 cases.

## M4: Golden set + CI gates

**Goal:** a trustworthy measuring stick.

Tasks
- **From M3 (ADR-019):** Nikola verifies the 30 drafts in
  `evals/datasets/drafts/golden.jsonl` and moves them to `golden.jsonl`
  (disputed labels: social-05, adversarial-01). A smoke run costs ~CHF 1.4
  against the CHF 0.50 goal: pick a cheaper CI judge (check its agreement on
  the human labels), a lower thinking level, or fewer CI cases. Fix the judge
  counting "Art. X does not exist" as an unsupported claim.
- Grow golden to 150 (EVALS.md §1), plus adversarial (50) and silver
  (300–500). Topic checklist:
  - **Residence:** L/B/C permits and their conditions, family reunification,
    permit after job loss, C-permit timeline, EU/EFTA vs third-country,
    change of canton, absence abroad.
  - **Citizenship:** residence years, integration criteria, the role of
    the C permit.
  - **Registration:** the federal frame (RHG) plus a cantonal pointer.
  - **Work:** probation, notice periods, termination during illness or
    pregnancy (protection periods), overtime vs extra time, holidays,
    references, non-compete.
  - **Social insurance:** AHV contributions, unemployment eligibility,
    maternity and paternity allowance, mandatory health insurance and the
    3-month deadline.
  - **Housing:** deposit cap, rent increase challenges, reference interest
    rate, retaliatory termination, defects, early move-out with a
    replacement tenant.
  - **Tax:** Quellensteuer basics, subsequent ordinary assessment (NOV)
    thresholds, federal vs cantonal.
  - **Mobility:** foreign licence exchange deadline, vehicle registration.
- Wire up `adk eval` for `multiturn.evalset.json` (user simulation).
- CI: retrieval + 20-case smoke on every PR (WIF auth, cost logged), and a
  full eval on the `full-eval` label that comments the report on the PR.
- Human-label 30 cases to measure judge agreement.

Done when: CI gates are active, judge agreement is reported, and the baseline
numbers for v1 are recorded in `evals/reports/` and summarised in the README.

## M5: Agent Runtime deployment

**Goal:** the agent runs managed in europe-west6 with Sessions and tracing.

Tasks
- `adk deploy agent_engine` (GCP.md §4, ask first). Store the resource ID.
- Pass config (MCP URL, profile) through env. Verify the mechanism.
- Enable tracing to Cloud Trace and confirm the tool spans are visible.
- `scripts/query_remote.py`: a streaming query against the deployed agent.
- Run the smoke eval against the **deployed** agent too (a harness target
  flag).

Done when: the remote smoke eval matches local within noise, and the traces
show model and tool spans.

## M6: Web UI

**Goal:** a demo people can use.

Tasks
- Next.js (App Router, TS) in `web/`. The BFF route calls Agent Runtime
  `:streamQuery` with the `swiss-nav-web@` SA and relays SSE to the browser.
- UI: chat with streaming; citation chips that open a side panel with the
  article text (from MCP `get_article`, original plus "unofficial translation"
  label, and a link to Fedlex); "as of" dates; a language switcher; an
  example-questions gallery; a permanent "Unofficial. Not legal advice"
  notice; feedback thumbs.
- Access code (Secret Manager) plus per-user daily quota and a global daily
  cap (Firestore counters).
- No official Swiss branding (ADR-010).
- Lighthouse a11y ≥ 90, mobile-first.

Done when: deployed on Cloud Run, a full Q&A works on a phone, and quotas and
the access code are enforced.

## M7: Memory Bank

**Goal:** opt-in personalisation done right (AGENTS.md §5).

Tasks
- `VertexAiMemoryBankService` wired up, with `preload_memory`, and saving
  gated on opt-in.
- Restrict extraction to whitelisted topics (verify the Memory Bank
  customisation API).
- UI: an opt-in toggle, a "What I remember" panel, and "Forget me".
- `memory.jsonl` + multi-turn evals: recall across sessions, nothing saved
  without opt-in, sensitive facts never stored, and deletion works.

Done when: the memory evals pass 100% on the privacy cases.

## M8: Multi-agent + verifier (E2, E6)

**Goal:** a data-backed answer to "is multi-agent worth it here?"

Tasks
- Build `navigator_v2` (AGENTS.md §4) as a separate agent package so v1 stays
  deployable.
- Run E2 (v1 vs v2) and E6 (verifier on/off) on golden + adversarial.
- Adopt v2 only if it wins. Write it up either way.

Done when: the experiment tables are in `docs/RESULTS.md` and DECISIONS.md is
updated.

## M9: Model comparison (E1, E3, E5)

**Goal:** the headline results table.

Tasks
- Apertus spike (GCP.md §4): Model Garden first, then Cloud Run GPU. Get it
  working with tools (non-thinking) and as answer-writer only.
- Claude in Model Garden: the quota was refused on 2026-10-16 (ADR-026). Use
  open models on MaaS (Qwen3, DeepSeek, GLM, gpt-oss; `global`) as the
  non-Google contenders unless a Claude quota is granted later.
- Run E1 (models × quality, cost, latency), E3 (tree navigation) and E5
  (languages).
- Ensure every GPU or endpoint resource is torn down after the runs. Verify
  with `gcloud run services list` and `gcloud ai endpoints list`.

Done when: `docs/RESULTS.md` has tables with CIs and cost per answer in CHF,
and no GPU resources are left running.

## M10: Security hardening (E7)

Tasks
- Model Armor on user input (and optionally tool output). Measure the block
  rate on adversarial cases and false positives on golden.
- Review MCP server rate limits, max instances, and logging of abuse.
- Stretch: Agent Gateway in front of the MCP server, with an audit log
  screenshot.

## M11: Showcase

- README: a one-paragraph pitch, a GIF/video, the architecture diagram, a
  results table (top 3 numbers), "what I learned", and links to the docs.
- A 2–3 minute demo video: a question in FR → cited answer → open article →
  memory → trace view.
- A blog post (dev.to / personal site): "Grounded legal QA over Swiss law with
  ADK, MCP and Agent Runtime — and what the evals said."
- CV bullets, numbers-driven. Templates (fill in real values):
  - "Built a multilingual (DE/FR/IT/EN) agent over 23 Swiss federal acts on
    Gemini Enterprise Agent Platform (ADK, Agent Runtime, Memory Bank) with a
    public MCP server; 0 hallucinated citations and X% key-fact accuracy on a
    150-case human-verified eval set."
  - "Benchmarked Gemini, Claude (Model Garden) and self-hosted Apertus (vLLM
    on Cloud Run GPU) for cost, latency and groundedness; chose X at Y CHF per
    answer."
  - "Eval-gated CI (GitHub Actions + WIF) blocking retrieval and
    citation-fidelity regressions."
- Add the project to the portfolio site (`nikext/portfolio2`).

## Stretch backlog (only after M11)

- **A2A:** expose the navigator as an A2A agent (ADK `to_a2a`) with an agent
  card, and demo another agent delegating to it.
- **Voice:** a Gemini Live API voice mode (ADK streaming) for spoken
  questions.
- **Zürich cantonal law:** evaluate sources (ZH-Lex; the openlex HF dataset is
  CC-BY-SA, so check the license implications).
- **Monthly refresh:** Cloud Scheduler → Cloud Build rebuilds the index, opens
  a PR with the lock diff, runs the full eval, then deploys.
- **Terraform** for all infra.
- **Online evaluation** with Agent Platform Agent Evaluation on live traffic.
