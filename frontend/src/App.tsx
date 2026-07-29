import { useMemo, useState } from "react";
import raw from "./data/dataset.json";
import type { Dataset, Machine } from "./types";
import { MemoryMountain } from "./components/MemoryMountain";
import { LevelCards } from "./components/LevelCards";
import { ValidationPanel } from "./components/ValidationPanel";
import { EstimatorPanel } from "./components/EstimatorPanel";
import { formatKiB } from "./lib/format";

const dataset = raw as Dataset;

/** The view is deep-linkable, so a particular machine can be shared or bookmarked. */
function readUrlState() {
  const q = new URLSearchParams(window.location.search);
  const id = q.get("machine");
  return {
    machineId: dataset.machines.some((m) => m.id === id) ? id! : dataset.machines[0].id,
    compare: q.get("compare") === "1",
  };
}

function writeUrlState(machineId: string, compare: boolean) {
  const q = new URLSearchParams(window.location.search);
  q.set("machine", machineId);
  if (compare) q.set("compare", "1");
  else q.delete("compare");
  window.history.replaceState(null, "", `${window.location.pathname}?${q}`);
}

export default function App() {
  const initial = readUrlState();
  const [machineId, setMachineId] = useState(initial.machineId);
  const [compare, setCompare] = useState(initial.compare);
  const [showBand, setShowBand] = useState(true);
  const [showLevels, setShowLevels] = useState(true);
  const [showBoundaries, setShowBoundaries] = useState(true);
  const [visibleRuns, setVisibleRuns] = useState<number[]>([]);

  const primary = useMemo(
    () => dataset.machines.find((m) => m.id === machineId) ?? dataset.machines[0],
    [machineId]
  );
  const plotted = compare ? dataset.machines : [primary];

  const selectMachine = (id: string) => {
    setMachineId(id);
    setCompare(false);
    setVisibleRuns([]);
    writeUrlState(id, false);
  };

  const toggleCompare = () => {
    const next = !compare;
    setCompare(next);
    writeUrlState(machineId, next);
  };

  const toggleRun = (run: number) =>
    setVisibleRuns((prev) =>
      prev.includes(run) ? prev.filter((r) => r !== run) : [...prev, run]
    );

  const maxWss = primary.curve.at(-1)?.wss_kib ?? 0;

  return (
    <div className="min-h-full">
      <header
        className="border-b"
        style={{ background: "var(--surface)", borderColor: "var(--hairline)" }}
      >
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-end justify-between gap-4 px-5 py-4">
          <div>
            <p className="eyebrow">Auto-Echo · memory-hierarchy discovery</p>
            <h1 className="display mt-1 text-2xl font-semibold tracking-tight">
              Memory Mountain
            </h1>
          </div>

          <nav aria-label="Machine" className="flex flex-wrap items-center gap-2">
            {dataset.machines.map((m) => {
              const active = m.id === primary.id && !compare;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => selectMachine(m.id)}
                  aria-pressed={active}
                  className="flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors"
                  style={{
                    borderColor: active ? m.color : "var(--hairline)",
                    background: active ? "var(--surface-2)" : "transparent",
                    color: active ? "var(--ink)" : "var(--ink-2)",
                  }}
                >
                  <span
                    aria-hidden="true"
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ background: m.color }}
                  />
                  {m.name}
                </button>
              );
            })}
            {dataset.machines.length > 1 && (
              <button
                type="button"
                onClick={toggleCompare}
                aria-pressed={compare}
                className="rounded-md border px-3 py-1.5 text-sm transition-colors"
                style={{
                  borderColor: compare ? "var(--accent)" : "var(--hairline)",
                  background: compare ? "var(--surface-2)" : "transparent",
                  color: compare ? "var(--ink)" : "var(--ink-2)",
                }}
              >
                Overlay all
              </button>
            )}
          </nav>
        </div>
      </header>

      <main className="mx-auto flex max-w-[1400px] flex-col gap-5 px-5 py-6">
        <MachineSummary machine={primary} maxWss={maxWss} />

        <LevelCards machine={primary} />

        <section
          className="rounded-lg border"
          style={{ background: "var(--surface)", borderColor: "var(--hairline)" }}
        >
          <header
            className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3"
            style={{ borderColor: "var(--hairline)" }}
          >
            <div>
              <h2 className="display text-base font-semibold">
                Pointer-chase latency vs working-set size
              </h2>
              <p className="mt-0.5 text-[11px]" style={{ color: "var(--ink-3)" }}>
                {compare
                  ? "Minimum curve for every measured machine, on one log–log axis."
                  : `Minimum over repeats; shaded regions are the detected levels for ${primary.name}.`}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
              <Toggle label="Cache bands" checked={showLevels} onChange={setShowLevels} />
              <Toggle
                label="Boundaries"
                checked={showBoundaries}
                onChange={setShowBoundaries}
              />
              <Toggle label="Min–max spread" checked={showBand} onChange={setShowBand} />
            </div>
          </header>

          <div className="px-2 pt-3">
            <MemoryMountain
              machines={plotted}
              primary={primary}
              showBand={showBand}
              showLevels={showLevels && !compare}
              showBoundaries={showBoundaries}
              visibleRuns={visibleRuns}
            />
          </div>

          <footer
            className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-3"
            style={{ borderColor: "var(--hairline)" }}
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="eyebrow mr-1">Overlay sweeps</span>
              {primary.runs.map((r) => {
                const on = visibleRuns.includes(r.run);
                return (
                  <button
                    key={r.run}
                    type="button"
                    onClick={() => toggleRun(r.run)}
                    aria-pressed={on}
                    className="mono rounded border px-2 py-1 text-[11px] transition-colors"
                    style={{
                      borderColor: on ? primary.color : "var(--hairline)",
                      background: on ? "var(--surface-2)" : "transparent",
                      color: on ? "var(--ink)" : "var(--ink-3)",
                    }}
                  >
                    run {r.run}
                  </button>
                );
              })}
              {visibleRuns.length > 0 && (
                <button
                  type="button"
                  onClick={() => setVisibleRuns([])}
                  className="text-[11px] underline"
                  style={{ color: "var(--ink-3)" }}
                >
                  clear
                </button>
              )}
            </div>

            <Legend machines={plotted} />
          </footer>
        </section>

        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <ValidationPanel machine={primary} />
          <EstimatorPanel machine={primary} />
        </div>

        <p className="pb-4 text-[11px]" style={{ color: "var(--ink-3)" }}>
          Built from <span className="mono">wss_curve.csv</span>,{" "}
          <span className="mono">wss_curves_all.csv</span> and{" "}
          <span className="mono">validation_report.md</span> in{" "}
          <span className="mono">data/</span> · generated{" "}
          {new Date(dataset.generatedAt).toLocaleString()} · re-run{" "}
          <span className="mono">npm run prep</span> after a new sweep.
        </p>
      </main>
    </div>
  );
}

