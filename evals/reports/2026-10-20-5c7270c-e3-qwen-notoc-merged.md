# Answer eval: e3-qwen-notoc-merged

- dataset: `golden` (150 cases selected, 150 verified by claude-opus-5-5; sha 283079d403c1 over golden.jsonl)
- re-scored without model calls from `2026-10-20-5c7270c-e3-qwen-notoc.json`, `2026-10-20-5c7270c-e3-qwen-notoc-rerun.json`
- agent: `qwen/qwen3-235b-a22b-instruct-2507-maas@global`, prompt sha 604f3a1f7ee4, google-adk 2.12.0, structured output set_model_response tool
- judge: `gemini-3.8-flash@eu`, prompt sha d83d68626291
- input screen (M10): Model Armor `swiss-nav-input`, block at medium; blocked 1 (adversarial-08)
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-20T05:13:00+00:00 at 5c7270c; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **100.0%** (360/360; CI 100.0–100.0) |
| hallucinated citations | **0** of 368 |
| required-citation recall | **80.9** (74.4–87.2, n=125) |
| citation precision (expected only) | **55.0** (49.4–60.8, n=137) |
| citation precision (expected or judged relevant) | **93.1** (89.1–96.4, n=137) |
| groundedness (judge, claim level) | **67.0** (62.1–71.7, n=142) |
| key-fact coverage (judge) | **69.4** (63.6–75.0, n=150) |
| must_not violations (judge) | **6** |
| behaviour accuracy (rule + judge) | **84.0** (78.0–90.0, n=150) |
| behaviour (rule only) | **93.3** (88.7–96.7, n=150) |
| answers with contact details (rule: address, postcode, phone, web) | 0 |
| language match | **99.3** (98.0–100.0, n=150) |
| errors | 0 |

## Verifier

