# Auto-Echo Setup & Verification Guide (Linux and Windows)

This is a step-by-step walkthrough for building, running, and **verifying**
Auto-Echo on a fresh Linux or Windows machine. Each step has a checkpoint so you
can confirm it worked before moving on. macOS is covered at the end.

> Goal: produce a `wss_curve.csv`, a `memory_mountain.png`, and a
> `validation_report.md` on each machine, then combine them into one figure.

---

## Part A — Linux (x86-64)

### A1. Install prerequisites
A C compiler and the Python development headers are required to build the probe.

**Debian / Ubuntu**
```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-dev python3-venv git
```
**Fedora / RHEL / CentOS**
```bash
sudo dnf install -y gcc python3-devel git
```
**Checkpoint:** `gcc --version` and `python3 --version` (≥ 3.10) both print a version.

### A2. Get the code and create an isolated environment
```bash
git clone <your-repo-url>
cd "MSc Project"          # or the repo folder name
python3 -m venv .venv
source .venv/bin/activate
```
**Checkpoint:** your prompt now shows `(.venv)`.

### A3. Build and install
```bash
pip install --upgrade pip
pip install -e .
```
This compiles two C extensions with `-O3`. It should end with
`Successfully installed autoecho-0.2.0`.

**Checkpoint — the probe imports and the timer calibrates:**
```bash
python -c "import autoecho.wss_probe_c as w; print('ns/tick =', round(w.calibrate(), 4))"
```
On a ~3 GHz x86 the invariant TSC is usually ~1 GHz-equivalent, so expect a
value on the order of `0.3–1.0`. Any positive number means calibration works.

### A4. Run the sweep
```bash
python -m autoecho --method wss --max-mb 512 --output-dir data_linux
```
For the steadiest curve (pin to a performance core, reduce interference):
```bash
taskset -c 0 nice -n -5 python -m autoecho --method wss --max-mb 512 --output-dir data_linux
```
**Checkpoint:** the run prints four progress lines and
`accuracy: <N>% (<m>/<n> caches matched)`. On a desktop x86 with L1/L2/L3 you
should see **four plateaus** and 2–3 caches matched.

### A5. Inspect the results
```bash
cat data_linux/validation_report.md      # detected levels vs ground truth
# open data_linux/memory_mountain.png in any image viewer
```
Ground truth is read from `/sys/devices/system/cpu/cpu0/cache/`. Cross-check the
printed L1/L2/L3 sizes against the CPU spec sheet (or `lscpu | grep -i cache`).

---

## Part B — Windows (x86-64)

### B1. Install prerequisites
1. **Python 3.10+** from python.org — during install tick **“Add python.exe to
   PATH.”**
2. **Microsoft C++ Build Tools** — download “Build Tools for Visual Studio”, run
   the installer, and select the **“Desktop development with C++”** workload.
   This provides the MSVC compiler needed to build the C extension.

**Checkpoint (in a new PowerShell window):**
```powershell
py --version          # 3.10 or newer
```

### B2. Get the code and create an environment
```powershell
git clone <your-repo-url>
cd "MSc Project"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If activation is blocked, allow it for this session:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
**Checkpoint:** the prompt shows `(.venv)`.

### B3. Build and install
```powershell
pip install --upgrade pip
pip install -e .
```
The build automatically uses `/O2` on MSVC (handled in `setup.py`). If it fails
with *“Microsoft Visual C++ 14.0 or greater is required,”* the Build Tools from
B1 are missing or the shell was opened before installing them — reopen and retry.

**Checkpoint:**
```powershell
python -c "import autoecho.wss_probe_c as w; print('ns/tick =', round(w.calibrate(), 4))"
```
A positive number confirms the tick counter and `QueryPerformanceCounter`
calibration work.

### B4. Run the sweep
Set the power plan to **High performance** first (reduces frequency wobble).
```powershell
python -m autoecho --method wss --max-mb 512 --output-dir data_windows
```
**Checkpoint:** progress lines print and a report/plot are written to
`data_windows\`.

### B5. Inspect the results
```powershell
type data_windows\validation_report.md
# open data_windows\memory_mountain.png
```
Windows ground truth is read from `Win32_CacheMemory` via PowerShell. The
Level→cache mapping and sizes vary by firmware, so **verify the printed ground
truth against the CPU spec sheet** — the detected curve itself is reliable
regardless. If the report shows `0/0 caches`, the OS query was blocked; the
discovery still worked, and you can note the expected sizes manually.

---

## Part C — macOS (already validated: Apple M1, 100% accuracy)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python -m autoecho --method wss --max-mb 256 --output-dir data
```

---

## Part D — Combine the machines into one figure
Copy each machine's `wss_curve.csv` into a shared location (e.g. via git or a USB
drive), then:
```bash
python compare_curves.py \
    data/wss_curve.csv data_linux/wss_curve.csv data_windows/wss_curve.csv \
    --labels "Apple M1,x86 Linux,x86 Windows" \
    --annotate \
    --output compare_mountain.png
```
`compare_mountain.png` overlays all curves on one log–log axis with each
machine's detected cache boundaries marked — the key evaluation figure for the
architecture-agnostic claim.

### Optional: external cross-check against lmbench (Linux)
Validate the probe against the established `lat_mem_rd` tool on the same machine:
```bash
sudo apt-get install -y lmbench          # or build from source
lat_mem_rd -N 5 -t 512 128 > lmbench_raw.txt      # 512 MiB max, 128-byte stride
python crosscheck_lmbench.py lmbench_raw.txt -o data_linux/lmbench_curve.csv
python compare_curves.py data_linux/wss_curve.csv data_linux/lmbench_curve.csv \
    --labels "Auto-Echo,lmbench lat_mem_rd" --annotate -o crosscheck.png
```
Close agreement between the two curves validates Auto-Echo's measurement against
trusted prior art.

---

## Common issues
| Symptom | Cause / fix |
| :--- | :--- |
| `Python.h: No such file or directory` (Linux) | install `python3-dev` / `python3-devel` |
| `Microsoft Visual C++ 14.0 … required` (Windows) | install the “Desktop development with C++” Build Tools, reopen shell |
| Curve is flat / everything ≈ 1 tick | running in a VM with a virtualised timer — use bare metal, or raise `--hops` |
| Very noisy plateaus | raise `--repeats` (e.g. 9) and/or `--hops`; close background apps; pin to a core |
| Too many / too few levels detected | tune `--penalty` (lower ⇒ more levels) |
| `accuracy: 0.0% (0/0)` | OS ground-truth query failed; discovery is unaffected — record spec-sheet sizes manually |

## Reproducibility
Runs are deterministic given `--seed` (the probe RNG and the Silhouette
computation are both seeded). Record the exact command and the machine model
alongside each `--output-dir` for the dissertation's methodology section.
