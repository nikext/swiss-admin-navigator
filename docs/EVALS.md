# Evaluation

Evals are the core of this project, not an afterthought. Most portfolio agent
demos have none. The README will lead with a results table.

## 1. Datasets

All in `evals/datasets/`, versioned in git.

| Set | Size (target) | Purpose |
|---|---|---|
| `retrieval.jsonl` | 200 queries (102 on 2026-10-15) | Retrieval only: query → expected `(sr, eid)` set, matched per article regardless of language. 55 everyday + 47 `difficulty: hard` queries, DE/EN/FR/IT; expected eIds checked against the article text (drafted by Claude, not yet reviewed by Nikola). Cheap; runs on every PR. `make eval-retrieval`. |
| `golden.jsonl` | 150 cases | End-to-end QA. **Gold.** Drafted by Claude in M4 (the 30 M3 drafts plus five batches of 24: housing; work; residence/citizenship/registration; social insurance; tax/mobility/data protection) and **model-verified** by Claude Opus 5.5 against the article text on 2026-10-15 at Nikola's request (`verified_by: claude-opus-5-5`, ADR-024); not human-verified. Spread: answerable 106, clarification 6, cantonal 15, out of scope 13, adversarial 10 (clarification labels follow system-prompt rule 1, ADR-024); DE 38, EN 38, FR 37, IT 37; 20 tagged `smoke` (5 per language). Text lock: `golden.lock.json`. |
| `silver.jsonl` | 352 cases | LLM-generated from single articles (`make silver`, profile agent model, thinking low; 410 articles sampled by per-act quotas, 54 skipped as not resident-facing, 4 rejected for naming the article; CHF 0.33). Spot check of 30: key facts supported 30/30. Used for broad regression, never for headline claims. |
| `multiturn.evalset.json` | 25 sessions | ADK EvalSet with user simulation (`make eval-multiturn`): clarification then answer (12), follow-ups (6), language switches (3), pushback and out of scope (4); per-case rubrics. Memory has its own eval (`memory.jsonl`). Drafted, not verified. |
| `adversarial.jsonl` | 50 cases | Golden schema. Fake articles/paragraphs/acts (12), prompt injection direct and inside quoted e-mails, contracts, letters and fake tool output (12), impersonation (6), individual advice and acting for the user (8), unlawful requests (4), false premises and pressure (8). Drafted by Claude, not verified; part of the full eval, not of headline numbers. |
| `memory.jsonl` | 26 cases | M7 (`make eval-memory`, ADR-029). 20 **extract** cases (DE 5, EN 7, FR 5, IT 3): a conversation → the whitelisted fields expected, fields that must stay empty, and forbidden strings (13 privacy cases: health, pregnancy, HIV, conviction, salary/debt/IBAN, name/address/phone/e-mail, religion, asylum status, disability, date of birth/AHV number, registered partnership, an injected "remember" instruction, a child's diagnosis). 6 **e2e** cases run the agent across sessions: recall (2, one across languages), no opt-in → nothing saved, switch off → nothing read, sensitive facts in a real conversation, Forget me. Drafted and model-verified by Claude Opus 5.5 at Nikola's request (ADR-024 extended, ADR-029). |
| `judge_labels.jsonl` | 30 answers | Labels of the 30 M3 answers for the judge-agreement study, by Claude Opus 5.5 at Nikola's request, blind to judge verdicts (`labeled_by: claude-opus-5-5`, ADR-024). `make label-answers` adds human labels. |

### Golden case schema

```json
{
  "id": "housing-017",
  "lang": "fr",
  "question": "Mon bailleur peut-il résilier mon bail parce que j'ai demandé des réparations ?",
  "category": "answerable | needs_clarification | cantonal_pointer | out_of_scope | adversarial",
  "domain": "housing",
  "expected_citations": [{"sr": "220", "eid": "art_271_a", "required": true},
                         {"sr": "220", "eid": "art_273", "required": false}],
  "key_facts": ["termination can be challenged", "deadline 30 days to the conciliation authority"],
  "must_not": ["claims termination is automatically void", "invents a cantonal form number"],
  "clarification_expected": false,
  "smoke": true,
  "verified_by": "nikola", "verified_on": "2026-10-xx", "as_of": "2026-10-01",
  "notes": "Art. 271a para. 1 lit. a"
}
```

`smoke: true` marks the 20 cases of the PR smoke run (5 per language, all
categories). The schema is enforced by `evals/harness/cases.py` (unknown keys
are errors).

### How to build the golden set without being a lawyer

1. Collect **real question shapes**: common expat questions about permits,
   Anmeldung, leases, notice periods, Quellensteuer, AHV, health insurance, and
   licence exchange (see the topic list in PLAN.md M4).
2. For each question, find the governing articles yourself through Fedlex
   (the MCP server's `get_toc` helps) and write `expected_citations` and
   `key_facts` **from the article text**.
3. Use an LLM to *propose* candidates. A reviewer confirms each one against
   the article text and sets `verified_by` (Nikola by default; for M4 he
   delegated the review to Claude, ADR-024). Unverified cases go to `silver`.
4. Spread: 5 domains × 4 languages, with roughly 60% answerable, 15%
   clarification, 10% cantonal pointer, 15% out-of-scope/adversarial.
   Label `needs_clarification` only where system-prompt rule 1 says to ask:
   the missing fact changes the answer and a correct general answer does not
   fit in two short sentences (ADR-024).
5. Re-check `as_of` when the corpus lock changes. `make check-cases` (also in
   eval-smoke) flags golden cases whose cited articles changed text since
   `golden.lock.json` (sha256 per cited article over all languages);
   `--update-lock` rewrites the lock in the PR that verifies cases or rebuilds
   the index.

**Workflow (M4, ADR-020).** Claude drafts cases from the article text in
batches (`drafts/batch-NN.jsonl`, new batches are new files so drafting never
rewrites a file under review); `make check-cases` validates schema, unique ids,
existing in-force expected citations and the clarification label;
`make review-golden` shows each draft with the full cited article text and
moves it to `golden.jsonl` on the reviewer's key press (edit and reject
included).

## 2. Metrics

| Metric | Type | Definition |
|---|---|---|
| **Retrieval recall@k / MRR** | deterministic | Expected eids found in `search_law` top-k. |
| **Citation precision** | deterministic | Share of produced citations that exist **and** appear in `expected_citations`, or that an LLM judge rates as relevant. |
| **Required-citation recall** | deterministic | Share of `required: true` citations produced. |
| **Quote fidelity** | deterministic | Share of `quote` fields that are exact substrings of the stored article text in `quote_lang`, pooled over citations. Normalised: whitespace, apostrophes (’ → '), soft hyphens and zero-width characters; an ellipsis splits a quote into parts that must occur in order (ADR-018). Target **100%**. Reported for final answers, plus the first-draft problems the verifier caught. |
| **Hallucinated citation rate** | deterministic | Citations to non-existent SR/article combinations. Target **0**. |
| **Groundedness** | LLM judge | Each legal claim in `answer_markdown`/`cantonal_note` is supported by the full text of the articles it cites: yes 1, partly 0.5, no 0, averaged per answer (custom rubric, `evals/harness/prompts/judge.md`). Pointers to authorities and "it depends on" statements are not claims. |
| **Key-fact coverage** | LLM judge | Share of `key_facts` stated correctly. |
| **must_not violations** | LLM judge | Count. Target **0**. |
| **Behaviour accuracy** | deterministic + judge | Correct category handling. Rule: answerable = cites and does not ask; clarification = `clarifying_question` set; cantonal = `cantonal_note` set; out of scope = `out_of_scope`; adversarial = no hallucinated citation. A case counts only if the rule **and** the judge agree. |
| **Language match** | deterministic | The `language` field and `langdetect` (seeded) on `answer_markdown` both equal the question language. |
| **Safety** | ADK `safety_v1` | — |
| **Cost / latency** | measured | Tokens → CHF per answer (price table in `evals/pricing.yaml`, dated; cached input and thinking priced separately). p50/p95 latency. Model and tool-call counts. |

ADK criteria available in the pinned version (verified list from adk.dev,
2026-10-15): `tool_trajectory_avg_score`, `response_match_score`,
`final_response_match_v2`, `rubric_based_final_response_quality_v1`,
`rubric_based_tool_use_quality_v1`,
`rubric_based_multi_turn_trajectory_quality_v1`, `hallucinations_v1`,
`safety_v1`, `per_turn_user_simulator_quality_v1`,
`multi_turn_task_success_v1`, `multi_turn_trajectory_quality_v1`,
`multi_turn_tool_use_quality_v1`, plus always-on `tool_call_count_v1`,
`inference_call_count_v1`, `token_usage_v1` and `invocation_duration_v1`.
`tool_trajectory_avg_score` and the response-match criteria do **not** work with
user simulation.

**Approach:** ADK `AgentEvaluator` for multi-turn (`evals/harness/multiturn.py`,
ADR-022): an LLM-backed user simulator, navigator_v1 over a local MCP server,
and `rubric_based_multi_turn_trajectory_quality_v1` (an ADK LLM judge; per-case
rubrics must have type `TRAJECTORY_QUALITY` or ADK silently drops them). The
EvalConfig is built from the profile; simulator and judge run on the judge's
endpoint location. The `multi_turn_*_v1` metrics call the managed Vertex
evaluation service and are not used. Single-turn cases run through the custom harness
`evals/harness/answer_eval.py` (built in M3, ADR-019): it runs the agent with
the local ADK runner against its own MCP server, re-checks every final
citation over MCP itself, asks the judge, and writes
`evals/reports/<date>-<git-sha>-<name>.json` plus a Markdown summary
(headline table with CIs, verifier stats, cost and latency, per-case
findings). Reports built on drafts are named `*-drafts` and say they are not
headline numbers.

**Judge hygiene:** pin the judge model and prompt. Judge with a different model
family than the one under test where possible. Claude has no quota in this
project (ADR-026), so the cross-family judge is Qwen3 235B on MaaS: whenever a
headline number is produced, re-grade the stored answers with
`make judge-study ARGS="--report <answers.json>" JUDGES="gemini-3.8-flash@global,qwen/qwen3-235b-a22b-instruct-2507-maas@global"`
(≈ CHF 0.001 per answer for Qwen) and read its must_not and behaviour flags
by hand; the report lists them per judge. Report judge agreement on a 30-case
human-labelled subset: `make label-answers` (Nikola grades each claim of the
reference split with verdicts hidden, plus key facts, must_not, behaviour),
then `make judge-study JUDGES=...` re-grades the same stored answers with each
candidate (`model@location[:thinking]`, Gemini or Claude) and reports MAE,
bias and Spearman of groundedness, kappa on "fully grounded", key facts and
behaviour, cost and latency; `--from` re-scores without model calls. The judge
prompt no longer counts "Art. X does not exist" as a claim (M4).

## 3. Gates (CI)

| When | What | Gate |
|---|---|---|
| Every PR | unit tests, `retrieval.jsonl`, 20-case golden smoke (Flash only) | Recall@8 must not drop by more than 2 pts below the committed baseline (98.5 on 102 queries, M2). Quote fidelity 100%. Hallucinated citations 0. |
| PR label `full-eval` | full golden + adversarial on the default config | Posts a report comment on the PR. No hard gate. Track the trend. |
| Manual / before release | full matrix (§4) | Updates the README results table. |

CI auth: GitHub Actions → GCP via **Workload Identity Federation** (no JSON
keys; `make gcp-wif`). The index comes from the project bucket by sha256
(`evals/ci_index.json`, `make publish-index`). Workflows: `eval-smoke.yml`
(check-cases, retrieval, 20-case smoke, gates via `evals/harness/gate.py` and
`evals/baselines.yaml`; ready PRs that touch agent, MCP, ingest or eval code)
and `eval-full.yml` (label `full-eval`; golden + adversarial; comments
the report). Both skip until the `GCP_*` repo variables exist. The gates are
deterministic, so the smoke needs no judge (`SMOKE_ARGS=--no-judge`, set as a
repo variable). **Live since 2026-10-15** (WIF pool `swiss-nav-github`, repo
variables `GCP_PROJECT`, `GCP_WIF_PROVIDER`, `GCP_CI_SA`, `SMOKE_ARGS`): first
run on PR #5 passed every gate, 20/20 cases, quote fidelity 65/65, 0
hallucinated, CHF 0.67, about 6 minutes.

Spend cap: the smoke eval should cost under CHF 0.50 per run. Log the cost.
**Measured in M3:** about CHF 1.4 per smoke run (agent 0.75, judge 0.66;
ADR-019). **Measured in M4 (20 smoke cases, agent only, no judge):**

| agent thinking | CHF/answer | run | p50 / p95 s | thoughts | behaviour rule | req. recall |
|---|---|---|---|---|---|---|
| default (M3 run 3e7e603) | 0.035 | 0.70 | 38 / 82 | 3.6k | 20/20 | 1.00 |
| medium | 0.034 | 0.68 | 38 / 103 | 4.0k | 20/20 | 1.00 |
| low | 0.023 | 0.46 | 22 / 34 | 0 | 18/20 | 0.96 |

Reports: `evals/reports/2026-10-15-0990ecd-smoke-think-{low,medium}-drafts.json`
(answers stored, not yet judged).

Low thinking is a third cheaper and much faster, but the agent then gives
branching answers instead of asking (residence-01, residence-07). Re-graded
with the chosen judge on the final golden definitions: groundedness default
0.76, medium 0.86, low 0.91; key facts 100% each; behaviour 20/20, 20/20,
18/20. The served level stays at the default (ADR-025).

### Deployed target (M5)

`make eval-smoke-remote` (`answer_eval --target remote`) runs the same cases
against the agent on Agent Runtime (`AGENT_RUNTIME_ID`): one Agent Platform
session per case, streamed through `async_stream_query`, scored by the same
code as the local runner. The citation re-check still uses its own MCP
server, so the check stays independent of the deployed one. Reports record
the deployed commit, identity, scaling and env, and refuse to run when the
deployed `NAV_PROFILE` differs from the local one (cost and model labels come
from the profile). Latency includes the network and session creation.
First comparison: ADR-027 (within noise of local).

## 4. Experiments (README material)

| ID | Question | Configs |
|---|---|---|
| E1 | Which model, at what cost? | `gemini-3.8-flash` vs `gemini-3.5-flash-lite` vs `gemini-3.1-pro-preview` vs Claude (Model Garden) vs **Apertus 1.5 8B** (self-hosted) |
| E2 | Single agent vs multi-agent | `navigator_v1` vs `navigator_v2` (same model) |
| E3 | Does tree navigation help? | `search_law` only vs `search_law` + `get_toc` |
| E4 | Retrieval ablation | BM25 vs dense vs hybrid (RRF, weighted); trigram vs unicode61; with vs without contextual headers; dims 256–3072; emb-2@eu vs emb-001@europe-west6. **Done in M2:** dense emb-2 + headers + 768 dims wins (R@8 98.5, MRR 0.881; hybrid −13.7). ADR-016, `evals/reports/2026-10-15-c756c89-e4-retrieval.md`. |
| E5 | Cross-lingual robustness | Same questions in EN/DE/FR/IT: does quality drop for EN given that EN source texts are mostly missing? |
| E6 | Verifier value | v1 with vs without citation_verifier: hallucinated citations, latency, cost |
| E7 | Model Armor | Injection block rate vs false positives on golden |
| E8 | Memory whitelist | Memory Bank defaults vs custom topics vs structured profile: field recall, leaks of sensitive data, privacy cases. **Done in M7:** ADR-029. |

Report each one as a table with 95% bootstrap confidence intervals. With 150
cases, differences under ~5 pts are probably noise. **Say so.**

### Memory eval (M7)

`make eval-memory ARGS="--variant profile|topics|default [--part extract|e2e]"`
(`evals/harness/memory_eval.py`) runs against the memory-only instance
`MEMORY_EVAL_RUNTIME_ID` (never the served bank) and applies the variant's
config first. Each case gets its own scope, purged afterwards.

- **Extract:** `memories.generate` on the case's conversation, then the
  stored profile, natural-language facts and each field's free-text `context`
  are read back. Field recall: profile values directly; facts mapped to the
  same fields by the judge model. A **leak** is a forbidden string anywhere in
  what is stored (contexts included) or a stored item the judge flags as
  sensitive.
- **E2E:** navigator_v1 on a local runner over several sessions with
  `memory_opt_in` per session; a counting wrapper around the memory service
  records writes, reads and facts handed to the agent, so "no opt-in → nothing
  saved or read" is checked exactly.
- **Gate:** every `privacy` case must pass (the M7 "Done when"); the command
  exits non-zero otherwise. Not in CI (it needs the eval instance and costs
  ~CHF 0.4 with the e2e part).

## 5. Production feedback loop

- Thumbs up/down plus an optional comment in the UI, stored in Firestore with
  the trace ID.
- A weekly script exports thumbs-down cases into `evals/inbox/` for triage.
  Promote them to golden after verification.
- Agent Platform **Agent Evaluation** (online autoraters on live traffic) is a
  stretch. Mention it if used.
