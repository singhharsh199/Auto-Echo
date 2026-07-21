# Literature Review: User-Space Discovery of the Memory Hierarchy

## 1. Introduction and Scope
This project sits at the intersection of two research traditions: (i) empirical
characterisation of the memory hierarchy from user space through timing
measurements, and (ii) unsupervised machine learning for automatic structure
discovery. The immediate inspiration is the ECOOP 2025 paper *"Shouting at
Memory: Where Did My Write Go?"* (Klimis et al.), but the measurement technique
Auto-Echo ultimately adopts belongs to a much older and well-established body of
work on cache-hierarchy benchmarking. This review situates the project honestly
within that lineage and states precisely where its novelty lies.

## 2. Memory Echolocation (Klimis et al., ECOOP 2025)
Klimis et al. introduce *memory echolocation*: emitting a store and timing the
subsequent load, whose latency acts as a signature for where the data currently
resides. Their headline contribution is not the latency profiling itself but its
use as an **Oracle inside an active model-learning loop** that infers the
persistency semantics of non-volatile memory (including the Intel Write Pending
Queue, WPQ). On an Intel Xeon E-2286G they report characteristic bands for L1,
L2, L3, WPQ, and DRAM.

Two points must be made carefully, because the original Auto-Echo framing
inherited assumptions from this paper that do not transfer:
- The **WPQ is a persistent-memory (Optane) construct**, not a general feature of
  the commodity cache hierarchy. Expecting a WPQ tier on an Apple M1 (as the
  first Auto-Echo prototype did) is a category error.
- Klimis et al. rely on **`clflush` and fine-grained `rdtscp`**, both x86-only.
  Neither is available in user space on Apple Silicon, so their exact method is
  not portable — motivating a different measurement primitive.

Auto-Echo isolates the *echolocation / hierarchy-mapping* aspect, makes it
architecture-agnostic and strictly user-space, and replaces manual latency
thresholding with unsupervised inference.

## 3. The Classical Lineage: User-Space Cache Characterisation
Measuring cache-hierarchy parameters from user space via a working-set-size
(WSS) sweep is a mature technique, and this project's probe is a modern
re-implementation of it. The key prior art:

- **Saavedra & Smith (1989/1995)** established that varying the size and stride
  of an array-access micro-benchmark reveals cache capacities and line sizes as
  discontinuities in measured time — the foundational "sweep" idea.
- **McVoy & Staelin, lmbench (1996)** — the `lat_mem_rd` benchmark performs a
  **pointer-chasing** load-latency sweep across increasing array sizes. Its
  data-dependent load chain is exactly the mechanism Auto-Echo uses to defeat
  the hardware prefetcher without any cache-flush instruction. This is the single
  closest antecedent to Auto-Echo's probe.
- **Yotov, Pingali & Stodghill (2005)** automated the *extraction* of cache
  parameters (capacity, line size, associativity) from such curves, framing
  hierarchy discovery as an automated measurement problem.
- **Manegold's Calibrator** and **Molka et al. (2009)** further refined
  latency/bandwidth characterisation across the hierarchy.
- **Bryant & O'Hallaron's "memory mountain"** popularised the WSS × stride
  latency surface as a pedagogical and diagnostic artifact; Auto-Echo's output
  plot is a 1-D (fixed-stride) slice of this mountain.

**Implication for novelty.** The *measurement* of cache sizes by pointer-chasing
is classical; claiming it as novel would be indefensible in a viva. Auto-Echo's
contribution is therefore explicitly reframed as the **layer above** the
measurement: a fully unsupervised, zero-configuration inference stage that
determines *how many* levels exist and *where their boundaries lie* — with no
hard-coded thresholds and no prior knowledge of the machine — and that validates
itself automatically against OS-reported ground truth across architectures.

## 4. Hardware Barriers to User-Space Timing
The literature and this project's own empirical work identify three barriers:
- **Prefetching.** Regular access patterns are predicted and hidden by the
  prefetcher. Pointer chasing with a randomised permutation makes each address
  data-dependent, serialising accesses and neutralising the prefetcher.
- **Timer quantisation.** Apple Silicon's `mach_absolute_time` advances on a
  24 MHz counter (~41.7 ns/tick), far coarser than an L1 hit (~1.5 ns).
  Amortising 10⁶+ dependent hops inside one timing window recovers
  sub-nanosecond effective resolution.
- **No user-space flush on ARM.** `clflush` is x86-only and macOS exposes no
  data-cache flush to user space. The WSS methodology sidesteps this entirely:
  a working set larger than a cache level simply overflows it by construction,
  so no explicit eviction is required.

## 5. Unsupervised Model Selection
The number of memory levels is unknown a priori, so the inference stage must
select model complexity automatically. Two families are relevant:
- **Clustering + internal validity indices.** K-Means and Gaussian Mixture
  Models with the **Silhouette Score** (Rousseeuw, 1987) or BIC provide a
  count of well-separated latency groups. DBSCAN (Ester et al., 1996) adds a
  density-based, count-free alternative that treats transition points as noise.
  A known limitation is that 1-D silhouette tends to favour the single largest
  gap, under-counting closely spaced levels.
- **Change-point detection.** Because a WSS curve is a piecewise-constant
  (staircase) signal, detecting the points at which the latency level shifts is
  a more natural formulation than clustering values. The `ruptures` library
  (Truong et al., 2020) provides PELT, which selects the number of breakpoints
  automatically via a penalty. Auto-Echo uses change-point detection as its
  primary estimator and the clustering indices as independent cross-checks.

## 6. Summary and Positioning
Klimis et al. demonstrate that software timing is a valid proxy for hardware
memory state; the classical benchmarking literature (lmbench, Saavedra & Smith,
Yotov) demonstrates that cache capacities are recoverable from user-space sweep
curves. Auto-Echo combines the portable, flush-free **pointer-chase WSS probe**
from the latter with an **unsupervised change-point + clustering inference
stage** to deliver automatic, architecture-agnostic, self-validating memory
hierarchy discovery — the specific gap left open by both traditions.
