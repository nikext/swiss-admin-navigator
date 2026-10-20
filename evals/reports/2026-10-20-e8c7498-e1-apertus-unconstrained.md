# Answer eval: e1-apertus-unconstrained

- dataset: `golden` (9 cases selected, 9 verified by claude-opus-5-5; sha 283079d403c1 over golden.jsonl)
- agent: `swiss-ai/Apertus-v1.5-8B@http://127.0.0.1:8081/v1`, prompt sha 604f3a1f7ee4, google-adk 2.12.0, structured output set_model_response tool
- judge: off
- input screen (M10): Model Armor `swiss-nav-input`, block at medium; blocked 0
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-20T10:42:46+00:00 at e8c7498; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **–%** (0/0) |
| hallucinated citations | **0** of 0 |
| required-citation recall | – |
| citation precision (expected only) | – |
| behaviour (rule only) | **0.0** (0.0–0.0, n=9) |
| answers with contact details (rule: address, postcode, phone, web) | 0 |
| language match | – |
| errors | 9 |

## Verifier

- first drafts: 0 citations, 0 quotes; problems none; 0 cases sent back once
- final status: {'none': 9}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0000 mean, 0.0000 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 0.000, judge CHF 0.000
- latency p50 – s, p95 – s; – model calls and – tool calls per answer; tokens per answer (mean):

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: answerable | 8 | 0 | – | – | 0 |
| category: cantonal_pointer | 1 | 0 | – | – | 0 |
| lang: de | 3 | 0 | – | – | 0 |
| lang: en | 2 | 0 | – | – | 0 |
| lang: fr | 2 | 0 | – | – | 0 |
| lang: it | 2 | 0 | – | – | 0 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| housing-01 | final answer is not JSON: Expecting value: line 1 column 1 (char 0) | 0 | 0/0 | 0 | 0 | – | – | **no** | None ✗ | 318 | 0.0000 |
| housing-02 | final answer is not JSON: Expecting value: line 1 column 1 (char 0) | 0 | 0/0 | 0 | 0 | – | – | **no** | None ✗ | 97 | 0.0000 |
| housing-03 | final answer is not JSON: Expecting value: line 1 column 1 (char 0) | 0 | 0/0 | 0 | 0 | – | – | **no** | None ✗ | 415 | 0.0000 |
| housing-04 | final answer is not JSON: Extra data: line 4 column 1 (char 2085) | 0 | 0/0 | 0 | 0 | – | – | **no** | None ✗ | 331 | 0.0000 |
| housing-05 | final answer is not JSON: Expecting value: line 1 column 1 (char 0) | 0 | 0/0 | 0 | 0 | – | – | **no** | None ✗ | 63 | 0.0000 |
| work-01 | final answer is not JSON: Extra data: line 1 column 1175 (char 1174) | 0 | 0/0 | 0 | 0 | – | – | **no** | None ✗ | 98 | 0.0000 |
| work-02 | final answer is not JSON: Expecting value: line 1 column 1 (char 0) | 0 | 0/0 | 0 | 0 | – | – | **no** | None ✗ | 169 | 0.0000 |
| work-03 | final answer is not JSON: Expecting value: line 1 column 1 (char 0) | 0 | 0/0 | 0 | 0 | – | – | **no** | None ✗ | 196 | 0.0000 |
| work-04 | final answer is not JSON: Expecting value: line 1 column 1 (char 0) | 0 | 0/0 | 0 | 0 | – | – | **no** | None ✗ | 197 | 0.0000 |

## Findings per case

- `housing-01`: error: final answer is not JSON: Expecting value: line 1 column 1 (char 0)
- `housing-02`: error: final answer is not JSON: Expecting value: line 1 column 1 (char 0)
- `housing-03`: error: final answer is not JSON: Expecting value: line 1 column 1 (char 0)
- `housing-04`: error: final answer is not JSON: Extra data: line 4 column 1 (char 2085)
- `housing-05`: error: final answer is not JSON: Expecting value: line 1 column 1 (char 0)
- `work-01`: error: final answer is not JSON: Extra data: line 1 column 1175 (char 1174)
- `work-02`: error: final answer is not JSON: Expecting value: line 1 column 1 (char 0)
- `work-03`: error: final answer is not JSON: Expecting value: line 1 column 1 (char 0)
- `work-04`: error: final answer is not JSON: Expecting value: line 1 column 1 (char 0)
