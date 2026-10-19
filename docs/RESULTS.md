# Results

Experiment results with 95% confidence intervals. Unofficial. Not legal advice.

How to read the tables:
- **n** = cases. Golden = the 150 model-verified cases (ADR-024); adversarial =
  the 50 adversarial cases. With 150 cases, differences under ~5 points are
  probably noise (EVALS.md §4); the paired CIs below say which ones are not.
- Metric CIs are bootstrap CIs over cases. **Paired differences** compare the
  same cases in both configurations (percentile bootstrap of the mean
  difference, 2,000 resamples); a CI that excludes 0 is a real difference.
- **Judges.** Groundedness, key facts, must_not and behaviour are graded by
  `gemini-3.8-flash@global` (ADR-023). Every headline is re-graded on golden by
  **Qwen3 235B** on MaaS (ADR-026), a different model family. Where they
  disagree, the Qwen number is the conservative one.
- Cost is CHF per answer at the prices in `evals/pricing.yaml` (agent, router
  and claim checker; judge excluded). Latency is wall-clock per answer.

Earlier experiments: E4 retrieval (M2, ADR-016,
`evals/reports/2026-10-15-c756c89-e4-retrieval.md`); E8 memory (M7, ADR-029).

## M8: multi-agent (E2) and verifier (E6), 2026-10-19

Setup: `navigator_v1` (one agent) and `navigator_v2` (router + domain
specialists, ADK dynamic workflow), both on gemini-3.8-flash; router and claim
checker on the same model at thinking low; all model calls on `global`.
One recorded run per agent with the full verifier (deterministic checks + LLM
claim checker); the `none` and `deterministic` arms are the paired prefixes of
those trajectories (`make eval-derive`, ADR-034), so all six arms answer the
same cases. Decision and discussion: **ADR-034**.

Caveat: Gemini on `global` and `eu` was degraded during the runs (calls queued
until their deadline, 429s). Absolute latencies are inflated; paired
differences are fair. 44 cases that failed on 504s/timeouts were re-run and
merged; one per arm still failed and counts as an error.

### E2: v1 vs v2 (golden)

Both with the claim checker, Flash judge:

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 150 | 0 | 99.7% (98.9–100.0) | 0 | 91.3 (87.8–94.4) | 94.3 (91.2–97.2) | 0 | 98.0 (95.3–100.0) | 98.0 (95.2–100.0) | 0.0669 | 127 / 419 | 12.5 |
| v2 | 150 | 1 | 99.7% (98.9–100.0) | 0 | 90.1 (86.5–93.0) | 96.5 (94.4–98.3) | 0 | 95.3 (91.3–98.7) | 98.1 (95.4–100.0) | 0.0756 | 151 / 521 | 14.9 |

Paired differences to **v1** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| v2 | -2.0 (-4.8…+1.2), n=146 | +2.2 (-0.8…+5.5) | -2.7 (-6.7…+0.7) | +0.0 (+0.0…+0.0) | +0.0087 (-0.0005…+0.0183) | +25.4 (-0.0…+52.5) |

Same answers, Qwen3 judge:

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 150 | 0 | 99.7% (98.9–100.0) | 0 | 96.0 (94.0–97.6) | 97.0 (94.7–98.9) | 2 | 96.7 (93.3–99.3) | 98.0 (95.2–100.0) | 0.0669 | 127 / 419 | 12.5 |
| v2 | 150 | 1 | 99.7% (98.9–100.0) | 0 | 94.1 (91.9–95.9) | 94.9 (91.7–97.5) | 5 | 94.0 (90.0–97.3) | 98.1 (95.4–100.0) | 0.0756 | 151 / 521 | 14.9 |

Paired differences to **v1** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| v2 | -1.7 (-3.6…+0.0), n=140 | -2.1 (-5.1…+0.7) | -2.7 (-6.0…+0.7) | +0.0 (+0.0…+0.0) | +0.0087 (-0.0005…+0.0183) | +25.4 (-0.0…+52.5) |

Without any verifier (first drafts), Qwen3 judge:

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 150 | 0 | 98.5% (97.1–99.6) | 0 | 91.6 (89.2–93.7) | 95.2 (92.4–97.6) | 4 | 95.3 (91.3–98.0) | 97.6 (94.8–99.6) | 0.0364 | 65 / 262 | 6.7 |
| v2 | 150 | 0 | 98.0% (96.5–99.2) | 0 | 88.7 (86.2–91.1) | 93.9 (90.7–96.7) | 6 | 93.3 (88.7–96.7) | 98.1 (95.5–100.0) | 0.0401 | 72 / 342 | 8.2 |

