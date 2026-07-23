# Prompt for Claude Code — Intel i5-13450HX (Windows) machine

> **How to use this:** on the Intel machine, `git pull`, open Claude Code in the
> repo root, and paste everything from the `─── PROMPT ───` line down. It is
> written to be handed to the AI verbatim. Tasks are ordered by value; do them in
> order and stop to report if a hardware/privilege blocker appears.

---

─── PROMPT ───

You are working on **Auto-Echo**, an MSc dissertation project (QMUL) that discovers a
CPU's cache hierarchy (L1/L2/L3/DRAM) from user space using a working-set-size (WSS)
pointer-chase latency sweep plus unsupervised level discovery, validated against
OS-reported ground truth. The repo is already set up; the primary probe is
`src/autoecho/wss/wss_probe.c` (+ wrapper `src/autoecho/wss/__init__.py`), analysis is
`src/autoecho/analysis.py`, ground-truth read is `src/autoecho/validation.py`, and the
CLI is `python -m autoecho`.

**This machine:** Intel Core i5-13450HX (Raptor Lake, 6 P-cores + 4 E-cores), Windows,
x86-64. Documented **per-core** caches: L1d **48 KiB**, L2 **~1.25–2 MiB/core**, L3
**~20 MiB shared**, 64-byte lines. The probe pins to CPU 0 (a P-core) via
`SetThreadAffinityMask`.

**Context you must respect:**
- The macOS/Apple-M1 path is validated and must NOT regress. Any Windows/x86-specific
  change must be **gated** (Windows-only branch, or behind a flag/env var) so the
  default cross-platform behaviour is unchanged.
- Known open issue this machine exists to fix: with default 4 KiB pages, DTLB/page-walk
  latency saturates the curve at ~143 ns by ~4 MiB and **masks the 20 MiB L3**; and the
  Windows ground-truth path currently reads **per-socket aggregate** cache sizes
  (`Win32_CacheMemory`), so validation reads **0%** even though the L1/L2 knees are
  correct.
- After any code change, run `pytest` and keep it green (expect **27 passed** once the
  C extension is built).

---

## Task 0 — Build & baseline (do first)

1. Create/activate a venv and build the native extensions (needs the **MSVC C++ Build
   Tools**): `python -m venv .venv`, activate, then `pip install -e .`.
2. `pytest -q` → expect **27 passed** (the `test_probe_sanity` tests run once the
   extension is built).
3. Sanity-run the pipeline and **confirm the machine label**:
   `python -m autoecho --method wss --max-mb 128 --runs 1 --output-dir data/_scratch`
   The report's `**Machine:**` line must read **`Intel Core i5-13450HX (x86-64, Windows)`**
   (this verifies the PowerShell-CIM brand fix and the `AMD64`→`x86-64` normalisation in
   `get_machine_label`). If it instead shows the raw `Intel64 Family 6 Model 183 …`
   string, the PowerShell CIM call failed — report the exact error before continuing.

Report the pytest result and the machine label, then proceed.

---

## Task 1 — Unmask the L3 with huge (large) pages  ★ highest value

**Goal:** allocate the pointer-chase buffer with **2 MiB large pages** so page-walk cost
is suppressed and the ~20 MiB L3 plateau becomes visible as a 4th band.

**Implementation (gated, Windows-only default-off):**
- In `src/autoecho/wss/wss_probe.c`, add a large-page allocation path used only when
  requested (env var `AUTOECHO_HUGEPAGES=1`, **or** a new `use_hugepages` argument
  threaded from `sweep()` via a `--huge-pages` CLI flag in `src/autoecho/__main__.py`).
  Keep the existing `aligned_alloc_portable` as the default.
- Windows large-page allocation:
  1. Enable **`SeLockMemoryPrivilege`** on the process token via
     `OpenProcessToken` + `LookupPrivilegeValue(NULL, SE_LOCK_MEMORY_NAME, …)` +
     `AdjustTokenPrivileges`.
  2. Round the size up to a multiple of `GetLargePageMinimum()` (typically 2 MiB).
  3. `VirtualAlloc(NULL, rounded, MEM_RESERVE|MEM_COMMIT|MEM_LARGE_PAGES, PAGE_READWRITE)`.
  4. Free with `VirtualFree(p, 0, MEM_RELEASE)`.
- **Graceful fallback:** if `VirtualAlloc` fails with `ERROR_PRIVILEGE_NOT_HELD` (1314)
  or `AdjustTokenPrivileges` reports the privilege wasn't assigned, fall back to the
  normal aligned allocation and print a clear one-line warning so the run still
  completes. Do **not** crash.

**Privilege setup (needs a Windows admin, one-time):** the "Lock pages in memory" user
right must be granted — `secpol.msc` → *Local Policies* → *User Rights Assignment* →
**Lock pages in memory** → add this user → **log out and back in**. The process must
also run **elevated** (admin shell). If you cannot obtain admin rights, say so, skip the
run, and record that Task 1 is blocked on the privilege (do not fake a result).

