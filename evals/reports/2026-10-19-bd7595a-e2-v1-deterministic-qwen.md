# Judge study

- answers: `2026-10-19-bd7595a-e2-v1-deterministic.json` (150 answers); judge prompt sha d83d68626291; run 2026-10-19T20:06:13+00:00 at bd7595a
- human labels: 0 answers (`evals/datasets/judge_labels.jsonl`); reference judge: `qwen/qwen3-235b-a22b-instruct-2507-maas@global`

## Agreement with human labels

| judge | CHF/answer | p50 s | grounded MAE | bias | ρ | fully-grounded acc / κ | key facts acc / κ (n) | must_not acc | behaviour acc / κ |
|---|---|---|---|---|---|---|---|---|---|
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 0.0009 | 9.03 | – | – | – | – / – | – / – (0) | – | – / – |

## Agreement with the reference judge (all answers)

| judge | n | grounded MAE | bias | ρ | key facts acc | behaviour acc | errors |
|---|---|---|---|---|---|---|---|
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 150 | 0.00 | 0.00 | 1.00 | 100 | 100 | 0 |

## The answers' scores under each judge

| judge | n | groundedness | key facts | behaviour | must_not violations | must_not flagged | behaviour failed |
|---|---|---|---|---|---|---|---|
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 150 | 92 | 95 | 97 | 4 | mobility-10, social-05, work-16, work-24 | mobility-07, mobility-10, residence-15, social-05 |

MAE/bias are on the 0–1 groundedness scale (bias > 0: judge more lenient than the reference). κ is Cohen's kappa. With n≈30 answers, differences of a few points are noise (EVALS.md §4).
