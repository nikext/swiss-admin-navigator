// Citation markers in answer_markdown ("[1]", "[1, 2]", "[1][2]") → links the
// Markdown renderer turns into chips. Only refs that exist in `citations` become
// chips (the verifier may have dropped some); anything else stays text.

import type { Citation } from "@/lib/contract";

export const CITE_PREFIX = "#cite-";

const MARKER = /\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\](?!\()/g;

export function linkCitations(markdown: string, refs: Iterable<string>): string {
  const known = new Set(refs);
  return markdown.replace(MARKER, (whole, inner: string) => {
    const nums = inner.split(",").map((n) => n.trim());
    if (!nums.every((n) => known.has(n))) return whole;
    return nums.map((n) => `[${n}](${CITE_PREFIX}${n})`).join("");
  });
}

/** "OR Art. 257e para. 2 let. a" in the UI's abbreviations. */
export function citationLabel(c: Citation, para: string, letter: string): string {
  const act = c.abbr ?? `SR ${c.sr}`;
  const pin = [c.paragraph && `${para} ${c.paragraph}`, c.letter && `${letter} ${c.letter}`]
    .filter(Boolean)
    .join(" ");
  return [act, c.article, pin].filter(Boolean).join(" ");
}
