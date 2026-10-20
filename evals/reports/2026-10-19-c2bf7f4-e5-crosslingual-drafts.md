# Answer eval: e5-crosslingual-drafts

- dataset: `evals/datasets/crosslingual.jsonl` (120 cases selected, 0 verified; sha df589c5e2986 over crosslingual.jsonl) — **includes drafts: not a headline number**
- agent: `gemini-3.8-flash@eu`, prompt sha 604f3a1f7ee4, google-adk 2.12.0, structured output native schema + tools
- judge: `gemini-3.8-flash@eu`, prompt sha d83d68626291
- input screen (M10): Model Armor `swiss-nav-input`, block at medium; blocked 0
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-19T22:53:17+00:00 at c2bf7f4; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **98.7%** (518/525; CI 97.1–100.0) |
| hallucinated citations | **0** of 525 |
| required-citation recall | **96.2** (92.9–99.2, n=120) |
| citation precision (expected only) | **59.1** (54.3–64.1, n=119) |
| citation precision (expected or judged relevant) | **99.7** (99.2–100.0, n=119) |
| groundedness (judge, claim level) | **86.2** (83.3–89.1, n=120) |
| key-fact coverage (judge) | **95.7** (92.9–98.1, n=120) |
| must_not violations (judge) | **0** |
| behaviour accuracy (rule + judge) | **99.2** (97.5–100.0, n=120) |
| behaviour (rule only) | **99.2** (97.5–100.0, n=120) |
| answers with contact details (rule: address, postcode, phone, web) | 0 |
| language match | **100.0** (100.0–100.0, n=120) |
| errors | 0 |

## Verifier

