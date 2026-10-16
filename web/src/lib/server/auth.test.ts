import { describe, expect, it } from "vitest";

import {
  agentUserId,
  checkCode,
  clientIp,
  COOKIE_MAX_AGE,
  decodeCookie,
  encodeCookie,
  newIdentity,
  WindowLimiter,
} from "@/lib/server/auth";

const CODE = "correct horse battery";

describe("access code", () => {
  it("accepts the code (ignoring surrounding whitespace) and nothing else", () => {
    expect(checkCode(CODE, CODE)).toBe(true);
    expect(checkCode(` ${CODE}\n`, CODE)).toBe(true);
    expect(checkCode("correct horse", CODE)).toBe(false);
    expect(checkCode("", CODE)).toBe(false);
  });
});

describe("session cookie", () => {
  it("round-trips an identity", () => {
    const id = newIdentity();
    expect(decodeCookie(encodeCookie(id, CODE), CODE)).toEqual(id);
    expect(agentUserId(id)).toBe(`web-${id.uid}`);
  });

  it("rejects tampering, a rotated code and expiry", () => {
    const id = newIdentity(Date.UTC(2026, 9, 16));
    const value = encodeCookie(id, CODE);
    const [payload, mac] = value.split(".");
    const forged = Buffer.from(JSON.stringify({ ...id, uid: "someone-else" })).toString(
      "base64url",
    );
    expect(decodeCookie(`${forged}.${mac}`, CODE)).toBeNull();
    expect(decodeCookie(`${payload}.${mac}x`, CODE)).toBeNull();
    expect(decodeCookie(value, "a new access code")).toBeNull();
    expect(decodeCookie("garbage", CODE)).toBeNull();
    expect(decodeCookie(undefined, CODE)).toBeNull();
    const later = (id.iat + COOKIE_MAX_AGE + 1) * 1000;
    expect(decodeCookie(value, CODE, later)).toBeNull();
  });
});

describe("clientIp", () => {
  it("takes the hop Cloud Run appended, not a forged first hop", () => {
    expect(clientIp(new Headers({ "x-forwarded-for": "6.6.6.6, 203.0.113.9" }))).toBe(
      "203.0.113.9",
    );
    expect(clientIp(new Headers({ "x-forwarded-for": "203.0.113.9" }))).toBe("203.0.113.9");
    expect(clientIp(new Headers())).toBe("local");
  });
});

describe("WindowLimiter", () => {
  it("allows `limit` hits per window per key", () => {
    const l = new WindowLimiter(2, 1000);
    expect([l.hit("a", 0), l.hit("a", 1), l.hit("a", 2)]).toEqual([true, true, false]);
    expect(l.hit("b", 2)).toBe(true);
    expect(l.hit("a", 1000)).toBe(true);
  });
});
