# Prompt for Claude Code — Intel i5-13450HX (Windows) machine

> **How to use:** on the Intel machine, `git pull`, open Claude Code in the repo root,
> and paste everything from the `─── PROMPT ───` line down. It is written to be handed
> to the AI verbatim. Tasks are ordered by value; do them in order and **stop to report
> if a hardware/privilege blocker appears — never fabricate a measurement.**

---

─── PROMPT ───

You are working on **Auto-Echo**, an MSc dissertation project (QMUL) that discovers a
CPU's cache hierarchy (L1/L2/L3/DRAM) from user space using a working-set-size (WSS)
pointer-chase latency sweep plus unsupervised level discovery, validated against
OS-reported ground truth. The repo is set up. Key files: probe
`src/autoecho/wss/wss_probe.c` (+ wrapper `src/autoecho/wss/__init__.py`), analysis
`src/autoecho/analysis.py`, ground-truth `src/autoecho/validation.py`, CLI
`python -m autoecho`.

**This machine:** Intel Core i5-13450HX (Raptor Lake, 6 P-cores + 4 E-cores), Windows,
x86-64. Documented **per-core** caches: L1d **48 KiB**, L2 **~1.25–2 MiB/core**, L3
**~20 MiB shared**, 64-byte lines. The probe pins to CPU 0 (a P-core).

**Rules you must respect:**
- The macOS/Apple-M1 path is validated and must NOT regress. Every Windows/x86-specific
  change must be **gated** (Windows-only branch, or behind a flag/env var).
- After any code change, run `pytest -q` and keep it green (**29 passed** once the C
  extension is built).
- Two open issues this machine exists to fix: (a) with default 4 KiB pages, page-walk
  latency saturates the curve at ~143 ns by ~4 MiB and **masks the 20 MiB L3**; (b) the
  Windows ground-truth path reads **per-socket aggregate** cache sizes
  (`Win32_CacheMemory`), so validation reads **0%** despite correct L1/L2 knees.
- The pipeline already reports **recall + precision** and supports
  `--capacity-method {edge,onset,hybrid}` (default `edge`). You do not need to change
  the analysis; you are supplying better measurements and better ground truth.

---

## Task 0 — Build, test, verify label

1. `python -m venv .venv`, activate, `pip install -e .` (needs **MSVC C++ Build Tools**).
2. `pytest -q` → expect **29 passed**.
3. `python -m autoecho --method wss --max-mb 128 --runs 1 --output-dir data/_scratch`
   and confirm the report's `**Machine:**` line reads **`Intel Core i5-13450HX (x86-64, Windows)`**.
   If it shows the raw `Intel64 Family 6 Model 183 …` string instead, the PowerShell-CIM
   brand query failed — report the exact error before continuing.

Report the pytest count and the machine label, then proceed.

---

## Task 1 — Unmask the L3 with huge (large) pages  ★ highest value

**Goal:** allocate the pointer-chase buffer with **2 MiB large pages** so page-walk cost
is suppressed and the ~20 MiB L3 becomes a visible 4th band.

**Implement (gated, default-off):** in `wss_probe.c`, add a large-page allocation path
used only when requested — env var `AUTOECHO_HUGEPAGES=1` **or** a `--huge-pages` CLI
flag threaded `__main__.py` → `sweep()` → `measure_wss`. Keep `aligned_alloc_portable`
as default. Windows large-page allocation:
1. Enable **`SeLockMemoryPrivilege`**: `OpenProcessToken` + `LookupPrivilegeValue(NULL, SE_LOCK_MEMORY_NAME, …)` + `AdjustTokenPrivileges`.
2. Round size up to a multiple of `GetLargePageMinimum()` (≈2 MiB).
3. `VirtualAlloc(NULL, rounded, MEM_RESERVE|MEM_COMMIT|MEM_LARGE_PAGES, PAGE_READWRITE)`; free with `VirtualFree(p, 0, MEM_RELEASE)`.
4. **Graceful fallback:** on `ERROR_PRIVILEGE_NOT_HELD` (1314) or if the privilege isn't
   assigned, fall back to the normal allocation and print a one-line warning. Never crash.

**Privilege setup (one-time, needs a Windows admin):** `secpol.msc` → *Local Policies* →
*User Rights Assignment* → **Lock pages in memory** → add this user → **log out/in**; run
the process **elevated**. If you cannot get admin rights, say so, skip the run, and
record Task 1 as *blocked on privilege* — do not fake it.

**Run & compare:** `set AUTOECHO_HUGEPAGES=1` (or `--huge-pages`), then
`python -m autoecho --method wss --max-mb 512 --runs 3 --output-dir data/intel_hugepage`.
Compare to the 4 KiB-page run: does a **4th plateau near ~20 MiB** now appear? Report the
detected levels + capacities for both. Success = L1/L2/**L3**/DRAM with L3 ≈ 20 MiB.

---

## Task 2 — Per-core Windows ground truth

