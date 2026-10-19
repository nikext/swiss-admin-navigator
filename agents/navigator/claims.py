"""The LLM claim checker (M8, ADR-030): does the cited text support each legal claim?

The deterministic check (`citecheck.py`) proves that every citation exists and
every quote is verbatim. It cannot see a true quote attached to a claim the
quoted article does not support, which is where groundedness was lost in M3/M4
(ADR-019). This checker reads the draft next to the full text of the cited
articles and grades each claim yes / partly / no (`prompts/claim_check.md`, a
prompt of its own, not the eval judge's).

The verifier runs it only on drafts that passed the deterministic check and
cite something. `partly` and `no` become `unsupported` problems for a redraft;
claims still rated `no` after the last round are removed from the answer text
(`citecheck.remove_claims`). A checker failure never blocks an answer: the
round is recorded without claims.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from .citecheck import Checked
from .config import HTTP, LlmRef
from .contract import ClaimCheck, DraftAnswer, Problem, TokenUsage

PROMPT_PATH = Path(__file__).parent / "prompts" / "claim_check.md"


class ClaimCheckResult(BaseModel):
    claims: list[ClaimCheck]


def payload(question: str, draft: DraftAnswer, checked: list[Checked]) -> dict[str, Any]:
    """What the checker sees: the question, the draft's user-facing text and citations,
    and the full text of each cited article in the quoted language."""
    cite_keys = ("ref", "abbr", "article", "paragraph", "letter", "quote")
    law: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for ch in checked:
        art = ch.article
        if not art:
            continue
        key = (str(art.get("sr")), str(art.get("label")), str(art.get("lang")))
        refs = [c.citation.ref for c in checked if c.article is art]
        if key in seen:
            continue
        seen.add(key)
        law.append(
            {
                "refs": refs,
                "act": art.get("abbr"),
                "article": art.get("label"),
                "lang": art.get("lang"),
                "text": art.get("text", ""),
            }
        )
    return {
        "question": question,
        "draft": {
            "answer_markdown": draft.answer_markdown,
            "cantonal_note": draft.cantonal_note,
            "citations": [
                {k: v for k, v in ch.citation.model_dump().items() if k in cite_keys}
                for ch in checked
            ],
        },
        "cited_law": law,
    }


def problems(claims: list[ClaimCheck]) -> list[Problem]:
    """`unsupported` problems for the redraft, one per claim rated partly or no."""
    out = []
    for c in claims:
        if c.supported == "yes":
            continue
        refs = ", ".join(f"[{r}]" for r in c.refs) or "no citation"
        how = "is not supported" if c.supported == "no" else "is only partly supported"
        issue = f" {c.issue.strip()}" if c.issue else ""
        msg = (
            f'"{c.claim}" ({refs}) {how} by the cited text.{issue} Cite an article whose text '
            "states it, narrow the claim to what the text says, or drop it."
        )
        out.append(Problem(ref=c.refs[0] if c.refs else None, kind="unsupported", message=msg))
    return out


def usage_of(meta: types.GenerateContentResponseUsageMetadata | None) -> TokenUsage:
    if meta is None:
        return TokenUsage(model_calls=1)
    return TokenUsage(
        model_calls=1,
        prompt=meta.prompt_token_count or 0,
        cached=meta.cached_content_token_count or 0,
        output=meta.candidates_token_count or 0,
        thoughts=meta.thoughts_token_count or 0,
    )


class ClaimChecker:
    """Grades a draft's claims with the profile's `verifier` model."""

    def __init__(self, ref: LlmRef, project: str | None = None) -> None:
        self.ref = ref
        self.prompt = PROMPT_PATH.read_text(encoding="utf-8")
        self._project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        # Built on first use: importing the agent must not need credentials (tests, adk web).
        if self._client is None:
            self._client = genai.Client(
                vertexai=True,
                project=self._project,
                location=self.ref.location,
                http_options=HTTP,
            )
        return self._client

    async def check(
        self, question: str, draft: DraftAnswer, checked: list[Checked]
    ) -> tuple[list[ClaimCheck], TokenUsage, float]:
        config = types.GenerateContentConfig(
            system_instruction=self.prompt,
            temperature=0,
            response_mime_type="application/json",
            response_schema=ClaimCheckResult,
        )
        if self.ref.thinking:
            level = types.ThinkingLevel(self.ref.thinking.upper())
            config.thinking_config = types.ThinkingConfig(thinking_level=level)
        text = json.dumps(payload(question, draft, checked), ensure_ascii=False)
        start = time.perf_counter()
        resp = await self.client.aio.models.generate_content(
            model=self.ref.model, contents=text, config=config
        )
        seconds = time.perf_counter() - start
        result = ClaimCheckResult.model_validate_json(resp.text or "")
        return result.claims, usage_of(resp.usage_metadata), seconds
