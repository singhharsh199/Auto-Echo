# Auto-Echo — Outstanding Work

Living checklist of what's left to do. Updated 2026-07-22.

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
- [x] Test coverage for the WSS report path + legacy samples path (suite 23/23)
- [x] `.gitignore` hardened against the web-dump / scratch-binary / LaTeX output

## Do now
- [ ] **Repo-hygiene deletions** (run locally — safety guard blocks the agent):
      the ~27 MB web-dump folder, `timecheck`(+`.c`), the copyrighted Klimis PDF,
      LaTeX build artifacts, the template `.zip`, the two redundant
      `generate_diagrams_{gv,polished}.py`, and `data/latency_distribution.png`.
- [ ] Commit the deletions once done.

## High (needs hardware / author)
- [ ] Run on the **Apple M5** (ARM64) → fill the `TBD` cells in §6.4/6.5; then
      add the combined cross-machine figure. (Intel x86/Windows now done.)
- [ ] **GenAI accountability statement** — complete, sign, add to an appendix (author).
- [ ] **Reflective essay** — write (author).

## Medium
- [ ] Front/back matter: Acknowledgements, Declaration of Originality, Appendix,
      word count (ToC already in the PDF).
- [ ] Port the dissertation into the official QMUL `.docx`/LaTeX template if required.
- [ ] Expand length (~4,400 words) — integrate the standalone literature review
      (`docs/01_`) and methodology (`docs/02_`) into the body.
- [ ] `compare_curves.py` / `crosscheck_lmbench.py` figures (need x86 data).

## Low
- [ ] Optionally expose `evaluate_lof_mitigation` via a CLI flag for one-command
      reproducibility (currently callable + cited in §5).
