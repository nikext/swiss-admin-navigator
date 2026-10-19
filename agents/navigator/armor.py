"""Model Armor screening of what users send the navigator (M10, docs/AGENTS.md §8).

`ModelArmor.screen` sends one text to a template's `sanitizeUserPrompt` (REST,
on the template's regional endpoint: `eu`, since Model Armor has no
europe-west6) and returns a `Verdict`: the prompt-injection/jailbreak
confidence, the Responsible AI categories that matched, and the Sensitive Data
Protection, malicious-URL and CSAM matches. The template reports every
detection from LOW_AND_ABOVE up (infra/model_armor.sh), so the threshold is
applied here (`Verdict.flags`): the E7 eval scores every threshold from one
pass, and changing it needs no template change.

Screening never raises. A failed call returns a Verdict with `error` set and
the caller decides what that means: `InputScreen` (the agent's
`before_agent_callback`) fails open and blocks only on the injection filter at
`MODEL_ARMOR_MIN_LEVEL`, measured in E7 (`evals/harness/armor_eval.py`,
ADR-032).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Literal

import google.auth
import google.auth.transport.requests
import httpx
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from .contract import Answer, Screening, Verification

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
TEMPLATE = re.compile(r"projects/[^/]+/locations/(?P<location>[^/]+)/templates/[^/]+")
MATCH = "MATCH_FOUND"
SKIPPED = "EXECUTION_SKIPPED"
# DetectionConfidenceLevel → rank. A match reported without a level counts as the lowest.
LEVELS = {"LOW_AND_ABOVE": 1, "MEDIUM_AND_ABOVE": 2, "HIGH": 3}
LEVEL_NAMES = {1: "low", 2: "medium", 3: "high"}
RETRY_STATUS = (429, 500, 503)


def level(name: str | None) -> int:
    """`low`/`medium`/`high` or the API's enum name → 1/2/3."""
    if not name:
        return 1
    by_name = {v: k for k, v in LEVEL_NAMES.items()}
    return LEVELS.get(name) or by_name.get(name.lower()) or 1


@dataclass(frozen=True)
class Verdict:
    invocation: str = ""  # SUCCESS | PARTIAL | FAILURE; "" when the call failed
    injection: int = 0  # prompt injection / jailbreak: 0 none, 1 low, 2 medium, 3 high
    rai: dict[str, int] = field(default_factory=dict)  # matched category -> level
    sdp: bool = False
    malicious_uri: bool = False
    csam: bool = False
    skipped: tuple[str, ...] = ()  # filters that did not run (too short, too long, ...)
    error: str | None = None
    latency_ms: float | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.invocation in ("SUCCESS", "PARTIAL")

    def flags(self, min_level: int = 3) -> list[str]:
        """What matched at or above `min_level` ("injection:high", "rai:dangerous:medium",
        "sdp", ...). SDP, malicious URLs and CSAM have no level and always count."""
        out = []
        if self.injection >= min_level:
            out.append(f"injection:{LEVEL_NAMES[self.injection]}")
        out += [f"rai:{k}:{LEVEL_NAMES[v]}" for k, v in sorted(self.rai.items()) if v >= min_level]
        out += [n for n, hit in (("sdp", self.sdp), ("malicious_uri", self.malicious_uri)) if hit]
        if self.csam:
            out.append("csam")
        return out

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["skipped"] = list(self.skipped)
        return {k: v for k, v in d.items() if v not in (None, False, 0, {}, [], "")} | {
            "invocation": self.invocation
        }


