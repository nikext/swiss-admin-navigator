import { cookies } from "next/headers";

import { deleteListedSession, listMemories, listSessions, purgeMemories } from "@/lib/server/agent";
import { agentUserId, COOKIE } from "@/lib/server/auth";
import { identify, log } from "@/lib/server/http";
import { forget, MEMORY_COOKIE } from "@/lib/server/memory";

/**
 * Sign out. The anonymous id is gone afterwards, and with it the only way to see
 * or delete what was remembered, so its memories and sessions are deleted too.
 */
export async function POST(): Promise<Response> {
  const id = await identify();
  if (id) {
    const deps = {
      listMemories,
      purgeMemories,
      listSessions,
      deleteSession: deleteListedSession,
    };
    await forget(deps, agentUserId(id))
      .then((out) => log("INFO", "logout forget", { uid: id.uid, ...out }))
      .catch((err) =>
        log("ERROR", "logout forget failed", { uid: id.uid, error: String(err).slice(0, 300) }),
      );
  }
  const jar = await cookies();
  jar.delete(COOKIE);
  jar.delete(MEMORY_COOKIE);
  return Response.json({ ok: true });
}
