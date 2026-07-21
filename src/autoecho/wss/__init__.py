"""Working-set-size (WSS) pointer-chasing probe.

Produces a memory-latency curve: average access latency as a function of the
working-set size. This is the signal from which cache-level capacities are
inferred (cf. lmbench ``lat_mem_rd``). It replaces the flawed sample-based
probe, whose write-before-read pattern guaranteed an L1 hit on every access.
"""
import platform
import subprocess

import numpy as np
import pandas as pd

import autoecho.wss_probe_c as wss_probe_c


def get_cache_line_size() -> int:
    """Detect the hardware cache-line size in bytes (128 on Apple Silicon,
    64 on x86 Linux/Windows). Falls back to 64."""
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.cachelinesize"])
            return int(out.strip())
        if system == "Linux":
            with open(
                "/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size"
            ) as f:
                return int(f.read().strip())
        # Windows: x86 uses 64-byte lines; the fallback below is correct there.
    except Exception:
        pass
    return 64


def get_timer_resolution_ns() -> float:
    """Nanoseconds per hardware timer tick, used to convert the probe's
    ticks-per-access into nanoseconds.

    Apple Silicon uses the exact rational from ``mach_timebase_info`` (125/3 on
    M1). Every other platform (x86 TSC, ARM ``cntvct``, via Windows QPC) is
    CALIBRATED at runtime against the OS monotonic clock -- this is robust to
    turbo/frequency scaling, unlike reading a nominal CPU frequency."""
    system = platform.system()
    arch = platform.machine()

    if system == "Darwin" and arch == "arm64":
        try:
            import ctypes
            import ctypes.util

            libc = ctypes.CDLL(ctypes.util.find_library("c"))

            class mach_timebase_info_data_t(ctypes.Structure):
                _fields_ = [("numer", ctypes.c_uint32), ("denom", ctypes.c_uint32)]

            info = mach_timebase_info_data_t()
            libc.mach_timebase_info(ctypes.byref(info))
            return info.numer / info.denom
        except Exception:
            return 125.0 / 3.0

    # x86 TSC and ARM-Linux: calibrate at runtime (correct on all of them).
    try:
        return float(wss_probe_c.calibrate())
    except Exception:
        return 1.0


def default_wss_sizes(line_size: int, max_bytes: int = 256 * 1024 * 1024) -> np.ndarray:
    """Log-spaced working-set sizes from one cache line up to ``max_bytes``.

    ~10 points per octave gives fine resolution around the cache-capacity
    transitions where the latency curve steps up."""
    min_bytes = line_size * 4
    n_octaves = np.log2(max_bytes / min_bytes)
    n_points = int(np.ceil(n_octaves * 10)) + 1
    sizes = np.unique(
        (min_bytes * 2.0 ** np.linspace(0, n_octaves, n_points)).astype(np.int64)
    )
    # Snap every size to a whole number of cache lines.
    sizes = np.unique((sizes // line_size) * line_size)
    return sizes[sizes >= line_size * 2]


def sweep(
    max_bytes: int = 256 * 1024 * 1024,
    hops: int = 1 << 20,
    repeats: int = 5,
    seed: int = 42,
    stride: int | None = None,
) -> pd.DataFrame:
    """Run the full working-set-size sweep.

    :returns: DataFrame with columns ``wss_bytes``, ``wss_kib``,
        ``latency_ns`` (minimum-over-repeats average access latency).
    """
    line = stride if stride is not None else get_cache_line_size()
    resolution = get_timer_resolution_ns()
    sizes = default_wss_sizes(line, max_bytes)

    rows = []
    for size in sizes:
        # Amortise more for larger sets; cap to bound total runtime.
        nslots = max(2, int(size) // line)
        this_hops = int(min(max(hops, nslots * 8), 1 << 23))
        ticks = wss_probe_c.measure_wss(int(size), int(line), this_hops, repeats, seed)
        rows.append(
            {
                "wss_bytes": int(size),
                "wss_kib": int(size) / 1024.0,
                "latency_ns": ticks * resolution,
            }
        )

    return pd.DataFrame(rows)
