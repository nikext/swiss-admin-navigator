# Answer eval: baseline-rerun

- dataset: `golden` (2 cases selected, 2 verified by claude-opus-5-5; sha 283079d403c1 over golden.jsonl)
- agent: `gemini-3.8-flash@eu`, prompt sha 766534f90f94, google-adk 2.12.0, structured output native schema + tools
- judge: `gemini-3.8-flash@global`, prompt sha d83d68626291
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-15T22:31:41+00:00 at 7bd9768; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **70.0%** (7/10; CI 25.0–100.0) |
| hallucinated citations | **0** of 10 |
| required-citation recall | **50.0** (0.0–100.0, n=2) |
| citation precision (expected only) | **25.0** (0.0–50.0, n=2) |
| citation precision (expected or judged relevant) | **87.5** (75.0–100.0, n=2) |
| groundedness (judge, claim level) | **66.7** (33.3–100.0, n=2) |
| key-fact coverage (judge) | **83.3** (66.7–100.0, n=2) |
| must_not violations (judge) | **0** |
| behaviour accuracy (rule + judge) | **100.0** (100.0–100.0, n=2) |
| behaviour (rule only) | **100.0** (100.0–100.0, n=2) |
| language match | **100.0** (100.0–100.0, n=2) |
| errors | 0 |

## Verifier

- first drafts: 10 citations, 10 quotes; problems {'paragraph': 3, 'quote': 3}; 1 cases sent back once
- final status: {'degraded': 1, 'passed': 1}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.1064 mean, 0.1769 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 0.213, judge CHF 0.018
- latency p50 55.7 s, p95 260.3 s; 14.0 model calls and 12.5 tool calls per answer; tokens per answer (mean): prompt 257,278, cached 189,896, output 2,274, thoughts 15,058

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: answerable | 2 | 100 | 67 | 83 | 100 |
| lang: en | 1 | 100 | 100 | 67 | 100 |
| lang: it | 1 | 100 | 33 | 100 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| residence-15 | degraded | 4 | 1/4 | 0 | 0 | 33 | 100 | ok | it | 260 | 0.1769 |
| general-01 | passed | 6 | 6/6 | 0 | 100 | 100 | 67 | ok | en | 56 | 0.0359 |

## Findings per case

- `residence-15`: unsupported: Poiché il contratto di lavoro è a tempo indeterminato (durata uguale o superiore a un anno), il permesso ha una validità di 5 anni ed è automaticamente rinnovabile per periodi di almeno 5 anni.; unsupported: Il lavoratore frontaliero è chi risiede in Italia e rientra regolarmente al proprio domicilio di norma ogni giorno o almeno una volta alla settimana.; unsupported: Per un impiego di durata pari o superiore a un anno, il permesso per frontalieri viene rilasciato per una durata di 5 anni ed è rinnovabile per periodi di almeno 5 anni purché continui a esercitare un'attività economica.; unsupported: Chi si trasferisce in Svizzera deve registrarsi presso l'ufficio controllo abitanti del proprio Comune di residenza entro 14 giorni dall'arrivo.; verifier: [2] non-existent paragraph removed; verifier: [3] non-existent paragraph removed; verifier: [4] non-existent paragraph removed
- `general-01`: missing fact: the information must be given free of charge, as a rule within 30 days, and the right cannot be waived in advance
