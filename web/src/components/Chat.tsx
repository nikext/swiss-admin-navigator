"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { citationLabel } from "@/lib/cite";
import type { Answer, Citation, Lang, Step, UiEvent } from "@/lib/contract";
import { STRINGS } from "@/lib/i18n";
import { LineSplitter } from "@/lib/lines";

import AnswerView from "./AnswerView";
import ArticlePanel from "./ArticlePanel";
import { Brand, LangSelect, Notice } from "./Shell";

type Msg =
  | { id: string; role: "user"; text: string }
  | {
      id: string;
      role: "assistant";
      state: "pending" | "done" | "error";
      steps: { step: Step; detail?: string }[];
      answer?: Answer;
      error?: string;
      rated?: "up" | "down";
    };

interface Saved {
  sessionId: string | null;
  messages: Msg[];
}

const STORE = "nav_chat";

function loadSaved(): Saved | null {
  try {
    const raw = sessionStorage.getItem(STORE);
    return raw ? (JSON.parse(raw) as Saved) : null;
  } catch {
    return null;
  }
}

function save(s: Saved): void {
  try {
    sessionStorage.setItem(STORE, JSON.stringify(s));
  } catch {
    // private mode or full: the chat still works, it just isn't restored on reload
  }
}

const uid = () => Math.random().toString(36).slice(2, 10);

