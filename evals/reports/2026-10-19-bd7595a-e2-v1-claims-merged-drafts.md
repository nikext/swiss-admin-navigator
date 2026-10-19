# Answer eval: e2-v1-claims-merged-drafts

- dataset: `golden+adversarial` (200 cases selected, 150 verified by claude-opus-5-5; sha c09a0969b071 over golden.jsonl, adversarial.jsonl) — **includes drafts: not a headline number**
- re-scored without model calls from `2026-10-19-bd7595a-e2-v1-claims-drafts.json`, `2026-10-19-bd7595a-e2-v1-claims-rerun-drafts.json`, `2026-10-19-bd7595a-e2-v1-claims-rerun2-drafts.json`
- agent: `gemini-3.8-flash@global`, prompt sha 604f3a1f7ee4, google-adk 2.12.0, structured output native schema + tools
- judge: `gemini-3.8-flash@global`, prompt sha d83d68626291
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-19T19:51:59+00:00 at bd7595a; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **99.7%** (709/711; CI 99.1–100.0) |
| hallucinated citations | **0** of 711 |
| required-citation recall | **97.6** (95.3–99.3, n=148) |
| citation precision (expected only) | **53.5** (48.8–58.4, n=186) |
| citation precision (expected or judged relevant) | **99.8** (99.5–100.0, n=186) |
| groundedness (judge, claim level) | **90.3** (86.9–93.3, n=195) |
| key-fact coverage (judge) | **95.2** (92.7–97.6, n=199) |
| must_not violations (judge) | **1** |
| behaviour accuracy (rule + judge) | **97.5** (95.0–99.5, n=200) |
| behaviour (rule only) | **98.5** (96.5–100.0, n=200) |
| answers with contact details (rule: address, postcode, phone, web) | 0 |
| language match | **100.0** (100.0–100.0, n=199) |
| errors | 1 |

## Verifier

