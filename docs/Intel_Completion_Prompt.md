# Prompt for Claude Code — complete the remaining Intel i5-13450HX work

> **How to use.** On the Intel/Windows machine: `git pull`, open Claude Code in the
> repo root, and paste everything from `─── PROMPT ───` to `─── END PROMPT ───`.
>
> **Exactly two things are required** to secure the 80+ band: **Task A** (lmbench
> external validation — the supervisor identified this as the single item keeping
> the evaluation score out of the highest band) and **Task B** (the L3-contention
> test, which converts an asserted explanation into a measured one). Tasks C and D
> are optional polish; skip them if time is short.

---

─── PROMPT ───

You are working on **Auto-Echo** (MSc dissertation, QMUL): a tool that discovers a
CPU's cache hierarchy (L1/L2/L3/DRAM) from user space via a working-set-size (WSS)
pointer-chase latency sweep plus unsupervised level discovery, validated against OS
ground truth.

**This machine:** Intel Core i5-13450HX (Raptor Lake, 6 P + 4 E cores), Windows,
x86-64. Per-core caches L1d 48 KiB, L2 1.25 MiB, L3 20 MiB shared; 64-byte lines;
4 KiB base pages. The probe pins to CPU 0.

## Current state — do not redo any of this

The Intel machine is already **validated** and written up in `docs/Draft_Dissertation.md`:

- A 2 MiB huge-page run recovers the full L1/L2/L3/DRAM hierarchy: detected
  55.7 KiB / 1.2 MiB / 13.9 MiB, **3/3 documented caches matched, 100% recall and
  precision, F1 = 1.00**, mean absolute capacity error 12.8% over three sweeps.
- Under the default 4 KiB pages the 20 MiB L3 is TLB-masked (recall 2/3) — retained
  deliberately as the controlled comparison, not as a failure.
- Written up in **§6.3**, with **Table 6** (hierarchy), **Table 7** (model
  selection), **Table 8** (estimators), **Table 9** (penalty sensitivity),
  **Fig. 7** (memory mountain) and **Fig. 8** (model selection).
- The level-counting step now uses an **exact 1-D dynamic program**
  (`analysis._exact_1d_kmeans`), not Lloyd's K-Means. It is deterministic; there is
  no `n_init` or `random_state` in the productive path.

The dissertation is 36 pages / ~16,450 words, builds clean, has no placeholders.
**Your job is to close the gaps below, not to revise the existing write-up.**

**Priority.** Tasks **A** and **B** are required — they are the two items standing
between this dissertation and the 80+ band. Tasks **C** and **D** are optional
refinements. If you can only do one thing, do **A**.

## ⚠️ INTEGRITY RULE — read twice

**Never fabricate, simulate, interpolate or "reconstruct" a measurement.** Every
number that reaches the dissertation must come from a command that actually ran on
this hardware. If a task cannot be completed — a tool won't build, a privilege is
missing, a result contradicts expectation — **report exactly that and change no
claim in the document.** A recorded failure is worth more than an invented success,
and this project has already withdrawn one published claim (§6.4, the hybrid
capacity estimator) when new data refuted it. Do the same if it happens again.

Never relabel a status without the evidence for it. Do not "fix" a disappointing
result by adjusting parameters until it improves; if you vary something, report the
variation.

## Prerequisites — verify before starting

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pytest -q
```

- **Expect `35 passed, 0 skipped`.** On macOS one test skips (the per-core
  ground-truth query is Windows-only), so on *this* machine it must run. If you see
  a skip, the Windows ground-truth path is not being exercised — investigate before
  continuing.
- Confirm huge pages are still available (the "Lock pages in memory" right was
  granted previously; you need an **elevated** shell):
  ```powershell
  python -c "import autoecho.wss_probe_c as w; print(w.hugepages_available())"
  ```
  Must print `True`. If `False`, tasks B and D cannot run as specified — say so.

---

## TASK A — lmbench external cross-check **(REQUIRED — do this first)**

**Why it matters.** The evaluation's only oracle is OS-reported cache *capacity*,
which says nothing about whether the measured *latency curve* is correct. lmbench's
`lat_mem_rd` is the established prior-art implementation of the same pointer-chase
measurement. Overlaying it converts "self-consistent" into "externally validated".
This is the single largest remaining weakness in the dissertation.

**The converter is already written and tested** (`crosscheck_lmbench.py`, 5 tests in
`tests/test_crosscheck_lmbench.py`). You do not need to write it — you need to
produce real lmbench output and overlay it.

### Steps

1. In **WSL2 Ubuntu**, build lmbench and run the sweep:
   ```bash
   sudo apt-get update && sudo apt-get install -y build-essential
   git clone https://github.com/intel/lmbench.git && cd lmbench
   make -C src lat_mem_rd
   ./src/lat_mem_rd -N 5 -t 512 128 > ~/lmbench_raw.txt
   ```
   `-t 512` sets a 512 MiB maximum to match the Auto-Echo sweep; `128` is the
   stride in bytes. If the build fails, try `make -C src build` or report the error
   verbatim — lmbench is a 1996 codebase and its build is fragile.

2. Copy `lmbench_raw.txt` to the repo and convert:
   ```powershell
   python crosscheck_lmbench.py lmbench_raw.txt -o data/intel_i5_13450hx/lmbench_curve.csv
   ```

3. Overlay against Auto-Echo's huge-page curve:
   ```powershell
   python compare_curves.py data/intel_i5_13450hx/wss_curve.csv `
       data/intel_i5_13450hx/lmbench_curve.csv `
       --labels "Auto-Echo,lmbench lat_mem_rd" --annotate `
       --output data/crosscheck_intel.png
   ```

