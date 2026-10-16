import { WindowLimiter } from "@/lib/server/auth";
import { fail, identify, log, unauthorized } from "@/lib/server/http";
import { articleQuery, getArticle, McpError } from "@/lib/server/mcp";

const perUser = new WindowLimiter(60, 60_000);

/** One article for the citation panel, from the MCP server's get_article. */
export async function GET(req: Request): Promise<Response> {
  const id = await identify();
  if (!id) return unauthorized();
  if (!perUser.hit(id.uid)) return fail(429, "bad_request", "too many requests");
  const q = articleQuery(new URL(req.url).searchParams);
  if (!q) return fail(400, "bad_request", "expected sr, article and lang (de, fr, it, en)");
  try {
    const article = await getArticle(q, AbortSignal.timeout(15_000));
    // Law text changes only with a new index; a private hour of caching is safe.
    return Response.json(article, { headers: { "Cache-Control": "private, max-age=3600" } });
  } catch (err) {
    const notFound = err instanceof McpError && /no article|unknown|not found/i.test(err.message);
    log(notFound ? "INFO" : "ERROR", "get_article failed", { error: String(err).slice(0, 300) });
    return notFound
      ? fail(404, "bad_request", "article not found")
      : fail(502, "upstream", "the law server could not be reached");
  }
}
