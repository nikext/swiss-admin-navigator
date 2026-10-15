# Answer eval: baseline-golden

- dataset: `golden` (150 cases selected, 150 verified by claude-opus-5-5; sha 283079d403c1 over golden.jsonl)
- re-scored without model calls from `2026-10-15-7bd9768-baseline-drafts.json`, `2026-10-15-7bd9768-baseline-rerun.json`
- agent: `gemini-3.8-flash@eu`, prompt sha 766534f90f94, google-adk 2.12.0, structured output native schema + tools
- judge: `gemini-3.8-flash@global`, prompt sha d83d68626291
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-15T22:32:20+00:00 at 7bd9768; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **99.4%** (539/542; CI 98.2–100.0) |
| hallucinated citations | **0** of 542 |
| required-citation recall | **96.5** (93.3–99.2, n=125) |
| citation precision (expected only) | **54.1** (49.3–59.6, n=141) |
| citation precision (expected or judged relevant) | **99.8** (99.5–100.0, n=141) |
| groundedness (judge, claim level) | **78.6** (74.9–82.4, n=147) |
| key-fact coverage (judge) | **95.5** (92.9–97.7, n=150) |
| must_not violations (judge) | **0** |
| behaviour accuracy (rule + judge) | **98.0** (95.3–100.0, n=150) |
| behaviour (rule only) | **98.0** (95.3–100.0, n=150) |
| language match | **100.0** (100.0–100.0, n=150) |
| errors | 0 |

## Verifier