export default function Chat({ initialLang, userQuota }: { initialLang: Lang; userQuota: number }) {
  const [lang, setLang] = useState<Lang>(initialLang);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [quota, setQuota] = useState<number | null>(null);
  const [panel, setPanel] = useState<Citation | null>(null);
  const [startedAt, setStartedAt] = useState(0);
  const [now, setNow] = useState(0);
  const bottom = useRef<HTMLDivElement>(null);
  const abort = useRef<AbortController | null>(null);
  const s = STRINGS[lang];

  useEffect(() => {
    const saved = loadSaved();
    if (saved) {
      // Restored after hydration: the server render can't see sessionStorage.
      // A reload mid-answer loses the stream; show those as failed instead of spinning.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMessages(
        saved.messages.map((m) =>
          m.role === "assistant" && m.state === "pending" ? { ...m, state: "error" } : m,
        ),
      );
      setSessionId(saved.sessionId);
    }
    fetch("/api/quota")
      .then((r) => (r.ok ? r.json() : null))
      .then((d: { remaining?: { user: number; global: number } } | null) => {
        if (d?.remaining) setQuota(Math.min(d.remaining.user, d.remaining.global));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    save({ sessionId, messages });
  }, [sessionId, messages]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  useEffect(() => {
    if (!busy) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [busy]);
  const elapsed = Math.max(0, Math.round((now - startedAt) / 1000));

  const update = useCallback((id: string, f: (m: Extract<Msg, { role: "assistant" }>) => Msg) => {
    setMessages((ms) => ms.map((m) => (m.id === id && m.role === "assistant" ? f(m) : m)));
  }, []);

  async function ask(text: string) {
    const question = text.trim();
    if (!question || busy) return;
    const aid = uid();
    setMessages((ms) => [
      ...ms,
      { id: uid(), role: "user", text: question },
      { id: aid, role: "assistant", state: "pending", steps: [] },
    ]);
    setInput("");
    setStartedAt(Date.now());
    setNow(Date.now());
    setBusy(true);
    const ctrl = new AbortController();
    abort.current = ctrl;
    let finished = false;
    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question, sessionId }),
        signal: ctrl.signal,
      });
      if (resp.status === 401) {
        window.location.reload();
        return;
      }
      if (!resp.ok || !resp.body) {
        const err = (await resp.json().catch(() => ({}))) as { code?: string };
        const msg =
          err.code === "quota_user"
            ? s.quotaUser
            : err.code === "quota_global"
              ? s.quotaGlobal
              : s.errorGeneric;
        if (err.code?.startsWith("quota")) setQuota(0);
        update(aid, (m) => ({ ...m, state: "error", error: msg }));
        finished = true;
        return;
      }
      const reader = resp.body.getReader();
      const lines = new LineSplitter();
      for (;;) {
        const { done, value } = await reader.read();
        for (const line of done ? lines.flush() : lines.push(value)) {
          const e = JSON.parse(line) as UiEvent;
          if (e.type === "session") setSessionId(e.sessionId);
          else if (e.type === "quota") setQuota(Math.min(e.user, e.global));
          else if (e.type === "progress") {
            update(aid, (m) => ({ ...m, steps: [...m.steps, { step: e.step, detail: e.detail }] }));
          } else if (e.type === "answer") {
            finished = true;
            update(aid, (m) => ({ ...m, state: "done", answer: e.answer }));
          } else if (e.type === "error") {
            finished = true;
            update(aid, (m) => ({ ...m, state: "error", error: s.errorGeneric }));
          }
        }
        if (done) break;
      }
    } catch {
      // network drop or abort; handled below
    } finally {
      if (!finished) update(aid, (m) => ({ ...m, state: "error", error: s.errorNetwork }));
      abort.current = null;
      setBusy(false);
    }
  }

  async function newChat() {
    abort.current?.abort();
    const old = sessionId;
    setMessages([]);
    setSessionId(null);
    setPanel(null);
    if (old) {
      await fetch("/api/session", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId: old }),
      }).catch(() => {});
    }
  }

  async function logout() {
    await newChat();
    await fetch("/api/logout", { method: "POST" }).catch(() => {});
    window.location.reload();
  }

  async function rate(id: string, answer: Answer, rating: "up" | "down") {
    update(id, (m) => ({ ...m, rated: rating }));
    if (!sessionId) return;
    await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rating,
        sessionId,
        language: answer.language,
        citations: answer.citations.map((c) => citationLabel(c, "para.", "let.")),
        verification: answer.verification?.status,
        confidence: answer.confidence,
      }),
    }).catch(() => {});
  }

  const empty = messages.length === 0;

  return (
    <div className="page">
      <header className="topbar">
        <Brand lang={lang} />
        <div className="actions">
          <LangSelect lang={lang} onChange={setLang} />
          {!empty && (
            <button type="button" className="ghost" onClick={newChat}>
              {s.newChat}
            </button>
          )}
          <button type="button" className="ghost" onClick={logout}>
            {s.logout}
          </button>
        </div>
      </header>

      <main className="chat">
        {empty && (
          <section className="examples" aria-labelledby="examples-title">
            <h2 id="examples-title">{s.examplesTitle}</h2>
            <ul>
              {s.examples.map((q) => (
                <li key={q}>
                  <button type="button" onClick={() => ask(q)} disabled={busy} lang={lang}>
                    {q}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}

        <ol className="messages" aria-label="Conversation">
          {messages.map((m) =>
            m.role === "user" ? (
              <li key={m.id} className="msg user">
                <span className="sr-only">{s.you}: </span>
                <p>{m.text}</p>
              </li>
            ) : (
              <li key={m.id} className="msg assistant">
                <span className="sr-only">{s.assistant}: </span>
                {m.state === "pending" && (
                  <div className="pending">
                    <p className="thinking" role="status" aria-live="polite">
                      <span className="spinner" aria-hidden="true" />
                      {m.steps.length
                        ? `${s.steps[m.steps.at(-1)!.step]}${m.steps.at(-1)!.detail ? `: ${m.steps.at(-1)!.detail}` : ""}`
                        : s.thinking}
                      <span className="muted"> · {elapsed}s</span>
                    </p>
                    {m.steps.length > 1 && (
                      <ul className="steps muted small">
                        {m.steps.slice(0, -1).map((st, i) => (
                          <li key={i}>
                            {s.steps[st.step]}
                            {st.detail ? `: ${st.detail}` : ""}
                          </li>
                        ))}
                      </ul>
                    )}
                    <p className="muted small">{s.slowHint}</p>
                  </div>
                )}
                {m.state === "error" && (
                  <p className="error" role="alert">
                    {m.error ?? s.errorGeneric}
                  </p>
                )}
                {m.state === "done" && m.answer && (
                  <>
                    <AnswerView
                      answer={m.answer}
                      lang={lang}
                      onCite={setPanel}
                      onAsk={ask}
                      disabled={busy}
                    />
                    <div
                      className="feedback"
                      role="group"
                      aria-label={`${s.helpful} / ${s.notHelpful}`}
                    >
                      {m.rated ? (
                        <p className="muted small" role="status">
                          {s.thanks}
                        </p>
                      ) : (
                        <>
                          <button
                            type="button"
                            className="icon"
                            aria-label={s.helpful}
                            onClick={() => rate(m.id, m.answer!, "up")}
                          >
                            👍
                          </button>
                          <button
                            type="button"
                            className="icon"
                            aria-label={s.notHelpful}
                            onClick={() => rate(m.id, m.answer!, "down")}
                          >
                            👎
                          </button>
                        </>
                      )}
                    </div>
                  </>
                )}
              </li>
            ),
          )}
        </ol>
        <div ref={bottom} />
      </main>

      <form
        className="composer"
        aria-label={s.send}
        onSubmit={(e) => {
          e.preventDefault();
          void ask(input);
        }}
      >
        <label htmlFor="question" className="sr-only">
          {s.askPlaceholder}
        </label>
        <textarea
          id="question"
          rows={2}
          maxLength={2000}
          placeholder={s.askPlaceholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              void ask(input);
            }
          }}
        />
        <button type="submit" className="primary" disabled={busy || !input.trim() || quota === 0}>
          {s.send}
        </button>
        {quota !== null && (
          <p className="quota muted small" aria-live="polite">
            {quota === 0 ? s.quotaUser : s.quotaLeft(quota, userQuota)}
          </p>
        )}
      </form>

      <Notice lang={lang} />
      {panel && (
        <ArticlePanel
          key={`${panel.sr}-${panel.article}-${panel.ref}`}
          citation={panel}
          lang={lang}
          onClose={() => setPanel(null)}
        />
      )}
    </div>
  );
}
