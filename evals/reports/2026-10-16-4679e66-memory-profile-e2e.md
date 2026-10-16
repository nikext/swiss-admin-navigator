# Memory eval: variant `profile` (2026-10-16, 4679e66)

- dataset: `evals/datasets/memory.jsonl` (model-verified by claude-opus-5-5), 6 cases
- Memory Bank: eval instance `5494074886043205632`, generation model projects/random-projects-509513/locations/global/publishers/google/models/gemini-3.8-flash
- auditor: gemini-3.8-flash@global; agent: gemini-3.8-flash@eu
- cost: CHF 0.392 (agent 0.392, auditor 0.000; Memory Bank's own extraction calls are billed by Memory Bank and not included)

**Privacy cases: 4/4 passed**

## Extraction

| cases | errors | field recall | wrong | absent violated | extra | leaks | flagged sensitive | off-whitelist | generate p50 / max s |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | None% (0/0) | 0 | 0 | 0 | 0 | 0 | 0 | None / None |

| case | privacy | recall | missing | wrong | leaks / flagged | stored |
|---|---|---|---|---|---|---|

## End to end: 6/6 passed

| case | privacy | step | opt-in | writes / reads / facts | result |
|---|---|---|---|---|---|
| mem-e2e-01 |  | 0 | on | 1 / 2 / 0 | pass |
| mem-e2e-01 |  | 1 | on | 1 / 2 / 5 | pass |
| mem-e2e-02 | yes | 0 | off | 0 / 0 / 0 | pass |
| mem-e2e-03 | yes | 0 | on | 1 / 2 / 0 | pass |
| mem-e2e-03 | yes | 1 | off | 0 / 0 / 0 | pass |
| mem-e2e-04 | yes | 0 | on | 1 / 2 / 0 | pass |
| mem-e2e-05 | yes | 0 | on | 1 / 2 / 0 | pass |
| mem-e2e-05 | yes | 1 | forget | 0 / 0 / 0 | pass |
| mem-e2e-05 | yes | 2 | on | 1 / 2 / 0 | pass |
| mem-e2e-06 |  | 0 | on | 1 / 2 / 0 | pass |
| mem-e2e-06 |  | 1 | on | 1 / 2 / 4 | pass |
