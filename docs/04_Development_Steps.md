# Development Steps: Building Auto-Echo

This document outlines the step-by-step process undertaken to build the Auto-Echo framework from scratch.

## 1. Project Initialization & Architecture
- Initialized a modular Python package structure within the `src/` directory.
- Created the `setup.py` build script to define dependencies (`numpy`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`) and configure the compilation of the native C-extension.
- Created foundational directories (`tests/`, `data/`, `docs/`) to separate source code, datasets, and written documentation.

## 2. Implementing the Memory Latency Probe
- **Objective:** Replicate the echolocation probe described in the "Shouting at Memory" paper to gather nanosecond-accurate access latencies.
- **Action:** Wrote a Python C-Extension (`src/autoecho/probe/probe.c`). Instead of writing massive CSV files to disk (which causes severe I/O bottlenecks), the extension loads directly into Python memory.
- **Hardware Abstraction:** The C code dynamically checks the system architecture. If compiled on an Intel machine, it utilizes inline assembly for `rdtscp` and `clflush`. For your Apple Silicon (M-series) Mac, it gracefully falls back to using macOS's native `mach_absolute_time()` to capture high-resolution hardware ticks.
- **Python Wrapper:** Created `src/autoecho/probe/__init__.py` to call the C-extension and convert the raw hardware ticks into a clean Pandas DataFrame in nanoseconds.

## 3. Data Preprocessing Pipeline
- **Objective:** Clean the raw latency data, stripping away OS-level jitter and context-switching interference.
- **Action:** Implemented `src/autoecho/preprocessing.py`.
- **Filtering Algorithms:** Added functions to remove outliers using both the Interquartile Range (IQR) method and the Local Outlier Factor (LOF) as suggested by the literature.
- **Smoothing:** Applied a rolling window moving average to the time-series data to emphasize distinct latency plateaus.

## 4. Unsupervised ML Clustering Engine
- **Objective:** Group the cleaned latencies into physical memory tiers (L1, L2, DRAM, etc.) without hardcoding latency thresholds.
- **Action:** Implemented `src/autoecho/clustering.py`.
- **Algorithms Used:** Utilized Scikit-Learn to apply K-Means and Gaussian Mixture Models (GMM) to the 1D latency data.
- **Automatic Model Selection:** Implemented an iterative search that tests different values of $k$ (number of clusters) from 2 to 6. For each $k$, the framework calculates the **Silhouette Score** and automatically selects the $k$ that yields the best mathematical separation. 
- **Mapping:** Added logic to extract the minimum and maximum latencies for each discovered cluster and map them ascendingly to logical names (L1 Cache, L2 Cache, etc.).

## 5. Reporting and Visualization
- **Objective:** Present the findings clearly.
- **Action:** Wrote `src/autoecho/report.py`.
- **Visualization:** Used `matplotlib` and `seaborn` to generate a 1D scatterplot of the memory accesses, color-coded by their discovered cluster.
- **Reporting:** Implemented a function to output the validation results (latency ranges, mean latencies, and data point counts) into a markdown table.

## 6. End-to-End CLI Integration
- **Action:** Created the `src/autoecho/__main__.py` entry point.
- This ties the entire pipeline together so that the user can trigger data collection, preprocessing, clustering, and report generation sequentially using a single command: `python -m autoecho --samples 50000`.

## 7. Critical Evaluation of the Baseline (Negative Result)
- **Finding:** On Apple Silicon the sample-based probe produced only timer-quantised output. Root-cause analysis identified three barriers: (1) the ~41.7 ns timer tick dwarfs an L1 hit; (2) `clflush` does not exist on ARM and macOS exposes no user-space data-cache flush, so "forced DRAM" mode was a silent no-op; (3) a write-before-read pattern pulled every line into L1, guaranteeing an L1 hit by construction. A secondary flaw was smoothing i.i.d. samples, which erodes level structure.
- **Decision:** Retain the sample-based probe as a documented naive baseline (`--method samples`) and redesign the measurement around a working-set-size sweep.

## 8. WSS Pointer-Chase Probe (Redesign)
- **Action:** Implemented `src/autoecho/wss/wss_probe.c` — a data-dependent pointer chase over a random Hamiltonian cycle (seeded Fisher–Yates), with a warm-up pass and batch-amortised timing (≥2²⁰ hops/window), taking the minimum over repeats.
- **Portability:** `rdtscp` on x86, `mach_absolute_time` on Apple Silicon; cache-line size auto-detected (128 B on M1); P-core QoS hint. No flush instruction needed — a working set larger than a level overflows it by construction.

## 9. Change-Point Inference Engine
- **Action:** Implemented `src/autoecho/analysis.py`. Primary estimator: `ruptures` PELT on the log-latency curve with adjacent-plateau merging and robust p5/p95 boundaries. Cross-checks: K-Means, GMM (Silhouette-selected), and **DBSCAN** (the previously missing deliverable).

## 10. Self-Validation
- **Action:** Implemented `src/autoecho/validation.py`, reading live ground truth from `sysctl` (macOS) / `/sys` (Linux) and matching detected capacities within one octave. Result on M1: **100% accuracy**; additionally detected the OS-unreported ~8 MB System-Level Cache.

## 11. Comparative Evaluation & Rigor
- **Elbow Method:** Added automatic knee detection on K-Means inertia (`analysis.elbow_method`) alongside Silhouette, applied and compared (project-definition requirement); both select k = 3 (`model_selection.png`).
- **Comparative evaluation (`evaluation.py`):** Scores every estimator (change-point, K-Means/Silhouette, K-Means/Elbow, GMM, DBSCAN) across multiple independent sweeps by count correctness and stability (std), identifying the most accurate and consistent method (Milestone 5).
- **Stability / error bars:** Added `--runs N` (independent sweeps); the memory-mountain plot now shows a min–max variability band, and validation reports mean absolute % capacity error (19.6% on M1).
- **Page-aligned buffer:** Switched to `posix_memalign`/`_aligned_malloc` (as in the reference paper) to reduce TLB noise in deep-memory plateaus.
- **LOF mitigation test (`evaluation.evaluate_lof_mitigation`):** Empirically evaluated the paper's proposed LOF filter on the baseline; it removes ~0.04% of points and 100% of survivors stay on timer-tick multiples, confirming the failure is structural.
- **Penalty sensitivity:** Reports change-point level count across penalties (robust: 4 levels for penalties 3–6).

## 12. Documentation
- **Action:** Rewrote the `Literature Review` (added lmbench, Saavedra & Smith, Yotov, memory-mountain lineage; reframed novelty), `Methodology`, and `Draft Dissertation` to reflect the WSS methodology, empirical results, the Klimis §7 future-work motivation, and the comparative evaluation. Added cross-platform (`05`) and setup (`06`) guides, plus `compare_curves.py` and `crosscheck_lmbench.py` helpers.
