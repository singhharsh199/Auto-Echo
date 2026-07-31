# Auto-Echo

**Discover your CPU's cache hierarchy from user space — no privileges, no vendor tables, no prior knowledge of the machine.**

Auto-Echo measures how long your processor takes to read memory at hundreds of
different working-set sizes, then *infers the cache hierarchy from the timing
alone*: how many levels of cache exist, and how large each one is. It asks the
operating system nothing. It needs no administrator rights, no kernel module, no
performance counters, and no architecture-specific instructions.

The inference is unsupervised. Nothing about the hierarchy is hard-coded:

| Stage | Method | What it answers |
| :--- | :--- | :--- |
| **Count** | Exact 1-D *k*-means by dynamic programming (`Ckmeans.1d.dp`, Wang & Song 2011) + Silhouette | *How many* memory levels does this machine have? |
| **Localise** | Change-point detection (`Dynp`), constrained to that count | *Where* is each cache's capacity boundary? |
| **Validate** | Hungarian matching against OS-reported ground truth | Was it right? |

Because the counting step is solved by dynamic programming rather than Lloyd's
heuristic, the partition it returns is the **global optimum** for every candidate
level count — deterministic, with no seeding, no restarts, and no random state.

> [!NOTE]
> This repository accompanies an MSc dissertation (Queen Mary University of
> London). It reports validated results on two machines: an **Apple M1**
> (3 levels, 2/2 documented caches recovered) and an **Intel Core i5-13450HX**
> (4 levels, 3/3 recovered under a 2 MiB huge-page allocation). See
> [`docs/Draft_Dissertation.pdf`](docs/Draft_Dissertation.pdf).

---

## 📚 What is this actually doing?

Think of your computer's memory as a library.

| Tier | In the library | On your CPU | Size | Speed |
| :--- | :--- | :--- | :--- | :--- |
| 1 | The **desk** in front of you | L1 cache | Tiny (tens of KB) | Instant (~1 ns) |
| 2 | The **shelf** beside the desk | L2 cache | Small (~1 MB) | A moment (~5 ns) |
| 3 | The **room** you're sitting in | L3 cache | Bigger (~20 MB) | A short walk (~20 ns) |
| 4 | The **off-site archive** | Main memory (DRAM) | Huge (many GB) | A long trip (~120 ns) |

Normally, a program that wants to know the size of each tier **asks the
librarian** — the operating system, or a vendor's own tool. Auto-Echo doesn't ask.
It runs an experiment instead.

It starts by working with a handful of books and times how fast it can fetch them.
Then a few more. Then more again, doubling and doubling. For a while nothing
changes — everything still fits on the desk, so every fetch is instant. Then, at
one particular pile size, fetches suddenly get slower. **That is the moment the
desk overflowed**, and the size of the pile at that moment *is* the size of the
desk. Keep going and the same thing happens at the shelf, then the room.

The result is a staircase: flat stretches where everything fits, and sharp steps
where it stops fitting. Auto-Echo's job is to find the steps automatically — which
is where the machine learning comes in. It has to decide **how many steps there
are** (a clustering problem) and **exactly where each one falls** (a change-point
problem), on noisy real-world timings, without being told the answer in advance.

One wrinkle makes this harder than it sounds. A modern CPU tries to *predict* what
you'll read next and fetch it early, which would smooth the staircase away. So
Auto-Echo reads in a random order where each book tells you which book to fetch
next — the CPU can't run ahead, because it doesn't know where you're going until
it arrives.

---

## 🚀 Quickstart

### Prerequisites

**For the pipeline** (the probe, the inference stage, the tests) — Python
**3.11 or newer** and a C compiler, because the timing probe is a C extension:

| Platform | Command |
| :--- | :--- |
| **macOS** | `xcode-select --install` |
| **Debian / Ubuntu** | `sudo apt-get install -y build-essential python3-dev` |
| **Windows** | Install *Desktop development with C++* (Visual Studio Build Tools) |

**For the dashboard only** — **Node.js `20.19+` or `22.12+`** (Vite 8 and oxlint
both require it; check with `node --version`). Nothing in the Python pipeline needs
Node, so skip this if you only want to run the probe.

