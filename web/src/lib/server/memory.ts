// Opt-in memory for the web (M7, ADR-029): the switch, "What I remember" and "Forget me".
//
// The switch is a cookie the BFF reads when it creates an Agent Runtime session;
// the session's initial state (`memory_opt_in`) is what the agent obeys, and the
// browser can't set it. Changing the switch or forgetting ends all of the
// visitor's sessions, so no open conversation keeps the old setting.
// Kept free of Next.js and GCP so it is unit-tested with fakes (memory.test.ts).

import { cleanProfile, type Profile } from "@/lib/profile";

export const MEMORY_COOKIE = "nav_memory";
export const OPT_IN = "memory_opt_in"; // agents/navigator/memory.py OPT_IN
export const SCHEMA_ID = "resident-profile"; // agents/navigator/memory.py SCHEMA_ID

export interface MemoryDeps {
  listMemories(userId: string): Promise<Record<string, unknown>[]>;
  purgeMemories(userId: string): Promise<void>;
  listSessions(userId: string): Promise<string[]>;
  deleteSession(userId: string, sessionId: string): Promise<void>;
}

/**
 * The switch is on when the cookie holds the visitor's own anonymous id, so a
 * new identity (signed out and back in) never inherits someone's opt-in.
 */
export function optedIn(cookieValue: string | undefined, uid: string): boolean {
  return Boolean(uid) && cookieValue === uid;
}

export function sessionState(enabled: boolean): Record<string, unknown> {
  return { [OPT_IN]: enabled };
}

/**
 * The visitor's structured profile, from Memory Bank's per-field memories
 * (`structuredContent.data`), older values overwritten by newer ones. Only
 * whitelisted values survive; the free-text `context` Memory Bank keeps next
 * to each field is never shown.
 */
export function profileOf(memories: Record<string, unknown>[]): Profile {
  const fields = memories
    .filter((m) => {
      const sc = m.structuredContent as { schemaId?: string } | undefined;
      return m.memoryType === "STRUCTURED_PROFILE" && sc?.schemaId === SCHEMA_ID;
    })
    .sort((a, b) => String(a.updateTime ?? "").localeCompare(String(b.updateTime ?? "")));
  const merged: Record<string, unknown> = {};
  for (const m of fields) Object.assign(merged, (m.structuredContent as { data?: object }).data);
  return cleanProfile(merged);
}

/** Ends every Agent Runtime session of the visitor; returns how many. */
export async function endSessions(deps: MemoryDeps, userId: string): Promise<number> {
  const ids = await deps.listSessions(userId);
  await Promise.all(ids.map((id) => deps.deleteSession(userId, id).catch(() => {})));
  return ids.length;
}

/** "Forget me": all memories and all sessions; then checks nothing is left. */
export async function forget(
  deps: MemoryDeps,
  userId: string,
): Promise<{ sessions: number; remaining: number }> {
  await deps.purgeMemories(userId);
  const sessions = await endSessions(deps, userId);
  const remaining = (await deps.listMemories(userId)).length;
  return { sessions, remaining };
}
