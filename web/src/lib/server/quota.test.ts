import { describe, expect, it } from "vitest";

import { decide, MemoryQuota, zurichDay } from "@/lib/server/quota";

const limits = { user: 2, global: 3 };

describe("decide", () => {
  it("allows under both limits and reports what is left after this one", () => {
    expect(decide({ user: 0, global: 0 }, limits)).toEqual({
      ok: true,
      remaining: { user: 1, global: 2 },
    });
  });

  it("checks the global cap first", () => {
    expect(decide({ user: 2, global: 3 }, limits)).toMatchObject({
      ok: false,
      reason: "quota_global",
    });
    expect(decide({ user: 2, global: 1 }, limits)).toMatchObject({
      ok: false,
      reason: "quota_user",
    });
  });
});

describe("MemoryQuota", () => {
  it("enforces per-user and global limits per day, and refunds", async () => {
    const q = new MemoryQuota();
    const d = "2026-10-16";
    expect((await q.consume(d, "a", limits)).ok).toBe(true);
    expect((await q.consume(d, "a", limits)).ok).toBe(true);
    expect(await q.consume(d, "a", limits)).toMatchObject({ ok: false, reason: "quota_user" });
    expect((await q.consume(d, "b", limits)).ok).toBe(true);
    expect(await q.consume(d, "c", limits)).toMatchObject({ ok: false, reason: "quota_global" });
    await q.refund(d, "b");
    expect(await q.peek(d, "b", limits)).toEqual({ user: 2, global: 1 });
    expect((await q.consume("2026-10-17", "a", limits)).ok).toBe(true);
  });
});

describe("zurichDay", () => {
  it("uses the Zürich calendar day, not UTC", () => {
    // 23:30 UTC on 15 Oct is 01:30 on 16 Oct in Zürich (CEST, UTC+2).
    expect(zurichDay(new Date("2026-10-15T23:30:00Z"))).toBe("2026-10-16");
    expect(zurichDay(new Date("2026-01-15T23:30:00Z"))).toBe("2026-01-16");
    expect(zurichDay(new Date("2026-01-15T22:30:00Z"))).toBe("2026-01-15");
  });
});
