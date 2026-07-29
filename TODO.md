# Auto-Echo — Outstanding Work

Living checklist of what's left to do. Updated 2026-07-29.

**Machine status: M1 = validated (2/2). Intel i5-13450HX = validated (3/3, 2 MiB
huge pages).** The two items that were blocking the 80+ band are now done: the
**lmbench external cross-check** (§6.3.1, Table 11, Fig. 11) and the **shared-L3
contention test** (§6.3.2, Table 12, Fig. 12). Suite: **35 passed, 0 skipped** on
Windows (one test skips only on macOS).

## Done
- [x] WSS pointer-chase probe + runtime timer calibration (working method)
- [x] **Level discovery**: Silhouette *counts* the levels, change-point *localises*
      them (no per-machine penalty)
- [x] **Exact 1-D clustering** — Lloyd's heuristic replaced by the globally optimal
      dynamic program (`_exact_1d_kmeans`; Fisher 1958 / Ckmeans.1d.dp). Counting is
      now provably optimal and deterministic; `n_init` and the K-Means
      `random_state` are gone. Verified to change no reported result
      (`verify_kmeans_optimality.py`).
- [x] Estimator comparison decoupled (independent cost-knee counter — non-circular)
- [x] **Intel i5-13450HX validated** — 2 MiB huge-page run unmasks the 20 MiB L3
      (detected 13.9 MiB, 0.52 oct), recall/precision 3/3 = 100%, F1 1.00,
      Silhouette stable at 4 levels (std 0.00) across 3 sweeps
- [x] **Sampling-density confound closed** — M1 re-measured at 5/10/20 points per
      octave, Intel subsampled to 2.5/5/10; selected count invariant on both
      (Table 10, `sampling_density_sweep.py`)
- [x] **§5 baseline contradiction resolved** — failure re-diagnosed as structural
      (write-before-read guarantees L1 residency), with the Intel `clflush`
      evidence promoted to Table 1 proving it fails on x86 too
- [x] Literature review and methodology inlined; §3 now has a full unsupervised
      model-selection subsection; 24 references, all cited
- [x] Hyperparameter disclosure table (§4.4, 16 constants, none tuned per machine)
- [x] Abstract cut to ~278 words with an explicit research question
- [x] Acknowledgements written; **Appendix A** (GenAI accountability) written
- [x] All placeholders removed (no TBDs, no M5 section)
- [x] Fig. 10 cross-machine overlay refreshed from the huge-page Intel curve
- [x] Interactive dashboard (`frontend/`) driven off the pipeline's own outputs
- [x] Five diagrams + machine-labelled result figures; PDF rebuilt with ToC

