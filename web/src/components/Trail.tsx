"use client";

import type { Lang, Step } from "@/lib/contract";
import { STRINGS } from "@/lib/i18n";
import { clock, type TrailStep } from "@/lib/present";

import Icon, { type IconName } from "./Icon";

const STEP_ICONS: Record<Step, IconName> = {
  search: "search",
  resolve: "link",
  read: "bookOpen",
  browse: "listTree",
  check: "shieldAlert",
};

/**
 * The agent's tool use as a timeline. Live: the last step is current and the
 * verifier's pass is shown as the next step (the stream has no event for it).
 */
export function StepList({ steps, lang, live }: { steps: TrailStep[]; lang: Lang; live: boolean }) {
  const s = STRINGS[lang];
  return (
    <ol className="steps" aria-label={s.researchSteps} aria-live={live ? "polite" : undefined}>
      {steps.map((st, i) => {
        const current = live && i === steps.length - 1;
        const cls = [
          "step",
          current ? "is-current is-new" : "is-done",
          st.step === "check" && !current ? "is-check" : "",
        ].join(" ");
        return (
          <li key={i} className={cls}>
            <span className="step-ic">
              <Icon name={STEP_ICONS[st.step]} size={14} />
            </span>
            <div className="step-body">
              <span className="step-label">{s.steps[st.step]}</span>
              {st.detail && <span className="step-detail">{st.detail}</span>}
            </div>
            <span className="step-time">{clock(st.at)}</span>
          </li>
        );
      })}
      {live && steps.length > 0 && (
        <li className="step is-next" aria-hidden="true">
          <span className="step-ic">
            <Icon name="shieldCheck" size={14} />
          </span>
          <div className="step-body">
            <span className="step-label">{s.stepWriting}</span>
          </div>
          <span />
        </li>
      )}
    </ol>
  );
}

/** The waiting state: what the agent is doing right now, with the elapsed time. */
export function WorkCard({
  steps,
  lang,
  elapsedMs,
}: {
  steps: TrailStep[];
  lang: Lang;
  elapsedMs: number;
}) {
  const s = STRINGS[lang];
  return (
    <section className="work" aria-labelledby="work-title" aria-busy="true">
      <div className="work-head">
        <span className="work-mark" aria-hidden="true">
          §
        </span>
        <div>
          <h2 id="work-title" className="work-title">
            {s.workTitle}
          </h2>
          <p className="work-sub">{s.workSub}</p>
        </div>
        <span className="elapsed">
          <span aria-hidden="true">{clock(elapsedMs)}</span>
          <span className="sr-only">{s.elapsed(Math.floor(elapsedMs / 1000))}</span>
        </span>
      </div>
      <div className="bar" aria-hidden="true" />
      <StepList steps={steps} lang={lang} live />
      <p className="work-hint">
        <Icon name="info" />
        {s.slowHint}
      </p>
    </section>
  );
}
