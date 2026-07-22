import numpy as np
import pandas as pd

# Shared timer resolution (single source of truth; see platform_timing).
from autoecho.platform_timing import get_timer_resolution_ns

try:
    import autoecho.probe_c as probe_c
except ImportError as _e:  # extension not built, or built for another platform
    raise ImportError(
        "Auto-Echo's native baseline probe (autoecho.probe_c) is not available. "
        "Build the C extensions from the project root with:\n\n"
        "    pip install -e .\n\n"
        "See README.md and docs/06_Setup_Guide.md for prerequisites.\n"
        f"Original import error: {_e}"
    ) from _e


def collect(num_samples: int = 100000, mode: int = 0) -> pd.DataFrame:
    """
    Collect memory access latencies.
    
    :param num_samples: Number of memory accesses to time.
    :param mode: 0 for L1/L2 natural eviction, 1 to force deep memory (DRAM) using clflush (x86 only).
    :return: Pandas DataFrame containing latencies in nanoseconds.
    """
    # Call the C-Extension
    raw_ticks = probe_c.collect_latencies(num_samples, mode)
    
    # Convert to NumPy array
    ticks_array = np.array(raw_ticks, dtype=np.float64)
    
    # Convert to nanoseconds
    resolution = get_timer_resolution_ns()
    ns_array = ticks_array * resolution
    
    df = pd.DataFrame({
        'access_index': np.arange(num_samples),
        'latency_ns': ns_array
    })
    
    return df
