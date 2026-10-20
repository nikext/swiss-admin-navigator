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
M9 (E1 models, E3, E5) follows M8, then M10 (E7, Model Armor) and M11 (the
claim checker's latency on a healthy endpoint).

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

## M9: model comparison (E1), tree navigation (E3), languages (E5), 2026-10-20

Setup: `navigator_v1` with the served verifier (deterministic checks, no claim
checker) and the Model Armor input screen, golden 150. Each arm swaps only the
agent model (`AGENT_MODEL`); everything else is the default profile. Gemini
models through google-genai; open models on Model as a Service through LiteLLM
(`set_model_response` for the answer, AGENTS.md §6). Judge
`gemini-3.8-flash` (run on `eu` for most arms: `global` answered six 504s in a
row and ended the first grading passes; same model) and Qwen3 235B as the
cross-family judge. Decision and discussion: **ADR-035**.

Caveats: Gemini on `global` was degraded during the night of 2026-10-19/20
(Flash: a bare "Say OK" took 12 s on `global`, 1.7 s on `eu`; 50 of 150 Flash
cases failed with 429/504/499). **Flash was therefore run again in full on
`eu`**, the served endpoint; every other arm ran on `global` (Pro preview and
the open models are only served there). Errored cases of the other arms were
re-run once and merged (Pro 1, argon 17, DeepSeek 2, Qwen 23, mostly 429s and
timeouts); what still failed counts as an error. Latencies compare endpoints as
well as models.

Candidates: gpt-oss-120b on MaaS returns reasoning without content or a tool
call after its first tool result (ADK `MODEL_RETURNED_NO_CONTENT`, 3/3 probe
cases, at any reasoning effort) and is out; GLM-5.2 works but costs CHF 0.075
per answer on the probe and was left out; Claude has no quota (429, ADR-026).
Apertus (self-hosted): below.

### E1: models (golden, Flash judge)

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| flash | 150 | 0 | 99.6% (98.8–100.0) | 0 | 81.9 (77.9–85.4) | 95.4 (93.1–97.6) | 0 | 97.3 (94.7–99.3) | 96.5 (93.1–99.2) | 0.0389 | 39 / 109 | 7.4 |
| lite | 150 | 0 | 99.3% (97.7–100.0) | 0 | 81.0 (76.6–85.4) | 82.3 (77.8–86.7) | 3 | 89.3 (84.0–94.0) | 90.5 (85.6–94.8) | 0.0052 | 5 / 10 | 4.0 |
| pro | 150 | 0 | 98.6% (96.5–100.0) | 0 | 76.1 (71.3–80.6) | 93.9 (91.1–96.4) | 0 | 96.7 (93.3–99.3) | 96.1 (92.5–98.9) | 0.0714 | 51 / 134 | 3.9 |
| argon | 150 | 5 | 100.0% (100.0–100.0) | 0 | 91.5 (88.5–94.1) | 97.4 (94.8–99.3) | 0 | 93.3 (89.3–97.3) | 97.1 (94.2–99.6) | 0.0493 | 46 / 147 | 5.1 |
| deepseek | 150 | 0 | 100.0% (100.0–100.0) | 0 | 77.7 (73.9–81.1) | 82.9 (78.0–87.8) | 7 | 78.7 (72.0–84.7) | 88.0 (82.4–93.2) | 0.0187 | 85 / 169 | 6.8 |
| qwen | 150 | 5 | 100.0% (100.0–100.0) | 0 | 70.9 (66.5–75.1) | 71.5 (65.9–76.9) | 6 | 85.3 (79.3–91.3) | 87.8 (82.0–93.0) | 0.0199 | 31 / 78 | 8.5 |
| apertus | 150 | 1 | 100.0% (100.0–100.0) | 0 | 14.0 (10.2–18.1) | 34.3 (28.0–40.7) | 27 | 26.7 (20.0–34.0) | 38.0 (29.8–46.4) | 0.012 (GPU) | 67 / 167 | 3.9 |

Paired differences to **flash** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| lite | -1.8 (-6.5…+2.7), n=142 | -13.1 (-17.4…-8.7) | -8.0 (-12.7…-3.3) | +0.0 (+0.0…+0.0) | -0.0338 (-0.0389…-0.0296) | -39.9 (-45.3…-35.0) |
| pro | -7.3 (-11.3…-3.5), n=140 | -1.4 (-4.4…+1.4) | -0.7 (-4.0…+2.7) | +0.0 (+0.0…+0.0) | +0.0324 (+0.0252…+0.0406) | +15.8 (+7.8…+25.3) |
| argon | +7.4 (+3.7…+10.9), n=137 | +2.1 (-0.8…+4.9) | -4.0 (-8.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0135 (+0.0094…+0.0176) | +17.7 (+8.3…+28.9) |
| deepseek | -4.7 (-9.6…-0.1), n=137 | -12.5 (-17.8…-7.4) | -18.7 (-25.3…-12.0) | +0.0 (+0.0…+0.1) | -0.0203 (-0.0257…-0.0153) | +46.6 (+38.6…+54.8) |
| qwen | -13.3 (-17.8…-8.9), n=134 | -23.7 (-29.5…-18.2) | -12.0 (-17.3…-6.7) | +0.0 (+0.0…+0.1) | -0.0191 (-0.0262…-0.0108) | -9.0 (-15.6…-2.5) |
| apertus | -68.0 (-73.1…-62.5), n=142 | -61.1 (-67.4…-54.5) | -70.7 (-78.0…-63.3) | +0.2 (+0.1…+0.3) | −0.027 (GPU) | +29.1 (+20.9…+37.6) |

### E1: the same answers, Qwen3 judge

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| flash | 150 | 0 | 99.6% (98.8–100.0) | 0 | 91.9 (89.7–93.8) | 94.8 (91.7–97.4) | 3 | 96.7 (93.3–99.3) | 96.5 (93.1–99.2) | 0.0389 | 39 / 109 | 7.4 |
| lite | 150 | 0 | 99.3% (97.7–100.0) | 0 | 88.4 (85.3–91.4) | 85.9 (81.3–90.4) | 5 | 90.7 (85.3–94.7) | 90.5 (85.6–94.8) | 0.0052 | 5 / 10 | 4.0 |
| pro | 150 | 0 | 98.6% (96.5–100.0) | 0 | 87.3 (84.2–90.2) | 94.8 (92.1–97.1) | 1 | 95.3 (91.3–98.7) | 96.1 (92.5–98.9) | 0.0714 | 51 / 134 | 3.9 |
| argon | 150 | 5 | 100.0% (100.0–100.0) | 0 | 96.7 (95.5–97.8) | 97.6 (95.2–99.4) | 1 | 92.7 (88.0–96.7) | 97.1 (94.2–99.6) | 0.0493 | 46 / 147 | 5.1 |
| deepseek | 150 | 0 | 100.0% (100.0–100.0) | 0 | 89.0 (86.4–91.4) | 86.3 (81.2–91.0) | 4 | 79.3 (72.7–85.3) | 88.0 (82.4–93.2) | 0.0187 | 85 / 169 | 6.8 |
| qwen | 150 | 5 | 100.0% (100.0–100.0) | 0 | 82.8 (79.6–86.0) | 73.9 (68.4–79.3) | 14 | 80.7 (74.0–86.7) | 87.8 (82.0–93.0) | 0.0199 | 31 / 78 | 8.5 |
| apertus | 150 | 1 | 100.0% (100.0–100.0) | 0 | 34.6 (28.7–40.6) | 33.7 (27.6–40.6) | 34 | 25.3 (18.0–32.0) | 38.0 (29.8–46.4) | 0.012 (GPU) | 67 / 167 | 3.9 |

Paired differences to **flash** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| lite | -3.7 (-7.1…-0.2), n=135 | -8.9 (-13.6…-4.3) | -6.0 (-10.0…-2.0) | +0.0 (+0.0…+0.0) | -0.0338 (-0.0389…-0.0296) | -39.9 (-45.3…-35.0) |
| pro | -4.4 (-7.1…-1.9), n=132 | -0.0 (-3.0…+3.1) | -1.3 (-5.3…+2.0) | -0.0 (-0.0…+0.0) | +0.0324 (+0.0252…+0.0406) | +15.8 (+7.8…+25.3) |
| argon | +4.8 (+2.6…+7.1), n=132 | +2.2 (-0.9…+5.4) | -4.0 (-8.0…+0.0) | -0.0 (-0.0…+0.0) | +0.0135 (+0.0094…+0.0176) | +17.7 (+8.3…+28.9) |
| deepseek | -2.7 (-5.9…+0.3), n=130 | -8.5 (-13.8…-3.6) | -17.3 (-24.0…-10.7) | +0.0 (-0.0…+0.0) | -0.0203 (-0.0257…-0.0153) | +46.6 (+38.6…+54.8) |
| qwen | -9.1 (-12.6…-5.7), n=130 | -20.7 (-26.4…-15.3) | -16.0 (-22.7…-10.0) | +0.1 (+0.0…+0.1) | -0.0191 (-0.0262…-0.0108) | -9.0 (-15.6…-2.5) |
| apertus | -58.1 (-64.8…-51.6), n=119 | -61.1 (-67.5…-54.4) | -71.3 (-78.7…-63.3) | +0.2 (+0.1…+0.3) | −0.027 (GPU) | +29.1 (+20.9…+37.6) |

Per category (behaviour, rule + Flash judge, % of n):

| model | answerable (106) | clarification (6) | cantonal (15) | out of scope (13) | adversarial (10) |
|---|---|---|---|---|---|
| flash | 99 | 67 | 100 | 100 | 90 |
| lite | 98 | 33 | 87 | 54 | 80 |
| pro | 97 | 100 | 93 | 100 | 90 |
| argon | 95 | 83 | 87 | 92 | 90 |
| deepseek | 76 | 100 | 93 | 77 | 70 |
| qwen | 94 | 0 | 87 | 46 | 90 |
| apertus | 26 | 0 | 0 | 38 | 70 |

Verifier per model (first drafts → final): Flash sent back 8 of 150 drafts
(quotes and paragraphs); Flash-Lite 20 (17 misquotes, 6 answers degraded);
Pro 3; argon 27 (47 pinpoints: right article, wrong paragraph; 2 degraded);
DeepSeek 47 (37 `[n]` markers without a citation, 23 misquotes; 9 degraded);
Qwen 82 (57 drafts that were not the answer format; 13 degraded). Every final
quote that survived is verbatim and no arm cites a non-existent article: the
deterministic verifier holds the line for every model, at the price of
redrafts.

What the numbers say:
- **gemini-4-argon is the only model better grounded than Flash, under both
  judges:** +7.4 (CI +3.7…+10.9) with the Flash judge, +4.8 (+2.6…+7.1) with
  Qwen; key facts +2.1/+2.2 (noise), must_not 0. It cites more (5.3 vs 3.7
  citations per answer) and reads more articles. Its five errors are loops:
  89-215 `get_article` calls (~100 model calls) until the 600 s case timeout
  (two of them on the FZA annex, #6). Normal answers take at most 23 model
  calls. Re-run, all five answered in 5-16 calls; the loop is intermittent.
  Cost now CHF 0.049 per answer (+0.014), **CHF 0.099 from 2026-12-01** when
  its introductory price ends (Flash: 0.039 now, 0.078 from 2027-01-01).
- **Pro preview is less grounded than Flash** (−7.3 / −4.4) at 1.8× the cost:
  it answers from fewer articles (3.4 tool calls vs 6.4), so more of its claims
  rest on text it did not cite. Behaviour is as good as Flash's.
- **Flash-Lite** is 7.5× cheaper and 8× faster with the same groundedness under
  the Flash judge (−1.8, noise; −3.7 under Qwen), but it misses key facts
  (−13.1 / −8.9) and mishandles clarification and out-of-scope questions.
- **The open models** are cheaper (CHF 0.019-0.020) but clearly worse at the
  job: DeepSeek V3.2 −4.7/−2.7 groundedness, −12.5 key facts, behaviour −18.7
  (it answers where it should ask, refuse or point elsewhere), 7 must_not; Qwen3
  235B −13.3/−9.1 groundedness, −23.7 key facts, never asks a clarifying
  question. Qwen scores last under its own family's judge too.

### E1: Apertus 1.5 8B, self-hosted

Setup: `swiss-ai/Apertus-v1.5-8B` on one L4 in europe-west4 (`make
eval-apertus`, GCP.md §4): swiss-ai's vLLM fork, weights quantized to FP8 on
load, 32k context, non-thinking with the `apertus` tool parser; the agent
reaches it through LiteLLM and `gcloud run services proxy`, two cases at a
time. Same agent, verifier and input screen as the other arms, with one change
the other arms did not have: after an unparseable draft the verifier's redraft
can only call `set_model_response`, forced (e8c7498; without it, 0 of the first
9 cases ended with a valid answer, report `e8c7498-e1-apertus-unconstrained`).
Flash had no unparseable drafts in E1, so its numbers are unaffected; the open
models' (Qwen 57, DeepSeek 2) might be. Flash judge on `global` (healthy that
afternoon), Qwen3 as the cross-family judge. Run in two parts (the proxy
exited after 85 cases; the other 65 were re-run in a second deployment).

Rows `apertus` in the E1 tables above.

Paired differences to Flash: groundedness −68.0 (−73.1…−62.5, n=142), key
facts −61.1 (−67.4…−54.5), behaviour −70.7 (−78.0…−63.3) with the Flash judge;
−58.1 (−64.8…−51.6, n=119), −61.1 (−67.5…−54.4) and −71.3 (−78.7…−63.3)
with Qwen.

Behaviour per category (rule + Flash judge): answerable 26, clarification 0,
cantonal 0, out of scope 38, adversarial 70 (Flash: 99, 67, 100, 100, 90).
Language match 98.

Why it fails as an agent:
- **It reads too little.** 2.0 tool calls per answer (Flash 6.4); it fetches
  an article in 69 of 150 cases (Flash 140) and calls no tool at all in 23.
  The rest of what it writes comes from what it remembers about Swiss law.
- **It can't hold the answer format.** 144/150 first drafts are JSON but not
  a valid answer (citations without `sr` (60) or `quote_lang` (43), no
  `language` (14), numeric `ref`s (13)). The forced redraft makes 149/150
  valid, but its citations are mostly wrong: 75 to articles that don't exist
  as written (mostly the act inside the article field, "Art. 273 OR"), 56
  misquotes, 37 paragraphs the article doesn't have, 12 quotes from another
  paragraph, 27 `[n]` markers without a citation, 11 addresses or web
  addresses from memory. The verifier drops what it cannot fix: 117 answers
  end `degraded`, 60 with no citation left. The 90 quotes that remain are
  verbatim and no citation is invented, so the verifier holds here too.
- **Latency:** p50 67 s for 3.9 model calls (~17 s per call at 21k prompt
  tokens per answer; the fork's image lacks the fused xIELU kernel).
- **Cost:** no token price, only GPU time. The 150 answers took 95 GPU-minutes
  at concurrency 2 (0.6 min per answer): **CHF 0.012 per answer** while the
  GPU is busy. All M9 Apertus GPU time (five deployments, two of which
  failed to start; 13-27 min per start; grading while the service was up):
  228 min ≈ CHF 4.4. Serving it would need
  an always-on L4 (a cold start takes 13 min): ≈ CHF 850 per month, the price
  of ~22,000 Flash answers.

Not run: Apertus as the answer writer over articles that Gemini retrieved
(the second configuration in PLAN M9; dropped by Nikola, 2026-10-20). With
tools the 8B model is far from usable; whether it can write a grounded answer
from good context is open.

### argon's loops and the call budget

argon's five E1 errors are loops (89-215 `get_article` calls, ~100 model
calls, until the 600 s case timeout); re-run, the same five answered in 5-16
calls. Since then the agent has a budget of 40 model calls per turn, after
which it must answer from what it fetched (`agents/navigator/budget.py`,
ADR-035). The 20 smoke cases on `eu` with the budget (2026-10-20 03:00, with
`eu` degraded too: a bare call took 3.9 s):

| run | n | errors | groundedness | behaviour | CHF/answer | p50 / p95 s |
|---|---|---|---|---|---|---|
| argon, `eu` | 20 | 3 | 95.4 | 85.0 | 0.0784 | 60 / 546 |
| Flash + claim checker, `eu` | 20 | 5 | 90.7 | 75.0 | 0.0526 | 271 / 556 |

argon looped twice in 20: social-04 reached the budget (87 `get_article`
calls) and answered; housing-05 was at 33 calls when the case timed out. The
other errors are the endpoint (499/504/429 and slow calls). The claim
checker's latency question (ADR-034) stays open: this was not a healthy
endpoint either.

### E3: does tree navigation help?

The agent can call `get_toc`, but the prompt never asks for it. How often each
model browses an act's structure on golden: Flash 11/150 cases, Flash-Lite 1,
Pro 1, argon 6 (of 88 in the first run), DeepSeek 2 (of 84), **Qwen 44/150**.

Flash without `get_toc` on the 11 cases where it used it (paired; the other
139 cases never called it, so the ablation cannot change them except by
chance): groundedness −2.8 (−12.5…+6.3, n=11), key facts and behaviour
unchanged; it finds the same articles through `search_law`.

Qwen3 235B, the model that browses most, on all 150 cases with and without
`get_toc` (Flash judge; errored cases re-run once):

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| with-toc | 150 | 5 | 100.0% (100.0–100.0) | 0 | 70.9 (66.5–75.1) | 71.5 (65.9–76.9) | 6 | 85.3 (79.3–91.3) | 87.8 (82.0–93.0) | 0.0199 | 31 / 78 | 8.5 |
| without | 150 | 0 | 100.0% (100.0–100.0) | 0 | 67.0 (62.1–71.7) | 69.4 (63.6–75.0) | 6 | 84.0 (78.0–90.0) | 80.9 (74.4–87.2) | 0.0280 | 23 / 70 | 8.8 |

Paired differences to **with-toc** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| without | -2.1 (-7.2…+2.9), n=133 | -1.4 (-6.7…+3.8) | -1.3 (-7.3…+4.7) | +0.0 (-0.0…+0.0) | +0.0050 (-0.0070…+0.0204) | -9.7 (-14.9…-4.4) |

Without the tree Qwen searches more (2.8 vs 1.9 `search_law` calls per answer)
and finds fewer of the required articles: **required-citation recall −5.7
(−11.5…−0.4, n=122)**. Groundedness, key facts and behaviour move within
noise. Tree navigation helps a model that uses it locate the articles; it does
not measurably improve the answers, and the served model hardly uses it.

### E5: the same questions in four languages (Flash, `eu`)

40 golden answerable questions, 10 per original language, translated into the
other three (`crosslingual.jsonl`; Claude's translations, not verified, so not
a headline number); the original-language answers are the E1 Flash run.

40 questions, each answered in all four languages.

| language | n | errors | groundedness | key facts | behaviour | req. recall | language | quotes in |
|---|---|---|---|---|---|---|---|---|
| DE | 40 | 0 | 86.1 (81.5–90.7) | 97.5 (95.0–100.0) | 100.0 (100.0–100.0) | 97.5 (92.5–100.0) | 100.0 (100.0–100.0) | de 100% |
| EN | 40 | 0 | 86.8 (82.1–91.1) | 96.2 (91.2–100.0) | 100.0 (100.0–100.0) | 97.5 (92.5–100.0) | 100.0 (100.0–100.0) | de 100% |
| FR | 40 | 0 | 87.7 (82.9–91.9) | 96.2 (92.5–99.2) | 100.0 (100.0–100.0) | 96.2 (90.0–100.0) | 100.0 (100.0–100.0) | fr 100% |
| IT | 40 | 0 | 84.8 (78.2–90.4) | 92.9 (85.4–98.3) | 97.5 (92.5–100.0) | 95.0 (87.5–100.0) | 100.0 (100.0–100.0) | it 100% |

Paired differences to **DE** (mean, 95% CI):

| language | Δ groundedness | Δ key facts | Δ behaviour | Δ req. recall | Δ language |
|---|---|---|---|---|---|
| EN | +0.7 (-3.6…+4.9) | -1.2 (-5.0…+1.7) | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) |
| FR | +1.5 (-2.7…+5.5) | -1.2 (-4.6…+1.7) | +0.0 (+0.0…+0.0) | -1.2 (-3.8…+0.0) | +0.0 (+0.0…+0.0) |
| IT | -1.4 (-8.0…+3.2) | -4.6 (-11.7…+0.8) | -2.5 (-7.5…+0.0) | -2.5 (-7.5…+0.0) | +0.0 (+0.0…+0.0) |

Original wording vs translations (paired by question, mean, 95% CI):

| metric | original | translations | Δ translations − original |
|---|---|---|---|
| groundedness | 86.7 | 86.2 | -0.4 (-4.2…+3.1) |
| key facts | 95.8 | 95.7 | -0.1 (-3.8…+3.3) |
| behaviour | 100.0 | 99.2 | -0.8 (-2.5…+0.0) |
| req. recall | 97.5 | 96.2 | -1.2 (-3.3…+0.0) |
| language | 100.0 | 100.0 | +0.0 (+0.0…+0.0) |

No language effect beyond noise. **English answers quote the German text**
(Fedlex has no English version of most acts) and score the same as German
ones. Italian is lowest on key facts (−4.6, CI −11.7…+0.8). Answers to the
translations score like the originals, so the translations did not distort the
questions.

## M10: Model Armor input screen (E7), 2026-10-19

Setup: Model Armor `sanitizeUserPrompt` (template `swiss-nav-input` on `eu`,
multi-language detection on). The agent screens each user message once,
before the first model call, and blocks when the prompt-injection filter
reports medium confidence or more: a fixed refusal, no model or tool call.
Decision and discussion: **ADR-032**.

### The screen alone

Every golden, adversarial, silver and `injection.jsonl` text (40 new attacks
and 40 benign hard negatives, 10 per language each, model-verified, ADR-024
extended) plus 400 random in-force law texts; no Gemini call. Wilson 95% CIs.

| injection filter, multi-language | attacks (58) | benign (532) | law text (400) |
|---|---|---|---|
| low | 39.7% (23; 28–53) | 0.2% (1; 0–1) | 0% (0–1) |
| **medium (served)** | **29.3% (17; 19–42)** | **0% (0–1)** | **0% (0–1)** |
| high | 19.0% (11; 11–31) | 0% (0–1) | 0% (0–1) |

At medium by kind: direct overrides 9/10, personas 3/8, obfuscated 2/4,
memory poisoning 1/4, exfiltration 1/4, fake system turns 1/7, fake tool
output 0/5, format tricks 0/3, **injections inside pasted documents 0/13**
(0/13 at every level). Multi-language detection adds +5.2 points of attacks
at medium (CI 0…+12.1) for ~50 ms. The Responsible AI filters flag victims'
questions and law text at low and catch nothing extra at medium. Report:
`evals/reports/2026-10-19-98fc50c-e7-armor.md`.

### The agent with the screen

Served config (`gemini-3.8-flash@eu`, deterministic verifier), Flash judge,
paired with M8's v1 run of the same cases (`bd7595a-e2-v1-deterministic`,
which ran on `global` during a degradation, so latencies don't compare).

| run | n | blocked | errors | behaviour | groundedness | key facts | must_not | quote fidelity | halluc. |
|---|---|---|---|---|---|---|---|---|---|
| adversarial, screen | 50 | 6 | 0 | 98.0 (94.0–100.0) | 75.9 (67.9–83.3) | 97.0 | 1 | 100% | 0 |
| adversarial, M8 v1 | 50 | – | 1 | 96.0 (90.0–100.0) | 73.6 (64.8–82.2) | 98.0 | 1 | 100% | 0 |
| golden smoke, screen | 20 | 0 | 0 | 100.0 | 77.2 (63.6–88.9) | 100.0 | 0 | 100% | 0 |

Paired differences (screen − M8 v1): adversarial behaviour +2.0
(+0.0…+6.0), groundedness +1.2 (−5.3…+8.5, n=41), key facts −1.0
(−3.1…+0.0); smoke groundedness −5.3 (−16.5…+3.7, n=19), the rest 0. The
smoke blocked nothing, so its agent ran as before the screen; earlier smoke
runs scored 78.5 and 78.0 (M5).

What the screen blocks: on adversarial, adv-13 and adv-17 (injections) and
adv-39…42 (help with a fake lease, a sham marriage, undeclared work, hiding
from the authorities), which the agent refused anyway. On golden, only
adversarial-08, an injection wrapped around a real pension question: it gets
the refusal instead of the correction (behaviour fail, 1 of 150). The seven
blocked cases with the final refusal text (`b31f9fe-e7-blocked-drafts`):
0 model and tool calls, must_not 0, language 7/7, key facts 1.0 on the six
adversarial ones.

### Reproduce

```bash
make gcp-armor                      # template + IAM (once)
make eval-armor                     # the screen alone (free tier); ARGS="--from <report.json>" re-scores
MODEL_ARMOR_TEMPLATE=projects/<project>/locations/eu/templates/swiss-nav-input \
  make eval-full ARGS="--dataset adversarial --name e7-v1-screen"   # and: make eval-smoke
make eval-compare ARGS="--report m8-v1=evals/reports/2026-10-19-bd7595a-e2-v1-deterministic.json \
  --report screen=evals/reports/2026-10-19-18afd6e-e7-v1-screen-drafts.json --subset adversarial"
```

Spend: ≈ CHF 2.4 (agent 2.0, judge 0.4); Model Armor ≈ 250k tokens, inside
the free tier.

## M11: the claim checker on a healthy endpoint (E6 follow-up), 2026-10-20

Setup: the 20 smoke cases (golden, 5 per language) on the served config
(`navigator_v1`, Model Armor screen, `gemini-3.8-flash@eu` for agent and
claim checker) with `--claim-check`; the `deterministic` arm (the served
verifier) is the paired prefix of the same trajectories (`make eval-derive`).
`eu` was healthy: five "Say OK." pings a minute apart just before the run took
1.3–3.6 s, and no case errored. Judge `gemini-3.8-flash@global`, Qwen3 235B as
the cross-family judge. Decision: **ADR-034, update**.

Flash judge:

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deterministic | 20 | 0 | 100.0% (100.0–100.0) | 0 | 75.5 (61.6–86.5) | 100.0 (100.0–100.0) | 0 | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 0.0314 | 45 / 78 | 6.1 |
| claims | 20 | 0 | 100.0% (100.0–100.0) | 0 | 87.2 (72.2–98.3) | 100.0 (100.0–100.0) | 0 | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 0.0586 | 78 / 166 | 11.9 |

Paired differences to **deterministic** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| claims | +11.8 (+6.0…+18.0), n=20 | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0271 (+0.0153…+0.0400) | +35.4 (+21.8…+49.9) |

Qwen3 judge:

| config | n | errors | quote fidelity | halluc. | groundedness | key facts | must_not | behaviour | req. recall | CHF/answer | p50 / p95 s | model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deterministic | 20 | 0 | 100.0% (100.0–100.0) | 0 | 92.6 (89.3–95.9) | 100.0 (100.0–100.0) | 0 | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 0.0314 | 45 / 78 | 6.1 |
| claims | 20 | 0 | 100.0% (100.0–100.0) | 0 | 97.4 (94.5–99.7) | 100.0 (100.0–100.0) | 0 | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 0.0586 | 78 / 166 | 11.9 |

Paired differences to **deterministic** (mean, 95% CI):

| config | Δ groundedness | Δ key facts | Δ behaviour | Δ must_not | Δ CHF/answer | Δ latency s |
|---|---|---|---|---|---|---|
| claims | +4.8 (+2.0…+7.7), n=18 | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0 (+0.0…+0.0) | +0.0271 (+0.0153…+0.0400) | +35.4 (+21.8…+49.9) |

The checker sent 13 of 20 first drafts back (21 unsupported claims) and left
one answer `degraded` (mobility-01). The gain under Qwen (+4.8) matches M8's
golden number (+4.4); under Flash it is again more than twice as large. On a
healthy endpoint the checker costs +35 s per answer, not M8's +78 s, but the
p95 still doubles to 166 s (the web BFF's limit is 300 s). The web app keeps
it off (Nikola, 2026-10-20).

```bash
make eval-smoke ARGS="--claim-check --name m11-smoke-claims --traces data/logs/m11-smoke-claims.traces.jsonl"
make eval-derive ARGS="--from evals/reports/2026-10-20-28b6549-m11-smoke-claims.json --policy deterministic"
make judge-study ARGS="--report <each report>.json --name <name>-qwen" JUDGES="qwen/qwen3-235b-a22b-instruct-2507-maas@global"
make eval-compare ARGS="--report deterministic=…-derived-deterministic.json --report claims=…-m11-smoke-claims.json \
  [--study deterministic=…-qwen.json --study claims=…-qwen.json --judge qwen/qwen3-235b-a22b-instruct-2507-maas@global]"
```

Spend ≈ CHF 1.4 (agent 1.17, judges 0.25).