- first drafts: 531 citations, 531 quotes; problems {'paragraph': 13, 'quote': 13, 'letter': 1}; 8 cases sent back once
- final status: {'passed': 112, 'passed_after_retry': 5, 'degraded': 3}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0441 mean, 0.1028 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 5.294, judge CHF 0.877
- latency p50 36.9 s, p95 132.3 s; 8.2 model calls and 7.2 tool calls per answer; tokens per answer (mean): prompt 88,579, cached 54,473, output 1,376, thoughts 5,060

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: answerable | 120 | 99 | 86 | 96 | 100 |
| lang: de | 30 | 100 | 88 | 99 | 100 |
| lang: en | 30 | 100 | 87 | 97 | 100 |
| lang: fr | 30 | 100 | 87 | 96 | 100 |
| lang: it | 30 | 97 | 83 | 91 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| housing-02-en | passed | 3 | 3/3 | 0 | 100 | 83 | 100 | ok | en | 18 | 0.0141 |
| housing-02-fr | passed | 3 | 3/3 | 0 | 100 | 80 | 100 | ok | fr | 16 | 0.0130 |
| housing-02-it | passed | 2 | 2/2 | 0 | 100 | 50 | 100 | ok | it | 12 | 0.0099 |
| housing-07-en | passed | 3 | 3/3 | 0 | 100 | 67 | 100 | ok | en | 21 | 0.0170 |
| housing-07-fr | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 39 | 0.0243 |
| housing-07-it | passed | 3 | 3/3 | 0 | 100 | 70 | 100 | ok | it | 20 | 0.0179 |
| housing-19-en | passed | 3 | 3/3 | 0 | 100 | 100 | 67 | ok | en | 21 | 0.0203 |
| housing-19-fr | passed | 3 | 3/3 | 0 | 100 | 75 | 67 | ok | fr | 28 | 0.0205 |
| housing-19-it | passed | 4 | 4/4 | 0 | 100 | 67 | 67 | ok | it | 28 | 0.0257 |
| residence-02-en | passed | 5 | 5/5 | 0 | 100 | 83 | 100 | ok | en | 60 | 0.0575 |
| residence-02-fr | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | fr | 52 | 0.0592 |
| residence-02-it | passed | 5 | 5/5 | 0 | 100 | 86 | 100 | ok | it | 71 | 0.0541 |
| residence-13-en | passed | 4 | 4/4 | 0 | 100 | 72 | 100 | ok | en | 32 | 0.0373 |
| residence-13-fr | passed | 5 | 5/5 | 0 | 100 | 75 | 100 | ok | fr | 29 | 0.0329 |
| residence-13-it | passed | 4 | 4/4 | 0 | 100 | 88 | 100 | ok | it | 39 | 0.0438 |
| residence-25-en | passed_after_retry | 6 | 6/6 | 0 | 100 | 93 | 100 | ok | en | 97 | 0.1127 |
| residence-25-fr | passed_after_retry | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | fr | 69 | 0.0804 |
| residence-25-it | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | it | 26 | 0.0245 |
| social-11-en | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | en | 26 | 0.0247 |
| social-11-fr | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 26 | 0.0248 |
| social-11-it | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 27 | 0.0275 |
| work-08-en | passed | 4 | 4/4 | 0 | 100 | 88 | 100 | ok | en | 27 | 0.0223 |
| work-08-fr | passed | 4 | 4/4 | 0 | 100 | 75 | 100 | ok | fr | 22 | 0.0223 |
| work-08-it | passed | 3 | 3/3 | 0 | 100 | 60 | 67 | ok | it | 22 | 0.0195 |
| work-12-en | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 28 | 0.0271 |
| work-12-fr | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | fr | 32 | 0.0240 |
| work-12-it | passed | 6 | 6/6 | 0 | 100 | 88 | 100 | ok | it | 34 | 0.0311 |
| work-23-en | passed | 3 | 3/3 | 0 | 100 | 67 | 100 | ok | en | 24 | 0.0204 |
| work-23-fr | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 23 | 0.0210 |
| work-23-it | passed | 3 | 3/3 | 0 | 100 | 67 | 100 | ok | it | 26 | 0.0252 |
| general-01-de | passed | 6 | 6/6 | 0 | 100 | 80 | 67 | ok | de | 41 | 0.0212 |
| general-01-fr | passed | 8 | 8/8 | 0 | 100 | 100 | 67 | ok | fr | 44 | 0.0440 |
| general-01-it | passed | 6 | 6/6 | 0 | 100 | 100 | 33 | ok | it | 28 | 0.0258 |
| housing-20-de | passed | 7 | 7/7 | 0 | 100 | 88 | 100 | ok | de | 37 | 0.0407 |
| housing-20-fr | passed | 7 | 7/7 | 0 | 100 | 88 | 100 | ok | fr | 33 | 0.0355 |
| housing-20-it | passed | 7 | 7/7 | 0 | 100 | 100 | 100 | ok | it | 37 | 0.0341 |
| mobility-01-de | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 41 | 0.0375 |
| mobility-01-fr | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | fr | 59 | 0.0541 |
| mobility-01-it | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 65 | 0.0592 |
| residence-17-de | passed | 5 | 5/5 | 0 | 100 | 71 | 100 | ok | de | 100 | 0.0921 |
| residence-17-fr | passed | 4 | 4/4 | 0 | 100 | 86 | 50 | ok | fr | 69 | 0.0635 |
| residence-17-it | passed | 3 | 3/3 | 0 | 100 | 83 | 50 | ok | it | 69 | 0.0666 |
| social-03-de | passed | 5 | 5/5 | 0 | 100 | 88 | 100 | ok | de | 31 | 0.0365 |
| social-03-fr | passed | 5 | 5/5 | 0 | 100 | 86 | 100 | ok | fr | 32 | 0.0352 |
| social-03-it | passed | 5 | 5/5 | 0 | 100 | 78 | 100 | ok | it | 32 | 0.0429 |
| social-07-de | passed | 3 | 3/3 | 0 | 100 | 90 | 100 | ok | de | 30 | 0.0267 |
| social-07-fr | passed | 3 | 3/3 | 0 | 100 | 90 | 100 | ok | fr | 40 | 0.0406 |
| social-07-it | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 36 | 0.0365 |
| tax-10-de | passed | 5 | 5/5 | 0 | 100 | 93 | 100 | ok | de | 38 | 0.0430 |
| tax-10-fr | passed | 5 | 5/5 | 0 | 50 | 71 | 100 | ok | fr | 52 | 0.0578 |
| tax-10-it | passed | 6 | 6/6 | 0 | 100 | 64 | 100 | ok | it | 84 | 0.0836 |
| work-04-de | passed | 4 | 4/4 | 0 | 100 | 86 | 100 | ok | de | 21 | 0.0219 |
| work-04-fr | passed | 4 | 4/4 | 0 | 100 | 86 | 100 | ok | fr | 49 | 0.0266 |
| work-04-it | passed | 3 | 3/3 | 0 | 100 | 83 | 100 | ok | it | 19 | 0.0237 |
| work-11-de | passed | 6 | 6/6 | 0 | 100 | 86 | 100 | ok | de | 31 | 0.0317 |
| work-11-fr | passed | 6 | 6/6 | 0 | 100 | 86 | 100 | ok | fr | 35 | 0.0365 |
| work-11-it | passed | 6 | 6/6 | 0 | 100 | 79 | 100 | ok | it | 69 | 0.0575 |
| work-19-de | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 26 | 0.0229 |
| work-19-fr | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 26 | 0.0255 |
| work-19-it | passed | 4 | 4/4 | 0 | 100 | 86 | 100 | ok | it | 27 | 0.0226 |
| housing-08-de | passed | 6 | 6/6 | 0 | 100 | 86 | 100 | ok | de | 34 | 0.0316 |
| housing-08-en | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 38 | 0.0329 |
| housing-08-it | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | it | 34 | 0.0359 |
| housing-16-de | passed | 3 | 3/3 | 0 | 100 | 56 | 100 | ok | de | 23 | 0.0206 |
| housing-16-en | passed | 3 | 3/3 | 0 | 100 | 70 | 50 | ok | en | 44 | 0.0363 |
| housing-16-it | passed | 5 | 5/5 | 0 | 100 | 83 | 100 | ok | it | 32 | 0.0298 |
| mobility-04-de | passed | 5 | 5/5 | 0 | 100 | 86 | 100 | ok | de | 43 | 0.0482 |
| mobility-04-en | passed | 5 | 5/5 | 0 | 100 | 86 | 100 | ok | en | 46 | 0.0418 |
| mobility-04-it | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 38 | 0.0367 |
| residence-03-de | passed_after_retry | 7 | 7/7 | 0 | 100 | 100 | 100 | ok | de | 132 | 0.1165 |
| residence-03-en | passed_after_retry | 7 | 7/7 | 0 | 100 | 95 | 100 | ok | en | 159 | 0.1224 |
| residence-03-it | passed_after_retry | 0 | 0/0 | 0 | 0 | 0 | 0 | **no** | it | 93 | 0.1028 |
| residence-09-de | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 49 | 0.0510 |
| residence-09-en | passed | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | en | 98 | 0.0729 |
| residence-09-it | passed | 4 | 4/4 | 0 | 100 | 75 | 100 | ok | it | 56 | 0.0582 |
| residence-20-de | passed | 4 | 4/4 | 0 | 100 | 70 | 100 | ok | de | 52 | 0.0514 |
| residence-20-en | passed | 5 | 5/5 | 0 | 100 | 80 | 100 | ok | en | 40 | 0.0433 |
| residence-20-it | passed | 5 | 5/5 | 0 | 100 | 83 | 100 | ok | it | 50 | 0.0540 |
| social-04-de | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 40 | 0.0355 |
| social-04-en | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 43 | 0.0343 |
| social-04-it | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | it | 70 | 0.0270 |
| tax-09-de | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 48 | 0.0511 |
| tax-09-en | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 64 | 0.0710 |
| tax-09-it | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 53 | 0.0567 |
| work-02-de | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 18 | 0.0188 |
| work-02-en | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | en | 20 | 0.0202 |
| work-02-it | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 15 | 0.0187 |
| work-06-de | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 37 | 0.0363 |
| work-06-en | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | en | 30 | 0.0324 |
| work-06-it | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 38 | 0.0339 |
| housing-17-de | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 39 | 0.0408 |
| housing-17-en | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 53 | 0.0436 |
| housing-17-fr | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 35 | 0.0300 |
| housing-21-de | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 30 | 0.0269 |
| housing-21-en | passed | 3 | 3/3 | 0 | 100 | 80 | 100 | ok | en | 43 | 0.0410 |
| housing-21-fr | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 24 | 0.0251 |
| mobility-05-de | passed | 6 | 6/6 | 0 | 100 | 100 | 100 | ok | de | 70 | 0.0614 |
| mobility-05-en | passed | 4 | 4/4 | 0 | 100 | 94 | 100 | ok | en | 55 | 0.0528 |
| mobility-05-fr | passed | 5 | 5/5 | 0 | 100 | 83 | 100 | ok | fr | 50 | 0.0514 |
| residence-04-de | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 32 | 0.0319 |
| residence-04-en | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | en | 38 | 0.0369 |
| residence-04-fr | passed | 4 | 4/4 | 0 | 100 | 93 | 100 | ok | fr | 25 | 0.0302 |
| residence-11-de | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 24 | 0.0285 |
| residence-11-en | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | en | 23 | 0.0260 |
| residence-11-fr | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 36 | 0.0450 |
| residence-15-de | degraded | 5 | 3/5 | 0 | 0 | 50 | 100 | ok | de | 181 | 0.2443 |
| residence-15-en | degraded | 6 | 3/6 | 0 | 0 | 25 | 100 | ok | en | 191 | 0.2147 |
| residence-15-fr | degraded | 4 | 2/4 | 0 | 0 | 40 | 100 | ok | fr | 197 | 0.1611 |
| residence-19-de | passed | 5 | 5/5 | 0 | 100 | 89 | 100 | ok | de | 27 | 0.0333 |
| residence-19-en | passed | 9 | 9/9 | 0 | 100 | 89 | 100 | ok | en | 143 | 0.0577 |
| residence-19-fr | passed | 9 | 9/9 | 0 | 100 | 80 | 100 | ok | fr | 43 | 0.0425 |
| social-02-de | passed | 6 | 6/6 | 0 | 100 | 92 | 100 | ok | de | 135 | 0.0830 |
| social-02-en | passed | 6 | 6/6 | 0 | 100 | 81 | 100 | ok | en | 41 | 0.0466 |
| social-02-fr | passed | 6 | 6/6 | 0 | 100 | 67 | 100 | ok | fr | 77 | 0.0646 |
| work-10-de | passed | 3 | 3/3 | 0 | 100 | 83 | 100 | ok | de | 16 | 0.0139 |
| work-10-en | passed | 3 | 3/3 | 0 | 100 | 83 | 100 | ok | en | 17 | 0.0171 |
| work-10-fr | passed | 3 | 3/3 | 0 | 100 | 88 | 100 | ok | fr | 18 | 0.0166 |
| work-14-de | passed | 3 | 3/3 | 0 | 100 | 62 | 100 | ok | de | 39 | 0.0372 |
| work-14-en | passed | 3 | 3/3 | 0 | 100 | 93 | 100 | ok | en | 41 | 0.0328 |
| work-14-fr | passed | 3 | 3/3 | 0 | 100 | 50 | 100 | ok | fr | 34 | 0.0337 |

