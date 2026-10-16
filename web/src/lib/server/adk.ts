// Agent Runtime's :streamQuery output → the BFF's UI events.
//
// The stream is one ADK `Event` per line as a snake_case JSON dict (verified
// 2026-10-16: newline-delimited JSON even with `?alt=sse`; lib/lines.ts
// also accepts `data: ` prefixes). Tool calls become progress steps; the final
// text event is the verified answer JSON (agents/navigator/verifier.py).

import type { Answer, Step, UiEvent } from "@/lib/contract";

type Json = Record<string, unknown>;

interface Part {
  text?: string | null;
  thought?: boolean | null;
  function_call?: { name?: string; args?: Json } | null;
  function_response?: { name?: string; response?: Json } | null;
}

const CHECK_TOOL = "citation_check"; // agents/navigator/verifier.py

/** An error item in the stream (Agent Runtime reports failures in-band). */
export function streamError(item: Json): string | null {
  if ("author" in item) return null;
  if ("error" in item) return JSON.stringify(item.error).slice(0, 300);
  if ("code" in item && "message" in item) return String(item.message).slice(0, 300);
  return null;
}

function short(value: unknown, max = 120): string | undefined {
  if (typeof value !== "string" || !value.trim()) return undefined;
  const v = value.trim().replace(/\s+/g, " ");
  return v.length > max ? `${v.slice(0, max - 1)}…` : v;
}

function progress(step: Step, detail?: string): UiEvent {
  return detail ? { type: "progress", step, detail } : { type: "progress", step };
}

/** Progress events for one ADK event; the final answer text is returned separately. */
export function toProgress(event: Json): UiEvent[] {
  const parts = ((event.content as Json | undefined)?.parts ?? []) as Part[];
  const out: UiEvent[] = [];
  for (const part of parts) {
    const call = part.function_call;
    if (call?.name) {
      const args = call.args ?? {};
      if (call.name === "search_law") out.push(progress("search", short(args.query)));
      else if (call.name === "resolve_citation") out.push(progress("resolve", short(args.text)));
      else if (call.name === "get_toc" || call.name === "list_acts") out.push(progress("browse"));
      else if (call.name === CHECK_TOOL) out.push(progress("check"));
    }
    const resp = part.function_response;
    if (resp?.name === "get_article") {
      const r = resp.response ?? {};
      const label = [r.abbr ?? (r.sr ? `SR ${r.sr}` : null), r.label].filter(Boolean).join(" ");
      out.push(progress("read", short(label)));
    }
  }
  return out;
}

/** The final response text of an ADK event, or null (tool calls, thoughts, partials). */
export function finalText(event: Json): string | null {
  if (event.partial) return null;
  const parts = ((event.content as Json | undefined)?.parts ?? []) as Part[];
  if (parts.some((p) => p.function_call || p.function_response)) return null;
  const text = parts
    .filter((p) => p.text && !p.thought)
    .map((p) => p.text)
    .join("");
  return text.trim() ? text : null;
}

/** Parses and sanity-checks the verified answer JSON. */
export function parseAnswer(text: string): Answer | null {
  try {
    const a = JSON.parse(text) as Partial<Answer>;
    if (typeof a.answer_markdown !== "string" || !Array.isArray(a.citations)) return null;
    return {
      ...a,
      follow_up_questions: a.follow_up_questions ?? [],
      notice: a.notice ?? "Unofficial. Not legal advice. Sources: Fedlex (fedlex.admin.ch).",
    } as Answer;
  } catch {
    return null;
  }
}
