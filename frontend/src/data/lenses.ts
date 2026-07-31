/**
 * Content for the "Three lenses" comparative section.
 *
 * The same two machines are described three times over, by three sources that do
 * not agree: the vendor's own system report, the OS topology descriptor read by
 * `hwloc`/`lstopo`, and this project's measurement. The disagreement is the
 * point, so the copy here is deliberately specific -- exact capacities, exact
 * error percentages -- rather than paraphrased.
 *
 * PROVENANCE. Every figure traces to `docs/Draft_Dissertation.md`:
 *   Lens 1  -- Windows System Properties / macOS System Information (§5.1, Table 6)
 *   Lens 2  -- `lstopo` console output on each machine (§5.1, Tables 5 and 6)
 *   Lens 3  -- Table 7 (Apple M1) and Table 11 (Intel, 2 MiB huge pages)
 *
 * These are curated rather than read from `dataset.json` because two of the three
 * lenses are not measurements this pipeline produces -- the pipeline has no view
 * of what `lstopo` reported. Keeping them in one typed module makes the section
 * auditable against the dissertation in a single diff.
 */

export type LensId = "system" | "topology" | "autoecho";
export type MachineKey = "intel" | "m1";

/** Hue family for a stack block; maps to the level tokens in `index.css`. */
export type BlockTone = "l1" | "l2" | "l3" | "dram";

export interface StackBlock {
  label: string;
  capacity: string;
  /** Latency, scope, or the reason the block is a ghost. */
  note?: string;
  tone: BlockTone;
  /**
   * Capacity in KiB, used only to size the block: height is proportional to
   * log2(capacityKiB), matching the log axis of the main chart. Without the log
   * a 20 MiB L3 would be 400x the height of a 48 KiB L1 and the small levels
   * would vanish. `null` means unbounded (DRAM), which gets a fixed weight.
   */
  capacityKiB: number | null;
  /**
   * Hardware this lens cannot see, drawn as a dashed outline. Used for the M1's
   * System-Level Cache under the topology lens: it exists, and the descriptor
   * does not mention it.
   */
  ghost?: boolean;
}

export interface Fact {
  k: string;
  v: string;
  /** Draws the value in the semantic colour: `warn` for a gap, `ok` for a hit. */
  flag?: "ok" | "warn";
}

export interface LensView {
  verdict: string;
  tone: "ok" | "warn";
  facts: Fact[];
  stack: StackBlock[];
  /** Shown instead of the stack when the lens reports no hierarchy at all. */
  stackEmpty?: string;
}

export interface Lens {
  id: LensId;
  ordinal: string;
  name: string;
  tagline: string;
  /** What is being read, in the user's own terms. */
  source: string;
  /** The question this lens can and cannot answer. */
  question: string;
  views: Record<MachineKey, LensView>;
  /** The comparative point, shown once beneath both columns. */
  insight: string;
}

export interface MachineIdentity {
  key: MachineKey;
  name: string;
  sub: string;
  /** Design-system series token, matching the curve colour in the main chart. */
  color: string;
}

export const MACHINES: MachineIdentity[] = [
  {
    key: "intel",
    name: "Intel Core i5-13450HX",
    sub: "x86-64 · Raptor Lake · Windows 11",
    color: "var(--series-2)",
  },
  {
    key: "m1",
    name: "Apple M1",
    sub: "ARM64 · Firestorm · macOS",
    color: "var(--series-1)",
  },
];

