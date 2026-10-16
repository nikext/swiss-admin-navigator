import { deleteSession } from "@/lib/server/agent";
import { agentUserId } from "@/lib/server/auth";
import { fail, identify, log, readJson, SESSION_ID, unauthorized } from "@/lib/server/http";

/** "New conversation": deletes the visitor's Agent Runtime session (it would expire in 24 h). */
export async function DELETE(req: Request): Promise<Response> {
  const id = await identify();
  if (!id) return unauthorized();
  const body = await readJson(req, 256);
  const sessionId = typeof body?.sessionId === "string" ? body.sessionId : "";
  if (!SESSION_ID.test(sessionId)) return fail(400, "bad_request", "bad session id");
  try {
    await deleteSession(agentUserId(id), sessionId);
  } catch (err) {
    // Not ours, already gone or expired: nothing to delete either way.
    log("WARNING", "delete session failed", { error: String(err).slice(0, 300) });
  }
  return Response.json({ ok: true });
}