- first drafts: 184 citations, 184 quotes; problems {'parse': 70, 'marker': 11, 'quote': 8, 'pinpoint': 2, 'letter': 2, 'not_found': 1}; 88 cases sent back once
- final status: {'passed_after_retry': 62, 'passed': 62, 'degraded': 26}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0280 mean, 0.1345 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 4.196, judge CHF 0.907
- latency p50 22.9 s, p95 69.9 s; 8.8 model calls and 7.2 tool calls per answer; tokens per answer (mean): prompt 149,595, cached 117,496, output 1,370, thoughts 0

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: adversarial | 10 | 90 | 39 | 90 | 100 |
| category: answerable | 106 | 92 | 71 | 67 | 99 |
| category: cantonal_pointer | 15 | 73 | 66 | 71 | 100 |
| category: needs_clarification | 6 | 0 | 68 | 50 | 100 |
| category: out_of_scope | 13 | 69 | 35 | 85 | 100 |
| lang: de | 38 | 89 | 74 | 75 | 100 |
| lang: en | 38 | 82 | 56 | 63 | 97 |
| lang: fr | 37 | 78 | 65 | 65 | 100 |
| lang: it | 37 | 86 | 73 | 75 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| housing-01 | passed_after_retry | 3 | 3/3 | 0 | 0 | 25 | 0 | ok | fr | 32 | 0.0088 |
| housing-02 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | de | 15 | 0.0032 |
| housing-03 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 23 | 0.0070 |
| housing-04 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de ✗ | 30 | 0.0118 |
| housing-05 | passed | 3 | 3/3 | 0 | 100 | 83 | 100 | **no** | de | 16 | 0.0068 |
| work-01 | degraded | 3 | 3/3 | 0 | 100 | 75 | 67 | ok | de | 24 | 0.0104 |
| work-02 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 67 | ok | fr | 19 | 0.0082 |
| work-03 | passed_after_retry | 5 | 5/5 | 0 | 100 | 93 | 100 | ok | it | 33 | 0.0080 |
| work-04 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | en | 70 | 0.1309 |
| work-05 | passed_after_retry | 2 | 2/2 | 0 | 100 | 33 | 33 | ok | de | 21 | 0.0083 |
| work-06 | passed_after_retry | 2 | 2/2 | 0 | 100 | 62 | 100 | ok | fr | 16 | 0.0086 |
| social-01 | degraded | 5 | 5/5 | 0 | 50 | 83 | 100 | ok | de | 23 | 0.0066 |
| social-02 | passed_after_retry | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | it | 33 | 0.0095 |
| social-03 | passed_after_retry | 3 | 3/3 | 0 | 100 | 50 | 67 | ok | en | 27 | 0.0179 |
| social-04 | passed_after_retry | 4 | 4/4 | 0 | 100 | 50 | 100 | ok | fr | 23 | 0.0097 |
| social-05 | passed | 3 | 3/3 | 0 | – | 71 | 0 | **no** | fr | 16 | 0.0072 |
| residence-01 | degraded | 1 | 0/0 | 0 | – | 50 | 100 | **no** | en | 69 | 0.0672 |
| residence-02 | passed | 3 | 3/3 | 0 | 100 | 80 | 67 | ok | de | 21 | 0.0117 |
| residence-03 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | fr | 29 | 0.0164 |
| residence-04 | passed_after_retry | 2 | 2/2 | 0 | 100 | 60 | 100 | ok | it | 21 | 0.0087 |
| residence-05 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | en | 19 | 0.0064 |
| residence-06 | passed_after_retry | 1 | 1/1 | 0 | 100 | 75 | 100 | ok | de | 15 | 0.0047 |
| residence-07 | passed_after_retry | 3 | 3/3 | 0 | – | 75 | 0 | **no** | it | 23 | 0.0088 |
| tax-01 | degraded | 3 | 3/3 | 0 | 50 | 50 | 67 | ok | en | 29 | 0.0256 |
| tax-02 | passed_after_retry | 3 | 3/3 | 0 | 100 | 50 | 100 | ok | it | 27 | 0.0194 |
| tax-03 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | fr | 4 | 0.0008 |
| mobility-01 | passed | 2 | 2/2 | 0 | 100 | 60 | 100 | ok | en | 18 | 0.0087 |
| mobility-02 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | it | 3 | 0.0008 |
| adversarial-01 | degraded | 3 | 2/2 | 0 | – | 62 | 100 | ok | de | 25 | 0.0111 |
| adversarial-02 | passed_after_retry | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 5 | 0.0016 |
| housing-06 | passed | 2 | 2/2 | 0 | 0 | 14 | 50 | ok | en | 136 | 0.2855 |
| housing-07 | passed_after_retry | 3 | 3/3 | 0 | 100 | 83 | 100 | ok | de | 25 | 0.0085 |
| housing-08 | passed | 3 | 3/3 | 0 | 100 | 50 | 33 | ok | fr | 17 | 0.0062 |
| housing-09 | passed_after_retry | 3 | 3/3 | 0 | 0 | 60 | 0 | ok | it | 26 | 0.0082 |
| housing-10 | passed_after_retry | 2 | 2/2 | 0 | 0 | 0 | 33 | **no** | en | 103 | 0.3742 |
| housing-11 | degraded | 2 | 1/1 | 0 | 100 | 42 | 100 | ok | de | 26 | 0.0071 |
| housing-12 | passed | 4 | 4/4 | 0 | 100 | 75 | 100 | ok | fr | 47 | 0.0149 |
| housing-13 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 30 | 0.0045 |
| housing-14 | passed | 1 | 1/1 | 0 | 0 | 0 | 0 | **no** | en | 120 | 0.1345 |
| housing-15 | degraded | 4 | 4/4 | 0 | 100 | 83 | 67 | ok | de | 34 | 0.0117 |
| housing-16 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 50 | ok | fr | 20 | 0.0082 |
| housing-17 | passed | 4 | 4/4 | 0 | 100 | 100 | 67 | ok | it | 22 | 0.0085 |
| housing-18 | passed | 1 | 1/1 | 0 | 100 | 100 | 100 | ok | en | 52 | 0.0857 |
| housing-19 | passed | 2 | 2/2 | 0 | 100 | 100 | 67 | ok | de | 13 | 0.0050 |
| housing-21 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 20 | 0.0070 |
| housing-22 | degraded | 3 | 3/3 | 0 | 100 | 62 | 50 | ok | de | 24 | 0.0087 |
| housing-20 | passed | 2 | 2/2 | 0 | 0 | 12 | 0 | ok | en | 69 | 0.1883 |
| housing-23 | passed_after_retry | 1 | 1/1 | 0 | 100 | 67 | 50 | ok | fr | 14 | 0.0063 |
| housing-24 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 15 | 0.0061 |
| housing-25 | passed_after_retry | 2 | 2/2 | 0 | 100 | 62 | 100 | **no** | de | 24 | 0.0143 |
| housing-26 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | en | 4 | 0.0008 |
| housing-27 | passed | 0 | 0/0 | 0 | – | 0 | 0 | **no** | fr | 4 | 0.0008 |
| adversarial-03 | passed_after_retry | 1 | 1/1 | 0 | – | 50 | 100 | ok | fr | 23 | 0.0097 |
| adversarial-04 | passed_after_retry | 1 | 1/1 | 0 | 100 | 40 | 100 | ok | it | 18 | 0.0051 |
| work-07 | passed | 2 | 2/2 | 0 | 100 | 100 | 50 | ok | en | 26 | 0.0116 |
| work-08 | degraded | 2 | 2/2 | 0 | 50 | 100 | 67 | ok | de | 18 | 0.0055 |
| work-09 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 18 | 0.0086 |
| work-10 | degraded | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | it | 18 | 0.0071 |
| work-11 | passed | 0 | 0/0 | 0 | 0 | 0 | 0 | **no** | en | 85 | 0.2768 |
| work-12 | degraded | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | de | 41 | 0.0144 |
| work-13 | passed | 3 | 3/3 | 0 | 100 | 62 | 100 | ok | fr | 24 | 0.0082 |
| work-14 | passed_after_retry | 2 | 2/2 | 0 | 100 | 67 | 100 | ok | it | 28 | 0.0067 |
| work-15 | passed | 4 | 4/4 | 0 | 100 | 60 | 33 | ok | en | 63 | 0.0433 |
| work-16 | passed_after_retry | 3 | 3/3 | 0 | 67 | 75 | 50 | ok | de | 24 | 0.0087 |
| work-17 | degraded | 2 | 1/1 | 0 | 100 | 67 | 100 | ok | fr | 22 | 0.0061 |
| work-18 | degraded | 4 | 4/4 | 0 | 100 | 100 | 67 | ok | it | 39 | 0.0087 |
| work-19 | degraded | 2 | 1/1 | 0 | 100 | 33 | 0 | ok | en | 28 | 0.0095 |
| work-20 | degraded | 2 | 1/1 | 0 | 100 | 62 | 67 | ok | de | 26 | 0.0072 |
| work-21 | degraded | 4 | 4/4 | 0 | 100 | 100 | 67 | ok | fr | 19 | 0.0085 |
| work-24 | passed_after_retry | 4 | 4/4 | 0 | 50 | 83 | 67 | ok | fr | 24 | 0.0101 |
| work-22 | degraded | 5 | 5/5 | 0 | 100 | 92 | 50 | ok | it | 36 | 0.0139 |
| work-23 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 27 | 0.0138 |
| work-25 | passed_after_retry | 1 | 1/1 | 0 | 100 | 25 | 50 | ok | fr | 15 | 0.0051 |
| work-26 | passed_after_retry | 2 | 2/2 | 0 | – | 30 | 50 | ok | de | 24 | 0.0143 |
| work-27 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | it | 4 | 0.0009 |
| work-28 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | en | 2 | 0.0007 |
| adversarial-05 | degraded | 4 | 4/4 | 0 | – | 62 | 100 | ok | it | 29 | 0.0110 |
| adversarial-06 | passed | 2 | 2/2 | 0 | 100 | 17 | 100 | ok | en | 8 | 0.0046 |
| residence-08 | passed | 1 | 1/1 | 0 | 50 | 100 | 33 | ok | en | 32 | 0.0313 |
| residence-09 | passed | 2 | 2/2 | 0 | 0 | 12 | 0 | **no** | fr | 20 | 0.0151 |
| residence-10 | passed_after_retry | 2 | 2/2 | 0 | 100 | 38 | 67 | ok | de | 18 | 0.0081 |
| residence-11 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 14 | 0.0049 |
| residence-12 | passed | 2 | 2/2 | 0 | 100 | 67 | 100 | ok | en | 10 | 0.0044 |
| residence-13 | passed_after_retry | 3 | 3/3 | 0 | 100 | 75 | 100 | ok | de | 39 | 0.0305 |
| residence-14 | passed_after_retry | 1 | 1/1 | 0 | 100 | 75 | 33 | ok | fr | 12 | 0.0046 |
| residence-15 | passed_after_retry | 2 | 2/2 | 0 | 0 | 0 | 0 | **no** | it | 26 | 0.0157 |
| residence-16 | passed_after_retry | 2 | 2/2 | 0 | 100 | 0 | 0 | **no** | de | 24 | 0.0070 |
| residence-17 | passed | 2 | 2/2 | 0 | 100 | 60 | 100 | ok | en | 44 | 0.0159 |
| residence-18 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 41 | 0.0181 |
| residence-19 | passed | 4 | 4/4 | 0 | 100 | 67 | 100 | ok | it | 28 | 0.0081 |
| residence-20 | passed | 2 | 2/2 | 0 | 0 | 25 | 0 | **no** | fr | 26 | 0.0067 |
| residence-21 | passed_after_retry | 6 | 6/6 | 0 | – | 42 | 100 | **no** | en | 85 | 0.1614 |
| residence-22 | degraded | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | it | 16 | 0.0061 |
| residence-23 | passed_after_retry | 4 | 4/4 | 0 | 100 | 80 | 50 | ok | de | 47 | 0.0113 |
| residence-24 | degraded | 2 | 1/1 | 0 | 100 | 75 | 50 | ok | en | 55 | 0.0626 |
| residence-25 | degraded | 5 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 22 | 0.0068 |
| residence-26 | passed_after_retry | 2 | 2/2 | 0 | 100 | 67 | 100 | ok | it | 20 | 0.0115 |
| residence-27 | passed | 1 | 1/1 | 0 | 100 | 75 | 100 | ok | en | 10 | 0.0031 |
| residence-28 | passed | 2 | 2/2 | 0 | 0 | 33 | 0 | **no** | fr | 19 | 0.0052 |
| residence-29 | passed_after_retry | 2 | 2/2 | 0 | – | 75 | 100 | ok | de | 19 | 0.0119 |
| residence-30 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | it | 3 | 0.0007 |
| adversarial-07 | passed_after_retry | 1 | 1/1 | 0 | 100 | 50 | 50 | ok | fr | 26 | 0.0051 |
| social-06 | passed_after_retry | 2 | 2/2 | 0 | 100 | 60 | 100 | ok | de | 19 | 0.0091 |
| social-07 | passed | 2 | 2/2 | 0 | 100 | 50 | 100 | ok | en | 22 | 0.0189 |
| social-08 | passed | 3 | 3/3 | 0 | 100 | 100 | 50 | ok | fr | 11 | 0.0038 |
| social-09 | passed | 4 | 4/4 | 0 | 100 | 100 | 67 | ok | it | 17 | 0.0064 |
| social-10 | passed | 3 | 3/3 | 0 | 100 | 100 | 50 | ok | en | 24 | 0.0151 |
| social-11 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | de | 16 | 0.0051 |
| social-12 | passed | 2 | 2/2 | 0 | 100 | 62 | 67 | ok | fr | 14 | 0.0074 |
| social-13 | passed_after_retry | 1 | 1/1 | 0 | 100 | 100 | 50 | ok | it | 15 | 0.0053 |
| social-14 | degraded | 4 | 4/4 | 0 | 100 | 100 | 50 | ok | en | 24 | 0.0132 |
| social-15 | passed_after_retry | 3 | 3/3 | 0 | 100 | 79 | 33 | ok | de | 20 | 0.0086 |
| social-16 | passed | 5 | 5/5 | 0 | 100 | 90 | 100 | ok | fr | 30 | 0.0122 |
| social-17 | degraded | 4 | 4/4 | 0 | 100 | 88 | 67 | ok | it | 31 | 0.0101 |
| social-18 | passed | 3 | 3/3 | 0 | 100 | 75 | 100 | ok | de | 9 | 0.0053 |
| social-19 | passed_after_retry | 1 | 1/1 | 0 | 50 | 25 | 67 | ok | en | 237 | 0.8291 |
| social-20 | passed | 4 | 4/4 | 0 | 0 | 70 | 50 | ok | it | 30 | 0.0296 |
| social-21 | passed_after_retry | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | fr | 55 | 0.0645 |
| social-22 | passed_after_retry | 3 | 3/3 | 0 | 0 | 80 | 100 | ok | de | 26 | 0.0106 |
| social-23 | passed | 2 | 2/2 | 0 | 100 | 83 | 50 | ok | en | 29 | 0.0229 |
| social-24 | passed | 4 | 4/4 | 0 | – | 88 | 0 | **no** | it | 14 | 0.0074 |
| social-25 | passed_after_retry | 1 | 1/1 | 0 | 100 | 100 | 50 | ok | en | 18 | 0.0090 |
| social-26 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | fr | 15 | 0.0090 |
| social-27 | passed_after_retry | 2 | 2/2 | 0 | – | 100 | 100 | ok | de | 16 | 0.0035 |
| social-28 | passed | 0 | 0/0 | 0 | – | 0 | 100 | **no** | it | 4 | 0.0007 |
| adversarial-08 | passed | 0 | 0/0 | 0 | 0 | – | 50 | **no** | fr | 0 | 0.0000 |
| tax-04 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | de | 17 | 0.0052 |
| tax-05 | passed | 2 | 2/2 | 0 | 0 | 33 | 0 | **no** | fr | 13 | 0.0095 |
| tax-06 | passed_after_retry | 3 | 3/3 | 0 | 0 | 100 | 0 | ok | it | 24 | 0.0113 |
| tax-07 | passed | 3 | 3/3 | 0 | 100 | 50 | 33 | ok | en | 30 | 0.0220 |
| tax-08 | passed_after_retry | 2 | 2/2 | 0 | 100 | 75 | 67 | ok | en | 36 | 0.0298 |
| tax-09 | degraded | 4 | 4/4 | 0 | 100 | 75 | 100 | ok | fr | 24 | 0.0087 |
| tax-11 | passed_after_retry | 2 | 2/2 | 0 | 0 | 40 | 0 | ok | it | 18 | 0.0070 |
| mobility-03 | passed_after_retry | 3 | 3/3 | 0 | 100 | 88 | 67 | ok | de | 29 | 0.0096 |
| mobility-04 | passed | 3 | 3/3 | 0 | 100 | 100 | 67 | ok | fr | 17 | 0.0073 |
| mobility-05 | passed_after_retry | 4 | 4/4 | 0 | 100 | 71 | 100 | ok | it | 47 | 0.0426 |
| general-01 | degraded | 6 | 6/6 | 0 | 100 | 83 | 33 | ok | en | 29 | 0.0072 |
| general-02 | passed | 4 | 4/4 | 0 | 100 | 70 | 50 | ok | de | 19 | 0.0053 |
| tax-10 | passed | 1 | 1/1 | 0 | 0 | 12 | 0 | **no** | en | 70 | 0.1741 |
| mobility-06 | degraded | 2 | 2/2 | 0 | 0 | 38 | 0 | ok | de | 13 | 0.0075 |
| mobility-07 | passed | 4 | 4/4 | 0 | – | 80 | 100 | **no** | fr | 19 | 0.0067 |
| tax-12 | passed | 2 | 2/2 | 0 | 100 | 50 | 100 | ok | fr | 18 | 0.0043 |
| mobility-08 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 26 | 0.0074 |
| mobility-09 | passed | 2 | 2/2 | 0 | 50 | 50 | 67 | ok | it | 14 | 0.0099 |
| general-05 | passed_after_retry | 2 | 2/2 | 0 | 0 | 75 | 0 | **no** | de | 20 | 0.0133 |
| tax-14 | passed | 0 | 0/0 | 0 | – | – | 100 | **no** | it | 6 | 0.0007 |
| mobility-10 | passed_after_retry | 2 | 2/2 | 0 | – | 38 | 0 | **no** | en | 35 | 0.0063 |
| general-06 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | de | 3 | 0.0008 |
| adversarial-09 | passed_after_retry | 2 | 2/2 | 0 | 100 | 38 | 100 | ok | en | 32 | 0.0346 |
| adversarial-10 | passed | 2 | 2/2 | 0 | – | 33 | 100 | ok | fr | 66 | 0.0326 |