- first drafts: 552 citations, 552 quotes; problems {'paragraph': 9, 'quote': 9}; 6 cases sent back once
- final status: {'passed': 144, 'passed_after_retry': 5, 'degraded': 1}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0381 mean, 0.0843 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 5.713, judge CHF 0.967
- latency p50 41.2 s, p95 104.0 s; 7.2 model calls and 6.2 tool calls per answer; tokens per answer (mean): prompt 68,854, cached 38,758, output 1,150, thoughts 4,442

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: adversarial | 10 | 100 | 79 | 100 | 100 |
| category: answerable | 106 | 99 | 84 | 94 | 100 |
| category: cantonal_pointer | 15 | 100 | 75 | 97 | 100 |
| category: needs_clarification | 6 | 67 | 34 | 100 | 100 |
| category: out_of_scope | 13 | 100 | 53 | 100 | 100 |
| lang: de | 38 | 100 | 79 | 92 | 100 |
| lang: en | 38 | 100 | 75 | 96 | 100 |
| lang: fr | 37 | 92 | 79 | 95 | 100 |
| lang: it | 37 | 100 | 81 | 99 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| housing-01 | passed | 3 | 3/3 | 0 | 100 | 62 | 100 | ok | fr | 49 | 0.0291 |
| housing-02 | passed | 3 | 3/3 | 0 | 100 | 80 | 100 | ok | de | 24 | 0.0187 |
| housing-03 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 28 | 0.0175 |
| housing-04 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 35 | 0.0243 |
| housing-05 | passed | 3 | 3/3 | 0 | 100 | 58 | 100 | ok | de | 72 | 0.0399 |
| work-01 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 47 | 0.0345 |
| work-02 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 21 | 0.0150 |
| work-03 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 43 | 0.0358 |
| work-04 | passed | 2 | 2/2 | 0 | 100 | 60 | 100 | ok | en | 24 | 0.0213 |
| work-05 | passed | 4 | 4/4 | 0 | 100 | 90 | 100 | ok | de | 39 | 0.0337 |
| work-06 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | fr | 76 | 0.0491 |
| social-01 | passed | 6 | 6/6 | 0 | 100 | 86 | 100 | ok | de | 51 | 0.0394 |
| social-02 | passed | 7 | 7/7 | 0 | 100 | 93 | 100 | ok | it | 52 | 0.0425 |
| social-03 | passed | 5 | 5/5 | 0 | 100 | 78 | 100 | ok | en | 53 | 0.0400 |
| social-04 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 57 | 0.0463 |
| social-05 | passed | 7 | 7/7 | 0 | – | 78 | 100 | **no** | fr | 53 | 0.0408 |
| residence-01 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 15 | 0.0109 |
| residence-02 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 50 | 0.0457 |
| residence-03 | passed_after_retry | 0 | 0/0 | 0 | 0 | 0 | 0 | **no** | fr | 131 | 0.0988 |
| residence-04 | passed | 4 | 4/4 | 0 | 100 | 90 | 100 | ok | it | 34 | 0.0362 |
| residence-05 | passed | 6 | 6/6 | 0 | 100 | 79 | 100 | ok | en | 42 | 0.0349 |
| residence-06 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 56 | 0.0530 |
| residence-07 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | it | 16 | 0.0125 |
| tax-01 | passed | 6 | 6/6 | 0 | 100 | 64 | 100 | ok | en | 49 | 0.0452 |
| tax-02 | passed | 3 | 3/3 | 0 | 100 | 60 | 100 | ok | it | 25 | 0.0227 |
| tax-03 | passed | 1 | 1/1 | 0 | – | 50 | 100 | ok | fr | 18 | 0.0143 |
| mobility-01 | passed | 6 | 6/6 | 0 | 100 | 86 | 100 | ok | en | 67 | 0.0514 |
| mobility-02 | passed | 1 | 1/1 | 0 | – | 100 | 100 | ok | it | 26 | 0.0232 |
| adversarial-01 | passed | 2 | 2/2 | 0 | – | 75 | 100 | ok | de | 27 | 0.0232 |
| adversarial-02 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | en | 7 | 0.0045 |
| housing-06 | passed | 2 | 2/2 | 0 | 100 | 67 | 100 | ok | en | 24 | 0.0191 |
| housing-07 | passed | 3 | 3/3 | 0 | 100 | 67 | 100 | ok | de | 15 | 0.0130 |
| housing-08 | passed | 6 | 6/6 | 0 | 100 | 78 | 100 | ok | fr | 41 | 0.0285 |
| housing-09 | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | it | 39 | 0.0287 |
| housing-10 | passed | 3 | 3/3 | 0 | 100 | 86 | 100 | ok | en | 22 | 0.0170 |
| housing-11 | passed | 4 | 4/4 | 0 | 100 | 83 | 100 | ok | de | 44 | 0.0282 |
| housing-12 | passed | 4 | 4/4 | 0 | 100 | 78 | 100 | ok | fr | 26 | 0.0203 |
| housing-13 | passed | 3 | 3/3 | 0 | 100 | 67 | 100 | ok | it | 17 | 0.0133 |
| housing-14 | passed | 1 | 1/1 | 0 | 100 | 67 | 100 | ok | en | 16 | 0.0138 |
| housing-15 | passed | 4 | 4/4 | 0 | 100 | 89 | 100 | ok | de | 44 | 0.0355 |
| housing-16 | passed | 4 | 4/4 | 0 | 100 | 79 | 100 | ok | fr | 64 | 0.0465 |
| housing-17 | passed | 4 | 4/4 | 0 | 100 | 83 | 100 | ok | it | 48 | 0.0362 |
| housing-18 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 39 | 0.0325 |
| housing-19 | passed | 4 | 4/4 | 0 | 100 | 75 | 67 | ok | de | 30 | 0.0290 |
| housing-21 | passed | 3 | 3/3 | 0 | 100 | 92 | 100 | ok | it | 30 | 0.0261 |
| housing-22 | passed | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | de | 25 | 0.0191 |
| housing-20 | passed | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | en | 29 | 0.0268 |
| housing-23 | passed | 2 | 2/2 | 0 | 100 | 75 | 50 | ok | fr | 25 | 0.0233 |
| housing-24 | passed | 3 | 3/3 | 0 | 100 | 83 | 100 | ok | it | 25 | 0.0205 |
| housing-25 | passed | 2 | 2/2 | 0 | 100 | 75 | 100 | ok | de | 41 | 0.0292 |
| housing-26 | passed | 2 | 2/2 | 0 | – | 50 | 100 | ok | en | 56 | 0.0251 |
| housing-27 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | fr | 10 | 0.0064 |
| adversarial-03 | passed | 2 | 2/2 | 0 | – | 100 | 100 | ok | fr | 39 | 0.0206 |
| adversarial-04 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 25 | 0.0233 |
| work-07 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | en | 12 | 0.0097 |
| work-08 | passed | 3 | 3/3 | 0 | 100 | 57 | 67 | ok | de | 28 | 0.0214 |
| work-09 | passed | 2 | 2/2 | 0 | 100 | 75 | 100 | ok | fr | 18 | 0.0163 |
| work-10 | passed | 3 | 3/3 | 0 | 100 | 62 | 100 | ok | it | 17 | 0.0154 |
| work-11 | passed | 6 | 6/6 | 0 | 100 | 86 | 100 | ok | en | 81 | 0.0470 |
| work-12 | passed | 5 | 5/5 | 0 | 100 | 86 | 100 | ok | de | 49 | 0.0325 |
| work-13 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 39 | 0.0278 |
| work-14 | passed | 3 | 3/3 | 0 | 100 | 80 | 100 | ok | it | 35 | 0.0234 |
| work-15 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | en | 30 | 0.0174 |
| work-16 | passed | 6 | 6/6 | 0 | 67 | 100 | 75 | ok | de | 45 | 0.0349 |
| work-17 | passed | 2 | 2/2 | 0 | 100 | 75 | 100 | ok | fr | 48 | 0.0304 |
| work-18 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 37 | 0.0277 |
| work-19 | passed | 3 | 3/3 | 0 | 100 | 83 | 100 | ok | en | 39 | 0.0237 |
| work-20 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | de | 31 | 0.0255 |
| work-21 | passed | 5 | 5/5 | 0 | 100 | 92 | 67 | ok | fr | 30 | 0.0246 |
| work-24 | passed | 5 | 5/5 | 0 | 100 | 56 | 100 | ok | fr | 37 | 0.0333 |
| work-22 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 19 | 0.0163 |
| work-23 | passed | 3 | 3/3 | 0 | 100 | 80 | 100 | ok | de | 22 | 0.0182 |
| work-25 | passed | 2 | 2/2 | 0 | 100 | 67 | 100 | ok | fr | 22 | 0.0191 |
| work-26 | passed | 1 | 1/1 | 0 | – | 33 | 100 | ok | de | 33 | 0.0251 |
| work-27 | passed | 2 | 2/2 | 0 | – | 67 | 100 | ok | it | 22 | 0.0187 |
| work-28 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 13 | 0.0113 |
| adversarial-05 | passed | 1 | 1/1 | 0 | – | 33 | 100 | ok | it | 44 | 0.0342 |
| adversarial-06 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | en | 30 | 0.0243 |
| residence-08 | passed | 5 | 5/5 | 0 | 50 | 100 | 67 | ok | en | 62 | 0.0443 |
| residence-09 | passed | 4 | 4/4 | 0 | 100 | 75 | 100 | ok | fr | 85 | 0.0620 |
| residence-10 | passed_after_retry | 5 | 5/5 | 0 | 100 | 62 | 67 | ok | de | 178 | 0.1339 |
| residence-11 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 26 | 0.0234 |
| residence-12 | passed | 5 | 5/5 | 0 | 100 | 81 | 100 | ok | en | 76 | 0.0617 |
| residence-13 | passed | 4 | 4/4 | 0 | 100 | 67 | 100 | ok | de | 68 | 0.0625 |
| residence-14 | passed | 5 | 5/5 | 0 | 100 | 81 | 100 | ok | fr | 49 | 0.0343 |
| residence-15 | degraded | 4 | 1/4 | 0 | 0 | 33 | 100 | ok | it | 260 | 0.1769 |
| residence-16 | passed_after_retry | 1 | 1/1 | 0 | 100 | 67 | 100 | ok | de | 113 | 0.1040 |
| residence-17 | passed | 3 | 3/3 | 0 | 100 | 79 | 100 | ok | en | 51 | 0.0393 |
| residence-18 | passed_after_retry | 5 | 5/5 | 0 | 100 | 92 | 100 | ok | fr | 143 | 0.1660 |
| residence-19 | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | it | 50 | 0.0425 |
| residence-20 | passed | 4 | 4/4 | 0 | 100 | 70 | 100 | ok | fr | 40 | 0.0324 |
| residence-21 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 14 | 0.0114 |
| residence-22 | passed | 6 | 6/6 | 0 | 100 | 72 | 100 | ok | it | 41 | 0.0344 |
| residence-23 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 65 | 0.0527 |
| residence-24 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 68 | 0.0547 |
| residence-25 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | de | 97 | 0.0843 |
| residence-26 | passed | 3 | 3/3 | 0 | 100 | 75 | 100 | ok | it | 84 | 0.0680 |
| residence-27 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | en | 34 | 0.0257 |
| residence-28 | passed | 4 | 4/4 | 0 | 100 | 75 | 100 | ok | fr | 66 | 0.0518 |
| residence-29 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | de | 11 | 0.0105 |
| residence-30 | passed | 2 | 2/2 | 0 | – | 50 | 100 | ok | it | 24 | 0.0160 |
| adversarial-07 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | fr | 63 | 0.0396 |
| social-06 | passed | 3 | 3/3 | 0 | 100 | 80 | 100 | ok | de | 60 | 0.0436 |
| social-07 | passed | 3 | 3/3 | 0 | 100 | 62 | 100 | ok | en | 42 | 0.0306 |
| social-08 | passed | 7 | 7/7 | 0 | 100 | 93 | 100 | ok | fr | 70 | 0.0687 |
| social-09 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 42 | 0.0394 |
| social-10 | passed | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | en | 47 | 0.0406 |
| social-11 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 25 | 0.0251 |
| social-12 | passed | 3 | 3/3 | 0 | 100 | 70 | 100 | ok | fr | 52 | 0.0419 |
| social-13 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 40 | 0.0303 |
| social-14 | passed | 4 | 4/4 | 0 | 100 | 71 | 50 | ok | en | 62 | 0.0499 |
| social-15 | passed | 2 | 2/2 | 0 | 100 | 100 | 67 | ok | de | 22 | 0.0207 |
| social-16 | passed | 8 | 8/8 | 0 | 100 | 100 | 100 | ok | fr | 87 | 0.0475 |
| social-17 | passed | 6 | 6/6 | 0 | 100 | 92 | 67 | ok | it | 47 | 0.0497 |
| social-18 | passed | 5 | 5/5 | 0 | 100 | 79 | 100 | ok | de | 86 | 0.0822 |
| social-19 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | en | 36 | 0.0290 |
| social-20 | passed | 7 | 7/7 | 0 | 0 | 88 | 100 | ok | it | 59 | 0.0484 |
| social-21 | passed | 4 | 4/4 | 0 | 100 | 79 | 100 | ok | fr | 57 | 0.0478 |
| social-22 | passed | 9 | 9/9 | 0 | 50 | 77 | 50 | ok | de | 62 | 0.0557 |
| social-23 | passed | 7 | 7/7 | 0 | 100 | 83 | 100 | ok | en | 57 | 0.0498 |
| social-24 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | it | 26 | 0.0252 |
| social-25 | passed | 3 | 3/3 | 0 | 100 | 90 | 100 | ok | en | 41 | 0.0308 |
| social-26 | passed | 4 | 4/4 | 0 | 100 | 88 | 100 | ok | fr | 42 | 0.0352 |
| social-27 | passed | 4 | 4/4 | 0 | – | 80 | 100 | ok | de | 55 | 0.0439 |
| social-28 | passed | 1 | 1/1 | 0 | – | 50 | 100 | ok | it | 28 | 0.0196 |
| adversarial-08 | passed | 3 | 3/3 | 0 | 100 | 58 | 100 | ok | fr | 21 | 0.0190 |
| tax-04 | passed | 2 | 2/2 | 0 | 100 | 80 | 100 | ok | de | 22 | 0.0223 |
| tax-05 | passed | 9 | 9/9 | 0 | 100 | 77 | 100 | ok | fr | 79 | 0.0602 |
| tax-06 | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | it | 80 | 0.0585 |
| tax-07 | passed | 4 | 4/4 | 0 | 100 | 64 | 67 | ok | en | 62 | 0.0467 |
| tax-08 | passed | 2 | 2/2 | 0 | 100 | 83 | 100 | ok | en | 44 | 0.0300 |
| tax-09 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 65 | 0.0492 |
| tax-11 | passed | 1 | 1/1 | 0 | 100 | 100 | 100 | ok | it | 19 | 0.0185 |
| mobility-03 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 69 | 0.0441 |
| mobility-04 | passed | 4 | 4/4 | 0 | 100 | 88 | 100 | ok | fr | 30 | 0.0284 |
| mobility-05 | passed | 5 | 5/5 | 0 | 100 | 88 | 100 | ok | it | 55 | 0.0459 |
| general-01 | passed | 6 | 6/6 | 0 | 100 | 100 | 67 | ok | en | 56 | 0.0359 |
| general-02 | passed | 6 | 6/6 | 0 | 100 | 100 | 50 | ok | de | 137 | 0.1610 |
| tax-10 | passed | 6 | 6/6 | 0 | 100 | 75 | 100 | ok | en | 55 | 0.0420 |
| mobility-06 | passed | 4 | 4/4 | 0 | 100 | 88 | 50 | ok | de | 63 | 0.0507 |
| mobility-07 | passed | 6 | 6/6 | 0 | – | 93 | 100 | **no** | fr | 104 | 0.0902 |
| tax-12 | passed | 4 | 4/4 | 0 | 100 | 86 | 100 | ok | fr | 70 | 0.0661 |
| mobility-08 | passed | 5 | 5/5 | 0 | 100 | 83 | 100 | ok | it | 101 | 0.0724 |
| mobility-09 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 119 | 0.0823 |
| general-05 | passed | 2 | 2/2 | 0 | 100 | 50 | 100 | ok | de | 24 | 0.0204 |
| tax-14 | passed | 3 | 3/3 | 0 | – | 75 | 100 | ok | it | 41 | 0.0300 |
| mobility-10 | passed | 1 | 1/1 | 0 | – | 50 | 100 | ok | en | 31 | 0.0233 |
| general-06 | passed | 2 | 2/2 | 0 | – | 67 | 100 | ok | de | 24 | 0.0139 |
| adversarial-09 | passed | 4 | 4/4 | 0 | 100 | 67 | 100 | ok | en | 34 | 0.0252 |
| adversarial-10 | passed | 3 | 3/3 | 0 | – | 75 | 100 | ok | fr | 27 | 0.0253 |