Paired differences to **v1** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| v2 | -2.8 (-5.4…-0.2), n=142 | -1.3 (-3.8…+1.2) | -2.0 (-6.0…+1.3) | +0.0 (-0.0…+0.0) | +0.0037 (+0.0000…+0.0087) | +21.8 (+3.2…+41.6) |

v2's router picked the expected domain for 98% of cases (195/199, CI
96–99.5): misrouting does not explain the gap.

### E2: v1 vs v2 (adversarial, claim checker, Flash judge)

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 50 | 1 | 100.0% (100.0–100.0) | 0 | 87.1 (78.3–94.7) | 98.0 (93.9–100.0) | 1 | 96.0 (90.0–100.0) | 95.7 (87.0–100.0) | 0.0425 | 112 / 512 | 9.0 |
| v2 | 50 | 0 | 100.0% (100.0–100.0) | 0 | 86.4 (78.4–93.5) | 97.0 (92.0–100.0) | 1 | 96.0 (90.0–100.0) | 95.8 (87.5–100.0) | 0.0525 | 86 / 417 | 11.3 |

Paired differences to **v1** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| v2 | -2.7 (-9.1…+3.6), n=46 | -1.0 (-3.1…+0.0) | +0.0 (-6.0…+6.0) | +0.0 (+0.0…+0.0) | +0.0095 (-0.0003…+0.0215) | -34.6 (-86.1…+11.7) |

### E6: what the verifier is worth (v1, golden)

`none` = the first draft as written; `deterministic` = v1's verifier
(ADR-018: re-fetch, quote and validity checks, one redraft); `claims` = plus the
LLM claim checker (two redrafts, unsupported claims removed). Flash judge:

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 150 | 0 | 98.5% (97.1–99.6) | 0 | 81.9 (78.1–85.3) | 94.9 (92.2–97.2) | 0 | 98.7 (96.7–100.0) | 97.6 (94.8–99.6) | 0.0364 | 65 / 262 | 6.7 |
| deterministic | 150 | 0 | 99.6% (98.8–100.0) | 0 | 83.2 (79.5–86.7) | 95.0 (92.3–97.3) | 0 | 98.7 (96.7–100.0) | 97.6 (94.8–99.6) | 0.0390 | 65 / 262 | 7.1 |
| claims | 150 | 0 | 99.7% (98.9–100.0) | 0 | 91.3 (87.8–94.4) | 94.3 (91.2–97.2) | 0 | 98.0 (95.3–100.0) | 98.0 (95.2–100.0) | 0.0669 | 127 / 419 | 12.5 |