function MachineSummary({ machine, maxWss }: { machine: Machine; maxWss: number }) {
  const facts = [
    { k: "Architecture", v: `${machine.arch} · ${machine.core}` },
    { k: "Cache line", v: machine.lineSize },
    { k: "Levels resolved", v: `${machine.levels.length}` },
    { k: "Sweep range", v: `up to ${formatKiB(maxWss, 0)}` },
    { k: "Allocation", v: machine.allocation },
  ];

  return (
    <section
      className="flex flex-wrap items-center gap-x-6 gap-y-3 rounded-lg border px-4 py-3"
      style={{ background: "var(--surface)", borderColor: "var(--hairline)" }}
    >
      <div className="flex items-center gap-2.5">
        <span
          aria-hidden="true"
          className="inline-block h-3 w-3 rounded-full"
          style={{ background: machine.color }}
        />
        <span className="display text-base font-semibold">{machine.name}</span>
        <StatusPill status={machine.status} />
        {machine.hugePages && (
          <span
            className="mono rounded px-1.5 py-0.5 text-[10px]"
            style={{ background: "var(--surface-2)", color: "var(--ink-2)" }}
            title="The 20 MiB L3 only resolves under a 2 MiB large-page allocation"
          >
            2 MiB pages
          </span>
        )}
      </div>

      {facts.map((f) => (
        <div key={f.k}>
          <p className="eyebrow">{f.k}</p>
          <p className="mono mt-0.5 text-xs">{f.v}</p>
        </div>
      ))}
    </section>
  );
}

function StatusPill({ status }: { status: string }) {
  const ok = status === "validated";
  return (
    <span
      className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
      style={{
        color: ok ? "var(--ok)" : "var(--warn)",
        background: ok ? "rgba(0,158,115,0.12)" : "rgba(230,159,0,0.12)",
      }}
    >
      {ok ? "✓ " : "· "}
      {status}
    </span>
  );
}

function Legend({ machines }: { machines: Machine[] }) {
  if (machines.length < 2) return null;
  return (
    <div className="flex flex-wrap items-center gap-3 text-[11px]">
      {machines.map((m) => (
        <span key={m.id} className="flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className="inline-block h-0.5 w-4 rounded"
            style={{ background: m.color }}
          />
          <span style={{ color: "var(--ink-2)" }}>{m.name}</span>
        </span>
      ))}
    </div>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-1.5 select-none">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-3.5 w-3.5 cursor-pointer accent-[var(--accent)]"
      />
      <span style={{ color: checked ? "var(--ink-2)" : "var(--ink-3)" }}>{label}</span>
    </label>
  );
}
