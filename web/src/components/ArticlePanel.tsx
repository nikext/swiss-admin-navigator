"use client";

import { useEffect, useId, useRef, useState } from "react";

import { citationLabel } from "@/lib/cite";
import type { ArticleText, Citation, Lang } from "@/lib/contract";
import { LANG_NAMES, STRINGS } from "@/lib/i18n";
import { longDate } from "@/lib/present";

import Icon from "./Icon";

interface Props {
  citation: Citation;
  lang: Lang; // UI language
  /** Side panel next to the chat (≥ 1100 px); otherwise a modal overlay or bottom sheet. */
  docked: boolean;
  onClose: () => void;
}

type Load = { key: string; article: ArticleText | null }; // article null: failed

/**
 * The cited article's text, from the MCP server's get_article. Opens in the
 * quote's language; DE, FR and IT are equally authoritative, EN is Fedlex's
 * unofficial translation (where one exists).
 */
export default function ArticlePanel({ citation, lang, docked, onClose }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const d = dialog.current;
    if (!docked && d && !d.open) d.showModal();
  }, [docked]);

  if (docked) {
    return (
      <aside
        className="panel"
        aria-labelledby="panel-title"
        onKeyDown={(e) => {
          if (e.key === "Escape") onClose();
        }}
      >
        <PanelBody citation={citation} lang={lang} onClose={onClose} focusTitle />
      </aside>
    );
  }
  return (
    <dialog
      ref={dialog}
      className="panel-dialog"
      aria-labelledby="panel-title"
      onClose={onClose}
      onClick={(e) => {
        if (e.target === dialog.current) dialog.current?.close(); // backdrop click
      }}
    >
      <div className="panel">
        <div className="grab" aria-hidden="true" />
        <PanelBody
          citation={citation}
          lang={lang}
          onClose={() => dialog.current?.close()}
          focusTitle={false}
        />
      </div>
    </dialog>
  );
}

