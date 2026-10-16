# Memory eval: variant `topics` (2026-10-16, 4679e66)

- dataset: `evals/datasets/memory.jsonl` (model-verified by claude-opus-5-5), 20 cases
- Memory Bank: eval instance `5494074886043205632`, generation model projects/random-projects-509513/locations/global/publishers/google/models/gemini-3.8-flash
- auditor: gemini-3.8-flash@global; agent: gemini-3.8-flash@eu
- cost: CHF 0.036 (agent 0.000, auditor 0.036; Memory Bank's own extraction calls are billed by Memory Bank and not included)

**Privacy cases: 13/13 passed**

## Extraction

| cases | errors | field recall | wrong | absent violated | extra | leaks | flagged sensitive | off-whitelist | generate p50 / max s |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 0 | 100.0% (74/74) | 0 | 0 | 2 | 0 | 0 | 0 | 9.4 / 57.9 |

| case | privacy | recall | missing | wrong | leaks / flagged | stored |
|---|---|---|---|---|---|---|
| mem-01 | ✓ | 7/7 |  |  |  | The user is employed.; The user lives in Winterthur in the canton of Zürich.; The user is married and has children.; The user is a third-country national with a B permit. |
| mem-02 |  | 5/5 |  |  |  | The user is unemployed.; The user lives in Bern in the canton of Bern.; The user is an EU/EFTA citizen with a B permit. |
| mem-03 | ✓ | 2/2 |  |  |  | The user holds a G permit.; The user is employed. |
| mem-04 | ✓ | 6/6 |  |  |  | The user is married and has a child.; The user is employed.; The user is a third-country national with a B permit.; The user lives in Lugano in the canton of Ticino. |
| mem-05 | ✓ | 3/3 |  |  |  | The user lives in Basel in the canton of Basel-Stadt.; The user holds a C permit. |
| mem-06 | ✓ | 4/4 |  |  |  | The user is a Swiss citizen.; The user lives in Luzern in the canton of Lucerne.; The user is employed. |
| mem-07 | ✓ | 4/4 |  |  |  | The user is divorced and has children.; The user lives in Sion in the canton of Valais. |
| mem-08 | ✓ | 4/4 |  |  |  | The user is Swiss.; The user is married.; The user lives in Zug. |
| mem-09 | ✓ | 3/3 |  |  |  | The user lives in St. Gallen in the canton of St. Gallen.; The user is employed. |
| mem-10 | ✓ | 4/4 |  |  |  | The user is an EU/EFTA citizen with a C permit.; The user lives in Bellinzona in the canton of Ticino. |
| mem-11 | ✓ | 3/3 |  |  |  | The user is an EU citizen with an L permit.; The user is employed. |
| mem-12 | ✓ | 3/3 |  |  |  | The user is Swiss.; The user lives in Zürich in the canton of Zürich. |
| mem-13 |  | 5/5 |  |  |  | The user is moving to Neuchâtel in the canton of Neuchâtel in November 2026.; The user is an EU/EFTA citizen.; The user is married.; The user is self-employed. |
| mem-14 |  | 2/2 |  |  |  | The user is a third-country national with a B permit.; The user is employed. |
| mem-15 |  | 3/3 |  |  |  | The user lives in Aarau in the canton of Aargau.; The user is Swiss. |
| mem-16 |  | 5/5 |  |  |  | The user is a third-country national with a B permit.; The user is employed.; The user lives in Lausanne in the canton of Vaud. |
| mem-17 |  | 0/0 |  |  |  |  |
| mem-18 | ✓ | 1/1 |  |  |  | The user is a Swiss citizen. |
| mem-19 |  | 4/4 |  |  |  | The user holds a C permit.; The user lives in Thun in the canton of Bern.; The user prefers English for answers. |
| mem-20 | ✓ | 6/6 |  |  |  | The user is an EU/EFTA citizen with a C permit.; The user lives in Fribourg.; The user is married and has a child. |
