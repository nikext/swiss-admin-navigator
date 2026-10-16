import { describe as group, expect, it } from "vitest";

import { LANGS } from "@/lib/contract";
import { cleanProfile, describe, FIELD_ORDER, PROFILE_FIELDS, PROFILE_LABELS } from "@/lib/profile";

group("cleanProfile", () => {
  it("keeps whitelisted fields with allowed values", () => {
    expect(
      cleanProfile({
        canton: "ZH",
        municipality: "La Chaux-de-Fonds",
        permit: "Ci",
        has_children: false,
        employment: " employed ",
      }),
    ).toEqual({
      canton: "ZH",
      municipality: "La Chaux-de-Fonds",
      permit: "Ci",
      has_children: false,
      employment: "employed",
    });
  });

  it("drops everything else", () => {
    expect(
      cleanProfile({
        canton: "Zürich",
        permit: "N",
        marital_status: "registered_partnership",
        municipality: "8400 Winterthur",
        has_children: "yes",
        diagnosis: "diabetes",
      }),
    ).toEqual({});
    expect(cleanProfile(null)).toEqual({});
    expect(cleanProfile("canton: ZH")).toEqual({});
  });
});

group("labels", () => {
  it("label every field and every enum value in every language", () => {
    for (const l of LANGS) {
      const labels = PROFILE_LABELS[l];
      for (const f of FIELD_ORDER) expect(labels.fields[f]).toBeTruthy();
      for (const f of ["language", "nationality_group", "employment", "marital_status"] as const) {
        for (const v of PROFILE_FIELDS[f]) expect(labels.values[v], `${l} ${v}`).toBeTruthy();
      }
    }
  });

  it("describe a remembered field", () => {
    expect(describe("permit", "B", "de")).toBe("Bewilligung: B");
    expect(describe("nationality_group", "eu_efta", "fr")).toBe("Nationalité: UE/AELE");
    expect(describe("has_children", true, "it")).toBe("Figli: Sì");
    expect(describe("municipality", "Thun", "en")).toBe("Municipality: Thun");
  });
});
