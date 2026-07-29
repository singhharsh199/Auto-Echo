/**
 * Build-time data pipeline for the Auto-Echo dashboard.
 *
 * Reads the pipeline's own outputs from ../data (the same files
 * `python -m autoecho --method wss --output-dir <dir>` writes) and emits a
 * single typed JSON bundle the React app imports. Run via `npm run prep`,
 * which `predev`/`prebuild` invoke automatically.
 *
 * To add a machine (e.g. the Apple M5) once its sweep exists, append one entry
 * to MACHINES below — nothing else in the app needs to change.
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = resolve(HERE, "../../data");
const OUT = resolve(HERE, "../src/data/dataset.json");

/** Okabe-Ito hues, matching `compare_curves.py` so the dashboard agrees with Fig. 10. */
const MACHINES = [
  {
    id: "m1",
    dir: ".",
    name: "Apple M1",
    arch: "ARM64",
    core: "Firestorm P-core",
    lineSize: "128 B",
    color: "#0072B2",
    status: "validated",
  },
  {
    id: "intel",
    dir: "intel_i5_13450hx",
    name: "Intel Core i5-13450HX",
    arch: "x86-64",
    core: "Raptor Lake P-core",
    lineSize: "64 B",
    color: "#D55E00",
    status: "validated",
  },
  // {
  //   id: "m5", dir: "m5", name: "Apple M5", arch: "ARM64",
  //   core: "TBD", lineSize: "TBD", color: "#CC79A7", status: "pending",
  // },
];

// ---------------------------------------------------------------- CSV parsing

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const header = lines[0].split(",").map((s) => s.trim());
  return lines.slice(1).map((line) => {
    const cells = line.split(",");
    const row = {};
    header.forEach((h, i) => {
      const v = Number(cells[i]);
      row[h] = Number.isNaN(v) ? cells[i] : v;
    });
    return row;
  });
}

/**
 * The min-max envelope across independent sweeps. The probe reports the
 * *minimum* over repeats, so the spread between sweeps is the honest
 * variability band -- the same band the dissertation's Fig. 5/7 shade.
 */
function envelope(allRows) {
  const bySize = new Map();
  for (const r of allRows) {
    const key = r.wss_kib;
    const e = bySize.get(key) ?? { wss_kib: key, min: Infinity, max: -Infinity };
    e.min = Math.min(e.min, r.latency_ns);
    e.max = Math.max(e.max, r.latency_ns);
    bySize.set(key, e);
  }
  return [...bySize.values()].sort((a, b) => a.wss_kib - b.wss_kib);
}

// ----------------------------------------------------- validation-report parsing

/** Split a markdown table row into trimmed cells, dropping the outer pipes. */
const cells = (line) =>
  line
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((s) => s.trim());

const isDivider = (line) => /^\|[\s:|-]+\|$/.test(line.trim());
const strip = (s) => s.replace(/\*\*/g, "").trim();

/** Collect the rows of the first markdown table appearing after `heading`. */
function tableAfter(md, heading) {
  const lines = md.split(/\r?\n/);
  const start = lines.findIndex((l) => l.includes(heading));
  if (start < 0) return [];
  const out = [];
  let seenHeader = false;
  for (let i = start + 1; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim().startsWith("#") && out.length) break;
    if (!line.trim().startsWith("|")) {
      if (out.length) break;
      continue;
    }
    if (isDivider(line)) continue;
    if (!seenHeader) {
      seenHeader = true;
      continue; // skip the header row itself
    }
    out.push(cells(line));
  }
  return out;
}

/** "55.7 KiB" | "1.2 MiB" -> KiB as a number. Returns null for "-"/"" cells. */
function toKiB(text) {
  const t = strip(text);
  if (!t || t === "-" || t === "—") return null;
  const m = t.match(/([\d.]+)\s*(B|KiB|MiB|GiB)/i);
  if (!m) return null;
  const n = parseFloat(m[1]);
  const unit = m[2].toLowerCase();
  if (unit === "b") return n / 1024;
  if (unit === "kib") return n;
  if (unit === "mib") return n * 1024;
  return n * 1024 * 1024;
}

const firstNumber = (text) => {
  const m = strip(text).match(/-?[\d.]+/);
  return m ? parseFloat(m[0]) : null;
};

