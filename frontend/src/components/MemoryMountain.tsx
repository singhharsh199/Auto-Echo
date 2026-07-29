import { useMemo } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Machine } from "../types";
import {
  bandColor,
  formatKiB,
  formatNs,
  logLatencyTicks,
  powerOfTwoTicks,
} from "../lib/format";

interface Props {
  machines: Machine[];
  /** The machine whose detected levels annotate the plot. */
  primary: Machine;
  showBand: boolean;
  showLevels: boolean;
  showBoundaries: boolean;
  visibleRuns: number[];
}

type Row = Record<string, number | [number, number] | undefined> & {
  wss: number;
};

const RUN_DASH = ["4 3", "1 3", "7 4"];

export function MemoryMountain({
  machines,
  primary,
  showBand,
  showLevels,
  showBoundaries,
  visibleRuns,
}: Props) {
  const { rows, xDomain, yDomain } = useMemo(() => {
    const byWss = new Map<number, Row>();
    const touch = (wss: number): Row => {
      let r = byWss.get(wss);
      if (!r) {
        r = { wss };
        byWss.set(wss, r);
      }
      return r;
    };

    for (const m of machines) {
      for (const p of m.curve) touch(p.wss_kib)[`min_${m.id}`] = p.latency_ns;
    }
    // The min-max envelope and per-run traces only ever annotate the primary
    // machine -- overlaying three runs for every machine at once is unreadable.
    if (showBand) {
      for (const b of primary.band) {
        touch(b.wss_kib)[`band_${primary.id}`] = [b.min, b.max];
      }
    }
    for (const runId of visibleRuns) {
      const run = primary.runs.find((r) => r.run === runId);
      if (!run) continue;
      for (const p of run.points) {
        touch(p.wss_kib)[`run_${primary.id}_${runId}`] = p.latency_ns;
      }
    }

    const rows = [...byWss.values()].sort((a, b) => a.wss - b.wss);

    const xs = rows.map((r) => r.wss);
    const ys: number[] = [];
    for (const m of machines) for (const p of m.curve) ys.push(p.latency_ns);
    if (showBand) for (const b of primary.band) ys.push(b.min, b.max);

    return {
      rows,
      xDomain: [Math.min(...xs), Math.max(...xs)] as [number, number],
      yDomain: [
        Math.max(0.5, Math.min(...ys) * 0.8),
        Math.max(...ys) * 1.25,
      ] as [number, number],
    };
  }, [machines, primary, showBand, visibleRuns]);

  const xTicks = powerOfTwoTicks(xDomain[0], xDomain[1]);
  const yTicks = logLatencyTicks(yDomain[0], yDomain[1]);

  return (
    <div className="h-[clamp(380px,52vh,620px)] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={{ top: 12, right: 18, bottom: 34, left: 8 }}>
          <CartesianGrid stroke="var(--grid)" strokeDasharray="2 4" />

          {/* Detected cache regions, shaded as in the report's memory mountain. */}
          {showLevels &&
            primary.levels.map((lv) =>
              lv.rangeLoKiB != null && lv.rangeHiKiB != null ? (
                <ReferenceArea
                  key={`band-${lv.label}`}
                  x1={Math.max(lv.rangeLoKiB, xDomain[0])}
                  x2={Math.min(lv.rangeHiKiB, xDomain[1])}
                  fill={bandColor(lv.label)}
                  stroke="none"
                  ifOverflow="hidden"
                />
              ) : null
            )}

          <XAxis
            dataKey="wss"
            type="number"
            scale="log"
            domain={xDomain}
            ticks={xTicks}
            allowDataOverflow
            tickFormatter={(v: number) => formatKiB(v, 0)}
            tick={{ fill: "var(--ink-3)", fontSize: 11 }}
            stroke="var(--hairline-strong)"
            label={{
              value: "Working-set size (log)",
              position: "insideBottom",
              offset: -18,
              fill: "var(--ink-2)",
              fontSize: 12,
            }}
          />
          <YAxis
            type="number"
            scale="log"
            domain={yDomain}
            ticks={yTicks}
            allowDataOverflow
            width={62}
            tickFormatter={(v: number) => `${v}`}
            tick={{ fill: "var(--ink-3)", fontSize: 11 }}
            stroke="var(--hairline-strong)"
            label={{
              value: "Latency (ns, log)",
              angle: -90,
              position: "insideLeft",
              offset: 14,
              fill: "var(--ink-2)",
              fontSize: 12,
              style: { textAnchor: "middle" },
            }}
          />

          <Tooltip
            content={<MountainTooltip machines={machines} primary={primary} />}
            cursor={{ stroke: "var(--ink-3)", strokeDasharray: "3 3" }}
          />

          {/* Min-max spread across the independent sweeps. */}
          {showBand && (
            <Area
              dataKey={`band_${primary.id}`}
              stroke="none"
              fill={primary.color}
              fillOpacity={0.16}
              isAnimationActive={false}
              connectNulls
              activeDot={false}
            />
          )}

          {/* Individual sweeps, dashed so they read as secondary to the minimum. */}
          {visibleRuns.map((runId, i) => (
            <Line
              key={`run-${runId}`}
              dataKey={`run_${primary.id}_${runId}`}
              stroke={primary.color}
              strokeOpacity={0.5}
              strokeWidth={1}
              strokeDasharray={RUN_DASH[i % RUN_DASH.length]}
              dot={false}
              isAnimationActive={false}
              connectNulls
            />
          ))}

          {/* The reported curve: minimum over repeats, per machine. */}
          {machines.map((m) => (
            <Line
              key={`min-${m.id}`}
              dataKey={`min_${m.id}`}
              stroke={m.color}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
              connectNulls
            />
          ))}

          {/* Inferred capacities: the plateau-to-rise transition per level. */}
          {showBoundaries &&
            primary.levels.map((lv) =>
              lv.capacityKiB != null ? (
                <ReferenceLine
                  key={`cap-${lv.label}`}
                  x={lv.capacityKiB}
                  stroke={primary.color}
                  strokeDasharray="5 4"
                  strokeOpacity={0.85}
                  ifOverflow="hidden"
                  label={{
                    value: formatKiB(lv.capacityKiB, 1),
                    position: "top",
                    fill: "var(--ink-2)",
                    fontSize: 10,
                  }}
                />
              ) : null
            )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

interface TooltipProps {
  active?: boolean;
  label?: number;
  machines: Machine[];
  primary: Machine;
  payload?: { dataKey?: string; value?: number | [number, number] }[];
}

function MountainTooltip({ active, label, machines, primary, payload }: TooltipProps) {
  if (!active || label == null || !payload?.length) return null;

  const get = (key: string) => payload.find((p) => p.dataKey === key)?.value;
  const band = get(`band_${primary.id}`) as [number, number] | undefined;
  const level = primary.levels.find(
    (lv) =>
      lv.rangeLoKiB != null &&
      lv.rangeHiKiB != null &&
      label >= lv.rangeLoKiB &&
      label <= lv.rangeHiKiB
  );

  return (
    <div
      className="mono rounded-md border px-3 py-2 text-xs shadow-lg"
      style={{
        background: "var(--surface)",
        borderColor: "var(--hairline-strong)",
        color: "var(--ink)",
      }}
    >
      <div className="mb-1.5 font-semibold">{formatKiB(label, 2)}</div>
      {machines.map((m) => {
        const v = get(`min_${m.id}`) as number | undefined;
        if (v == null) return null;
        return (
          <div key={m.id} className="flex items-center gap-2 py-0.5">
            <span
              aria-hidden="true"
              className="inline-block h-2 w-2 shrink-0 rounded-full"
              style={{ background: m.color }}
            />
            <span style={{ color: "var(--ink-2)" }}>{m.name}</span>
            <span className="ml-auto pl-3">{formatNs(v)}</span>
          </div>
        );
      })}
      {band && (
        <div className="mt-1 pt-1" style={{ borderTop: "1px solid var(--hairline)" }}>
          <span style={{ color: "var(--ink-3)" }}>spread </span>
          {formatNs(band[0])} – {formatNs(band[1])}
        </div>
      )}
      {level && (
        <div className="mt-1" style={{ color: "var(--ink-3)" }}>
          in {level.label}
        </div>
      )}
    </div>
  );
}
