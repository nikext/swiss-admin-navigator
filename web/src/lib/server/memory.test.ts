import { describe, expect, it } from "vitest";

import {
  endSessions,
  forget,
  optedIn,
  profileOf,
  sessionState,
  type MemoryDeps,
} from "@/lib/server/memory";

const field = (
  data: Record<string, unknown>,
  updateTime: string,
  schemaId = "resident-profile",
) => ({
  name: `projects/p/locations/l/reasoningEngines/1/memories/${updateTime}`,
  memoryType: "STRUCTURED_PROFILE",
  structuredContent: { schemaId, data },
  context: "The user mentioned they have diabetes.", // stored by Memory Bank, never shown
  updateTime,
});

function fakeDeps(memories: Record<string, unknown>[], sessions: string[]) {
  const deleted: string[] = [];
  let purged = 0;
  const deps: MemoryDeps = {
    async listMemories() {
      return memories;
    },
    async purgeMemories() {
      purged += 1;
      memories = [];
    },
    async listSessions() {
      return sessions;
    },
    async deleteSession(_u, id) {
      if (id === "bad") throw new Error("gone");
      deleted.push(id);
    },
  };
  return { deps, deleted, purged: () => purged };
}

describe("memory switch", () => {
  it("is on only when the cookie names this visitor", () => {
    expect(optedIn("abc", "abc")).toBe(true);
    for (const v of [undefined, "", "on", "true", "abd"]) expect(optedIn(v, "abc")).toBe(false);
    expect(optedIn("", "")).toBe(false);
  });

  it("puts the agent's state key into new sessions", () => {
    expect(sessionState(true)).toEqual({ memory_opt_in: true });
    expect(sessionState(false)).toEqual({ memory_opt_in: false });
  });
});

describe("profileOf", () => {
  it("merges per-field memories, newest wins, whitelisted values only", () => {
    const profile = profileOf([
      field({ canton: "ZH" }, "2026-10-16T10:00:00Z"),
      field({ canton: "BE" }, "2026-10-16T11:00:00Z"),
      field({ permit: "F" }, "2026-10-16T09:00:00Z"), // asylum-related: not storable
      field({ health: "diabetes" }, "2026-10-16T09:00:00Z"), // not a field
      field({ municipality: "Bahnhofstrasse 12, 8001 Zürich" }, "2026-10-16T09:00:00Z"),
      field({ has_children: true }, "2026-10-16T09:00:00Z"),
      field({ permit: "B" }, "2026-10-16T09:00:00Z", "other-schema"),
      { memoryType: "NATURAL_LANGUAGE_COLLECTION", fact: "I have diabetes." },
    ]);
    expect(profile).toEqual({ canton: "BE", has_children: true });
    expect(JSON.stringify(profile)).not.toContain("diabetes");
  });

  it("is empty without memories", () => {
    expect(profileOf([])).toEqual({});
  });
});

describe("forget", () => {
  it("purges, ends every session (even if one delete fails) and checks nothing is left", async () => {
    const f = fakeDeps([field({ canton: "ZH" }, "t")], ["1", "bad", "3"]);
    expect(await forget(f.deps, "web-x")).toEqual({ sessions: 3, remaining: 0 });
    expect(f.purged()).toBe(1);
    expect(f.deleted).toEqual(["1", "3"]);
  });

  it("reports what a purge left behind", async () => {
    const f = fakeDeps([field({ canton: "ZH" }, "t")], []);
    f.deps.purgeMemories = async () => {};
    expect(await forget(f.deps, "web-x")).toEqual({ sessions: 0, remaining: 1 });
  });

  it("endSessions counts the sessions it ended", async () => {
    const f = fakeDeps([], ["7", "8"]);
    expect(await endSessions(f.deps, "web-x")).toBe(2);
    expect(f.deleted).toEqual(["7", "8"]);
  });
});