function parseReport(md) {
  const machine = md.match(/\*\*Machine:\*\*\s*(.+)/)?.[1]?.trim() ?? null;
  // Absent on runs that predate the flag (e.g. the M1) -- treat as the default.
  const allocation =
    md.match(/\*\*Chase-buffer allocation:\*\*\s*(.+)/)?.[1]?.trim() ??
    "default 4 KiB pages";

  const levels = tableAfter(md, "## 1. Discovered Memory Hierarchy").map((c) => {
    const [lo, hi] = strip(c[4]).split(/[–-]/).map((s) => firstNumber(s));
    return {
      label: strip(c[0]),
      capacityKiB: toKiB(c[1]),
      capacityText: strip(c[1]),
      medianNs: firstNumber(c[2]),
      p5Ns: firstNumber(strip(c[3]).split(/[–]/)[0]),
      p95Ns: firstNumber(strip(c[3]).split(/[–]/)[1] ?? ""),
      rangeLoKiB: lo,
      rangeHiKiB: hi,
      points: firstNumber(c[5]),
    };
  });

  const estimators = tableAfter(md, "## 2. Level-Count Agreement").map((c) => ({
    name: strip(c[0]),
    detected: firstNumber(c[1]),
    score: strip(c[1]).match(/score\s*([\d.]+)/)?.[1] ?? null,
  }));

  const penaltyRows = tableAfter(md, "### 2.1 Change-Point Penalty Sensitivity");
  const penaltyHeader = (() => {
    const lines = md.split(/\r?\n/);
    const i = lines.findIndex((l) => l.includes("### 2.1 Change-Point"));
    const h = lines.slice(i).find((l) => l.trim().startsWith("| Penalty"));
    return h ? cells(h).slice(1).map(Number) : [];
  })();
  const penalty = penaltyRows.length
    ? penaltyHeader.map((p, i) => ({
        penalty: p,
        levels: Number(penaltyRows[0][i + 1]),
      }))
    : [];

  const comparison = tableAfter(md, "## 3. Level-Count Estimator Comparison").map(
    (c) => ({
      rank: firstNumber(c[0]),
      method: strip(c[1]),
      meanLevels: firstNumber(c[2]),
      std: firstNumber(c[3]),
      agreement: firstNumber(c[4]),
      modal: firstNumber(c[5]),
      expected: firstNumber(c[6]),
      countOk: c[8]?.includes("✅") ?? false,
    })
  );

  const groundTruth = tableAfter(md, "## 4. Validation Against Hardware").map((c) => ({
    cache: strip(c[0]),
    truthKiB: toKiB(c[1]),
    truthText: strip(c[1]),
    detectedKiB: toKiB(c[2]),
    detectedText: strip(c[2]),
    errorOctaves: firstNumber(c[3]),
    errorPct: firstNumber(c[4]),
    match: c[5]?.includes("✅") ?? false,
  }));

  return {
    machineLabel: machine,
    allocation,
    hugePages: /large page/i.test(allocation),
    levels,
    estimators,
    penalty,
    comparison,
    groundTruth,
    metrics: {
      recall: firstNumber(md.match(/\*\*Recall:\*\*\s*([\d.]+)%/)?.[1] ?? ""),
      precision: firstNumber(md.match(/\*\*Precision:\*\*\s*([\d.]+)%/)?.[1] ?? ""),
      f1: firstNumber(md.match(/\*\*F1:\*\*\s*([\d.]+)/)?.[1] ?? ""),
      meanAbsErrorPct: firstNumber(
        md.match(/Mean absolute capacity error[^*]*\*\*([\d.]+)%\*\*/)?.[1] ?? ""
      ),
      sweeps: firstNumber(md.match(/(\d+)\s+sweeps?\)/)?.[1] ?? ""),
    },
  };
}

// ------------------------------------------------------------------ build

const machines = [];

for (const m of MACHINES) {
  const base = join(DATA, m.dir);
  const curvePath = join(base, "wss_curve.csv");
  const allPath = join(base, "wss_curves_all.csv");
  const reportPath = join(base, "validation_report.md");

  if (!existsSync(curvePath) || !existsSync(reportPath)) {
    console.warn(`  skip ${m.id}: no wss_curve.csv / validation_report.md in ${base}`);
    continue;
  }

  const curve = parseCsv(readFileSync(curvePath, "utf8")).map((r) => ({
    wss_kib: r.wss_kib,
    latency_ns: r.latency_ns,
  }));

  let runs = [];
  let band = [];
  if (existsSync(allPath)) {
    const all = parseCsv(readFileSync(allPath, "utf8"));
    const ids = [...new Set(all.map((r) => r.run))].sort((a, b) => a - b);
    runs = ids.map((id) => ({
      run: id,
      points: all
        .filter((r) => r.run === id)
        .map((r) => ({ wss_kib: r.wss_kib, latency_ns: r.latency_ns })),
    }));
    band = envelope(all);
  }

  const report = parseReport(readFileSync(reportPath, "utf8"));

  machines.push({ ...m, curve, runs, band, ...report });
  console.log(
    `  ${m.id}: ${curve.length} pts, ${runs.length} runs, ` +
      `${report.levels.length} levels, ${report.allocation}`
  );
}

if (!machines.length) throw new Error("no machines found under " + DATA);

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(
  OUT,
  JSON.stringify({ generatedAt: new Date().toISOString(), machines }, null, 0)
);
console.log(`wrote ${OUT} (${machines.length} machines)`);
