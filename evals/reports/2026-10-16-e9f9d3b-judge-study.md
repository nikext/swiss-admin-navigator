# Judge study

- answers: `2026-10-15-3e7e603-answers-drafts.json` (30 answers); judge prompt sha d83d68626291; run 2026-10-16T07:06:11+00:00 at e9f9d3b
- human labels: 30 answers (`evals/datasets/judge_labels.jsonl`); reference judge: `gemini-3.8-flash@global`

## Agreement with human labels

| judge | CHF/answer | p50 s | grounded MAE | bias | ρ | fully-grounded acc / κ | key facts acc / κ (n) | must_not acc | behaviour acc / κ |
|---|---|---|---|---|---|---|---|---|---|
| `gemini-3.8-flash@global` | 0.0062 | 10.69 | 0.10 | -0.09 | 0.64 | 82 / 0.65 | 100 / 1.00 (66) | 100 | 100 / 1.00 |
| `zai-org/glm-5.2-maas@global` | 0.0180 | 41.82 | 0.16 | -0.07 | 0.27 | 57 / 0.18 | 100 / 1.00 (66) | 94 | 93 / 0.47 |
| `deepseek-ai/deepseek-v3.2-maas@global` | 0.0018 | 46.69 | 0.14 | -0.06 | 0.34 | 61 / 0.25 | 100 / 1.00 (66) | 97 | 100 / 1.00 |
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 0.0009 | 5.48 | 0.08 | 0.04 | 0.51 | 77 / 0.52 | 98 / 0.00 (66) | 91 | 97 / 0.65 |
| `openai/gpt-oss-120b-maas@global` | 0.0007 | 60.52 | 0.20 | -0.16 | 0.25 | 57 / 0.21 | 100 / 1.00 (66) | 91 | 90 / 0.37 |

## Agreement with the reference judge (all answers)

| judge | n | grounded MAE | bias | ρ | key facts acc | behaviour acc | errors |
|---|---|---|---|---|---|---|---|
| `gemini-3.8-flash@global` | 30 | 0.00 | 0.00 | 1.00 | 100 | 100 | 0 |
| `zai-org/glm-5.2-maas@global` | 30 | 0.09 | 0.01 | 0.53 | 100 | 93 | 0 |
| `deepseek-ai/deepseek-v3.2-maas@global` | 30 | 0.17 | 0.02 | 0.16 | 100 | 100 | 0 |
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 30 | 0.10 | 0.08 | 0.44 | 98 | 97 | 0 |
| `openai/gpt-oss-120b-maas@global` | 30 | 0.11 | -0.07 | 0.62 | 100 | 90 | 0 |

## The answers' scores under each judge

| judge | n | groundedness | key facts | behaviour | must_not violations | must_not flagged | behaviour failed |
|---|---|---|---|---|---|---|---|
| `gemini-3.8-flash@global` | 30 | 80 | 100 | 97 | 0 | – | social-05 |
| `zai-org/glm-5.2-maas@global` | 30 | 81 | 100 | 90 | 2 | housing-05, social-05 | housing-05, social-05, tax-02 |
| `deepseek-ai/deepseek-v3.2-maas@global` | 30 | 80 | 100 | 97 | 1 | social-05 | social-05 |
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 30 | 94 | 98 | 93 | 3 | housing-05, residence-06, social-05 | housing-05, social-05 |
| `openai/gpt-oss-120b-maas@global` | 30 | 71 | 100 | 87 | 3 | housing-05, residence-06, social-05 | housing-05, residence-06, social-05, tax-02 |

MAE/bias are on the 0–1 groundedness scale (bias > 0: judge more lenient than the reference). κ is Cohen's kappa. With n≈30 answers, differences of a few points are noise (EVALS.md §4).
