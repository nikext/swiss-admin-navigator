"use client";

import { useEffect, useRef, useState } from "react";

import type { Lang } from "@/lib/contract";
import { STRINGS } from "@/lib/i18n";
import { describeParts, FIELD_ORDER, type Profile } from "@/lib/profile";

import Icon from "./Icon";

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
 * fields only, as the BFF returns them), the keep/never policy and "Forget me".
 * Centred modal; full screen on phones.
 */
export default function MemoryPanel({ lang, enabled, onReset, onClose }: Props) {
  const s = STRINGS[lang];
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const [load, setLoad] = useState<Load>(null);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [forgotten, setForgotten] = useState(false);
  const [failed, setFailed] = useState(false);

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
  }, [attempt]);

  useEffect(() => {
    if (confirming) cancel.current?.focus();
  }, [confirming]);

  async function toggle(next: boolean) {
    setBusy(true);
    setFailed(false);
    setForgotten(false);
    try {
      const r = await fetch("/api/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: next }),
      });
      if (!r.ok) throw new Error(String(r.status));
      onReset(next);
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  async function forgetAll() {
    setBusy(true);
    setFailed(false);
    try {
      const r = await fetch("/api/memory", { method: "DELETE" });
      if (!r.ok) throw new Error(String(r.status));
      setLoad({ profile: {} });
      setForgotten(true);
      onReset(enabled);
    } catch {
      setFailed(true);
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
      className="dialog"
      aria-labelledby="memory-title"
      aria-describedby="memory-intro"
      onClose={onClose}
      onClick={(e) => {
        if (e.target === dialog.current) dialog.current?.close(); // backdrop click
      }}
    >
      <div className="dialog-head">
        <h2 id="memory-title" className="t-h1">
          {s.memory}
        </h2>
        <button
          type="button"
          className="btn btn-ghost btn-icon"
          onClick={() => dialog.current?.close()}
          aria-label={s.close}
        >
          <Icon name="x" size={20} />
        </button>
      </div>

      <div className="dialog-body">
        <p id="memory-intro" className="muted">
          {s.memoryIntro}
        </p>

        <div className="switch-row">
          <div>
            <label id="memory-switch-label" htmlFor="memory-switch">
              {s.memorySwitch}
            </label>
            <p className="t-small regular subtle">{s.memoryRestart}</p>
          </div>
          <button
            id="memory-switch"
            type="button"
            className="switch"
            role="switch"
            aria-checked={enabled}
            aria-labelledby="memory-switch-label"
            disabled={busy || load === null}
            onClick={() => void toggle(!enabled)}
          />
        </div>

        {forgotten && (
          <p className="done" role="status">
            <Icon name="check" />
            {s.forgotten}
          </p>
        )}
        {failed && (
          <p className="field-error" role="alert">
            <Icon name="circleAlert" />
            {s.memoryError}
          </p>
        )}

        <section className="remember" aria-labelledby="remember-title" aria-busy={load === null}>
          <div className="remember-head">
            <h3 id="remember-title" className="t-h2">
              {s.rememberTitle}
            </h3>
            {enabled && <span className="t-small regular subtle">{s.rememberDelay}</span>}
          </div>
          {load === null && (
            <p
              role="status"
              className="t-small subtle"
              style={{ display: "flex", gap: 8, alignItems: "center" }}
            >
              <Icon name="loader" className="spin" />
              {s.loading}
            </p>
          )}
          {load === "error" && (
            <div className="callout callout-error" role="alert">
              <Icon name="triangleAlert" size={20} />
              <div>
                <p className="callout-body">{s.memoryError}</p>
                <div className="callout-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setLoad(null);
                      setAttempt((a) => a + 1);
                    }}
                  >
                    <Icon name="rotateCcw" />
                    {s.tryAgain}
                  </button>
                </div>
              </div>
            </div>
          )}
          {profile && fields.length === 0 && <p className="muted">{s.rememberEmpty}</p>}
          {profile && fields.length > 0 && (
            <dl className="facts">
              {fields.map((f) => {
                const { label, value } = describeParts(f, profile[f]!, lang);
                return (
                  <div key={f} className="fact">
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                );
              })}
            </dl>
          )}
        </section>

        <div className="policy">
          <div className="policy-col keep">
            <h3 className="policy-head">
              <Icon name="check" />
              {s.keepTitle}
            </h3>
            <ul className="policy-list">
              {s.keepList.map((item) => (
                <li key={item}>
                  <Icon name="check" size={14} />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="policy-col never">
            <h3 className="policy-head">
              <Icon name="lock" />
              {s.neverTitle}
            </h3>
            <ul className="policy-list">
              {s.neverList.map((item) => (
                <li key={item}>
                  <Icon name="ban" size={14} />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <p className="expiry t-small regular subtle">
          <Icon name="clock" />
          {s.memoryExpiry}
        </p>
      </div>

      <div className="dialog-foot">
        {confirming ? (
          <div className="confirm">
            <p>{s.forgetConfirm}</p>
            <div className="confirm-actions">
              <button
                ref={cancel}
                type="button"
                className="btn btn-secondary"
                onClick={() => setConfirming(false)}
              >
                {s.cancel}
              </button>
              <button
                type="button"
                className="btn btn-danger"
                disabled={busy}
                onClick={() => void forgetAll()}
              >
                {busy ? (
                  <>
                    <Icon name="loader" className="spin" />
                    {s.deleting}
                  </>
                ) : (
                  <>
                    <Icon name="trash" />
                    {s.forget}
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <>
            <button
              type="button"
              className="btn btn-danger-outline"
              disabled={busy}
              onClick={() => setConfirming(true)}
            >
              <Icon name="trash" />
              {s.forget}
            </button>
            <span className="spacer" />
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => dialog.current?.close()}
            >
              {s.done}
            </button>
          </>
        )}
      </div>
    </dialog>
  );
}
