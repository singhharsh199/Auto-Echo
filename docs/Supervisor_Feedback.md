# Auto-Echo — Supervisor Evaluation & Viva Preparation

*Rigorous UK MSc (Computer Science — Systems Architecture & Machine Learning)
assessment. Dated 2026-07-22. Intended as brutal, formative feedback ahead of the
viva — not a final board mark.*

---

## Overall: **67 / 100** — High Merit, on the cusp of Distinction

A genuinely strong *engineering* project wrapped around an *empirical* claim it
does not yet substantiate. The systems work and the critical analysis are
Distinction-calibre; the evidence base and some of the claims are not. The gap
between them is where the viva will focus.

**Weighting:** Technical Achievement 30% · Methodological Rigour 30% · Critical
Analysis 20% · Presentation 20%.

| Category | Mark |
|---|---|
| Technical Achievement | 74 / 100 |
| Methodological Rigour | 60 / 100 |
| Critical Analysis | 72 / 100 |
| Presentation | 64 / 100 |
| **Overall (weighted)** | **67 / 100** |

---

## Technical Achievement — 74/100

**The strongest part, and genuinely good.** The pointer-chasing WSS probe (seeded
Fisher–Yates Hamiltonian cycle to serialise data-dependent loads), batch-amortised
timing to defeat a coarse timer, runtime tick→ns calibration against the monotonic
clock, and single-core pinning across three OS/ISA targets is competent, idiomatic
low-level systems work. The runtime-calibration argument is a legitimate
improvement over the reference paper's `/proc/cpuinfo` approach. The
count-then-localise ML design (Silhouette chooses *k*, change-point localises
boundaries) is elegant and the correct division of labour.

**Where it loses marks:**
- "Sub-nanosecond precision" is *timer resolution*, not *measurement accuracy*.
  Amortisation removes quantisation; it does nothing for the systematic inclusion
  of pipeline latency in a load-to-use chain. The ~1.5 ns "L1" is a serialised
  load-to-use figure, not a cache access time — say so explicitly.
- Single-threaded, single-buffer; the deep-memory plateau is contaminated by
  DTLB/page-walk cost that page-alignment does not remove. No huge-page control.
  Flagged in §6.6 (credit) but unaddressed.

## Methodological Rigour — 60/100

**This is what caps the mark.**
- **The entire empirical base is one machine.** The Intel/AMD tables are 17 `TBD`
  cells — half the results chapter is a placeholder. "Architecture-agnostic" is an
  assertion about the *code*, not a *finding*. Generality cannot be claimed from n=1.
- **The synthetic cross-platform validation is quasi-circular.** Staircase curves
  generated from assumed capacities, then shown to be recovered, validate the
  estimator against its own modelling assumptions — not real x86 silicon. Present
  Fig. 7 as *method verification*, never as a result.
- **A factor-of-two matching tolerance is close to unfalsifiable.** A 200 KiB
  reading "matches" a 128 KiB L1. Report ±10/25/50% tolerances so "100% (2/2)"
  carries weight.
- **Reproducibility.** The count is now stable via automatic model selection, but
  the honest story is that it was not before. Own that the fixed-seed 3-level
  result is robust *because of* the method change, not by luck.

## Critical Analysis — 72/100

**The best intellectual asset.** The documented failure baseline is exactly right:
identifying that write-before-read pulls the line into L1 and masks the hierarchy,
that `clflush` is x86-only, and that single-read timing measures the 41.7 ns tick
rather than memory — mechanism-level reasoning at distinction level. Retaining it
as a *negative result* is mature. §6.6 threats are honest. Loses marks only for
stopping short on the SLC claim (below).

## Presentation — 64/100

Well-structured, clean prose, coherent failure→redesign→validation arc; clear,
pedagogically effective diagrams. **But:**
- The diagrams are **not "vector"** — they are 300 DPI raster PNGs from Matplotlib.
  Export SVG/PDF for true vector. Calling raster "vector" in a systems dissertation
  is a small credibility ding.
- **~4,400 words is short** for an MSc; lit review and methodology are off-loaded
  to separate files rather than integrated.
- Missing declaration/appendix/word count; the 17 visible `TBD`s read as unfinished.

---

## Three claims to retract or hedge before the viva

1. **"The M1 has been *perfectly mapped and validated*."** — No. 2/2 documented
   caches matched *within a factor of two*, ~20% mean capacity error (L1 +23%,
   mid-band +16%). "Perfectly mapped" is false and will have to be retracted live.
2. **"Discovering... the Apple M1 SLC."** — The reproducible, automatically-selected
   result is **three levels**: L1, a **merged L2/SLC band**, DRAM. The four-level
   split appears only under a hand-forced penalty that is then removed. Defensible
   claim: "L2 and SLC are too close to separate by automatic model selection; the
   finer split is a *candidate* sub-structure." Do not headline SLC detection.
3. **"Consensus between K-Means, GMM, and DBSCAN."** — GMM and DBSCAN were the
   *unstable* estimators. It is Silhouette-K-Means carrying the count with the
   others as noisy corroboration, not a consensus of equals.

## Viva questions to prepare for

- *"Half the results are `TBD`. Defend architecture-agnosticism from one machine."*
- *"Is the ML doing real work? A 1-D, well-separated, three-mode log-latency
  distribution is trivially separable — why not a threshold?"* → Lead with the one
  strong answer: the **number** of modes is unknown a priori and varies by machine,
  which is precisely what unsupervised model selection is for.
- *"Your synthetic validation assumes the answer. What independent evidence exists?"*
  → `crosscheck_lmbench.py` exists but was **never run**. Running lmbench
  `lat_mem_rd` on the same M1 and overlaying is the highest-value missing experiment.
- *"Separate cache latency from TLB/page-walk in the 10–14 MB region."*
- *"The DRAM band is p5–p95 = 45–141 ns — a 3× spread. What does that say about the
  stability of the deepest measurement?"*
- *"Novelty over Yotov (2005) and lmbench, precisely?"*

## Route from 67 → 72–75 (Distinction), in priority order

1. **Run one real x86 machine** (Intel *or* AMD). Fills the tables, enables the
   cross-machine overlay, and converts "architecture-agnostic" from claim to
   finding. Worth ~4–6 marks alone.
2. **Run the lmbench cross-check** on the M1 — external validation available today,
   no new hardware.
3. **Tighten validation** to multiple tolerances; retire "perfect"/"SLC-detected".
4. **One TLB control** (huge pages) to defend the deep-memory plateau.
5. **Expand to length**, integrate lit-review/methodology, export vector figures,
   add the missing front/back matter.

**Verdict:** a Distinction-grade *instrument* and a Merit-grade *study*. The
engineering is done; the science is half-finished. Finish the x86 run and the
lmbench overlay, drop the two overclaims, and this is a 72+. Left as-is, a rigorous
examiner lands it at 65–67.