export const LENSES: Lens[] = [
  {
    id: "system",
    ordinal: "01",
    name: "System properties",
    tagline: "The commercial view",
    source: "Windows System Properties · macOS System Information",
    question:
      "Answers “what did I buy?”. Says nothing whatsoever about how the memory hierarchy behaves.",
    views: {
      intel: {
        verdict: "No cache data at any level",
        tone: "warn",
        facts: [
          { k: "Processor", v: "13th Gen Core i5-13450HX @ 2.40 GHz" },
          { k: "Cores", v: "10 physical — 6 P + 4 E · 16 threads" },
          { k: "Installed memory", v: "24.0 GB (23.7 GB usable)" },
          { k: "Reserved", v: "~0.3 GB — firmware + Intel UHD Graphics", flag: "warn" },
          { k: "Cache hierarchy", v: "not reported", flag: "warn" },
        ],
        stack: [],
        stackEmpty:
          "System Properties lists the processor, its core count and its memory. It does not name a single cache.",
      },
      m1: {
        verdict: "No cache data at any level",
        tone: "warn",
        facts: [
          { k: "Chip", v: "Apple M1 · MacBook Air (MacBookAir10,1)" },
          { k: "Cores", v: "8 total — 4 performance + 4 efficiency" },
          { k: "Memory", v: "8 GB unified" },
          {
            k: "Reserved",
            v: "none fixed — CPU, GPU and Neural Engine share one pool on demand",
          },
          { k: "Cache hierarchy", v: "not reported", flag: "warn" },
        ],
        stack: [],
        stackEmpty:
          "System Information reports model, chip, cores, memory, firmware and serial number — and no cache figure of any kind.",
      },
    },
    insight:
      "Neither vendor publishes a cache size. Both machines look like a core count and a memory total, which is the specification a buyer needs and not the one a performance engineer needs. Anyone asking how large L1 is has already had to reach for a second tool.",
  },

  {
    id: "topology",
    ordinal: "02",
    name: "OS topology",
    tagline: "The software view",
    source: "lstopo · hwloc, reading the OS cache descriptors",
    question:
      "Answers “what has the operating system been told?”. Complete only where the vendor chose to export the truth.",
    views: {
      intel: {
        verdict: "Complete hierarchy — every documented cache present",
        tone: "ok",
        facts: [
          { k: "L1d", v: "48 KB per P-core", flag: "ok" },
          { k: "L2", v: "1280 KB per P-core", flag: "ok" },
          { k: "L3", v: "20 MB shared across the package", flag: "ok" },
          { k: "E-cores", v: "32 KB L1d · 2048 KB L2, shared by all four" },
          { k: "Memory", v: "6928 MB reported vs 24 GB installed", flag: "warn" },
        ],
        stack: [
          { label: "L1d", capacity: "48 KB", note: "per P-core", tone: "l1", capacityKiB: 48 },
          {
            label: "L2",
            capacity: "1280 KB",
            note: "per P-core, private",
            tone: "l2",
            capacityKiB: 1280,
          },
          {
            label: "L3",
            capacity: "20 MB",
            note: "shared, all cores",
            tone: "l3",
            capacityKiB: 20480,
          },
          { label: "DRAM", capacity: "—", note: "beyond L3", tone: "dram", capacityKiB: null },
        ],
      },
      m1: {
        verdict: "Incomplete — an entire ~8 MiB tier is missing",
        tone: "warn",
        facts: [
          { k: "L1d", v: "128 KB (performance) · 64 KB (efficiency)", flag: "ok" },
          { k: "L2", v: "12 MB (P-cluster) · 4 MB (E-cluster)", flag: "ok" },
          { k: "System-Level Cache", v: "absent from the descriptor", flag: "warn" },
          { k: "Memory", v: "8192 MB — exact match to installed", flag: "ok" },
          { k: "Clusters", v: "two L2 domains, cores 0–3 and 4–7" },
        ],
        stack: [
          {
            label: "L1d",
            capacity: "128 KB",
            note: "per Firestorm core",
            tone: "l1",
            capacityKiB: 128,
          },
          {
            label: "L2",
            capacity: "12 MB",
            note: "shared by the P-cluster",
            tone: "l2",
            capacityKiB: 12288,
          },
          {
            label: "System-Level Cache",
            capacity: "~8 MB",
            note: "exists in silicon · invisible to the OS",
            tone: "l3",
            capacityKiB: 8192,
            ghost: true,
          },
          { label: "DRAM", capacity: "—", note: "beyond the SLC", tone: "dram", capacityKiB: null },
        ],
      },
    },
    insight:
      "One tool, two outcomes. On the Intel part hwloc is complete and there is no undocumented tier to find. On the M1 a whole ~8 MiB cache is missing, because hwloc reads the same OS interfaces everything else does — it is an independent implementation, not an independent source. What the vendor never exported cannot be read by anyone.",
  },

  {
    id: "autoecho",
    ordinal: "03",
    name: "Auto-Echo",
    tagline: "The physical reality",
    source: "Pointer-chase latency sweep · no privileges, no descriptors",
    question:
      "Answers “how does this silicon actually behave?”. Sees only what the hardware does, including what nobody documented.",
    views: {
      intel: {
        verdict: "Full four-tier staircase recovered blind",
        tone: "ok",
        facts: [
          { k: "Levels found", v: "4 — L1 → L2 → L3 → DRAM", flag: "ok" },
          { k: "L1", v: "55.7 KiB vs 48 KiB documented · +16.0%", flag: "ok" },
          { k: "L2", v: "1.2 MiB vs 1.25 MiB documented · −1.5%", flag: "ok" },
          { k: "L3", v: "19.7 MiB vs 20 MiB documented · −1.5%", flag: "ok" },
          { k: "Requires", v: "2 MiB huge pages — on 4 KiB pages the L3 never appears" },
        ],
        stack: [
          { label: "L1", capacity: "55.7 KiB", note: "1.57 ns", tone: "l1", capacityKiB: 55.7 },
          { label: "L2", capacity: "1.2 MiB", note: "4.71 ns", tone: "l2", capacityKiB: 1229 },
          { label: "L3", capacity: "19.7 MiB", note: "20.81 ns", tone: "l3", capacityKiB: 20173 },
          { label: "DRAM", capacity: "—", note: "122.36 ns", tone: "dram", capacityKiB: null },
        ],
      },
      m1: {
        verdict: "Resolves capacity the OS never documented",
        tone: "ok",
        facts: [
          { k: "Levels found", v: "3 — L1 → L2+SLC → DRAM", flag: "ok" },
          { k: "L1", v: "157.5 KiB vs 128 KiB documented · +23.0%", flag: "ok" },
          { k: "L2 + SLC", v: "13.9 MiB against a 12 MiB documented L2 · +16.1%", flag: "ok" },
          { k: "What that shows", v: "the shelf runs past the L2 the OS reports", flag: "ok" },
          { k: "Cost", v: "L2 and SLC merge into one plateau — no boundary between them" },
        ],
        stack: [
          { label: "L1", capacity: "157.5 KiB", note: "1.53 ns", tone: "l1", capacityKiB: 157.5 },
          {
            label: "L2 + SLC",
            capacity: "13.9 MiB",
            note: "9.19 ns · one merged shelf",
            tone: "l2",
            capacityKiB: 14234,
          },
          { label: "DRAM", capacity: "—", note: "130.43 ns", tone: "dram", capacityKiB: null },
        ],
      },
    },
    insight:
      "The same unsupervised code path, given no descriptor and no privileges, reconstructs an x86 hierarchy to within 1.5% on two of three levels and detects an Apple cache that neither the vendor nor hwloc will admit exists. The three lenses are not three attempts at one measurement of which one is best — they are three different claims: what the vendor publishes, what the OS exports, and what the hardware does. Only the third is answerable by measurement.",
  },
];