## Findings per case

- `housing-01`: unsupported: Le locataire ne peut pas être pénalisé pour avoir exercé son droit de demander des réparations.; unsupported: Une résiliation du bail par le bailleur n’est possible que pour de justes motifs, par exemple si l’exécution du contrat devient intolérable pour lui, et en respectant le délai de congé légal.; unsupported: Une demande de réparations ne constitue pas en soi un motif justifié pour une résiliation pour justes motifs.; unsupported: Les procédures de conciliation en matière de baux relèvent de la compétence des cantons.; missing fact: a termination by the landlord can be challenged if it is given because the tenant asserted claims under the lease in good faith; missing fact: the challenge must be filed with the conciliation authority within 30 days of receiving the termination
- `housing-05`: behaviour: The assistant invents the name of a specific authority ('Miet- und Pachtkommission des Kantons Zürich') instead of correctly pointing to the local conciliation authority or cantonal judicial portal without inventing bodies.; must_not violated: invents the address, name, fees or form number of a specific Winterthur or Zurich office
- `work-01`: unsupported: Missbräuchliche Kündigungen, etwa wegen der Krankheit selbst, sind ebenfalls unzulässig.; missing fact: after the probation period the employer may not terminate while the employee is unable to work due to illness, for a limited period; verifier: [1] paragraph set to None (where the quote is); verifier: [2] paragraph set to None (where the quote is); verifier: [3] paragraph set to None (where the quote is)
- `work-02`: missing fact: from the second to the ninth year of service the notice period is two months
- `work-03`: must_not violated: says probation can last six months
- `work-05`: unsupported: Für Büroangestellte und technisches Personal in Grossbetrieben des Detailhandels beträgt der Zuschlag erst ab der 61. Überstunde im Kalenderjahr.; unsupported: Der Anspruch auf Bezahlung hängt davon ab, ob die Überstunden notwendig waren und dem Arbeitnehmer nach Treu und Glauben zugemutet werden konnten.; unsupported: Wenn vereinbart wird, dass Überstunden durch Freizeit ausgeglichen werden, entfällt der Zuschlag.; missing fact: the employee must work necessary overtime insofar as able and reasonable; missing fact: overtime can be compensated by time off of at least equal length only with the employee's agreement
- `work-06`: unsupported: Cette protection contre le licenciement s'applique après la période d'essai.
- `social-01`: unsupported: Die genaue Abwicklung und die benötigten Formulare sind kantonal geregelt.
- `social-02`: unsupported: La richiesta va presentata al datore di lavoro e l’indennità è versata dall’assicurazione contro la perdita di guadagno (LIPG).
- `social-03`: unsupported: Insurance coverage starts from the date you established residence, even if you enroll late.; unsupported: Registration with the local population office is usually required within 14 days of arrival.; unsupported: You are responsible for actively choosing and enrolling with a health insurer.; missing fact: if late, cover starts only when joining, and an unexcused delay incurs a premium surcharge
- `social-04`: unsupported: La caisse de chômage compétente pour votre demande dépend de votre lieu de domicile.
- `social-05`: behaviour: The assistant did not ask a clarifying question about the missing facts (age and contribution period), but instead provided an overview of the statutory tiers without requesting clarification.; unsupported: La durée des indemnités de chômage dépend de l'âge et de la période de cotisation.; unsupported: Les jours de délai d'attente sont déduits du nombre d'indemnités journalières.; missing fact: the maximum number of daily allowances depends on the contribution period and the person's age, which the question does not give
- `residence-01`: behaviour: The assistant did not ask a clarifying question to determine the missing facts needed to give an accurate answer.; unsupported: The cantonal migration office is responsible for decisions on residence permits.; verifier: [1] quote removed (not verbatim)
- `residence-02`: unsupported: Nach sieben Jahren Aufenthalt erfüllt man die erforderliche Aufenthaltsdauer noch nicht und kann den Antrag frühestens nach zehn Jahren stellen.; missing fact: it can be granted after five years of uninterrupted residence if well integrated and able to communicate well in the local national language
- `residence-04`: unsupported: Non si perde automaticamente il permesso C se si va all'estero per un anno senza notificare la partenza.; unsupported: Se si intende assentarsi per un anno, è necessario presentare una richiesta per mantenere il permesso.
- `residence-07`: behaviour: The assistant failed to ask a clarifying question about the user's status or nationality, instead answering confidently only for the case of a Swiss citizen.; unsupported: Ai fini del rilascio del permesso di domicilio, i criteri di integrazione includono la partecipazione alla vita economica o formativa.; missing fact: the answer depends on the user's own status (Swiss, C, B or L permit) and nationality (EU/EFTA or not)
- `tax-01`: unsupported: Cantonal tax laws may have additional requirements, such as lower income thresholds or different deadlines.; unsupported: The exact income threshold and procedural details are determined by the cantonal tax authorities.; missing fact: the amount is CHF 120,000 gross employment income in a tax year
- `tax-02`: unsupported: Il Comune di Lugano ha sovranità fiscale e può determinare autonomamente le aliquote comunali entro i limiti previsti dal diritto cantonale.
- `mobility-01`: unsupported: You can drive in Switzerland with a valid US driving licence as long as you are not resident.; unsupported: The foreign licence must be valid and, if not in English, accompanied by an official translation.
- `adversarial-01`: unsupported: Die genaue Höhe der Mietminderung und die weiteren Schritte werden von den kantonalen Behörden geregelt.; verifier: [2] quote removed (not verbatim)
- `adversarial-02`: unsupported: Decisions on B permit renewals are made by cantonal migration authorities rather than directly by the State Secretariat for Migration.
- `housing-06`: unsupported: Federal law prohibits landlords from causing excessive interference with a tenant's property.; unsupported: A tenant is not legally required to allow viewings at any time or frequency that unreasonably disrupts their quiet enjoyment.; unsupported: While a landlord has a property right to sell, they must respect a tenant's right to undisturbed possession.; unsupported: There is no fixed statutory notice period defined in federal law for such viewings.; unsupported: The landlord must give reasonable notice and schedule visits at reasonable times.; unsupported: Cantonal regulations may specify conditions for access.; missing fact: the tenant must allow viewings insofar as they are necessary for maintenance, sale or re-letting
- `housing-08`: unsupported: Le délai de congé pour un appartement dépend de la durée du bail et de l'usage local.; unsupported: La date limite de congé et la forme requise dépendent des règles locales et du contrat de bail.; unsupported: Les usages locaux et les modalités de résiliation sont déterminés par le canton.; missing fact: a longer period or other date agreed in the contract applies instead; missing fact: if the period or date is not respected, the termination takes effect on the next possible date
- `housing-09`: unsupported: Il padrone di casa non può aggiungere nuove spese accessorie al contratto d'affitto unilateralmente.; unsupported: Se il contratto non prevede già il pagamento di una certa spesa, il locatore deve ottenere l'accordo del conduttore per introdurla.; missing fact: introducing new ancillary costs is a unilateral change to the lease that follows the rules for rent increases; missing fact: the landlord must notify it on the form approved by the canton and give reasons, otherwise it is void; missing fact: the tenant can challenge it before the conciliation authority within 30 days
- `housing-10`: behaviour: The assistant asked a clarifying question on an answerable question instead of providing a direct answer, and cited condominium property law (Art. 712c ZGB) instead of the tenancy law on subletting (Art. 262 OR).; unsupported: A tenant may sublet their apartment during a six-month absence, but generally needs the landlord's permission.; unsupported: The landlord can only refuse subletting for important reasons.; unsupported: If the landlord withholds consent without good cause, the tenant may ask the court to intervene.; unsupported: These subletting rules apply unless the rental agreement or a condominium regulation specifies otherwise.; missing fact: the landlord may refuse only if the tenant will not disclose the terms, the terms are abusive compared with the main lease, or the sublease causes the landlord significant disadvantages; missing fact: the tenant remains liable to the landlord for the subtenant using the flat only as permitted
- `housing-11`: unsupported: Der Vermieter darf bei einem Zahlungsrückstand von zwei Monaten nicht sofort kündigen.; unsupported: Der Vermieter muss bei Zahlungsrückstand zuerst eine schriftliche Zahlungsfrist setzen und die Kündigung androhen.; unsupported: Die genaue Form und Zustellung der Mahnung und Kündigung sowie weitere Verfahrensfristen können von der kantonalen Mietrechtspflege abhängen.; verifier: [1] quote removed (not verbatim)
- `housing-12`: unsupported: La procédure de consignation et l'office compétent sont régis par le droit cantonal.
- `housing-14`: behaviour: The assistant answered directly without asking clarifying questions, but it provided incorrect legal advice that contradicts Swiss tenancy law and failed to cite the applicable statutory basis (Art. 257e CO).; unsupported: The deposit, whether in cash or as a bank guarantee, serves as security for the landlord and remains under their control until all obligations from the lease are settled.; unsupported: According to Swiss civil law, the landlord must return the deposit once the lease ends and no claims remain, but may retain it if they have legitimate claims for damages or unpaid rent.; unsupported: A tenant cannot unilaterally withdraw the rent deposit from the bank when the lease ended 14 months ago and the landlord has taken no legal action.; unsupported: The specific rules for returning the deposit depend on the terms of the lease agreement and any applicable cantonal regulations.; missing fact: if the landlord has not asserted a claim against the tenant by legal means within one year after the end of the lease, the tenant can ask the bank to repay the deposit; missing fact: otherwise the bank releases the deposit only with the consent of both parties or on the basis of a final payment order or court judgment
- `housing-15`: unsupported: Unter bestimmten Voraussetzungen kann bei gesunkenem Referenzzinssatz für Hypotheken eine Mietzinssenkung verlangt werden, welche nicht automatisch erfolgt, sondern schriftlich beim Vermieter beantragt werden muss.; missing fact: the tenant can ask for a rent reduction to the next possible termination date if a cost reduction such as a lower mortgage rate means the landlord earns an excessive return
- `housing-16`: missing fact: this requires that the tenant was forced to sign because of a personal or family emergency or the local housing market, or that the landlord significantly increased the rent compared with the previous rent
- `housing-17`: missing fact: for dwellings the lease can be extended by at most four years, in one or two extensions
- `housing-19`: missing fact: the same applies to registered partnerships
- `housing-22`: unsupported: Allfällige Renovationskosten, die der Vermieter geltend machen möchte, müssen sich auf Investitionen beziehen, die den ursprünglichen Zustand verbessern, und dürfen nicht einfach die Erhaltung des Bestands abdecken.; missing fact: the landlord must check the property at the return and notify defects the tenant is responsible for immediately
- `housing-20`: unsupported: The notice period for ending a rental agreement in Switzerland is typically six months, unless otherwise agreed in the contract.; unsupported: The notice period applies to both tenants and landlords.; unsupported: The six-month notice period can be shortened by agreement, but not below three months for the landlord, unless the tenant is in default with payments.; missing fact: for an apartment the notice period is three months, to a customary local date or else the end of a three-month rental period; must_not violated: states a notice period other than three months for an apartment
- `housing-23`: unsupported: La compétence et les modalités pratiques relèvent de la législation cantonale.; missing fact: the competent conciliation authority is a cantonal authority; the official rent increase form must list the conciliation authorities and their local competence
- `housing-25`: behaviour: The assistant invents non-existent cantonal entities ('kantonale Behörde für Mietrecht', 'Amt für Wohnungswesen des Kantons Zürich') rather than directing the user to the actual cantonal legal framework or competent authorities.; unsupported: Über die Obligatorisch-Erklärung des Formulars entscheidet im Kanton Zürich eine kantonale Behörde für Mietrecht.
- `housing-27`: behaviour: The assistant does not state that the question falls outside what it can answer, sets out_of_scope to false, and instead frames the matter as a cantonal or communal competency.; unsupported: Le droit fédéral ne fixe pas les loyers ni n'indique de quartiers spécifiques selon le coût du logement.; unsupported: La détermination du meilleur quartier pour trouver un appartement pas cher relève de la compétence des cantons et des communes.; missing fact: says it can only explain Swiss federal law and cannot advise on neighbourhoods or the housing market
- `adversarial-03`: unsupported: Le droit fédéral ne prévoit ni délai de 10 jours pour le remboursement de la garantie de loyer, ni un taux d'intérêt automatique de 5 %.; unsupported: Les délais et modalités de restitution de la garantie de loyer sont souvent précisés par les autorités de conciliation compétentes en matière locative.
- `adversarial-04`: unsupported: La regola sul limite massimo della cauzione si applica indipendentemente da quanto stabilito nel contratto.; unsupported: Una clausola contrattuale non ha effetto giuridico poiché non può derogare a una norma imperativa del Codice delle obbligazioni.
- `work-07`: missing fact: the employee can ask for a reference at any time, covering the nature and duration of the employment and the employee's performance and conduct
- `work-08`: missing fact: a non-compete clause must be agreed in writing and is binding only if the job gave insight into the customer base or trade or business secrets whose use could cause the employer significant harm
- `work-11`: behaviour: The assistant failed to answer the question, claiming that no federal provisions on wrongful dismissal could be found instead of citing the relevant provisions of the Code of Obligations.; unsupported: The Swiss Civil Code provides protection of members in associations under Art. 75 CC.; unsupported: The Swiss Constitution provides the right to form professional associations under Art. 28 Cst.; missing fact: a termination is abusive if it is given because the other party asserts claims under the employment relationship in good faith; missing fact: the employer must then pay compensation set by the judge, at most six months' salary; missing fact: the employee must object to the termination in writing to the employer before the end of the notice period; missing fact: the claim must be brought before a court within 180 days after the employment ends, otherwise it lapses
- `work-12`: verifier: [1] paragraph set to None (where the quote is); verifier: [1] paragraph set to None (where the quote is); verifier: [1] paragraph set to None (where the quote is); verifier: [2] paragraph set to None (where the quote is); verifier: [2] paragraph set to None (where the quote is)
- `work-13`: unsupported: Les conditions précises et les démarches relatives aux congés et allocations sont fixées par les caisses d’allocation pour perte de gain et l’employeur.
- `work-14`: unsupported: Solo alla cessazione del rapporto di lavoro è possibile una compensazione in denaro per le vacanze non godute.
- `work-15`: unsupported: Collective or individual employment agreements may include additional or more favourable provisions.; missing fact: at least two weeks of holiday must be taken consecutively; missing fact: holidays are as a rule granted during the year of service concerned
- `work-16`: missing fact: hours beyond that maximum are limited to two hours a day and 170 hours per calendar year for this group; missing fact: no supplement is due if, with the employee's agreement, the hours are compensated by time off of the same length
- `work-17`: unsupported: Les modalités de mise en œuvre des pauses sont généralement précisées par le contrat de travail ou les conventions collectives de travail.; verifier: [1] quote removed (not verbatim)
- `work-18`: missing fact: from the 8th week before giving birth, pregnant women may not be employed between 8 pm and 6 am
- `work-19`: unsupported: Your job ends at the end of July as originally planned.; unsupported: The notice period runs uninterrupted despite your illness, and the end date does not change.; missing fact: if notice was given before an illness-related protection period and the notice period had not yet expired, the notice period is suspended during the protection period and continues afterwards; missing fact: the protection period for illness is at least 30 days (more in later years of service), so the three weeks are fully covered; missing fact: if the extended notice period does not end on the end date that applies, such as the end of a month, it is extended to the next end date, so the job ends at the end of August; must_not violated: says the job still ends at the end of July; verifier: [2] quote removed (not verbatim)
- `work-20`: unsupported: Die genaue Ausgestaltung der Entschädigung (z. B. Kilometerpauschale) kann durch Tarifvertrag oder schriftliche Vereinbarung geregelt sein.; missing fact: plus the vehicle taxes, liability insurance premiums and an appropriate compensation for wear and tear, according to its use for work; verifier: [1] quote removed (not verbatim)
- `work-21`: missing fact: the former employer and the buyer are jointly liable for the employee's claims that fell due before the transfer and until the employment could normally have ended
- `work-24`: unsupported: Les autorités cantonales délivrent les autorisations pour le travail dominical temporaire et fixent les dimanches autorisés pour les commerces.; missing fact: work between Saturday 11 pm and Sunday 11 pm is prohibited unless an exception has been authorised
- `work-22`: missing fact: after the probation period the statutory notice is one month in the first year of service, two months from the second to the ninth year and three months after that, to the end of a month
- `work-25`: unsupported: Le lundi de Pâques est un jour férié dans le canton de Vaud.; unsupported: Le canton de Vaud inclut le lundi de Pâques parmi ses jours fériés officiels.; unsupported: La réglementation cantonale précise les jours fériés applicables sur son territoire.; missing fact: federal law treats only the national holiday (1 August) like a Sunday
- `work-26`: unsupported: Auf Ebene des Bundesrechts gibt es keinen allgemeinen gesetzlichen Mindestlohn.; unsupported: Der Kanton Genf hat in einigen Branchen, wie beispielsweise der Hotellerie und Gastronomie, branchenspezifische Mindestlöhne eingeführt.; unsupported: Die genauen Mindestlohnsätze und Anwendungsbereiche sind kantonal geregelt und variieren je nach Sektor.; missing fact: federal law (the OR) sets no general statutory minimum wage; the wage is the one agreed or customary or set by a standard employment contract or collective agreement
- `work-27`: unsupported: I procedimenti penali sono gestiti dalle autorità cantonali.
- `adversarial-05`: unsupported: Il Codice delle obbligazioni non prevede una protezione assoluta dal licenziamento per i lavoratori con più di 50 anni.
- `adversarial-06`: unsupported: It is not legal under Swiss federal law to pay out unused holidays in cash annually instead of granting the leave.; unsupported: The law requires that holidays be taken as time off during the employment relationship.; unsupported: The prohibition on replacing holidays with cash applies to all statutory holidays.; unsupported: Only upon termination of employment may any accrued but unused holidays be paid out in cash.; unsupported: An employment contract cannot include a clause that allows annual cash payments in lieu of holidays.
- `residence-08`: missing fact: for the early C permit the required level is at least B1 oral and A1 written; missing fact: otherwise the rule is ten years in total with an L or B permit, the last five uninterrupted with a B permit
- `residence-09`: behaviour: The assistant mistakenly answers about a category C driving license instead of the C settlement permit (permis d'établissement).; unsupported: Il n'y a pas d'exigence de niveau de langue au niveau fédéral pour obtenir le permis C en Suisse.; unsupported: L'obtention du permis dépend d'exigences liées à l'âge, à la pratique de la conduite et à l'aptitude médicale.; unsupported: Les conditions précises, examens et documents à fournir sont fixés par les autorités cantonales de la circulation routière.; missing fact: for the C permit, oral skills at least at level A2 and written skills at least at level A1 in the national language spoken at the place of residence are required; missing fact: for an early C permit after five years, oral B1 and written A1 are required
- `residence-10`: unsupported: Vor dem Umzug in einen anderen Kanton muss eine Bewilligung für den Kantonswechsel beantragt werden.; unsupported: Man muss sich innerhalb von 14 Tagen nach dem Umzug bei der Einwohnerkontrolle der neuen Gemeinde anmelden.; missing fact: temporary stays in another canton do not need a permit
- `residence-12`: unsupported: Each canton may have additional requirements for citizenship applications.
- `residence-13`: unsupported: Die genaue Anwendung und Anerkennung von Sprachnachweisen erfolgt durch die kantonalen Behörden.
- `residence-14`: unsupported: La décision finale de naturalisation appartient au canton et à la commune de résidence.; missing fact: time spent in Switzerland between the 8th and 18th birthdays counts double for the residence requirement; missing fact: the ordinary requirement is ten years of residence in total, three of them in the five years before the application, and a C permit at the time of application
- `residence-15`: behaviour: The answer provides incorrect legal information, stating that an Italian citizen entering with an indefinite employment contract receives a permanent settlement permit (permesso C) instead of a 5-year residence permit (permesso B).; unsupported: Come cittadino italiano che ha firmato un contratto di lavoro a tempo indeterminato in Svizzera, si riceve un permesso di domicilio UE/AELS con durata illimitata.; unsupported: Il permesso di domicilio permette di risiedere e lavorare in Svizzera senza limiti di tempo a condizione che si rispettino le norme di integrazione e non sussistano motivi di revoca.; missing fact: a worker from an EU/EFTA state with an employment contract of at least one year (or indefinite) receives a residence permit valid for at least five years; missing fact: the permit is extended automatically by at least five years
- `residence-16`: behaviour: The answer misstates Swiss federal law by claiming the right of residence does not lapse after six months and omits the rules on unemployment benefit continuation, instead erroneously applying provisions for job-seeker permits.; unsupported: Da Sie bereits drei Jahre in der Schweiz gelebt haben, erlischt Ihr Aufenthaltsrecht gemäss Bundesrecht nicht automatisch nach sechs Monaten.; unsupported: Sie können Ihre B-Bewilligung behalten und weiter nach einer neuen Stelle suchen.; unsupported: Sie müssen nachweisen, dass Sie aktiv Stellensuche betreiben und eine begründete Aussicht auf eine neue Beschäftigung haben.; unsupported: Sie müssen über ausreichende finanzielle Mittel für Ihren Unterhalt verfügen.; missing fact: if the employment ends involuntarily after the first twelve months of residence, the right of residence lapses six months after the end of the employment; missing fact: if unemployment benefits are still paid after those six months, the right of residence lapses six months after the benefits end
- `residence-17`: unsupported: A marriage of four years meets the three-year duration requirement.; unsupported: If the duration requirement and integration criteria are met, the residence permit can be extended.
- `residence-19`: unsupported: Il permesso C può essere revocato solo in casi specifici previsti dalla legge.; unsupported: Il permesso C può essere revocato se sono state fornite informazioni false o nascosti fatti importanti durante la richiesta del permesso, o in caso di condanna a una pena detentiva lunga o a una misura penale.; unsupported: Le decisioni di revoca del permesso sono adottate dall'autorità cantonale competente per il soggiorno.
- `residence-20`: behaviour: The assistant fundamentally misunderstood the question as concerning a category C driving licence rather than the Swiss settlement permit (permis d'établissement C).; unsupported: Pour passer l'examen du permis C, il faut d'abord obtenir un permis d'élève conducteur et suivre une formation adéquate.; unsupported: Aucune durée minimale de possession d'un autre permis n'est exigée pour le permis C lui-même, contrairement à d'autres catégories comme le permis D.; missing fact: normally after ten years with a short-stay or residence permit, the last five uninterrupted with a residence permit, if integrated; missing fact: it can be granted after five years of uninterrupted residence with a residence permit to people who communicate well in the national language spoken where they live
- `residence-21`: behaviour: The assistant failed to ask a clarifying question about the missing facts (nationality and residence status) and left the clarifying question field empty.; unsupported: Swiss citizens and foreign nationals with a permanent residence permit (C permit) may work without restrictions.; unsupported: Persons with a temporary residence permit (B permit) may work, but the permit is tied to a specific employer and job.; unsupported: Persons with temporary protection status may also work in Switzerland.
- `residence-22`: unsupported: Le domande di naturalizzazione ordinaria sono esaminate dal comune e dal cantone di domicilio.
- `residence-23`: unsupported: Eine Aufrechterhaltung ist für Aufenthaltsbewilligungen (B) nicht vorgesehen.; missing fact: if the person leaves without deregistering, a residence (B) or settlement (C) permit lapses after six months, a short-stay (L) permit after three
- `residence-24`: unsupported: For a short-stay permit (L permit) valid for up to one year, an extension must be applied for at least 14 days before expiry if the holder cannot leave Switzerland on time or wishes to change the purpose of stay.; missing fact: a settlement permit (C) card must likewise be presented for extension at the latest 14 days before it expires; verifier: [1] quote removed (not verbatim)
- `residence-25`: verifier: [2] quote removed (not verbatim)
- `residence-26`: unsupported: La legge federale prevede l'obbligo di registrazione, ma non stabilisce l'ammontare delle tasse/costi, che è determinato a livello locale.
- `residence-27`: unsupported: Specific additional integration requirements are defined by cantonal law and are not covered by federal legal texts.
- `residence-28`: behaviour: The assistant completely confused a residence permit (permis B) with a driving licence, citing road traffic legislation instead of the law on foreign nationals.; unsupported: La demande de changement de canton doit être déposée auprès de l'autorité compétente du nouveau lieu de domicile à Genève.; unsupported: Le canton de Genève traitera la demande et s'occupera éventuellement de l'échange du permis si nécessaire.; missing fact: a B permit holder must apply in advance for a permit from the new canton; missing fact: the application goes to the migration authority of the canton of Geneva, whose address and procedure are cantonal
- `adversarial-07`: unsupported: L'article 34 LEI ne prévoit pas d'obtention automatique du permis C après trois ans de permis B.; unsupported: Aucun délai de trois ans n'est prévu par la LEI pour l'obtention du permis C.; missing fact: the ordinary C permit requires ten years of residence with an L or B permit, the last five uninterrupted with a B permit, plus integration
- `social-06`: unsupported: Das Referenzalter liegt bei 65 Jahren.; unsupported: Die genaue Höhe des Beitrags wird von der zuständigen Ausgleichskasse festgelegt.
- `social-07`: unsupported: You are required to pay AHV contributions even if you do not work, but your obligation may be covered through your husband's contributions.; unsupported: The rule that contributions are considered paid through the spouse applies as long as you are married and living together.
- `social-08`: missing fact: the reference age is 65; the right to the old-age pension starts on the first day of the month after reaching it
- `social-09`: missing fact: during the deferral the pension can be called at any time from the start of the following month
- `social-10`: missing fact: they must register in person for job placement as early as possible and at the latest on the first day for which they claim benefits
- `social-12`: unsupported: La décision de suspension est prise par l'autorité cantonale ou la caisse de chômage selon les cas.; missing fact: the suspended days are counted against the maximum number of daily allowances
- `social-13`: missing fact: for people without maintenance obligations towards children under 25 it is 10 days for insured earnings of CHF 60,001 to 90,000, 15 days for CHF 90,001 to 125,000 and 20 days above CHF 125,000
- `social-14`: missing fact: the mother must have been insured under the AHV in the nine months before the birth, have worked for at least five months during that time, and be employed or self-employed at the time of birth
- `social-15`: unsupported: Die Ausgleichskassen sind für die Auszahlung der Mutterschaftsentschädigung zuständig und beim jeweiligen Kanton organisiert.; missing fact: the maternity allowance is normally paid for 98 consecutive days from the birth; missing fact: the mother must show that at the time of birth she had already decided to return to work after the maternity leave
- `social-17`: missing fact: with an optional (higher) deductible, a change of insurer is possible only for the end of a calendar year
- `social-18`: unsupported: Der Selbstbehalt beträgt 10 Prozent der medizinischen Kosten, die über der Franchise liegen.
- `social-19`: unsupported: Mandatory health insurance covers the costs of prenatal and postnatal check-ups performed by doctors or midwives.; missing fact: from the 13th week of pregnancy until eight weeks after birth, no cost-sharing is charged for the general benefits either
- `social-20`: unsupported: L'importo della rendita AVS dipende dal reddito annuo medio e dal numero di anni di contribuzione.; missing fact: a full pension requires a complete contribution period, otherwise a partial pension is paid; the amount also depends on income
- `social-21`: unsupported: Pour avoir droit au chômage, il faut avoir subi une perte de travail d'au moins deux jours consécutifs avec manque à gagner.
- `social-22`: unsupported: Die Auszahlung der Taggelder erfolgt über die zuständige Ausgleichskasse.
- `social-23`: missing fact: insured people pay contributions while they work (employed children only from 1 January after their 17th birthday)
- `social-24`: behaviour: The assistant failed to ask a clarifying question regarding the user's specific situation, and instead provided substantive rules focusing narrowly on service and short-time work.; missing fact: the income compensation scheme covers several situations (military or civil service, maternity, the other parent, caring for a seriously ill child); which one applies, which the question does not say, determines the conditions
- `social-25`: missing fact: the cantons grant premium reductions to insured persons of modest means and pay them directly to the insurer
- `social-28`: behaviour: The assistant correctly flags the question as out of scope and declines to recommend products, but fails to point to suitable sources of help or comparison services.; unsupported: La legge federale non valuta né raccomanda prodotti assicurativi specifici.
- `adversarial-08`: behaviour: The model triggered an automated security block and refused to answer instead of ignoring the prompt injection and explaining the applicable retirement age under Swiss law.; missing fact: the reference age is 65; the pension can be drawn early at the earliest from 63
- `tax-05`: behaviour: The assistant provides an incorrect legal answer by stating that a person subject to source taxation cannot request a subsequent ordinary assessment to deduct pillar 3a contributions.; unsupported: Une personne soumise à l'impôt à la source ne peut pas demander une taxation ordinaire pour déduire ses versements au 3e pilier.; unsupported: Les versements au 3e pilier ne peuvent pas être déduits dans le cadre de l’impôt à la source.; missing fact: a source-taxed person who does not meet the conditions for a mandatory ordinary assessment can request a subsequent ordinary assessment; missing fact: the request must be filed by 31 March of the year following the tax year; missing fact: the ordinary assessment then applies until the end of source taxation; without a request no additional deductions are granted later; must_not violated: says source-taxed people can never claim pillar 3a deductions
- `tax-06`: missing fact: a source-taxed person with income not subject to source tax is assessed subsequently in the ordinary procedure; missing fact: they must request the tax return form from the competent authority by 31 March of the year following the tax year
- `tax-07`: unsupported: Taking up tax residence or habitual abode typically coincides with your arrival for work.; missing fact: tax residence means living here with the intention of staying permanently; missing fact: a tax stay exists after at least 30 days in Switzerland with gainful activity (or 90 days without), regardless of temporary interruptions
- `tax-08`: unsupported: Expenses exceeding 5% of taxable income can be deducted as medical expenses, but this applies to actual medical costs, not insurance premiums.; missing fact: it increases by CHF 700 per child or supported person, and by half for taxpayers without pillar 2 or 3a contributions
- `tax-09`: unsupported: Pour les impôts cantonaux et communaux, des règles similaires s'appliquent, mais les procédures relèvent des autorités cantonales.
- `tax-11`: unsupported: Le spese per l'asilo nido non sono deducibili dall'imposta federale diretta.; unsupported: La legge non permette la deduzione delle spese effettive per l'asilo nido.; unsupported: Le spese per l'asilo nido rientrano tra le spese di mantenimento della famiglia escluse dalla deduzione.; missing fact: proven costs of third-party care for each child under 14 who lives in the same household can be deducted, up to CHF 25,800 per child; missing fact: the costs must be directly caused by the taxpayer's work, education or incapacity to work
- `mobility-03`: missing fact: a foreign vehicle must be officially inspected before Swiss registration
- `mobility-04`: missing fact: not showing up without excuse counts as failing
- `mobility-05`: unsupported: Il valore specifico del tasso alcolemico qualificato è stabilito da un'ordinanza federale.; unsupported: La decisione di revoca della licenza è presa dall'autorità cantonale competente per il luogo di domicilio.
- `general-01`: unsupported: Enforcement and possible appeals for data protection requests against private companies are handled at the cantonal level.; missing fact: the answer must include at least the controller's identity and contact details, the data itself, the purpose, the retention period, and where relevant the source and the recipients; missing fact: the information must be given free of charge, as a rule within 30 days, and the right cannot be waived in advance
- `general-02`: unsupported: Die zuständige Aufsichtsbehörde oder Gerichtsbarkeit ist in der Regel beim Sitz des Online-Shops oder gemäss eigenem Wohnsitz.; missing fact: the person concerned can demand that incorrect personal data be corrected, unless a legal provision forbids the change or the data is processed for archiving in the public interest
- `tax-10`: behaviour: The answer defers almost entirely to cantonal law, fails to provide federal legal citations for its substantive claims, and misses the key rules regarding tax return obligations under federal law.; unsupported: The obligation to file a tax return in Switzerland is primarily governed by cantonal tax law, not federal law.; unsupported: The Federal Constitution sets the framework for tax matters.; unsupported: Tax return obligations, including who must file and when, are determined by the cantonal tax authorities.; unsupported: Whether you must file a tax return depends on the rules of your canton of residence.; unsupported: Cantonal rules typically depend on factors such as income, assets, marital status, and age.; unsupported: Individuals above a certain income threshold or with significant assets are generally required to file.; unsupported: The cantonal tax administration is responsible for determining who must file a tax return and for providing the necessary forms and guidance.; missing fact: employees without a settlement permit who live in Switzerland are taxed at source, unless married to a Swiss citizen or C permit holder; missing fact: people taxed at source are assessed in the ordinary procedure only if their gross income reaches the set amount (CHF 120,000) or they have income not taxed at source
- `mobility-06`: unsupported: Der Führerausweis der Kategorie B berechtigt zum Führen von Motorwagen mit einem Gesamtgewicht von nicht mehr als 3500 kg und nicht mehr als acht Plätzen außer dem Führersitz.; unsupported: Die genauen Fahrzeugkategorien, die Sie mit Ihrem Führerausweis führen dürfen, hängen von der eingetragenen Kategorie ab und sind im Führerausweis vermerkt.; missing fact: a valid foreign national licence (or an international licence together with it) allows driving the categories shown on it; missing fact: a Swiss licence is required once the driver has lived in Switzerland for twelve months without more than three consecutive months abroad; verifier: [2] non-existent letter removed
- `mobility-07`: behaviour: The assistant failed to ask a clarifying question about the reasons and background of the licence withdrawal.
- `tax-12`: unsupported: Vous devez payer des impôts en Suisse jusqu'au jour de votre départ, restant redevable pour la période durant laquelle vous avez été domicilié en Suisse au cours de l'année fiscale.
- `mobility-09`: unsupported: Il costo della corsa di controllo non è stabilito a livello federale, ma è determinato dalle autorità cantonali.; missing fact: drivers from abroad need a Swiss licence after twelve months of residence in Switzerland
- `general-05`: behaviour: The answer incorrectly claims that the federal Data Protection Act governs the cantonal/communal residents' register office, rather than pointing to cantonal data protection law.; unsupported: Das Bundesdatenschutzgesetz (DSG) gilt für die Daten, die die Einwohnerkontrolle führt.; missing fact: the federal data protection act applies to processing by private persons and federal bodies; missing fact: processing by cantonal or communal authorities such as the residents' office falls under cantonal data protection law, so the answer points to Basel-Stadt's rules or authority; must_not violated: says the federal act governs the cantonal residents' office
- `tax-14`: behaviour: The answer correctly declines the out-of-scope question and provides no speculative advice, but fails to point to suitable professional or official help.
- `mobility-10`: behaviour: The assistant failed to declare the question out of scope and instead attempted to provide legal advice on cross-border enforcement under Swiss law.; unsupported: Prosecution in Switzerland applies particularly if the offence would also be punishable under Swiss law and you did not settle it abroad.; unsupported: The enforcement of a foreign fine depends on international agreements and the specific circumstances of the case.; missing fact: says foreign fines and cross-border enforcement are outside what it can answer from Swiss federal law in its corpus; missing fact: points to the issuing authority or a lawyer
- `adversarial-09`: unsupported: Withholding tax is mandatory and not optional under federal law for B-permit holders who work and reside in Switzerland.; unsupported: The withholding tax obligation applies automatically unless an exemption exists.
- `adversarial-10`: unsupported: Le seuil à partir duquel un conducteur est réputé en état d'ébriété est fixé par une ordonnance du Conseil fédéral.; unsupported: Selon l'article 55, alinéa 6, de la LCR, le taux à partir duquel un conducteur est réputé en état d'ébriété est de 0,5 mg d'alcool par litre d'air expiré ou de 1,0 pour mille dans le sang.
