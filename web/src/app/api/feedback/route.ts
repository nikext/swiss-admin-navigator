import { WindowLimiter } from "@/lib/server/auth";
import { fail, identify, log, readJson, SESSION_ID, unauthorized } from "@/lib/server/http";
import { feedbackStore } from "@/lib/server/stores";

const perUser = new WindowLimiter(30, 60_000);

function strings(value: unknown, max: number): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((v): v is string => typeof v === "string")
    .slice(0, 20)
    .map((v) => v.slice(0, max));
}

function str(value: unknown, max: number): string | null {
  return typeof value === "string" && value.trim() ? value.trim().slice(0, max) : null;
}

export async function POST(req: Request): Promise<Response> {
  const id = await identify();
  if (!id) return unauthorized();
  if (!perUser.hit(id.uid)) return fail(429, "bad_request", "too many requests");
  const b = await readJson(req, 4_096);
  const rating = b?.rating;
  const sessionId = str(b?.sessionId, 40) ?? "";
  if ((rating !== "up" && rating !== "down") || !SESSION_ID.test(sessionId)) {
    return fail(400, "bad_request", "expected rating (up|down) and sessionId");
  }
  try {
    await feedbackStore().add({
      rating,
      sessionId,
      uid: id.uid,
      language: str(b?.language, 5),
      citations: strings(b?.citations, 40),
      verification: str(b?.verification, 30),
      confidence: str(b?.confidence, 10),
      at: new Date(),
    });
  } catch (err) {
    log("ERROR", "feedback write failed", { error: String(err).slice(0, 300) });
    return fail(502, "upstream", "feedback could not be saved");
  }
  return Response.json({ ok: true });
}
