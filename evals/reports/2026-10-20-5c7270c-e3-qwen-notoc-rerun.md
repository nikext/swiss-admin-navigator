# Answer eval: e3-qwen-notoc-rerun

- dataset: `golden` (16 cases selected, 16 verified by claude-opus-5-5; sha 283079d403c1 over golden.jsonl)
- agent: `qwen/qwen3-235b-a22b-instruct-2507-maas@global`, prompt sha 604f3a1f7ee4, google-adk 2.12.0, structured output set_model_response tool
- judge: `gemini-3.8-flash@eu`, prompt sha d83d68626291
- input screen (M10): Model Armor `swiss-nav-input`, block at medium; blocked 0
- law: local (started by the harness) (index as_of 2026-10-15, built from c756c89)
- run: 2026-10-20T05:12:57+00:00 at 5c7270c; CIs are 95% percentile bootstraps over cases (2,000 resamples, seed 0)

## Headline

| metric | value |
|---|---|
| quote fidelity (final answers) | **100.0%** (40/40; CI 100.0–100.0) |
| hallucinated citations | **0** of 40 |
| required-citation recall | **46.7** (23.3–70.0, n=15) |
| citation precision (expected only) | **40.0** (22.2–60.0, n=15) |
| citation precision (expected or judged relevant) | **90.0** (73.3–100.0, n=15) |
| groundedness (judge, claim level) | **43.9** (29.0–59.3, n=16) |
| key-fact coverage (judge) | **54.2** (31.2–77.1, n=16) |
| must_not violations (judge) | **3** |
| behaviour accuracy (rule + judge) | **62.5** (37.5–87.5, n=16) |
| behaviour (rule only) | **81.2** (62.5–100.0, n=16) |
| answers with contact details (rule: address, postcode, phone, web) | 0 |
| language match | **100.0** (100.0–100.0, n=16) |
| errors | 0 |

## Verifier

- first drafts: 22 citations, 22 quotes; problems {'parse': 6, 'marker': 1, 'letter': 1, 'quote': 1}; 9 cases sent back once
- final status: {'degraded': 4, 'passed_after_retry': 5, 'passed': 7}; citations dropped: 0; not in force: 0; unchecked: 0

## Cost and latency (agent only)

- per answer: CHF 0.0817 mean, 0.2768 p95 (USD→CHF 0.82, prices as of 2026-10-15); run: agent CHF 1.307, judge CHF 0.101
- latency p50 19.7 s, p95 85.3 s; 17.1 model calls and 15.7 tool calls per answer; tokens per answer (mean): prompt 446,436, cached 349,391, output 1,571, thoughts 0

## By category and language

| group | n | behaviour | groundedness | key facts | language |
|---|---|---|---|---|---|
| category: adversarial | 2 | 100 | 27 | 100 | 100 |
| category: answerable | 11 | 64 | 44 | 45 | 100 |
| category: cantonal_pointer | 2 | 50 | 62 | 33 | 100 |
| category: needs_clarification | 1 | 0 | 42 | 100 | 100 |
| lang: de | 3 | 67 | 62 | 33 | 100 |
| lang: en | 8 | 50 | 21 | 50 | 100 |
| lang: fr | 2 | 50 | 67 | 50 | 100 |
| lang: it | 3 | 100 | 70 | 89 | 100 |

## Cases