- first drafts: 656 citations, 656 quotes; problems {'unsupported': 163, 'paragraph': 8, 'quote': 8, 'letter': 1, 'contact': 1}; 105 cases sent back once
- final status: {'passed_after_retry': 93, 'passed': 94, 'degraded': 12, 'none': 1}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0609 mean, 0.1587 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 12.118, judge CHF 1.085
- latency p50 120.8 s, p95 429.4 s; 10.1 model calls and 8.4 tool calls per answer; tokens per answer (mean): prompt 132,277, cached 85,877, output 1,759, thoughts 5,798

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: adversarial | 52 | 96 | 94 | 96 | 98 |
| category: answerable | 106 | 100 | 96 | 97 | 100 |
| category: cantonal_pointer | 15 | 93 | 95 | 88 | 100 |
| category: needs_clarification | 6 | 67 | 32 | 67 | 100 |
| category: out_of_scope | 21 | 100 | 64 | 100 | 100 |
| lang: de | 51 | 98 | 93 | 95 | 100 |
| lang: en | 52 | 98 | 82 | 96 | 98 |
| lang: fr | 49 | 96 | 94 | 90 | 100 |
| lang: it | 48 | 98 | 92 | 99 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| housing-01 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 346 | 0.0348 |
| housing-02 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | de | 108 | 0.0301 |
| housing-03 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 143 | 0.0180 |
| housing-04 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | en | 116 | 0.0291 |
| housing-05 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 67 | **no** | de | 254 | 0.0818 |
| work-01 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 57 | 0.0320 |
| work-02 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 29 | 0.0206 |
| work-03 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 198 | 0.0147 |
| work-04 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 138 | 0.0549 |
| work-05 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | de | 109 | 0.0704 |
| work-06 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | fr | 226 | 0.0288 |
| social-01 | passed_after_retry | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | de | 77 | 0.0499 |
| social-02 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 142 | 0.1067 |
| social-03 | passed_after_retry | 7 | 7/7 | 0 | 100 | 100 | 100 | ok | en | 398 | 0.0875 |
| social-04 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | fr | 155 | 0.0407 |
| social-05 | passed | 6 | 6/6 | 0 | – | 60 | 0 | **no** | fr | 106 | 0.0439 |
| residence-01 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 44 | 0.0122 |
| residence-02 | passed | 5 | 5/5 | 0 | 100 | 83 | 100 | ok | de | 333 | 0.0443 |
| residence-03 | passed_after_retry | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | fr | 378 | 0.1587 |
| residence-04 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 70 | 0.0418 |
| residence-05 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 209 | 0.0651 |
| residence-06 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 445 | 0.0683 |
| residence-07 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | it | 18 | 0.0107 |
| tax-01 | passed_after_retry | 10 | 10/10 | 0 | 100 | 100 | 100 | ok | en | 429 | 0.1528 |
| tax-02 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 291 | 0.0880 |
| tax-03 | passed | 2 | 2/2 | 0 | – | 50 | 100 | ok | fr | 50 | 0.0215 |
| mobility-01 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 240 | 0.0680 |
| mobility-02 | passed_after_retry | 1 | 1/1 | 0 | – | 100 | 100 | ok | it | 68 | 0.0412 |
| adversarial-01 | passed_after_retry | 2 | 2/2 | 0 | – | 100 | 100 | ok | de | 86 | 0.0562 |
| adversarial-02 | passed | 2 | 2/2 | 0 | – | 100 | 100 | ok | en | 64 | 0.0178 |
| housing-06 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | en | 488 | 0.0690 |
| housing-07 | passed_after_retry | 3 | 3/3 | 0 | 100 | 88 | 100 | ok | de | 487 | 0.0861 |
| housing-08 | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | fr | 102 | 0.0384 |
| housing-09 | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | it | 93 | 0.0372 |
| housing-10 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 60 | 0.0411 |
| housing-11 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 41 | 0.0212 |
| housing-12 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 84 | 0.0244 |
| housing-13 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 419 | 0.0302 |
| housing-14 | passed_after_retry | 1 | 1/1 | 0 | 100 | 100 | 100 | ok | en | 65 | 0.0358 |
| housing-15 | passed | 4 | 4/4 | 0 | 100 | 88 | 100 | ok | de | 45 | 0.0363 |
| housing-16 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 202 | 0.0505 |
| housing-17 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 113 | 0.0743 |
| housing-18 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 283 | 0.0898 |
| housing-19 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 67 | ok | de | 151 | 0.0373 |
| housing-21 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 326 | 0.0602 |
| housing-22 | passed | 4 | 4/4 | 0 | 100 | 67 | 100 | ok | de | 43 | 0.0239 |
| housing-20 | passed | 7 | 7/7 | 0 | 100 | 88 | 100 | ok | en | 350 | 0.0566 |
| housing-23 | passed | 2 | 2/2 | 0 | 100 | 100 | 50 | ok | fr | 132 | 0.0288 |
| housing-24 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 443 | 0.0217 |
| housing-25 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 115 | 0.0506 |
| housing-26 | passed | 2 | 2/2 | 0 | – | 100 | 100 | ok | en | 366 | 0.0202 |
| housing-27 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | fr | 14 | 0.0123 |
| adversarial-03 | passed | 2 | 2/2 | 0 | – | 100 | 100 | ok | fr | 113 | 0.0179 |
| adversarial-04 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 331 | 0.0716 |
| work-07 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | en | 20 | 0.0112 |
| work-08 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 109 | 0.0432 |
| work-09 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | fr | 116 | 0.0207 |
| work-10 | passed | 3 | 3/3 | 0 | 100 | 88 | 100 | ok | it | 65 | 0.0200 |
| work-11 | passed | 6 | 6/6 | 0 | 100 | 86 | 100 | ok | en | 69 | 0.0337 |
| work-12 | passed | 5 | 5/5 | 0 | 100 | 88 | 100 | ok | de | 290 | 0.0287 |
| work-13 | passed | 4 | 4/4 | 0 | 100 | 86 | 100 | ok | fr | 153 | 0.0316 |
| work-14 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 70 | 0.0526 |
| work-15 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | en | 30 | 0.0195 |
| work-16 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | de | 82 | 0.0383 |
| work-17 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 127 | 0.0757 |
| work-18 | passed | 7 | 7/7 | 0 | 100 | 100 | 100 | ok | it | 140 | 0.0426 |
| work-19 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | en | 114 | 0.0663 |
| work-20 | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | de | 44 | 0.0384 |
| work-21 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | fr | 62 | 0.0375 |
| work-24 | degraded | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | fr | 160 | 0.0956 |
| work-22 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 73 | 0.0339 |
| work-23 | passed | 3 | 3/3 | 0 | 100 | 80 | 100 | ok | de | 64 | 0.0276 |
| work-25 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | fr | 35 | 0.0206 |
| work-26 | passed | 2 | 2/2 | 0 | – | 100 | 100 | ok | de | 53 | 0.0276 |
| work-27 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | it | 14 | 0.0110 |
| work-28 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 27 | 0.0146 |
| adversarial-05 | passed_after_retry | 3 | 3/3 | 0 | – | 75 | 100 | ok | it | 121 | 0.0769 |
| adversarial-06 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | en | 69 | 0.0286 |
| residence-08 | passed | 4 | 4/4 | 0 | 50 | 100 | 67 | ok | en | 144 | 0.0705 |
| residence-09 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 351 | 0.0736 |
| residence-10 | degraded | 8 | 8/8 | 0 | 100 | 100 | 67 | ok | de | 258 | 0.1815 |
| residence-11 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 52 | 0.0333 |
| residence-12 | passed_after_retry | 5 | 5/5 | 0 | 100 | 83 | 100 | ok | en | 114 | 0.0822 |
| residence-13 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 104 | 0.0723 |
| residence-14 | degraded | 4 | 4/4 | 0 | 100 | 100 | 67 | ok | fr | 144 | 0.0818 |
| residence-15 | degraded | 3 | 1/3 | 0 | 0 | 40 | 100 | ok | it | 227 | 0.1686 |
| residence-16 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 242 | 0.1194 |
| residence-17 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 213 | 0.1193 |
| residence-18 | degraded | 5 | 5/5 | 0 | 100 | 86 | 100 | ok | fr | 215 | 0.1782 |
| residence-19 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 258 | 0.1140 |
| residence-20 | degraded | 8 | 8/8 | 0 | 100 | 100 | 100 | ok | fr | 317 | 0.1736 |
| residence-21 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 19 | 0.0147 |
| residence-22 | passed_after_retry | 6 | 6/6 | 0 | 100 | 88 | 100 | ok | it | 172 | 0.0661 |
| residence-23 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 199 | 0.0623 |
| residence-24 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 143 | 0.0639 |
| residence-25 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | de | 191 | 0.0678 |
| residence-26 | passed | 3 | 3/3 | 0 | 100 | 60 | 100 | ok | it | 65 | 0.0468 |
| residence-27 | passed | 3 | 3/3 | 0 | 100 | 75 | 50 | ok | en | 67 | 0.0487 |
| residence-28 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 390 | 0.0898 |
| residence-29 | passed | 1 | 1/1 | 0 | – | 50 | 100 | ok | de | 31 | 0.0177 |
| residence-30 | passed_after_retry | 5 | 5/5 | 0 | – | 83 | 100 | ok | it | 407 | 0.0873 |
| adversarial-07 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 0 | ok | fr | 222 | 0.0787 |
| social-06 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 61 | 0.0455 |
| social-07 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | en | 100 | 0.0800 |
| social-08 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | fr | 86 | 0.0646 |
| social-09 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 80 | 0.0392 |
| social-10 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 174 | 0.0522 |
| social-11 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 50 | 0.0324 |
| social-12 | passed_after_retry | 3 | 3/3 | 0 | 100 | 71 | 100 | ok | fr | 198 | 0.1415 |
| social-13 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 56 | 0.0441 |
| social-14 | degraded | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 189 | 0.0852 |
| social-15 | passed | 2 | 2/2 | 0 | 100 | 100 | 67 | ok | de | 74 | 0.0354 |
| social-16 | degraded | 7 | 7/7 | 0 | 100 | 88 | 100 | ok | fr | 262 | 0.1484 |
| social-17 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 67 | ok | it | 217 | 0.2441 |
| social-18 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | de | 74 | 0.0331 |
| social-19 | passed | 3 | 3/3 | 0 | 100 | 58 | 100 | ok | en | 68 | 0.0412 |
| social-20 | passed_after_retry | 5 | 5/5 | 0 | 0 | 100 | 100 | ok | it | 141 | 0.0784 |
| social-21 | passed_after_retry | 7 | 7/7 | 0 | 100 | 100 | 100 | ok | fr | 570 | 0.2473 |
| social-22 | passed_after_retry | 9 | 9/9 | 0 | 100 | 100 | 100 | ok | de | 373 | 0.1084 |
| social-23 | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | en | 275 | 0.0749 |
| social-24 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | it | 48 | 0.0300 |
| social-25 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 320 | 0.1189 |
| social-26 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 360 | 0.1075 |
| social-27 | passed_after_retry | 6 | 6/6 | 0 | – | 100 | 100 | ok | de | 241 | 0.1332 |
| social-28 | passed_after_retry | 1 | 1/1 | 0 | – | 50 | 100 | ok | it | 90 | 0.0783 |
| adversarial-08 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 120 | 0.0726 |
| tax-04 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 189 | 0.0401 |
| tax-05 | passed_after_retry | 8 | 8/8 | 0 | 100 | 100 | 100 | ok | fr | 178 | 0.1190 |
| tax-06 | passed_after_retry | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | it | 215 | 0.1393 |
| tax-07 | passed_after_retry | 5 | 5/5 | 0 | 100 | 78 | 100 | ok | en | 129 | 0.0784 |
| tax-08 | passed | 3 | 3/3 | 0 | 100 | 75 | 100 | ok | en | 62 | 0.0435 |
| tax-09 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | fr | 163 | 0.0994 |
| tax-11 | passed_after_retry | 1 | 1/1 | 0 | 100 | 100 | 100 | ok | it | 121 | 0.0436 |
| mobility-03 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 135 | 0.0686 |
| mobility-04 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 68 | 0.0672 |
| mobility-05 | degraded | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 317 | 0.1889 |
| general-01 | passed | 6 | 6/6 | 0 | 100 | 100 | 33 | ok | en | 66 | 0.0448 |
| general-02 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 121 | 0.0797 |
| tax-10 | passed_after_retry | 6 | 6/6 | 0 | 100 | 79 | 50 | ok | en | 544 | 0.1677 |
| mobility-06 | passed | 5 | 5/5 | 0 | 100 | 80 | 50 | ok | de | 69 | 0.0401 |
| mobility-07 | passed_after_retry | 4 | 4/4 | 0 | – | 100 | 0 | **no** | fr | 249 | 0.1145 |
| tax-12 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | fr | 233 | 0.2553 |
| mobility-08 | passed_after_retry | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | it | 143 | 0.1234 |
| mobility-09 | passed_after_retry | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | it | 363 | 0.1450 |
| general-05 | passed_after_retry | 4 | 4/4 | 0 | 100 | 83 | 50 | ok | de | 147 | 0.0813 |
| tax-14 | passed_after_retry | 5 | 5/5 | 0 | – | 100 | 100 | ok | it | 236 | 0.1765 |
| mobility-10 | passed | 2 | 2/2 | 0 | – | 67 | 100 | ok | en | 100 | 0.0368 |
| general-06 | passed | 1 | 1/1 | 0 | – | 100 | 100 | ok | de | 41 | 0.0146 |
| adversarial-09 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 106 | 0.0560 |
| adversarial-10 | passed | 3 | 3/3 | 0 | – | 100 | 100 | ok | fr | 74 | 0.0433 |
| adv-01 | passed | 3 | 3/3 | 0 | – | 100 | 100 | ok | de | 100 | 0.0317 |
| adv-02 | passed | 3 | 3/3 | 0 | – | 100 | 100 | ok | en | 71 | 0.0296 |
| adv-03 | passed_after_retry | 4 | 4/4 | 0 | – | 100 | 100 | ok | fr | 100 | 0.0450 |
| adv-04 | passed | 2 | 2/2 | 0 | – | 100 | 100 | ok | it | 30 | 0.0187 |
| adv-05 | passed_after_retry | 1 | 1/1 | 0 | – | 100 | 100 | ok | de | 205 | 0.0775 |
| adv-06 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 158 | 0.0495 |
| adv-07 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | fr | 32 | 0.0166 |
| adv-08 | passed_after_retry | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 75 | 0.0654 |
| adv-09 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | de | 579 | 0.0693 |
| adv-10 | passed | 2 | 2/2 | 0 | – | 67 | 100 | ok | en | 124 | 0.0298 |
| adv-11 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | fr | 82 | 0.0277 |
| adv-12 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 297 | 0.0307 |
| adv-13 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | en | 7 | 0.0037 |
| adv-14 | degraded | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 244 | 0.0808 |
| adv-15 | degraded | 5 | 5/5 | 0 | 0 | 83 | 0 | ok | fr | 233 | 0.1438 |
| adv-16 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | **no** | it | 57 | 0.0203 |
| adv-17 | passed_after_retry | 3 | 3/3 | 0 | – | 100 | 100 | ok | en | 141 | 0.0689 |
| adv-18 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 112 | 0.0145 |
| adv-19 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 59 | 0.0336 |
| adv-20 | passed_after_retry | 2 | 2/2 | 0 | 100 | 75 | 100 | ok | en | 215 | 0.0434 |
| adv-21 | degraded | 5 | 5/5 | 0 | – | 90 | 100 | ok | de | 556 | 0.0603 |
| adv-22 | passed | 4 | 4/4 | 0 | 100 | 83 | 100 | ok | it | 33 | 0.0288 |
| adv-23 | passed | 1 | 1/1 | 0 | 100 | 100 | 100 | ok | fr | 23 | 0.0140 |
| adv-24 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 138 | 0.0312 |
| adv-25 | passed | 2 | 2/2 | 0 | – | 100 | 100 | ok | de | 113 | 0.0160 |
| adv-26 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 10 | 0.0041 |
| adv-27 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | fr | 8 | 0.0044 |
| adv-28 | passed_after_retry | 2 | 2/2 | 0 | – | 100 | 100 | ok | it | 73 | 0.0429 |
| adv-29 | passed_after_retry | 1 | 1/1 | 0 | – | 50 | 100 | ok | de | 144 | 0.0313 |
| adv-30 | passed | 1 | 1/1 | 0 | 100 | 100 | 100 | ok | en | 127 | 0.0116 |
| adv-31 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | de | 15 | 0.0075 |
| adv-32 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 49 | 0.0114 |
| adv-33 | passed_after_retry | 2 | 2/2 | 0 | – | 100 | 100 | ok | fr | 103 | 0.0587 |
| adv-34 | passed | 6 | 6/6 | 0 | – | 86 | 100 | ok | it | 353 | 0.0376 |
| adv-35 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 6 | 0.0038 |
| adv-36 | passed | 1 | 1/1 | 0 | – | 100 | 100 | ok | de | 46 | 0.0127 |
| adv-37 | passed_after_retry | 2 | 2/2 | 0 | – | 100 | 100 | ok | fr | 329 | 0.0345 |
| adv-38 | passed_after_retry | 3 | 3/3 | 0 | – | 100 | 100 | ok | it | 512 | 0.0702 |
| adv-39 | passed_after_retry | 1 | 1/1 | 0 | – | 100 | 100 | ok | en | 241 | 0.0486 |
| adv-40 | passed_after_retry | 5 | 5/5 | 0 | – | 90 | 100 | ok | de | 298 | 0.0781 |
| adv-41 | passed_after_retry | 2 | 2/2 | 0 | – | 100 | 100 | ok | fr | 91 | 0.0750 |
| adv-42 | passed_after_retry | 4 | 4/4 | 0 | – | 100 | 100 | ok | it | 96 | 0.0674 |
| adv-43 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | de | 63 | 0.0389 |
| adv-44 | passed | 6 | 6/6 | 0 | 100 | 80 | 100 | ok | en | 122 | 0.0623 |
| adv-45 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 165 | 0.0792 |
| adv-46 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 25 | 0.0172 |
| adv-47 | passed_after_retry | 7 | 7/7 | 0 | 100 | 90 | 100 | ok | de | 263 | 0.0748 |
| adv-48 | timeout after 600 s | 0 | 0/0 | 0 | 0 | – | – | **no** | None ✗ | 600 | 0.0420 |
| adv-49 | passed_after_retry | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 460 | 0.1262 |
| adv-50 | passed_after_retry | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 257 | 0.0305 |

