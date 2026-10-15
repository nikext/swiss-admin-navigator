# Answer eval: answers-drafts

- dataset: `evals/datasets/drafts/golden.jsonl` (30 cases, sha a804ef589951) — **drafts, not human-verified: not a headline number**
- agent: `gemini-3.8-flash@eu`, prompt sha 766534f90f94, google-adk 2.12.0, structured output native schema + tools
- judge: `gemini-3.1-pro-preview@global`, prompt sha f27c1e4d6e4f
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-15T18:13:55+00:00 at 3e7e603; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **100.0%** (108/108; CI 100.0–100.0) |
| hallucinated citations | **0** of 108 |
| required-citation recall | **100.0** (100.0–100.0, n=23) |
| citation precision (expected only) | **54.7** (44.6–65.4, n=26) |
| citation precision (expected or judged relevant) | **100.0** (100.0–100.0, n=26) |
| groundedness (judge, claim level) | **80.7** (70.0–90.2, n=28) |
| key-fact coverage (judge) | **100.0** (100.0–100.0, n=30) |
| must_not violations (judge) | **0** |
| behaviour accuracy (rule + judge) | **93.3** (83.3–100.0, n=30) |
| behaviour (rule only) | **96.7** (90.0–100.0, n=30) |
| language match | **100.0** (100.0–100.0, n=30) |
| errors | 0 |

## Verifier

- first drafts: 109 citations, 109 quotes; problems {'paragraph': 1, 'quote': 1}; 1 cases sent back once
- final status: {'passed': 29, 'passed_after_retry': 1}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0364 mean, 0.1298 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 1.092, judge CHF 0.885
- latency p50 35.4 s, p95 129.2 s; 7.2 model calls and 6.2 tool calls per answer; tokens per answer (mean): prompt 67,650, cached 37,784, output 1,157, thoughts 3,954

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: adversarial | 2 | 100 | 17 | 100 | 100 |
| category: answerable | 20 | 95 | 87 | 100 | 100 |
| category: cantonal_pointer | 3 | 100 | 93 | 100 | 100 |
| category: needs_clarification | 3 | 67 | 50 | 100 | 100 |
| category: out_of_scope | 2 | 100 | 100 | 100 | 100 |
| lang: de | 8 | 88 | 80 | 100 | 100 |
| lang: en | 8 | 100 | 62 | 100 | 100 |
| lang: fr | 7 | 86 | 96 | 100 | 100 |
| lang: it | 7 | 100 | 92 | 100 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| housing-01 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 62 | 0.0484 |
| housing-02 | passed | 2 | 2/2 | 0 | 100 | 75 | 100 | ok | de | 16 | 0.0128 |
| housing-03 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 20 | 0.0114 |
| housing-04 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | en | 28 | 0.0228 |
| housing-05 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 31 | 0.0291 |
| work-01 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 46 | 0.0330 |
| work-02 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 23 | 0.0236 |
| work-03 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 22 | 0.0190 |
| work-04 | passed | 2 | 2/2 | 0 | 100 | 75 | 100 | ok | en | 15 | 0.0124 |
| work-05 | passed | 5 | 5/5 | 0 | 100 | 56 | 100 | **no** | de | 59 | 0.0558 |
| work-06 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | fr | 38 | 0.0312 |
| social-01 | passed | 6 | 6/6 | 0 | 100 | 83 | 100 | ok | de | 129 | 0.1298 |
| social-02 | passed | 7 | 7/7 | 0 | 100 | 78 | 100 | ok | it | 76 | 0.0549 |
| social-03 | passed | 5 | 5/5 | 0 | 100 | 59 | 100 | ok | en | 42 | 0.0396 |
| social-04 | passed | 5 | 5/5 | 0 | 100 | 80 | 100 | ok | fr | 39 | 0.0335 |
| social-05 | passed | 5 | 5/5 | 0 | – | 100 | 100 | **no** | fr | 52 | 0.0365 |
| residence-01 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 22 | 0.0156 |
| residence-02 | passed | 5 | 5/5 | 0 | 100 | 90 | 100 | ok | de | 82 | 0.0437 |
| residence-03 | passed_after_retry | 7 | 7/7 | 0 | 100 | 90 | 100 | ok | fr | 199 | 0.1328 |
| residence-04 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 41 | 0.0377 |
| residence-05 | passed | 5 | 5/5 | 0 | 100 | 90 | 100 | ok | en | 42 | 0.0364 |
| residence-06 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 33 | 0.0272 |
| residence-07 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | it | 32 | 0.0250 |
| tax-01 | passed | 6 | 6/6 | 0 | 100 | 70 | 100 | ok | en | 68 | 0.0479 |
| tax-02 | passed | 3 | 3/3 | 0 | 100 | 80 | 100 | ok | it | 35 | 0.0257 |
| tax-03 | passed | 1 | 1/1 | 0 | – | 100 | 100 | ok | fr | 29 | 0.0153 |
| mobility-01 | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | en | 78 | 0.0607 |
| mobility-02 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | it | 8 | 0.0044 |
| adversarial-01 | passed | 2 | 2/2 | 0 | – | 33 | 100 | ok | de | 32 | 0.0214 |
| adversarial-02 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 8 | 0.0046 |

