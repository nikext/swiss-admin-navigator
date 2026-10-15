# Evaluation

Evals are the core of this project, not an afterthought. Most portfolio agent
demos have none. The README will lead with a results table.

## 1. Datasets

All in `evals/datasets/`, versioned in git.

| Set | Size (target) | Purpose |
|---|---|---|
| `retrieval.jsonl` | 200 queries (102 on 2026-10-15) | Retrieval only: query → expected `(sr, eid)` set, matched per article regardless of language. 55 everyday + 47 `difficulty: hard` queries, DE/EN/FR/IT; expected eIds checked against the article text (drafted by Claude, not yet reviewed by Nikola). Cheap; runs on every PR. `make eval-retrieval`. |
| `golden.jsonl` | 150 cases | End-to-end QA, human-verified. **Gold.** |
| `silver.jsonl` | 300–500 cases | LLM-generated from articles, spot-checked. Used for broad regression, never for headline claims. |
| `multiturn.evalset.json` | 25 sessions | Clarification behaviour and memory use (ADK evalset format, user simulation). |
| `adversarial.jsonl` | 50 cases | Prompt injection, fake article numbers, out-of-scope, requests for individual legal advice, attempts to make it impersonate an official authority. |
| `memory.jsonl` | 20 cases | Memory recall, opt-out respected, sensitive facts **not** stored. |

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
  "verified_by": "nikola", "verified_on": "2026-10-xx", "as_of": "2026-10-01",
  "notes": "Art. 271a para. 1 lit. a"
}
```

### How to build the golden set without being a lawyer

1. Collect **real question shapes**: common expat questions about permits,
   Anmeldung, leases, notice periods, Quellensteuer, AHV, health insurance, and
   licence exchange (see the topic list in PLAN.md M4).
2. For each question, find the governing articles yourself through Fedlex
   (the MCP server's `get_toc` helps) and write `expected_citations` and
   `key_facts` **from the article text**.
3. Use an LLM to *propose* candidates. A human (Nikola) confirms each one
   against the article text and sets `verified_by`. Unverified cases go to
   `silver`.
4. Spread: 5 domains × 4 languages, with roughly 60% answerable, 15%
   clarification, 10% cantonal pointer, 15% out-of-scope/adversarial.
5. Re-check `as_of` when the corpus lock changes. A CI job flags golden cases
   whose cited articles changed text between builds.

## 2. Metrics

| Metric | Type | Definition |
|---|---|---|
| **Retrieval recall@k / MRR** | deterministic | Expected eids found in `search_law` top-k. |
| **Citation precision** | deterministic | Share of produced citations that exist **and** appear in `expected_citations`, or that an LLM judge rates as relevant. |
| **Required-citation recall** | deterministic | Share of `required: true` citations produced. |
| **Quote fidelity** | deterministic | Share of `quote` fields that are exact substrings of the stored article text (normalised whitespace). Target **100%**. |
| **Hallucinated citation rate** | deterministic | Citations to non-existent SR/article combinations. Target **0**. |
| **Groundedness** | LLM judge | Each claim in `answer_markdown` is supported by the cited text (claim-level, then averaged). ADK `hallucinations_v1` and/or a custom rubric. |
| **Key-fact coverage** | LLM judge | Share of `key_facts` stated correctly. |
| **must_not violations** | LLM judge | Count. Target **0**. |
| **Behaviour accuracy** | deterministic + judge | Correct category handling: asked when clarification was expected, declined out-of-scope, gave a cantonal pointer. |
| **Language match** | deterministic | Answer language == question language (langdetect). |
| **Safety** | ADK `safety_v1` | — |
| **Cost / latency** | measured | Tokens → CHF per answer (price table in `evals/pricing.yaml`, dated). p50/p95 latency. Tool-call count. |

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

**Approach:** use ADK `adk eval` / `AgentEvaluator` for multi-turn and rubric
criteria. Write the citation and quote metrics as a small custom harness
(`evals/harness/`) that calls the agent and parses the JSON answer contract.
Both write to a common `evals/reports/<date>-<git-sha>-<config>.json` and a
Markdown summary.

**Judge hygiene:** pin the judge model and prompt. Judge with a different model
family than the one under test where possible (e.g. Claude via Model Garden
judging Gemini answers, and vice versa). Report judge agreement on a 30-case
human-labelled subset.

## 3. Gates (CI)

| When | What | Gate |
|---|---|---|
| Every PR | unit tests, `retrieval.jsonl`, 20-case golden smoke (Flash only) | Recall@8 must not drop by more than 2 pts below the committed baseline (98.5 on 102 queries, M2). Quote fidelity 100%. Hallucinated citations 0. |
| PR label `full-eval` | full golden + adversarial on the default config | Posts a report comment on the PR. No hard gate. Track the trend. |
| Manual / before release | full matrix (§4) | Updates the README results table. |

CI auth: GitHub Actions → GCP via **Workload Identity Federation** (no JSON
keys). Spend cap: the smoke eval should cost under CHF 0.50 per run. Log the
cost.

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

Report each one as a table with 95% bootstrap confidence intervals. With 150
cases, differences under ~5 pts are probably noise. **Say so.**

## 5. Production feedback loop

- Thumbs up/down plus an optional comment in the UI, stored in Firestore with
  the trace ID.
- A weekly script exports thumbs-down cases into `evals/inbox/` for triage.
  Promote them to golden after verification.
- Agent Platform **Agent Evaluation** (online autoraters on live traffic) is a
  stretch. Mention it if used.