| Platform | Command |
| :--- | :--- |
| **macOS** | `brew install node` |
| **Debian / Ubuntu** | `curl -fsSL https://deb.nodesource.com/setup_22.x \| sudo -E bash - && sudo apt-get install -y nodejs` |
| **Windows** | Download the LTS installer from [nodejs.org](https://nodejs.org) |
| **Any platform** | Or use [nvm](https://github.com/nvm-sh/nvm): `nvm install 22 && nvm use 22` |

### Install

```bash
# 1. Create an isolated environment
python3 -m venv .venv

# 2. Activate it
source .venv/bin/activate
#    Windows PowerShell:  .\.venv\Scripts\Activate.ps1

# 3. Install the package and compile the C extensions


pip install -e .
```

That last step builds two native modules (`autoecho.wss_probe_c` and
`autoecho.probe_c`). If it succeeds, you're ready.

### Run

```bash
python -m autoecho --method wss --max-mb 256 --output-dir data/my_run
```

Takes roughly **3 minutes** for a 256 MiB sweep. You'll see the pipeline's five
stages, ending with a validation summary like:

```text
[4/5] Validating against hardware ground truth...
      recall 100.0% (2/2 caches found), precision 100.0% (0 false positive(s));
      mean |capacity error| 20.5%
```

> [!WARNING]
> **Always write to a new directory, such as `data/my_run`.**
> `data/` itself holds the committed Apple M1 sweep that the dissertation's §5.2
> tables are computed from, and `data/intel_*/` holds the Intel sweeps. Pointing
> `--output-dir` at one of those **overwrites the published experimental evidence**
> with a fresh measurement of *your* machine — and the two will not agree.
> Re-measuring the M1 here moves the detected L2 boundary from the reported
> 13.9 MiB to 9.8 MiB, because a live machine's deep-cache region genuinely varies
> between runs (§5.3.2 quantifies exactly this effect).

### What you get

Four files land in your output directory:

| File | Contents |
| :--- | :--- |
| `validation_report.md` | Discovered hierarchy, estimator agreement, accuracy vs ground truth |
| `memory_mountain.png` | The latency staircase, with detected cache bands shaded |
| `model_selection.png` | Elbow vs Silhouette — how the level count was chosen |
| `wss_curve.csv` | Raw measurements, one row per working-set size |

---

## 📊 The Dashboard

An interactive React dashboard renders the whole result set — the latency curve
with cache bands, per-level capacity cards, ground-truth validation, and estimator
agreement.

```bash
cd frontend
npm install
npm run dev
```

Open **<http://localhost:5173>**.

> [!TIP]
> The dashboard works **immediately after `npm install`** — it ships with the two
> validated machines from the dissertation, so you can explore real results
> without running the Python pipeline at all. It's the fastest way to see what
> this project produces.

To add **your own** run alongside them, point it at the directory you just created:

```bash
AUTOECHO_RUN=my_run npm run dev
```

A third machine ("This machine") appears in the switcher. On Windows PowerShell
use `$env:AUTOECHO_RUN="my_run"; npm run dev`.

Features: switch between machines, overlay all of them on one axis, toggle cache
bands / boundaries / the min–max spread, and overlay individual sweeps to see
run-to-run variability. The view is deep-linkable (`?machine=intel&compare=1`).

---

## 🗂 Repository layout

```text
.
├── src/autoecho/                  the package
│   ├── __main__.py                CLI entry point (`python -m autoecho`)
│   ├── wss/
│   │   ├── wss_probe.c            native pointer-chase probe (C extension)
│   │   └── __init__.py            Python wrapper: sweep scheduling, tick→ns
│   ├── analysis.py                level discovery: exact 1-D k-means + change-point
│   ├── validation.py              ground truth (sysctl / sysfs / Win32) + matching
│   ├── evaluation.py              estimator comparison across independent sweeps
│   ├── report.py                  Markdown report and figures
│   ├── generate_diagrams.py       conceptual diagrams for the dissertation
│   ├── platform_timing.py         per-platform timer constants
│   └── probe/, preprocessing.py, clustering.py
│                                  legacy sample-based baseline (documented
│                                  negative result — see dissertation §4)
│
├── scripts/                       one-off analyses behind specific results
│   ├── verify_kmeans_optimality.py   audits exact DP vs Lloyd's heuristic (§3.2.1)
│   ├── crosscheck_plateaus.py        Auto-Echo vs lmbench lat_mem_rd (§5.3.1)
│   ├── crosscheck_lmbench.py         converts lat_mem_rd output to our CSV format
│   ├── capacity_ci.py                per-level capacity spread over N sweeps (§5.3)
│   ├── l3_load.py                    shared-L3 contention generator (§5.3.2)
│   ├── l3_contention_report.py       quiesced-vs-loaded comparison (§5.3.2)
│   ├── sampling_density_sweep.py     is the level count grid-dependent? (§5.4)
│   ├── compare_curves.py             overlay curves from several machines
│   └── build_pdf.sh                  rebuild the dissertation PDF
│
├── frontend/                      React + Vite dashboard (vanilla CSS, Recharts)
│   ├── scripts/build-data.mjs     bundles data/ outputs into typed JSON
│   └── src/                       components, design system, formatting helpers
│
├── docs/                          dissertation + supporting write-ups
│   ├── Draft_Dissertation.md      the dissertation source
│   ├── Draft_Dissertation.pdf     built artefact (scripts/build_pdf.sh)
│   └── pandoc-header.tex          LaTeX header used by that build
│
├── data/                          committed experimental evidence — do not overwrite
│   ├── wss_curve.csv, …           Apple M1 (dissertation §5.2)
│   ├── intel_i5_13450hx/          Intel, 3-sweep run + lmbench cross-check
│   ├── intel_ci/                  Intel, 10-sweep run (§5.3 headline)
│   ├── intel_l3_{loaded,quiesced}/ contention experiment (§5.3.2)
│   └── density{,_intel}/          sampling-density robustness (§5.4)
│
└── tests/                         pytest suite (36 tests)
```

---

## 🔬 For examiners and advanced users

### CLI reference

| Flag | Meaning |
| :--- | :--- |
| `--method {wss,samples,lof-check}` | `wss` is the delivered pipeline. `samples` reproduces the naive baseline whose failure motivates the design (§4); `lof-check` reproduces the evidence that the failure is structural, not filterable noise. |
| `--max-mb N` | Largest working-set size. Raise to ≥ 512 on machines with a large L3. |
| `--runs N` | Independent sweeps, for stability and error bars. |
| `--repeats N` | Repeats per size; the **minimum** is kept (standard lmbench practice). |
| `--hops N` | Pointer-chase hops per timing window (default 2²⁰). |
| `--huge-pages` | Allocate the buffer with 2 MiB large pages (Windows; needs *Lock pages in memory* + elevation). Decisive for seeing a large L3 — see below. |
| `--capacity-method {edge,onset,hybrid,midpoint}` | Capacity estimator. `edge` is the default and the only one used for reported results. |
| `--penalty F` | Manual change-point penalty **override**. Omit it — automatic model selection is the point of the project. |
| `--seed N` | RNG seed for the reproducible pointer-chase permutation. |

### Reproducing the dissertation's results

```bash
pytest                                    # 36 tests
python scripts/verify_kmeans_optimality.py "Apple M1=data/wss_curve.csv"
python scripts/crosscheck_plateaus.py \
    data/intel_i5_13450hx/wss_curve.csv \
    data/intel_i5_13450hx/lmbench_curve.csv
python scripts/capacity_ci.py data/intel_ci/wss_curves_all.csv --ground-truth 20
./scripts/build_pdf.sh                    # rebuild the PDF (needs pandoc + XeLaTeX)
```

**After a new multi-sweep run, regenerate the capacity sidecar**, or the dashboard
will quietly fall back to the aggregate-curve capacities:

```bash
python scripts/capacity_ci.py data/<run>/wss_curves_all.csv \
    --json data/<run>/capacity_spread.json
```

`capacity_spread.json` holds the **median of the per-sweep detections**, which is
what §5.3 reports. The aggregated `wss_curve.csv` is the *minimum* over sweeps at
each size — the right statistic for a latency, the wrong one for a boundary, since
the lower envelope drags a detected knee inward. On the ten-sweep Intel run that is
the difference between an L3 of 13.9 MiB (−30.4 %) and one of 19.7 MiB (−1.5 %).
`npm run prep` prints which of the two it used for each machine.

### Two results worth knowing before you run it

**Page size can hide a cache entirely.** On the Intel machine with default 4 KiB
pages, address-translation cost saturates the curve *before* the 20 MiB L3 is
reached — so the L3 is invisible and a TLB artefact appears in its place. Under
`--huge-pages` the same code recovers all four levels. If your machine has a large
L3 and you only see three levels, this is why.

**A shared cache measures as smaller than it is.** What the probe recovers of a
*shared* L3 is the portion actually available to the probing core. Under a
deliberate eight-core load the detected L3 falls from 19.7 MiB to 3.5 MiB. Close
other work before measuring.

### Troubleshooting

| Symptom | Fix |
| :--- | :--- |
| `No module named 'autoecho'` | Run `pip install -e .` from the repository root, with the venv active. |
| `No module named 'autoecho.wss_probe_c'` | The C extension didn't build. Check the compiler prerequisites above, then re-run `pip install -e .`. |
| Import fails after copying the folder | Delete stale `*.so` / `*.pyd` files and rebuild with `pip install -e .`. |
| Latencies look impossibly small (~0 ns) | The compiler elided the timed loop. `pytest tests/test_probe_sanity.py` guards against exactly this. |
| Only 3 levels on a machine with an L3 | Address translation is masking it — see `--huge-pages` above. |
| Dashboard shows no data | Run `npm install` first; `predev` regenerates the bundle automatically. |

---

## 📄 Citation and context

MSc Advanced Computer Science dissertation, Queen Mary University of London.
The project takes up an open direction identified in §7 of:

> V. Klimis, "Shouting at Memory: Where Did My Write Go?", *Proc. 39th European
> Conference on Object-Oriented Programming (ECOOP 2025)*, LIPIcs vol. 333,
> Art. 41. doi: [10.4230/LIPIcs.ECOOP.2025.41](https://doi.org/10.4230/LIPIcs.ECOOP.2025.41)

The measurement technique descends from McVoy & Staelin's `lat_mem_rd` (lmbench,
USENIX ATC 1996); the contribution is the unsupervised inference layer above it.
Full context, including the relationship to `hwloc`, Intel MLC and the
cache-side-channel literature, is in §2 of the dissertation.
