// One question: session → Agent Runtime stream → UI events, with the quota refund rule.
//
// Kept free of Next.js and GCP so the relay logic is unit-tested with fakes
// (chat.test.ts); app/api/chat/route.ts wires in the real agent and stores.

import type { Answer, UiEvent } from "@/lib/contract";
import { finalText, parseAnswer, toProgress } from "@/lib/server/adk";

export interface ChatDeps {
  createSession(userId: string): Promise<string>;
  streamQuery(
    userId: string,
    sessionId: string,
    message: string,
    signal: AbortSignal,
  ): AsyncIterable<Record<string, unknown>>;
}

export interface ChatOutcome {
  sessionId: string | null;
  answer: Answer | null;
  error: string | null;
  /** True if the agent did any work (a tool call or model output): the quota stays used. */
  agentWorked: boolean;
}

/**
 * Streams one question. A given session id that yields nothing (Agent Runtime
 * answers an expired, deleted or foreign session with an empty 200 stream,
 * verified 2026-10-16) or fails before the first event is replaced once by a
 * new session, and the browser is told about the new id. The new session has no
 * history: the agent then answers the question on its own.
 */
export async function runChat(
  deps: ChatDeps,
  userId: string,
  message: string,
  sessionId: string | null,
  signal: AbortSignal,
  send: (e: UiEvent) => void,
): Promise<ChatOutcome> {
  const out: ChatOutcome = { sessionId, answer: null, error: null, agentWorked: false };
  let raw: string | null = null;

  const attempt = async (sid: string): Promise<void> => {
    for await (const item of deps.streamQuery(userId, sid, message, signal)) {
      out.agentWorked = true;
      for (const e of toProgress(item)) send(e);
      raw = finalText(item) ?? raw;
    }
  };
  const fresh = async (): Promise<void> => {
    out.sessionId = await deps.createSession(userId);
    send({ type: "session", sessionId: out.sessionId });
    await attempt(out.sessionId);
  };

  try {
    if (!out.sessionId) {
      await fresh();
    } else {
      try {
        await attempt(out.sessionId);
      } catch (err) {
        if (out.agentWorked || signal.aborted) throw err;
      }
      if (!out.agentWorked && !signal.aborted) await fresh();
    }
  } catch (err) {
    out.error = String(err instanceof Error ? err.message : err).slice(0, 500);
  }

  if (raw) out.answer = parseAnswer(raw);
  if (out.answer) {
    send({ type: "answer", answer: out.answer });
  } else if (!signal.aborted) {
    const failed = out.error !== null; // the stream broke, vs. ended without a usable answer
    out.error ??= raw ? "final answer is not valid JSON" : "no final answer";
    send({
      type: "error",
      code: failed ? "upstream" : "no_answer",
      message: "The assistant could not finish this answer. Please try again.",
    });
  }
  return out;
}