**Run & compare:**
- `set AUTOECHO_HUGEPAGES=1` (or use `--huge-pages`), then
  `python -m autoecho --method wss --max-mb 512 --runs 3 --output-dir data/intel_hugepage`
  (512 MiB so the sweep reaches well past 20 MiB into DRAM).
- Compare against the 4 KiB-page run: does a **4th plateau near ~20 MiB** now appear with
  a distinct L3 latency step? Save both `memory_mountain.png`s and report the detected
  levels + capacities for each. Success = L1/L2/**L3**/DRAM (4 bands) with L3 ≈ 20 MiB.

---

## Task 2 — Per-core Windows ground truth

**Goal:** replace the per-socket **aggregate** cache sizes with true **per-core** sizes
so the validation metric is meaningful on Windows.

- In `src/autoecho/validation.py`, `get_ground_truth()` Windows branch: implement
  cache-size reading via **`GetLogicalProcessorInformationEx(RelationCache, …)`**
  (kernel32) — cleanest via **ctypes** (no rebuild). Iterate the
  `SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX` records; for each `CACHE_RELATIONSHIP` take
  `Level`, `Type` (keep `CacheData` and `CacheUnified`, drop `CacheInstruction`), and
  `CacheSize` — these are **per-cache** (per-core for L1/L2), not summed. Map to
  `{"L1": …, "L2": …, "L3": …}` in bytes, choosing the caches associated with CPU 0.
- Keep the old `Win32_CacheMemory` path only as a labelled fallback.
- **Sanity check:** expected per-core ground truth ≈ L1d **49152** (48 KiB), L2 **≈1.25–2 MiB**,
  L3 **≈20–24 MiB**. Validation recall should jump from 0% to matching L1 and L2 (and L3
  too if Task 1 unmasked it).

Add a Windows-guarded unit test if practical, and keep `pytest` green.

---

## Task 3 — Regenerate the committed Intel artifacts

Once Tasks 1–2 land:
`python -m autoecho --method wss --max-mb 512 --runs 3 --output-dir data/intel_i5_13450hx`
(add `--huge-pages` if the privilege was granted). Confirm the regenerated
`data/intel_i5_13450hx/validation_report.md` now shows: the clean machine label,
**Recall + Precision** (not just "accuracy"), and real per-core accuracy. Re-check the
figures carry the correct subtitle.

---

## Task 4 — `clflush` naive baseline (x86-only, fills a TBD cell)

x86 can flush a line from userspace (ARM cannot), so this machine can run the documented
naive baseline that the dissertation contrasts against:
`python -m autoecho --method samples --mode 1 --samples 50000 --output-dir data/intel_baseline`
Record its result — it is *expected to fail* to resolve the hierarchy (write-before-read
+ timer-tick quantisation); that failure is the point. This fills the "Naive baseline
(with `clflush`)" **TBD** cell in the §6.5 comparison table.

---

## Task 5 — Update the dissertation with the new numbers

Edit `docs/Draft_Dissertation.md`:
- **§6.3 (Intel)** — update the discovered-hierarchy table and text: if Task 1 unmasked
  the L3, change "L3 masked by TLB" to the measured L3; update the accuracy from the
  per-core ground truth (Task 2); add precision.
- **§6.5** comparison table — update the Intel column: levels resolved, count stability,
  caches matched, and the naive-baseline cell.
- Rebuild the PDF. On Windows, `pandoc … --pdf-engine=xelatex --toc --toc-depth=3
  --resource-path=docs -V mainfont="Cambria"` (Cambria covers the `→`/`≈` glyphs; if a
  glyph is still missing, use the repo's build-copy trick — replace `→`/`≈` with
  `$\rightarrow$`/`$\approx$` in a temp copy — see the prior build notes). Output to
  `Draft_Dissertation.pdf`.

---

## Verification checklist (report all)

- [ ] `pytest` green (27+ passed) after every code change.
- [ ] Machine label reads `Intel Core i5-13450HX (x86-64, Windows)`.
- [ ] Huge-page run: L3 (~20 MiB) plateau present? (yes/no/blocked-on-privilege — with the exact reason).
- [ ] Per-core ground truth returns L1≈48 KiB, L2≈1.25–2 MiB, L3≈20–24 MiB.
- [ ] Regenerated Intel report shows real Recall **and** Precision (not 0%).
- [ ] clflush baseline run recorded.
- [ ] §6.3 / §6.5 updated; PDF rebuilt.

**Do not fabricate any measurement.** If a task is blocked (no admin rights, privilege
not grantable, MSVC missing), stop, say exactly what blocked it, and move to the next
independent task. Keep all Windows/x86-specific code paths gated so the macOS/ARM path
is untouched.

─── END PROMPT ───
