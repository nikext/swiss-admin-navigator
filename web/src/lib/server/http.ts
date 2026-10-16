// Small helpers shared by the route handlers.

import { cookies } from "next/headers";

import type { ErrorCode } from "@/lib/contract";
import { COOKIE, decodeCookie, type Identity } from "@/lib/server/auth";
import { config } from "@/lib/server/config";

/** The visitor behind the session cookie, or null (no or invalid cookie). */
export async function identify(): Promise<Identity | null> {
  const jar = await cookies();
  return decodeCookie(jar.get(COOKIE)?.value, config().accessCode);
}

export function fail(status: number, code: ErrorCode, message: string): Response {
  return Response.json({ code, message }, { status, headers: { "Cache-Control": "no-store" } });
}

export const unauthorized = () => fail(401, "unauthorized", "access code required");

/** One structured log line (Cloud Run parses JSON on stdout). Never pass question text. */
export function log(severity: "INFO" | "WARNING" | "ERROR", message: string, fields = {}): void {
  console.log(JSON.stringify({ severity, message, ...fields }));
}

/** Reads a JSON body of at most `max` bytes; null if too big or malformed. */
export async function readJson(req: Request, max = 8_192): Promise<Record<string, unknown> | null> {
  const text = await req.text().catch(() => "");
  if (!text || text.length > max) return null;
  try {
    const v = JSON.parse(text) as unknown;
    return v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

/** Agent Runtime session ids are numeric. */
export const SESSION_ID = /^[0-9]{1,30}$/;
