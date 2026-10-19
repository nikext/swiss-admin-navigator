"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

import { citationLabel } from "@/lib/cite";
import type { Answer, Citation, Lang, UiEvent } from "@/lib/contract";
import { STRINGS, type Domain } from "@/lib/i18n";
import { LineSplitter } from "@/lib/lines";
import { count, COUNTER_FROM, MAX_CHARS, type TrailStep } from "@/lib/present";

import AnswerView from "./AnswerView";
import ArticlePanel from "./ArticlePanel";
import Icon, { type IconName } from "./Icon";
import MemoryPanel from "./MemoryPanel";
import { Brand, Disclaimer, LangMenu, Menu } from "./Shell";
import { WorkCard } from "./Trail";

type Failure = "generic" | "network" | "quota_user" | "quota_global";

type Msg =
  | { id: string; role: "user"; text: string }
  | {
      id: string;
      role: "assistant";
      question: string;
      state: "pending" | "done" | "error";
      steps: TrailStep[];
      took?: number;
      answer?: Answer;
      error?: Failure;
      rated?: "up" | "down";
    };

type AssistantMsg = Extract<Msg, { role: "assistant" }>;

interface Saved {
  sessionId: string | null;
  messages: Msg[];
}

const STORE = "nav_chat";

const DOMAIN_ICONS: Record<Domain, IconName> = {
  housing: "house",
  work: "briefcase",
  social: "umbrella",
  residence: "idCard",
  mobility: "car",
  tax: "receipt",
};

