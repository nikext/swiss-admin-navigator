// The answer contract (docs/ARCHITECTURE.md §4) as the UI sees it, mirrored by hand from
// agents/navigator/contract.py, plus the events the BFF streams to the browser.

export type Lang = "de" | "fr" | "it" | "en";
export const LANGS: readonly Lang[] = ["en", "de", "fr", "it"];

export function isLang(value: unknown): value is Lang {
  return typeof value === "string" && (LANGS as readonly string[]).includes(value);
}

export interface Citation {
  ref: string;
  sr: string;
  article: string;
  paragraph: string | null;
  letter: string | null;
  quote_lang: Lang;
  quote: string | null; // null: removed by the verifier
  translation: string | null;
  abbr: string | null;
  url: string | null;
  as_of: string | null;
}

export interface Verification {
  status: "passed" | "passed_after_retry" | "degraded" | "unavailable";
  dropped: string[];
  repairs: string[];
}

export interface Answer {
  language: Lang;
  answer_markdown: string;
  citations: Citation[];
  clarifying_question: string | null;
  cantonal_note: string | null;
  follow_up_questions: string[];
  confidence: "high" | "medium" | "low";
  out_of_scope: boolean;
  verification: Verification;
  notice: string;
  /** Set when the agent's input screen (Model Armor, M10) stopped the question. */
  screening?: { status: "blocked"; flags: string[] } | null;
}

/** One article as the MCP server's get_article returns it (the fields the panel shows). */
export interface ArticleText {
  sr: string;
  abbr: string;
  act_title: string;
  label: string;
  lang: Lang;
  status: string;
  heading: string | null;
  heading_path: string[];
  paragraphs: { eid: string; num: string | null; text: string }[];
  text: string;
  url: string;
  as_of: string;
  available_langs: Lang[];
  fallback?: string;
}

export type Step = "search" | "resolve" | "read" | "browse" | "check";

/** What the BFF streams to the browser, one per SSE `data:` line. */
export type UiEvent =
  | { type: "session"; sessionId: string }
  | { type: "quota"; user: number; global: number }
  | { type: "progress"; step: Step; detail?: string }
  | { type: "answer"; answer: Answer }
  | { type: "error"; code: ErrorCode; message: string };

export type ErrorCode =
  "unauthorized" | "quota_user" | "quota_global" | "bad_request" | "upstream" | "no_answer";
