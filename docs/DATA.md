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
  (verified, ≈5 s for 23 acts)
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
5. **English is unofficial and sparse.** On 2026-10-15 only 5 of 23 corpus acts
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

Parsing rules:

- **Article IDs:** `art_<n>[_<letter>][_bis|_ter|_quater…]`.
  Examples: `art_1`, `art_271_a`, `art_329_g_bis`. Display form: `Art. 271a`,
  `Art. 329g bis`. Build a bidirectional mapping and unit-test it.
  (OR has 1,685 `<article>` elements.)
- **Headings path:** walk the ancestor `<level>`/`part`/`title`/`chapter`
  elements and collect `<num>` + `<heading>`. That gives a breadcrumb like
  `Zweite Abteilung › Achter Titel: Die Miete › … › Kündigungsschutz`. Store it
  per article. It drives the TOC tool and gives retrieval useful context.
- **Footnotes:** `<authorialNote>` elements are inline amendment notes (947 in
  OR alone). **Strip them from the article text.** Keep them in a separate
  `notes` field, since they're useful for "since when is this in force?"
  questions.
- **Repealed articles:** still present, with body text like "Aufgehoben" /
  "Abrogé" / "Abrogato" (verify the exact markup). Index them with
  `repealed: true` and exclude them from search by default.
- **Inline refs:** `<ref href="https://fedlex.data.admin.ch/eli/…">` point to
  other acts or to amendment publications (AS/BBl). Keep the hrefs as structured
  `refs`.
- **Whitespace:** text nodes have leading spaces and line breaks. Normalise
  them.

## 4. Pipeline (M1–M2)

```
acts.yaml ─▶ resolve (SPARQL) ─▶ manifest.lock.json ─▶ download XML (cache/raw/)
          ─▶ parse ─▶ articles.jsonl ─▶ chunk ─▶ embed ─▶ build index.sqlite
```

1. **resolve**: run `latest_consolidations.rq` with `AS_OF` = today. Write
   `corpus/manifest.lock.json` with sr, eli, consolidation URI, date, and per
   language the file URL and sha256. **Commit the lock file. Do not commit the
   XML.** The lock file makes builds reproducible and diffable ("OR changed on
   2026-10-01").
2. **download** to `cache/raw/<sr>/<date>/<lang>.xml` (gitignored). Skip files
   whose sha256 matches. Total is roughly 60–100 MB for 23 acts × 3–4
   languages (verify).
3. **parse** into `articles.jsonl`, one record per article per language:

   ```json
   {
     "id": "220:art_271_a:de",
     "sr": "220", "abbr": "OR", "lang": "de",
     "eid": "art_271_a", "label": "Art. 271a",
     "heading_path": ["Zweite Abteilung", "Achter Titel: Die Miete", "…", "Kündigungsschutz"],
     "marginal_heading": "…",
     "text": "1 Die Kündigung durch den Vermieter ist insbesondere anfechtbar, wenn …",
     "paragraphs": [{"eid": "art_271_a/para_1", "num": "1", "text": "…"}],
     "notes": ["Eingefügt durch Ziff. I des BG vom …"],
     "refs": ["https://fedlex.data.admin.ch/eli/oc/…"],
     "repealed": false,
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
5. **embed** with `gemini-embedding-2` (fallback `gemini-embedding-001`), both
   listed for europe-west6. Verify the task-type parameters
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

## 6. Size estimates (to verify in M1)

- OR DE XML: 2.2 MB. ZGB DE XML: 1.6 MB.
- ~23 acts × ~3.3 languages ≈ 75 documents, roughly 60–100 MB raw.
- Articles ≈ 8–10k per language, ≈ 30k article-language records.
- Vectors at 768 dims × float32 × 30k ≈ 92 MB, fine to bake into the image.
