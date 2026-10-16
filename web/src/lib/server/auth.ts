// Access code → a signed, httpOnly session cookie that carries an anonymous user id.
//
// The cookie key is derived from the access code, so rotating the code (a new
// Secret Manager version) logs everyone out. The anonymous id keys the per-user
// quota and the Agent Runtime sessions (`web-<uid>`); ADK refuses a session
// that belongs to another user id, so a client can't read someone else's chat.

import { createHash, createHmac, randomBytes, timingSafeEqual } from "node:crypto";

export const COOKIE = "nav_session";
export const COOKIE_MAX_AGE = 30 * 24 * 3600;

export interface Identity {
  uid: string;
  iat: number;
}

function key(accessCode: string): Buffer {
  return createHmac("sha256", accessCode).update("swiss-nav-web cookie v1").digest();
}

function sign(payload: string, accessCode: string): string {
  return createHmac("sha256", key(accessCode)).update(payload).digest("base64url");
}

export function checkCode(given: string, accessCode: string): boolean {
  // Compare digests: equal length, constant time, no length leak.
  const a = createHash("sha256").update(given.trim()).digest();
  const b = createHash("sha256").update(accessCode).digest();
  return timingSafeEqual(a, b);
}

export function newIdentity(now = Date.now()): Identity {
  return { uid: randomBytes(12).toString("base64url"), iat: Math.floor(now / 1000) };
}

export function encodeCookie(id: Identity, accessCode: string): string {
  const payload = Buffer.from(JSON.stringify(id)).toString("base64url");
  return `${payload}.${sign(payload, accessCode)}`;
}

export function decodeCookie(
  value: string | undefined,
  accessCode: string,
  now = Date.now(),
): Identity | null {
  if (!value) return null;
  const [payload, mac] = value.split(".");
  if (!payload || !mac) return null;
  const expected = Buffer.from(sign(payload, accessCode));
  const given = Buffer.from(mac);
  if (expected.length !== given.length || !timingSafeEqual(expected, given)) return null;
  try {
    const id = JSON.parse(Buffer.from(payload, "base64url").toString()) as Identity;
    if (typeof id.uid !== "string" || typeof id.iat !== "number") return null;
    if (now / 1000 - id.iat > COOKIE_MAX_AGE) return null;
    return id;
  } catch {
    return null;
  }
}

/** The Agent Runtime user id for a web visitor. */
export function agentUserId(id: Identity): string {
  return `web-${id.uid}`;
}

/**
 * The client IP behind Cloud Run's front end: the last X-Forwarded-For hop is the
 * one Google appended; earlier hops are client-supplied and can be forged.
 */
export function clientIp(headers: Headers): string {
  const hops = (headers.get("x-forwarded-for") ?? "").split(",").map((h) => h.trim());
  return hops.filter(Boolean).at(-1) ?? "local";
}

/** A fixed-window counter per key, in process memory (one Cloud Run instance's view). */
export class WindowLimiter {
  private hits = new Map<string, { start: number; count: number }>();

  constructor(
    private readonly limit: number,
    private readonly windowMs: number,
  ) {}

  /** Counts one hit; false when the key is over the limit in the current window. */
  hit(key: string, now = Date.now()): boolean {
    const entry = this.hits.get(key);
    if (!entry || now - entry.start >= this.windowMs) {
      this.hits.set(key, { start: now, count: 1 });
      if (this.hits.size > 10_000) this.prune(now);
      return true;
    }
    entry.count += 1;
    return entry.count <= this.limit;
  }

  private prune(now: number): void {
    for (const [k, v] of this.hits) if (now - v.start >= this.windowMs) this.hits.delete(k);
  }
}