## Findings per case

- `housing-02-en`: unsupported: Cantons may enact supplementary provisions regarding rental deposits.
- `housing-02-fr`: unsupported: Les cantons peuvent édicter des règles complémentaires relatives aux sûretés (note cantonale).
- `housing-02-it`: unsupported: Il locatore non può trattenere il denaro sul proprio conto personale né richiedere più di tre mesi di pigione come deposito cauzionale.; unsupported: I Cantoni possono emanare disposizioni complementari in materia di garanzie.
- `housing-07-en`: unsupported: An ordinary e-mail does not satisfy the statutory written form requirement.; unsupported: Because a void notice has no legal effect, the tenancy continues as though the termination had not been issued.
- `housing-07-it`: unsupported: Un messaggio di posta elettronica ordinario non rispetta il requisito della forma scritta previsto dalla legge
- `housing-19-en`: missing fact: the same applies to registered partnerships
- `housing-19-fr`: unsupported: L'organisation judiciaire et la désignation du tribunal ou de l'autorité compétente pour statuer en cas de refus du conjoint relèvent du droit de chaque canton.; missing fact: the same applies to registered partnerships
- `housing-19-it`: unsupported: La regola del consenso si applica anche se il contratto di locazione è stato firmato da uno solo dei coniugi.; unsupported: La designazione del giudice competente e delle autorità di conciliazione in materia di locazione è disciplinata dall'ordinamento giudiziario di ciascun Cantone.; missing fact: the same applies to registered partnerships
- `residence-02-en`: unsupported: A bilateral treaty or reciprocal practice between Switzerland and the United States may provide for settlement after five years.
- `residence-02-it`: unsupported: Per i cittadini statunitensi potrebbero applicarsi accordi o prassi amministrative specifiche sullo stabilimento dopo cinque anni.
- `residence-13-en`: unsupported: Naturalisation applications are processed primarily by the cantonal migration or naturalisation authority and the communal administration.; unsupported: Cantons may require higher language levels (such as B2 oral or B1 written) or mandate specific language certificates.
- `residence-13-fr`: unsupported: Les cantons et les communes appliquent les critères d'intégration et peuvent fixer des exigences plus strictes ou préciser les certificats linguistiques admis.
- `residence-13-it`: unsupported: I requisiti federali rappresentano la soglia minima e diversi Cantoni richiedono livelli linguistici superiori (come B2 orale o B1 scritto) o attestati specifici.
- `work-08-en`: unsupported: Covering all of Switzerland is excessive unless the employer's genuine business activities and potential for harm justify such territorial reach.
- `work-08-fr`: unsupported: Une clause de non-concurrence prévoyant une durée de cinq ans pour toute la Suisse est présumée excessive au regard du droit fédéral, mais elle n'est pas obligatoirement nulle dans son intégralité.; unsupported: Une interdiction couvrant l'ensemble de la Suisse n'est justifiée que si le rayon d'activité effectif de l'employeur s'étend à tout le pays.
- `work-08-it`: unsupported: Una clausola di divieto di concorrenza di cinque anni estesa a tutta la Svizzera è, nella maggior parte dei casi, eccessiva.; unsupported: L'estensione geografica all'intero territorio svizzero deve corrispondere all'effettivo raggio di attività dell'azienda.; missing fact: a non-compete clause must be agreed in writing and is binding only if the job gave insight into the customer base or trade or business secrets whose use could cause the employer significant harm
- `work-12-it`: unsupported: La legge federale non stabilisce una regola automatica per i ritardi e la valutazione dipende dalla gravità oggettiva delle circostanze.
- `work-23-en`: unsupported: The law does not define fixed numbers of weeks for subsequent years, and in practice courts apply regional scales such as the Bernese, Zurich, or Basel scales.; unsupported: An equivalent alternative scheme includes daily sickness benefits insurance covering 80% of salary for up to 720 or 730 days.
- `work-23-it`: unsupported: Nella prassi svizzera i tribunali fanno spesso riferimento a tabelle come la scala bernese, zurighese o basilese, le quali tuttavia non figurano nel testo della legge federale.; unsupported: In molti contratti è prevista un'assicurazione d'indennità giornaliera per perdita di guadagno in caso di malattia (solitamente pari all'80% dello stipendio fino a 720 o 730 giorni).
- `general-01-de`: unsupported: Niemand kann im Voraus auf das Auskunftsrecht verzichten.; unsupported: Die Auskunft darf verweigert, eingeschränkt oder aufgeschoben werden, wenn eigene überwiegende Interessen des Unternehmens dies erfordern und es die Daten nicht an Dritte weitergibt.; missing fact: the answer must include at least the controller's identity and contact details, the data itself, the purpose, the retention period, and where relevant the source and the recipients
- `general-01-fr`: missing fact: the information must be given free of charge, as a rule within 30 days, and the right cannot be waived in advance
- `general-01-it`: missing fact: the answer must include at least the controller's identity and contact details, the data itself, the purpose, the retention period, and where relevant the source and the recipients; missing fact: the information must be given free of charge, as a rule within 30 days, and the right cannot be waived in advance
- `housing-20-de`: unsupported: Die ortsüblichen Kündigungstermine sind kantonal bzw. lokal unterschiedlich geregelt.
- `housing-20-fr`: unsupported: Les termes de congé fixés par l'usage local varient d'un canton ou d'un district à l'autre.
- `residence-17-de`: unsupported: Nach behördlicher Praxis muss die eheliche Gemeinschaft in der Regel mindestens drei Jahre in der Schweiz gelebt worden sein.; unsupported: Bei Bürgerinnen oder Bürgern eines EU/EFTA-Staates, die eine Stelle ausüben, leitet sich das Aufenthaltsrecht primär direkt aus dem Freizügigkeitsabkommen ab.
- `residence-17-fr`: unsupported: La pratique exige en principe que la vie commune d'au moins trois ans ait été menée en Suisse, bien que le texte légal ne le précise pas expressément.; missing fact: or if important personal reasons require a further stay in Switzerland, such as domestic violence or strongly endangered reintegration in the home country
- `residence-17-it`: unsupported: Secondo la prassi applicativa, si richiede di regola che la convivenza coniugale sia stata vissuta effettivamente in Svizzera per tale durata di almeno tre anni.; missing fact: or if important personal reasons require a further stay in Switzerland, such as domestic violence or strongly endangered reintegration in the home country
- `social-03-de`: unsupported: Die Kantone überwachen die Einhaltung der Versicherungspflicht und fordern den Versicherungsnachweis an.
- `social-03-fr`: unsupported: Le contrôle de l'obligation de s'assurer et la procédure d'affiliation d'office relèvent de la compétence des cantons.
- `social-03-it`: unsupported: Eventuali spese mediche sostenute prima della data di affiliazione tardiva non sono coperte dall'assicurazione.; unsupported: Il controllo dell'obbligo d'assicurazione e l'eventuale affiliazione d'ufficio sono di competenza dell'autorità cantonale designata.
- `tax-10-fr`: unsupported: Une personne imposée à la source doit remplir une déclaration d'impôt si elle dispose d'autres revenus ou éléments de fortune non soumis à la source.; unsupported: L'envoi des formules, les délais de dépôt de la déclaration d'impôt et les barèmes fiscaux relèvent de la compétence de l'autorité fiscale cantonale ou communale.
- `tax-10-it`: unsupported: La gestione e la riscossione dell'imposta federale diretta e delle imposte cantonali e comunali sono delegate alle autorità fiscali cantonali o comunali, che determinano le scadenze ordinarie di presentazione, i moduli e le modalità per richiedere una proroga del termine.
- `work-04-de`: unsupported: Ein Einzelarbeitsvertrag oder ein Gesamtarbeitsvertrag (GAV) darf dem Arbeitnehmer mehr Ferien als das gesetzliche Minimum gewähren.
- `work-04-fr`: unsupported: Le contrat individuel de travail ou une convention collective de travail peut prévoir un nombre de semaines de vacances plus élevé que le minimum légal.
- `work-04-it`: unsupported: Il contratto individuale d'impiego o un contratto collettivo di lavoro (CCL) possono prevedere una durata maggiore di vacanze, ma non una durata inferiore.
- `work-11-de`: unsupported: Eine missbräuchliche Kündigung beendet das Arbeitsverhältnis dennoch.
- `work-11-fr`: unsupported: En droit suisse, un congé abusif reste valable et met fin au contrat de travail, mais ouvre droit à une indemnité financière.
- `work-11-it`: unsupported: L'azione giudiziaria per controversie di lavoro deve essere preceduta da un'istanza all'autorità di conciliazione cantonale competente.
- `work-19-it`: unsupported: Il suo rapporto di lavoro terminerà il 31 agosto.
- `housing-08-de`: unsupported: Welche Termine als ortsüblich gelten, richtet sich nach dem kantonalen bzw. regionalen Ortsgebrauch.
- `housing-16-de`: unsupported: Verpasst man die Frist von 30 Tagen nach Übernahme der Sache, gilt der vereinbarte Mietzins.; unsupported: Zuständig ist die Schlichtungsbehörde für Mietsachen am Ort der Mietsache.; unsupported: Ob am Wohnort eine Pflicht zur Mitteilung des Anfangsmietzinses mit amtlichem Formular gilt, bestimmt das jeweilige kantonale Recht.
- `housing-16-en`: unsupported: Cantons specify whether an official initial rent notification form is mandatory in their territory.; missing fact: this requires that the tenant was forced to sign because of a personal or family emergency or the local housing market, or that the landlord significantly increased the rent compared with the previous rent
- `housing-16-it`: unsupported: Spetta ai singoli Cantoni stabilire se sussiste penuria di alloggi e se è obbligatorio l'uso del modulo ufficiale cantonale alla conclusione del contratto.
- `mobility-04-de`: unsupported: Wenn man in der Schweiz nach nicht bestandener Kontrollfahrt wieder fahren möchte, muss man den schweizerischen Führerausweis auf dem regulären Weg von Grund auf erwerben (Lernfahrausweis, Theorieprüfung und praktische Führerprüfung).
- `mobility-04-en`: unsupported: To drive in Switzerland again after failing the control drive, you cannot use a simplified exchange procedure and must go through the standard Swiss licensing process from the beginning (applying for a learner's permit and passing theory and practical exams).
- `residence-03-it`: behaviour: The assistant asked a clarifying question instead of answering directly with citations for an answerable question.; unsupported: Se si applica l'Accordo sulla libera circolazione per i cittadini dell'UE/AELS non vi sono termini perentori di legge per il ricongiungimento familiare.; unsupported: Per i cittadini di Paesi terzi la Legge federale sugli stranieri e la loro integrazione stabilisce condizioni d'integrazione e scadenze temporali rigide, differenziate per la fascia d'età dei figli.; missing fact: the spouse and unmarried children under 18 of a C permit holder are entitled to a residence permit if conditions are met (living together, suitable housing, no social assistance); missing fact: family reunification must be requested within five years; missing fact: children over 12 must be brought within twelve months
- `residence-20-de`: unsupported: Für Staatsangehörige bestimmter Länder, namentlich vieler EU/EFTA-Staaten, bestehen teils bilaterale Niederlassungsvereinbarungen mit kürzeren Fristen von in der Regel 5 Jahren.
- `housing-21-en`: unsupported: Requests for lease extensions must be submitted to the local conciliation authority for tenancy matters of the district or canton where the property is located.
- `mobility-05-fr`: unsupported: La durée minimale passe à au moins 12 mois (voire une durée indéterminée) en cas de récidives plus lourdes.
- `residence-15-de`: unsupported: Bei einem unbefristeten Arbeitsvertrag (mindestens ein Jahr) beträgt die Gültigkeitsdauer der Aufenthaltsbewilligung fünf Jahre ab Erteilung und wird grundsätzlich automatisch um mindestens fünf Jahre verlängert.; unsupported: Bei einem unbefristeten Arbeitsvertrag wird die Grenzgängerbescheinigung für eine Gültigkeitsdauer von mindestens fünf Jahren ausgestellt und verlängert.; verifier: [3] non-existent paragraph removed; verifier: [4] non-existent paragraph removed
- `residence-15-en`: unsupported: Because your employment contract has an indefinite duration (at least one year), the Permit B is valid for 5 years.; unsupported: The Permit B is automatically renewed for further 5-year periods as long as you remain employed.; unsupported: For an employment contract of at least one year or permanent duration, Permit G is valid for 5 years and renewable.; unsupported: For the issue of the residence permit, the authority may only require you to present your valid travel document and a certificate of employment or written declaration of engagement from your employer.; unsupported: If residing in Switzerland, registration is handled at the municipal residents' registration office of your commune of residence, which forwards the file to the cantonal migration office; for cross-border commuters, application is typically submitted to the cantonal migration office at the place of work.; verifier: [1] non-existent paragraph removed; verifier: [4] non-existent paragraph removed; verifier: [6] non-existent paragraph removed
- `residence-15-fr`: unsupported: La durée de validité du permis B est de cinq ans au moins à compter de sa délivrance, et elle est prolongée automatiquement pour au moins cinq ans.; unsupported: L'autorisation frontalière UE/AELE est délivrée pour une durée de cinq ans au moins.; verifier: [1] non-existent paragraph removed; verifier: [4] non-existent paragraph removed
- `residence-19-fr`: unsupported: L'ouverture d'une procédure de révocation et la décision relèvent de l'autorité cantonale de migration.
- `social-02-en`: unsupported: Any unused leave days are forfeited once the six-month deadline expires.
- `social-02-fr`: unsupported: Les jours non pris à l'échéance du délai de six mois sont perdus.; unsupported: Pour une activité à temps plein (semaine de 5 jours ouvrés), cela représente 10 jours de congé.; unsupported: Le versement de l'indemnité est soumis à des conditions d'assurance et de cotisation, et les indépendants y ont également droit en cas d'interruption d'activité.
- `work-14-de`: unsupported: Der Ferienanspruch dient dem Gesundheitsschutz und der tatsächlichen Erholung.; unsupported: Selbst bei gegenseitigem Einverständnis ist ein Verzicht auf den Bezug von Ferien zugunsten einer Auszahlung während der Anstellung unzulässig.; unsupported: Endet das Arbeitsverhältnis und können verbleibende Ferientage bis zum Austrittstermin nicht mehr tatsächlich bezogen werden, ist der restliche Feriensaldo bei Austritt finanziell abzugelten.
- `work-14-fr`: unsupported: L'interdiction de remplacer les vacances par des prestations en argent ou d'autres avantages a pour but de garantir le repos du travailleur.; unsupported: En cas de travail à temps partiel irrégulier, la jurisprudence admet sous strictes conditions l'intégration d'une indemnité de vacances dans le salaire courant.
