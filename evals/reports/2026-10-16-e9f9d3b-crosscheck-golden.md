# Judge study

- answers: `2026-10-15-7bd9768-baseline-golden.json` (150 answers); judge prompt sha d83d68626291; run 2026-10-16T07:24:15+00:00 at e9f9d3b
- human labels: 0 answers (`evals/datasets/judge_labels.jsonl`); reference judge: `gemini-3.8-flash@global`

## Agreement with human labels

| judge | CHF/answer | p50 s | grounded MAE | bias | ρ | fully-grounded acc / κ | key facts acc / κ (n) | must_not acc | behaviour acc / κ |
|---|---|---|---|---|---|---|---|---|---|
| `gemini-3.8-flash@global` | 0.0068 | 11.26 | – | – | – | – / – | – / – (0) | – | – / – |
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 0.0009 | 5.81 | – | – | – | – / – | – / – (0) | – | – / – |

## Agreement with the reference judge (all answers)

| judge | n | grounded MAE | bias | ρ | key facts acc | behaviour acc | errors |
|---|---|---|---|---|---|---|---|
| `gemini-3.8-flash@global` | 150 | 0.00 | 0.00 | 1.00 | 100 | 100 | 0 |
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 150 | 0.12 | 0.08 | 0.40 | 97 | 97 | 0 |

## The answers' scores under each judge

| judge | n | groundedness | key facts | behaviour | must_not violations | must_not flagged | behaviour failed |
|---|---|---|---|---|---|---|---|
| `gemini-3.8-flash@global` | 150 | 80 | 94 | 98 | 0 | – | mobility-07, residence-03, social-05 |
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 150 | 92 | 94 | 95 | 8 | housing-05, mobility-07, mobility-09, mobility-10, residence-05, residence-28, social-05, social-26 | housing-05, mobility-07, mobility-10, residence-03, residence-15, residence-28, social-05 |

MAE/bias are on the 0–1 groundedness scale (bias > 0: judge more lenient than the reference). κ is Cohen's kappa. With n≈30 answers, differences of a few points are noise (EVALS.md §4).
