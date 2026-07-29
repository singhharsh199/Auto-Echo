# Auto-Echo — Outstanding Work

Living checklist of what's left to do. Updated 2026-07-29.

**Machine status: M1 = validated (2/2). Intel i5-13450HX = validated (3/3, 2 MiB
huge pages).** Both are fully written up. The dissertation is 35 pages / ~15,760
words, builds clean, and contains no placeholders. Suite: 34 passed, 1 skipped.

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

## Blocking the 80+ band (one experiment)
- [ ] **lmbench external cross-check.** The evaluation's only oracle is OS-reported
      capacity, which says nothing about whether the *latency curve* is right.
      Converter is written and tested (5 tests). On the Intel box under WSL2:
      ```
      lat_mem_rd -N 5 -t 512 128 > lmbench_raw.txt
      python crosscheck_lmbench.py lmbench_raw.txt -o data/intel_i5_13450hx/lmbench_curve.csv
      python compare_curves.py data/intel_i5_13450hx/wss_curve.csv \
          data/intel_i5_13450hx/lmbench_curve.csv \
          --labels "Auto-Echo,lmbench lat_mem_rd" --annotate -o data/crosscheck_intel.png
      ```

## Open on the M1
- [ ] **Page size is never stated, and it is not 4 KiB.** macOS on Apple Silicon
      uses **16 KiB** base pages (`sysctl hw.pagesize` = 16384). The dissertation
      makes page size the decisive variable for the Intel L3 but never gives the
      M1's, so the cross-machine comparison is confounded by an unstated factor.
      Worth one sentence in §6.4 and a row in §6.1. The likely quantitative story —
      that the M1's TLB reach comfortably exceeds its cache hierarchy while the
      Intel's 4 KiB reach does not — would *strengthen* the TLB argument, but the
      TLB entry counts need a citable source before the claim is made.
- [ ] **Huge pages never tested on the M1.** The `--huge-pages` path is
      Windows-only (`VirtualAlloc(MEM_LARGE_PAGES)`). macOS exposes
      `VM_FLAGS_SUPERPAGE_SIZE_2MB`. Open question: would larger pages split the
      merged L2+SLC band that §6.2 reports as a single mid-band?

## Open on the Intel
- [ ] **The −30.4% L3 under-read is asserted, not tested.** §6.3 attributes it to
      shared-L3 contention. One quiesced-vs-loaded sweep pair would test it; if the
      knee moves, that is evidence, and if it does not, the explanation is wrong.
- [ ] Performance-counter corroboration of the TLB story.

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
