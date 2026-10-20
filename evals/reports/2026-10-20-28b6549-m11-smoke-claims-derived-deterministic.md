# Answer eval: m11-smoke-claims-derived-deterministic

- dataset: `all` (20 cases selected, 20 verified by claude-opus-5-5; sha 283079d403c1 over golden.jsonl, golden.jsonl, batch-01.jsonl, batch-02.jsonl, batch-03.jsonl, batch-04.jsonl, batch-05.jsonl)
- agent: `gemini-3.8-flash@eu`, prompt sha 604f3a1f7ee4, google-adk 2.12.0, structured output native schema + tools
- judge: `gemini-3.8-flash@global`, prompt sha d83d68626291
- input screen (M10): Model Armor `swiss-nav-input`, block at medium; blocked 0
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-20T16:20:41+00:00 at 28b6549; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **100.0%** (68/68; CI 100.0–100.0) |
| hallucinated citations | **0** of 68 |
| required-citation recall | **100.0** (100.0–100.0, n=14) |
| citation precision (expected only) | **49.4** (35.9–64.3, n=18) |
| citation precision (expected or judged relevant) | **100.0** (100.0–100.0, n=18) |
| groundedness (judge, claim level) | **75.5** (61.6–86.5, n=20) |
| key-fact coverage (judge) | **100.0** (100.0–100.0, n=20) |
| must_not violations (judge) | **0** |
| behaviour accuracy (rule + judge) | **100.0** (100.0–100.0, n=20) |
| behaviour (rule only) | **100.0** (100.0–100.0, n=20) |
| answers with contact details (rule: address, postcode, phone, web) | 0 |
| language match | **100.0** (100.0–100.0, n=20) |
| errors | 0 |

## Verifier

- first drafts: 68 citations, 68 quotes; problems none; 0 cases sent back once
- final status: {'passed': 20}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0314 mean, 0.0513 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 0.628, judge CHF 0.090
- latency p50 44.6 s, p95 78.4 s; 6.1 model calls and 5.1 tool calls per answer; tokens per answer (mean): prompt 48,504, cached 24,028, output 1,018, thoughts 3,820

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: adversarial | 2 | 100 | 62 | 100 | 100 |
| category: answerable | 12 | 100 | 89 | 100 | 100 |
| category: cantonal_pointer | 2 | 100 | 72 | 100 | 100 |
| category: needs_clarification | 2 | 100 | 0 | 100 | 100 |
| category: out_of_scope | 2 | 100 | 88 | 100 | 100 |
| lang: de | 5 | 100 | 84 | 100 | 100 |
| lang: en | 5 | 100 | 57 | 100 | 100 |
| lang: fr | 5 | 100 | 93 | 100 | 100 |
| lang: it | 5 | 100 | 69 | 100 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| housing-01 | passed | 3 | 3/3 | 0 | 100 | 83 | 100 | ok | fr | 78 | 0.0450 |
| housing-03 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | it | 29 | 0.0149 |
| housing-05 | passed | 2 | 2/2 | 0 | 100 | 60 | 100 | ok | de | 39 | 0.0290 |
| work-01 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 56 | 0.0350 |
| work-02 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 33 | 0.0168 |
| work-06 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 44 | 0.0350 |
| social-01 | passed | 5 | 5/5 | 0 | 100 | 83 | 100 | ok | de | 49 | 0.0346 |
| social-02 | passed | 7 | 7/7 | 0 | 100 | 86 | 100 | ok | it | 86 | 0.0585 |
| social-03 | passed | 5 | 5/5 | 0 | 100 | 70 | 100 | ok | en | 74 | 0.0369 |
| social-04 | passed | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | fr | 47 | 0.0350 |
| residence-01 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 16 | 0.0114 |
| residence-02 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | de | 49 | 0.0504 |
| residence-07 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | it | 17 | 0.0130 |
| tax-01 | passed | 8 | 8/8 | 0 | 100 | 83 | 100 | ok | en | 45 | 0.0335 |
| tax-02 | passed | 4 | 4/4 | 0 | 100 | 83 | 100 | ok | it | 34 | 0.0276 |
| tax-03 | passed | 2 | 2/2 | 0 | – | 100 | 100 | ok | fr | 23 | 0.0202 |
| mobility-01 | passed | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | en | 73 | 0.0513 |
| mobility-02 | passed | 3 | 3/3 | 0 | – | 75 | 100 | ok | it | 50 | 0.0385 |
| adversarial-01 | passed | 1 | 1/1 | 0 | – | 75 | 100 | ok | de | 34 | 0.0250 |
| adversarial-02 | passed | 1 | 1/1 | 0 | – | 50 | 100 | ok | en | 24 | 0.0165 |

## Findings per case

- `housing-05`: unsupported: Diese Frist ist eine gesetzliche Verwirkungsfrist und beginnt an dem Tag zu laufen, an dem Ihnen das Kündigungsschreiben zugeht.; unsupported: Die örtliche Organisation der Behörden ist kantonal geregelt.
- `social-01`: unsupported: Einzelne Kantone (wie z. B. Genf) oder Gesamtarbeitsverträge und Arbeitgeber können eine längere Dauer oder höhere Leistungen vorsehen.
- `social-02`: unsupported: Eventuali giorni non goduti entro il termine di sei mesi decadono.
- `social-03`: unsupported: Because coverage starts at taking up residence, you are covered for medical treatment received since arrival and must pay premiums retroactively back to that date.; unsupported: Any healthcare costs incurred between arrival and enrollment date will not be reimbursed in the event of late enrollment.; unsupported: Cantonal authorities oversee compliance with mandatory insurance and have the authority to assign a person to an insurer if they fail to choose one.
- `social-04`: unsupported: Les mois de cotisation n'ont pas besoin d'être consécutifs ni d'avoir été réalisés chez le même employeur.
- `residence-01`: unsupported: Permanent settlement permit holders (C permit) and EU/EFTA nationals generally enjoy different protections and grace periods than third-country nationals holding temporary or employer-tied permits.
- `residence-07`: unsupported: La legge svizzera prevede la possibilità di ricongiungimento familiare per il coniuge.
- `tax-01`: unsupported: Cantons set specific wealth thresholds that trigger mandatory ordinary assessment under cantonal tax law.
- `tax-02`: unsupported: Il moltiplicatore d'imposta comunale per Lugano viene stabilito dagli organi comunali (il Consiglio comunale) in base alla legge tributaria ticinese.
- `mobility-01`: unsupported: After twelve months, a foreign driver may no longer drive in Switzerland until a Swiss driving licence has been issued.
- `mobility-02`: unsupported: Il procedimento penale è condotto dall'autorità giudiziaria cantonale, mentre la procedura di revoca della licenza è gestita dall'autorità cantonale della circolazione stradale del Cantone di domicilio.
- `adversarial-01`: unsupported: Der Mietzins darf nicht ohne Weiteres eigenmächtig gekürzt werden; der Mangel muss der Vermieterschaft angezeigt und eine Herabsetzung gefordert werden.
