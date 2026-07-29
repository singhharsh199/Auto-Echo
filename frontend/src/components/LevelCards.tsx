import type { Machine } from "../types";
import { formatKiB, formatNs, formatSignedPct } from "../lib/format";
import { bandTint, levelEdge } from "../lib/series";

/**
 * One card per discovered level. The ground-truth comparison is joined in by
 * cache name so DRAM (which has no documented capacity) simply shows none.
 */
export function LevelCards({ machine }: { machine: Machine }) {
  return (
    <div className="levels">
      {machine.levels.map((lv, i) => {
        const short = lv.label.replace(/\s*Cache$/i, "");
        const gt = machine.groundTruth.find(
          (g) => g.cache.toLowerCase() === short.toLowerCase()
        );
        return (
          <article
            key={lv.label}
            className="level rise"
            style={
              {
                "--i": i + 1,
                "--tint": bandTint(lv.label),
                "--edge": levelEdge(lv.label),
              } as React.CSSProperties
            }
          >
            <div className="level__top">
              <h3 className="level__name">{short}</h3>
              <span className="eyebrow">{lv.points} pts</span>
            </div>

            <p className="level__cap">
              {lv.capacityKiB != null ? formatKiB(lv.capacityKiB) : "—"}
            </p>
            <p className="eyebrow">
              {lv.capacityKiB != null ? "inferred capacity" : "no upper bound"}
            </p>

            <dl className="level__dl">
              <div className="level__row">
                <dt>median</dt>
                <dd>{formatNs(lv.medianNs)}</dd>
              </div>
              {lv.p5Ns != null && lv.p95Ns != null && (
                <div className="level__row">
                  <dt>p5–p95</dt>
                  <dd>
                    {lv.p5Ns.toFixed(2)}–{lv.p95Ns.toFixed(2)}
                  </dd>
                </div>
              )}
              {gt && (
                <div className="level__row">
                  <dt>vs {gt.truthText}</dt>
                  <dd className={gt.match ? "t-ok" : "t-warn"}>
                    <span aria-hidden="true">{gt.match ? "✓" : "!"}</span>
                    {gt.errorPct != null ? formatSignedPct(gt.errorPct) : "—"}
                  </dd>
                </div>
              )}
            </dl>
          </article>
        );
      })}
    </div>
  );
}
