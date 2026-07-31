import type { Machine } from "../types";
import { formatSignedPct } from "../lib/format";

const pct = (v: number | null) => (v == null ? "—" : `${v}%`);

/** Headline validation metrics, then the per-cache ground-truth comparison. */
export function ValidationPanel({ machine }: { machine: Machine }) {
  const { metrics } = machine;
  const stats = [
    { label: "Recall", value: pct(metrics.recall), hint: "documented caches found" },
    {
      label: "Precision",
      value: pct(metrics.precision),
      hint: "detected knees that are real",
    },
    { label: "F1", value: metrics.f1?.toFixed(2) ?? "—", hint: "harmonic mean" },
    {
      label: "Mean abs. error",
      value: pct(metrics.meanAbsErrorPct),
      // Averaged over every sweep and cache, NOT over the median capacities in
      // the table below -- the two differ (Intel: 7.3% vs 6.3%). Naming the
      // statistic keeps a reader from trying to derive one from the other.
      hint: `per-sweep mean, ${metrics.sweeps ?? "?"} sweeps`,
    },
  ];

  const prov = machine.capacityProvenance;

  return (
    <section className="panel rise" style={{ "--i": 6 } as React.CSSProperties}>
      <header className="panel__head">
        <h2 className="panel__title">Validation vs OS ground truth</h2>
        <span className="eyebrow">Hungarian matching · factor-of-2 tolerance</span>
      </header>

      {prov && (
        <p className="provenance">
          Detected capacities are the <strong>median of {prov.sweeps} per-sweep
          detections</strong>, not a single detection on the aggregated curve — the
          aggregate is the minimum over sweeps, which biases a boundary inward.
          Localised by {prov.rule}.
        </p>
      )}

      <div className="stats">
        {stats.map((s) => (
          <div className="stat" key={s.label}>
            <p className="eyebrow">{s.label}</p>
            <p className="stat__v">{s.value}</p>
            <p className="stat__hint">{s.hint}</p>
          </div>
        ))}
      </div>

      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Cache</th>
              <th>Ground truth</th>
              <th>Detected</th>
              <th className="t-right">Octaves</th>
              <th className="t-right">Error</th>
              <th className="t-right">Match</th>
            </tr>
          </thead>
          <tbody>
            {machine.groundTruth.map((g) => (
              <tr key={g.cache}>
                <td className="t-name">{g.cache}</td>
                <td className="t-dim">{g.truthText}</td>
                <td>{g.detectedText || "—"}</td>
                <td className="t-right t-dim">{g.errorOctaves?.toFixed(2) ?? "—"}</td>
                <td className="t-right">
                  {g.errorPct != null ? formatSignedPct(g.errorPct) : "—"}
                </td>
                <td className={`t-right ${g.match ? "t-ok" : "t-warn"}`}>
                  {g.match ? "✓ yes" : "✗ no"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
