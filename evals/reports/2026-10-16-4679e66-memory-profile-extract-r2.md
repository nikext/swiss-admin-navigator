# Memory eval: variant `profile` (2026-10-16, 4679e66)

- dataset: `evals/datasets/memory.jsonl` (model-verified by claude-opus-5-5), 20 cases
- Memory Bank: eval instance `5494074886043205632`, generation model projects/random-projects-509513/locations/global/publishers/google/models/gemini-3.8-flash
- auditor: gemini-3.8-flash@global; agent: gemini-3.8-flash@eu
- cost: CHF 0.029 (agent 0.000, auditor 0.029; Memory Bank's own extraction calls are billed by Memory Bank and not included)

**Privacy cases: 13/13 passed**

## Extraction

| cases | errors | field recall | wrong | absent violated | extra | leaks | flagged sensitive | off-whitelist | generate p50 / max s |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 0 | 97.3% (72/74) | 0 | 0 | 0 | 0 | 0 | 0 | 11.7 / 77.4 |

| case | privacy | recall | missing | wrong | leaks / flagged | stored |
|---|---|---|---|---|---|---|
| mem-01 | ✓ | 7/7 |  |  |  | nationality_group=third_country; has_children=True; employment=employed; marital_status=married; permit=B; municipality=Winterthur |
| mem-02 |  | 5/5 |  |  |  | permit=B; nationality_group=eu_efta; municipality=Bern; canton=BE; employment=unemployed |
| mem-03 | ✓ | 2/2 |  |  |  | employment=employed; permit=G |
| mem-04 | ✓ | 6/6 |  |  |  | marital_status=married; municipality=Lugano; has_children=True; permit=B; nationality_group=third_country |
| mem-05 | ✓ | 3/3 |  |  |  | permit=C; municipality=Basel |
| mem-06 | ✓ | 3/4 | employment |  |  | nationality_group=swiss; municipality=Luzern; canton=LU |
| mem-07 | ✓ | 4/4 |  |  |  | municipality=Sion; marital_status=divorced; has_children=True |
| mem-08 | ✓ | 4/4 |  |  |  | nationality_group=swiss; marital_status=married; canton=ZG; municipality=Zug |
| mem-09 | ✓ | 3/3 |  |  |  | canton=SG; employment=employed; municipality=St. Gallen |
| mem-10 | ✓ | 4/4 |  |  |  | municipality=Bellinzona; permit=C; nationality_group=eu_efta |
| mem-11 | ✓ | 3/3 |  |  |  | nationality_group=eu_efta; permit=L; employment=employed |
| mem-12 | ✓ | 3/3 |  |  |  | nationality_group=swiss; municipality=Zürich; canton=ZH |
| mem-13 |  | 5/5 |  |  |  | employment=self_employed; municipality=Neuchâtel; marital_status=married; nationality_group=eu_efta; canton=NE |
| mem-14 |  | 1/2 | nationality_group |  |  | permit=B |
| mem-15 |  | 3/3 |  |  |  | nationality_group=swiss; municipality=Aarau |
| mem-16 |  | 5/5 |  |  |  | permit=B; municipality=Lausanne; nationality_group=third_country; employment=employed |
| mem-17 |  | 0/0 |  |  |  |  |
| mem-18 | ✓ | 1/1 |  |  |  | nationality_group=swiss |
| mem-19 |  | 4/4 |  |  |  | permit=C; language=en; municipality=Thun |
| mem-20 | ✓ | 6/6 |  |  |  | marital_status=married; nationality_group=eu_efta; municipality=Fribourg; has_children=True; canton=FR; permit=C |