function PanelBody({
  citation,
  lang,
  onClose,
  focusTitle,
}: {
  citation: Citation;
  lang: Lang;
  onClose: () => void;
  focusTitle: boolean;
}) {
  const s = STRINGS[lang];
  const id = useId();
  const title = useRef<HTMLHeadingElement>(null);
  const tabs = useRef<HTMLDivElement>(null);
  const [textLang, setTextLang] = useState<Lang>(citation.quote_lang);
  const [attempt, setAttempt] = useState(0);
  const [load, setLoad] = useState<Load | null>(null);
  const [fullPath, setFullPath] = useState(false);
  const key = `${textLang}#${attempt}`;

  useEffect(() => {
    if (focusTitle) title.current?.focus();
  }, [focusTitle, citation]);

  useEffect(() => {
    const ctrl = new AbortController();
    const params = new URLSearchParams({
      sr: citation.sr,
      article: citation.article,
      lang: textLang,
    });
    fetch(`/api/article?${params}`, { signal: ctrl.signal })
      .then(async (r) => {
        if (!r.ok) throw new Error(String(r.status));
        setLoad({ key, article: (await r.json()) as ArticleText });
      })
      .catch(() => {
        if (!ctrl.signal.aborted) setLoad({ key, article: null });
      });
    return () => ctrl.abort();
  }, [citation.sr, citation.article, textLang, key]);

  const current = load?.key === key ? load : null; // null while loading
  const article = current?.article ?? null;
  // The authoritative languages first, then Fedlex's unofficial English.
  const offered = (["de", "fr", "it", "en"] as const).filter(
    (l) => l === "en" || !article || article.available_langs.includes(l),
  );
  const translation = textLang === "en" && article?.lang === "en";
  const url = article?.url ?? citation.url;
  const path = article?.heading_path ?? [];

  function onTabKey(e: React.KeyboardEvent) {
    const i = offered.indexOf(textLang);
    const next =
      e.key === "ArrowRight"
        ? offered[(i + 1) % offered.length]
        : e.key === "ArrowLeft"
          ? offered[(i - 1 + offered.length) % offered.length]
          : e.key === "Home"
            ? offered[0]
            : e.key === "End"
              ? offered[offered.length - 1]
              : null;
    if (!next) return;
    e.preventDefault();
    setTextLang(next);
    tabs.current?.querySelector<HTMLButtonElement>(`[data-lang="${next}"]`)?.focus();
  }

  return (
    <>
      <header className="panel-head">
        <div className="panel-titles">
          <span className="panel-kicker">
            {s.citedAs(citation.ref)} · SR {citation.sr}
          </span>
          <h2 id="panel-title" className="panel-title" ref={title} tabIndex={-1}>
            {citationLabel(citation, s.paragraph, s.letter)}
          </h2>
          {article?.heading ? (
            <p className="panel-sub" lang={article.lang}>
              {article.heading}
            </p>
          ) : (
            !current && (
              <div className="skeleton" style={{ width: "60%", height: 18, marginTop: 6 }} />
            )
          )}
        </div>
        <button
          type="button"
          className="btn btn-ghost btn-icon"
          aria-label={s.closeArticle}
          onClick={onClose}
        >
          <Icon name="x" size={20} />
        </button>
      </header>

      <div
        className="tabs"
        role="tablist"
        aria-label={s.lawTextLang}
        ref={tabs}
        onKeyDown={onTabKey}
      >
        {offered.map((l) => (
          <button
            key={l}
            id={`${id}-tab-${l}`}
            data-lang={l}
            type="button"
            className="tab"
            role="tab"
            aria-selected={textLang === l}
            aria-controls={`${id}-body`}
            tabIndex={textLang === l ? 0 : -1}
            onClick={() => setTextLang(l)}
            lang={l}
          >
            {LANG_NAMES[l]}
          </button>
        ))}
      </div>

      <div
        className="panel-scroll"
        id={`${id}-body`}
        role="tabpanel"
        aria-labelledby={`${id}-tab-${textLang}`}
        aria-busy={!current}
      >
        {article && (
          <p className="authority">
            {translation ? (
              <>
                <span className="unofficial">
                  <Icon name="languages" />
                  {s.unofficialTitle}
                </span>
                <span>{s.onlyAuthoritative}</span>
              </>
            ) : (
              <>
                <span className="ok">
                  <Icon name="shieldCheck" />
                  {s.authoritativeTitle}
                </span>
                <span>
                  {s.asOf} {longDate(article.as_of, lang)}
                </span>
              </>
            )}
          </p>
        )}

        {article && (article.fallback || article.status !== "in_force") && (
          <div className="panel-notes">
            {article.fallback && (
              <>
                <span className="badge badge-warn inline-badge">
                  <Icon name="info" />
                  {s.fallback}
                </span>
                <p className="t-small regular subtle">{s.englishNote}</p>
              </>
            )}
            {article.status !== "in_force" && (
              <span className="badge badge-warn inline-badge">
                <Icon name="clock" />
                {s.repealed}
              </span>
            )}
          </div>
        )}

        {path.length > 0 && (
          <nav className="crumbs" aria-label={s.positionInAct} lang={article?.lang}>
            <p className={`crumbs-text${fullPath ? "" : " clamped"}`}>
              {path.slice(0, -1).map((h) => `${h} › `)}
              <b>{path.at(-1)}</b>
            </p>
            {path.length > 2 && (
              <button
                type="button"
                className="btn btn-ghost btn-icon"
                aria-label={s.showPath}
                aria-expanded={fullPath}
                onClick={() => setFullPath((f) => !f)}
              >
                <Icon name="chevronDown" />
              </button>
            )}
          </nav>
        )}

        {!current && (
          <div className="article-body is-loading">
            <p
              className="t-small subtle"
              role="status"
              style={{ display: "flex", gap: 8, alignItems: "center" }}
            >
              <Icon name="loader" className="spin" />
              {s.loading}
            </p>
            <div className="skeleton" />
            <div className="skeleton" style={{ width: "92%" }} />
            <div className="skeleton" style={{ width: "70%" }} />
            <div className="skeleton" style={{ marginTop: 12 }} />
            <div className="skeleton" style={{ width: "85%" }} />
          </div>
        )}

        {current && !article && (
          <div className="article-body">
            <div className="callout callout-error" role="alert">
              <Icon name="triangleAlert" size={20} />
              <div>
                <p className="callout-body">{s.articleError}</p>
                <div className="callout-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setAttempt((a) => a + 1)}
                  >
                    <Icon name="rotateCcw" />
                    {s.tryAgain}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {article && (
          <div className="article-body" lang={article.lang}>
            {article.paragraphs.length > 0 ? (
              article.paragraphs.map((p, i) => {
                const cited = !!p.num && p.num === citation.paragraph;
                const cls = `para${cited ? " is-cited" : ""}${translation ? " is-translation" : ""}`;
                return (
                  <div key={p.eid || i} className={cls}>
                    <span className="num">{p.num}</span>
                    <div>
                      {cited && (
                        <span className="cited-tag" lang={lang}>
                          <Icon name="check" size={14} />
                          {s.citedInAnswer(citation.ref)}
                        </span>
                      )}
                      <p>{p.text}</p>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className={`para${translation ? " is-translation" : ""}`}>
                <span className="num" />
                <p>{article.text}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {(article || (current && url)) && (
        <footer className="panel-foot">
          {url && (
            <a className="btn btn-secondary" href={url} target="_blank" rel="noopener noreferrer">
              {s.onFedlex}
              <Icon name="externalLink" />
              <span className="sr-only">{s.newTab}</span>
            </a>
          )}
          {article && (
            <p className="act-title" lang={article.lang}>
              {article.act_title}
            </p>
          )}
        </footer>
      )}
    </>
  );
}
