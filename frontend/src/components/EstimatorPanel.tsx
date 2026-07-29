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
    <section className="panel rise" style={{ "--i": 7 } as React.CSSProperties}>
      <header className="panel__head">
        <h2 className="panel__title">Level-count estimators</h2>
        <span className="eyebrow">
          {machine.metrics.sweeps ?? "?"} sweeps · expected {expected}
        </span>
      </header>

      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Method</th>
              <th className="t-right">Mean</th>
              <th className="t-right">Std</th>
              <th className="t-right">Modal</th>
              <th className="t-right">Count</th>
            </tr>
          </thead>
          <tbody>
            {machine.comparison.map((c) => (
              <tr key={c.method}>
                <td>
                  <span className="t-name">{c.method}</span>
                  {c.std === 0 && <span className="tag">stable</span>}
                </td>
                <td className="t-right">{c.meanLevels.toFixed(2)}</td>
                <td className={`t-right ${c.std === 0 ? "t-ok" : "t-warn"}`}>
                  {c.std.toFixed(2)}
                </td>
                <td className="t-right">{c.modal}</td>
                <td className={`t-right ${c.countOk ? "t-ok" : "t-warn"}`}>
                  {c.countOk
                    ? "✓ ok"
                    : `✗ ${c.modal - c.expected > 0 ? "+" : ""}${c.modal - c.expected}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel__body" style={{ borderTop: "1px solid var(--hairline)" }}>
        <p className="eyebrow">Change-point penalty sensitivity</p>
        <p className="panel__sub" style={{ marginBottom: "var(--s-3)" }}>
          Level count as the manual PELT penalty varies — the knob the automatic,
          penalty-free method removes.
        </p>
        <div className="ladder">
          {machine.penalty.map((p) => (
            <div
              key={p.penalty}
              className={`rung${p.levels === expected ? " rung--hit" : ""}`}
              title={`penalty ${p.penalty} → ${p.levels} levels`}
            >
              <span className="rung__k">{p.penalty}</span>
              <span
                className="rung__v"
                style={{
                  color: p.levels === expected ? "var(--ok)" : "var(--ink-2)",
                  opacity: 0.45 + 0.55 * (p.levels / maxLevels),
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
