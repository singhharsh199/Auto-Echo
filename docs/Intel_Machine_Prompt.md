# Prompt for Claude Code — VALIDATE the Intel i5-13450HX results (benchmarked to the Apple M1)

> **How to use:** on the Intel machine, `git pull`, open Claude Code in the repo root, and
> paste everything from `─── PROMPT ───` down. The Apple M1 is the fully-validated reference;
> the goal is to bring the Intel result up to that same standard. **Never fabricate a
> measurement, and never relabel a result "validated" without the evidence** (see the
> Integrity Rule).

---

─── PROMPT ───

You are working on **Auto-Echo** (MSc dissertation, QMUL): a tool that discovers a CPU's
cache hierarchy (L1/L2/L3/DRAM) from user space via a working-set-size (WSS) pointer-chase
latency sweep plus unsupervised level discovery, validated against OS ground truth. Key
files: probe `src/autoecho/wss/wss_probe.c` (+ wrapper `src/autoecho/wss/__init__.py`),
analysis `src/autoecho/analysis.py`, ground truth `src/autoecho/validation.py`, CLI
`python -m autoecho`. Machine: **Intel Core i5-13450HX** (Raptor Lake, 6 P + 4 E cores),
Windows, x86-64; per-core caches L1d **48 KiB**, L2 **~1.25–2 MiB/core**, L3 **~20 MiB
shared**, 64-byte lines; the probe pins to CPU 0.

## YOUR GOAL: validate the Intel results — move the Intel machine from "measured" to "validated"

The framework is fully **validated** on an Apple M1 — that is the standard you must reach.
The dissertation deliberately grades its machines:

- **"validated"** (Apple M1): every documented cache matched OS ground truth → **100% recall,
  100% precision (2/2)**, and all five level-count estimators **agree** (unanimous, std 0).
- **"measured"** (Intel, current): the tool ran and recovered real data, but only **L1 + L2
  (2/3 = 66.7%)** — the **20 MiB L3 is masked by 4 KiB-page TLB/page-walk latency** — and the
  level count is **unstable** (estimators range 2–5 across sweeps). It is honestly *not*
  called "validated" because a documented cache was not recovered.

**What separates the two is exactly one thing: the masked L3.** Unmasking it with **2 MiB
large pages** is the single action that can earn the Intel result the "validated" label — and
the dissertation predicts large pages will *also* stabilise the level count. The large-page
code is already written (`--huge-pages` / `AUTOECHO_HUGEPAGES=1`, `hugepages_available()`,
graceful fallback); what remains is the **privileged run** and, only if it succeeds, the relabel.

### ⚠️ INTEGRITY RULE — read twice
Upgrade the Intel status to **"validated" ONLY IF** the huge-page run *actually* produces:
(a) provenance "**2 MiB large pages**" in the report (huge pages truly took effect), **and**
(b) a real **~20 MiB L3 plateau**, giving **recall 3/3 = 100%** with the L3 within a factor of two.
If the L3 does **not** resolve, or admin rights are unavailable, the Intel result **stays
"measured"** — record exactly what you observed and change no labels. **Never relabel on
faith; the honest "measured" is worth more than an unearned "validated."**

## The M1 benchmark — physical anchors that must hold on the Intel run too
- Build: `pip install -e .` clean (needs **MSVC C++ Build Tools**). Tests: `pytest` →
  **~30 passed** on Windows (the per-core-GT test that skips on macOS runs here).
- Label: **`13th Gen Intel Core i5-13450HX (x86-64, Windows)`**.
- L1 ≈ **1.6 ns**, DRAM ≈ **143 ns**, monotonic staircase. **If L1 < 0.3 ns or DRAM < 15 ns,
  the tick→ns calibration is broken — stop and report.**

## Already done and committed — verify intact, do NOT rebuild
Per-core ground truth (`GetLogicalProcessorInformationEx`) → **0% → 66.7%** (L1 +16%, L2 −1.5%
matched; the 3.5 MiB "L3" correctly a false positive); clflush baseline; regenerated artifacts
+ cross-machine overlay (Fig. 10); dissertation §6.3/§6.5/§6.6. **Rule:** the M1/macOS/ARM path
is the validated benchmark and must NOT regress — gate every Windows/x86 change; keep `pytest`
green.

## REQUIRED ACTIONS (in order)

**0. Reproduce the benchmark build.** venv + `pip install -e .`; `pytest -q` (~30 passed);
`python -m autoecho --method wss --max-mb 128 --runs 1 --output-dir data/_scratch` — confirm
the label and L1 ≈ 1.6 ns / DRAM ≈ 143 ns. Report these.

**1. Grant + prove the privilege** (needs a Windows admin, ~15 min). `secpol.msc` → *Local
Policies* → *User Rights Assignment* → **Lock pages in memory** → add your user → **log out
and back in**. Open an **elevated** shell, `cd` repo, activate venv. Prove it:
`python -c "import autoecho.wss_probe_c as w; print(w.hugepages_available())"` → must print
**`True`**. If `False`, the right isn't active — recheck the grant + elevation; do not proceed
to step 2's validation claim.

