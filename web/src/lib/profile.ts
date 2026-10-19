// The memory whitelist (M7, ADR-029), mirrored by hand from agents/navigator/memory.py:
// the only fields Memory Bank's structured profile may hold, and their allowed values.
// agents/navigator/tests/test_memory.py parses the JSON block between the markers
// and fails if it drifts from PROFILE_FIELDS.

import type { Lang } from "@/lib/contract";

// whitelist:start
export const PROFILE_FIELDS = {
  canton: [
    "AG",
    "AI",
    "AR",
    "BE",
    "BL",
    "BS",
    "FR",
    "GE",
    "GL",
    "GR",
    "JU",
    "LU",
    "NE",
    "NW",
    "OW",
    "SG",
    "SH",
    "SO",
    "SZ",
    "TG",
    "TI",
    "UR",
    "VD",
    "VS",
    "ZG",
    "ZH",
  ],
  municipality: null,
  language: ["de", "fr", "it", "en"],
  nationality_group: ["swiss", "eu_efta", "third_country"],
  permit: ["L", "B", "C", "Ci", "G"],
  employment: ["employed", "self_employed", "unemployed", "student", "retired", "not_working"],
  marital_status: ["single", "married", "divorced", "widowed"],
  has_children: "boolean",
} as const;
// whitelist:end

export type ProfileField = keyof typeof PROFILE_FIELDS;
export type Profile = Partial<Record<ProfileField, string | boolean>>;
export const FIELD_ORDER = Object.keys(PROFILE_FIELDS) as ProfileField[];

// Letters, spaces and . ' ’ ( ) / - only, as in memory.py: no postcode or house number.
const MUNICIPALITY = /^\p{L}[\p{L} .'’()/-]{0,48}$/u;

/** Only whitelisted fields with allowed values: what Memory Bank returns is not trusted. */
export function cleanProfile(raw: unknown): Profile {
  const out: Profile = {};
  if (!raw || typeof raw !== "object") return out;
  for (const [name, value] of Object.entries(raw as Record<string, unknown>)) {
    if (!(name in PROFILE_FIELDS)) continue;
    const spec = PROFILE_FIELDS[name as ProfileField];
    if (spec === "boolean") {
      if (typeof value === "boolean") out[name as ProfileField] = value;
    } else if (typeof value === "string") {
      const v = value.trim();
      const ok = spec === null ? MUNICIPALITY.test(v) : (spec as readonly string[]).includes(v);
      if (ok) out[name as ProfileField] = v;
    }
  }
  return out;
}

type Labels = {
  fields: Record<ProfileField, string>;
  values: Record<string, string>;
  yes: string;
  no: string;
};

export const PROFILE_LABELS: Record<Lang, Labels> = {
  en: {
    fields: {
      canton: "Canton",
      municipality: "Municipality",
      language: "Language",
      nationality_group: "Nationality",
      permit: "Permit",
      employment: "Work",
      marital_status: "Civil status",
      has_children: "Children",
    },
    values: {
      de: "German",
      fr: "French",
      it: "Italian",
      en: "English",
      swiss: "Swiss",
      eu_efta: "EU/EFTA",
      third_country: "Other country",
      employed: "Employed",
      self_employed: "Self-employed",
      unemployed: "Unemployed",
      student: "Student",
      retired: "Retired",
      not_working: "Not working",
      single: "Single",
      married: "Married",
      divorced: "Divorced",
      widowed: "Widowed",
    },
    yes: "Yes",
    no: "No",
  },
  de: {
    fields: {
      canton: "Kanton",
      municipality: "Gemeinde",
      language: "Sprache",
      nationality_group: "Staatsangehörigkeit",
      permit: "Bewilligung",
      employment: "Arbeit",
      marital_status: "Zivilstand",
      has_children: "Kinder",
    },
    values: {
      de: "Deutsch",
      fr: "Französisch",
      it: "Italienisch",
      en: "Englisch",
      swiss: "Schweiz",
      eu_efta: "EU/EFTA",
      third_country: "Drittstaat",
      employed: "Angestellt",
      self_employed: "Selbständig",
      unemployed: "Arbeitslos",
      student: "In Ausbildung",
      retired: "Pensioniert",
      not_working: "Nicht erwerbstätig",
      single: "Ledig",
      married: "Verheiratet",
      divorced: "Geschieden",
      widowed: "Verwitwet",
    },
    yes: "Ja",
    no: "Nein",
  },
  fr: {
    fields: {
      canton: "Canton",
      municipality: "Commune",
      language: "Langue",
      nationality_group: "Nationalité",
      permit: "Permis",
      employment: "Travail",
      marital_status: "État civil",
      has_children: "Enfants",
    },
    values: {
      de: "Allemand",
      fr: "Français",
      it: "Italien",
      en: "Anglais",
      swiss: "Suisse",
      eu_efta: "UE/AELE",
      third_country: "État tiers",
      employed: "Salarié·e",
      self_employed: "Indépendant·e",
      unemployed: "Au chômage",
      student: "En formation",
      retired: "Retraité·e",
      not_working: "Sans activité",
      single: "Célibataire",
      married: "Marié·e",
      divorced: "Divorcé·e",
      widowed: "Veuf·ve",
    },
    yes: "Oui",
    no: "Non",
  },
  it: {
    fields: {
      canton: "Cantone",
      municipality: "Comune",
      language: "Lingua",
      nationality_group: "Nazionalità",
      permit: "Permesso",
      employment: "Lavoro",
      marital_status: "Stato civile",
      has_children: "Figli",
    },
    values: {
      de: "Tedesco",
      fr: "Francese",
      it: "Italiano",
      en: "Inglese",
      swiss: "Svizzera",
      eu_efta: "UE/AELS",
      third_country: "Stato terzo",
      employed: "Dipendente",
      self_employed: "Indipendente",
      unemployed: "Disoccupato/a",
      student: "In formazione",
      retired: "Pensionato/a",
      not_working: "Senza attività",
      single: "Celibe/nubile",
      married: "Sposato/a",
      divorced: "Divorziato/a",
      widowed: "Vedovo/a",
    },
    yes: "Sì",
    no: "No",
  },
};

/** A remembered field as the memory dialog shows it: label and value in the UI language. */
export function describeParts(
  field: ProfileField,
  value: string | boolean,
  lang: Lang,
): { label: string; value: string } {
  const l = PROFILE_LABELS[lang];
  const shown =
    typeof value === "boolean"
      ? value
        ? l.yes
        : l.no
      : field === "canton" || field === "permit" || field === "municipality"
        ? value
        : (l.values[value] ?? value);
  return { label: l.fields[field], value: shown };
}

/** "Permit: B", "Civil status: Married" — a remembered field as one line. */
export function describe(field: ProfileField, value: string | boolean, lang: Lang): string {
  const { label, value: shown } = describeParts(field, value, lang);
  return `${label}: ${shown}`;
}