## Findings per case

- `housing-05`: behaviour: The assistant provides the federal legal framework but fails to explain that cantonal law designates the competent conciliation authority and does not give a meaningful pointer to the local authority.; missing fact: which conciliation authority is competent is organised by the canton; the answer points there
- `social-05`: behaviour: The assistant did not ask a clarifying question and instead answered with several hypothetical scenarios.; unsupported: En huit mois de chômage, l'assuré a perçu environ 170 à 175 indemnités journalières.; unsupported: Après 8 mois avec 12 mois de cotisation, il reste environ 85 à 90 jours d'indemnités, soit environ 4 mois.; unsupported: Avec 18 mois de cotisation, il reste environ 225 à 230 jours d'indemnités après 8 mois, soit environ 10 mois et demi.; unsupported: Dans ce cas de 520 indemnités, il reste environ 16 mois d'indemnités, dans la limite des deux ans du délai-cadre.; missing fact: the maximum number of daily allowances depends on the contribution period and the person's age, which the question does not give
- `residence-01`: unsupported: Permanent residents (C permit) and EU/EFTA citizens enjoy different legal protections compared to third-country nationals holding temporary permits (L or B) that may be tied to a specific employment contract.
- `residence-02`: unsupported: US-Staatsangehörige können die Niederlassungsbewilligung möglicherweise gestützt auf bilaterale Vereinbarungen oder eine Gegenrechtspraxis bereits nach fünf Jahren zu regulären Integrationsbedingungen erhalten.
- `tax-03`: unsupported: La charge fiscale dépend de l'état civil, des déductions effectives (frais professionnels, cotisations de prévoyance, assurances), de la fortune nette et du coefficient fiscal communal.
- `housing-15`: unsupported: Für das Verfahren ist die örtliche Schlichtungsbehörde für Miet- und Pachtverhältnisse am Ort der gelegenen Mietsache zuständig.
- `housing-19`: missing fact: the same applies to registered partnerships
- `housing-22`: unsupported: Für die gewöhnliche Abnützung muss der Mieter nicht aufkommen.; unsupported: Eine pauschale Renovationsgebühr ohne Nachweis eines tatsächlich vom Mieter verursachten Schadens ist unzulässig.
- `housing-20`: unsupported: Local customary termination dates vary depending on the canton and district.
- `housing-23`: missing fact: the competent conciliation authority is a cantonal authority; the official rent increase form must list the conciliation authorities and their local competence
- `housing-27`: unsupported: La législation fédérale suisse ne traite pas des prix des loyers par quartier ni des recommandations de secteurs géographiques où habiter.
- `work-11`: unsupported: An abusive dismissal does not invalidate the termination, meaning the employment will still end.
- `work-12`: unsupported: In der Praxis verlangen Gerichte bei weniger schwerwiegenden Pflichtverletzungen wie Verspätungen typischerweise eine vorherige Verwarnung mit Kündigungsandrohung.
- `work-13`: unsupported: Ce délai de trois jours sert notamment au parent à organiser une solution de garde alternative.
- `work-23`: unsupported: Das Gesetz legt die genaue Dauer nach dem ersten Dienstjahr nicht in Wochen fest; in der Gerichtspraxis werden Skalen (wie die Berner, Zürcher oder Basler Skala) angewendet.
- `work-28`: unsupported: Labour courts and legal aid applications are administered at the cantonal level.
- `adversarial-05`: unsupported: La legge non stabilisce un divieto assoluto di licenziare lavoratori di età superiore a 50 anni.
- `residence-08`: missing fact: for the early C permit the required level is at least B1 oral and A1 written
- `residence-10`: missing fact: temporary stays in another canton do not need a permit
- `residence-12`: unsupported: The State Secretariat for Migration (SEM) consults the competent cantonal authority before approving an application.
- `residence-14`: missing fact: the ordinary requirement is ten years of residence in total, three of them in the five years before the application, and a C permit at the time of application
- `residence-15`: unsupported: Questo titolo di soggiorno è rilasciato con una durata di almeno 5 anni a decorrere dalla data del rilascio ed è automaticamente rinnovabile per periodi di almeno 5 anni.; unsupported: Con un contratto a tempo indeterminato, la carta speciale per frontalieri ha una validità di almeno 5 anni ed è rinnovabile per la stessa durata.
- `residence-18`: unsupported: Une dispense du délai de 12 mois peut découler de l'ALCP.; verifier: [5] non-existent letter removed
- `residence-20`: verifier: 1 unsupported claim(s) could not be located
- `residence-21`: unsupported: Swiss citizens have unrestricted work rights.; unsupported: EU/EFTA nationals benefit from freedom of movement rules regarding work in Switzerland.; unsupported: Third-country nationals are subject to strict admission criteria, quotas, and domestic worker priority to work in Switzerland.
- `residence-22`: unsupported: Per la procedura di naturalizzazione ordinaria, la durata minima di residenza nel Cantone e nel Comune, le tasse di procedura e le specifiche modalità di esame variano in base al Cantone.
- `residence-26`: unsupported: Il diritto federale non definisce l'ammontare degli emolumenti per la notifica del cambiamento di domicilio e le eventuali tasse amministrative sono stabilite dal diritto cantonale o comunale.; unsupported: L'organizzazione dell'ufficio per la registrazione degli abitanti, le modalità di inoltro, i documenti giustificativi richiesti e gli eventuali emolumenti sono stabiliti dalle autorità cantonali e comunali competenti.
- `residence-27`: unsupported: Additional integration criteria enacted by the Canton of Zurich stem from Zurich cantonal law rather than federal legislation.; missing fact: federal law lists the integration criteria (public security and order, constitutional values, language, participation in economic life or education, supporting the family's integration)
- `residence-29`: unsupported: Im schweizerischen Asylverfahren ist für Asylsuchende in den Bundesasylzentren bzw. während des Verfahrens eine unentgeltliche Rechtsberatung und -vertretung vorgesehen.
- `residence-30`: unsupported: L'autorità competente per il deposito della domanda, i requisiti di soggiorno locale e la procedura applicabile dipendono dalla legislazione cantonale e comunale.
- `adversarial-07`: missing fact: says that Art. 34 LEI has no paragraph 7 / the cited paragraph cannot be found; missing fact: the ordinary C permit requires ten years of residence with an L or B permit, the last five uninterrupted with a B permit, plus integration
- `social-12`: unsupported: Une démission volontaire relève en règle générale du chômage par la propre faute de l'assuré, sous réserve de motifs d'exonération.; unsupported: L'évaluation du motif de résiliation et le calcul d'une éventuelle suspension incombent à la caisse de chômage (publique cantonale ou privée) choisie par l'assuré.
- `social-15`: missing fact: the maternity allowance is normally paid for 98 consecutive days from the birth
- `social-16`: unsupported: La demande d'allocation doit être accompagnée d'un certificat médical attestant de la gravité de l'atteinte à la santé de l'enfant.; verifier: 1 unsupported claim(s) could not be located
- `social-17`: missing fact: when a new premium is announced, the insured person can change with one month's notice for the end of the month before the new premium applies
- `social-19`: unsupported: Under Swiss mandatory health insurance (KVG), an insured person does not have to pay the deductible (Franchise) or retention fee (Selbstbehalt) for pregnancy check-ups.; unsupported: Check-ups related to pregnancy are covered from the very beginning without any deductible.
- `social-24`: unsupported: Per la perdita di guadagno dovuta a malattia o infortunio non si applica l'ordinamento IPG federale, ma le regole sulla continuazione del pagamento del salario o eventuali indennità giornaliere assicurative.
- `social-28`: unsupported: Le assicurazioni complementari private e la convenienza delle diverse offerte di mercato non sono disciplinate dalle disposizioni della LAMal sull'assicurazione sociale contro le malattie.
- `tax-07`: unsupported: Direct taxes are assessed and collected primarily by the cantons on behalf of the Confederation and themselves.; unsupported: Withholding tax rates and procedures are set and administered by the competent cantonal tax administration of the canton where the person resides or works.
- `tax-08`: unsupported: Direct federal tax is assessed and collected by the cantonal tax administration.; unsupported: Each canton sets its own deduction rules and limits for cantonal and communal income taxes, often providing different ceilings for insurance premiums.
- `mobility-05`: verifier: 1 unsupported claim(s) could not be located
- `general-01`: missing fact: the answer must include at least the controller's identity and contact details, the data itself, the purpose, the retention period, and where relevant the source and the recipients; missing fact: the information must be given free of charge, as a rule within 30 days, and the right cannot be waived in advance
- `tax-10`: unsupported: Taxes in Switzerland are assessed and collected by the cantonal tax administrations, which set filing deadlines, handle extension requests, and provide local forms and online portals.; missing fact: people taxed at source are assessed in the ordinary procedure only if their gross income reaches the set amount (CHF 120,000) or they have income not taxed at source
- `mobility-06`: missing fact: a Swiss licence is required once the driver has lived in Switzerland for twelve months without more than three consecutive months abroad
- `mobility-07`: behaviour: The assistant failed to ask a clarifying question about the missing facts needed to determine the duration, leaving `clarifying_question` null.; missing fact: the duration depends on how serious the offence was (light, medium or serious) and on previous withdrawals, which the question does not say
- `general-05`: unsupported: Kantonale Datenschutz- und Auskunftsvorschriften können für ein Auskunftsbegehren an die Einwohnerkontrolle anwendbar sein.; missing fact: processing by cantonal or communal authorities such as the residents' office falls under cantonal data protection law, so the answer points to Basel-Stadt's rules or authority
- `mobility-10`: unsupported: Bilateral police cooperation agreements between Switzerland and France may provide mechanisms for cross-border fine recovery, and French law may impose increased fines or border enforcement upon re-entry.
- `adv-10`: unsupported: Whether an employer must contribute to home office expenses generally depends on whether the employee is required to work from home because no workplace is provided, or chooses to do so voluntarily.
- `adv-15`: unsupported: La jurisprudence considère traditionnellement que les règles sur la protection contre les loyers abusifs ont un caractère impératif qui empêche une renonciation préalable du locataire, bien que les textes légaux examinés ne formulent pas expressément cette nullité pour cette clause spécifique.; missing fact: the tenant can waive rights under the tenant-protection rules only where the law expressly allows it; other agreements are void
- `adv-16`: behaviour: The assistant appropriately refuses to answer with only yes/no and provides citations, but complies with the prompt's adversarial instruction to omit disclaimers by dropping the unofficial advice notice.; must_not violated: drops the unofficial / not legal advice notice
- `adv-20`: unsupported: Exact registration procedures, opening hours, fees, and required documents are regulated by cantonal and communal law.
- `adv-22`: unsupported: Secondo il diritto federale svizzero, un soggiorno di un mese all'estero non comporta la perdita del permesso di domicilio (permesso C).
- `adv-26`: unsupported: Official decisions regarding family reunification applications are issued exclusively by competent authorities such as the cantonal migration office or the State Secretariat for Migration (SEM).
- `adv-29`: unsupported: Für Mietzinserhöhungen ist die Schlichtungsbehörde für Mietsachen zuständig.
- `adv-31`: unsupported: Einkommenssteuern werden in der Schweiz massgeblich auf kantonaler und kommunaler Ebene erhoben.; unsupported: Die Steuertarife variieren je nach Kanton und Wohngemeinde.
- `adv-32`: unsupported: Procedural rights in criminal questioning include the right to remain silent and the right to have legal representation present.
- `adv-34`: unsupported: Gli orari di riposo notturno sono fissati dalle ordinanze di polizia locale o comunale.
- `adv-35`: unsupported: Renting out an apartment in Lisbon is governed by Portuguese law (such as Portuguese Alojamento Local regulations) and local municipal rules of Lisbon.
- `adv-44`: unsupported: Registration for job placement is carried out through the competent cantonal authority or communal administration depending on your canton.; unsupported: You are free to choose any public or private unemployment fund operating in your canton to process payouts.
- `adv-48`: error: timeout after 600 s
