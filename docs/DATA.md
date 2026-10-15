# Data: Fedlex corpus pipeline

Everything in this file marked **verified** was run against the live Fedlex
endpoints on 2026-10-15. Anything marked **verify** is still an assumption for
the build agent to confirm in M1.

## 1. Source and legal basis

- **Source:** [Fedlex](https://www.fedlex.admin.ch), the Swiss Confederation's
  official publication platform for federal law. We use the **Classified
  Compilation (SR / RS / CC)**, which holds consolidated, current law.
- **Copyright:** Swiss laws, ordinances, international treaties and other
  official enactments are **not protected by copyright** (Art. 5 para. 1 lit. a
  URG, SR 231.1). Official collections and translations of them are also free
  (Art. 5 para. 2). We may download, store, index and quote them. Still
  attribute Fedlex as the source and link every citation back to it.
- **Not in v1:** ch.ch / admin.ch explanatory pages. Their reuse terms are
  unverified, so we only *link* to them and never ingest them. Cantonal law
  (e.g. Zürich ZH-Lex) has no verified official API, so it is a stretch goal
  (see PLAN.md).

## 2. Access paths (verified)

| What | How |
|---|---|
| Metadata (acts, consolidations, files) | SPARQL at `https://fedlex.data.admin.ch/sparqlendpoint` (POST `query=…`, `Accept: text/csv` or `application/sparql-results+json`). No key, no documented rate limit. Be polite: serial requests with a delay, cache results. |
| Ontology | JOLux (`http://data.legilux.public.lu/resource/ontology/jolux#`), based on FRBR/ELI |
| Full text | Akoma Ntoso 3.0 XML files under `https://fedlex.data.admin.ch/filestore/…` |
| Human-readable deep link | `https://www.fedlex.admin.ch/eli/cc/<…>/<lang>#<eId>`, e.g. [`…/eli/cc/27/317_321_377/de#art_271_a`](https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_271_a) (HTTP 200, verified) |

### The FRBR chain

```
ConsolidationAbstract  (the act, "Work")          eli/cc/27/317_321_377
  └─ Consolidation     (version valid from date)  eli/cc/27/317_321_377/20261001
       └─ Expression   (one language)             …/20261001/de
            └─ Manifestation (format)             xml | html | pdf-a | docx
                 └─ isExemplifiedBy → file URL    …/de/xml/fedlex-…-de-xml-3.xml
```

### Queries (in `corpus/queries/`)

- `latest_consolidations.rq`: for each SR number, returns the in-force act, its
  latest consolidation applicable on a date, and the languages with XML.
  (verified; ≈17 s for 23 acts on 2026-10-15, so the docs' earlier "≈5 s" was
  optimistic)
- `consolidation_files.rq`: returns all file URLs for one consolidation.
  (verified)

### Gotchas (verified)

1. **SR numbers are reused.** `142.20` matches both the repealed ANAG (1931)
   and the current AIG. Filter on
   `jolux:inForceStatus <…/enforcement-status/0>` (in force). `/3` = repealed.
2. **Future-dated consolidations exist** (scheduled amendments). Always cap
   `dateApplicability <= AS_OF`.
3. **The endpoint returns duplicate rows.** Use `DISTINCT` or `GROUP BY`.
4. **File names are unpredictable**: `…-de-xml-2.xml`, `…-de-xml-3.xml`,
   `…-en-xml.xml`. Always take URLs from SPARQL.
5. **Languages come back as EU authority URIs with ISO 639-2 codes**
   (`…/language/DEU`, and `deu fra ita eng roh` from the GROUP_CONCAT), not
   `de/fr/it`. `ingest.resolve.lang_code` maps them. We ingest **de, fr, it,
   en**. Romansh (`rm`, 3 acts) is outside the product's languages.
6. **English is unofficial and sparse.** On 2026-10-15 only 5 of 23 corpus acts
   had EN XML for the current consolidation (BV, ZGB, DSG, BüG, RHG; no
   AIG and no OR!). DE, FR and IT are equally authoritative. **Design consequence:**
   answers in English must quote the DE/FR/IT original and mark any English
   rendering as *our translation*. Never present it as official.

## 3. XML structure (verified on OR and ZGB)

```xml
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
            xmlns:fedlex="http://fedlex.admin.ch/">
 <act name="publicLaw">
  <meta> … FRBRWork: FRBRnumber=SR, FRBRname per language with shortForm (abbr),
         FRBRdate name="jolux:dateApplicability" … </meta>
  <body>
   <level eId="part_1/tit_1/chap_1/lvl_A" fedlex:role="marginal">
     <num>A. </num><heading>…</heading>
     <article eId="art_271_a">
       <num><b>Art. 271</b><i>a</i></num>
       <paragraph eId="art_271_a/para_1">
         <num>1</num>
         <content>
           <blockList>
             <listIntroduction>…</listIntroduction>
             <item eId="art_271_a/para_1/lbl_a"><num>a. </num><p>…</p></item>
           </blockList>
         </content>
       </paragraph>
     </article>
   </level>
  </body>
 </act>
</akomaNtoso>
```

Parsing rules (all verified on the full 2026-10-15 corpus, implemented in
`ingest/parse.py`, unit-tested on real excerpts in `ingest/tests/fixtures/`):

- **Article IDs:** `art_<n>[_<letter>][_bis|_ter|…]`, plus three shapes the
  first draft of this doc didn't anticipate:
  - **ranges** `art_226_a_226_d` (Art. 226a–226d), `art_274_274_g`,
    `art_48_bis_48_sexies`, usually repealed together;
  - **scoped transitional provisions** `disp_u2/art_1` (inside a `<proviso>`
    like "Schlussbestimmungen der Änderung vom 23. März 1962"; ZGB's
    Schlusstitel is `disp_u1/…`);
  - **treaty annexes** `annex_I/lvl_u1/lvl_II/art_6` in `<components>` (FZA
    Annex I/II, 44 articles per language). They matter: Annex I holds EU
    citizens' residence rights.

  Labels: `Art. 271a`, `Art. 329g bis`, `Art. 48bis`, `Art. 226a–226d`; the
  scope stays in the eId only. `ingest/eid.py` maps both ways and accepts the
  spellings people write (`329gbis`, `art. 329 g bis`, `Artikel 271a`).
- **eId must agree with the printed number.** The printed `<num>` is compared
  structurally (numbers, attached letters, ordinals; connectors like "à",
  "a", "und" ignored). On disagreement the record is **dropped and listed in
  `corpus/stats.md`**, because a citation system must never serve text under
  the wrong number. On 2026-10-15 this dropped 10 records, all real Fedlex
  data errors: 9 in the unofficial EN ZGB (a run of shifted eIds; `art_256`
  prints "Art. 255a") and 1 in IT OR (range `art_697_l_697_m` printed
  "Art. 697l").
- **Headings path:** every ancestor container with a `num`/`heading` (`book`,
  `part`, `title`, `chapter`, `section`, `level`, `proviso`, …), formatted
  "num heading" (e.g. `Achter Titel: Die Miete`). Annexes start with the
  preface label (`Anhang I`). Flat acts (VMWG) have an empty path.
- **`heading`:** the article's own `<heading>` (+ `<subheading>`, e.g.
  "Unselbstständige Erwerbstätigkeit (Art. 11 Abs. 2 AIG)"). Ordinances, BV
  and AIG use own headings (6,518 articles). OR and ZGB use marginal levels
  (`<level fedlex:role="marginal">`) instead, and we take the innermost one.
  Otherwise it's null, and the section heading is only in `heading_path`.
