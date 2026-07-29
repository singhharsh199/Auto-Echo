# Auto-Echo — Outstanding Work

Living checklist of what's left to do. Updated 2026-07-29.

**Machine status: M1 = validated (2/2). Intel i5-13450HX = validated (3/3, 2 MiB
huge pages). Apple M5 = next.** Both measured machines are fully written up in the
dissertation and the PDF is rebuilt; §6.4 and the M5 column of §6.5 are the only
result placeholders left.

## Done
- [x] WSS pointer-chase probe + runtime timer calibration (working method)
- [x] **Hybrid level discovery**: K-Means + Silhouette *counts* the levels,
      change-point *localises* them (penalty-free, architecture-agnostic)
- [x] Cross-platform behaviour validated *in method* on synthetic Intel/AMD/M1/VM curves
- [x] Estimator comparison decoupled (independent cost-knee counter — non-circular)
- [x] §6 of the dissertation reconciled to the 3-level M1 result (Tables 1/3/4,
      abstract, contributions, threats, conclusion)
- [x] Five novice-friendly diagrams (hierarchy, staircase, pointer-chase,
      pipeline, cross-platform) + `Draft_Dissertation.pdf` rebuilt with a ToC
- [x] Machine-labelled result figures
- [x] Stale docs fixed (`03_Validation_Report.md`, `Project_Story_For_Viva.md`)
- [x] Packaging: `[build-system]`, Python floor unified to 3.10
- [x] README nits (stray fence, documented flags)
- [x] Duplicate-"DRAM" label bug fixed
- [x] Dead code removed (`discover_memory_levels_gmm`)
- [x] Test coverage for the WSS report path + legacy samples path (suite 29 passed,
      1 skipped — the per-core-GT test skips off Windows)
- [x] `.gitignore` hardened against the web-dump / scratch-binary / LaTeX output
- [x] **Intel i5-13450HX validated** — 2 MiB huge-page run unmasks the 20 MiB L3
      (detected 13.9 MiB, 0.52 oct), recall/precision 3/3 = 100%, F1 1.00, and
      K-Means + Silhouette stable at 4 levels (std 0.00) across 3 sweeps
- [x] Dissertation reconciled to that result (abstract, contributions, §4.1 huge-page
      control, §6.1/§6.3/§6.5/§6.6, §7, §8) and `Draft_Dissertation.pdf` rebuilt
- [x] Fig. 10 cross-machine overlay refreshed from the huge-page Intel curve
- [x] §6.5 capacity-estimator table recomputed on the huge-page curve (+ an L3 row);
      the stale "hybrid is never catastrophic" claim withdrawn — see below

## Do now
- [ ] **Repo-hygiene**: only the copyrighted Klimis PDF is still in the repo root
      (author's call whether to keep it locally and gitignore it). The web-dump
      folder, `timecheck`(+`.c`), `generate_diagrams_{gv,polished}.py` and
      `data/latency_distribution.png` are already gone.

## High (needs hardware / author)
- [ ] Run on the **Apple M5** (ARM64) → fill the `TBD` cells in §6.4/6.5; then
      refresh the Fig. 10 overlay with a third curve. (M1 and Intel both done.)
      Use `--max-mb 512 --runs 3`; huge pages are Windows-gated, so the M5 runs
      the plain path like the M1 did.
- [ ] **GenAI accountability statement** — complete, sign, add to an appendix (author).
- [ ] **Reflective essay** — write (author).

## Medium
- [ ] **Noise-robust onset rule** (§7, new). The gated hybrid capacity estimator
      collapses on the huge-page Intel L1 (−96.9%): `_onset_capacity` stops at the
      *first* sample above threshold, and one 2.02 ns spike at 1.5 KiB on an
      otherwise flat 1.58 ns plateau triggers it. Require a **sustained** departure
      (k consecutive points) in `analysis._onset_capacity`. The improved measurement
      is what exposed this — the 4 KiB L1 plateau failed the flatness gate and so
      fell back safely to `edge`.
- [ ] Front/back matter: Acknowledgements (placeholder in the PDF), Appendix,
      word count. Declaration of Originality and ToC are already in.
- [ ] Port the dissertation into the official QMUL `.docx`/LaTeX template if required.
- [ ] Expand length (currently ~9,800 words) — integrate the standalone literature
      review (`docs/01_`) and methodology (`docs/02_`) into the body.
- [ ] `crosscheck_lmbench.py` overlay — needs an lmbench `lat_mem_rd` run (WSL2 on
      the Intel box); would give external corroboration neither machine has yet.
      (`compare_curves.py` is done — Fig. 10.)

## Low
- [ ] Optionally expose `evaluate_lof_mitigation` via a CLI flag for one-command
      reproducibility (currently callable + cited in §5).
