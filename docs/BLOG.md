# Grounded legal QA over Swiss law with ADK, MCP and Agent Runtime, and what the evals said

*Draft for dev.to / a personal site. Numbers as of 2026-10-20; every one of
them links back to a report or an ADR in
[the repo](https://github.com/nikext/swiss-admin-navigator).*

> Unofficial. Not legal advice. The project is not affiliated with the Swiss
> Confederation or any canton.

## The problem

Moving to Switzerland comes with a stream of legal questions. How long until a
C permit? Can my landlord keep the whole deposit? Is my employer allowed to
fire me while I'm on sick leave? The answers are in federal law and are
public, but they are spread over the Civil Code, the Code of Obligations, the
Foreign Nationals and Integration Act, the social insurance acts and a dozen
ordinances. They exist in German, French and Italian (all three equally
authoritative), and only some acts have an unofficial English translation.

An LLM will answer any of these questions fluently, and a fluent answer
without a source is worse than none. So I set myself two rules:

1. **Every legal statement cites an article, and the quote is verbatim.** Not
   "the model was told to quote verbatim": code checks it before the answer
   leaves the agent.
2. **Every design choice is decided by an eval.** Retrieval method, single or
   multi-agent, verifier, model, memory configuration, injection screen.
   Each has a measured number and a decision record behind it.

The result is [Swiss Admin Navigator](https://github.com/nikext/swiss-admin-navigator):
an ADK agent on Gemini Enterprise Agent Platform's Agent Runtime, retrieving
through a public MCP server over 23 federal acts, behind a small Next.js web
app.

## The corpus: the law is already structured

Fedlex, the federal publication platform, serves every consolidated act as
Akoma Ntoso XML and has a SPARQL endpoint that says which consolidation is
current. Every article has a stable element ID (`art_271_a` for Art. 271a OR),
so the article is the natural unit for both retrieval and citation.

The ingest pipeline is lock-driven: `make resolve` asks SPARQL for the current
consolidation of each act and writes `corpus/manifest.lock.json` with every
file URL and its sha256. `make ingest` downloads only what the lock names,
checks the hashes, and parses every article in every language into one record
with its heading path, footnotes split out, a repealed flag and a deep link.
That gave 18,396 article records. A random sample of 110 matched Fedlex's own
HTML rendering, text and URL.

## Retrieval as an MCP server, and the result I didn't expect

Retrieval lives behind an MCP server with five tools: `search_law`,
`get_article`, `get_toc`, `list_acts` and `resolve_citation`, which turns
"Art. 271a Abs. 1 lit. a OR" or "art. 30 al. 1 let. a LEI" into checked IDs.
The index is a single SQLite file (FTS5 plus vectors) baked into the container
image on Cloud Run. For 23 acts a vector database would only add a cost
floor, and the server starts in under three seconds. Because it is MCP, the
same server works from Claude Code or any other MCP client, and it is public.

Before choosing a retriever I built 102 retrieval queries in four languages
and measured. The usual advice is hybrid search: BM25 plus dense vectors,
fused with reciprocal rank fusion. On this corpus:

| retriever | recall@8 |
|---|---|
| BM25 | 51% |
| dense (`gemini-embedding-2`, contextual chunk headers) | **98.5%** |
| hybrid, equal-weight RRF | 85% |

Hybrid was 13.7 points *worse* than dense alone (paired CI −20.6…−7.4). People
ask in everyday words ("can my landlord kick me out because I complained"),
the law uses its own vocabulary, and the keyword list mostly added noise that
pushed good dense hits out of the top eight. Dense retrieval is served; BM25
stays only as the fallback when the embedding call fails
([ADR-016](DECISIONS.md)).

## The agent and the answer contract

The agent is a single ADK `LlmAgent` with the MCP toolset and a structured
output schema. It doesn't produce free text: it fills an answer contract
with markdown that carries `[n]` markers and one citation object per marker:

```json
{"ref": "1", "sr": "220", "article": "Art. 271a", "paragraph": "1", "letter": "a",
 "quote_lang": "fr", "quote": "Le congé est annulable lorsqu’il est donné par le bailleur, notamment: a. parce que le locataire fait valoir de bonne foi des prétentions découlant du bail;"}
```

The model does not write the Fedlex link, the act's abbreviation or the
"as of" date. Code fills those in from the article it fetched.

The important part is the **citation verifier**, an ADK `after_model_callback`.
When the model produces its final answer, the callback re-fetches every cited
article over the agent's own MCP session and checks it:

- the article exists and is in force;
- the paragraph and letter exist;
- the quote is a substring of that paragraph after normalising whitespace and
  apostrophes (a quote from another paragraph comes back as a wrong pinpoint);
- every `[n]` marker has a citation;
- the answer contains no addresses or phone numbers that came from the model
  instead of the law.

If anything fails, the callback replaces the answer with a call to a reserved
tool whose "result" lists the exact problems ("[1] the quote is not verbatim
in the FR text of CO Art. 271a. Copy it character for character from
get_article …"). The model redrafts in the same invocation. This is the
pattern of ADK's `ReflectAndRetryModelPlugin`, and the model can't call that
tool itself. After the last round, anything still unverifiable is dropped and
the answer is marked `degraded`.

## Measuring it

The eval suite has a **golden set of 150 cases** in four languages and five
domains: 106 answerable questions, 15 that should get the federal frame plus
a pointer to the canton, 13 out of scope, 10 adversarial and 6 where the
agent should ask a clarifying question first. Each case lists the expected
articles, the key facts an answer must contain, and what it must not say. I
drafted the cases with Claude and had them checked against the article text
by Claude Opus 5.5, case by case. That is a model, not a lawyer, and the
repo says so wherever the numbers appear.

Metrics come in two kinds:

- **Deterministic:** quote fidelity, hallucinated citations, required-citation
  recall, behaviour by rule, language. No judge, no noise.
- **Judged:** groundedness (share of claims supported by the cited text), key
  facts, must-not violations. The judge (`gemini-3.8-flash`) was picked by
  agreement with labelled answers (labelled by Claude, again not by a human). Every headline is graded again by **Qwen3
  235B**, a different model family, because a judge that shares the agent's
  family may share its blind spots.

Every number has a 95% bootstrap CI, and comparisons are **paired**: the same
cases under both configurations, bootstrapping the mean difference. With 150
cases, a 3-point difference in groundedness is usually noise, and the paired
CI says when it isn't.

One trick saved a lot of money. The verifier policies are nested (no check ⊂
code check ⊂ code check + LLM claim check), so the *prefix* of one recorded
claim-check run is a sample of each cheaper policy. One agent run gives all
three arms on the same trajectories, and only the judge runs again.

CI runs the retrieval eval and a 20-case smoke eval against Gemini on every
ready PR (GitHub Actions with Workload Identity Federation, no keys). Quote
fidelity below 100% or a single hallucinated citation fails the build.

The served configuration on golden: **0 hallucinated citations** of 549,
**99.6%** verbatim quotes, groundedness 81.9 (Flash judge) / 91.9 (Qwen
judge), key facts 95.4, correct behaviour 97.3%, **CHF 0.039** and a median of
39 s per answer.

## What the evals said

### Multi-agent didn't pay

The obvious upgrade is a router and domain specialists: housing, work,
residence, social insurance, tax. I built it as an ADK 2.x workflow (v2) and
ran both agents on golden and adversarial. The router picked the expected
domain 98% of the time. v2 was still **less grounded in every arm** (−1.7 to
−2.8 points; −2.8 with a CI excluding zero under the cross-family judge) and
13% more expensive. The specialists' narrower search scopes cost more than
their focused instructions gained. The single agent stays
([ADR-034](DECISIONS.md)).

### The verifier is where the quality comes from

- **Code check** (re-fetch, compare, one redraft): quote fidelity 98.5% →
  99.6%, for 7% more cost. It is always on.
- **LLM claim checker** (rates each claim against the cited text, sends
  unsupported claims back, removes what still fails): groundedness **+4.4**
  (CI +2.4…+6.5) under the Qwen judge, at 1.8× the cost and twice the latency.
  It stays opt-in.

Under the Flash judge the claim checker's gain was +9.4, twice the Qwen
number. Part of it was Flash agreeing with Flash. Without the second judge I
would have reported the bigger number.

### Model choice: the newest model is not automatically the answer

Same agent, same verifier, only the model swapped (golden; groundedness
change vs Flash on the same cases, Flash judge / Qwen judge):

| model | Δ groundedness | key facts | CHF / answer |
|---|---|---|---|
| gemini-3.8-flash (served) | — | 95.4 | 0.039 |
| gemini-4-argon | +7.4 / +4.8 | 97.4 | 0.049 (0.099 from Dec.) |
| gemini-3.1-pro-preview | −7.3 / −4.4 | 93.9 | 0.071 |
| gemini-3.5-flash-lite | −1.8 / −3.7 | 82.3 | 0.005 |
| DeepSeek V3.2 | −4.7 / −2.7 | 82.9 | 0.019 |
| Qwen3 235B | −13.3 / −9.1 | 71.5 | 0.020 |
| Apertus 1.5 8B, self-hosted | −68.0 / −58.1 | 34.3 | 0.012 (GPU time) |

- **gemini-4-argon** is the only model better grounded than Flash under both
  judges. But it looped in 3–10% of cases (up to 215 `get_article` calls
  before the timeout), and its price doubles in December. The agent now has a
  budget of 40 model calls per turn, after which it must answer from what it
  has. Flash stays, and argon gets a second look when its loop rate drops.
- **Pro preview** was *less* grounded: it read fewer articles (3.4 tool calls
  vs 6.4) and answered more from memory.
- **Apertus**, the Swiss open model, ran self-hosted with vLLM on a Cloud Run
  L4 in europe-west4 (no GPUs in Zürich). As a tool-using agent the 8B model
  read too little (2 tool calls per answer) and couldn't hold the answer
  format: 144 of 150 first drafts were off-schema. It is cheap per answer
  while the GPU is busy, but a cold start takes 13 minutes, so serving it
  would need an always-on GPU at about CHF 850 a month.

Across every model, including the 8B one, **no answer cited an article that
doesn't exist**. The verifier holds that line regardless of the model. A
weaker model pays for it in redrafts and dropped citations.

### Languages: no effect

40 golden questions, each asked in German, English, French and Italian: no
difference beyond noise. English answers quote the German text, because most
acts have no English version, and they score the same.

### Memory: the defaults stored health data

Opt-in memory should remember the useful facts (canton, permit type,
employment status) and nothing sensitive. With Memory Bank's default
extraction, only **2 of 13** privacy cases passed: it stored diagnoses, a
conviction and a religion. The configuration that worked was a **structured
profile whose schema is the whitelist**: canton, municipality, permit and a
few more fields, with enums wherever possible and natural-language memories
switched off. It passed 39 of 39 privacy checks over three runs. The user sees
what is stored and can delete it ([ADR-029](DECISIONS.md)).

### Model Armor: a layer, not a wall

Every message is screened by Model Armor before the first model call. On 58
attacks, 532 benign questions and 400 law texts, its prompt-injection filter
at medium confidence blocked 29% of attacks with **zero false positives**. It
caught 9 of 10 blunt "ignore your instructions" overrides, and **0 of 13**
injections hidden inside a pasted contract, e-mail or letter, at any
threshold. The screen is cheap and harmless, so it stays. What protects the
answers from a document full of instructions is that tool output and pasted
text are treated as data, and that every citation is checked
([ADR-032](DECISIONS.md)).

## Running it

- **Agent Runtime** in europe-west6 (Zürich) with managed Sessions and Memory
  Bank, deployed with `adk deploy agent_engine` from a staged folder. It
  scales to zero at 1 vCPU / 2 GiB; the default, one always-on instance at
  4 vCPU / 4 GiB, would have cost about USD 270 a month. Every model and tool call is a span in Cloud Trace.
- **Data residency, stated precisely:** Gemini isn't served in Zürich, so the
  agent's model calls go to the `eu` endpoint, which processes within EU
  member states (Switzerland excluded). The honest wording is "deployed in
  Zürich, model calls processed in the EU", not "data never leaves
  Switzerland".
- **Web:** a Next.js BFF holds the service-account credentials, checks an
  access code and Firestore quotas (10 questions per visitor, 20 per day
  overall), and relays the agent's progress ("Reading OR Art. 271a…") as
  server-sent events until the verified answer arrives.
- **Capacity:** the shared `eu` and `global` endpoints degraded for hours
  at a time during the experiments, with "Say OK." taking 10–40 s or failing
  with 429s. Per-call deadlines with retries, and eval runs that checkpoint
  every case and resume, turned outages into re-runs instead of lost days.

The experiments from M4 to M10 cost about CHF 145 in model calls, according to
the spend notes in each milestone's PR; M8 (multi-agent) and M9 (models) were
most of it.

## What I'd do next

- Have a Swiss lawyer review a sample of the golden cases. Until then, the
  ground truth is model-verified.
- Cantonal law, starting with Zürich, so the cantonal pointer becomes an
  answer.
- Decide whether the web app turns on the claim checker: +4.4 groundedness
  for twice the wait is a product decision, not an eval result.
- Expose the agent over A2A, and rebuild the index monthly with an eval run
  before each deploy.

The code, every eval report and the 35 decision records are in the repo:
<https://github.com/nikext/swiss-admin-navigator>. The MCP server is public,
so you can plug Swiss federal law into your own MCP client:

```bash
claude mcp add --transport http swiss-law https://swiss-nav-mcp-mdyqt5hgsq-oa.a.run.app/mcp
```