## Blocking the 80+ band — DONE
- [x] **lmbench external cross-check (§6.3.1, Table 11, Fig. 11).** lmbench
      `lat_mem_rd` built under WSL2 (needed `libtirpc` for the removed `rpc/rpc.h`
      and a direct compile against its lib sources to link on gcc 15) and swept with
      `-N 5 -t 512 128`. Overlaid on the Auto-Echo 2 MiB huge-page curve: the two
      independent tools recover the **same four-tier staircase** with an almost
      identical L1→L2 step (3.0× vs 3.1×); the inner hierarchy agrees within
      ~20–25 %, the deep region carries an identified page-size/WSL2 confound. The
      default (non-`-t`) stride mode is retained as a **negative control** — its
      prefetchable walk collapses deep latency to ~5–12 ns, confirming `-t`
      (thrash, prefetcher-defeating like Auto-Echo's randomised chase) is the correct
      comparator. Artefacts: `data/intel_i5_13450hx/lmbench_raw.txt`,
      `lmbench_curve.csv`, `lmbench_stride_curve.csv`, `data/crosscheck_intel.png`.

## Open on the M1
- [ ] **Page size is never stated, and it is not 4 KiB.** macOS on Apple Silicon
      uses **16 KiB** base pages (`sysctl hw.pagesize` = 16384). The dissertation
      makes page size the decisive variable for the Intel L3 but never gives the
      M1's, so the cross-machine comparison is confounded by an unstated factor.
      Worth one sentence in §6.4 and a row in §6.1. The likely quantitative story —
      that the M1's TLB reach comfortably exceeds its cache hierarchy while the
      Intel's 4 KiB reach does not — would *strengthen* the TLB argument, but the
      TLB entry counts need a citable source before the claim is made.
- [x] ~~Huge pages on the M1~~ — **tested and impossible from user space.** macOS
      superpages (`VM_FLAGS_SUPERPAGE_SIZE_2MB` *and* `VM_FLAGS_SUPERPAGE_SIZE_ANY`)
      both fail with `EINVAL` on Apple Silicon; they are an Intel-era facility arm64
      does not honour. Written up in §6.4 and §7 as a finding about platform
      asymmetry rather than an outstanding experiment. Answering the L2/SLC merge
      question on Apple Silicon now needs performance counters or a kernel-side
      allocation, not a larger page.

## Open on the Intel
- [x] **The −30.4% L3 under-read is now MEASURED as contention (§6.3.2, Table 12,
      Fig. 12).** Quiesced-vs-loaded huge-page comparison: an 8-worker shared-L3
      streaming load (`l3_load.py`, 8 × 32 MiB pinned off CPU 0) collapses the
      detected L3 knee from 13.9 MiB to a stable **3.5 MiB**, while the least-contended
      sweep recovers ~19.7 MiB (≈ nominal 20) — a monotonic contention gradient. The
      knee is frequency-invariant, so the capacity result survives the all-core-turbo
      DVFS drop under load. Methodological note: the 512 MiB probe allocation loses
      2 MiB pages under load (Windows error 1450, large-page-pool depletion), so the
      loaded sweep used `--max-mb 128` (the knee sits below 20 MiB, on the identical
      grid, so it is unaffected). Reported as a *two-condition* comparison on one
      machine, not a proven dose-response law. Artefacts: `data/intel_l3_quiesced/`,
      `data/intel_l3_loaded/`, `data/l3_contention_intel.png`, `l3_contention_report.py`.
- [ ] Performance-counter corroboration of the TLB story.
- [x] *(C — DONE)* **Capacity confidence intervals over 10 huge-page sweeps**
      (`capacity_ci.py`; Table 6 footnote, §7). After cooling the CPU back to full
      turbo (L1 1.57 ns), a `--runs 10 --max-mb 512 --huge-pages` run gives per-level
      capacity median [min–max]: **L1 55.7 KiB [55.7–55.7], L2 1.2 MiB [1.2–1.2],
      L3 19.7 MiB [13.9–19.7]** — private L1/L2 zero spread, only the shared L3 varies,
      corroborating §6.3.2. That run also hit 3/3 recall+precision at 7.3 % mean
      error. Artefacts: `data/intel_ci/`, `capacity_ci.py`.
- [x] *(D — DONE)* **Measured Intel density rows for Table 10 at 5/10/20 pts/octave**
      (`sampling_density_sweep.py measure --densities 5 10 20 --max-mb 512
      --huge-pages`). Selected count **k = 4 at every density** (104/202/388 points;
      silhouette ~0.93; elbow 2, DBSCAN 4, cp-knee 2) — confirms the previously
      subsampled rows. Table 10 now shows measured Intel rows, including the 20
      pts/octave density that lies *above* the old subsampled grid. Artefacts:
      `data/density_intel/`.

## Author items (not code)
- [ ] Sign and date the Declaration of Originality.
- [ ] **Verify Appendix A line by line before signing** — it must describe your
      conduct, not a template.
- [ ] Acknowledgements: confirm Klimis's full name (reference [1] gives only "V.")
      and name the owner of the Windows machine if appropriate.
- [ ] Reflective essay (separate deliverable).
- [ ] Port into the official QMUL template if required; add final word count.
- [ ] Repo hygiene: the copyrighted Klimis PDF is still in the repo root.

## Medium
- [ ] **Noise-robust onset rule.** The gated hybrid capacity estimator collapses on
      the huge-page Intel L1 (−96.9%): `_onset_capacity` stops at the *first* sample
      above threshold, and one 2.02 ns spike at 1.5 KiB on an otherwise flat 1.58 ns
      plateau triggers it. Require a **sustained** departure (k consecutive points).
- [ ] Confidence intervals on capacities (std is reported for level counts only).
- [ ] GMM scored by BIC as a further independent count — the mixture is now the only
      estimator in the ensemble still fitted heuristically.

## Adding a third machine
The M5 placeholder section was deleted, so a third machine needs structural edits,
not just data. Collect in one session:
```
python -m autoecho --method wss --max-mb 512 --runs 3 --output-dir data/<id>
python sampling_density_sweep.py measure --densities 5 10 20 --save data/density_<id>
python verify_kmeans_optimality.py "<Name>=data/<id>/wss_curve.csv"
python compare_curves.py data/wss_curve.csv data/intel_i5_13450hx/wss_curve.csv \
    data/<id>/wss_curve.csv --labels "Apple M1,Intel i5-13450HX,<Name>" \
    --annotate --output data/compare_mountain.png
```
Then: add a row to §6.1; insert a results subsection (renumbering §6.4/§6.5);
add a column to the §6.4 comparison table; add rows to Table 10 and the §4.2.1
optimality table; refresh Fig. 10; update "two machines"/"two ISAs" in the
abstract, contributions and §8; uncomment the machine entry in
`frontend/scripts/build-data.mjs` and re-run `npm run prep`.