| id | status | cites | verbatim | halluc. | req. recall | grounded | facts | behaviour | lang | s | CHF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| tax-01 | degraded | 3 | 3/3 | 0 | 50 | 50 | 67 | ok | en | 29 | 0.0256 |
| housing-10 | passed_after_retry | 2 | 2/2 | 0 | 0 | 0 | 33 | **no** | en | 103 | 0.3742 |
| housing-20 | passed | 2 | 2/2 | 0 | 0 | 12 | 0 | ok | en | 69 | 0.1883 |
| work-09 | passed_after_retry | 3 | 3/3 | 0 | 100 | 100 | 100 | ok | fr | 18 | 0.0086 |
| work-10 | degraded | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | it | 18 | 0.0071 |
| work-11 | passed | 0 | 0/0 | 0 | 0 | 0 | 0 | **no** | en | 85 | 0.2768 |
| adversarial-06 | passed | 2 | 2/2 | 0 | 100 | 17 | 100 | ok | en | 8 | 0.0046 |
| residence-21 | passed_after_retry | 6 | 6/6 | 0 | – | 42 | 100 | **no** | en | 85 | 0.1614 |
| residence-22 | degraded | 4 | 4/4 | 0 | 100 | 80 | 100 | ok | it | 16 | 0.0061 |
| social-18 | passed | 3 | 3/3 | 0 | 100 | 75 | 100 | ok | de | 9 | 0.0053 |
| tax-05 | passed | 2 | 2/2 | 0 | 0 | 33 | 0 | **no** | fr | 13 | 0.0095 |
| tax-10 | passed | 1 | 1/1 | 0 | 0 | 12 | 0 | **no** | en | 70 | 0.1741 |
| mobility-06 | degraded | 2 | 2/2 | 0 | 0 | 38 | 0 | ok | de | 13 | 0.0075 |
| mobility-09 | passed | 2 | 2/2 | 0 | 50 | 50 | 67 | ok | it | 14 | 0.0099 |
| general-05 | passed_after_retry | 2 | 2/2 | 0 | 0 | 75 | 0 | **no** | de | 20 | 0.0133 |
| adversarial-09 | passed_after_retry | 2 | 2/2 | 0 | 100 | 38 | 100 | ok | en | 32 | 0.0346 |

## Findings per case

