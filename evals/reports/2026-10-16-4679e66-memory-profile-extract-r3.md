# Memory eval: variant `profile` (2026-10-16, 4679e66)

- dataset: `evals/datasets/memory.jsonl` (model-verified by claude-opus-5-5), 20 cases
- Memory Bank: eval instance `5494074886043205632`, generation model projects/random-projects-509513/locations/global/publishers/google/models/gemini-3.8-flash
- auditor: gemini-3.8-flash@global; agent: gemini-3.8-flash@eu
- cost: CHF 0.030 (agent 0.000, auditor 0.030; Memory Bank's own extraction calls are billed by Memory Bank and not included)

**Privacy cases: 13/13 passed**

## Extraction

| cases | errors | field recall | wrong | absent violated | extra | leaks | flagged sensitive | off-whitelist | generate p50 / max s |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 0 | 98.6% (73/74) | 0 | 0 | 1 | 0 | 0 | 0 | 11.9 / 116.7 |

| case | privacy | recall | missing | wrong | leaks / flagged | stored |
|---|---|---|---|---|---|---|
| mem-01 | ✓ | 7/7 |  |  |  | permit=B; nationality_group=third_country; has_children=True; employment=employed; marital_status=married; municipality=Winterthur |
| mem-02 |  | 5/5 |  |  |  | municipality=Bern; employment=unemployed; canton=BE; nationality_group=eu_efta; permit=B |
| mem-03 | ✓ | 2/2 |  |  |  | employment=employed; permit=G |
| mem-04 | ✓ | 6/6 |  |  |  | has_children=True; employment=employed; nationality_group=third_country; municipality=Lugano; permit=B; marital_status=married |
| mem-05 | ✓ | 3/3 |  |  |  | permit=C; municipality=Basel |
| mem-06 | ✓ | 3/4 | employment |  |  | municipality=Luzern; canton=LU; nationality_group=swiss |
| mem-07 | ✓ | 4/4 |  |  |  | has_children=True; marital_status=divorced; municipality=Sion |
| mem-08 | ✓ | 4/4 |  |  |  | nationality_group=swiss; canton=ZG; marital_status=married; municipality=Zug |
| mem-09 | ✓ | 3/3 |  |  |  | canton=SG; municipality=St. Gallen; employment=employed |
| mem-10 | ✓ | 4/4 |  |  |  | permit=C; municipality=Bellinzona; nationality_group=eu_efta |
| mem-11 | ✓ | 3/3 |  |  |  | permit=L; nationality_group=eu_efta; employment=employed |
| mem-12 | ✓ | 3/3 |  |  |  | canton=ZH; nationality_group=swiss; municipality=Zürich |
| mem-13 |  | 5/5 |  |  |  | municipality=Neuchâtel; employment=self_employed; nationality_group=eu_efta; canton=NE; marital_status=married |
| mem-14 |  | 2/2 |  |  |  | permit=B; nationality_group=third_country |
| mem-15 |  | 3/3 |  |  |  | municipality=Aarau; nationality_group=swiss |
| mem-16 |  | 5/5 |  |  |  | employment=employed; permit=B; nationality_group=third_country; municipality=Lausanne |
| mem-17 |  | 0/0 |  |  |  |  |
| mem-18 | ✓ | 1/1 |  |  |  | nationality_group=swiss |
| mem-19 |  | 4/4 |  |  |  | language=en; municipality=Thun; permit=C |
| mem-20 | ✓ | 6/6 |  |  |  | has_children=True; permit=C; canton=FR; marital_status=married; nationality_group=eu_efta; municipality=Fribourg |
