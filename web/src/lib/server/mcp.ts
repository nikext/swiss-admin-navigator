// get_article from the swiss-law MCP server for the citation panel.
//
// The server is stateless Streamable HTTP with JSON responses (mcp_server/server.py),
// so one JSON-RPC `tools/call` POST is a complete exchange: no initialize, no
// session (verified against Cloud Run, 2026-10-16).

import { isLang, type ArticleText, type Lang } from "@/lib/contract";
import { config } from "@/lib/server/config";

const SR = /^[0-9][0-9.]{0,20}$/;
const ARTICLE = /^[\p{L}\p{N} ._-]{1,40}$/u;

export interface ArticleQuery {
  sr: string;
  article: string;
  lang: Lang;
}

/** Validates user-supplied panel parameters; null if any is malformed. */
export function articleQuery(params: URLSearchParams): ArticleQuery | null {
  const sr = params.get("sr")?.trim() ?? "";
  const article = params.get("article")?.trim() ?? "";
  const lang = params.get("lang") ?? "de";
  if (!SR.test(sr) || !ARTICLE.test(article) || !isLang(lang)) return null;
  return { sr, article, lang };
}

export class McpError extends Error {}

/** Unwraps a tools/call result: structuredContent, else the first text block as JSON. */
export function toolResult(body: unknown): Record<string, unknown> {
  const rpc = body as {
    result?: {
      isError?: boolean;
      structuredContent?: Record<string, unknown>;
      content?: { type?: string; text?: string }[];
    };
    error?: { message?: string };
  };
  if (rpc.error) throw new McpError(rpc.error.message ?? "MCP error");
  const result = rpc.result;
  if (!result) throw new McpError("no result");
  const text = result.content?.find((c) => typeof c.text === "string")?.text;
  if (result.isError) throw new McpError(text?.slice(0, 200) ?? "tool error");
  if (result.structuredContent) {
    // FastMCP wraps non-object returns as {"result": …}; get_article returns an object.
    return result.structuredContent;
  }
  if (!text) throw new McpError("empty tool result");
  return JSON.parse(text) as Record<string, unknown>;
}

export async function getArticle(q: ArticleQuery, signal?: AbortSignal): Promise<ArticleText> {
  const resp = await fetch(config().mcpUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: { name: "get_article", arguments: { sr: q.sr, article: q.article, lang: q.lang } },
    }),
    signal,
  });
  if (!resp.ok) throw new McpError(`MCP server ${resp.status}`);
  const data = toolResult(await resp.json());
  if (data.error) throw new McpError(String(data.error));
  return data as unknown as ArticleText;
}