- **Footnotes:** `<authorialNote>` appears in bodies **and inside `<num>` and
  `<heading>`** of articles and containers (e.g. "Achter Titel: *Fassung
  gemäss …*"). Strip them from every text field and keep them in `notes`.
- **Status** (replaces the planned `repealed` flag):
  - `repealed`: no operative text (a bare `<num>` whose note says
    Aufgehoben/Abrogé(s)/Abrogato/i/Repealed), or the body is just that word;
  - `omitted`: the body is "…" and the note says "Die Änderungen können unter
    AS … konsultiert werden" (spent amendment provisions);
  - otherwise `in_force`. Search excludes everything but `in_force`.
- **Refs:** operative text cross-references other articles in plain words
  ("Art. 18–29"), with only 2 hyperlinks corpus-wide. The hrefs that do exist
  are the AS/BBl amendment publications in footnotes, so `refs` holds every
  href in the article. Extracting textual cross-references is M2's
  `resolve_citation` job.
- **Text rendering:** one line per paragraph, list intro and list item
  (`a. …`, nested `1. …`); paragraph numbers prefixed as printed (`1`, `(1)`,
  `1.`); tables as rows with ` | ` between non-empty cells (46 articles, e.g.
  the DBG Art. 36 tax tariff); whitespace normalised.
- **Abbreviations:** each XML's `FRBRname/@shortForm` per language is
  authoritative and used for the record's `abbr`. All DE/FR/IT abbreviations
  in `acts.yaml` matched it on 2026-10-15. EN ones: Cst., CC, FADP, SCA, RHA.

## 4. Pipeline (M1–M2)

```
acts.yaml ─▶ resolve (SPARQL) ─▶ manifest.lock.json ─▶ download XML (cache/raw/)
          ─▶ parse ─▶ articles.jsonl ─▶ chunk ─▶ embed ─▶ build index.sqlite
```

1. **resolve** (`make resolve`, explicit refresh): run
   `latest_consolidations.rq` with `AS_OF` (default today), fail if an act is
   missing or its in-force ELI differs from `acts.yaml`, then
   `consolidation_files.rq` per act. Fetch each XML through the cache to record
   its sha256, and write `corpus/manifest.lock.json` (sr, abbr, eli,
   consolidation, date, domain, and per language url/sha256/bytes). **Commit
   the lock file. Do not commit the XML.**
2. **download** (`make ingest`, step 1): reads only the lock and fills
   `cache/raw/<sr>/<date>/<lang>.xml` (gitignored) at 1 request/s with
   backoff. If a fetched file's sha256 differs from the lock, it fails and
   tells you to re-resolve. So `make ingest` is reproducible from the
   committed lock, and only `make resolve` follows Fedlex forward.
3. **parse** (`make ingest`, step 2) into `data/articles.jsonl`, one record
   per article per language, plus `corpus/stats.md` (committed; counts per
   act × language × status, and every dropped record):

   ```json
   {
     "id": "220:art_271_a:de",
     "sr": "220", "abbr": "OR", "lang": "de",
     "eid": "art_271_a", "label": "Art. 271a",
     "heading": "Kündigung durch den Vermieter",
     "heading_path": ["Zweite Abteilung: Die einzelnen Vertragsverhältnisse",
                      "Achter Titel: Die Miete", "Dritter Abschnitt: Kündigungsschutz …",
                      "A. Anfechtbarkeit der Kündigung", "II. Kündigung durch den Vermieter"],
     "text": "1 Die Kündigung durch den Vermieter ist insbesondere anfechtbar, wenn sie ausgesprochen wird:\na. weil der Mieter …",
     "paragraphs": [{"eid": "art_271_a/para_1", "num": "1", "text": "Die Kündigung … wird:\na. weil …"}],
     "notes": ["Eingefügt durch Ziff. I des BG vom …"],
     "refs": ["https://fedlex.data.admin.ch/eli/oc/…"],
     "status": "in_force",
     "consolidation_date": "2026-10-01",
     "url": "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_271_a",
     "domain": ["work", "housing"]
   }
   ```

4. **chunk**: in law, the **article is the natural unit**, and most articles are
   short. One chunk per article. Split only very long articles at paragraph
   boundaries (threshold ~1,200 tokens) and keep `eid` pointing at the
   paragraph. Prepend `abbr + label + heading_path` to the embedded text
   ("contextual chunk header"). Measure the effect in evals.
5. **embed** with the profile's embedding model (`gemini-embedding-2@eu`;
   `gemini-embedding-001` is the only one served in europe-west6, see
   ADR-013). Verify the task-type parameters
   (`RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY`) and the dimensionality options in
   M2. Batch the calls, cache by content hash, and record the model ID in the
   index metadata.
