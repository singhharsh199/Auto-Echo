import type { Machine } from "../types";
import { bandColor, formatKiB, formatNs, formatSignedPct } from "../lib/format";

/**
 * One card per discovered level. The ground-truth comparison is joined in by
 * cache name so DRAM (which has no documented capacity) simply shows none.
 */
export function LevelCards({ machine }: { machine: Machine }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {machine.levels.map((lv) => {
        const short = lv.label.replace(/\s*Cache$/i, "");
        const gt = machine.groundTruth.find(
          (g) => g.cache.toLowerCase() === short.toLowerCase()
        );
        return (
          <article
            key={lv.label}
            className="relative overflow-hidden rounded-lg border p-4"
            style={{ background: "var(--surface)", borderColor: "var(--hairline)" }}
          >
            <div
              aria-hidden="true"
              className="absolute inset-x-0 top-0 h-full"
              style={{ background: bandColor(lv.label) }}
            />
            <div className="relative">
              <div className="flex items-baseline justify-between gap-2">
                <h3 className="display text-base font-semibold">{short}</h3>
                <span className="eyebrow">{lv.points} pts</span>
              </div>

              <p className="mono mt-2 text-2xl font-semibold tracking-tight">
                {lv.capacityKiB != null ? formatKiB(lv.capacityKiB) : "—"}
              </p>
              <p className="eyebrow mt-0.5">
                {lv.capacityKiB != null ? "inferred capacity" : "no upper bound"}
              </p>

              <dl
                className="mono mt-3 space-y-1 border-t pt-3 text-xs"
                style={{ borderColor: "var(--hairline)" }}
              >
                <div className="flex justify-between gap-3">
                  <dt style={{ color: "var(--ink-3)" }}>median</dt>
                  <dd>{formatNs(lv.medianNs)}</dd>
                </div>
                {lv.p5Ns != null && lv.p95Ns != null && (
                  <div className="flex justify-between gap-3">
                    <dt style={{ color: "var(--ink-3)" }}>p5–p95</dt>
                    <dd>
                      {lv.p5Ns.toFixed(2)}–{lv.p95Ns.toFixed(2)}
                    </dd>
                  </div>
                )}
                {gt && (
                  <div className="flex justify-between gap-3">
                    <dt style={{ color: "var(--ink-3)" }}>vs {gt.truthText}</dt>
                    <dd
                      className="flex items-center gap-1.5"
                      style={{ color: gt.match ? "var(--ok)" : "var(--warn)" }}
                    >
                      <span aria-hidden="true">{gt.match ? "✓" : "!"}</span>
                      {gt.errorPct != null ? formatSignedPct(gt.errorPct) : "—"}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </article>
        );
      })}
    </div>
  );
}
