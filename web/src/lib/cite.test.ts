import { describe, expect, it } from "vitest";

import { citationLabel, linkCitations } from "@/lib/cite";
import type { Citation } from "@/lib/contract";

describe("linkCitations", () => {
  const refs = ["1", "2", "3"];

  it("links known markers", () => {
    expect(linkCitations("drei Monatszinse [1].", refs)).toBe("drei Monatszinse [1](#cite-1).");
  });

  it("splits grouped and adjacent markers", () => {
    expect(linkCitations("x [1, 2] y [2][3]", refs)).toBe(
      "x [1](#cite-1)[2](#cite-2) y [2](#cite-2)[3](#cite-3)",
    );
  });

  it("leaves unknown refs (dropped by the verifier) and real links alone", () => {
    expect(linkCitations("a [4] b", refs)).toBe("a [4] b");
    expect(linkCitations("[1, 9]", refs)).toBe("[1, 9]");
    expect(linkCitations("see [1](https://example.org)", refs)).toBe(
      "see [1](https://example.org)",
    );
  });
});

describe("citationLabel", () => {
  const c: Citation = {
    ref: "1",
    sr: "220",
    article: "Art. 271a",
    paragraph: "1",
    letter: "a",
    quote_lang: "de",
    quote: "…",
    translation: null,
    abbr: "OR",
    url: null,
    as_of: null,
  };

  it("uses the UI language's abbreviations", () => {
    expect(citationLabel(c, "Abs.", "Bst.")).toBe("OR Art. 271a Abs. 1 Bst. a");
    expect(citationLabel({ ...c, abbr: null, paragraph: null, letter: null }, "al.", "let.")).toBe(
      "SR 220 Art. 271a",
    );
  });
});
