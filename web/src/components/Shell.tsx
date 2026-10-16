"use client";

import { LANGS, type Lang } from "@/lib/contract";
import { LANG_NAMES, STRINGS } from "@/lib/i18n";

/** Saves the UI language for the next visit (a preference, not personal data). */
export function saveLang(lang: Lang): void {
  document.cookie = `nav_lang=${lang}; path=/; max-age=31536000; samesite=lax`;
  document.documentElement.lang = lang;
}

export function LangSelect({ lang, onChange }: { lang: Lang; onChange: (l: Lang) => void }) {
  return (
    <label className="lang">
      <span className="sr-only">{STRINGS[lang].language}</span>
      <select
        value={lang}
        onChange={(e) => {
          const next = e.target.value as Lang;
          saveLang(next);
          onChange(next);
        }}
      >
        {LANGS.map((l) => (
          <option key={l} value={l} lang={l}>
            {LANG_NAMES[l]}
          </option>
        ))}
      </select>
    </label>
  );
}

/** The permanent notice (ADR-010); the English line is always shown. */
export function Notice({ lang }: { lang: Lang }) {
  const s = STRINGS[lang];
  return (
    <footer className="notice" role="contentinfo">
      <p>
        <strong>{s.notice}</strong>
        {lang !== "en" && <span lang="en"> · {STRINGS.en.notice}</span>}
      </p>
      <p className="muted">{s.noticeLong}</p>
    </footer>
  );
}

export function Brand({ lang }: { lang: Lang }) {
  return (
    <div className="brand">
      <span className="brand-mark" aria-hidden="true">
        §
      </span>
      <div>
        <h1>Swiss Admin Navigator</h1>
        <p className="tagline">{STRINGS[lang].tagline}</p>
      </div>
    </div>
  );
}
