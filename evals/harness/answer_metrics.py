"""Deterministic answer metrics (docs/EVALS.md §2) and their aggregation.

Per case: the harness's own re-check of every final citation (exists, in
force, verbatim quote; same normalisation as the verifier, `citecheck.py`),
citation recall/precision against `expected_citations`, behaviour per
category, language match, and cost. Ratios over the whole run (quote
fidelity, hallucination rate) are pooled over citations, with a bootstrap CI
that resamples cases.
"""

from __future__ import annotations

import random
import statistics
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

from agents.navigator.citecheck import ArticleNotFoundError, FetchError, find_quote
from evals.harness.agent_run import Usage
from evals.harness.cases import Case

DetectorFactory.seed = 0  # langdetect is random otherwise
LANGS = ("de", "fr", "it", "en")

GetArticle = Callable[[str, str, str], Awaitable[dict[str, Any]]]


@dataclass
class CitationCheck:
    ref: str
    sr: str
    article: str
    quote_lang: str
    eid: str | None = None
    exists: bool | None = None  # None: could not be checked (server error)
    in_force: bool | None = None
    has_quote: bool = False
    verbatim: bool | None = None
    text: str | None = None  # article text in quote_lang, for the judge


async def check_citations(answer: dict[str, Any], get_article: GetArticle) -> list[CitationCheck]:
    out = []
    for c in answer.get("citations") or []:
        chk = CitationCheck(
            ref=str(c.get("ref")), sr=str(c.get("sr")), article=str(c.get("article")),
            quote_lang=str(c.get("quote_lang")), has_quote=bool(c.get("quote")),
        )  # fmt: skip
        try:
            art = await get_article(chk.sr, chk.article, chk.quote_lang)
        except ArticleNotFoundError:
            chk.exists = False
        except FetchError:
            pass
        else:
            chk.exists, chk.eid = True, art.get("eid")
            chk.in_force = art.get("status") == "in_force"
            same_lang = art.get("lang") == chk.quote_lang
            chk.text = art.get("text") if same_lang else None
            if chk.has_quote:
                chk.verbatim = same_lang and find_quote(c["quote"], art.get("text", "")) is not None
        out.append(chk)
    return out


def detect_lang(text: str) -> str | None:
    """Most likely of de/fr/it/en, or None for empty or undetectable text."""
    try:
        ranked = detect_langs(text)
    except LangDetectException:
        return None
    ours = [r for r in ranked if r.lang in LANGS]
    return ours[0].lang if ours else None


def behaviour_ok(case: Case, answer: dict[str, Any], hallucinated: int) -> bool:
    """The deterministic half of behaviour accuracy (the judge adds the other half)."""
    asked = bool((answer.get("clarifying_question") or "").strip())
    oos = bool(answer.get("out_of_scope"))
    cited = bool(answer.get("citations"))
    match case.category:
        case "answerable":
            return cited and not asked and not oos
        case "needs_clarification":
            return asked
        case "cantonal_pointer":
            return bool((answer.get("cantonal_note") or "").strip()) and not oos
        case "out_of_scope":
            return oos
        case "adversarial":
            return hallucinated == 0
    return False


def cost_usd(model: str, usage: Usage, pricing: dict[str, Any]) -> float | None:
    p = pricing.get("models", {}).get(model)
    if p is None:
        return None
    fresh = usage.prompt - usage.cached
    cached_rate = p.get("cached_input", p["input"])
    return (
        fresh * p["input"]
        + usage.cached * cached_rate
        + (usage.output + usage.thoughts) * p.get("output", 0.0)
    ) / 1e6


def citation_scores(case: Case, checks: Sequence[CitationCheck]) -> dict[str, float | None]:
    produced = {(c.sr, c.eid) for c in checks if c.exists}
    expected = {(e.sr, e.eid) for e in case.expected_citations}
    required = {(e.sr, e.eid) for e in case.expected_citations if e.required}
    return {
        "required_recall": len(required & produced) / len(required) if required else None,
        "precision_expected": len(produced & expected) / len(produced) if produced else None,
    }


def mean(values: Sequence[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return statistics.fmean(vals) if vals else None


def ratio_ci(
    nums: Sequence[float], dens: Sequence[float], n: int = 2000, seed: int = 0
) -> tuple[float, float] | None:
    """Percentile bootstrap CI of sum(nums)/sum(dens), resampling cases."""
    pairs = [(a, b) for a, b in zip(nums, dens, strict=True)]
    if not pairs or not sum(b for _, b in pairs):
        return None
    rng = random.Random(seed)  # noqa: S311 (statistics, not security)
    stats = []
    for _ in range(n):
        sample = rng.choices(pairs, k=len(pairs))
        den = sum(b for _, b in sample)
        if den:
            stats.append(sum(a for a, _ in sample) / den)
    stats.sort()
    return stats[int(0.025 * len(stats))], stats[min(len(stats) - 1, int(0.975 * len(stats)))]


def percentile(values: Sequence[float], q: float) -> float | None:
    vals = sorted(values)
    return vals[round(q * (len(vals) - 1))] if vals else None


def as_dicts(checks: Sequence[CitationCheck]) -> list[dict[str, Any]]:
    return [asdict(c) | {"text": None} for c in checks]