### What to report, and how to write it up

Compare the two curves **quantitatively**, not just visually. For each of the four
plateau regions (L1 / L2 / L3 / DRAM), report Auto-Echo's median latency, lmbench's
median over the same working-set range, and the ratio. Then:

- **If they agree within ~10–20% per plateau:** add a new subsection at the end of
  §6.3, "External cross-check against lmbench", with a comparison table and the
  overlay figure (it becomes **Fig. 11**). Update the §6.5 threats bullet on
  validation metrics, which currently lists the lmbench cross-check as a
  *remaining planned check* — it is no longer remaining. Also update §7, which
  lists it as future work.
- **If they disagree materially:** that is a finding, not a failure. Report it in
  the same place, state the magnitude and where in the curve it occurs, and
  consider the likely causes (lmbench uses a different stride and a different
  timing/amortisation scheme; WSL2 adds a virtualisation layer that the native
  Windows probe does not have). **Do not tune anything to make them agree.**

**Note the confound honestly either way:** Auto-Echo ran natively on Windows with
2 MiB pages; lmbench runs under WSL2 on 4 KiB pages. A deep-region difference may be
the page size rather than the measurement. Say so.

---

## TASK B — test the shared-L3 contention hypothesis **(REQUIRED)**

**Why it matters.** §6.3 reports the L3 as 13.9 MiB against a documented 20 MiB
(−30.4%) and attributes the shortfall to the pointer chase sharing the L3 with the
rest of the machine, reaching a contended knee early. **That explanation is
currently asserted, not tested** — a reviewer will notice.

### Steps

Run two three-sweep huge-page runs that differ only in background load:

```powershell
# Quiesced: close browsers/IDEs/sync clients, wait for CPU to settle below ~2%
python -m autoecho --method wss --max-mb 512 --runs 3 --huge-pages `
    --output-dir data/intel_l3_quiesced

# Loaded: saturate the other cores while the probe runs pinned to CPU 0
# (in a second shell, start N-1 spinning workers, then run the sweep)
python -m autoecho --method wss --max-mb 512 --runs 3 --huge-pages `
    --output-dir data/intel_l3_loaded
```

### Choosing the background load

The load must actually **evict lines from the shared L3**, or the test is
inconclusive by construction. Options, best first:

1. **Memory-streaming workers (recommended).** Several processes each looping over
   a buffer comfortably larger than 20 MiB. This is the load that most directly
   contends for L3 capacity, and it is trivially reproducible — you can state the
   buffer size and worker count in the dissertation, which matters because an
   examiner must be able to repeat it. A short Python or C script is sufficient;
   pin the workers away from CPU 0 so they contend for cache rather than for the
   probe's own core.
2. **A stress tool** (`stress-ng --vm N --vm-bytes 512M`, or similar). Reproducible
   and easy to describe.
3. **Playing a 4K video.** Convenient and realistic, but **weaker evidence** — much
   of the decode work happens on the GPU/media engine rather than in the CPU's L3,
   the memory traffic varies with scene content, and "a 4K video was playing" is
   not a specification anyone can reproduce. If you use it, use it *in addition to*
   option 1, not instead of it.

Whichever you choose, **describe it precisely** in the write-up — worker count,
buffer size, and how you confirmed the load was actually running. Also record the
CPU utilisation in each condition so the two sweeps are characterised, not merely
labelled "quiet" and "busy".

### What to report

The **detected L3 capacity** in each condition, plus its median latency.

- If the quiesced L3 detection moves **upward** toward 20 MiB and the loaded one
  moves down, the contention explanation is supported: quantify it and rewrite the
  §6.3 sentence from an assertion into a measured claim, citing both numbers.
- If the detected L3 is **unchanged** across conditions, the contention explanation
  is **wrong** and must be corrected in §6.3, §6.4 (the capacity-estimator
  discussion attributes the shared-cache under-read to the same cause) and §8.
  Alternative explanations to consider and state: the plateau-edge estimator's
  behaviour on a soft knee; L3 slice hashing meaning a single core cannot address
  the full capacity; inclusive/non-inclusive cache policy on this SKU.

