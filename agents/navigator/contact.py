"""Contact details in an answer: street addresses, postcodes, phone numbers, web addresses.

The corpus is federal law, so none of these come from the tools; when an answer
has them, the model wrote them from memory (issue #7: an invented address for
a cantonal office). The verifier sends such drafts back, and the eval counts
them in final answers. Fedlex links are allowed.
"""

from __future__ import annotations

import re

STREET = re.compile(
    r"\b(?:Via|Viale|Rue|Route|Avenue|Av\.|Chemin|Place|Quai|Boulevard)\s+"
    r"[^\d\n,;()]{2,40}?\s\d{1,4}[a-z]?\b"
    r"|\b[\wÀ-ÿ-]+(?:strasse|straße|gasse|weg|platz|rain|quai)\s\d{1,4}[a-z]?\b",
    re.IGNORECASE,
)
POSTCODE = re.compile(r"(?:,\s*|\bCH-)[1-9]\d{3}\s+[A-ZÀ-Ý][\wÀ-ÿ-]+")
PHONE = re.compile(r"(?:\+41[\s.]?\d{2}|\b0\d{2})[\s.]?\d{3}[\s.]?\d{2}[\s.]?\d{2}\b")
WEB = re.compile(
    r"\b(?:https?://)?(?:[a-z0-9-]+\.)+(?:ch|swiss|com|org|net)\b(?:/[\w./-]*)?", re.IGNORECASE
)
PATTERNS = {
    "street address": STREET,
    "postcode": POSTCODE,
    "phone number": PHONE,
    "web address": WEB,
}
FIELDS = ("answer_markdown", "clarifying_question", "cantonal_note")


def contact_details(text: str) -> list[tuple[str, str]]:
    """(kind, matched text) for every contact detail in `text`, Fedlex links excepted."""
    found = []
    for kind, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            if "fedlex" not in m.group(0).lower():
                found.append((kind, m.group(0).strip(", ").rstrip(".:;")))
    return found


def answer_contact_details(answer: dict[str, object]) -> list[tuple[str, str]]:
    """Contact details in the user-facing text fields of an answer or draft."""
    text = "\n".join(str(answer.get(f) or "") for f in FIELDS)
    return contact_details(text)