Replace the aggregate cache sizes with true per-core sizes. In
`validation.py`, `get_ground_truth()` Windows branch: read caches via
**`GetLogicalProcessorInformationEx(RelationCache, …)`** (kernel32) — cleanest via
**ctypes** (no rebuild). Iterate `CACHE_RELATIONSHIP` records; keep `CacheData`/
`CacheUnified` (drop `CacheInstruction`); use `Level` + `CacheSize` (these are per-cache,
not summed) for the caches on CPU 0. Keep the old `Win32_CacheMemory` path as a labelled
fallback. **Sanity:** expect L1 **49152**, L2 **≈1.25–2 MiB**, L3 **≈20–24 MiB**.
Validation recall should jump from 0% to matching L1/L2 (and L3 if Task 1 unmasked it).
Add a Windows-guarded test if practical; keep `pytest` green.

---

## Task 3 — Regenerate the committed Intel artifacts + the cross-machine overlay

1. `python -m autoecho --method wss --max-mb 512 --runs 3 --output-dir data/intel_i5_13450hx`
   (add `--huge-pages` if granted). Confirm the report shows the clean label, **Recall +
   Precision**, and real per-core accuracy.
2. Optionally report `--capacity-method hybrid` vs `edge` for the Intel caps (hybrid
   falls back to edge on sloped plateaus, so expect them equal here).
3. **Regenerate the cross-machine overlay** (the committed M1 curve `data/wss_curve.csv`
   is in the repo):
   `python compare_curves.py data/wss_curve.csv data/intel_i5_13450hx/wss_curve.csv --labels "Apple M1 (ARM64),Intel i5-13450HX (x86-64)" --annotate --output data/compare_mountain.png`
   — this refreshes Fig. 9 with the new (huge-page) Intel curve.

---

## Task 4 — `clflush` naive baseline (x86-only, fills a TBD cell)

`python -m autoecho --method samples --mode 1 --samples 50000 --output-dir data/intel_baseline`.
Record the result — it is *expected to fail* to resolve the hierarchy (write-before-read +
timer-tick quantisation); that failure is the point, and fills the "Naive baseline (with
`clflush`)" **TBD** cell in the §6.5 comparison table. (Cross-check reproducible via
`python -m autoecho --method lof-check`.)

---

## Task 4b — lmbench external cross-check (best done here / on WSL Linux)

lmbench does **not** build on ARM macOS, so this external validation belongs on x86. On
this machine (ideally via **WSL2 Ubuntu**): install/build lmbench (`sudo apt install
lmbench` or build from source), then
`lat_mem_rd -N 5 -t 512 128 > lmbench_raw.txt`, convert and overlay:
`python crosscheck_lmbench.py lmbench_raw.txt -o data/intel_i5_13450hx/lmbench_curve.csv`
then
`python compare_curves.py data/intel_i5_13450hx/wss_curve.csv data/intel_i5_13450hx/lmbench_curve.csv --labels "Auto-Echo,lmbench lat_mem_rd" --annotate -o data/crosscheck_intel.png`.
This validates the probe against trusted prior art on identical hardware — a strong
evaluation figure. If lmbench can't be built, record that and move on.

---

## Task 5 — Update the dissertation + rebuild PDF

Edit `docs/Draft_Dissertation.md`:
- **§6.3 (Intel)** — update the hierarchy table and text: if Task 1 unmasked the L3,
  replace "L3 masked by TLB" with the measured L3; update accuracy from the per-core
  ground truth (Task 2); add precision. If Task 4b ran, add the lmbench cross-check figure.
- **§6.5** comparison table — update the Intel column (levels resolved, count stability,
  caches matched, the naive-baseline cell).
- Rebuild the PDF. On Windows use `-V mainfont="Cambria"` (covers `→`/`≈`); if a glyph is
  still missing, use the build-copy trick — replace `→`/`≈` with `$\rightarrow$`/`$\approx$`
  in a temp copy first:
  `pandoc <tmp>.md -o Draft_Dissertation.pdf --pdf-engine=xelatex --toc --toc-depth=3 --resource-path=docs -V geometry:margin=1in -V mainfont="Cambria"`.

---

## Verification checklist (report all)

- [ ] `pytest` green (29+ passed) after every code change.
- [ ] Machine label = `Intel Core i5-13450HX (x86-64, Windows)`.
- [ ] Huge-page run: L3 (~20 MiB) plateau present? (yes / no / blocked-on-privilege — with the exact reason).
- [ ] Per-core ground truth returns L1≈48 KiB, L2≈1.25–2 MiB, L3≈20–24 MiB.
- [ ] Regenerated Intel report shows real Recall **and** Precision (not 0%).
- [ ] Cross-machine overlay (Fig. 9) refreshed with the new Intel curve.
- [ ] clflush baseline recorded; lmbench cross-check done (or recorded as blocked).
- [ ] §6.3 / §6.5 updated; PDF rebuilt.

Keep all Windows/x86-specific code paths gated so the macOS/ARM path is untouched.

─── END PROMPT ───
