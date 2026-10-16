import { cookies } from "next/headers";

import {
  checkCode,
  clientIp,
  COOKIE,
  COOKIE_MAX_AGE,
  encodeCookie,
  newIdentity,
  WindowLimiter,
} from "@/lib/server/auth";
import { config } from "@/lib/server/config";
import { fail, log, readJson } from "@/lib/server/http";

// 10 attempts per IP per 15 minutes (per instance; max 2 instances).
const attempts = new WindowLimiter(10, 15 * 60_000);

export async function POST(req: Request): Promise<Response> {
  const ip = clientIp(req.headers);
  if (!attempts.hit(ip)) return fail(429, "bad_request", "too many attempts, try again later");
  const body = await readJson(req, 1_024);
  const code = typeof body?.code === "string" ? body.code : "";
  const c = config();
  if (!code || !checkCode(code, c.accessCode)) {
    log("WARNING", "login failed");
    return fail(401, "unauthorized", "wrong access code");
  }
  const id = newIdentity();
  (await cookies()).set(COOKIE, encodeCookie(id, c.accessCode), {
    httpOnly: true,
    secure: c.secureCookies,
    sameSite: "lax",
    path: "/",
    maxAge: COOKIE_MAX_AGE,
  });
  log("INFO", "login", { uid: id.uid });
  return Response.json({ ok: true });
}
