# Answer eval: cantonal-contact

- dataset: `golden` (15 cases selected, 15 verified by claude-opus-5-5; sha 283079d403c1 over golden.jsonl)
- agent: `gemini-3.8-flash@eu`, prompt sha 604f3a1f7ee4, google-adk 2.12.0, structured output native schema + tools
- judge: `gemini-3.8-flash@global`, prompt sha d83d68626291
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-16T07:57:18+00:00 at 5bb5b0a; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **100.0%** (53/53; CI 100.0–100.0) |
| hallucinated citations | **0** of 53 |
| required-citation recall | **100.0** (100.0–100.0, n=14) |
| citation precision (expected only) | **51.1** (38.9–65.6, n=15) |
| citation precision (expected or judged relevant) | **100.0** (100.0–100.0, n=15) |
| groundedness (judge, claim level) | **82.9** (75.3–90.8, n=15) |
| key-fact coverage (judge) | **93.3** (83.3–100.0, n=15) |
| must_not violations (judge) | **0** |
| behaviour accuracy (rule + judge) | **100.0** (100.0–100.0, n=15) |
| behaviour (rule only) | **100.0** (100.0–100.0, n=15) |
| answers with contact details (rule: address, postcode, phone, web) | 0 |
| language match | **100.0** (100.0–100.0, n=15) |
| errors | 0 |

## Verifier

- first drafts: 53 citations, 53 quotes; problems none; 0 cases sent back once
- final status: {'passed': 15}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0365 mean, 0.0558 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 0.548, judge CHF 0.108
- latency p50 56.3 s, p95 127.0 s; 7.6 model calls and 6.6 tool calls per answer; tokens per answer (mean): prompt 67,975, cached 37,240, output 1,058, thoughts 3,931

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: cantonal_pointer | 15 | 100 | 83 | 93 | 100 |
| lang: de | 5 | 100 | 80 | 100 | 100 |
| lang: en | 2 | 100 | 100 | 75 | 100 |
| lang: fr | 4 | 100 | 80 | 88 | 100 |
| lang: it | 4 | 100 | 81 | 100 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| housing-05 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 30 | 0.0202 |
| residence-06 | passed | 4 | 4/4 | 0 | 100 | 81 | 100 | ok | de | 47 | 0.0322 |
| tax-02 | passed | 3 | 3/3 | 0 | 100 | 75 | 100 | ok | it | 44 | 0.0283 |
| housing-23 | passed | 2 | 2/2 | 0 | 100 | 75 | 50 | ok | fr | 40 | 0.0273 |
| housing-24 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 37 | 0.0216 |
| housing-25 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 64 | 0.0353 |
| work-25 | passed | 2 | 2/2 | 0 | 100 | 67 | 100 | ok | fr | 23 | 0.0167 |
| work-26 | passed | 2 | 2/2 | 0 | – | 50 | 100 | ok | de | 76 | 0.0340 |
| residence-26 | passed | 3 | 3/3 | 0 | 100 | 70 | 100 | ok | it | 56 | 0.0433 |
| residence-27 | passed | 3 | 3/3 | 0 | 100 | 100 | 50 | ok | en | 127 | 0.0580 |
| residence-28 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 69 | 0.0462 |
| social-25 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 43 | 0.0342 |
| social-26 | passed | 6 | 6/6 | 0 | 100 | 80 | 100 | ok | fr | 129 | 0.0410 |
| mobility-09 | passed | 6 | 6/6 | 0 | 100 | 79 | 100 | ok | it | 125 | 0.0539 |
| general-05 | passed | 4 | 4/4 | 0 | 100 | 67 | 100 | ok | de | 117 | 0.0558 |

## Findings per case

- `residence-06`: unsupported: Die organisatorische Bezeichnung der Meldebehörden ist kantonal und kommunal geregelt.
- `tax-02`: unsupported: Nel diritto svizzero, la fissazione delle aliquote e dei moltiplicatori d'imposta comunali non è disciplinata dal diritto federale, bensì dal diritto cantonale e comunale.
- `housing-23`: unsupported: L'organisation judiciaire et les modalités pratiques de dépôt dépendent du droit cantonal.; missing fact: the competent conciliation authority is a cantonal authority; the official rent increase form must list the conciliation authorities and their local competence
- `work-25`: unsupported: Le statut du lundi de Pâques dans le canton de Vaud relève du droit cantonal vaudois.
- `work-26`: unsupported: Das Schweizer Bundesrecht sieht keinen landesweiten gesetzlichen Mindestlohn vor.; unsupported: Ein genereller gesetzlicher Mindestlohn im Kanton Genf sowie dessen genaue Höhe sind im kantonalen Recht geregelt.
- `residence-26`: unsupported: Il diritto federale non disciplina una tariffa fissa per la registrazione del cambio di indirizzo; gli eventuali emolumenti amministrativi sono stabiliti dal diritto cantonale o comunale.
- `residence-27`: missing fact: federal law lists the integration criteria (public security and order, constitutional values, language, participation in economic life or education, supporting the family's integration)
- `mobility-09`: unsupported: I titolari di patenti rilasciate da Stati dell'UE/AELS o da Paesi con intese di reciprocità sono di regola esentati dalla corsa di controllo e ottengono la licenza svizzera direttamente su pratica amministrativa.
- `general-05`: unsupported: Das Auskunftsrecht bezüglich der Daten einer kantonalen bzw. kommunalen Einwohnerkontrolle beurteilt sich nach dem jeweiligen kantonalen Datenschutzrecht.; unsupported: Die Kantone können darüber hinaus weitere Merkmale in ihren Einwohnerregistern vorsehen.
