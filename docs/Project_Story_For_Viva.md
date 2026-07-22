# Auto-Echo: Architecture, Methodology & Design Story
*A guide for the viva / supervisor discussion of the delivered Auto-Echo system*

This document explains what Auto-Echo does, how it works, and the design journey —
including a deliberately **retained negative result** that motivated the final
design. It reflects the delivered system (the WSS pointer-chase pipeline), not the
early prototype.

---

## 1. The research problem
- **Inspiration:** the Klimis ECOOP 2025 paper *"Shouting at Memory"* (memory
  echolocation — inferring where data lives from access timing).
- **Goal:** automatically discover a machine's memory hierarchy **purely from user
  space** — no admin privileges, no architecture-specific instructions, no
  hardware documentation.
- **Challenge:** bridge precise low-level timing (nanosecond cache latency) with
  unsupervised machine learning that turns raw timings into labelled cache
  levels — and do it *portably* across architectures.

## 2. The delivered system — WSS pointer-chase, then "count, then localise"

### Stage 1 — The probe (C extension, `src/autoecho/wss/wss_probe.c`)
- **Working-set-size (WSS) sweep:** for each buffer size (a few cache lines up to
  256 MiB, ~10 points/octave), measure the average access latency.
- **Pointer chasing defeats the prefetcher:** the buffer is linked into a single
  random Hamiltonian cycle (seeded Fisher–Yates), so each load's address depends
  on the value returned by the previous load — the prefetcher cannot run ahead.
- **Batch-amortised timing beats the coarse timer:** ~1,000,000 dependent hops are
  timed together and divided by the count, recovering sub-nanosecond latency
  despite Apple's ~42 ns timer tick. No cache flush is needed — a working set
  larger than a level overflows it by construction.

### Stage 2 — Runtime timer calibration
Tick→nanosecond conversion is **calibrated at runtime** against the OS monotonic
clock, so it is correct on any machine and robust to turbo/frequency scaling — an
improvement over the reference paper's fixed `/proc/cpuinfo` frequency parsing.

### Stage 3 — Level discovery: count, then localise (`src/autoecho/analysis.py`)
- **Count** the levels with **K-Means + Silhouette** (cross-checked by GMM,
  DBSCAN, and the Elbow method). Because this counts distinct latency *levels*
  directly, it is robust across architectures.
- **Localise** each cache boundary with **change-point detection** constrained to
  exactly that many segments (dynamic programming; **no manual penalty**).
- Principle: *clustering counts the levels, change-point localises their
  capacities.* The level count is chosen from the data, never hard-coded — the
  same code recovers **4 levels on x86, 3 on the Apple M1** (L2 + SLC blur
  together), and **2 on a virtual machine**.

### Stage 4 — Self-validation & reporting (`validation.py`, `evaluation.py`, `report.py`)
- Detected capacities are checked against **live OS ground truth**
  (`sysctl` / `/sys` / `Win32_CacheMemory`).
- Every estimator is scored across independent sweeps for **accuracy and
  stability**, satisfying the requirement to identify the best method.
- Outputs: a Markdown validation report, a memory-mountain figure, and a
  model-selection figure.

---

## 3. The retained negative result (why the design looks like this)
The **first prototype** was a naive port of the reference paper's technique:
sequential single reads timed individually, with x86 `clflush` to force misses.
On Apple Silicon it **failed**, for three structural reasons:

1. **`clflush` is x86-only** — no user-space data-cache flush on ARM, so the
   "forced DRAM" path silently degenerated.
2. **Hardware prefetcher** — sequential reads are predicted and pre-loaded,
   hiding L2/L3/DRAM.
3. **Timer quantisation** — the ~42 ns tick dwarfs an L1 hit (~1.5 ns), so timing
   a single read measures the timer, not memory.

This prototype is **retained** as the documented `--method samples` baseline
(dissertation §5; `docs/03_Validation_Report.md`). It is **not** the current
method — it is the failure that motivated the WSS redesign, and each defect maps
to a fix above: prefetcher → pointer chasing; timer → batch amortisation;
flush → WSS overflow.

---

## 4. Results (Apple M1)
- **Three levels**, agreed by all five estimators: L1 (~158 KiB), a merged L2/SLC
  mid-band (~13.9 MiB), and DRAM.
- **100 % (2/2)** of OS-documented caches matched within a factor of two; mean
  absolute capacity error **~19.9 %**.
- Cross-platform behaviour is validated *in method* on synthetic Intel/AMD/VM
  curves; real x86 and Windows hardware runs are the immediate next step.

---

## 5. Likely viva questions
- **Why pointer chasing?** Data-dependent loads serialise memory access so the
  prefetcher cannot hide latency.
- **Why not a fixed threshold/penalty?** It is machine-specific and unstable;
  automatic model selection (Silhouette) adapts the level count to the hardware.
- **Why does the M1 show 3 levels, not 4?** The 12 MiB L2 and ~8 MB SLC are too
  close to separate reliably; the honest, reproducible answer is one merged
  mid-band, with the finer split reported as a candidate sub-structure.
- **What is novel versus lmbench?** The measurement lineage is classical; the
  contribution is the unsupervised, self-validating, architecture-agnostic
  inference layer built on top of it.
