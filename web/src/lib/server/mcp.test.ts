import { describe, expect, it } from "vitest";

import { articleQuery, McpError, toolResult } from "@/lib/server/mcp";

describe("articleQuery", () => {
  const q = (s: string) => articleQuery(new URLSearchParams(s));

  it("accepts SR numbers, article labels and the four languages", () => {
    expect(q("sr=220&article=Art.%20329g%20bis&lang=fr")).toEqual({
      sr: "220",
      article: "Art. 329g bis",
      lang: "fr",
    });
    expect(q("sr=142.20&article=30")).toEqual({ sr: "142.20", article: "30", lang: "de" });
  });

  it("rejects malformed input", () => {
    expect(q("sr=OR&article=1")).toBeNull();
    expect(q("sr=220&article=1&lang=es")).toBeNull();
    expect(q("sr=220&article=" + "x".repeat(41))).toBeNull();
    expect(q("sr=220&article=%3Cscript%3E")).toBeNull();
    expect(q("article=1")).toBeNull();
  });
});

describe("toolResult", () => {
  it("prefers structuredContent, else parses the text block", () => {
    expect(toolResult({ result: { structuredContent: { a: 1 }, content: [] } })).toEqual({ a: 1 });
    expect(toolResult({ result: { content: [{ type: "text", text: '{"b":2}' }] } })).toEqual({
      b: 2,
    });
  });

  it("raises tool and protocol errors", () => {
    const toolErr = {
      result: { isError: true, content: [{ type: "text", text: "no article '9999z'" }] },
    };
    expect(() => toolResult(toolErr)).toThrow(McpError);
    expect(() => toolResult({ error: { message: "bad" } })).toThrow("bad");
  });
});
