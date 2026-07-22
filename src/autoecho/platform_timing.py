"""Shared platform detection: cache-line size and tick-to-nanosecond resolution.

Consolidated in one place so the WSS probe and the legacy baseline probe share a
single implementation. Previously each module defined its own
``get_timer_resolution_ns`` with subtly different (and inconsistent) behaviour.
"""
import platform
import subprocess

# mach_absolute_time on Apple Silicon runs off a 24 MHz counter; mach_timebase
# reports numer/denom = 125/3, i.e. ~41.667 ns per tick. Used as a fallback when
# the exact timebase cannot be queried.
APPLE_SILICON_NS_PER_TICK = 125.0 / 3.0
DEFAULT_CACHE_LINE_BYTES = 64


def get_cache_line_size() -> int:
    """Detect the hardware cache-line size in bytes (128 on Apple Silicon,
    64 on x86 Linux/Windows). Falls back to ``DEFAULT_CACHE_LINE_BYTES``."""
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
        # Windows: x86 uses 64-byte lines, matching the default below.
    except Exception:
        pass
    return DEFAULT_CACHE_LINE_BYTES


def get_timer_resolution_ns() -> float:
    """Nanoseconds per hardware timer tick, used to convert ticks-per-access
    into nanoseconds.

    Apple Silicon uses the exact rational from ``mach_timebase_info``. Every
    other platform (x86 TSC, ARM ``cntvct``, via Windows QPC) is calibrated at
    runtime against the OS monotonic clock -- robust to turbo/frequency scaling,
    unlike reading a nominal CPU frequency."""
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
            return APPLE_SILICON_NS_PER_TICK

    # x86 TSC and ARM-Linux: calibrate at runtime via the native extension.
    try:
        import autoecho.wss_probe_c as wss_probe_c

        ns_per_tick = float(wss_probe_c.calibrate())
        if ns_per_tick <= 0 or ns_per_tick > 1000:
            raise ValueError(f"implausible calibration: {ns_per_tick} ns/tick")
        return ns_per_tick
    except Exception as exc:
        # Never silently substitute 1.0 in a scientific run: a wrong scale
        # produces plausible-looking but incorrect latencies. Warn loudly.
        import warnings

        warnings.warn(
            f"Timer calibration failed ({exc}); falling back to 1.0 ns/tick. "
            "Reported latencies will be in raw ticks, NOT nanoseconds — do not "
            "trust absolute values from this run.",
            RuntimeWarning,
            stacklevel=2,
        )
        return 1.0
