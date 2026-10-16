import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import { finalText, parseAnswer, streamError, toProgress } from "@/lib/server/adk";
import { LineSplitter } from "@/lib/lines";

const fixture = readFileSync(new URL("./fixtures/stream-deposit.ndjson", import.meta.url));
const events = fixture
  .toString()
  .split("\n")
  .filter(Boolean)
  .map((l) => JSON.parse(l) as Record<string, unknown>);

describe("LineSplitter", () => {
  it("reassembles lines split across chunks and multi-byte characters", () => {
    const bytes = new TextEncoder().encode('{"a":"Mietzinsdepot ü"}\n{"b":2}\n{"c":3}');
    const s = new LineSplitter();
    const out: string[] = [];
    for (let i = 0; i < bytes.length; i += 5) out.push(...s.push(bytes.slice(i, i + 5)));
    out.push(...s.flush());
    expect(out).toEqual(['{"a":"Mietzinsdepot ü"}', '{"b":2}', '{"c":3}']);
  });

  it("strips SSE data prefixes and drops comments and blank lines", () => {
    const s = new LineSplitter();
    const out = s.push(new TextEncoder().encode(': keepalive\n\ndata: {"x":1}\r\n\n'));
    expect(out).toEqual(['{"x":1}']);
  });

  it("splits the recorded Agent Runtime stream into its seven events", () => {
    const s = new LineSplitter();
    expect([...s.push(fixture), ...s.flush()]).toHaveLength(7);
  });
});

describe("recorded stream (Agent Runtime, 2026-10-16)", () => {
  it("maps tool calls and article reads to progress steps", () => {
    const steps = events.flatMap(toProgress);
    expect(steps).toEqual([
      { type: "progress", step: "resolve", detail: "Art. 257e OR" },
      { type: "progress", step: "read", detail: "OR Art. 257e" },
      expect.objectContaining({ type: "progress", step: "search" }),
    ]);
  });

  it("finds exactly one final answer, the last event", () => {
    const finals = events.map(finalText);
    expect(finals.slice(0, -1).every((t) => t === null)).toBe(true);
    const answer = parseAnswer(finals.at(-1)!);
    expect(answer?.language).toBe("de");
    expect(answer?.citations.map((c) => c.ref)).toEqual(["1", "2", "3"]);
    expect(answer?.citations[0]?.abbr).toBe("OR");
    expect(answer?.verification.status).toBe("passed");
  });

  it("has no stream errors", () => {
    expect(events.map(streamError).every((e) => e === null)).toBe(true);
  });
});

describe("event mapping", () => {
  const call = (name: string, args: Record<string, unknown>) => ({
    author: "navigator",
    content: { parts: [{ function_call: { name, args } }] },
  });

  it("reports the verifier sending a draft back", () => {
    expect(toProgress(call("citation_check", { draft: {} }))).toEqual([
      { type: "progress", step: "check" },
    ]);
  });

  it("truncates long details and ignores unknown tools", () => {
    const [e] = toProgress(call("search_law", { query: "x".repeat(300) }));
    expect(e && e.type === "progress" && e.detail?.length).toBe(120);
    expect(toProgress(call("something_else", {}))).toEqual([]);
  });

  it("skips thoughts and partial events as final text", () => {
    const thought = { content: { parts: [{ text: "hmm", thought: true }] } };
    expect(finalText(thought)).toBeNull();
    expect(finalText({ partial: true, content: { parts: [{ text: "{}" }] } })).toBeNull();
  });

  it("recognises in-band errors but not events", () => {
    expect(streamError({ code: 503, message: "unavailable" })).toBe("unavailable");
    expect(streamError({ error: { code: 429 } })).toContain("429");
    expect(streamError({ author: "navigator", code: 1, message: "x" })).toBeNull();
  });

  it("rejects answers that are not the contract", () => {
    expect(parseAnswer("not json")).toBeNull();
    expect(parseAnswer('{"citations": []}')).toBeNull();
    const a = parseAnswer('{"answer_markdown": "x", "citations": []}');
    expect(a?.follow_up_questions).toEqual([]);
    expect(a?.notice).toMatch(/^Unofficial\. Not legal advice\./);
  });
});
