"use client";

import { useState } from "react";

import type { Lang } from "@/lib/contract";
import { STRINGS } from "@/lib/i18n";

import Icon, { type IconName } from "./Icon";
import { Brand, Disclaimer, LangMenu } from "./Shell";

const POINT_ICONS: IconName[] = ["shieldCheck", "languages", "bookOpen"];

export default function Login({ initialLang }: { initialLang: Lang }) {
  const [lang, setLang] = useState<Lang>(initialLang);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const s = STRINGS[lang];

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const resp = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });
      if (resp.ok) {
        window.location.reload();
        return;
      }
      setError(resp.status === 429 ? s.tooManyAttempts : s.wrongCode);
    } catch {
      setError(s.errorNetwork);
    }
    setBusy(false);
  }

  return (
    <div className="shell">
      <header className="topbar bare">
        <Brand />
        <LangMenu lang={lang} onChange={setLang} />
      </header>
      <main className="access-main">
        <div className="access">
          <div className="access-intro">
            <div className="access-title">
              <span className="mark mark-lg" aria-hidden="true">
                §
              </span>
              <h1>Swiss Admin Navigator</h1>
              <p className="access-tagline">{s.tagline}</p>
            </div>
            <ul className="points" aria-label={s.whatThisIs}>
              {s.points.map((p, i) => (
                <li key={p.title} className="point">
                  <span className="point-ic">
                    <Icon name={POINT_ICONS[i] ?? "check"} />
                  </span>
                  <div>
                    <p className="point-title">{p.title}</p>
                    <p className="point-body t-small regular muted">{p.body}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <form onSubmit={submit} className="card access-card" aria-labelledby="ac-title">
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <h2 id="ac-title" className="t-h1">
                {s.loginTitle}
              </h2>
              <p className="muted">{s.loginHelp}</p>
            </div>
            <div className="field">
              <label htmlFor="code">{s.accessCode}</label>
              <input
                id="code"
                name="code"
                className="input"
                type="password"
                autoComplete="current-password"
                required
                value={code}
                onChange={(e) => {
                  setCode(e.target.value);
                  if (error) setError(null);
                }}
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? "code-error" : undefined}
              />
              {error && (
                <p id="code-error" className="field-error" role="alert">
                  <Icon name="circleAlert" />
                  {error}
                </p>
              )}
            </div>
            <button type="submit" className="btn btn-primary btn-block" disabled={busy || !code}>
              {busy ? (
                <>
                  <Icon name="loader" className="spin" />
                  {s.checking}
                </>
              ) : (
                s.enter
              )}
            </button>
          </form>
        </div>
      </main>
      <Disclaimer lang={lang} />
    </div>
  );
}
