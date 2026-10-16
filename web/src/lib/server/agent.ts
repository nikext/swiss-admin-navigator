// Agent Runtime REST client (docs/GCP.md §4). On Cloud Run the token is the
// swiss-nav-web@ service account's (metadata server); locally it is ADC.
//
// Sessions: AdkApp's `async_create_session` / `async_delete_session` through
// `:query`; `ttl` is passed to the Sessions API, which requires at least 24 h
// (verified 2026-10-16: "`ttl` must be at least 24 hours"). Questions:
// `:streamQuery` with `async_stream_query`, one ADK event per line.

import { GoogleAuth } from "google-auth-library";

import { config } from "@/lib/server/config";
import { streamError } from "@/lib/server/adk";
import { LineSplitter } from "@/lib/lines";

const auth = new GoogleAuth({ scopes: ["https://www.googleapis.com/auth/cloud-platform"] });

export const SESSION_TTL = "86400s";

export class UpstreamError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

function base(): string {
  const { project, agentLocation, agentRuntimeId } = config();
  const host = `https://${agentLocation}-aiplatform.googleapis.com/v1`;
  const name = agentRuntimeId.startsWith("projects/")
    ? agentRuntimeId
    : `projects/${project}/locations/${agentLocation}/reasoningEngines/${agentRuntimeId}`;
  return `${host}/${name}`;
}

async function headers(): Promise<Record<string, string>> {
  const token = await auth.getAccessToken();
  if (!token) throw new UpstreamError("no access token (ADC / metadata server)", 500);
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

const RETRYABLE = new Set([429, 500, 502, 503, 504]);

/** POST with up to two retries on 429/5xx before any response body was consumed. */
async function post(url: string, body: unknown, signal?: AbortSignal): Promise<Response> {
  let last: Response | null = null;
  for (let attempt = 0; attempt < 3; attempt++) {
    if (attempt > 0) await sleep(500 * 2 ** attempt, signal);
    last = await fetch(url, {
      method: "POST",
      headers: await headers(),
      body: JSON.stringify(body),
      signal,
    });
    if (!RETRYABLE.has(last.status)) return last;
    await last.body?.cancel();
  }
  return last as Response;
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal?.addEventListener("abort", () => {
      clearTimeout(t);
      reject(signal.reason);
    });
  });
}

async function query(method: string, input: Record<string, unknown>): Promise<unknown> {
  const resp = await post(`${base()}:query`, { class_method: method, input });
  const data = (await resp.json().catch(() => ({}))) as { output?: unknown; error?: unknown };
  if (!resp.ok || data.error) {
    throw new UpstreamError(`${method}: ${JSON.stringify(data.error ?? resp.status)}`, resp.status);
  }
  return data.output;
}

export async function createSession(userId: string): Promise<string> {
  const out = (await query("async_create_session", { user_id: userId, ttl: SESSION_TTL })) as {
    id?: string;
  };
  if (!out?.id) throw new UpstreamError("async_create_session returned no id", 502);
  return out.id;
}

export async function deleteSession(userId: string, sessionId: string): Promise<void> {
  await query("async_delete_session", { user_id: userId, session_id: sessionId });
}

/** The agent's events for one message, parsed; an in-band error item throws. */
export async function* streamQuery(
  userId: string,
  sessionId: string,
  message: string,
  signal: AbortSignal,
): AsyncGenerator<Record<string, unknown>> {
  const resp = await post(
    `${base()}:streamQuery?alt=sse`,
    {
      class_method: "async_stream_query",
      input: { user_id: userId, session_id: sessionId, message },
    },
    signal,
  );
  if (!resp.ok || !resp.body) {
    const text = await resp.text().catch(() => "");
    throw new UpstreamError(`streamQuery ${resp.status}: ${text.slice(0, 300)}`, resp.status);
  }
  const lines = new LineSplitter();
  const reader = resp.body.getReader();
  try {
    for (;;) {
      const { done, value } = await reader.read();
      const batch = done ? lines.flush() : lines.push(value);
      for (const line of batch) {
        let item: Record<string, unknown>;
        try {
          item = JSON.parse(line) as Record<string, unknown>;
        } catch {
          throw new UpstreamError(`unparseable stream item: ${line.slice(0, 200)}`, 502);
        }
        const err = streamError(item);
        if (err) throw new UpstreamError(`agent error: ${err}`, 502);
        yield item;
      }
      if (done) return;
    }
  } finally {
    reader.releaseLock();
  }
}
