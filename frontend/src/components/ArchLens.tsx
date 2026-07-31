import { useRef, useState } from "react";
import { LENSES, MACHINES, type LensId } from "../data/lenses";
import { LensCard } from "./LensCard";

/**
 * "Three lenses on the same silicon" -- the comparative centrepiece.
 *
 * Two machines are described three times over by three sources that disagree:
 * the vendor's system report, the OS topology descriptor, and this project's
 * measurement. Presenting them as tabs rather than as one long table is what
 * makes the disagreement visible: the machine identity stays fixed in place
 * while the description under it changes, so the reader sees an ~8 MiB cache
 * appear between lens 02 and lens 03 rather than having to diff two tables.
 *
 * The tablist follows the WAI-ARIA authoring practice for tabs: roving
 * tabindex, arrow keys to move between tabs, Home/End to jump to the ends.
 */
export function ArchLens() {
  const [active, setActive] = useState<LensId>("system");
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  const index = LENSES.findIndex((l) => l.id === active);
  const lens = LENSES[index];

  const focusTab = (i: number) => {
    const next = (i + LENSES.length) % LENSES.length;
    setActive(LENSES[next].id);
    tabRefs.current[next]?.focus();
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    const moves: Record<string, number> = {
      ArrowRight: index + 1,
      ArrowDown: index + 1,
      ArrowLeft: index - 1,
      ArrowUp: index - 1,
      Home: 0,
      End: LENSES.length - 1,
    };
    const target = moves[e.key];
    if (target === undefined) return;
    e.preventDefault();
    focusTab(target);
  };

  return (
    <section className="panel archLens rise" style={{ "--i": 8 } as React.CSSProperties}>
      <header className="panel__head">
        <div>
          <h2 className="panel__title">Three lenses on the same silicon</h2>
          <p className="panel__sub">
            Two machines, described by three sources that do not agree. Step through the
            lenses to watch a cache appear.
          </p>
        </div>
      </header>

      <div className="lensTabs" role="tablist" aria-label="Comparison lens" onKeyDown={onKeyDown}>
        {LENSES.map((l, i) => {
          const on = l.id === active;
          return (
            <button
              key={l.id}
              ref={(el) => {
                tabRefs.current[i] = el;
              }}
              type="button"
              role="tab"
              id={`lenstab-${l.id}`}
              aria-selected={on}
              aria-controls={`lenspanel-${l.id}`}
              tabIndex={on ? 0 : -1}
              className="lensTab"
              onClick={() => setActive(l.id)}
            >
              <span className="lensTab__ord">{l.ordinal}</span>
              <span className="lensTab__body">
                <span className="lensTab__name">{l.name}</span>
                <span className="lensTab__tag">{l.tagline}</span>
              </span>
            </button>
          );
        })}
      </div>

      <div
        role="tabpanel"
        id={`lenspanel-${lens.id}`}
        aria-labelledby={`lenstab-${lens.id}`}
        className="lensPanel"
        key={lens.id}
      >
        <div className="lensMeta">
          <p className="lensMeta__source">
            <span className="eyebrow">Reading</span>
            <span className="mono">{lens.source}</span>
          </p>
          <p className="lensMeta__q">{lens.question}</p>
        </div>

        <div className="lensGrid">
          {MACHINES.map((m) => (
            <LensCard
              key={m.key}
              machine={m}
              view={lens.views[m.key]}
              animationKey={`${lens.id}-${m.key}`}
            />
          ))}
        </div>

        <aside className="insight">
          <span className="insight__mark" aria-hidden="true">
            <SparkMark />
          </span>
          <p className="insight__text">{lens.insight}</p>
        </aside>
      </div>
    </section>
  );
}

/** A staircase, echoing the latency curve the section is ultimately about. */
function SparkMark() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M3 19h4v-5h4V9h4V4h6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
