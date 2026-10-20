# Answer eval: e1-argon-budget

- dataset: `golden` (5 cases selected, 5 verified by claude-opus-5-5; sha 283079d403c1 over golden.jsonl)
- agent: `gemini-4-argon@global`, prompt sha 604f3a1f7ee4, google-adk 2.12.0, structured output native schema + tools
- judge: `gemini-3.8-flash@eu`, prompt sha d83d68626291
- input screen (M10): Model Armor `swiss-nav-input`, block at medium; blocked 0
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-20T00:57:12+00:00 at 31e2ad7; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **93.9%** (31/33; CI 80.0–100.0) |
| hallucinated citations | **0** of 33 |
| required-citation recall | **75.0** (25.0–100.0, n=4) |
| citation precision (expected only) | **19.5** (2.9–36.7, n=5) |
| citation precision (expected or judged relevant) | **100.0** (100.0–100.0, n=5) |
| groundedness (judge, claim level) | **91.7** (75.0–100.0, n=5) |
| key-fact coverage (judge) | **100.0** (100.0–100.0, n=5) |
| must_not violations (judge) | **0** |
| behaviour accuracy (rule + judge) | **100.0** (100.0–100.0, n=5) |
| behaviour (rule only) | **100.0** (100.0–100.0, n=5) |
| answers with contact details (rule: address, postcode, phone, web) | 0 |
| language match | **100.0** (100.0–100.0, n=5) |
| errors | 0 |

## Verifier

- first drafts: 35 citations, 35 quotes; problems {'paragraph': 5, 'quote': 5}; 1 cases sent back once
- final status: {'passed': 4, 'passed_after_retry': 1}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0832 mean, 0.1504 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 0.416, judge CHF 0.047
- latency p50 58.1 s, p95 166.5 s; 8.8 model calls and 12.2 tool calls per answer; tokens per answer (mean): prompt 120,193, cached 90,769, output 2,264, thoughts 1,086

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: answerable | 3 | 100 | 86 | 100 | 100 |
| category: cantonal_pointer | 1 | 100 | 100 | 100 | 100 |
| category: out_of_scope | 1 | 100 | 100 | 100 | 100 |
| lang: de | 1 | 100 | 100 | 100 | 100 |
| lang: fr | 1 | 100 | 100 | 100 | 100 |
| lang: it | 3 | 100 | 86 | 100 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| social-02 | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | it | 58 | 0.0598 |
| residence-15 | passed_after_retry | 6 | 4/6 | 0 | 0 | 58 | 100 | ok | it | 166 | 0.1504 |
| residence-16 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 81 | 0.0999 |
| residence-28 | passed | 8 | 8/8 | 0 | 100 | 100 | 100 | ok | fr | 49 | 0.0408 |
| tax-14 | passed | 9 | 9/9 | 0 | – | 100 | 100 | ok | it | 57 | 0.0649 |

## Findings per case

- `residence-15`: unsupported: Con un impiego di durata uguale o superiore a un anno, la carta di soggiorno ha una durata di almeno 5 anni a decorrere dal rilascio ed è automaticamente rinnovabile per almeno 5 anni.; unsupported: In occasione del primo rinnovo della carta di soggiorno, la validità può essere limitata (a non meno di un anno) in caso di disoccupazione involontaria da oltre 12 mesi consecutivi.
