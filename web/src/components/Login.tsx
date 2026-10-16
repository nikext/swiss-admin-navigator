"use client";

import { useState } from "react";

import type { Lang } from "@/lib/contract";
import { STRINGS } from "@/lib/i18n";

import { Brand, LangSelect, Notice } from "./Shell";

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
    <div className="page">
      <header className="topbar">
        <Brand lang={lang} />
        <LangSelect lang={lang} onChange={setLang} />
      </header>
      <main className="login">
        <form onSubmit={submit} className="card">
          <h2>{s.loginTitle}</h2>
          <p className="muted">{s.loginHelp}</p>
          <label htmlFor="code">{s.accessCode}</label>
          <input
            id="code"
            name="code"
            type="password"
            autoComplete="current-password"
            required
            value={code}
            onChange={(e) => setCode(e.target.value)}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? "code-error" : undefined}
          />
          {error && (
            <p id="code-error" className="error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="primary" disabled={busy || !code}>
            {s.enter}
          </button>
        </form>
      </main>
      <Notice lang={lang} />
    </div>
  );
}
