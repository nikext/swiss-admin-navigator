# Judge study

- answers: `2026-10-20-e38b51c-e1-apertus.json` (149 answers); judge prompt sha d83d68626291; run 2026-10-20T13:29:17+00:00 at e38b51c
- human labels: 0 answers (`evals/datasets/judge_labels.jsonl`); reference judge: `qwen/qwen3-235b-a22b-instruct-2507-maas@global`

## Agreement with human labels

| judge | CHF/answer | p50 s | grounded MAE | bias | ρ | fully-grounded acc / κ | key facts acc / κ (n) | must_not acc | behaviour acc / κ |
|---|---|---|---|---|---|---|---|---|---|
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 0.0006 | 3.99 | – | – | – | – / – | – / – (0) | – | – / – |

## Agreement with the reference judge (all answers)

| judge | n | grounded MAE | bias | ρ | key facts acc | behaviour acc | errors |
|---|---|---|---|---|---|---|---|
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 149 | 0.00 | 0.00 | 1.00 | 100 | 100 | 0 |

## The answers' scores under each judge

| judge | n | groundedness | key facts | behaviour | must_not violations | must_not flagged | behaviour failed |
|---|---|---|---|---|---|---|---|
| `qwen/qwen3-235b-a22b-instruct-2507-maas@global` | 149 | 35 | 33 | 34 | 34 | adversarial-02, general-05, general-06, housing-10, housing-24, mobility-02, mobility-07, mobility-08, mobility-09, residence-10, residence-12, residence-18, residence-21, residence-23, residence-24, residence-25, residence-30, social-05, social-16, social-25, social-26, tax-03, tax-04, tax-14, work-02, work-07, work-10, work-12, work-16, work-19, work-20, work-27 | adversarial-02, adversarial-04, adversarial-06, general-05, general-06, housing-01, housing-05, housing-06, housing-07, housing-10, housing-11, housing-13, housing-14, housing-15, housing-16, housing-18, housing-19, housing-20, housing-22, housing-24, mobility-01, mobility-03, mobility-04, mobility-06, mobility-07, mobility-08, mobility-09, residence-01, residence-02, residence-04, residence-06, residence-07, residence-08, residence-09, residence-10, residence-12, residence-15, residence-16, residence-17, residence-18, residence-20, residence-21, residence-22, residence-23, residence-24, residence-25, residence-27, residence-29, residence-30, social-03, social-04, social-05, social-07, social-09, social-10, social-13, social-14, social-15, social-16, social-18, social-19, social-20, social-21, social-22, social-23, social-24, social-25, social-26, tax-01, tax-02, tax-03, tax-04, tax-05, tax-06, tax-07, tax-08, tax-09, tax-10, tax-11, tax-14, work-02, work-04, work-07, work-08, work-09, work-10, work-11, work-12, work-13, work-15, work-16, work-17, work-18, work-19, work-20, work-22, work-24, work-26, work-27 |

MAE/bias are on the 0–1 groundedness scale (bias > 0: judge more lenient than the reference). κ is Cohen's kappa. With n≈30 answers, differences of a few points are noise (EVALS.md §4).
