import { useMemo, useState } from "react";
import raw from "./data/dataset.json";
import type { Dataset, Machine } from "./types";
import { MemoryMountain } from "./components/MemoryMountain";
import { LevelCards } from "./components/LevelCards";
import { ValidationPanel } from "./components/ValidationPanel";
import { EstimatorPanel } from "./components/EstimatorPanel";
import { formatKiB } from "./lib/format";
import { seriesColor } from "./lib/series";

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
  const primaryColor = seriesColor(primary, dataset.machines.indexOf(primary));

  return (
    <div className="app">
      <header className="masthead">
        <div className="shell masthead__inner">
          <div className="brand">
            <span className="brand__mark" aria-hidden="true">
              <WaveMark />
            </span>
            <div className="brand__text">
              <p className="eyebrow">Memory-hierarchy discovery</p>
              <h1 className="brand__title gradient-text">Auto-Echo</h1>
            </div>
          </div>

          <nav className="segmented" aria-label="Machine">
            {dataset.machines.map((m, i) => {
              const active = m.id === primary.id && !compare;
              return (
                <button
                  key={m.id}
                  type="button"
                  className="seg"
                  onClick={() => selectMachine(m.id)}
                  aria-pressed={active}
                  style={{ "--dot": seriesColor(m, i) } as React.CSSProperties}
                >
                  <span className="seg__dot" aria-hidden="true" />
                  {m.name}
                </button>
              );
            })}
            {dataset.machines.length > 1 && (
              <button
                type="button"
                className="seg"
                onClick={toggleCompare}
                aria-pressed={compare}
              >
                Overlay all
              </button>
            )}
          </nav>
        </div>
      </header>

      <main className="shell">
        <section className="panel hero rise" style={{ "--i": 0 } as React.CSSProperties}>
          <MachineIdentity machine={primary} color={primaryColor} />
          <MachineFacts machine={primary} maxWss={maxWss} />
        </section>

        <LevelCards machine={primary} />

        <section className="panel rise" style={{ "--i": 5 } as React.CSSProperties}>
          <header className="panel__head">
            <div>
              <h2 className="panel__title">
                Pointer-chase latency vs working-set size
              </h2>
              <p className="panel__sub">
                {compare
                  ? "Minimum curve for every measured machine, on one log–log axis."
                  : `Minimum over repeats; shaded regions are the detected levels for ${primary.name}.`}
              </p>
            </div>

            <div className="chips" role="group" aria-label="Chart layers">
              <Toggle label="Cache bands" checked={showLevels} onChange={setShowLevels} />
              <Toggle
                label="Boundaries"
                checked={showBoundaries}
                onChange={setShowBoundaries}
              />
              <Toggle label="Min–max spread" checked={showBand} onChange={setShowBand} />
            </div>
          </header>

          <div className="chart">
            <MemoryMountain
              machines={plotted}
              primary={primary}
              showBand={showBand}
              showLevels={showLevels && !compare}
              showBoundaries={showBoundaries}
              visibleRuns={visibleRuns}
            />
          </div>

          <footer className="panel__foot">
            <div className="chips">
              <span className="eyebrow">Overlay sweeps</span>
              {primary.runs.map((r) => {
                const on = visibleRuns.includes(r.run);
                return (
                  <button
                    key={r.run}
                    type="button"
                    className="chip"
                    onClick={() => toggleRun(r.run)}
                    aria-pressed={on}
                    style={{ "--chip": primaryColor } as React.CSSProperties}
                  >
                    run {r.run}
                  </button>
                );
              })}
              {visibleRuns.length > 0 && (
                <button
                  type="button"
                  className="link-btn"
                  onClick={() => setVisibleRuns([])}
                >
                  clear
                </button>
              )}
            </div>

            <Legend machines={plotted} />
          </footer>
        </section>

        <div className="duo">
          <ValidationPanel machine={primary} />
          <EstimatorPanel machine={primary} />
        </div>

        <p className="colophon fade" style={{ "--i": 8 } as React.CSSProperties}>
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

/** Brand mark: three echo arcs, referencing the pointer-chase latency curve. */
function WaveMark() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M3 17h3.2l2.1-8.4 2.4 12 2.5-15L17.6 17H21"
        stroke="white"
        strokeWidth="2.1"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.95"
      />
    </svg>
  );
}

function MachineIdentity({ machine, color }: { machine: Machine; color: string }) {
  return (
    <div className="hero__id">
      <span
        className="seg__dot"
        aria-hidden="true"
        style={{ "--dot": color, width: 11, height: 11 } as React.CSSProperties}
      />
      <span className="hero__name display">{machine.name}</span>
      <StatusPill status={machine.status} />
      {machine.hugePages && (
        <span
          className="pill pill--muted"
          title="The 20 MiB L3 only resolves under a 2 MiB large-page allocation"
        >
          2 MiB pages
        </span>
      )}
    </div>
  );
}

function MachineFacts({ machine, maxWss }: { machine: Machine; maxWss: number }) {
  const facts = [
    { k: "Architecture", v: `${machine.arch} · ${machine.core}` },
    { k: "Cache line", v: machine.lineSize },
    { k: "Levels resolved", v: `${machine.levels.length}` },
    { k: "Sweep range", v: `up to ${formatKiB(maxWss, 0)}` },
    { k: "Allocation", v: machine.allocation },
  ];

  return (
    <div className="facts">
      {facts.map((f) => (
        <div className="fact" key={f.k}>
          <p className="eyebrow">{f.k}</p>
          <p className="fact__v">{f.v}</p>
        </div>
      ))}
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const ok = status === "validated";
  return (
    <span className={ok ? "pill pill--ok" : "pill pill--warn"}>
      <span className="pill__led" aria-hidden="true" />
      {status}
    </span>
  );
}

function Legend({ machines }: { machines: Machine[] }) {
  if (machines.length < 2) return null;
  return (
    <div className="legend">
      {machines.map((m, i) => (
        <span className="legend__item" key={m.id}>
          <span
            className="legend__swatch"
            aria-hidden="true"
            style={{ "--dot": seriesColor(m, i) } as React.CSSProperties}
          />
          {m.name}
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
    <label className="switch">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span>{label}</span>
    </label>
  );
}
