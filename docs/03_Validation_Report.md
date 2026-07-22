# Naive Baseline Failure Log (Negative Result — NOT the WSS Validation)

> ⚠️ **Read this first.** This file is **not** an Auto-Echo validation result. It
> is the archived output of the **naive sample-based probe** — the abandoned
> `--method samples` baseline (sequential/single reads + x86 `clflush` +
> write-before-read, with IQR/LOF/moving-average preprocessing). It is retained
> **only as documented evidence of that baseline's failure**, per the dissertation's
> critical analysis (see `docs/Draft_Dissertation.md` §5, "Baseline and Its
> Failure"). The tiers and latencies below are **timer-quantisation artefacts**,
> not real memory-hierarchy measurements — do not cite them as a discovered
> hierarchy.
>
> 👉 **For the actual delivered result** (WSS pointer-chase probe + runtime timer
> calibration + change-point/PELT level discovery + clustering cross-check +
> automatic OS ground-truth self-validation), see the real, current report:
> **[`data/validation_report.md`](../data/validation_report.md)**.

---

## Why this output is meaningless (summary)

The naive baseline timed **individual** random reads on Apple Silicon. As analysed
in dissertation §5, three structural defects made its output carry **no
memory-latency information**:

1. **Timer quantisation.** `mach_absolute_time` advances on a ~24 MHz counter
   (~41.7 ns/tick), far coarser than an L1 hit (~1.5 ns). Each single read
   therefore measured **0 or 1 tick** (0 or ~41.7 ns) — the timer, not memory.
2. **No user-space flush on ARM.** `clflush` is x86-only and macOS exposes no
   data-cache flush, so the "forced DRAM" path silently degenerated and generated
   no deep-memory accesses.
3. **Write-before-read guarantees L1 residency.** Writing a line immediately
   before timing its read pulls it into L1, so every measured access was an L1 hit
   by construction — masking L2/L3/DRAM entirely.

The apparent "tiers" in the table below are a **smoothing artefact**: a window-5
moving average over the 0/1-tick samples blends them into spurious sub-steps at
multiples of 41.7 / 5 ≈ 8.3 ns (≈ 0, 8, 17, 25, 33 ns). The labels ("L1 Cache",
"WPQ / Memory Controller", etc.) are the naive pipeline's **incorrect
attributions** of these artefacts, not identified caches. A direct LOF evaluation
(dissertation §5) confirmed the failure is *structural*, not noise: ~0.04% of
samples were flagged, and 100% of survivors still lay exactly on integer
timer-tick multiples.

The numbers are reproduced **unaltered** below purely so this artefact is on record.

---

## Archived naive-baseline output (timer-quantisation artefacts — do not cite)

| Naive pipeline's (spurious) label | Latency Range [ns] | Mean Latency [ns] | Data Points |
|---|---|---|---|
| **L1 Cache** | 0 - 0 | 0.00 | 813 |
| **L2 Cache** | 8 - 8 | 8.33 | 4151 |
| **L3 Cache** | 16 - 16 | 16.67 | 3814 |
| **WPQ / Memory Controller** | 24 - 25 | 25.00 | 1077 |
| **DRAM** | 33 - 33 | 33.33 | 116 |
| **Swap/Disk** | 41 - 50 | 42.33 | 25 |

*Every value above is an integer (or window-5-averaged) multiple of the ~41.7 ns
timer tick — the signature of the quantisation failure, not of a cache hierarchy.
These findings motivated the WSS redesign; the real validated hierarchy is in
[`data/validation_report.md`](../data/validation_report.md).*
