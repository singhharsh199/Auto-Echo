# Auto-Echo Methodology

## 1. System Architecture
Auto-Echo is a modular Python pipeline that couples a low-level C measurement
probe with a high-level unsupervised-inference stage. It has four stages:

1. **Data collection** — a working-set-size (WSS) pointer-chase sweep (C extension)
2. **Level discovery** — change-point detection on the latency curve
3. **Cross-validation of level count** — K-Means / GMM / DBSCAN clustering
4. **Ground-truth validation and reporting**

An earlier sample-based probe (Section 6) is retained as a *documented naive
baseline* rather than the primary method, because it was shown to be
fundamentally unable to measure the hierarchy (see Draft Dissertation, Section 5).

## 2. Data Collection: The WSS Pointer-Chase Probe (`src/autoecho/wss/`)
Nanosecond memory timing requires a native probe; Auto-Echo implements it as a
Python C-extension (`wss_probe.c`). For each working-set size `S` in a
log-spaced sweep (four cache lines up to 256 MiB, ~10 points per octave):

1. A **page-aligned** buffer (`posix_memalign`/`_aligned_malloc`, as in the
   reference paper) of size `S` is divided into slots one **cache line apart**
   (the line size is auto-detected: 128 B on Apple Silicon, typically 64 B on
   x86). Page alignment avoids spurious TLB effects in the deep-memory plateaus.
2. The slots are linked into a **single random Hamiltonian cycle** using a
   Fisher–Yates shuffle driven by a **seeded xorshift64 RNG** (reproducible).
   Building this cycle writes every slot, which also pre-faults every page.
3. The probe performs a data-dependent **pointer chase**: each load returns the
   address of the next load. Because addresses are unpredictable, the hardware
   prefetcher cannot run ahead, and accesses are fully serialised — **no
   cache-flush instruction is needed**, which is essential on ARM/macOS where
   none is available in user space.
4. A warm-up traversal brings the working set to steady state, then `N ≥ 2²⁰`
   dependent hops are timed in a single window and divided by `N`. This **batch
   amortisation** yields sub-nanosecond effective resolution despite the coarse
   (~41.7 ns) Apple Silicon timer tick.
5. Each size is measured `R` times and the **minimum** is kept: for a
   micro-benchmark, interference can only add time, so the fastest run is the
   best estimate of true latency (standard lmbench practice).

The probe returns ticks-per-access; Python converts to nanoseconds using the
platform timer resolution (`mach_timebase_info` on macOS, TSC frequency on
Linux). On Apple Silicon a QoS hint biases the thread onto a performance core so
the measured L1/L2 capacities correspond to a documented core cluster.

## 3. Level Discovery: Change-Point Detection (`src/autoecho/analysis.py`)
A cache of capacity `C` keeps latency flat while the working set fits
(`S ≤ C`) and steps up once it overflows. The number of memory levels therefore
equals the number of **plateaus** in the latency-versus-`log(S)` curve, and each
cache's capacity is the working-set size at the plateau-to-rise transition.

- The curve is lightly median-smoothed (appropriate here because, unlike the
  i.i.d. sample path, this is a genuine ordered sweep whose neighbours share a
  level).
- Change points are detected with **`ruptures` PELT** on the **log-latency**
  signal. Working in log space keeps the small L1→L2 step and the large
  L2→DRAM step comparable in magnitude, so both are detected.
- Adjacent segments whose median-latency ratio is below a threshold (default
  1.4×) are **merged**, correcting noise-induced over-segmentation.
- Each level's latency is summarised by its **median** and **5th/95th
  percentiles** — robust statistics that a single mis-measured point cannot
  distort (replacing the earlier fragile min/max boundaries).

## 4. Cross-Validation of the Level Count (Clustering)
To satisfy the unsupervised-ML objective and provide an independent check on the
change-point count, the per-size latencies (in log space) are additionally
clustered:
- **K-Means** and **GMM**, with the number of clusters chosen automatically by
  **both** the **Elbow Method** (knee of the K-Means inertia curve, located by
  maximum distance to the first–last chord) and the **Silhouette Score** over
  `k ∈ [2, 6]` — applied and compared as the project definition requires.
- **DBSCAN**, a density-based method that needs no `k` and labels sparse
  transition points as noise.

Agreement (or disagreement) between the change-point count and the clustering
counts is reported directly. Across repeated sweeps (`--runs`) each estimator is
scored by count correctness and stability (std of the level count), identifying
the most accurate and consistent method; change-point additionally localises the
capacities and is the productive method for mapping.

## 5. Ground-Truth Validation (`src/autoecho/validation.py`)
Detected cache capacities are compared to hardware ground truth read live from
the OS — `sysctl hw.perflevel0.*` on macOS, `/sys/.../cache/index*/size` on
Linux, `Win32_CacheMemory` on Windows — so the framework validates itself on
whatever machine it runs on. A detected capacity matches a documented cache when
they lie within one octave (a factor of two) on a `log₂` scale, the natural
metric since cache sizes are powers of two sampled geometrically by the sweep;
the exact percentage error is also reported.

## 6. Retained Naive Baseline (`src/autoecho/probe/`, `preprocessing.py`)
The original sample-based probe timed individual random reads preceded by a
write to the same address. This guaranteed L1 residency on every access and,
combined with timer quantisation and the absent ARM flush, made the hierarchy
unmeasurable. It is kept behind `--method samples` purely as the baseline whose
failure motivates the WSS design; its moving-average smoothing (invalid for
i.i.d. samples) is not used in the primary path.
