"use client";

import { useId, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { CITE_PREFIX, citationLabel, linkCitations } from "@/lib/cite";
import type { Answer, Citation, Lang } from "@/lib/contract";
import { LANG_NAMES, STRINGS } from "@/lib/i18n";
import {
  CLAMP_CHARS,
  longDate,
  quoted,
  sourceStats,
  trailSummary,
  type SourceStats,
  type TrailStep,
} from "@/lib/present";

import Icon from "./Icon";
import { StepList } from "./Trail";

interface Props {
  answer: Answer;
  lang: Lang;
  steps: TrailStep[];
  /** Seconds from question to answer; null for answers restored from before it was kept. */
  took: number | null;
  /** The ref whose article is open in the panel, if it belongs to this answer. */
  activeRef: string | null;
  onCite: (c: Citation) => void;
  onAsk: (question: string) => void;
  disabled: boolean;
  rated?: "up" | "down";
  onRate: (rating: "up" | "down") => void;
}

export default function AnswerView(props: Props) {
  const { answer, lang, steps, took, activeRef, onCite, onAsk, disabled, rated, onRate } = props;
  const s = STRINGS[lang];
  const [trailOpen, setTrailOpen] = useState(false);
  const id = useId();
  const byRef = new Map(answer.citations.map((c) => [c.ref, c]));
  const markdown = linkCitations(answer.answer_markdown, byRef.keys());
  const stats = sourceStats(answer);
  const v = answer.verification?.status ?? "unavailable";
  const verifiedOk = v === "passed" || v === "passed_after_retry";
  const summary = trailSummary(steps);
  const label = (c: Citation) => citationLabel(c, s.paragraph, s.letter);

  return (
    <article className="answer" aria-label={s.answer}>
      <div className="answer-meta">
        {answer.out_of_scope && (
          <span className="badge badge-warn">
            <Icon name="octagonAlert" />
            {s.outOfScope}
          </span>
        )}
        {answer.citations.length > 0 && (
          <span className={`badge ${verifiedOk ? "badge-ok" : "badge-warn"}`}>
            <Icon name={verifiedOk ? "shieldCheck" : "triangleAlert"} />
            {s.verification[v]}
          </span>
        )}
        {!answer.out_of_scope && <Confidence level={answer.confidence} lang={lang} />}
        {steps.length > 0 && took !== null && (
          <button
            type="button"
            className="trail-toggle"
            aria-expanded={trailOpen}
            aria-controls={`${id}-trail`}
            onClick={() => setTrailOpen((o) => !o)}
          >
            <Icon name="chevronRight" />
            {s.trail(summary.articles, took, summary.corrections)}
          </button>
        )}
      </div>
      {trailOpen && (
        <div className="trail-done" id={`${id}-trail`}>
          <StepList steps={steps} lang={lang} live={false} />
        </div>
      )}

      <div className="prose" lang={answer.language}>
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
                    className="cite"
                    lang={lang}
                    aria-expanded={activeRef === c.ref}
                    aria-label={s.source(c.ref, label(c))}
                    onClick={() => onCite(c)}
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
        <div className="callout callout-ask" role="note">
          <Icon name="messageQuestion" size={20} />
          <div>
            <p className="callout-title">{s.clarify}</p>
            <p className="callout-body" lang={answer.language}>
              {answer.clarifying_question}
            </p>
            <p className="reply-hint t-small">{s.replyBelow}</p>
          </div>
        </div>
      )}

      {answer.cantonal_note && (
        <div className="callout" role="note">
          <Icon name="mapPin" size={20} />
          <div>
            <p className="callout-title">{s.cantonal}</p>
            <p className="callout-body" lang={answer.language}>
              {answer.cantonal_note}
            </p>
          </div>
        </div>
      )}

      {answer.citations.length > 0 && (
        <Sources
          headId={`${id}-src`}
          answer={answer}
          lang={lang}
          stats={stats}
          activeRef={activeRef}
          onCite={onCite}
          label={label}
        />
      )}

      {answer.follow_up_questions.length > 0 && (
        <div className="fu-section" role="group" aria-labelledby={`${id}-fu`}>
          <h2 id={`${id}-fu`} className="t-label muted">
            {s.followUps}
          </h2>
          <ul className="fu-list">
            {answer.follow_up_questions.slice(0, 3).map((q) => (
              <li key={q}>
                <button
                  type="button"
                  className="fu"
                  onClick={() => onAsk(q)}
                  disabled={disabled}
                  lang={answer.language}
                >
                  <Icon name="cornerDownRight" />
                  {q}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="answer-foot">
        <p className="notice" lang="en">
          {answer.notice}
        </p>
        <div className="feedback" role="group" aria-label={`${s.helpful} / ${s.notHelpful}`}>
          <button
            type="button"
            className="btn btn-ghost btn-icon"
            aria-label={s.helpful}
            title={s.helpful}
            aria-pressed={rated === "up"}
            disabled={rated === "down"}
            onClick={() => !rated && onRate("up")}
          >
            <Icon name="thumbsUp" />
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-icon"
            aria-label={s.notHelpful}
            title={s.notHelpful}
            aria-pressed={rated === "down"}
            disabled={rated === "up"}
            onClick={() => !rated && onRate("down")}
          >
            <Icon name="thumbsDown" />
          </button>
          {rated && (
            <span className="thanks t-small muted" role="status">
              {s.thanks}
            </span>
          )}
        </div>
      </div>
    </article>
  );
}

function Confidence({ level, lang }: { level: Answer["confidence"]; lang: Lang }) {
  const bars = level === "high" ? 3 : level === "medium" ? 2 : 1;
  return (
    <span className="badge badge-neutral">
      <span className="meter" aria-hidden="true">
        {[1, 2, 3].map((n) => (
          <span key={n} className={n > bars ? "off" : undefined} />
        ))}
      </span>
      {STRINGS[lang].confidence[level] ?? level}
    </span>
  );
}

function Sources({
  headId,
  answer,
  lang,
  stats,
  activeRef,
  onCite,
  label,
}: {
  headId: string;
  answer: Answer;
  lang: Lang;
  stats: SourceStats;
  activeRef: string | null;
  onCite: (c: Citation) => void;
  label: (c: Citation) => string;
}) {
  const s = STRINGS[lang];
  const asOf = [...new Set(answer.citations.map((c) => c.as_of).filter((d): d is string => !!d))];
  const seal = !stats.checked
    ? { warn: true, text: s.verification.unavailable }
    : stats.removed
      ? { warn: true, text: s.sealPartial(stats.verified, stats.total, stats.removed) }
      : { warn: false, text: s.seal(stats.verified, stats.total) };

  return (
    <div className="sources" role="group" aria-labelledby={headId}>
      <div className="sources-head">
        <div className="sources-title">
          <h2 id={headId} className="t-h2">
            {s.sources}
          </h2>
          {asOf.length > 0 && (
            <span className="t-small subtle">
              {s.asOf} {asOf.map((d) => longDate(d, lang)).join(", ")}
            </span>
          )}
        </div>
        <span className={`seal${seal.warn ? " warn" : ""}`}>
          <Icon name={seal.warn ? "triangleAlert" : "shieldCheck"} />
          {seal.text}
        </span>
      </div>
      <ol className="source-list">
        {answer.citations.map((c) => (
          <SourceItem
            key={c.ref}
            c={c}
            lang={lang}
            answerLang={answer.language}
            checked={stats.checked}
            active={activeRef === c.ref}
            label={label(c)}
            onOpen={() => onCite(c)}
          />
        ))}
      </ol>
    </div>
  );
}

function SourceItem({
  c,
  lang,
  answerLang,
  checked,
  active,
  label,
  onOpen,
}: {
  c: Citation;
  lang: Lang;
  answerLang: Lang;
  checked: boolean;
  active: boolean;
  label: string;
  onOpen: () => void;
}) {
  const s = STRINGS[lang];
  const long = (c.quote?.length ?? 0) > CLAMP_CHARS;
  const [expanded, setExpanded] = useState(false);
  const clamped = long && !expanded;
  const pin = [
    c.paragraph && `${s.paragraph} ${c.paragraph}`,
    c.letter && `${s.letter} ${c.letter}`,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <li className={`source${active ? " is-active" : ""}`}>
      <div className="source-head">
        <span className="ref" aria-hidden="true">
          {c.ref}
        </span>
        <span className="source-label">
          <span className="sr-only">[{c.ref}] </span>
          {c.abbr ?? `SR ${c.sr}`} {c.article} {pin && <span className="pin">{pin}</span>}
        </span>
        <button
          type="button"
          className="btn btn-ghost source-open"
          aria-label={`${s.openArticle}: ${label}`}
          aria-expanded={active}
          onClick={onOpen}
        >
          <Icon name="panelRight" />
          <span className="only-wide">{s.openArticle}</span>
        </button>
      </div>
      {c.quote ? (
        <>
          <div className="law">
            <div className="law-meta">
              <span>
                {LANG_NAMES[c.quote_lang]} · {s.authoritative}
              </span>
              {checked && (
                <span className="ok">
                  <Icon name="check" size={14} />
                  {s.verified}
                </span>
              )}
            </div>
            <p className={`law-text${clamped ? " clamp-3" : ""}`} lang={c.quote_lang}>
              {quoted(c.quote, c.quote_lang)}
            </p>
            {long && (
              <button
                type="button"
                className="more"
                aria-expanded={expanded}
                onClick={() => setExpanded((e) => !e)}
              >
                {expanded ? s.showLess : c.translation ? s.showMoreTranslation : s.showMore}
                <Icon name="chevronDown" size={14} />
              </button>
            )}
          </div>
          {c.translation && !clamped && (
            <div className="mt">
              <Icon name="languages" />
              <div>
                <p className="mt-label">{s.machineTranslation}</p>
                <p className="mt-text" lang={answerLang}>
                  {quoted(c.translation, answerLang)}
                </p>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="removed">
          <Icon name="triangleAlert" />
          <span>
            {s.quoteRemoved} {s.quoteRemovedHint}
          </span>
        </div>
      )}
    </li>
  );
}
