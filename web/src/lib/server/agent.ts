// Agent Runtime REST client (docs/GCP.md §4). On Cloud Run the token is the
// swiss-nav-web@ service account's (metadata server); locally it is ADC.
//
// Sessions: AdkApp's `async_create_session` / `async_delete_session` through
// `:query`; `ttl` is passed to the Sessions API, which requires at least 24 h
// (verified 2026-10-16: "`ttl` must be at least 24 hours"). Questions:
// `:streamQuery` with `async_stream_query`, one ADK event per line.
//
// Memory (M7, ADR-029): the session's initial state carries `memory_opt_in`, the
// only switch the agent obeys; Memory Bank's REST API (v1beta1, the version the
// Python SDK uses) lists and purges a visitor's memories by `scope.user_id`.

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

function base(version = "v1"): string {
  const { project, agentLocation, agentRuntimeId } = config();
  const host = `https://${agentLocation}-aiplatform.googleapis.com/${version}`;
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

export async function createSession(
  userId: string,
  state: Record<string, unknown> = {},
): Promise<string> {
  const out = (await query("async_create_session", {
    user_id: userId,
    ttl: SESSION_TTL,
    state,
  })) as { id?: string };
  if (!out?.id) throw new UpstreamError("async_create_session returned no id", 502);
  return out.id;
}

/**
 * The visitor's session ids, from the Sessions REST API (no agent container, so no
 * cold start; `async_list_sessions` through `:query` took 23 s from idle).
 */
export async function listSessions(userId: string): Promise<string[]> {
  const ids: string[] = [];
  let pageToken = "";
  for (let page = 0; page < 10; page++) {
    const params = new URLSearchParams({
      filter: `user_id="${checkedUser(userId)}"`,
      pageSize: "100",
    });
    if (pageToken) params.set("pageToken", pageToken);
    const resp = await fetch(`${base("v1beta1")}/sessions?${params}`, { headers: await headers() });
    const data = (await resp.json().catch(() => ({}))) as {
      sessions?: { name?: string; userId?: string }[];
      nextPageToken?: string;
      error?: unknown;
    };
    if (!resp.ok)
      throw new UpstreamError(
        `list sessions: ${JSON.stringify(data.error ?? resp.status)}`,
        resp.status,
      );
    for (const s of data.sessions ?? []) {
      if (s.name && s.userId === userId) ids.push(s.name.split("/").at(-1)!);
    }
    pageToken = data.nextPageToken ?? "";
    if (!pageToken) break;
  }
  return ids;
}

/**
 * Deletes a session over REST. The REST API doesn't check the owner, so this is only
 * for ids from `listSessions(userId)`; a browser-supplied id goes through
 * `deleteSession`, where ADK refuses another user's session.
 */
export async function deleteListedSession(_userId: string, sessionId: string): Promise<void> {
  if (!SESSION_ID_RE.test(sessionId)) throw new Error("bad session id");
  const resp = await fetch(`${base("v1beta1")}/sessions/${sessionId}`, {
    method: "DELETE",
    headers: await headers(),
  });
  if (!resp.ok && resp.status !== 404) {
    throw new UpstreamError(`delete session: ${resp.status}`, resp.status);
  }
}

const SESSION_ID_RE = /^[0-9]{1,30}$/;

function checkedUser(userId: string): string {
  if (!/^[\w-]{1,80}$/.test(userId)) throw new Error("bad user id");
  return userId;
}

export async function deleteSession(userId: string, sessionId: string): Promise<void> {
  await query("async_delete_session", { user_id: userId, session_id: sessionId });
}

/** Memory Bank's filter for everything stored about one visitor (any app name). */
export function userFilter(userId: string): string {
  return `scope.user_id="${checkedUser(userId)}"`;
}

export async function listMemories(userId: string): Promise<Record<string, unknown>[]> {
  const out: Record<string, unknown>[] = [];
  let pageToken = "";
  for (let page = 0; page < 10; page++) {
    const params = new URLSearchParams({ filter: userFilter(userId), pageSize: "100" });
    if (pageToken) params.set("pageToken", pageToken);
    const resp = await fetch(`${base("v1beta1")}/memories?${params}`, { headers: await headers() });
    const data = (await resp.json().catch(() => ({}))) as {
      memories?: Record<string, unknown>[];
      nextPageToken?: string;
      error?: unknown;
    };
    if (!resp.ok)
      throw new UpstreamError(
        `list memories: ${JSON.stringify(data.error ?? resp.status)}`,
        resp.status,
      );
    out.push(...(data.memories ?? []));
    pageToken = data.nextPageToken ?? "";
    if (!pageToken) break;
  }
  return out;
}

/** Deletes every memory of the visitor and waits for the purge to finish (≤ 30 s). */
export async function purgeMemories(userId: string): Promise<void> {
  const resp = await post(`${base("v1beta1")}/memories:purge`, {
    filter: userFilter(userId),
    force: true,
  });
  let op = (await resp.json().catch(() => ({}))) as {
    name?: string;
    done?: boolean;
    error?: unknown;
  };
  if (!resp.ok || op.error) {
    throw new UpstreamError(
      `purge memories: ${JSON.stringify(op.error ?? resp.status)}`,
      resp.status,
    );
  }
  const { agentLocation } = config();
  for (let i = 0; !op.done && op.name && i < 30; i++) {
    await sleep(1_000);
    const r = await fetch(`https://${agentLocation}-aiplatform.googleapis.com/v1beta1/${op.name}`, {
      headers: await headers(),
    });
    op = (await r.json().catch(() => ({}))) as typeof op;
    if (op.error) throw new UpstreamError(`purge memories: ${JSON.stringify(op.error)}`, 502);
  }
  if (!op.done) throw new UpstreamError("purge memories: not finished after 30 s", 504);
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
