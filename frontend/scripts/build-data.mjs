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
    // The TEN-sweep huge-page run, which is the one §5.3 reports. `intel_i5_13450hx`
    // is the earlier three-sweep run and disagrees with the dissertation on every
    // latency (1.59/4.75/22.94/123.25 there vs 1.57/4.71/20.81/122.36 in Table 11);
    // it is kept because it carries the lmbench cross-check of §5.3.1.
    id: "intel",
    dir: "intel_ci",
    name: "Intel Core i5-13450HX",
    arch: "x86-64",
    core: "Raptor Lake P-core",
    lineSize: "64 B",
    color: "#D55E00",
    status: "validated",
  },
  // To add a machine permanently: copy an entry above, point `dir` at its output
  // directory under data/, and fill every field from that machine's own
  // validation_report.md -- `core` and `lineSize` are reported in §5.1 of the
  // dissertation and must not be guessed. `lib/series.ts` assigns the on-screen
  // series colour, so `color` here is only a fallback.
];

/**
 * Ad-hoc machine from the environment, so someone who has just run the pipeline
 * can see *their own* sweep without editing this file:
 *
 *     AUTOECHO_RUN=my_run npm run dev
 *
 * `AUTOECHO_RUN` is a directory name under data/. The descriptive fields are
 * unknown for an arbitrary machine, so they are labelled "measured on this host"
 * rather than guessed; everything the dashboard actually plots (curve, levels,
 * estimators, ground truth) comes from that directory's own outputs.
 */
const EXTRA_RUN = process.env.AUTOECHO_RUN;
if (EXTRA_RUN) {
  if (!existsSync(join(DATA, EXTRA_RUN))) {
    console.error(
      `AUTOECHO_RUN="${EXTRA_RUN}" but data/${EXTRA_RUN} does not exist.\n` +
        `Run the pipeline first, e.g.:\n` +
        `  python -m autoecho --method wss --max-mb 256 --output-dir data/${EXTRA_RUN}`
    );
    process.exit(1);
  }
  MACHINES.push({
    id: "local",
    dir: EXTRA_RUN,
    name: `This machine (${EXTRA_RUN})`,
    arch: process.arch,
    core: "measured on this host",
    lineSize: "auto-detected",
    color: "#CC79A7",
    status: "measured",
  });
}

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
  // Absent on runs that predate the --huge-pages flag (e.g. the M1). Do NOT
  // assume 4 KiB: the OS base page size is platform-specific and Apple Silicon
  // uses 16 KiB, so guessing would display a false provenance. Report the gap.
  const allocation =
    md.match(/\*\*Chase-buffer allocation:\*\*\s*(.+)/)?.[1]?.trim() ??
    "OS default pages (not recorded)";

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
    // Overwritten by applyCapacitySpread() when a capacity_spread.json exists.
    // Always emitted so the field's absence never has to be distinguished from
    // a run that genuinely detected on the aggregate curve.
    capacityProvenance: null,
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

// ------------------------------------------------------- per-sweep capacities

/**
 * Replace the aggregate-curve capacities with the per-sweep median.
 *
 * WHY THIS EXISTS. `validation_report.md` detects levels once, on the aggregated
 * `wss_curve.csv`, which is the *minimum* over sweeps at each size. The minimum
 * is the right statistic for a latency -- interference can only add time -- but
 * the wrong one for a *boundary*: in the noisy L3->DRAM transition the lower
 * envelope drags the detected knee inward. On the ten-sweep Intel run that is the
 * difference between an L3 of 13.9 MiB (-30.4%) and one of 19.7 MiB (-1.5%);
 * 9 of the 10 individual sweeps give the latter. §5.3 therefore reports the median
 * of per-sweep detections, and so must this dashboard, or the two artefacts
 * contradict each other on the project's headline x86 result.
 *
 * The medians are computed by `scripts/capacity_ci.py --json`, not here: that
 * script owns the detection maths (exact 1-D k-means + penalty-free Dynp) and
 * re-implementing it in JavaScript would create a second, divergent estimator.
 * This function only substitutes values and re-derives the error columns.
 *
 * `metrics.meanAbsErrorPct` is deliberately NOT touched. The reports' figure is a
 * mean over every sweep and cache (M1 19.9%, Intel 7.3%), which is a different
 * statistic from the mean of the three median capacities (Intel 6.3%). Both are
 * legitimate; silently swapping one for the other would contradict §5.2, which
 * quotes the per-sweep form. The UI labels which one it is showing instead.
 */
function applyCapacitySpread(report, spread) {
  const bounded = report.levels.filter((l) => l.capacityKiB != null);
  if (!spread.levels?.length) return report;

  // capacity_ci.py drops unbounded levels before indexing, so its i-th entry is
  // the i-th level that has a capacity -- DRAM is absent from both lists.
  spread.levels.forEach((s, i) => {
    const level = bounded[i];
    if (!level) return;
    level.capacityKiB = s.medianBytes / 1024;
    level.capacityText = s.medianText;
  });

  const byName = new Map(spread.levels.map((s) => [s.name.toLowerCase(), s]));
  for (const g of report.groundTruth) {
    const s = byName.get(g.cache.toLowerCase());
    if (!s || g.truthKiB == null) continue;
    const detectedKiB = s.medianBytes / 1024;
    g.detectedKiB = detectedKiB;
    g.detectedText = s.medianText;
    g.errorPct = (100 * (detectedKiB - g.truthKiB)) / g.truthKiB;
    g.errorOctaves = Math.abs(Math.log2(detectedKiB / g.truthKiB));
    // The factor-of-two matching tolerance of §5.5, restated: |octaves| <= 1.
    g.match = g.errorOctaves <= 1;
  }

  report.capacityProvenance = {
    sweeps: spread.sweeps,
    rule: spread.rule,
    source: spread.source,
  };
  return report;
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

  let report = parseReport(readFileSync(reportPath, "utf8"));

  // Optional, and generated by `scripts/capacity_ci.py --json`. Absent for a
  // single-sweep run, where a per-sweep median would be the aggregate anyway.
  const spreadPath = join(base, "capacity_spread.json");
  if (existsSync(spreadPath)) {
    report = applyCapacitySpread(report, JSON.parse(readFileSync(spreadPath, "utf8")));
  }

  machines.push({ ...m, curve, runs, band, ...report });
  const caps = report.levels
    .filter((l) => l.capacityKiB != null)
    .map((l) => l.capacityText)
    .join(", ");
  console.log(
    `  ${m.id}: ${curve.length} pts, ${runs.length} runs, ` +
      `${report.levels.length} levels, ${report.allocation}\n` +
      `        capacities ${caps}` +
      (report.capacityProvenance
        ? ` (median of ${report.capacityProvenance.sweeps} per-sweep detections)`
        : ` (aggregate curve — no capacity_spread.json)`)
  );
}

if (!machines.length) throw new Error("no machines found under " + DATA);

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(
  OUT,
  JSON.stringify({ generatedAt: new Date().toISOString(), machines }, null, 0)
);
console.log(`wrote ${OUT} (${machines.length} machines)`);
