import type { UiEvent } from "@/lib/contract";
import { createSession, streamQuery } from "@/lib/server/agent";
import { agentUserId } from "@/lib/server/auth";
import { runChat } from "@/lib/server/chat";
import { config } from "@/lib/server/config";
import { fail, identify, log, readJson, SESSION_ID, unauthorized } from "@/lib/server/http";
import { zurichDay } from "@/lib/server/quota";
import { quotaStore } from "@/lib/server/stores";

export const dynamic = "force-dynamic";
// Answers take 40–70 s at the median and up to ~3 min (ADR-027); Cloud Run's
// request timeout is set to match (infra/deploy_web.sh).
export const maxDuration = 300;

const MAX_MESSAGE = 2_000;
const KEEPALIVE_MS = 15_000;

/** Ask the navigator; the response is SSE, one UiEvent per `data:` line. */
export async function POST(req: Request): Promise<Response> {
  const id = await identify();
  if (!id) return unauthorized();
  const body = await readJson(req);
  const message = typeof body?.message === "string" ? body.message.trim() : "";
  const given = typeof body?.sessionId === "string" ? body.sessionId : null;
  if (!message || message.length > MAX_MESSAGE) {
    return fail(400, "bad_request", `message must be 1–${MAX_MESSAGE} characters`);
  }
  if (given !== null && !SESSION_ID.test(given)) return fail(400, "bad_request", "bad session id");

  const c = config();
  const day = zurichDay();
  const quota = await quotaStore().consume(day, id.uid, {
    user: c.userDailyQuota,
    global: c.globalDailyCap,
  });
  if (!quota.ok) {
    log("WARNING", "quota exhausted", { reason: quota.reason, uid: id.uid });
    return Response.json(
      { code: quota.reason, message: "daily limit reached", remaining: quota.remaining },
      { status: 429, headers: { "Cache-Control": "no-store" } },
    );
  }

  const encoder = new TextEncoder();
  const started = Date.now();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      let open = true;
      const write = (text: string) => {
        if (!open) return;
        try {
          controller.enqueue(encoder.encode(text));
        } catch {
          open = false; // the browser went away
        }
      };
      const send = (e: UiEvent) => write(`data: ${JSON.stringify(e)}\n\n`);
      // Comments keep proxies from closing a quiet stream while the agent thinks.
      const keepalive = setInterval(() => write(": keepalive\n\n"), KEEPALIVE_MS);

      send({ type: "quota", ...quota.remaining });
      const out = await runChat(
        { createSession, streamQuery },
        agentUserId(id),
        message,
        given,
        req.signal,
        send,
      );
      clearInterval(keepalive);
      if (!out.answer && !out.agentWorked)
        await quotaStore()
          .refund(day, id.uid)
          .catch(() => {});
      log(out.answer ? "INFO" : "ERROR", "chat", {
        uid: id.uid,
        sessionId: out.sessionId,
        ms: Date.now() - started,
        answered: Boolean(out.answer),
        verification: out.answer?.verification?.status,
        citations: out.answer?.citations.length,
        aborted: req.signal.aborted,
        error: out.error,
      });
      if (open) controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-store, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}