def parse_result(result: Mapping[str, Any]) -> Verdict:
    """A `sanitizationResult` → Verdict."""
    injection, rai, skipped = 0, {}, []
    sdp = malicious_uri = csam = False
    for name, wrapper in (result.get("filterResults") or {}).items():
        for kind, body in (wrapper or {}).items():
            if kind == "sdpFilterResult":  # one more level: inspectResult / deidentifyResult
                body = next(iter(body.values()), {}) if body else {}
            if body.get("executionState") == SKIPPED:
                skipped.append(name)
            matched = body.get("matchState") == MATCH
            if kind == "piAndJailbreakFilterResult" and matched:
                injection = level(body.get("confidenceLevel"))
            elif kind == "raiFilterResult":
                for category, r in (body.get("raiFilterTypeResults") or {}).items():
                    if r.get("matchState") == MATCH:
                        rai[category] = level(r.get("confidenceLevel"))
            elif kind == "sdpFilterResult":
                sdp = matched
            elif kind == "maliciousUriFilterResult":
                malicious_uri = matched
            elif kind == "csamFilterFilterResult":
                csam = matched
    return Verdict(
        invocation=str(result.get("invocationResult", "")),
        injection=injection,
        rai=rai,
        sdp=sdp,
        malicious_uri=malicious_uri,
        csam=csam,
        skipped=tuple(sorted(skipped)),
    )


