# Judge study

- answers: `2026-10-15-0990ecd-smoke-think-low-drafts.json` (20 answers); judge prompt sha d83d68626291; run 2026-10-15T21:38:08+00:00 at 7bd9768
- human labels: 0 answers (`evals/datasets/judge_labels.jsonl`); reference judge: `gemini-3.8-flash@global`

## Agreement with human labels

| judge | CHF/answer | p50 s | grounded MAE | bias | ρ | fully-grounded acc / κ | key facts acc / κ (n) | must_not acc | behaviour acc / κ |
|---|---|---|---|---|---|---|---|---|---|
| `gemini-3.8-flash@global` | 0.0070 | 10.24 | – | – | – | – / – | – / – (0) | – | – / – |

## Agreement with the reference judge (all answers)

| judge | n | grounded MAE | bias | ρ | key facts acc | behaviour acc | errors |
|---|---|---|---|---|---|---|---|
| `gemini-3.8-flash@global` | 20 | 0.00 | 0.00 | 1.00 | 100 | 100 | 0 |

MAE/bias are on the 0–1 groundedness scale (bias > 0: judge more lenient than the reference). κ is Cohen's kappa. With n≈30 answers, differences of a few points are noise (EVALS.md §4).
