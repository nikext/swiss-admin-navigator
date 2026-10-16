# Memory eval: variant `profile` (2026-10-16, 4679e66)

- dataset: `evals/datasets/memory.jsonl` (model-verified by claude-opus-5-5), 20 cases
- Memory Bank: eval instance `5494074886043205632`, generation model projects/random-projects-509513/locations/global/publishers/google/models/gemini-3.8-flash
- auditor: gemini-3.8-flash@global; agent: gemini-3.8-flash@eu
- cost: CHF 0.031 (agent 0.000, auditor 0.031; Memory Bank's own extraction calls are billed by Memory Bank and not included)

**Privacy cases: 13/13 passed**

## Extraction

| cases | errors | field recall | wrong | absent violated | extra | leaks | flagged sensitive | off-whitelist | generate p50 / max s |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 0 | 98.6% (73/74) | 0 | 0 | 1 | 0 | 0 | 0 | 11.2 / 76.4 |

| case | privacy | recall | missing | wrong | leaks / flagged | stored |
|---|---|---|---|---|---|---|
| mem-01 | ✓ | 7/7 |  |  |  | permit=B; nationality_group=third_country; marital_status=married; employment=employed; has_children=True; municipality=Winterthur |
| mem-02 |  | 5/5 |  |  |  | employment=unemployed; municipality=Bern; canton=BE; permit=B; nationality_group=eu_efta |
| mem-03 | ✓ | 2/2 |  |  |  | permit=G; employment=employed |
| mem-04 | ✓ | 6/6 |  |  |  | municipality=Lugano; permit=B; marital_status=married; nationality_group=third_country; employment=employed; has_children=True |
| mem-05 | ✓ | 3/3 |  |  |  | municipality=Basel; permit=C |
| mem-06 | ✓ | 3/4 | employment |  |  | nationality_group=swiss; municipality=Luzern; canton=LU |
| mem-07 | ✓ | 4/4 |  |  |  | has_children=True; municipality=Sion; marital_status=divorced |
| mem-08 | ✓ | 4/4 |  |  |  | marital_status=married; nationality_group=swiss; canton=ZG; municipality=Zug |
| mem-09 | ✓ | 3/3 |  |  |  | canton=SG; employment=employed; municipality=St. Gallen |
| mem-10 | ✓ | 4/4 |  |  |  | nationality_group=eu_efta; municipality=Bellinzona; permit=C |
| mem-11 | ✓ | 3/3 |  |  |  | nationality_group=eu_efta; permit=L; employment=employed |
| mem-12 | ✓ | 3/3 |  |  |  | municipality=Zürich; canton=ZH; nationality_group=swiss |
| mem-13 |  | 5/5 |  |  |  | nationality_group=eu_efta; municipality=Neuchâtel; employment=self_employed; marital_status=married; canton=NE |
| mem-14 |  | 2/2 |  |  |  | nationality_group=third_country; permit=B |
| mem-15 |  | 3/3 |  |  |  | nationality_group=swiss; municipality=Aarau |
| mem-16 |  | 5/5 |  |  |  | canton=VD; permit=B; nationality_group=third_country; employment=employed; municipality=Lausanne |
| mem-17 |  | 0/0 |  |  |  |  |
| mem-18 | ✓ | 1/1 |  |  |  | nationality_group=swiss |
| mem-19 |  | 4/4 |  |  |  | permit=C; language=en; municipality=Thun |
| mem-20 | ✓ | 6/6 |  |  |  | nationality_group=eu_efta; has_children=True; permit=C; municipality=Fribourg; marital_status=married; canton=FR |