class ModelArmor:
    """`sanitizeUserPrompt` against one template, with ADC (or the given credentials)."""

    def __init__(
        self,
        template: str,
        *,
        timeout_s: float = 5.0,
        credentials: Any = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        m = TEMPLATE.fullmatch(template)
        if not m:
            raise ValueError(f"not a template name: {template!r}")
        self.template = template
        self.location = m["location"]
        self.url = (
            f"https://modelarmor.{self.location}.rep.googleapis.com/v1/{template}"
            ":sanitizeUserPrompt"
        )
        self.timeout_s = timeout_s
        self._creds = credentials
        self._transport = transport
        self._lock = asyncio.Lock()
        self._client: httpx.AsyncClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def _http(self) -> httpx.AsyncClient:
        # A client's connections belong to the loop that opened them; eval runs and
        # tests start several loops in one process.
        loop = asyncio.get_running_loop()
        if self._client is None or self._loop is not loop:
            self._client = httpx.AsyncClient(transport=self._transport, timeout=self.timeout_s)
            self._loop = loop
            self._lock = asyncio.Lock()
        return self._client

    async def _headers(self) -> dict[str, str]:
        async with self._lock:
            if self._creds is None:
                self._creds, _ = await asyncio.to_thread(google.auth.default, scopes=SCOPES)
            if not self._creds.valid:
                request = google.auth.transport.requests.Request()
                await asyncio.to_thread(self._creds.refresh, request)
        headers: dict[str, str] = {}
        self._creds.apply(headers)  # Authorization, plus x-goog-user-project for user ADC
        return headers

    async def screen(
        self, text: str, *, multilang: bool = True, lang: str | None = None
    ) -> Verdict:
        """One text. `multilang` turns on Model Armor's multi-language detection
        (`lang`: the source language, if known)."""
        body: dict[str, Any] = {"userPromptData": {"text": text}}
        if multilang:
            meta: dict[str, Any] = {"enableMultiLanguageDetection": True}
            if lang:
                meta["sourceLanguage"] = lang
            body["multiLanguageDetectionMetadata"] = meta
        start = time.perf_counter()
        try:
            client = self._http()
            headers = await self._headers()
            resp = await client.post(self.url, json=body, headers=headers)
            if resp.status_code in RETRY_STATUS:
                await asyncio.sleep(0.5)
                resp = await client.post(self.url, json=body, headers=headers)
            resp.raise_for_status()
            verdict = parse_result(resp.json().get("sanitizationResult") or {})
        except Exception as exc:  # never raise: the caller decides what a failure means
            verdict = Verdict(error=f"{type(exc).__name__}: {str(exc)[:200]}")
        return replace(verdict, latency_ms=round((time.perf_counter() - start) * 1000, 1))


# --- the agent's input screen --------------------------------------------------------------

Mode = Literal["off", "log", "block"]
MODES: tuple[Mode, ...] = ("off", "log", "block")

# What the user reads when a message is stopped. No citations, so the UI shows no
# verification badge; `out_of_scope` gives it the "outside what this tool can answer" badge.
# The screen also matches requests for help with fraud (E7: fake contracts, sham
# marriage), so the text names both.
BLOCKED = {
    "en": (
        "An automatic safety check stopped this message, so I haven't answered it. It looks "
        "like an attempt to change how the assistant works (for example, to make it ignore "
        "its rules or reveal its setup), or like a request for help with something unlawful. "
        "Please ask your question about Swiss federal law again without such instructions. "
        "If you pasted a letter or a contract, you can describe what it says instead. If "
        "you have a problem with an authority, a lawyer or a legal-aid office can explain "
        "your lawful options. If this happened by mistake, try rephrasing."
    ),
    "de": (
        "Eine automatische Sicherheitsprüfung hat diese Nachricht gestoppt, deshalb habe ich "
        "sie nicht beantwortet. Sie sieht aus wie ein Versuch, die Arbeitsweise des "
        "Assistenten zu ändern (etwa, ihn seine Regeln ignorieren oder seine Einstellungen "
        "offenlegen zu lassen), oder wie eine Bitte um Hilfe bei etwas Rechtswidrigem. Bitte "
        "stellen Sie Ihre Frage zum Bundesrecht ohne solche Anweisungen noch einmal. Wenn Sie "
        "einen Brief oder Vertrag eingefügt haben, können Sie auch beschreiben, was darin "
        "steht. Wenn Sie ein Problem mit einer Behörde haben, kann Ihnen eine Anwältin, ein "
        "Anwalt oder eine Rechtsberatungsstelle Ihre legalen Möglichkeiten erklären. Falls "
        "das ein Irrtum war, formulieren Sie die Frage bitte um."
    ),
    "fr": (
        "Un contrôle de sécurité automatique a bloqué ce message, je n'y ai donc pas répondu. "
        "Il ressemble à une tentative de modifier le fonctionnement de l'assistant (par "
        "exemple lui faire ignorer ses règles ou révéler sa configuration) ou à une demande "
        "d'aide pour quelque chose d'illégal. Posez à nouveau votre question sur le droit "
        "fédéral, sans ces instructions. Si vous avez collé une lettre ou un contrat, vous "
        "pouvez aussi décrire ce qu'il contient. Si vous avez un problème avec une autorité, "
        "un avocat ou un service de consultation juridique peut vous expliquer vos options "
        "légales. S'il s'agit d'une erreur, reformulez votre question."
    ),
    "it": (
        "Un controllo di sicurezza automatico ha bloccato questo messaggio, quindi non ho "
        "risposto. Sembra un tentativo di cambiare il funzionamento dell'assistente (per "
        "esempio fargli ignorare le sue regole o rivelarne la configurazione) o una richiesta "
        "di aiuto per qualcosa di illecito. Riformuli la sua domanda sul diritto federale "
        "senza queste istruzioni. Se ha incollato una lettera o un contratto, può anche "
        "descriverne il contenuto. Se ha un problema con un'autorità, un avvocato o un "
        "servizio di consulenza giuridica può spiegarle le sue possibilità legali. Se si "
        "tratta di un errore, provi a riformularla."
    ),
}

# Frequent short words per language: enough to pick the refusal's language, nothing more.
_WORDS = {
    "de": "der die das und ist nicht ich mein meine mich mir ein eine zu mit auf den dem wie "
    "kann darf muss wenn bei von für sie es",
    "fr": "le la les et est pas je mon ma mes un une des du de que qui pour avec dans sur "
    "peut dois mais il elle ce cette",
    "it": "il lo la gli le e è non io mio mia un una di che per con su posso devo ma della "
    "del sono questo questa",
    "en": "the and is not i my me a an of to for with on can must if do does what how this "
    "that it you your",
}
_VOCAB = {lang: set(words.split()) for lang, words in _WORDS.items()}


def guess_lang(text: str) -> str:
    """de/fr/it/en by stopword hits; English on a tie (the agent's fallback language)."""
    tokens = re.findall(r"[a-zàâäçéèêëîïôöùûüœ]+", text.lower())
    scores = {lang: sum(t in vocab for t in tokens) for lang, vocab in _VOCAB.items()}
    best = max(scores.values())
    return "en" if scores["en"] == best else max(scores, key=lambda k: scores[k])


def blocked_answer(lang: str, flags: list[str]) -> Answer:
    lang = lang if lang in BLOCKED else "en"
    return Answer(
        language=lang,  # type: ignore[arg-type]
        answer_markdown=BLOCKED[lang],
        citations=[],
        clarifying_question=None,
        cantonal_note=None,
        follow_up_questions=[],
        confidence="low",
        out_of_scope=True,
        # Nothing was cited, so nothing failed: the verifier never ran.
        verification=Verification(status="passed", rounds=[]),
        screening=Screening(status="blocked", flags=flags),
    )


def user_text(content: types.Content | None) -> str:
    if not content or not content.parts:
        return ""
    return "\n".join(p.text for p in content.parts if p.text and not p.thought).strip()


class InputScreen:
    """`before_agent_callback`: screens each user message once, before any model call.

    `block` answers a message whose prompt-injection/jailbreak confidence reaches
    `min_level` with `blocked_answer` and ends the turn: no model call, no tool call,
    and (ADK skips `after_agent_callback` then) nothing sent to Memory Bank. `log`
    screens and logs only. Multi-language detection is on (E7: +3 of 58 attacks at
    medium, no false positive, ~50 ms). Only the injection filter decides: Responsible
    AI flags victims' questions (violence, harassment) and law text at low confidence,
    and catches no attack at medium or above that the injection filter misses (E7,
    ADR-032).

    Fails open: when Model Armor errors or times out the question goes to the agent,
    whose own defences (prompt rule, citation verifier) don't depend on it. Logs carry
    the verdict and latency, never the text."""

    def __init__(self, armor: ModelArmor | None, mode: Mode = "block", min_level: int = 2) -> None:
        if mode not in MODES:
            raise ValueError(f"MODEL_ARMOR_MODE must be one of {MODES}")
        self.armor = armor if mode != "off" else None
        self.mode = mode
        self.min_level = min_level

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> InputScreen:
        """`MODEL_ARMOR_TEMPLATE` (unset: off), `MODEL_ARMOR_MODE` (default block),
        `MODEL_ARMOR_MIN_LEVEL` low|medium|high (default medium)."""
        env = os.environ if env is None else env
        template = env.get("MODEL_ARMOR_TEMPLATE", "").strip()
        mode = (env.get("MODEL_ARMOR_MODE") or "block").strip().lower()
        min_level = level(env.get("MODEL_ARMOR_MIN_LEVEL") or "medium")
        armor = ModelArmor(template, timeout_s=3.0) if template else None
        return cls(armor, mode if armor else "off", min_level)  # type: ignore[arg-type]

    def as_dict(self) -> dict[str, str] | None:
        """The settings for eval reports; None when screening is off."""
        if self.armor is None:
            return None
        return {
            "template": self.armor.template,
            "mode": self.mode,
            "min_level": LEVEL_NAMES[self.min_level],
        }

    async def before_agent(self, callback_context: CallbackContext) -> types.Content | None:
        if self.armor is None:
            return None
        text = user_text(callback_context.user_content)
        if not text:
            return None
        verdict = await self.armor.screen(text, multilang=True)
        blocked = verdict.ok and verdict.injection >= self.min_level
        fields = json.dumps(
            {
                "model_armor": verdict.as_dict(),
                "flags": verdict.flags(self.min_level),
                "blocked": blocked and self.mode == "block",
                "mode": self.mode,
            }
        )
        if not verdict.ok:
            logger.warning("model armor unavailable, not screened: %s", fields)
        elif blocked:
            logger.warning("model armor match: %s", fields)
        else:
            logger.info("model armor clean: %s", fields)
        if not (blocked and self.mode == "block"):
            return None
        answer = blocked_answer(guess_lang(text), verdict.flags(self.min_level))
        return types.Content(role="model", parts=[types.Part(text=answer.model_dump_json())])
