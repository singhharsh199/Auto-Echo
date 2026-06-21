import platform
import subprocess
import numpy as np
import pandas as pd
import autoecho.probe_c as probe_c

def get_timer_resolution_ns():
    """Returns the timer resolution multiplier to convert ticks to nanoseconds."""
    system = platform.system()
    arch = platform.machine()
    
    if system == "Darwin" and arch == "arm64":
        # On Apple Silicon, mach_absolute_time() needs to be converted using timebase
        try:
            import ctypes
            import ctypes.util
            libc = ctypes.CDLL(ctypes.util.find_library('c'))
            class mach_timebase_info_data_t(ctypes.Structure):
                _fields_ = [("numer", ctypes.c_uint32), ("denom", ctypes.c_uint32)]
            
            info = mach_timebase_info_data_t()
            libc.mach_timebase_info(ctypes.byref(info))
            return info.numer / info.denom
        except Exception:
            return 125.0 / 3.0 # Default for M1/M2 (24MHz)
    elif system == "Linux" and arch in ["x86_64", "i386"]:
        # Estimate from /proc/cpuinfo "cpu MHz"
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if "cpu MHz" in line:
                        mhz = float(line.split(':')[1].strip())
                        return 1000.0 / mhz # 1 cycle in ns
        except Exception:
            return 0.3 # Fallback ~3.3GHz
    return 1.0

def collect(num_samples: int = 100000, mode: int = 0) -> pd.DataFrame:
    """
    Collect memory access latencies.
    
    :param num_samples: Number of memory accesses to time.
    :param mode: 0 for L1/L2 natural eviction, 1 to force deep memory (WPQ/DRAM) using clflush.
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
