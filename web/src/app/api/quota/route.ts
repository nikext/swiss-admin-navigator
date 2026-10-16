import { config } from "@/lib/server/config";
import { identify, unauthorized } from "@/lib/server/http";
import { zurichDay } from "@/lib/server/quota";
import { quotaStore } from "@/lib/server/stores";

export const dynamic = "force-dynamic";

export async function GET(): Promise<Response> {
  const id = await identify();
  if (!id) return unauthorized();
  const c = config();
  const limits = { user: c.userDailyQuota, global: c.globalDailyCap };
  const remaining = await quotaStore().peek(zurichDay(), id.uid, limits);
  return Response.json({ remaining, limits }, { headers: { "Cache-Control": "no-store" } });
}
