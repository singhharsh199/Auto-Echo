import type { Machine } from "../types";

/**
 * How many levels each independent estimator counted, and how stable that count
 * was across sweeps. A std of 0 means every sweep agreed; the pipeline uses
 * K-Means + Silhouette to set the count and change-point only to localise it.
 */
export function EstimatorPanel({ machine }: { machine: Machine }) {
  const expected = machine.comparison[0]?.expected ?? machine.levels.length;
  const maxLevels = Math.max(
    ...machine.penalty.map((p) => p.levels),
    ...machine.comparison.map((c) => c.modal),
    1
  );

  return (
    <section
      className="rounded-lg border"
      style={{ background: "var(--surface)", borderColor: "var(--hairline)" }}
    >
      <header
        className="flex items-baseline justify-between gap-3 border-b px-4 py-3"
        style={{ borderColor: "var(--hairline)" }}
      >
        <h2 className="display text-base font-semibold">Level-count estimators</h2>
        <span className="eyebrow">
          {machine.metrics.sweeps ?? "?"} sweeps · expected {expected}
        </span>
      </header>

      <div className="overflow-x-auto">
        <table className="mono w-full min-w-[32rem] text-xs">
          <thead>
            <tr
              className="border-b text-left"
              style={{ borderColor: "var(--hairline)", color: "var(--ink-3)" }}
            >
              <th className="px-4 py-2 font-medium">Method</th>
              <th className="px-4 py-2 text-right font-medium">Mean</th>
              <th className="px-4 py-2 text-right font-medium">Std</th>
              <th className="px-4 py-2 text-right font-medium">Modal</th>
              <th className="px-4 py-2 text-right font-medium">Count</th>
            </tr>
          </thead>
          <tbody>
            {machine.comparison.map((c) => (
              <tr
                key={c.method}
                className="border-b last:border-b-0"
                style={{ borderColor: "var(--hairline)" }}
              >
                <td className="px-4 py-2">
                  <span className="font-semibold">{c.method}</span>
                  {c.std === 0 && (
                    <span className="ml-2 text-[10px]" style={{ color: "var(--ink-3)" }}>
                      stable
                    </span>
                  )}
                </td>
                <td className="px-4 py-2 text-right">{c.meanLevels.toFixed(2)}</td>
                <td
                  className="px-4 py-2 text-right"
                  style={{ color: c.std === 0 ? "var(--ok)" : "var(--warn)" }}
                >
                  {c.std.toFixed(2)}
                </td>
                <td className="px-4 py-2 text-right">{c.modal}</td>
                <td
                  className="px-4 py-2 text-right font-semibold"
                  style={{ color: c.countOk ? "var(--ok)" : "var(--warn)" }}
                >
                  {c.countOk ? "✓ ok" : `✗ ${c.modal - c.expected > 0 ? "+" : ""}${c.modal - c.expected}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t px-4 py-3" style={{ borderColor: "var(--hairline)" }}>
        <p className="eyebrow mb-2">Change-point penalty sensitivity</p>
        <p className="mb-2 text-[11px]" style={{ color: "var(--ink-3)" }}>
          Level count as the manual PELT penalty varies — the knob the automatic,
          penalty-free method removes.
        </p>
        <div className="flex flex-wrap gap-1.5">
          {machine.penalty.map((p) => (
            <div
              key={p.penalty}
              className="mono flex flex-col items-center rounded border px-2 py-1"
              style={{
                borderColor: "var(--hairline)",
                background: "var(--surface-2)",
              }}
              title={`penalty ${p.penalty} → ${p.levels} levels`}
            >
              <span className="text-[10px]" style={{ color: "var(--ink-3)" }}>
                {p.penalty}
              </span>
              <span
                className="text-sm font-semibold"
                style={{
                  color: p.levels === expected ? "var(--ok)" : "var(--ink-2)",
                  opacity: 0.4 + 0.6 * (p.levels / maxLevels),
                }}
              >
                {p.levels}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
