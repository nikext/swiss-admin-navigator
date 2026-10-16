"use client";

import { useEffect, useRef, useState } from "react";

import { citationLabel } from "@/lib/cite";
import { LANGS, type ArticleText, type Citation, type Lang } from "@/lib/contract";
import { LANG_NAMES, STRINGS } from "@/lib/i18n";

interface Props {
  citation: Citation;
  lang: Lang; // UI language
  onClose: () => void;
}

type Load = { lang: Lang; article: ArticleText | null }; // article null: failed

/**
 * The cited article's text, from the MCP server's get_article. Opens in the
 * quote's language; DE, FR and IT are equally authoritative, EN is Fedlex's
 * unofficial translation (where one exists).
 */
export default function ArticlePanel({ citation, lang, onClose }: Props) {
  const s = STRINGS[lang];
  const dialog = useRef<HTMLDialogElement>(null);
  const [textLang, setTextLang] = useState<Lang>(citation.quote_lang);
  const [load, setLoad] = useState<Load | null>(null);

  useEffect(() => {
    const d = dialog.current;
    if (d && !d.open) d.showModal();
  }, []);

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
        setLoad({ lang: textLang, article: (await r.json()) as ArticleText });
      })
      .catch(() => {
        if (!ctrl.signal.aborted) setLoad({ lang: textLang, article: null });
      });
    return () => ctrl.abort();
  }, [citation.sr, citation.article, textLang]);

  const current = load?.lang === textLang ? load : null; // null while loading
  const article = current?.article ?? null;
  const offered = LANGS.filter(
    (l) => l === "en" || !article || article.available_langs.includes(l),
  );

  return (
    <dialog
      ref={dialog}
      className="panel"
      aria-labelledby="panel-title"
      onClose={onClose}
      onClick={(e) => {
        if (e.target === dialog.current) dialog.current?.close(); // backdrop click
      }}
    >
      <div className="panel-inner">
        <header className="panel-head">
          <div>
            <h2 id="panel-title">{citationLabel(citation, s.paragraph, s.letter)}</h2>
            {article?.heading && <p className="muted">{article.heading}</p>}
          </div>
          <button
            type="button"
            className="icon"
            onClick={() => dialog.current?.close()}
            aria-label={s.close}
          >
            ×
          </button>
        </header>

        <div className="tabs" role="group" aria-label={s.language}>
          {offered.map((l) => (
            <button
              key={l}
              type="button"
              aria-pressed={textLang === l}
              onClick={() => setTextLang(l)}
              lang={l}
            >
              {LANG_NAMES[l]}
            </button>
          ))}
        </div>
        <p className="muted small">
          {textLang === "en" ? s.unofficialTranslation : s.authoritative}
          {article && ` · ${s.asOf} ${article.as_of}`}
        </p>

        {!current && (
          <p role="status" className="muted">
            {s.loading}
          </p>
        )}
        {current && !article && (
          <p role="alert" className="error">
            {s.articleError}
          </p>
        )}
        {article && (
          <article lang={article.lang}>
            {article.fallback && <p className="badge warn">{s.fallback}</p>}
            {article.status !== "in_force" && <p className="badge warn">{s.repealed}</p>}
            {article.heading_path.length > 0 && (
              <p className="crumbs muted small">{article.heading_path.join(" › ")}</p>
            )}
            {article.paragraphs.length > 0 ? (
              article.paragraphs.map((p, i) => (
                <p
                  key={p.eid || i}
                  className={p.num && p.num === citation.paragraph ? "para cited" : "para"}
                >
                  {p.num && <sup>{p.num}</sup>} {p.text}
                </p>
              ))
            ) : (
              <p className="para">{article.text}</p>
            )}
            <p>
              <a href={article.url} target="_blank" rel="noopener noreferrer">
                {s.onFedlex} ↗
              </a>
            </p>
            <p className="muted small">{article.act_title}</p>
          </article>
        )}
      </div>
    </dialog>
  );
}
