/** Shapes emitted by `scripts/build-data.mjs` from the pipeline's own outputs. */

export interface CurvePoint {
  wss_kib: number;
  latency_ns: number;
}

export interface BandPoint {
  wss_kib: number;
  min: number;
  max: number;
}

export interface Run {
  run: number;
  points: CurvePoint[];
}

export interface Level {
  label: string;
  /** null for DRAM, which has no upper boundary to report. */
  capacityKiB: number | null;
  capacityText: string;
  medianNs: number;
  p5Ns: number | null;
  p95Ns: number | null;
  rangeLoKiB: number | null;
  rangeHiKiB: number | null;
  points: number;
}

export interface Estimator {
  name: string;
  detected: number;
  score: string | null;
}

export interface ComparisonRow {
  rank: number;
  method: string;
  meanLevels: number;
  std: number;
  agreement: number;
  modal: number;
  expected: number;
  countOk: boolean;
}

export interface GroundTruthRow {
  cache: string;
  truthKiB: number | null;
  truthText: string;
  detectedKiB: number | null;
  detectedText: string;
  errorOctaves: number | null;
  errorPct: number | null;
  match: boolean;
}

export interface Machine {
  id: string;
  name: string;
  arch: string;
  core: string;
  lineSize: string;
  color: string;
  status: string;
  machineLabel: string | null;
  /** e.g. "2 MiB large pages" -- decisive for whether the L3 is visible. */
  allocation: string;
  hugePages: boolean;
  curve: CurvePoint[];
  runs: Run[];
  band: BandPoint[];
  levels: Level[];
  /**
   * Present when capacities are the median of per-sweep detections rather than a
   * single detection on the aggregated (minimum-over-sweeps) curve. Absent for
   * runs with no `capacity_spread.json`. See `scripts/build-data.mjs`.
   */
  capacityProvenance: {
    sweeps: number;
    rule: string;
    source: string;
  } | null;
  estimators: Estimator[];
  penalty: { penalty: number; levels: number }[];
  comparison: ComparisonRow[];
  groundTruth: GroundTruthRow[];
  metrics: {
    recall: number | null;
    precision: number | null;
    f1: number | null;
    meanAbsErrorPct: number | null;
    sweeps: number | null;
  };
}

export interface Dataset {
  generatedAt: string;
  machines: Machine[];
}
