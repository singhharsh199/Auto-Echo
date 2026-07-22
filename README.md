# Auto-Echo

**Automated discovery of the CPU memory hierarchy (L1/L2/L3/SLC/DRAM) from user
space**, with no privileges, no architecture-specific flush instructions, and no
prior knowledge of the machine. Auto-Echo runs a working-set-size pointer-chase
sweep and applies unsupervised change-point detection and clustering to locate
each cache's capacity, then validates itself against the OS-reported ground truth.

MSc Advanced Computer Science project (QMUL), referencing Klimis et al.,
*"Shouting at Memory: Where Did My Write Go?"* (ECOOP 2025).

---

## ⚠️ Quickstart — you MUST build before running

This project contains **native C extensions** that are *not* included in the
repository/zip (they are compiled per machine). Running the tool without
building first will fail with `No module named 'autoecho'` or
`No module named 'autoecho.wss_probe_c'`. To build and run:

```bash
# 1. (recommended) create an isolated environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1

# 2. build + install the package and its C extensions
pip install -e .

# 3. run the pipeline
python -m autoecho --method wss --max-mb 256 --output-dir data
```

`pip install -e .` both compiles the C extensions **and** puts the `autoecho`
package (which lives under `src/`) on the import path — do not skip it.

### Prerequisites (a C compiler + Python headers)
| Platform | Install |
|---|---|
| Debian/Ubuntu | `sudo apt-get install -y build-essential python3-dev` |
| Fedora/RHEL | `sudo dnf install -y gcc python3-devel` |
| macOS | Xcode Command Line Tools (`xcode-select --install`) |
| Windows | "Desktop development with C++" (MSVC Build Tools) |

Python **3.10+** is required. Dependencies (numpy, pandas, scikit-learn, scipy,
matplotlib, seaborn, ruptures) install automatically with the command above.

---

## What you get
Running the pipeline writes to the output directory:
- `validation_report.md` — discovered levels, estimator comparison, ground-truth accuracy
- `memory_mountain.png` — latency-vs-working-set curve with detected cache bands
- `model_selection.png` — Elbow vs Silhouette model selection
- `wss_curve.csv` (+ `wss_curves_all.csv` with `--runs > 1`) — the raw curve(s)

## Useful options
| Flag | Meaning |
|---|---|
| `--max-mb N` | Largest working-set size (raise to ≥512 for large-L3/DRAM machines) |
| `--runs N` | Independent sweeps for stability/error-bar evaluation |
| `--repeats N` | Repeats per size (minimum is kept) |
| `--hops N` | Minimum pointer-chase hops per timing window (default 2^20) |
| `--penalty F` | Change-point penalty **override**; omit for automatic level selection (the default) |
| `--seed N` | RNG seed (reproducible permutations) |
| `--method samples` | The documented naive baseline (retained to reproduce its failure) |
| `--samples N`, `--mode {0,1}` | Sample count / access mode for the legacy `samples` baseline |

## Repository layout
```
src/autoecho/
  wss/wss_probe.c, wss/__init__.py   native WSS pointer-chase probe + wrapper
  analysis.py                        change-point + clustering level discovery
  validation.py                      ground-truth comparison (sysctl / sysfs / WMI)
  evaluation.py                      comparative evaluation across sweeps
  report.py                          plots + Markdown report
  probe/, preprocessing.py, clustering.py   legacy sample-based baseline
compare_curves.py                    overlay curves from several machines
crosscheck_lmbench.py                convert lmbench lat_mem_rd output for overlay
docs/                                literature review, methodology, dissertation, guides
```

## Cross-platform notes
The probe builds and runs on **Linux, Windows, and macOS** across x86-64 and
ARM64; tick-to-nanosecond conversion is calibrated at runtime against the OS
monotonic clock. See `docs/05_Cross_Platform_Guide.md` and
`docs/06_Setup_Guide.md` for per-OS, step-by-step instructions.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `No module named 'autoecho'` | Run `pip install -e .` from the project root (the package lives under `src/`). |
| `No module named 'autoecho.wss_probe_c'` | The C extension isn't built — run `pip install -e .`. |
| `Python.h: No such file` (Linux) | Install `python3-dev` / `python3-devel`. |
| `Microsoft Visual C++ 14.0 … required` (Windows) | Install the MSVC C++ Build Tools, reopen the shell. |
| Import fails after copying the folder between machines | Delete any stale `*.so`/`*.pyd` and rebuild with `pip install -e .` — compiled extensions are platform-specific. |
