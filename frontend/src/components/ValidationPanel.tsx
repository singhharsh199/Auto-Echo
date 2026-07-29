import type { Machine } from "../types";
import { formatSignedPct } from "../lib/format";

const pct = (v: number | null) => (v == null ? "—" : `${v}%`);

/** Headline validation metrics, then the per-cache ground-truth comparison. */
export function ValidationPanel({ machine }: { machine: Machine }) {
  const { metrics } = machine;
  const stats = [
    { label: "Recall", value: pct(metrics.recall), hint: "documented caches found" },
    { label: "Precision", value: pct(metrics.precision), hint: "detected knees that are real" },
    { label: "F1", value: metrics.f1?.toFixed(2) ?? "—", hint: "harmonic mean" },
    {
      label: "Mean abs. error",
      value: pct(metrics.meanAbsErrorPct),
      hint: `matched caches, ${metrics.sweeps ?? "?"} sweeps`,
    },
  ];

  return (
    <section
      className="rounded-lg border"
      style={{ background: "var(--surface)", borderColor: "var(--hairline)" }}
    >
      <header
        className="flex items-baseline justify-between gap-3 border-b px-4 py-3"
        style={{ borderColor: "var(--hairline)" }}
      >
        <h2 className="display text-base font-semibold">Validation vs OS ground truth</h2>
        <span className="eyebrow">Hungarian matching, factor-of-2 tolerance</span>
      </header>

      <div className="grid grid-cols-2 lg:grid-cols-4">
        {stats.map((s, i) => (
          <div
            key={s.label}
            className="border-b px-4 py-3 lg:border-b-0"
            style={{
              borderColor: "var(--hairline)",
              borderLeftWidth: i % 2 === 1 ? 1 : 0,
              borderLeftStyle: "solid",
            }}
          >
            <p className="eyebrow">{s.label}</p>
            <p className="mono mt-1 text-xl font-semibold">{s.value}</p>
            <p className="mt-0.5 text-[11px]" style={{ color: "var(--ink-3)" }}>
              {s.hint}
            </p>
          </div>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="mono w-full min-w-[34rem] text-xs">
          <thead>
            <tr
              className="border-y text-left"
              style={{ borderColor: "var(--hairline)", color: "var(--ink-3)" }}
            >
              <th className="px-4 py-2 font-medium">Cache</th>
              <th className="px-4 py-2 font-medium">Ground truth</th>
              <th className="px-4 py-2 font-medium">Detected</th>
              <th className="px-4 py-2 text-right font-medium">Octaves</th>
              <th className="px-4 py-2 text-right font-medium">Error</th>
              <th className="px-4 py-2 text-right font-medium">Match</th>
            </tr>
          </thead>
          <tbody>
            {machine.groundTruth.map((g) => (
              <tr
                key={g.cache}
                className="border-b last:border-b-0"
                style={{ borderColor: "var(--hairline)" }}
              >
                <td className="px-4 py-2 font-semibold">{g.cache}</td>
                <td className="px-4 py-2" style={{ color: "var(--ink-2)" }}>
                  {g.truthText}
                </td>
                <td className="px-4 py-2">{g.detectedText || "—"}</td>
                <td className="px-4 py-2 text-right" style={{ color: "var(--ink-2)" }}>
                  {g.errorOctaves?.toFixed(2) ?? "—"}
                </td>
                <td className="px-4 py-2 text-right">
                  {g.errorPct != null ? formatSignedPct(g.errorPct) : "—"}
                </td>
                <td
                  className="px-4 py-2 text-right font-semibold"
                  style={{ color: g.match ? "var(--ok)" : "var(--warn)" }}
                >
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
