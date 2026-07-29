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
import { formatKiB, formatNs, logLatencyTicks, powerOfTwoTicks } from "../lib/format";
import { bandTint, seriesColor } from "../lib/series";

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
  const primaryColor = seriesColor(primary);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={rows} margin={{ top: 16, right: 22, bottom: 38, left: 8 }}>
        {/*
          Per-series gradients for the envelope fill: a vertical fade so the
          spread band is densest at the curve and dissolves downward, rather
          than sitting as a flat translucent slab.
        */}
        <defs>
          {machines.map((m, i) => {
            const c = seriesColor(m, i);
            return (
              <linearGradient
                key={`grad-${m.id}`}
                id={`fill-${m.id}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor={c} stopOpacity={0.32} />
                <stop offset="100%" stopColor={c} stopOpacity={0.04} />
              </linearGradient>
            );
          })}
          {/* Soft glow applied to the reported curve, which is what makes the
              line read as emissive against the dark plot ground. */}
          <filter id="curve-glow" x="-20%" y="-40%" width="140%" height="180%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <CartesianGrid stroke="var(--grid)" strokeDasharray="2 5" />

        {/* Detected cache regions, shaded as in the report's memory mountain. */}
        {showLevels &&
          primary.levels.map((lv) =>
            lv.rangeLoKiB != null && lv.rangeHiKiB != null ? (
              <ReferenceArea
                key={`band-${lv.label}`}
                x1={Math.max(lv.rangeLoKiB, xDomain[0])}
                x2={Math.min(lv.rangeHiKiB, xDomain[1])}
                fill={bandTint(lv.label)}
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
          tick={{ fill: "var(--ink-3)", fontSize: 11, fontFamily: "var(--font-mono)" }}
          stroke="var(--axis)"
          tickLine={{ stroke: "var(--axis)" }}
          /* Presentation only: the tick *values* still come from
             powerOfTwoTicks(). This lets Recharts drop labels that would
             collide on a narrow viewport rather than overprinting them. */
          minTickGap={26}
          label={{
            value: "WORKING-SET SIZE (LOG)",
            position: "insideBottom",
            offset: -20,
            fill: "var(--ink-4)",
            fontSize: 10,
            letterSpacing: "0.12em",
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
          tick={{ fill: "var(--ink-3)", fontSize: 11, fontFamily: "var(--font-mono)" }}
          stroke="var(--axis)"
          tickLine={{ stroke: "var(--axis)" }}
          label={{
            value: "LATENCY (NS, LOG)",
            angle: -90,
            position: "insideLeft",
            offset: 14,
            fill: "var(--ink-4)",
            fontSize: 10,
            letterSpacing: "0.12em",
            style: { textAnchor: "middle" },
          }}
        />

        <Tooltip
          content={<MountainTooltip machines={machines} primary={primary} />}
          cursor={{ stroke: "var(--accent-2)", strokeWidth: 1, strokeDasharray: "3 4" }}
        />

        {/* Min-max spread across the independent sweeps. */}
        {showBand && (
          <Area
            dataKey={`band_${primary.id}`}
            stroke="none"
            fill={`url(#fill-${primary.id})`}
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
            stroke={primaryColor}
            strokeOpacity={0.45}
            strokeWidth={1}
            strokeDasharray={RUN_DASH[i % RUN_DASH.length]}
            dot={false}
            isAnimationActive={false}
            connectNulls
          />
        ))}

        {/* The reported curve: minimum over repeats, per machine. */}
        {machines.map((m, i) => (
          <Line
            key={`min-${m.id}`}
            dataKey={`min_${m.id}`}
            stroke={seriesColor(m, i)}
            strokeWidth={2.25}
            strokeLinecap="round"
            dot={false}
            isAnimationActive={false}
            connectNulls
            filter="url(#curve-glow)"
            activeDot={{
              r: 4,
              fill: seriesColor(m, i),
              stroke: "var(--bg)",
              strokeWidth: 2,
            }}
          />
        ))}

        {/* Inferred capacities: the plateau-to-rise transition per level. */}
        {showBoundaries &&
          primary.levels.map((lv) =>
            lv.capacityKiB != null ? (
              <ReferenceLine
                key={`cap-${lv.label}`}
                x={lv.capacityKiB}
                stroke={primaryColor}
                strokeDasharray="5 5"
                strokeOpacity={0.7}
                ifOverflow="hidden"
                label={{
                  value: formatKiB(lv.capacityKiB, 1),
                  position: "top",
                  fill: "var(--ink-2)",
                  fontSize: 10,
                  fontFamily: "var(--font-mono)",
                }}
              />
            ) : null
          )}
      </ComposedChart>
    </ResponsiveContainer>
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
    <div className="tip">
      <div className="tip__wss">{formatKiB(label, 2)}</div>
      {machines.map((m, i) => {
        const v = get(`min_${m.id}`) as number | undefined;
        if (v == null) return null;
        return (
          <div
            className="tip__row"
            key={m.id}
            style={{ "--dot": seriesColor(m, i) } as React.CSSProperties}
          >
            <span className="tip__dot" aria-hidden="true" />
            <span className="tip__name">{m.name}</span>
            <span className="tip__val">{formatNs(v)}</span>
          </div>
        );
      })}
      {band && (
        <div className="tip__meta">
          spread {formatNs(band[0])} – {formatNs(band[1])}
        </div>
      )}
      {level && <div className="tip__meta">in {level.label}</div>}
    </div>
  );
}
