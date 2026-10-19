import { describe, expect, it } from "vitest";

import type { Answer, Citation } from "@/lib/contract";
import { clock, count, longDate, quoted, sourceStats, trailSummary } from "@/lib/present";

const cite = (ref: string, quote: string | null): Citation => ({
  ref,
  sr: "220",
  article: "Art. 257e",
  paragraph: "2",
  letter: null,
  quote_lang: "de",
  quote,
  translation: null,
  abbr: "OR",
  url: null,
  as_of: "2026-10-01",
});

const answer = (status: Answer["verification"]["status"], quotes: (string | null)[]): Answer => ({
  language: "en",
  answer_markdown: "",
  citations: quotes.map((q, i) => cite(String(i + 1), q)),
  clarifying_question: null,
  cantonal_note: null,
  follow_up_questions: [],
  confidence: "high",
  out_of_scope: false,
  verification: { status, dropped: [], repairs: [] },
  notice: "",
});

describe("clock", () => {
  it("formats minutes and zero-padded seconds", () => {
    expect(clock(0)).toBe("0:00");
    expect(clock(42_900)).toBe("0:42");
    expect(clock(65_000)).toBe("1:05");
    expect(clock(-5)).toBe("0:00");
  });
});

describe("trailSummary", () => {
  it("counts distinct articles read and re-checks", () => {
    expect(
      trailSummary([
        { step: "search", detail: "deposit", at: 1 },
        { step: "read", detail: "OR Art. 257e", at: 2 },
        { step: "read", detail: "OR Art. 257", at: 3 },
        { step: "check", at: 4 },
        { step: "read", detail: "OR Art. 257e", at: 5 },
      ]),
    ).toEqual({ articles: 2, corrections: 1 });
    expect(trailSummary([])).toEqual({ articles: 0, corrections: 0 });
  });
});

describe("longDate", () => {
  it("writes the date out in the UI language without a time-zone shift", () => {
    expect(longDate("2026-10-01", "en")).toBe("1 October 2026");
    expect(longDate("2026-10-01", "en", true)).toBe("1 Oct 2026");
    expect(longDate("2026-10-01", "de")).toBe("1. Oktober 2026");
    expect(longDate("not a date", "fr")).toBe("not a date");
  });
});

describe("count", () => {
  it("groups thousands per locale", () => {
    expect(count(2000, "en")).toBe("2,000");
    expect(count(1912, "de")).toMatch(/^1.912$/);
  });
});

describe("quoted", () => {
  it("uses each language's quotation marks", () => {
    expect(quoted("Text", "de")).toBe("„Text“");
    expect(quoted("texte", "fr")).toBe("« texte »");
    expect(quoted("testo", "it")).toBe("« testo »");
    expect(quoted("text", "en")).toBe("“text”");
  });
});

describe("sourceStats", () => {
  it("counts verified and removed quotes", () => {
    expect(sourceStats(answer("passed", ["a", "b", "c"]))).toEqual({
      total: 3,
      verified: 3,
      removed: 0,
      checked: true,
    });
    expect(sourceStats(answer("degraded", ["a", null]))).toEqual({
      total: 2,
      verified: 1,
      removed: 1,
      checked: true,
    });
  });

  it("marks nothing verified when the verifier did not run", () => {
    expect(sourceStats(answer("unavailable", ["a", "b"]))).toEqual({
      total: 2,
      verified: 0,
      removed: 0,
      checked: false,
    });
  });
});
