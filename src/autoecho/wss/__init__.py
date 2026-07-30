"""Working-set-size (WSS) pointer-chasing probe.

Produces a memory-latency curve: average access latency as a function of the
working-set size. This is the signal from which cache-level capacities are
inferred (cf. lmbench ``lat_mem_rd``). It replaces the flawed sample-based
probe, whose write-before-read pattern guaranteed an L1 hit on every access.
"""

from __future__ import annotations  # allow "int | None" on Python 3.9

import numpy as np
import pandas as pd

# Shared platform helpers (single source of truth). Re-exported so existing
# imports such as `from autoecho.wss import get_timer_resolution_ns` keep working.
from autoecho.platform_timing import get_cache_line_size, get_timer_resolution_ns

try:
    import autoecho.wss_probe_c as wss_probe_c
except ImportError as _e:  # extension not built, or built for another platform
    raise ImportError(
        "Auto-Echo's native probe (autoecho.wss_probe_c) is not available. "
        "This usually means the C extension has not been compiled for this "
        "machine. From the project root run:\n\n"
        "    pip install -e .\n\n"
        "(requires a C compiler and the Python development headers; on Debian/"
        "Ubuntu: 'sudo apt-get install build-essential python3-dev', on Windows: "
        "the MSVC C++ Build Tools). See README.md and docs/06_Setup_Guide.md.\n"
        f"Original import error: {_e}"
    ) from _e


# Number of geometrically-spaced sample points per doubling (octave) of the
# working-set size. Denser sampling ⇒ sharper localisation of the cache knees.
SAMPLES_PER_OCTAVE = 10
# Smallest working set probed, as a multiple of the cache-line size.
MIN_WORKING_SET_LINES = 4
# Default largest working set (bytes). 256 MiB comfortably overflows commodity
# L3/SLC into DRAM; raise for servers with very large last-level caches.
DEFAULT_MAX_BYTES = 256 * 1024 * 1024
# Timing-window sizing: hops per window is at least DEFAULT_MIN_HOPS and at least
# HOPS_PER_SLOT × (slots in the working set), capped at MAX_HOPS so the deepest
# (slowest) sizes do not blow up total runtime.
DEFAULT_MIN_HOPS = 1 << 20
HOPS_PER_SLOT = 8
MAX_HOPS = 1 << 23
DEFAULT_REPEATS = 5
DEFAULT_SEED = 42


def default_wss_sizes(line_size: int, max_bytes: int = DEFAULT_MAX_BYTES) -> np.ndarray:
    """Log-spaced working-set sizes from one cache line up to ``max_bytes``.

    ``SAMPLES_PER_OCTAVE`` points per octave give fine resolution around the
    cache-capacity transitions where the latency curve steps up."""
    min_bytes = line_size * MIN_WORKING_SET_LINES
    n_octaves = np.log2(max_bytes / min_bytes)
    n_points = int(np.ceil(n_octaves * SAMPLES_PER_OCTAVE)) + 1
    sizes = np.unique(
        (min_bytes * 2.0 ** np.linspace(0, n_octaves, n_points)).astype(np.int64)
    )
    # Snap every size to a whole number of cache lines.
    sizes = np.unique((sizes // line_size) * line_size)
    return sizes[sizes >= line_size * 2]


def sweep(
    max_bytes: int = DEFAULT_MAX_BYTES,
    hops: int = DEFAULT_MIN_HOPS,
    repeats: int = DEFAULT_REPEATS,
    seed: int = DEFAULT_SEED,
    stride: int | None = None,
    huge_pages: bool = False,
) -> pd.DataFrame:
    """Run the full working-set-size sweep.

    :param huge_pages: if True, request a 2 MiB large-page chase buffer (Windows
        only; the probe falls back to ordinary 4 KiB pages with a one-line
        warning if ``SeLockMemoryPrivilege`` is unavailable). Large pages
        suppress page-walk latency so a large shared L3 is not masked by the TLB
        (see ``wss_probe.c``). Off by default; ARM/macOS are unaffected.
    :returns: DataFrame with columns ``wss_bytes``, ``wss_kib``,
        ``latency_ns`` (minimum-over-repeats average access latency).
    """
    line = stride if stride is not None else get_cache_line_size()
    resolution = get_timer_resolution_ns()
    sizes = default_wss_sizes(line, max_bytes)

    # Measure sizes in a seed-shuffled order so that thermal/DVFS drift over the
    # multi-minute sweep is decorrelated from the working-set size (otherwise the
    # deepest, longest-running sizes are always measured last and their latency
    # is systematically biased). Deterministic given the seed; sorted for output.
    order = np.random.default_rng(seed).permutation(len(sizes))

    rows = []
    for idx in order:
        size = int(sizes[idx])
        # Amortise more for larger sets; cap to bound total runtime.
        nslots = max(2, size // line)
        this_hops = int(min(max(hops, nslots * HOPS_PER_SLOT), MAX_HOPS))
        ticks = wss_probe_c.measure_wss(
            size, int(line), this_hops, repeats, seed, bool(huge_pages)
        )
        rows.append(
            {
                "wss_bytes": size,
                "wss_kib": size / 1024.0,
                "latency_ns": ticks * resolution,
            }
        )

    return pd.DataFrame(rows).sort_values("wss_bytes").reset_index(drop=True)