**2. Run the validating sweep:**
`python -m autoecho --method wss --max-mb 512 --runs 3 --huge-pages --output-dir data/intel_i5_13450hx`

**3. Check the validation criterion and report each item explicitly:**
- [ ] Report's `Chase-buffer allocation:` line = **"2 MiB large pages"**.
- [ ] A **4th plateau near ~20 MiB** (the L3) is present in the curve.
- [ ] **Recall = 3/3 = 100%**; L3 detected within a factor of two of 20 MiB.
- [ ] Level count now **stable** across the 3 sweeps (report the agreement vs the old 2–5).
- [ ] L1 ≈ 1.6 ns and DRAM ≈ 143 ns still hold.

**4a. IF the criterion is met → the Intel is VALIDATED. Relabel (only now):**
- §6.1 test-machine table, Status cell: `measured (L1/L2; L3 masked by TLB)` → **`validated`**.
- §6.3 heading: `Intel x86 (Raptor Lake P-core) — measured` → `— validated`.
- §6.1 intro line "Two real machines are now measured" and the §6.5 comparison table
  (`2/3 (L1, L2)` → `3/3 documented`; `L3 masked by TLB` → the measured L3; count stability →
  the new value).
- Abstract + §8 conclusion: revise the "masks the 20 MiB L3 / honest limit / measured"
  language to state that the **2 MiB huge-page control resolves the full L1/L2/L3/DRAM
  hierarchy on x86, validated** — while **explicitly recording the provenance**: this L3
  result requires huge pages and is not the default 4 KiB-page behaviour (keep that honest).
- **Model-selection figure (Fig. 9) + Table 6:** these currently show the estimators
  *disagreeing* (Elbow k = 2 vs Silhouette k = 4) — the visual proof of the unstable count.
  If huge pages **stabilise** the count (estimators now agree), the `--huge-pages` run
  regenerates `data/intel_i5_13450hx/model_selection.png`; update **Fig. 9**'s caption and
  **Table 6** from "disagree" to the new agreement (mirroring the M1's Fig. 6 / Table 2). If
  the count stays unstable even with the L3 resolved, leave Fig. 9 / Table 6 as "disagree".

**4b. IF the criterion is NOT met (L3 still masked, or blocked on admin):** leave every
"measured" label untouched; add one sentence recording the huge-page attempt and its outcome.
The dissertation remains honest and correct as-is.

**5. Refresh the cross-machine overlay** (Intel vs the M1 benchmark):
`python compare_curves.py data/wss_curve.csv data/intel_i5_13450hx/wss_curve.csv --labels "Apple M1 (ARM64),Intel i5-13450HX (x86-64)" --annotate --output data/compare_mountain.png`

**6. Verify the already-done work is intact** (per-core GT recall ≥ 66.7%; clflush baseline;
`pytest` green).

**7. Rebuild the PDF and commit.**
`pandoc <tmp>.md -o Draft_Dissertation.pdf --pdf-engine=xelatex --toc --toc-depth=3 --resource-path=docs -V geometry:margin=1in -V mainfont="Cambria"` (if a `→`/`≈` glyph is missing, replace it with `$\rightarrow$`/`$\approx$` in a temp copy first).

## (Optional) External corroboration the M1 lacks — lmbench
Via **WSL2 Ubuntu**: build lmbench, `lat_mem_rd -N 5 -t 512 128 > lmbench_raw.txt`,
`python crosscheck_lmbench.py lmbench_raw.txt -o data/intel_i5_13450hx/lmbench_curve.csv`,
`python compare_curves.py data/intel_i5_13450hx/wss_curve.csv data/intel_i5_13450hx/lmbench_curve.csv --labels "Auto-Echo,lmbench lat_mem_rd" --annotate -o data/crosscheck_intel.png`.
Auto-Echo's curve should overlay lmbench's within tolerance — external evidence the M1 run lacks.

## Verification checklist
- [ ] Build clean; `pytest` ~30 passed; label = `13th Gen Intel Core i5-13450HX (x86-64, Windows)`.
- [ ] L1 ≈ 1.6 ns / DRAM ≈ 143 ns (timer calibration matches the M1 anchors).
- [ ] Huge pages: provenance "2 MiB large pages"; ~20 MiB L3 present; **recall 3/3 = 100%** — OR clearly reported as *not achieved / blocked*, with labels left "measured".
- [ ] "measured → validated" relabel done **only if** recall 3/3 was actually achieved; otherwise every label left honest.
- [ ] Overlay refreshed; per-core GT + baseline intact; PDF rebuilt; committed.

Keep the macOS/ARM benchmark path untouched throughout.

─── END PROMPT ───