Paired differences to **none** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| deterministic | +1.3 (-0.2…+2.9), n=148 | +0.1 (-0.7…+1.0) | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0026 (+0.0007…+0.0051) | +4.9 (+1.5…+9.2) |
| claims | +9.4 (+7.3…+11.7), n=148 | -0.6 (-3.2…+1.8) | -0.7 (-2.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0305 (+0.0245…+0.0375) | +77.9 (+62.9…+94.2) |

Qwen3 judge:

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 150 | 0 | 98.5% (97.1–99.6) | 0 | 91.6 (89.2–93.7) | 95.2 (92.4–97.6) | 4 | 95.3 (91.3–98.0) | 97.6 (94.8–99.6) | 0.0364 | 65 / 262 | 6.7 |
| deterministic | 150 | 0 | 99.6% (98.8–100.0) | 0 | 92.1 (89.9–94.0) | 95.6 (92.9–97.8) | 4 | 97.3 (94.7–99.3) | 97.6 (94.8–99.6) | 0.0390 | 65 / 262 | 7.1 |
| claims | 150 | 0 | 99.7% (98.9–100.0) | 0 | 96.0 (94.0–97.6) | 97.0 (94.7–98.9) | 2 | 96.7 (93.3–99.3) | 98.0 (95.2–100.0) | 0.0669 | 127 / 419 | 12.5 |

Paired differences to **none** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| deterministic | +0.5 (-0.7…+1.9), n=143 | +0.3 (-1.0…+2.0) | +2.0 (+0.0…+4.7) | +0.0 (-0.0…+0.0) | +0.0026 (+0.0007…+0.0051) | +4.9 (+1.5…+9.2) |
| claims | +4.4 (+2.4…+6.5), n=143 | +1.8 (+0.0…+4.0) | +1.3 (-1.3…+4.0) | -0.0 (-0.0…+0.0) | +0.0305 (+0.0245…+0.0375) | +77.9 (+62.9…+94.2) |

The claim checker's gain under Flash (+9.4) is twice its gain under Qwen
(+4.4): part of it is Flash grading against its own standard. The Qwen number
is the one to quote.

### E6: v1, adversarial (Flash judge)

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 50 | 1 | 100.0% (100.0–100.0) | 0 | 72.3 (63.4–80.9) | 98.0 (93.9–100.0) | 1 | 96.0 (90.0–100.0) | 95.7 (87.0–100.0) | 0.0222 | 45 / 205 | 4.4 |
| deterministic | 50 | 1 | 100.0% (100.0–100.0) | 0 | 73.6 (64.8–82.2) | 98.0 (93.9–100.0) | 1 | 96.0 (90.0–100.0) | 95.7 (87.0–100.0) | 0.0225 | 45 / 212 | 4.5 |
| claims | 50 | 1 | 100.0% (100.0–100.0) | 0 | 87.1 (78.3–94.7) | 98.0 (93.9–100.0) | 1 | 96.0 (90.0–100.0) | 95.7 (87.0–100.0) | 0.0425 | 112 / 512 | 9.0 |

Paired differences to **none** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| deterministic | +1.3 (-1.9…+4.6), n=47 | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0003 (+0.0000…+0.0008) | +0.3 (+0.0…+0.9) |
| claims | +14.8 (+9.1…+21.0), n=47 | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0202 (+0.0142…+0.0272) | +87.7 (+56.7…+123.6) |

### E6: the same for v2 (golden, Flash judge)

The pattern repeats on v2's trajectories.

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 150 | 0 | 98.0% (96.5–99.2) | 0 | 80.4 (76.9–83.6) | 96.9 (95.0–98.6) | 0 | 96.7 (93.3–99.3) | 98.1 (95.5–100.0) | 0.0401 | 72 / 342 | 8.2 |
| deterministic | 150 | 0 | 99.7% (98.9–100.0) | 0 | 81.8 (78.3–85.1) | 96.9 (95.0–98.6) | 0 | 96.7 (93.3–99.3) | 98.1 (95.5–100.0) | 0.0440 | 73 / 421 | 8.8 |
| claims | 150 | 1 | 99.7% (98.9–100.0) | 0 | 90.1 (86.5–93.0) | 96.5 (94.4–98.3) | 0 | 95.3 (91.3–98.7) | 98.1 (95.4–100.0) | 0.0756 | 151 / 521 | 14.9 |

Paired differences to **none** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| deterministic | +1.4 (+0.2…+2.8), n=149 | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0039 (+0.0014…+0.0070) | +8.5 (+2.7…+16.0) |
| claims | +9.7 (+7.1…+12.3), n=148 | -0.4 (-1.6…+0.4) | -1.3 (-3.3…+0.0) | +0.0 (+0.0…+0.0) | +0.0355 (+0.0292…+0.0423) | +82.6 (+67.5…+99.2) |

### Reproduce

```bash
export AGENT_LOCATION=global ROUTER_LOCATION=global VERIFIER_LOCATION=global
uv run python -m evals.harness.answer_eval --dataset golden+adversarial --agent v1 \
  --claim-check --case-timeout 600 --name e2-v1-claims --traces data/logs/e2-v1-claims.traces.jsonl
# (same with --agent v2); re-run errored cases with --ids, merge with --from A.json --from B.json
make eval-derive ARGS="--from <merged.json> --policy none"           # and --policy deterministic
make judge-study ARGS="--report <answers.json>" JUDGES="qwen/qwen3-235b-a22b-instruct-2507-maas@global"
make eval-compare ARGS="--report v1=A.json --report v2=B.json [--study v1=SA.json --study v2=SB.json --judge qwen/…@global] [--subset adversarial]"
```

Reports: `evals/reports/2026-10-19-bd7595a-e2-{v1,v2}-claims-merged-drafts.json` (recorded runs, merged with
their re-runs), `evals/reports/2026-10-19-bd7595a-e2-{v1,v2}-none.json`, `…-bd7595a-e2-v1-deterministic.json` and `…-51d2a7a-e2-v2-deterministic.json` (derived arms),
`evals/reports/2026-10-19-bd7595a-e2-*-qwen.json` (Qwen3 grades of golden).
