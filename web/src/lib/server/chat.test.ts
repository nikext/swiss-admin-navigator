import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import type { UiEvent } from "@/lib/contract";
import { runChat, type ChatDeps } from "@/lib/server/chat";

const events = readFileSync(new URL("./fixtures/stream-deposit.ndjson", import.meta.url))
  .toString()
  .split("\n")
  .filter(Boolean)
  .map((l) => JSON.parse(l) as Record<string, unknown>);

function fake(opts: {
  failFor?: Set<string>;
  emptyFor?: Set<string>;
  failAfter?: number;
  items?: typeof events;
}) {
  const created: string[] = [];
  const deps: ChatDeps = {
    async createSession() {
      const id = String(100 + created.length);
      created.push(id);
      return id;
    },
    async *streamQuery(_u, sid) {
      if (opts.failFor?.has(sid)) throw new Error(`Session ${sid} not found`);
      if (opts.emptyFor?.has(sid)) return;
      let n = 0;
      for (const item of opts.items ?? events) {
        if (opts.failAfter !== undefined && n++ >= opts.failAfter) throw new Error("503");
        yield item;
      }
    },
  };
  return { deps, created };
}

async function run(deps: ChatDeps, sessionId: string | null) {
  const sent: UiEvent[] = [];
  const out = await runChat(
    deps,
    "web-u",
    "Mietzinsdepot?",
    sessionId,
    new AbortController().signal,
    (e) => sent.push(e),
  );
  return { out, sent };
}

describe("runChat", () => {
  it("creates a session, streams progress, then the answer", async () => {
    const { deps, created } = fake({});
    const { out, sent } = await run(deps, null);
    expect(created).toEqual(["100"]);
    expect(sent[0]).toEqual({ type: "session", sessionId: "100" });
    expect(sent.filter((e) => e.type === "progress")).toHaveLength(3);
    expect(sent.at(-1)?.type).toBe("answer");
    expect(out).toMatchObject({ sessionId: "100", error: null, agentWorked: true });
  });

  it("reuses a given session", async () => {
    const { deps, created } = fake({});
    const { out, sent } = await run(deps, "42");
    expect(created).toEqual([]);
    expect(sent.some((e) => e.type === "session")).toBe(false);
    expect(out.answer).not.toBeNull();
  });

  it("replaces an expired or foreign session once, before any event", async () => {
    const { deps, created } = fake({ failFor: new Set(["42"]) });
    const { out, sent } = await run(deps, "42");
    expect(created).toEqual(["100"]);
    expect(sent[0]).toEqual({ type: "session", sessionId: "100" });
    expect(out.answer).not.toBeNull();
  });

  it("replaces a session that yields an empty stream (Agent Runtime's answer to a dead one)", async () => {
    const { deps, created } = fake({ emptyFor: new Set(["42"]) });
    const { out, sent } = await run(deps, "42");
    expect(created).toEqual(["100"]);
    expect(sent[0]).toEqual({ type: "session", sessionId: "100" });
    expect(out.answer).not.toBeNull();
  });

  it("gives up if a new session yields nothing too", async () => {
    const { deps, created } = fake({ emptyFor: new Set(["100"]) });
    const { out, sent } = await run(deps, null);
    expect(created).toEqual(["100"]);
    expect(out.answer).toBeNull();
    expect(sent.at(-1)).toMatchObject({ type: "error", code: "no_answer" });
  });

  it("does not retry after the agent started working", async () => {
    const { deps, created } = fake({ failAfter: 2 });
    const { out, sent } = await run(deps, "42");
    expect(created).toEqual([]);
    expect(out.agentWorked).toBe(true);
    expect(out.answer).toBeNull();
    expect(sent.at(-1)).toMatchObject({ type: "error", code: "upstream" });
  });

  it("reports a stream that ends without an answer", async () => {
    const { deps } = fake({ items: events.slice(0, 2) });
    const { out, sent } = await run(deps, "42");
    expect(out.error).toBe("no final answer");
    expect(sent.at(-1)).toMatchObject({ type: "error", code: "no_answer" });
  });

  it("marks a failure before any work so the quota can be refunded", async () => {
    const { deps } = fake({ failAfter: 0 });
    const { out } = await run(deps, null);
    expect(out.agentWorked).toBe(false);
    expect(out.answer).toBeNull();
  });
});
