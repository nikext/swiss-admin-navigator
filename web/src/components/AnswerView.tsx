"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { CITE_PREFIX, citationLabel, linkCitations } from "@/lib/cite";
import type { Answer, Citation, Lang } from "@/lib/contract";
import { STRINGS } from "@/lib/i18n";

interface Props {
  answer: Answer;
  lang: Lang;
  onCite: (c: Citation) => void;
  onAsk: (question: string) => void;
  disabled: boolean;
}

export default function AnswerView({ answer, lang, onCite, onAsk, disabled }: Props) {
  const s = STRINGS[lang];
  const byRef = new Map(answer.citations.map((c) => [c.ref, c]));
  const markdown = linkCitations(answer.answer_markdown, byRef.keys());
  const asOf = [...new Set(answer.citations.map((c) => c.as_of).filter(Boolean))];
  const v = answer.verification?.status;

  return (
    <div className="answer" lang={answer.language}>
      {answer.out_of_scope && <p className="badge warn">{s.outOfScope}</p>}
      <div className="markdown">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a({ href, children }) {
              if (href?.startsWith(CITE_PREFIX)) {
                const c = byRef.get(href.slice(CITE_PREFIX.length));
                if (!c) return <>{children}</>;
                return (
                  <button
                    type="button"
                    className="chip"
                    onClick={() => onCite(c)}
                    title={citationLabel(c, s.paragraph, s.letter)}
                    aria-label={`${citationLabel(c, s.paragraph, s.letter)}: ${s.openArticle}`}
                  >
                    {children}
                  </button>
                );
              }
              return (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              );
            },
          }}
        >
          {markdown}
        </ReactMarkdown>
      </div>

      {answer.clarifying_question && (
        <div className="callout ask">
          <p className="callout-title">{s.clarify}</p>
          <p>{answer.clarifying_question}</p>
        </div>
      )}

      {answer.cantonal_note && (
        <div className="callout">
          <p className="callout-title">{s.cantonal}</p>
          <p>{answer.cantonal_note}</p>
        </div>
      )}

      {answer.citations.length > 0 && (
        <section className="sources" aria-label={s.sources}>
          <h2 className="sources-title">
            {s.sources}
            {asOf.length > 0 && (
              <span className="muted">
                {" "}
                · {s.asOf} {asOf.join(", ")}
              </span>
            )}
          </h2>
          <ol>
            {answer.citations.map((c) => (
              <li key={c.ref} id={`src-${c.ref}`}>
                <button type="button" className="source" onClick={() => onCite(c)}>
                  <span className="source-ref">[{c.ref}]</span>
                  <span className="source-label">{citationLabel(c, s.paragraph, s.letter)}</span>
                  {c.quote ? (
                    <q lang={c.quote_lang}>{c.quote}</q>
                  ) : (
                    <span className="muted">{s.quoteRemoved}</span>
                  )}
                  {c.translation && c.quote && (
                    <span className="translation" lang={answer.language}>
                      {s.machineTranslation}: {c.translation}
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ol>
        </section>
      )}

      <p className="meta">
        <span className={`badge ${v === "passed" || v === "passed_after_retry" ? "ok" : "warn"}`}>
          {v ? s.verification[v] : s.verification.unavailable}
        </span>
        <span className="badge">{s.confidence[answer.confidence] ?? answer.confidence}</span>
      </p>

      {answer.follow_up_questions.length > 0 && (
        <div className="followups">
          <p className="callout-title">{s.followUps}</p>
          <ul>
            {answer.follow_up_questions.slice(0, 3).map((q) => (
              <li key={q}>
                <button type="button" className="link" onClick={() => onAsk(q)} disabled={disabled}>
                  {q}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="muted small" lang="en">
        {answer.notice}
      </p>
    </div>
  );
}
