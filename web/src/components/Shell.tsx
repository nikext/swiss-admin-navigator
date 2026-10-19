"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";

import { LANGS, type Lang } from "@/lib/contract";
import { LANG_NAMES, STRINGS } from "@/lib/i18n";

import Icon, { type IconName } from "./Icon";

/** Saves the UI language for the next visit (a preference, not personal data). */
export function saveLang(lang: Lang): void {
  document.cookie = `nav_lang=${lang}; path=/; max-age=31536000; samesite=lax`;
  document.documentElement.lang = lang;
}

export interface MenuItem {
  key: string;
  label: string;
  icon?: IconName;
  /** Set for a radio menu: the current choice. */
  checked?: boolean;
  code?: string;
  lang?: string;
  onSelect: () => void;
}

/**
 * A button with a popup menu (role=menu): arrow keys, Home/End, Esc returns focus
 * to the button, a click outside or Tab closes it.
 */
export function Menu({
  label,
  buttonLabel,
  button,
  buttonClass,
  items,
  radio = false,
}: {
  /** The menu's name; also the button's unless the button has visible text. */
  label: string;
  buttonLabel?: string;
  button: ReactNode;
  buttonClass: string;
  items: MenuItem[];
  radio?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const list = useRef<HTMLDivElement>(null);
  const id = useId();

  useEffect(() => {
    if (!open) return;
    const items = [
      ...(list.current?.querySelectorAll<HTMLButtonElement>("[role^=menuitem]") ?? []),
    ];
    (items.find((i) => i.getAttribute("aria-checked") === "true") ?? items[0])?.focus();
    const outside = (e: PointerEvent) => {
      if (!wrap.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, [open]);

  function onKey(e: React.KeyboardEvent) {
    const items = [
      ...(list.current?.querySelectorAll<HTMLButtonElement>("[role^=menuitem]") ?? []),
    ];
    const i = items.indexOf(document.activeElement as HTMLButtonElement);
    const move = (n: number) => items[(n + items.length) % items.length]?.focus();
    if (e.key === "ArrowDown") move(i + 1);
    else if (e.key === "ArrowUp") move(i - 1);
    else if (e.key === "Home") move(0);
    else if (e.key === "End") move(items.length - 1);
    else if (e.key === "Escape") {
      setOpen(false);
      btn.current?.focus();
    } else if (e.key === "Tab") {
      setOpen(false);
      return;
    } else return;
    e.preventDefault();
  }

  return (
    <div className="menu-wrap" ref={wrap}>
      <button
        ref={btn}
        type="button"
        className={buttonClass}
        aria-label={buttonLabel}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown" && !open) {
            e.preventDefault();
            setOpen(true);
          }
        }}
      >
        {button}
      </button>
      {open && (
        <div className="menu" role="menu" id={id} aria-label={label} ref={list} onKeyDown={onKey}>
          {items.map((it) => (
            <button
              key={it.key}
              type="button"
              className="menu-item"
              role={radio ? "menuitemradio" : "menuitem"}
              aria-checked={radio ? Boolean(it.checked) : undefined}
              lang={it.lang}
              tabIndex={-1}
              onClick={() => {
                setOpen(false);
                btn.current?.focus();
                it.onSelect();
              }}
            >
              <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
                {it.icon && <Icon name={it.icon} />}
                {it.label}
              </span>
              {radio && it.checked ? (
                <Icon name="check" />
              ) : (
                it.code && <span className="code">{it.code}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** The language switcher: full name on wide screens, the code on phones. */
export function LangMenu({ lang, onChange }: { lang: Lang; onChange: (l: Lang) => void }) {
  const s = STRINGS[lang];
  const items: MenuItem[] = LANGS.map((l) => ({
    key: l,
    label: LANG_NAMES[l],
    code: l.toUpperCase(),
    lang: l,
    checked: l === lang,
    onSelect: () => {
      saveLang(l);
      onChange(l);
    },
  }));
  return (
    <Menu
      label={s.language}
      buttonClass="btn btn-ghost lang-btn"
      radio
      items={items}
      button={
        <>
          <Icon name="languages" className="only-wide" />
          <span className="sr-only">{s.language}: </span>
          <span className="only-wide">{LANG_NAMES[lang]}</span>
          <span className="only-narrow">{lang.toUpperCase()}</span>
          <Icon name="chevronDown" size={14} className="only-wide" />
        </>
      }
    />
  );
}

/** The permanent notice (ADR-010), outside the scroll area; the English line is always shown. */
export function Disclaimer({ lang }: { lang: Lang }) {
  const s = STRINGS[lang];
  const [details, setDetails] = useState(false);
  return (
    <footer className="disclaimer">
      <strong>{s.notice}</strong>
      {lang !== "en" && (
        <span className="en" lang="en">
          {STRINGS.en.notice}
        </span>
      )}
      <span className="only-wide">{s.noticeSources}</span>
      {details ? (
        <span className="only-narrow">{s.noticeSources}</span>
      ) : (
        <button
          type="button"
          className="details-btn only-narrow"
          aria-expanded={false}
          onClick={() => setDetails(true)}
        >
          {s.details}
        </button>
      )}
    </footer>
  );
}

export function Brand() {
  return (
    <span className="brand">
      <span className="mark" aria-hidden="true">
        §
      </span>
      <span className="brand-name">Swiss Admin Navigator</span>
    </span>
  );
}
