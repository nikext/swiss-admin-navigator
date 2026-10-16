import { describe, expect, it } from "vitest";

import { LANGS } from "@/lib/contract";
import { pickLang, STRINGS } from "@/lib/i18n";

describe("strings", () => {
  it("has every key in every language", () => {
    const keys = Object.keys(STRINGS.en).sort();
    for (const l of LANGS) expect(Object.keys(STRINGS[l]).sort()).toEqual(keys);
  });

  it("keeps the notice in every language and six examples each", () => {
    expect(STRINGS.en.notice).toBe("Unofficial. Not legal advice.");
    for (const l of LANGS) {
      expect(STRINGS[l].examples).toHaveLength(6);
      expect(STRINGS[l].noticeLong).toContain("Fedlex");
    }
  });

  it("never claims to be official (ADR-010)", () => {
    // Only negated forms: unofficial, inoffiziell, non officiel(le), non ufficiale.
    const claim = /(?<!un|in|non )(official|offiziell|officiel|ufficiale)/i;
    for (const l of LANGS) expect(JSON.stringify(STRINGS[l])).not.toMatch(claim);
  });
});

describe("pickLang", () => {
  it("prefers the saved choice, then Accept-Language, then English", () => {
    expect(pickLang("it", "de-CH,de;q=0.9")).toBe("it");
    expect(pickLang(undefined, "fr-CH, fr;q=0.9, en;q=0.8")).toBe("fr");
    expect(pickLang("xx", "es-ES,pt;q=0.5")).toBe("en");
    expect(pickLang(undefined, null)).toBe("en");
  });
});