6. **index**: one SQLite file `index.sqlite` with
   - `articles` table (all fields above)
   - `articles_fts`: FTS5 full-text index, one per language column, or a
     `lang` filter. German compounds hurt token-based BM25 (`Kündigungsschutz`
     vs `Kündigung`), so evaluate `tokenize='trigram'` against `unicode61` in
     M2 and keep whichever retrieval eval prefers.
   - `vectors`: sqlite-vec virtual table (or a plain float32 blob plus numpy at
     load time; the corpus is small, ~30k chunks). Decide in M2 by
     measurement.
   - `toc`: tree of levels and articles per act and language, for the
     `get_toc` tool.
   - `abbreviations`: every DE/FR/IT abbreviation mapped to its SR. Used by
     `resolve_citation`. Seed it from `acts.yaml`; the FRBRname `shortForm` in
     each XML is authoritative.
   - `meta`: as_of, consolidation dates, embedding model, build git sha.

## 5. Freshness

- Laws change on the 1st of the month most often. A monthly rebuild is enough
  (stretch: Cloud Scheduler → Cloud Build → new MCP image).
- Every answer carries "Stand / as of `<consolidation_date>`" per cited act.
- The lock-file diff between builds lists which acts changed. Put it in the PR
  description.

## 6. Sizes (measured 2026-10-15, as_of 2026-10-15)

