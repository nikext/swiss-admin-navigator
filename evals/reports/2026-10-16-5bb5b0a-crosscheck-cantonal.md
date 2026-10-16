# Judge study

- answers: `2026-10-16-5bb5b0a-cantonal-contact.json` (15 answers); judge prompt sha d83d68626291; run 2026-10-16T07:58:10+00:00 at 5bb5b0a
- human labels: 0 answers (`evals/datasets/judge_labels.jsonl`); reference judge: `qwen/qwen3-235b-a22b-instruct-2507-maas@global`

## Agreement with human labels

| judge | CHF/answer | p50 s | grounded MAE | bias | ρ | fully-grounded acc / κ | key facts acc / κ (n) | must_not acc | behaviour acc / κ |
|---|---|---|---|---|---|---|---|---|---|
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 0.0009 | 5.80 | – | – | – | – / – | – / – (0) | – | – / – |

## Agreement with the reference judge (all answers)

| judge | n | grounded MAE | bias | ρ | key facts acc | behaviour acc | errors |
|---|---|---|---|---|---|---|---|
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 15 | 0.00 | 0.00 | 1.00 | 100 | 100 | 0 |

## The answers' scores under each judge

| judge | n | groundedness | key facts | behaviour | must_not violations | must_not flagged | behaviour failed |
|---|---|---|---|---|---|---|---|
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 15 | 96 | 97 | 100 | 0 | – | – |

MAE/bias are on the 0–1 groundedness scale (bias > 0: judge more lenient than the reference). κ is Cohen's kappa. With n≈30 answers, differences of a few points are noise (EVALS.md §4).
