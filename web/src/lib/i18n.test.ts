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
      expect(STRINGS[l].noticeSources).toContain("Fedlex");
    }
  });

  it("lists the same memory policy in every language", () => {
    for (const l of LANGS) {
      expect(STRINGS[l].keepList).toHaveLength(STRINGS.en.keepList.length);
      expect(STRINGS[l].neverList).toHaveLength(STRINGS.en.neverList.length);
      expect(STRINGS[l].points).toHaveLength(3);
    }
  });

  it("pluralises the trail and the seal", () => {
    expect(STRINGS.en.trail(4, 48, 0)).toBe("Checked 4 articles in 48 s");
    expect(STRINGS.en.trail(1, 39, 1)).toBe("Checked 1 article in 39 s · 1 correction");
    expect(STRINGS.de.trail(4, 48, 0)).toBe("4 Artikel in 48 s geprüft");
    expect(STRINGS.en.seal(3, 3)).toBe("3 of 3 quotes checked against the law text");
    expect(STRINGS.en.sealPartial(1, 2, 1)).toBe("1 of 2 quotes verified · 1 removed");
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
