// Daily question quotas: per visitor and for the whole app (the cost cap).
//
// One question costs about CHF 0.03–0.04 in model calls (ADR-027), so the global
// daily cap bounds the demo's spend whatever happens to the access code. Days are
// Zürich calendar days. Firestore keeps the counters (database FIRESTORE_DATABASE,
// collection `quota`, one doc per day and key, updated in a transaction);
// QUOTA_BACKEND=memory is for local dev and tests.

import type { Firestore } from "@google-cloud/firestore";

export interface Limits {
  user: number;
  global: number;
}

export type QuotaResult =
  | { ok: true; remaining: Limits }
  | { ok: false; reason: "quota_user" | "quota_global"; remaining: Limits };

export interface QuotaStore {
  /** Atomically checks both counters and, if both are under their limit, adds one. */
  consume(day: string, uid: string, limits: Limits): Promise<QuotaResult>;
  /** Gives one back (the agent failed before answering). */
  refund(day: string, uid: string): Promise<void>;
  peek(day: string, uid: string, limits: Limits): Promise<Limits>;
}

/** YYYY-MM-DD in Europe/Zurich. */
export function zurichDay(now = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Zurich",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
}

export function decide(used: Limits, limits: Limits): QuotaResult {
  const remaining = (u: Limits): Limits => ({
    user: Math.max(0, limits.user - u.user),
    global: Math.max(0, limits.global - u.global),
  });
  if (used.global >= limits.global) {
    return { ok: false, reason: "quota_global", remaining: remaining(used) };
  }
  if (used.user >= limits.user) {
    return { ok: false, reason: "quota_user", remaining: remaining(used) };
  }
  return { ok: true, remaining: remaining({ user: used.user + 1, global: used.global + 1 }) };
}

export class MemoryQuota implements QuotaStore {
  private counts = new Map<string, number>();

  private used(day: string, uid: string): Limits {
    return {
      user: this.counts.get(`${day}/u/${uid}`) ?? 0,
      global: this.counts.get(`${day}/global`) ?? 0,
    };
  }

  private add(day: string, uid: string, delta: number): void {
    for (const k of [`${day}/u/${uid}`, `${day}/global`]) {
      this.counts.set(k, Math.max(0, (this.counts.get(k) ?? 0) + delta));
    }
  }

  async consume(day: string, uid: string, limits: Limits): Promise<QuotaResult> {
    const result = decide(this.used(day, uid), limits);
    if (result.ok) this.add(day, uid, 1);
    return result;
  }

  async refund(day: string, uid: string): Promise<void> {
    this.add(day, uid, -1);
  }

  async peek(day: string, uid: string, limits: Limits): Promise<Limits> {
    const used = this.used(day, uid);
    return {
      user: Math.max(0, limits.user - used.user),
      global: Math.max(0, limits.global - used.global),
    };
  }
}

export class FirestoreQuota implements QuotaStore {
  constructor(private readonly db: Firestore) {}

  private refs(day: string, uid: string) {
    const col = this.db.collection("quota");
    // A day's docs expire via the `expires` field (Firestore TTL policy on `quota`).
    return { user: col.doc(`${day}_u_${uid}`), global: col.doc(`${day}_global`) };
  }

  async consume(day: string, uid: string, limits: Limits): Promise<QuotaResult> {
    const refs = this.refs(day, uid);
    return this.db.runTransaction(async (tx) => {
      const [u, g] = await tx.getAll(refs.user, refs.global);
      const used = { user: Number(u?.get("count") ?? 0), global: Number(g?.get("count") ?? 0) };
      const result = decide(used, limits);
      if (result.ok) {
        const expires = expiry(day);
        tx.set(refs.user, { count: used.user + 1, day, expires }, { merge: true });
        tx.set(refs.global, { count: used.global + 1, day, expires }, { merge: true });
      }
      return result;
    });
  }

  async refund(day: string, uid: string): Promise<void> {
    const refs = this.refs(day, uid);
    await this.db.runTransaction(async (tx) => {
      const [u, g] = await tx.getAll(refs.user, refs.global);
      if (u?.exists) tx.update(refs.user, { count: Math.max(0, Number(u.get("count")) - 1) });
      if (g?.exists) tx.update(refs.global, { count: Math.max(0, Number(g.get("count")) - 1) });
    });
  }

  async peek(day: string, uid: string, limits: Limits): Promise<Limits> {
    const refs = this.refs(day, uid);
    const [u, g] = await this.db.getAll(refs.user, refs.global);
    return {
      user: Math.max(0, limits.user - Number(u?.get("count") ?? 0)),
      global: Math.max(0, limits.global - Number(g?.get("count") ?? 0)),
    };
  }
}

/** Counters are kept a week after their day (for the cost log), then expire. */
function expiry(day: string): Date {
  const d = new Date(`${day}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 8);
  return d;
}
