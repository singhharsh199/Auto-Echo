# Running Auto-Echo on Linux, Windows, and macOS

Auto-Echo now builds and runs on **Linux, Windows, and macOS**, on x86-64 and
ARM64. The core probe is portable; the tick-to-nanosecond conversion is
**calibrated at runtime** against the OS monotonic clock, so no per-machine
frequency needs to be configured.

## What is portable, and how

| Concern | Mechanism |
| :--- | :--- |
| Tick counter | `rdtscp` (x86, incl. MSVC `<intrin.h>`), `mach_absolute_time` (Apple), `cntvct_el0` (ARM Linux) |
| Tick → ns | Runtime calibration vs `clock_gettime` (POSIX) / `QueryPerformanceCounter` (Windows); Apple uses its exact `mach_timebase_info` |
| Prefetcher | Data-dependent pointer chase — no flush instruction needed on any platform |
| Cache line size | `sysctl` (macOS), `/sys` (Linux), 64 B fallback (correct on x86 Windows) |
| Core pinning | QoS hint (Apple), `sched_setaffinity` (Linux), `SetThreadAffinityMask` (Windows) |
| Ground truth | `sysctl` (macOS), `/sys/.../cache` (Linux), `Win32_CacheMemory` via PowerShell (Windows) |

---

## Linux (x86-64) — recommended for a clean 3-level result

Prerequisites: Python 3.10+, a C compiler, and Python headers.
```bash
sudo apt-get install -y build-essential python3-dev python3-venv   # Debian/Ubuntu
# Fedora/RHEL:  sudo dnf install -y gcc python3-devel

git clone <your-repo> && cd "MSc Project"
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python -m autoecho --method wss --max-mb 512 --output-dir data_linux
```
Notes:
- On a desktop/server x86 with a real **L1/L2/L3**, you should see four
  plateaus and validation matching all three caches — the cross-platform
  result your dissertation needs.
- The invariant TSC is calibrated automatically; you do **not** need to read
  CPU MHz. If the machine has an old/variant TSC, prefer a physical box over a
  VM (VMs can virtualise the TSC and add noise).
- For the steadiest curve, pin to a performance core and reduce interference:
  ```bash
  taskset -c 0 nice -n -5 python -m autoecho --method wss --max-mb 512
  ```

## Windows (x86-64)

Prerequisites: Python 3.10+ (python.org) and the **MSVC Build Tools**
("Desktop development with C++") so the C extension can compile.
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m autoecho --method wss --max-mb 512 --output-dir data_windows
```
Notes:
- The build uses `/O2` automatically on MSVC (handled in `setup.py`).
- Ground truth is read from `Win32_CacheMemory` via PowerShell. The Level→cache
  mapping (3→L1, 4→L2, 5→L3) and reported sizes vary by firmware — **sanity-check
  the printed ground truth** against the CPU's spec sheet; the detected curve is
  the reliable part.
- Disable turbo-variability effects by setting the power plan to *High
  performance* before running.

## macOS (Apple Silicon / Intel) — already validated

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python -m autoecho --method wss --max-mb 256 --output-dir data
```

---

## Useful flags
| Flag | Meaning |
| :--- | :--- |
| `--max-mb N` | Largest working-set size (raise to ≥512 on machines with large L3/DRAM) |
| `--repeats N` | Repeats per size; the minimum is kept (raise for noisier machines) |
| `--hops N` | Minimum pointer-chase hops per timing window (raise if a plateau looks noisy) |
| `--penalty F` | Change-point sensitivity (lower ⇒ more levels detected) |
| `--seed N` | RNG seed for reproducible permutations |
| `--method samples` | The naive baseline, kept only to reproduce the documented failure |

## Outputs (per `--output-dir`)
- `validation_report.md` — discovered levels, estimator agreement, ground-truth accuracy
- `memory_mountain.png` — the latency-vs-WSS curve with detected bands
- `wss_curve.csv` — the raw curve (for re-plotting / cross-machine comparison)

## Cross-machine comparison tip
Run on each machine into a separate `--output-dir`, then compare the
`wss_curve.csv` files. Plotting several curves together (M1 vs x86 Linux vs
Windows) makes a strong evaluation figure and directly supports the
"architecture-agnostic" claim.

## Troubleshooting
- **`error: Microsoft Visual C++ 14.0 or greater is required`** (Windows):
  install the MSVC Build Tools, then reopen the shell.
- **`Python.h: No such file`** (Linux): install `python3-dev` / `python3-devel`.
- **Flat curve with no steps / everything ~1 tick** (VMs): the guest TSC may be
  virtualised; run on bare metal, or raise `--hops`.
- **Ground truth empty (0/0 caches)**: the OS query failed (e.g. locked-down
  PowerShell). The discovery still works; supply expected sizes from the spec
  sheet manually when writing up.
