# Auto-Echo: CPU Memory Discovery

**Welcome to Auto-Echo!** If you're new here, don't worry—this project might sound highly technical, but it's designed to be completely automatic and easy to run.

In simple terms, Auto-Echo is a tool that discovers the hidden architecture of your computer's brain (the CPU). It figures out exactly how much fast memory (L1, L2, L3 caches) your CPU has, entirely from scratch, without asking the operating system for help.

## 📖 For Novices: What is this doing?

Imagine your computer's memory is like a library:
1. **L1 Cache (The Desk):** Tiny, but instantly accessible.
2. **L2/L3 Caches (The Nearby Bookshelves):** Larger, but takes a few steps to reach.
3. **DRAM / RAM (The Archives):** Huge, but takes a long time to fetch a book.

Normally, software asks the librarian (the Operating System) how big these shelves are. **Auto-Echo doesn't ask the librarian.** Instead, it runs an experiment: it starts reading small piles of books, then bigger and bigger piles, and measures *exactly how long* it takes. When it notices a sudden slow-down, it knows it just overflowed one of the shelves!

It uses Machine Learning (Clustering and Change-point detection) to automatically draw a map of your CPU's memory shelves based on these slow-downs.

---

## 🚀 Quickstart: Running Auto-Echo

To run this project, you need Python installed, and you need to compile a tiny piece of C code so the timing is ultra-precise.

### Step 1: Install Prerequisites
Depending on your OS, you need a C compiler:
- **macOS:** Open terminal and run `xcode-select --install`
- **Ubuntu/Linux:** Run `sudo apt-get install -y build-essential python3-dev`
- **Windows:** Install "Desktop development with C++" (MSVC Build Tools)

### Step 2: Build and Run
Open your terminal in the project folder and run these commands:

```bash
# 1. Create a clean Python environment
python3 -m venv .venv

# 2. Activate it 
# (On Windows use: .\.venv\Scripts\Activate.ps1)
source .venv/bin/activate

# 3. Build the tool 
pip install -e .

# 4. Run the experiment! (about 3 minutes for a 256 MiB sweep)
python -m autoecho --method wss --max-mb 256 --output-dir data/my_run
```

> **Note on `--output-dir`.** Write your own run to a *new* directory, as above.
> `data/` itself holds the committed Apple M1 sweep that the dissertation's §5.2
> tables are computed from, and `data/intel_*/` the Intel sweeps; pointing
> `--output-dir` at one of those overwrites the published evidence with a fresh
> measurement of *your* machine. Re-measuring the M1 here, for instance, moves the
> detected L2 boundary from the reported 13.9 MiB to 9.8 MiB, because a live
> machine's deep-cache region varies between runs (§5.3.2 quantifies exactly this
> effect). The dashboard reads `data/` by default — see `frontend/README.md` to
> point it at your own directory.

### Step 3: View the Dashboard (Highly Recommended)
We have a beautiful visual dashboard to show you the results! Once you've generated data in Step 2, open a new terminal window and run this to view it:

```bash
cd frontend
npm install
npm run dev
```
Then open `http://localhost:5173` in your browser to see your CPU's memory map!

---

## 🔬 For Advanced Users & Examiners

### What you get from the CLI
Running the pipeline writes to the `data/` output directory:
- `validation_report.md` — discovered levels, estimator comparison, ground-truth accuracy.
- `memory_mountain.png` — latency-vs-working-set curve with detected cache bands.
- `model_selection.png` — Elbow vs Silhouette model selection.
- `wss_curve.csv` — the raw experimental data.

### Useful Options
| Flag | Meaning |
|---|---|
| `--max-mb N` | Largest working-set size (raise to ≥512 for large-L3/DRAM machines) |
| `--runs N` | Independent sweeps for stability/error-bar evaluation |
| `--repeats N` | Repeats per size (minimum is kept) |
| `--hops N` | Minimum pointer-chase hops per timing window (default 2^20) |
| `--penalty F` | Change-point penalty **override**; omit for automatic level selection |
| `--method samples` | The documented naive baseline (retained to reproduce its failure) |

### Repository layout
```text
src/autoecho/
  wss/wss_probe.c, wss/__init__.py   native WSS pointer-chase probe + wrapper
  analysis.py                        change-point + clustering level discovery
  validation.py                      ground-truth comparison (sysctl / sysfs / WMI)
  evaluation.py                      comparative evaluation across sweeps
  report.py                          plots + Markdown report
  probe/, preprocessing.py, clustering.py   legacy sample-based baseline
scripts/                             One-off experiments and dissertation cross-checks
docs/                                literature review, methodology, dissertation, guides
frontend/                            React/Vite dashboard for visualizing results
```

### Troubleshooting
| Symptom | Fix |
|---|---|
| `No module named 'autoecho'` | Run `pip install -e .` from the project root. |
| `No module named 'autoecho.wss_probe_c'` | The C extension isn't built — run `pip install -e .`. |
| Import fails after copying folder | Delete any stale `*.so`/`*.pyd` and rebuild with `pip install -e .` |

---
*MSc Advanced Computer Science project (QMUL), referencing Klimis et al., "Shouting at Memory: Where Did My Write Go?" (ECOOP 2025).*
