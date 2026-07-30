"""Shared pytest fixtures.

Tests here exercise the pure-Python analysis/validation/evaluation logic on
*synthetic* latency curves, so they run without a compiled C extension and
without any particular hardware.
"""

import numpy as np
import pandas as pd
import pytest


def _synthetic_curve(
    steps, points_per_octave=10, max_bytes=256 * 1024 * 1024, line=64, noise=0.0, seed=0
):
    """Build a clean staircase latency curve.

    :param steps: list of (capacity_bytes, latency_ns) plateaus, ascending. A
        working set larger than a plateau's capacity takes the next plateau's
        latency; the final plateau's latency represents DRAM.
    """
    rng = np.random.default_rng(seed)
    min_bytes = line * 4
    n_oct = np.log2(max_bytes / min_bytes)
    n = int(np.ceil(n_oct * points_per_octave)) + 1
    sizes = np.unique((min_bytes * 2.0 ** np.linspace(0, n_oct, n)).astype(np.int64))
    sizes = np.unique((sizes // line) * line)

    caps = [c for c, _ in steps]
    lats = [latency for _, latency in steps]

    def latency_for(wss):
        for cap, lat in zip(caps, lats, strict=True):
            if wss <= cap:
                return lat
        return lats[-1]

    latency = np.array([latency_for(s) for s in sizes], dtype=float)
    if noise:
        latency = latency * (1.0 + rng.normal(0, noise, size=latency.shape))
    return pd.DataFrame(
        {
            "wss_bytes": sizes,
            "wss_kib": sizes / 1024.0,
            "latency_ns": latency,
        }
    )


@pytest.fixture
def three_level_curve():
    """L1 32 KiB @1.5 ns, L2 256 KiB @5 ns, then DRAM @90 ns."""
    return _synthetic_curve(
        [
            (32 * 1024, 1.5),
            (256 * 1024, 5.0),
            (8 * 1024 * 1024, 14.0),
        ]
    )


@pytest.fixture
def make_curve():
    """Factory so tests can build custom staircases."""
    return _synthetic_curve
