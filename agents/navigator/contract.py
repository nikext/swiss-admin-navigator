"""The answer contract (docs/ARCHITECTURE.md §4, ADR-018).

The model fills `DraftAnswer` (ADK `output_schema`). The citation verifier
(`verifier.py`) checks it against the law text and returns an `Answer`: the
same fields, plus what code derives instead of the model (each citation's
abbreviation, Fedlex URL and as-of date, the exact quote span from the
source), the verification record and the fixed notice (ADR-010).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Lang = Literal["de", "fr", "it", "en"]

NOTICE = "Unofficial. Not legal advice. Sources: Fedlex (fedlex.admin.ch)."


class DraftCitation(BaseModel):
    ref: str = Field(description='Marker used in answer_markdown: "1" for [1].')
    sr: str = Field(description='SR number of the act as the tools return it, e.g. "220".')
    article: str = Field(description='Article label as get_article returns it, e.g. "Art. 271a".')
    paragraph: str | None = Field(
        default=None, description='Paragraph number (Abs./al./cpv.), e.g. "1"; null if none.'
    )
    letter: str | None = Field(
        default=None, description='Letter (lit./let./lett.), e.g. "a"; null if none.'
    )
    quote_lang: Lang = Field(description="Language of the get_article text the quote is from.")
    quote: str = Field(
        description="Verbatim excerpt from that get_article text: one contiguous passage, "
        "copied character for character. Mark omissions with …"
    )
    translation: str | None = Field(
        default=None,
        description="Translation of the quote into the answer language when quote_lang differs; "
        "it is unofficial. Null otherwise.",
    )


class DraftAnswer(BaseModel):
    language: Lang = Field(description="Language of the user's question and of this answer.")
    answer_markdown: str = Field(
        description="The answer in Markdown. Every legal statement carries a marker like [1] "
        "that matches a citation's ref."
    )
    citations: list[DraftCitation] = Field(
        description="One entry per marker; every article was fetched with get_article."
    )
    clarifying_question: str | None = Field(
        default=None,
        description="The one question to ask when a missing fact changes the answer; null "
        "otherwise.",
    )
    cantonal_note: str | None = Field(
        default=None,
        description="Pointer to the competent cantonal or communal authority when part of the "
        "answer is cantonal; null otherwise.",
    )
    follow_up_questions: list[str] = Field(
        default_factory=list, description="Up to three questions the user may want to ask next."
    )
    confidence: Literal["high", "medium", "low"]
    out_of_scope: bool = Field(
        description="True when the question is outside federal law in this corpus or needs a "
        "lawyer (criminal defence, ongoing proceedings, individual tax computation)."
    )


class Citation(DraftCitation):
    quote: str | None  # type: ignore[assignment]  # None: removed by the verifier
    abbr: str | None = None
    url: str | None = None
    as_of: str | None = None


class Problem(BaseModel):
    ref: str | None
    kind: Literal[
        "parse",  # the output is not a valid DraftAnswer
        "marker",  # [n] in answer_markdown without a citation
        "not_found",  # SR/article does not exist
        "not_in_force",  # repealed or omitted article
        "lang",  # no text in quote_lang for this article
        "paragraph",  # paragraph number does not exist
        "letter",  # letter does not exist in that paragraph
        "quote",  # quote is not in the article text
        "pinpoint",  # quote is in the article, but not in the cited paragraph
        "fetch",  # the law server could not be reached (not the model's fault)
        "contact",  # street address, postcode, phone or web address written from memory
    ]
    message: str


class Round(BaseModel):
    citations: int
    quotes: int
    problems: list[Problem]


class Verification(BaseModel):
    status: Literal["passed", "passed_after_retry", "degraded", "unavailable"]
    rounds: list[Round] = Field(description="One per checked draft, first draft first.")
    dropped: list[str] = Field(default_factory=list, description="Refs removed from the answer.")
    repairs: list[str] = Field(default_factory=list, description="Deterministic fixes applied.")


class Answer(DraftAnswer):
    citations: list[Citation]  # type: ignore[assignment]
    verification: Verification
    notice: str = NOTICE