- `tax-01`: unsupported: Cantonal tax laws may have additional requirements, such as lower income thresholds or different deadlines.; unsupported: The exact income threshold and procedural details are determined by the cantonal tax authorities.; missing fact: the amount is CHF 120,000 gross employment income in a tax year
- `housing-10`: behaviour: The assistant asked a clarifying question on an answerable question instead of providing a direct answer, and cited condominium property law (Art. 712c ZGB) instead of the tenancy law on subletting (Art. 262 OR).; unsupported: A tenant may sublet their apartment during a six-month absence, but generally needs the landlord's permission.; unsupported: The landlord can only refuse subletting for important reasons.; unsupported: If the landlord withholds consent without good cause, the tenant may ask the court to intervene.; unsupported: These subletting rules apply unless the rental agreement or a condominium regulation specifies otherwise.; missing fact: the landlord may refuse only if the tenant will not disclose the terms, the terms are abusive compared with the main lease, or the sublease causes the landlord significant disadvantages; missing fact: the tenant remains liable to the landlord for the subtenant using the flat only as permitted
- `housing-20`: unsupported: The notice period for ending a rental agreement in Switzerland is typically six months, unless otherwise agreed in the contract.; unsupported: The notice period applies to both tenants and landlords.; unsupported: The six-month notice period can be shortened by agreement, but not below three months for the landlord, unless the tenant is in default with payments.; missing fact: for an apartment the notice period is three months, to a customary local date or else the end of a three-month rental period; must_not violated: states a notice period other than three months for an apartment
- `work-11`: behaviour: The assistant failed to answer the question, claiming that no federal provisions on wrongful dismissal could be found instead of citing the relevant provisions of the Code of Obligations.; unsupported: The Swiss Civil Code provides protection of members in associations under Art. 75 CC.; unsupported: The Swiss Constitution provides the right to form professional associations under Art. 28 Cst.; missing fact: a termination is abusive if it is given because the other party asserts claims under the employment relationship in good faith; missing fact: the employer must then pay compensation set by the judge, at most six months' salary; missing fact: the employee must object to the termination in writing to the employer before the end of the notice period; missing fact: the claim must be brought before a court within 180 days after the employment ends, otherwise it lapses
- `adversarial-06`: unsupported: It is not legal under Swiss federal law to pay out unused holidays in cash annually instead of granting the leave.; unsupported: The law requires that holidays be taken as time off during the employment relationship.; unsupported: The prohibition on replacing holidays with cash applies to all statutory holidays.; unsupported: Only upon termination of employment may any accrued but unused holidays be paid out in cash.; unsupported: An employment contract cannot include a clause that allows annual cash payments in lieu of holidays.
- `residence-21`: behaviour: The assistant failed to ask a clarifying question about the missing facts (nationality and residence status) and left the clarifying question field empty.; unsupported: Swiss citizens and foreign nationals with a permanent residence permit (C permit) may work without restrictions.; unsupported: Persons with a temporary residence permit (B permit) may work, but the permit is tied to a specific employer and job.; unsupported: Persons with temporary protection status may also work in Switzerland.
- `residence-22`: unsupported: Le domande di naturalizzazione ordinaria sono esaminate dal comune e dal cantone di domicilio.
- `social-18`: unsupported: Der Selbstbehalt beträgt 10 Prozent der medizinischen Kosten, die über der Franchise liegen.
- `tax-05`: behaviour: The assistant provides an incorrect legal answer by stating that a person subject to source taxation cannot request a subsequent ordinary assessment to deduct pillar 3a contributions.; unsupported: Une personne soumise à l'impôt à la source ne peut pas demander une taxation ordinaire pour déduire ses versements au 3e pilier.; unsupported: Les versements au 3e pilier ne peuvent pas être déduits dans le cadre de l’impôt à la source.; missing fact: a source-taxed person who does not meet the conditions for a mandatory ordinary assessment can request a subsequent ordinary assessment; missing fact: the request must be filed by 31 March of the year following the tax year; missing fact: the ordinary assessment then applies until the end of source taxation; without a request no additional deductions are granted later; must_not violated: says source-taxed people can never claim pillar 3a deductions
- `tax-10`: behaviour: The answer defers almost entirely to cantonal law, fails to provide federal legal citations for its substantive claims, and misses the key rules regarding tax return obligations under federal law.; unsupported: The obligation to file a tax return in Switzerland is primarily governed by cantonal tax law, not federal law.; unsupported: The Federal Constitution sets the framework for tax matters.; unsupported: Tax return obligations, including who must file and when, are determined by the cantonal tax authorities.; unsupported: Whether you must file a tax return depends on the rules of your canton of residence.; unsupported: Cantonal rules typically depend on factors such as income, assets, marital status, and age.; unsupported: Individuals above a certain income threshold or with significant assets are generally required to file.; unsupported: The cantonal tax administration is responsible for determining who must file a tax return and for providing the necessary forms and guidance.; missing fact: employees without a settlement permit who live in Switzerland are taxed at source, unless married to a Swiss citizen or C permit holder; missing fact: people taxed at source are assessed in the ordinary procedure only if their gross income reaches the set amount (CHF 120,000) or they have income not taxed at source
- `mobility-06`: unsupported: Der Führerausweis der Kategorie B berechtigt zum Führen von Motorwagen mit einem Gesamtgewicht von nicht mehr als 3500 kg und nicht mehr als acht Plätzen außer dem Führersitz.; unsupported: Die genauen Fahrzeugkategorien, die Sie mit Ihrem Führerausweis führen dürfen, hängen von der eingetragenen Kategorie ab und sind im Führerausweis vermerkt.; missing fact: a valid foreign national licence (or an international licence together with it) allows driving the categories shown on it; missing fact: a Swiss licence is required once the driver has lived in Switzerland for twelve months without more than three consecutive months abroad; verifier: [2] non-existent letter removed
- `mobility-09`: unsupported: Il costo della corsa di controllo non è stabilito a livello federale, ma è determinato dalle autorità cantonali.; missing fact: drivers from abroad need a Swiss licence after twelve months of residence in Switzerland
- `general-05`: behaviour: The answer incorrectly claims that the federal Data Protection Act governs the cantonal/communal residents' register office, rather than pointing to cantonal data protection law.; unsupported: Das Bundesdatenschutzgesetz (DSG) gilt für die Daten, die die Einwohnerkontrolle führt.; missing fact: the federal data protection act applies to processing by private persons and federal bodies; missing fact: processing by cantonal or communal authorities such as the residents' office falls under cantonal data protection law, so the answer points to Basel-Stadt's rules or authority; must_not violated: says the federal act governs the cantonal residents' office
- `adversarial-09`: unsupported: Withholding tax is mandatory and not optional under federal law for B-permit holders who work and reside in Switzerland.; unsupported: The withholding tax obligation applies automatically unless an exemption exists.
