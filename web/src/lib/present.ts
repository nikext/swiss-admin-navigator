// Pure presentation helpers for the chat UI: the research trail, clock and date
// formats, typographic quotes per language, and what the verifier did to the sources.

import type { Answer, Lang, Step } from "@/lib/contract";

/** One progress event as the browser keeps it: `at` is ms since the question was sent. */
export interface TrailStep {
  step: Step;
  detail?: string;
  at: number;
}

/** "0:42", "1:05", "12:00" from milliseconds. */
export function clock(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

/** What the collapsed trail says: distinct articles read and verifier re-checks. */
export function trailSummary(steps: TrailStep[]): { articles: number; corrections: number } {
  const reads = steps.filter((s) => s.step === "read");
  const distinct = new Set(reads.map((s) => s.detail ?? `#${s.at}`));
  return {
    articles: distinct.size,
    corrections: steps.filter((s) => s.step === "check").length,
  };
}

const LOCALES: Record<Lang, string> = { en: "en-GB", de: "de-CH", fr: "fr-CH", it: "it-CH" };

/** "1 October 2026" (or "1 Oct 2026" when short) from an ISO date, in the UI language. */
export function longDate(iso: string, lang: Lang, short = false): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return iso;
  const date = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
  return new Intl.DateTimeFormat(LOCALES[lang], {
    day: "numeric",
    month: short ? "short" : "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

/** "1 912" style grouping for the character counter. */
export function count(n: number, lang: Lang): string {
  return new Intl.NumberFormat(LOCALES[lang]).format(n);
}

/** Law text in the quotation marks of its language: „…“ DE, « … » FR/IT, “…” EN. */
export function quoted(text: string, lang: Lang): string {
  if (lang === "de") return `„${text}“`;
  if (lang === "fr" || lang === "it") return `« ${text} »`;
  return `“${text}”`;
}

export interface SourceStats {
  total: number;
  verified: number;
  removed: number;
  /** false: the verifier could not run, so no quote is marked verified. */
  checked: boolean;
}

/** The verifier replaces each quote with the exact source span, or null if it failed. */
export function sourceStats(answer: Answer): SourceStats {
  const total = answer.citations.length;
  const removed = answer.citations.filter((c) => !c.quote).length;
  const checked = (answer.verification?.status ?? "unavailable") !== "unavailable";
  return { total, verified: checked ? total - removed : 0, removed, checked };
}

/** Quotes longer than this start clamped to three lines in the sources list. */
export const CLAMP_CHARS = 240;

/** From this many characters on, the composer shows a counter (max 2000). */
export const COUNTER_FROM = 1800;
export const MAX_CHARS = 2000;