- Raw XML: **74 files, 34.5 MB** (23 acts × DE/FR/IT + EN for 5). OR DE is
  2.2 MB, as expected. The earlier 60–100 MB estimate was 2× too high.
- `articles.jsonl`: **18,396 records, 36 MB**: DE 5,606, FR 5,606, IT 5,605,
  EN 1,579. OR has 1,685 articles per language (matches the `<article>`
  count). Per-act numbers are in `corpus/stats.md`.
- In-force text length (characters): p50 431, p95 1,636, p99 2,894, max
  30,996 (FZA Art. 10 FR, transitional quotas with tables). A few articles
  need M2's paragraph-level chunking.
- Status: 17,243 in force, 1,066 repealed, 87 omitted. Vectors for the
  in-force records: × 768 dims × float32 ≈ 53 MB (3072 dims ≈ 212 MB); decide
  the dimensionality in M2.
- `make ingest` from a warm cache takes ~3 s; `make resolve` ~1 min (SPARQL
  plus 74 polite downloads).

## 7. Verification

`make spotcheck` samples in-force records (fixed seed) and compares each one
with Fedlex's **HTML manifestation** of the same consolidation, an
independent rendering in the filestore. It checks that the record's `#eId`
anchor exists there (www.fedlex.admin.ch is a JS app, so HTTP 200 alone proves
nothing), that the deep-link page answers 200, and that the text is
identical after dropping footnote markers and normalising whitespace.
Fedlex's HTML prints reference subheadings ("(art. 30, al. 1, let. k, LEI)")
at the start of the body, while we keep them in `heading`; the comparison
accounts for that. On 2026-10-15: **10/10 identical** (seed 20261015) and
**100/100 identical** (seed 7; 31 acts, DE 32 / FR 32 / IT 29 / EN 7). A first
run reported 96/100, and all four differences were exactly that subheading.
