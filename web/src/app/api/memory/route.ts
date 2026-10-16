import { cookies } from "next/headers";

import { deleteListedSession, listMemories, listSessions, purgeMemories } from "@/lib/server/agent";
import { agentUserId, COOKIE_MAX_AGE } from "@/lib/server/auth";
import { config } from "@/lib/server/config";
import { fail, identify, log, readJson, unauthorized } from "@/lib/server/http";
import {
  endSessions,
  forget,
  MEMORY_COOKIE,
  optedIn,
  profileOf,
  type MemoryDeps,
} from "@/lib/server/memory";

export const dynamic = "force-dynamic";

const deps: MemoryDeps = {
  listMemories,
  purgeMemories,
  listSessions,
  deleteSession: deleteListedSession,
};
const noStore = { "Cache-Control": "no-store" };

/** "What I remember": the switch and the remembered profile (whitelisted fields only). */
export async function GET(): Promise<Response> {
  const id = await identify();
  if (!id) return unauthorized();
  const enabled = optedIn((await cookies()).get(MEMORY_COOKIE)?.value, id.uid);
  try {
    const profile = profileOf(await listMemories(agentUserId(id)));
    return Response.json({ enabled, profile }, { headers: noStore });
  } catch (err) {
    log("ERROR", "memory list failed", { uid: id.uid, error: String(err).slice(0, 300) });
    return fail(502, "upstream", "memory is unavailable");
  }
}

/** The switch. Ends the visitor's sessions so none keeps the old setting. */
export async function POST(req: Request): Promise<Response> {
  const id = await identify();
  if (!id) return unauthorized();
  const body = await readJson(req, 256);
  if (typeof body?.enabled !== "boolean")
    return fail(400, "bad_request", "enabled must be a boolean");
  const enabled = body.enabled;
  const jar = await cookies();
  if (enabled) {
    jar.set(MEMORY_COOKIE, id.uid, {
      httpOnly: true,
      sameSite: "lax",
      secure: config().secureCookies,
      path: "/",
      maxAge: COOKIE_MAX_AGE,
    });
  } else {
    jar.delete(MEMORY_COOKIE);
  }
  const sessions = await endSessions(deps, agentUserId(id)).catch(() => -1);
  log("INFO", "memory switch", { uid: id.uid, enabled, sessions });
  return Response.json({ enabled }, { headers: noStore });
}

/** "Forget me": deletes every memory and every session of the visitor. */
export async function DELETE(): Promise<Response> {
  const id = await identify();
  if (!id) return unauthorized();
  try {
    const out = await forget(deps, agentUserId(id));
    log(out.remaining ? "ERROR" : "INFO", "memory forget", { uid: id.uid, ...out });
    if (out.remaining) return fail(502, "upstream", "some memories could not be deleted");
    return Response.json({ ok: true }, { headers: noStore });
  } catch (err) {
    log("ERROR", "memory forget failed", { uid: id.uid, error: String(err).slice(0, 300) });
    return fail(502, "upstream", "memory is unavailable");
  }
}
