"use client";

import { useEffect, useRef, useState } from "react";

import type { Lang } from "@/lib/contract";
import { STRINGS } from "@/lib/i18n";
import { describe, FIELD_ORDER, type Profile } from "@/lib/profile";

interface Props {
  lang: Lang;
  enabled: boolean;
  /** The switch changed or everything was forgotten: the conversation starts over. */
  onReset: (enabled: boolean) => void;
  onClose: () => void;
}

type Load = { profile: Profile } | "error" | null; // null: loading

/**
 * Opt-in memory (M7, ADR-029): the switch, what is remembered (whitelisted
 * fields only, as the BFF returns them) and "Forget me".
 */
export default function MemoryPanel({ lang, enabled, onReset, onClose }: Props) {
  const s = STRINGS[lang];
  const dialog = useRef<HTMLDialogElement>(null);
  const [load, setLoad] = useState<Load>(null);
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    const d = dialog.current;
    if (d && !d.open) d.showModal();
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    fetch("/api/memory", { signal: ctrl.signal })
      .then(async (r) => {
        if (!r.ok) throw new Error(String(r.status));
        const d = (await r.json()) as { profile: Profile };
        setLoad({ profile: d.profile });
      })
      .catch(() => {
        if (!ctrl.signal.aborted) setLoad("error");
      });
    return () => ctrl.abort();
  }, []);

  async function toggle(next: boolean) {
    setBusy(true);
    setStatus(null);
    try {
      const r = await fetch("/api/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: next }),
      });
      if (!r.ok) throw new Error(String(r.status));
      onReset(next);
    } catch {
      setStatus(s.memoryError);
    } finally {
      setBusy(false);
    }
  }

  async function forgetAll() {
    setBusy(true);
    setStatus(null);
    try {
      const r = await fetch("/api/memory", { method: "DELETE" });
      if (!r.ok) throw new Error(String(r.status));
      setLoad({ profile: {} });
      setStatus(s.forgotten);
      onReset(enabled);
    } catch {
      setStatus(s.memoryError);
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  }

  const profile = load && load !== "error" ? load.profile : null;
  const fields = profile ? FIELD_ORDER.filter((f) => profile[f] !== undefined) : [];

  return (
    <dialog
      ref={dialog}
      className="panel"
      aria-labelledby="memory-title"
      onClose={onClose}
      onClick={(e) => {
        if (e.target === dialog.current) dialog.current?.close(); // backdrop click
      }}
    >
      <div className="panel-inner memory">
        <header className="panel-head">
          <h2 id="memory-title">{s.memory}</h2>
          <button
            type="button"
            className="icon"
            onClick={() => dialog.current?.close()}
            aria-label={s.close}
          >
            ×
          </button>
        </header>

        <p>{s.memoryIntro}</p>
        <p className="small">{s.memoryKeeps}</p>
        <p className="small">{s.memoryNever}</p>

        <label className="switch">
          <input
            type="checkbox"
            checked={enabled}
            disabled={busy}
            onChange={(e) => void toggle(e.target.checked)}
          />
          <span>{s.memorySwitch}</span>
        </label>
        <p className="muted small">{s.memoryRestart}</p>

        <h3>{s.rememberTitle}</h3>
        {load === null && (
          <p role="status" className="muted">
            {s.loading}
          </p>
        )}
        {load === "error" && (
          <p role="alert" className="error">
            {s.memoryError}
          </p>
        )}
        {profile && fields.length === 0 && <p className="muted">{s.rememberEmpty}</p>}
        {profile && fields.length > 0 && (
          <ul className="remembered">
            {fields.map((f) => (
              <li key={f}>{describe(f, profile[f]!, lang)}</li>
            ))}
          </ul>
        )}
        {enabled && <p className="muted small">{s.rememberDelay}</p>}

        <div className="forget">
          {confirming ? (
            <>
              <p>{s.forgetConfirm}</p>
              <button
                type="button"
                className="danger"
                disabled={busy}
                onClick={() => void forgetAll()}
              >
                {s.forget}
              </button>{" "}
              <button type="button" className="ghost" onClick={() => setConfirming(false)}>
                {s.close}
              </button>
            </>
          ) : (
            <button
              type="button"
              className="ghost"
              disabled={busy}
              onClick={() => setConfirming(true)}
            >
              {s.forget}
            </button>
          )}
        </div>
        {status && (
          <p role="status" className="small">
            {status}
          </p>
        )}
      </div>
    </dialog>
  );
}