## Findings per case

- `housing-02`: unsupported: Die Kantone können zum Mietzinsdepot ergänzende Bestimmungen erlassen.
- `work-04`: unsupported: An individual employment contract or an applicable collective bargaining agreement may provide for more vacation days.
- `work-05`: behaviour: The answer includes several legal statements without citations, such as the definition of Überzeit, the specific weekly maximum hours, and the inability to contractually waive compensation for Überzeit.; unsupported: Im Schweizer Arbeitsrecht muss zwischen Überstunden (Überschreitung der vertraglichen Arbeitszeit) und Überzeit (Überschreitung der gesetzlichen Höchstarbeitszeit) unterschieden werden.; unsupported: Eine vertragliche Klausel, wonach Überstunden ohne Zuschlag bezahlt werden oder mit dem Grundlohn abgegolten sind, ist bei Überstunden rechtlich zulässig.; unsupported: Wird die gesetzliche wöchentliche Höchstarbeitszeit (nach Arbeitsgesetz 45 bzw. 50 Stunden) überschritten, handelt es sich um Überzeit.; unsupported: Der Anspruch auf Abgeltung von Überzeit kann im Arbeitsvertrag nicht wegbedungen werden.
- `social-02`: unsupported: Per un'attività a tempo pieno, due settimane di congedo corrispondono a 10 giorni lavorativi.; unsupported: Per avere diritto all'indennità è necessario essere stati assicurati AVS per almeno 9 mesi e aver lavorato almeno 5 mesi prima della nascita.
- `social-03`: unsupported: You will have to pay monthly premiums retroactively from the date you took up residence.; unsupported: Any medical treatments or healthcare costs incurred before the date you join will not be reimbursed.; unsupported: Cantons are tasked with enforcing the insurance mandate.; unsupported: Each canton designates a specific authority (typically the cantonal health or social insurance office) that checks whether new residents have obtained coverage and assigns them to an insurer if they do not comply.
- `social-04`: unsupported: Ces 12 mois de cotisation ne doivent pas nécessairement être continus ni réalisés auprès du même employeur.
- `social-05`: behaviour: The assistant provided a detailed branching answer covering multiple scenarios instead of asking a concise clarifying question about the user's age and contribution period.
- `residence-01`: unsupported: Permanent residence permit holders (C permit) generally do not lose their status due to unemployment.; unsupported: EU/EFTA and third-country nationals holding short-stay (L) or residence (B) permits are subject to different grace periods, conditions, and rules regarding unemployment compensation.
- `residence-05`: unsupported: Communes often set their own municipal residence requirements.
- `tax-01`: unsupported: Any tax already deducted at source is credited without interest against the final tax liability.; unsupported: Cantons set their own wealth tax thresholds that may trigger mandatory filing.
- `tax-02`: unsupported: L'aliquota comunale di Lugano viene stabilita secondo le regole del diritto cantonale ticinese dagli organi politici del Comune (il Consiglio comunale, su proposta del Municipio).
- `adversarial-01`: unsupported: Einen Artikel «Art. 271z» gibt es im Schweizerischen Obligationenrecht (OR) nicht.; unsupported: Es existiert im Bundesrecht keine pauschale Bestimmung, die eine Mietzinskürzung um 50 % bei Lärm vorsieht.; unsupported: Das Gesetz legt keinen festen Prozentsatz für die Mietzinsherabsetzung fest; sie muss dem Ausmass der tatsächlichen Beeinträchtigung entsprechen.; unsupported: Der Mietzins darf nicht einfach eigenmächtig gekürzt werden.
- `adversarial-02`: unsupported: Decisions on the renewal of residence permits (B permits) fall under the jurisdiction of the competent cantonal migration authorities and, where applicable, the SEM.
