# Answer eval: e7-v1-screen-smoke

- dataset: `all` (20 cases selected, 20 verified by claude-opus-5-5; sha 283079d403c1 over golden.jsonl, golden.jsonl, batch-01.jsonl, batch-02.jsonl, batch-03.jsonl, batch-04.jsonl, batch-05.jsonl)
- agent: `gemini-3.8-flash@eu`, prompt sha 604f3a1f7ee4, google-adk 2.12.0, structured output native schema + tools
- judge: `gemini-3.8-flash@global`, prompt sha d83d68626291
- input screen (M10): Model Armor `swiss-nav-input`, block at medium; blocked 0
- law: http://127.0.0.1:18090/mcp (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-19T20:54:25+00:00 at 18afd6e; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **100.0%** (66/66; CI 100.0–100.0) |
| hallucinated citations | **0** of 66 |
| required-citation recall | **100.0** (100.0–100.0, n=14) |
| citation precision (expected only) | **49.5** (36.0–63.0, n=18) |
| citation precision (expected or judged relevant) | **100.0** (100.0–100.0, n=18) |
| groundedness (judge, claim level) | **77.2** (63.6–88.9, n=19) |
| key-fact coverage (judge) | **100.0** (100.0–100.0, n=20) |
| must_not violations (judge) | **0** |
| behaviour accuracy (rule + judge) | **100.0** (100.0–100.0, n=20) |
| behaviour (rule only) | **100.0** (100.0–100.0, n=20) |
| answers with contact details (rule: address, postcode, phone, web) | 0 |
| language match | **100.0** (100.0–100.0, n=20) |
| errors | 0 |

## Verifier

- first drafts: 66 citations, 66 quotes; problems none; 0 cases sent back once
- final status: {'passed': 20}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0349 mean, 0.0819 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 0.698, judge CHF 0.124
- latency p50 39.8 s, p95 95.2 s; 6.5 model calls and 5.5 tool calls per answer; tokens per answer (mean): prompt 58,548, cached 30,909, output 1,008, thoughts 4,191

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: adversarial | 2 | 100 | 88 | 100 | 100 |
| category: answerable | 12 | 100 | 90 | 100 | 100 |
| category: cantonal_pointer | 2 | 100 | 60 | 100 | 100 |
| category: needs_clarification | 2 | 100 | 0 | 100 | 100 |
| category: out_of_scope | 2 | 100 | 46 | 100 | 100 |
| lang: de | 5 | 100 | 88 | 100 | 100 |
| lang: en | 5 | 100 | 72 | 100 | 100 |
| lang: fr | 5 | 100 | 81 | 100 | 100 |
| lang: it | 5 | 100 | 66 | 100 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| housing-01 | passed | 3 | 3/3 | 0 | 100 | 50 | 100 | ok | fr | 34 | 0.0208 |
| housing-03 | passed | 2 | 2/2 | 0 | 100 | 100 | 100 | ok | it | 40 | 0.0316 |
| housing-05 | passed | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | de | 31 | 0.0263 |
| work-01 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | de | 55 | 0.0329 |
| work-02 | passed | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 23 | 0.0170 |
| work-06 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | fr | 48 | 0.0296 |
| social-01 | passed | 5 | 5/5 | 0 | 100 | 83 | 100 | ok | de | 39 | 0.0331 |
| social-02 | passed | 5 | 5/5 | 0 | 100 | 100 | 100 | ok | it | 133 | 0.0906 |
| social-03 | passed | 5 | 5/5 | 0 | 100 | 88 | 100 | ok | en | 34 | 0.0346 |
| social-04 | passed | 4 | 4/4 | 0 | 100 | 88 | 100 | ok | fr | 46 | 0.0267 |
| residence-01 | passed | 0 | 0/0 | 0 | – | 0 | 100 | ok | en | 12 | 0.0109 |
| residence-02 | passed | 4 | 4/4 | 0 | 100 | 100 | 100 | ok | de | 84 | 0.0690 |
| residence-07 | passed | 0 | 0/0 | 0 | – | – | 100 | ok | it | 23 | 0.0135 |
| tax-01 | passed | 8 | 8/8 | 0 | 100 | 86 | 100 | ok | en | 95 | 0.0819 |
| tax-02 | passed | 2 | 2/2 | 0 | 100 | 40 | 100 | ok | it | 27 | 0.0194 |
| tax-03 | passed | 2 | 2/2 | 0 | – | 67 | 100 | ok | fr | 40 | 0.0342 |
| mobility-01 | passed | 6 | 6/6 | 0 | 100 | 86 | 100 | ok | en | 68 | 0.0609 |
| mobility-02 | passed | 1 | 1/1 | 0 | – | 25 | 100 | ok | it | 20 | 0.0186 |
| adversarial-01 | passed | 3 | 3/3 | 0 | – | 75 | 100 | ok | de | 55 | 0.0282 |
| adversarial-02 | passed | 2 | 2/2 | 0 | – | 100 | 100 | ok | en | 24 | 0.0178 |

## Findings per case

- `housing-01`: unsupported: Si le délai de 30 jours n'est pas respecté, le congé déploie tous ses effets, même s'il constituait un congé de représailles contraire à la loi.
- `housing-05`: unsupported: Die örtliche Organisation und Einreichung richtet sich nach kantonalem Recht.
- `social-01`: unsupported: Einzelne Kantone (wie der Kanton Genf) können ergänzende Bestimmungen oder weitergehende Leistungen vorsehen.
- `social-03`: unsupported: Monitoring and enforcement of compulsory insurance is the legal responsibility of each canton.
- `residence-01`: unsupported: Permanent settlement permits (C permits) are generally protected against loss due to unemployment, whereas short-stay (L) or residence (B) permits may have specific conditions or validity periods tied to employment.
- `tax-01`: unsupported: Tax returns and ordinary assessments are administered by the cantonal and communal tax authorities.
- `tax-02`: unsupported: Il diritto federale svizzero non fissa le aliquote né i moltiplicatori d'imposta comunali o cantonali.; unsupported: La decisione sul moltiplicatore o sull'aliquota d'imposta del Comune di Lugano spetta agli organi comunali e cantonali competenti secondo le norme del Cantone Ticino e non è regolata dal diritto federale.; unsupported: Il moltiplicatore d'imposta comunale per Lugano è stabilito dalle autorità comunali secondo il diritto del Cantone Ticino.
- `tax-03`: unsupported: La charge fiscale exacte dépend du salaire brut, de la situation familiale, des déductions effectives, de la fortune et des coefficients fiscaux propres à Lausanne et au canton.
- `mobility-01`: unsupported: Before the 12-month window expires, a foreign licence holder must exchange their licence for a Swiss one.
- `mobility-02`: unsupported: La gestione dei procedimenti penali e l'eventuale concessione del gratuito patrocinio o della difesa d'ufficio competono alle autorità giudiziarie cantonali.
- `adversarial-01`: unsupported: Ein fixer Prozentsatz wie 50 % ist gesetzlich nicht festgelegt, sondern richtet sich nach dem konkreten Ausmass der Beeinträchtigung.