## Findings per case

- `housing-01`: unsupported: À défaut de saisine de l'autorité de conciliation dans le délai de 30 jours, le congé est réputé accepté.
- `housing-02`: unsupported: Das Geld darf nicht auf das private Konto des Vermieters fliessen.
- `housing-05`: unsupported: Bei der 30-tägigen Frist handelt es sich um eine gesetzliche Verwirkungsfrist, bei der der Zeitpunkt massgebend ist, an dem das Kündigungsschreiben zugegangen ist.; unsupported: Die Organisation der Schlichtungsbehörden obliegt den Kantonen.
- `work-04`: unsupported: Because an employee is 24 years old, the general statutory minimum of 4 weeks applies.; unsupported: An individual employment contract, collective bargaining agreement (GAV/CCT), or company regulations may provide for more holiday, but cannot legally grant less than the 4-week statutory minimum.
- `social-01`: unsupported: Kantonale Regelungen, Gesamtarbeitsverträge oder der Arbeitgeber können weitergehende Leistungen vorsehen.
- `social-03`: unsupported: Cantons are responsible for supervising compliance with compulsory health insurance.; unsupported: The communal residents' registration office or cantonal health department will monitor coverage and assign you to an insurer if you fail to take out insurance yourself.
- `social-05`: behaviour: The assistant did not ask a clarifying question to determine the missing facts (contribution duration and age), but instead provided a breakdown of multiple scenarios.; unsupported: En huit mois de chômage complet, l'assuré perçoit environ 173 indemnités journalières.; unsupported: Le calcul s'applique en l'absence de suspension ou d'exercice d'une activité intermédiaire.
- `residence-01`: unsupported: Under Swiss immigration rules, permanent residence holders face no impact on their right to stay upon losing a job, while others have specific grace periods or potential revocation depending on EU/EFTA or third-country nationality.
- `residence-03`: behaviour: The assistant asked a clarifying question instead of answering directly with citations.; unsupported: Les règles de regroupement familial applicables aux ressortissants d'États tiers sous la LEI prévoient des délais stricts, en particulier pour un enfant de plus de 12 ans.; missing fact: the spouse and unmarried children under 18 of a C permit holder are entitled to a residence permit if conditions are met (living together, suitable housing, no social assistance); missing fact: family reunification must be requested within five years; missing fact: children over 12 must be brought within twelve months
- `residence-05`: unsupported: Each canton and municipality sets its own minimum residence periods (between 2 and 5 years), integration tests, language levels, and procedural fees in addition to federal requirements.
- `tax-01`: unsupported: For married couples living together, mandatory assessment is triggered if either spouse earns at least CHF 120,000.; unsupported: Once subject to ordinary assessment, it remains mandatory for subsequent years until withholding tax liability ends.
- `tax-02`: unsupported: In Canton Ticino l'aliquota comunale è denominata moltiplicatore d'imposta comunale ed è stabilita dal Comune di Lugano secondo le disposizioni della legislazione ticinese.; unsupported: Il moltiplicatore d'imposta di Lugano è stabilito dal Consiglio comunale e approvato conformemente alla legge cantonale ticinese.
- `tax-03`: unsupported: La charge fiscale effective varie selon la situation personnelle (état civil, enfants à charge, fortune), les déductions admissibles (frais professionnels, cotisations de prévoyance, assurances), ainsi que les barèmes et coefficients fiscaux cantonaux et communaux.
- `mobility-01`: unsupported: Driving licence exchanges are handled by the canton of residence through its road traffic office, which determines procedure, fees, eye test requirements, and state-specific practical test exemptions.
- `adversarial-01`: unsupported: Die Miete darf nicht einfach eigenmächtig gekürzt werden.
- `housing-06`: unsupported: Practice and court rulings may apply standard notice periods such as 24 to 48 hours in advance.
- `housing-07`: unsupported: Eine gewöhnliche E-Mail erfüllt die gesetzliche Schriftform nicht.; unsupported: Das vorgeschriebene Kündigungsformular wird vom jeweiligen Kanton festgelegt und genehmigt.
- `housing-08`: unsupported: Un délai de congé plus court convenu par contrat n'est pas opposable au locataire.; unsupported: Les termes de congé fixés par l'usage local varient d'un canton à l'autre.
- `housing-10`: unsupported: If none of the statutory grounds apply, the landlord is legally required to give consent.
- `housing-11`: unsupported: Der Vermieter darf bei einem Zahlungsrückstand nicht sofort kündigen.
- `housing-12`: unsupported: Le locataire ne doit en aucun cas retenir l'argent sur son propre compte bancaire.; unsupported: L'office auprès duquel le loyer doit être déposé ainsi que l'autorité de conciliation compétente sont fixés par chaque canton.
- `housing-13`: unsupported: Il locatore non può attendere mesi per contestare danni che potevano essere rilevati subito.; unsupported: In caso di difetti occulti, una segnalazione tardiva dopo la scoperta fa decadere la responsabilità dell'inquilino.
- `housing-14`: unsupported: Cantons have the authority to enact supplementary provisions regarding rental deposits.
- `housing-15`: unsupported: Das mietrechtliche Schlichtungsverfahren ist in der Regel kostenlos.
- `housing-16`: unsupported: L'obligation d'utiliser la formule officielle lors de la conclusion d'un nouveau bail dépend des règles fixées par chaque canton en cas de pénurie de logements.
- `housing-17`: unsupported: L'organizzazione e la sede dell'autorità di conciliazione competente in materia di locazione sono definite dal diritto cantonale.
- `housing-19`: unsupported: Sie können den Mietvertrag für Ihre Familienwohnung grundsätzlich nicht alleine kündigen.; missing fact: the same applies to registered partnerships
- `housing-22`: unsupported: Normale Abnützung ist mit dem Mietzins bezahlt und berechtigt den Vermieter nicht zu Renovationsforderungen.
- `housing-20`: unsupported: Local customary moving dates vary across cantons and districts.
- `housing-23`: unsupported: La requête de conciliation doit être adressée par écrit à l'autorité compétente.; missing fact: the competent conciliation authority is a cantonal authority; the official rent increase form must list the conciliation authorities and their local competence
- `housing-24`: unsupported: La designazione dell'organo di deposito è di competenza cantonale.
- `housing-25`: unsupported: Ob im Kanton Zürich für die jeweilige Gemeinde oder den Bezirk derzeit eine solche Formularpflicht gilt, richtet sich nach kantonalem Recht.
- `housing-26`: unsupported: To recover compensation, the tenant must prove that the defect caused the damage and demonstrate the actual monetary value of the loss (ordinarily considering depreciated current value rather than original purchase price).; unsupported: Tenancy claims in the Canton of Basel-Stadt must first be submitted to the local conciliation authority (Staatliche Schlichtungsstelle für Mietstreitigkeiten).; unsupported: In Basel-Landschaft, tenancy claims go to the competent regional Schlichtungsbehörde.
- `work-08`: unsupported: Ein Konkurrenzverbot von fünf Jahren für die gesamte Schweiz ist in dieser Form in aller Regel übermässig und rechtlich so nicht durchsetzbar.; unsupported: Das gesamte Schweizer Staatsgebiet kommt als örtlicher Geltungsbereich nur in Betracht, wenn sich der tatsächliche Kunden- und Geschäftskreis des Arbeitgebers darauf erstreckt.; unsupported: Eine übermässige Vereinbarung ist nicht zwingend von Beginn an völlig nichtig.; missing fact: a non-compete clause must be agreed in writing and is binding only if the job gave insight into the customer base or trade or business secrets whose use could cause the employer significant harm
- `work-09`: unsupported: Si l'employeur est en mesure d'établir que le congé est justifié par un motif imputable au travailleur, la clause continue de s'appliquer.
- `work-10`: unsupported: Un'assenza per malattia di due settimane rientra nel termine minimo legale di tre settimane.
- `work-11`: unsupported: An abusive dismissal remains legally effective in ending the employment.
- `work-12`: unsupported: Ob ein zweimaliges Zuspätkommen die Schwelle für eine fristlose Kündigung erreicht oder ob zuvor eine Verwarnung nötig gewesen wäre, beurteilt die Rechtsprechung im Einzelfall; das Gesetz selbst regelt solche Einzelfallkriterien nicht ausdrücklich.
- `work-16`: missing fact: hours beyond that maximum are limited to two hours a day and 170 hours per calendar year for this group
- `work-19`: unsupported: Your employment ends on 31 August.
- `work-21`: missing fact: the former employer and the buyer are jointly liable for the employee's claims that fell due before the transfer and until the employment could normally have ended
- `work-24`: unsupported: Le consentement du travailleur peut avoir été donné dans le contrat de travail ou ultérieurement.; unsupported: En cas de travail dominical temporaire, l'employeur doit accorder un temps de repos compensatoire.; unsupported: L'inspection cantonale du travail est l'autorité compétente pour délivrer les autorisations de travail dominical temporaire et surveiller le respect de la loi.; unsupported: Les cantons peuvent fixer jusqu'à quatre dimanches ouvrés par an pour les magasins.
- `work-23`: unsupported: In der gerichtlichen Praxis wird die Dauer der Lohnfortzahlung nach dem ersten Dienstjahr oft nach kantonalen Skalen berechnet, die im Gesetz selbst nicht geregelt sind.
- `work-25`: unsupported: La désignation des jours fériés applicables dans le canton de Vaud (notamment si le lundi de Pâques en fait partie) relève du droit cantonal vaudois.
- `work-26`: unsupported: Auf Bundesebene gibt es in der Schweiz keinen allgemeinen gesetzlichen Mindestlohn.; unsupported: Ein flächendeckender, gesetzlicher kantonaler Mindestlohn wie im Kanton Genf beruht ausschliesslich auf kantonalem Recht und wird nicht durch das Bundesrecht geregelt.
- `work-27`: unsupported: L'azione penale e l'esame delle richieste di patrocinio gratuito o difesa d'ufficio sono di competenza dell'autorità di perseguimento penale o giudiziaria cantonale.
- `work-28`: unsupported: A party who lacks sufficient financial means and whose case does not appear devoid of any chance of success can apply to the court for legal aid (unentgeltliche Rechtspflege) to obtain a court-appointed attorney.
- `adversarial-05`: unsupported: Non sussiste alcun divieto assoluto di licenziare dipendenti che abbiano superato i 50 anni di età e nessuna disposizione federale vieta di per sé il licenziamento in base all'età.; unsupported: La legge prevede specifiche protezioni contro le disdette abusive (art. 336 CO) o date in tempo inopportuno (art. 336c CO, ad esempio in caso di malattia o infortunio).
- `residence-08`: missing fact: for the early C permit the required level is at least B1 oral and A1 written
- `residence-10`: unsupported: Nach Prüfung und Bewilligung stellt der Kanton Bern einen neuen kantonalen Ausländerausweis aus.; unsupported: EU- oder EFTA-Angehörige benötigen keine vorgängige Bewilligung für den Kantonswechsel.; unsupported: Das Aufenthaltsrecht von EU/EFTA-Bürgern bleibt bestehen und bei der Anmeldung im neuen Kanton wird lediglich der Ausländerausweis auf den neuen Kanton ausgestellt.; missing fact: temporary stays in another canton do not need a permit
- `residence-12`: unsupported: Local or cantonal authorities usually handle application intake, background checks, or personal interviews for simplified naturalisation.
- `residence-13`: unsupported: Die Kantone und Gemeinden sind für das Verfahren der ordentlichen Einbürgerung zuständig.; unsupported: Kantone und Gemeinden können über das Bundesrecht hinausgehen und höhere Sprachniveaus sowie bestimmte kantonale Sprachtests oder Zertifikate vorschreiben.
- `residence-14`: unsupported: Les cantons et les communes fixent des durées de séjour locales obligatoires (entre 2 et 5 ans) ainsi que des critères d'émoluments et de procédure spécifiques.
- `residence-15`: unsupported: Poiché il contratto di lavoro è a tempo indeterminato (durata uguale o superiore a un anno), il permesso ha una validità di 5 anni ed è automaticamente rinnovabile per periodi di almeno 5 anni.; unsupported: Il lavoratore frontaliero è chi risiede in Italia e rientra regolarmente al proprio domicilio di norma ogni giorno o almeno una volta alla settimana.; unsupported: Per un impiego di durata pari o superiore a un anno, il permesso per frontalieri viene rilasciato per una durata di 5 anni ed è rinnovabile per periodi di almeno 5 anni purché continui a esercitare un'attività economica.; unsupported: Chi si trasferisce in Svizzera deve registrarsi presso l'ufficio controllo abitanti del proprio Comune di residenza entro 14 giorni dall'arrivo.; verifier: [2] non-existent paragraph removed; verifier: [3] non-existent paragraph removed; verifier: [4] non-existent paragraph removed
- `residence-16`: unsupported: Die unfreiwillige Beendigung des Arbeitsverhältnisses führt nicht zum sofortigen Erlöschen des Aufenthaltsrechts.
- `residence-17`: unsupported: Administrative and judicial practice generally requires marital cohabitation to have taken place in Switzerland, which the statutory text does not explicitly state.
- `residence-20`: unsupported: Des accords d'établissement bilatéraux prévoient l'octroi du permis C après 5 ans de séjour pour la plupart des ressortissants de l'UE/AELE.
- `residence-21`: unsupported: Swiss and EU/EFTA nationals have broad access to the Swiss labour market under freedom of movement rules.; unsupported: Third-country nationals must fulfill strict statutory requirements to work in Switzerland, including employer sponsorship, qualifications, and quota availability.
- `residence-22`: unsupported: È possibile ottenere la cittadinanza svizzera soddisfacendo i requisiti legali, principalmente tramite la naturalizzazione ordinaria o quella agevolata.; unsupported: I Cantoni e i Comuni stabiliscono requisiti di soggiorno specifici (tra 2 e 5 anni a livello cantonale), nonché ulteriori criteri d'integrazione, tasse amministrative e la procedura formale.
- `residence-26`: unsupported: Il diritto federale non stabilisce tariffe o emolumenti per la notifica del trasloco, e i costi dipendono dalle norme cantonali e comunali.
- `residence-28`: unsupported: Pour les ressortissants d'un pays membre de l'UE/AELE, la mobilité géographique est garantie par l'accord sur la libre circulation des personnes.
- `residence-29`: unsupported: Im Asylverfahren gelten sehr kurze Beschwerdefristen.; unsupported: Personen, die sich in einem Bundesasylzentrum befanden oder deren Verfahren dort lief, wurde eine kostenlose Rechtsvertretung zugewiesen.
- `residence-30`: unsupported: La decisione e la valutazione dei criteri di idoneità comunali e cantonali spettano esclusivamente alle autorità locali previste dal diritto del Cantone.; unsupported: I requisiti di soggiorno comunale, le condizioni procedurali, i costi e l'organo decisionale dipendono interamente dalla legislazione del Cantone e dai regolamenti del Comune di residenza.
- `social-06`: unsupported: Nichterwerbstätige müssen sich in der Regel selbstständig bei der Ausgleichskasse anmelden, um Beitragslücken und Rentenkürzungen zu vermeiden.
- `social-07`: unsupported: AHV contribution accounts and individual assessments for non-employed persons are administered by the compensation fund (Ausgleichskasse) of your canton of residence.
- `social-10`: unsupported: An insured person cannot receive benefits for any days prior to the date they registered.
- `social-12`: unsupported: En présence d'un juste motif pour démissionner (par exemple conditions intolérables ou atteinte à la santé), la caisse peut renoncer à prononcer une suspension ou en réduire la durée.
- `social-14`: unsupported: Insurance or work periods in an EU or EFTA country immediately before moving to Switzerland may be aggregated under international social security coordination agreements.; unsupported: Some cantons (such as Geneva) have their own supplementary maternity benefits with different eligibility conditions.; missing fact: four months of work does not meet the five-month condition; the Federal Council regulates exceptions for women who could not work because of incapacity or unemployment
- `social-15`: missing fact: the maternity allowance is normally paid for 98 consecutive days from the birth
- `social-17`: missing fact: when a new premium is announced, the insured person can change with one month's notice for the end of the month before the new premium applies
- `social-18`: unsupported: In der obligatorischen Krankenpflegeversicherung setzt sich die Kostenbeteiligung aus der Franchise und dem Selbstbehalt zusammen.
- `social-20`: unsupported: La rendita effettiva si colloca tra l'importo minimo e massimo a seconda del reddito medio conseguito.
- `social-21`: unsupported: Les personnes indépendantes n'étant pas assujetties à l'assurance-chômage, elles n'y ont en principe pas droit sauf si elles justifient de 12 mois de salariat antérieur.
- `social-22`: unsupported: Die Auszahlung der Entschädigung erfolgt über die zuständige Ausgleichskasse (in der Regel über die Ausgleichskasse des Arbeitgebers).; unsupported: Einzelne Kantone oder Gesamtarbeitsverträge können über das Bundesrecht hinausgehende Regelungen vorsehen.; missing fact: the other parent is entitled to two weeks of leave, at most 14 daily allowances
- `social-23`: unsupported: AHV contributions are assessed and collected by cantonal or industry-specific compensation funds, and non-employed residents and self-employed individuals must register with their cantonal compensation fund.
- `social-24`: unsupported: L'ordinamento svizzero delle indennità di perdita di guadagno non copre qualsiasi calo di reddito, ma si applica a eventi specifici quali il servizio militare o civile, la maternità, il congedo per l'altro genitore, l'adozione o l'assistenza a un figlio gravemente malato.
- `social-27`: unsupported: Bei verheirateten oder geschiedenen Personen werden die Einkommen während der Ehejahre aufgeteilt (Splitting).
- `social-28`: unsupported: Le assicurazioni complementari private sono polizze di diritto privato regolate dalla Legge federale sul contratto d'assicurazione (LCA), ambito in cui vige la libertà contrattuale e ogni compagnia stabilisce liberamente premi, prestazioni coperte, limiti d'età e riserve d'entrata.
- `adversarial-08`: unsupported: Selon le droit fédéral, il n'est pas possible de percevoir une rente AVS complète dès l'âge de 60 ans.; unsupported: Il n'existe aucune base légale permettant de toucher une rente AVS complète à l'âge de 60 ans.
- `tax-04`: unsupported: Sie und Ihre Ehefrau werden gemeinsam im ordentlichen Steuerverfahren veranlagt und füllen jährlich eine reguläre Steuererklärung aus.
- `tax-05`: unsupported: Le barème de l'impôt à la source inclut des déductions forfaitaires moyennes.; unsupported: Lors d'une taxation ordinaire, le barème communal et cantonal effectif du lieu de domicile s'applique, ce qui peut aboutir à un impôt final supérieur.
- `tax-07`: unsupported: Direct income taxes in Switzerland are levied at the federal, cantonal, and municipal levels.; unsupported: Specific withholding tax rates, registration forms, and collection procedures are administered by the tax administration of the canton of residence.; missing fact: a tax stay exists after at least 30 days in Switzerland with gainful activity (or 90 days without), regardless of temporary interruptions
- `tax-08`: unsupported: Cantons set their own deduction rules and limits for cantonal and communal income taxes.
- `mobility-05`: unsupported: La procedura di revoca della licenza è gestita dall'autorità cantonale competente per la circolazione stradale del Cantone di domicilio, la quale decide la durata esatta del provvedimento.
- `general-01`: missing fact: the information must be given free of charge, as a rule within 30 days, and the right cannot be waived in advance
- `general-02`: missing fact: the person concerned can demand that incorrect personal data be corrected, unless a legal provision forbids the change or the data is processed for archiving in the public interest
- `tax-10`: unsupported: Direct taxes in Switzerland are assessed and collected by cantonal and communal tax administrations.
- `mobility-06`: missing fact: a Swiss licence is required once the driver has lived in Switzerland for twelve months without more than three consecutive months abroad
- `mobility-07`: behaviour: The question required clarification regarding the circumstances and infractions, but the assistant provided an overview of durations without asking a clarifying question.
- `tax-12`: unsupported: Il faut déposer une déclaration fiscale de départ avant de quitter la Suisse et régler le décompte d'impôt correspondant, ou l'impôt est prélevé à la source sur le salaire jusqu'au départ.
- `mobility-08`: unsupported: Accordi internazionali o direttive specifiche possono prevedere l'esenzione dalla corsa di controllo e la conversione diretta su base documentale.
- `general-05`: unsupported: Die Bearbeitung von Meldedaten durch die Einwohnerkontrolle und der Auskunftsanspruch gegenüber dieser Stelle richten sich nach kantonalem Datenschutzrecht und nicht nach dem Bundesdatenschutzgesetz.; unsupported: Für das Auskunftsbegehren gegenüber der Einwohnerkontrolle in Basel ist das Gesetz über die Information und den Datenschutz (IDG) des Kantons Basel-Stadt massgebend.
- `tax-14`: unsupported: La gestione della dichiarazione d'imposta, la tassazione e l'elaborazione dell'autodenuncia esente da pena sono di competenza dell'amministrazione fiscale del Cantone di domicilio.
- `mobility-10`: unsupported: Ignoring a French fine often leads to increased penalties, collection proceedings, or problems when traveling to France in the future.
- `general-06`: unsupported: Die Zuständigkeit und Organisation des Notariats ist kantonal geregelt.
- `adversarial-09`: unsupported: An employer is obligated by law to withhold this tax from the employee's salary.; unsupported: If annual gross income reaches or exceeds CHF 120,000, or the person has non-withholding income, an ordinary assessment is mandatory.
- `adversarial-10`: unsupported: Il est formellement interdit de conduire un véhicule automobile avec un taux d'alcool de 1,5 pour mille, même si l'on paraît sobre.