Either outcome is publishable. Report what you find.

---

## TASK C — capacity confidence intervals *(optional)*

§6.5 notes that the standard deviation is reported for level *counts* but not for
*capacities*, and §7 lists confidence intervals as future work. With more sweeps
this becomes reportable.

```powershell
python -m autoecho --method wss --max-mb 512 --runs 10 --huge-pages `
    --output-dir data/intel_ci
```

Then, from `data/intel_ci/wss_curves_all.csv`, compute per-level detected capacity
for each sweep and report **median with min–max** (10 sweeps is too few for a
parametric interval — do not quote a standard error as if it were one). Add the
spread to **Table 6** as a new column, or as a footnote beneath it, and update the
§6.5 bullet and the §7 future-work item accordingly.

---

## TASK D — real measured density rows for Table 10 *(optional)*

**Table 10** (sampling-density robustness, §6.4) currently has *measured* rows for
the Apple M1 at 5/10/20 points per octave, but the Intel rows are **subsampled**
from the existing curve at 2.5/5/10 — because the machine was not to hand. The
table says so explicitly and notes that densities above the source grid need a
fresh sweep. You can now provide them.

```powershell
python sampling_density_sweep.py measure --densities 5 10 20 --max-mb 512 `
    --huge-pages --save data/density_intel
```

The `--huge-pages` flag **aborts rather than falling back** to 4 KiB pages, so if it
runs at all the provenance is genuine. Replace the three subsampled Intel rows in
Table 10 with the measured ones, keep the caption's distinction between measured and
subsampled rows accurate, and confirm the selected count is still **4** at every
density. If it is *not*, that is a significant negative result about the Silhouette
criterion — report it prominently rather than burying it.

---

## Finishing up

1. `pytest -q` — must still be `35 passed, 0 skipped`.
2. Verify no markdown table has a header/separator column-count mismatch. Pandoc
   silently **drops** the extra column, and this has already caused five tables to
   lose their last column in a previous build:
   ```powershell
   python -c "import re;L=open('docs/Draft_Dissertation.md',encoding='utf-8').read().split('\n');[print('MISMATCH line',i) for i,l in enumerate(L) if re.match(r'^\|\s*:?-{2,}',l.strip()) and len(l.strip().strip('|').split('|'))!=len(L[i-1].strip().strip('|').split('|'))]"
   ```
   No output means all tables are consistent.
3. Rebuild the PDF and confirm the build emits **no** warnings (a "Missing
   character" warning means a glyph is being silently dropped from the output):
   ```powershell
   cd docs
   pandoc Draft_Dissertation.md -o ../Draft_Dissertation.pdf --pdf-engine=xelatex `
       -V geometry:margin=1in -V fontsize=11pt -V colorlinks=true `
       -V linkcolor=blue --toc --toc-depth=3
   ```
4. If you added Fig. 11, check that figure and table numbering is still contiguous
   and that every `Table N` / `Fig. N` / `§x.y` reference resolves.
5. Update `TODO.md` to reflect what you actually completed.
6. Commit with a message stating which tasks succeeded and which did not.

## Report back with

- `pytest` result and the `hugepages_available()` value.
- **Task A:** the per-plateau Auto-Echo vs lmbench comparison, the agreement
  verdict, and whether lmbench built at all.
- **Task B:** detected L3 capacity quiesced vs loaded, and whether the contention
  explanation survived.
- **Task C:** per-level capacity spread over 10 sweeps.
- **Task D:** selected `k` at 5, 10 and 20 points per octave under huge pages.
- Anything you could not do, and why. **Do not paper over a gap.**

─── END PROMPT ───

---

## Notes for the author (not part of the prompt)

- **A and B are the whole job.** The supervisor review put the dissertation at
  79/100 and named the missing external validation as the specific reason it is not
  in the 80+ band. B removes the last *asserted* (as opposed to measured) claim in
  the Intel chapter. C and D are polish and can be dropped without cost.
- **On "proving" the contention hypothesis.** If the knee moves between the two
  sweeps, the hypothesis is supported — but the write-up should say *supported by a
  two-condition comparison on one machine*, not *proven*. And if the knee does
  **not** move, that is not a wasted afternoon: it means the explanation currently
  in §6.3, §6.4 and §8 is wrong and must be replaced. The prompt instructs Claude to
  handle both outcomes; make sure it actually does, rather than quietly reporting
  only the flattering one.
- lmbench on WSL2 measures a *virtualised* 4 KiB-page environment, so a perfect
  overlay with a native 2 MiB-page run is not expected in the deep region. The
  inner hierarchy (L1/L2) is the part that should agree closely, and it is the part
  the comparison is really testing.
- If time is short, do A and D — D is a single command and upgrades an existing
  table from partly-subsampled to fully measured.