function loadSaved(): Saved | null {
  try {
    const raw = sessionStorage.getItem(STORE);
    if (!raw) return null;
    const saved = JSON.parse(raw) as Saved;
    // Older saves have no question, step times or durations; keep them readable.
    saved.messages = saved.messages.map((m, i, all) => {
      if (m.role !== "assistant") return m;
      const prev = all[i - 1];
      return {
        ...m,
        question: m.question ?? (prev?.role === "user" ? prev.text : ""),
        steps: (m.steps ?? []).map((st) => ({ ...st, at: st.at ?? 0 })),
      };
    });
    return saved;
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

/** A CSS media query as React state (false on the server). */
function useMedia(query: string): boolean {
  const subscribe = useCallback(
    (notify: () => void) => {
      const mq = window.matchMedia(query);
      mq.addEventListener("change", notify);
      return () => mq.removeEventListener("change", notify);
    },
    [query],
  );
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(query).matches,
    () => false,
  );
}

export default function Chat({
  initialLang,
  userQuota,
  initialMemory,
}: {
  initialLang: Lang;
  userQuota: number;
  initialMemory: boolean;
}) {
  const [lang, setLang] = useState<Lang>(initialLang);
  const [memoryOn, setMemoryOn] = useState(initialMemory);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [quota, setQuota] = useState<number | null>(null);
  const [quotaReason, setQuotaReason] = useState<"user" | "global">("user");
  const [panel, setPanel] = useState<{ msgId: string; citation: Citation } | null>(null);
  const [startedAt, setStartedAt] = useState(0);
  const [now, setNow] = useState(0);
  const bottom = useRef<HTMLDivElement>(null);
  const textarea = useRef<HTMLTextAreaElement>(null);
  const abort = useRef<AbortController | null>(null);
  const opener = useRef<HTMLElement | null>(null);
  const docked = useMedia("(min-width: 1100px)");
  const s = STRINGS[lang];

  useEffect(() => {
    const saved = loadSaved();
    if (saved) {
      // Restored after hydration: the server render can't see sessionStorage.
      // A reload mid-answer loses the stream; show those as failed instead of spinning.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMessages(
        saved.messages.map((m) =>
          m.role === "assistant" && m.state === "pending"
            ? { ...m, state: "error", error: "network" }
            : m,
        ),
      );
      setSessionId(saved.sessionId);
    }
    fetch("/api/quota")
      .then((r) => (r.ok ? r.json() : null))
      .then((d: { remaining?: { user: number; global: number } } | null) => {
        if (d?.remaining) {
          setQuota(Math.min(d.remaining.user, d.remaining.global));
          setQuotaReason(d.remaining.global < d.remaining.user ? "global" : "user");
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    save({ sessionId, messages });
  }, [sessionId, messages]);

  useEffect(() => {
    if (messages.length) bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  useEffect(() => {
    if (!busy) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [busy]);

  const update = useCallback((id: string, f: (m: AssistantMsg) => Msg) => {
    setMessages((ms) => ms.map((m) => (m.id === id && m.role === "assistant" ? f(m) : m)));
  }, []);

  async function ask(text: string) {
    const question = text.trim();
    if (!question || busy) return;
    const aid = uid();
    const t0 = Date.now();
    setMessages((ms) => [
      ...ms,
      { id: uid(), role: "user", text: question },
      { id: aid, role: "assistant", question, state: "pending", steps: [] },
    ]);
    setInput("");
    setStartedAt(t0);
    setNow(t0);
    setBusy(true);
    const ctrl = new AbortController();
    abort.current = ctrl;
    let finished = false;
    const fail = (error: Failure) => {
      finished = true;
      update(aid, (m) => ({ ...m, state: "error", error }));
    };
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
        if (err.code === "quota_user" || err.code === "quota_global") {
          setQuota(0);
          setQuotaReason(err.code === "quota_global" ? "global" : "user");
          fail(err.code);
        } else fail("generic");
        return;
      }
      const reader = resp.body.getReader();
      const lines = new LineSplitter();
      for (;;) {
        const { done, value } = await reader.read();
        for (const line of done ? lines.flush() : lines.push(value)) {
          const e = JSON.parse(line) as UiEvent;
          if (e.type === "session") setSessionId(e.sessionId);
          else if (e.type === "quota") {
            setQuota(Math.min(e.user, e.global));
            setQuotaReason(e.global < e.user ? "global" : "user");
          } else if (e.type === "progress") {
            const at = Date.now() - t0;
            update(aid, (m) => ({
              ...m,
              steps: [...m.steps, { step: e.step, detail: e.detail, at }],
            }));
          } else if (e.type === "answer") {
            finished = true;
            const took = Math.round((Date.now() - t0) / 1000);
            update(aid, (m) => ({ ...m, state: "done", answer: e.answer, took }));
          } else if (e.type === "error") {
            fail("generic");
          }
        }
        if (done) break;
      }
    } catch {
      // network drop or abort; handled below
    } finally {
      if (!finished) update(aid, (m) => ({ ...m, state: "error", error: "network" }));
      abort.current = null;
      setBusy(false);
    }
  }

  /** Drops the failed turn and asks its question again. */
  function retry(m: AssistantMsg) {
    setMessages((ms) => {
      const i = ms.findIndex((x) => x.id === m.id);
      return i > 0 && ms[i - 1]?.role === "user" ? [...ms.slice(0, i - 1), ...ms.slice(i + 1)] : ms;
    });
    void ask(m.question);
  }

  function openCitation(msgId: string, citation: Citation) {
    if (panel?.msgId === msgId && panel.citation.ref === citation.ref) {
      closePanel();
      return;
    }
    opener.current = document.activeElement as HTMLElement | null;
    setPanel({ msgId, citation });
  }

  function closePanel() {
    setPanel(null);
    const el = opener.current;
    opener.current = null;
    if (el?.isConnected) requestAnimationFrame(() => el.focus());
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
    textarea.current?.focus();
  }

  /** The memory switch changed or everything was forgotten; the BFF ended the sessions. */
  function memoryReset(enabled: boolean) {
    abort.current?.abort();
    setMemoryOn(enabled);
    setMessages([]);
    setSessionId(null);
    setPanel(null);
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
  const outOfQuota = quota === 0;
  const quotaMessage = quotaReason === "global" ? s.quotaGlobal : s.quotaUser;
  const placeholder = outOfQuota
    ? s.quotaPlaceholder
    : busy
      ? s.waitPlaceholder
      : empty
        ? s.askPlaceholder
        : s.followUpPlaceholder;
  const turns = pairTurns(messages);

  // The composer grows with its text (or a wrapping placeholder), up to its max-height.
  useEffect(() => {
    const t = textarea.current;
    if (!t) return;
    t.style.height = "auto";
    t.style.height = `${t.scrollHeight}px`;
  }, [input, placeholder]);
  const memoryLabel = `${s.memory}: ${memoryOn ? s.memoryOn : s.memoryOff}`;

  return (
    <div className="shell">
      <header className="topbar">
        <Brand />
        <nav className="topbar-actions" aria-label={s.account}>
          {!empty && (
            <button type="button" className="btn btn-ghost only-wide" onClick={newChat}>
              <Icon name="squarePen" />
              {s.newChat}
            </button>
          )}
          <LangMenu lang={lang} onChange={setLang} />
          <button
            type="button"
            className="btn btn-ghost mem-btn only-wide"
            aria-haspopup="dialog"
            onClick={() => setMemoryOpen(true)}
          >
            <span className={`dot${memoryOn ? "" : " off"}`} aria-hidden="true" />
            {memoryLabel}
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-icon mem-btn only-narrow"
            aria-haspopup="dialog"
            aria-label={memoryLabel}
            onClick={() => setMemoryOpen(true)}
          >
            <Icon name="stickyNote" size={20} />
            <span className={`dot corner${memoryOn ? "" : " off"}`} aria-hidden="true" />
          </button>
          <button type="button" className="btn btn-ghost only-wide" onClick={logout}>
            <Icon name="logOut" />
            {s.logout}
          </button>
          <span className="only-narrow">
            <Menu
              label={s.more}
              buttonLabel={s.more}
              buttonClass="btn btn-ghost btn-icon"
              button={<Icon name="moreVertical" size={20} />}
              items={[
                ...(empty
                  ? []
                  : [
                      {
                        key: "new",
                        label: s.newChat,
                        icon: "squarePen" as const,
                        onSelect: newChat,
                      },
                    ]),
                { key: "out", label: s.logout, icon: "logOut" as const, onSelect: logout },
              ]}
            />
          </span>
        </nav>
      </header>

      <div className="main">
        {/* Focusable so the conversation scrolls by keyboard even when nothing in it is. */}
        <div className="chat-pane" tabIndex={0}>
          <main className={`chat${empty ? " is-empty" : ""}`}>
            {empty ? (
              <>
                <div className="hero">
                  <h1 className="t-display">{s.heroTitle}</h1>
                  <p className="hero-sub t-body-lg muted">{s.heroSub}</p>
                </div>
                <section className="examples-section" aria-labelledby="examples-title">
                  <h2 id="examples-title" className="t-label muted">
                    {s.examplesTitle}
                  </h2>
                  <ul className="examples">
                    {s.examples.map((ex) => (
                      <li key={ex.q}>
                        <button
                          type="button"
                          className="ex"
                          onClick={() => ask(ex.q)}
                          disabled={busy || outOfQuota}
                          lang={lang}
                        >
                          <span className="tag">
                            <Icon name={DOMAIN_ICONS[ex.domain]} size={14} />
                            {s.domains[ex.domain]}
                          </span>
                          {ex.q}
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>
              </>
            ) : (
              <>
                <h1 className="sr-only">Swiss Admin Navigator</h1>
                <ol className="turns" aria-label={s.assistant}>
                  {turns.map(({ user, reply }) => (
                    <li key={reply?.id ?? user.id} className="turn">
                      <p className="msg-user">
                        <span className="sr-only">{s.you}: </span>
                        {user.text}
                      </p>
                      {reply && (
                        <Reply
                          m={reply}
                          lang={lang}
                          busy={busy}
                          elapsedMs={now - startedAt}
                          activeRef={panel?.msgId === reply.id ? panel.citation.ref : null}
                          onCite={(c) => openCitation(reply.id, c)}
                          onAsk={ask}
                          onRetry={() => retry(reply)}
                          onRate={(r) => reply.answer && rate(reply.id, reply.answer, r)}
                          quotaMessage={quotaMessage}
                        />
                      )}
                    </li>
                  ))}
                </ol>
              </>
            )}
            <div ref={bottom} />
          </main>

          <div className="dock">
            <form
              className="dock-inner"
              aria-label={s.send}
              onSubmit={(e) => {
                e.preventDefault();
                void ask(input);
              }}
            >
              <div className={`composer${busy || outOfQuota ? " is-disabled" : ""}`}>
                <label htmlFor="question" className="sr-only">
                  {s.yourQuestion}
                </label>
                <textarea
                  id="question"
                  ref={textarea}
                  rows={1}
                  maxLength={MAX_CHARS}
                  placeholder={placeholder}
                  value={input}
                  disabled={outOfQuota}
                  aria-describedby="composer-meta"
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                      e.preventDefault();
                      void ask(input);
                    }
                  }}
                />
                <button
                  type="submit"
                  className="btn btn-primary send"
                  aria-label={s.send}
                  disabled={busy || !input.trim() || outOfQuota}
                >
                  <span className="only-wide">{s.send}</span>
                  <Icon name="arrowUp" />
                </button>
              </div>
              <div className="composer-meta" id="composer-meta">
                {outOfQuota ? (
                  <span className="limit" role="status">
                    <Icon name="clock" />
                    {quotaMessage}
                  </span>
                ) : (
                  <span aria-live="polite">{quota !== null && s.quotaLeft(quota, userQuota)}</span>
                )}
                {input.length >= COUNTER_FROM ? (
                  <span className="count">
                    {count(input.length, lang)} / {count(MAX_CHARS, lang)}
                  </span>
                ) : (
                  !outOfQuota && (
                    <span className="keys" aria-hidden="true">
                      <kbd>Enter</kbd> {s.toSend} · <kbd>Shift</kbd>+<kbd>Enter</kbd> {s.newLine}
                    </span>
                  )
                )}
              </div>
            </form>
          </div>
        </div>

        {panel && docked && (
          <ArticlePanel
            key={`${panel.msgId}-${panel.citation.ref}`}
            citation={panel.citation}
            lang={lang}
            docked
            onClose={closePanel}
          />
        )}
      </div>

      <Disclaimer lang={lang} />

      {panel && !docked && (
        <ArticlePanel
          key={`${panel.msgId}-${panel.citation.ref}`}
          citation={panel.citation}
          lang={lang}
          docked={false}
          onClose={closePanel}
        />
      )}
      {memoryOpen && (
        <MemoryPanel
          lang={lang}
          enabled={memoryOn}
          onReset={memoryReset}
          onClose={() => setMemoryOpen(false)}
        />
      )}
    </div>
  );
}

/** Messages alternate user → assistant; a turn is one question and its reply. */
function pairTurns(messages: Msg[]) {
  const turns: { user: Extract<Msg, { role: "user" }>; reply?: AssistantMsg }[] = [];
  for (const m of messages) {
    if (m.role === "user") turns.push({ user: m });
    else if (turns.length && !turns.at(-1)!.reply) turns.at(-1)!.reply = m;
  }
  return turns;
}

function Reply({
  m,
  lang,
  busy,
  elapsedMs,
  activeRef,
  onCite,
  onAsk,
  onRetry,
  onRate,
  quotaMessage,
}: {
  m: AssistantMsg;
  lang: Lang;
  busy: boolean;
  elapsedMs: number;
  activeRef: string | null;
  onCite: (c: Citation) => void;
  onAsk: (q: string) => void;
  onRetry: () => void;
  onRate: (r: "up" | "down") => void;
  quotaMessage: string;
}) {
  const s = STRINGS[lang];
  if (m.state === "pending") return <WorkCard steps={m.steps} lang={lang} elapsedMs={elapsedMs} />;
  if (m.state === "done" && m.answer) {
    return (
      <AnswerView
        answer={m.answer}
        lang={lang}
        steps={m.steps}
        took={m.took ?? null}
        activeRef={activeRef}
        onCite={onCite}
        onAsk={onAsk}
        disabled={busy}
        rated={m.rated}
        onRate={onRate}
      />
    );
  }
  const quota = m.error === "quota_user" || m.error === "quota_global";
  const title = quota ? s.quotaTitle : m.error === "network" ? s.networkTitle : s.errorTitle;
  const body = quota ? quotaMessage : m.error === "network" ? s.errorNetwork : s.errorGeneric;
  return (
    <div className={`callout ${quota ? "callout-warn" : "callout-error"}`} role="alert">
      <Icon name={quota ? "clock" : "triangleAlert"} size={20} />
      <div>
        <p className="callout-title">{title}</p>
        <p className="callout-body">{body}</p>
        {!quota && (
          <div className="callout-actions">
            <button type="button" className="btn btn-secondary" onClick={onRetry} disabled={busy}>
              <Icon name="rotateCcw" />
              {s.tryAgain}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
