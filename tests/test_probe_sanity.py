"""Sanity checks on the native probe.

These guard against the compiler optimising the pointer chase away (the
``void *volatile g_sink`` / compiler-barrier fix): if the loop were deleted, the
measured latencies collapse to physically impossible ~0 ns and these tests fail.
Skipped automatically when the C extension is not built.
"""

import pytest

pytest.importorskip("autoecho.wss_probe_c")

from autoecho.wss import sweep  # noqa: E402  (import after skip guard)


def test_probe_latency_is_physically_plausible():
    df = sweep(max_bytes=16 * 1024 * 1024, hops=1 << 19, repeats=3)
    lo = df["latency_ns"].min()
    hi = df["latency_ns"].max()
    # An L1 hit is ~1 ns; anything far below that means the loop was elided.
    assert lo > 0.3, f"latency {lo} ns implausibly small — pointer chase elided?"
    # The largest working set must reach real DRAM latency (tens of ns).
    assert hi > 15.0, f"max latency {hi} ns too small — no deep-memory plateau"


def test_probe_latency_increases_with_working_set():
    df = sweep(max_bytes=64 * 1024 * 1024, hops=1 << 19, repeats=3)
    smallest = df.iloc[0]["latency_ns"]
    largest = df.iloc[-1]["latency_ns"]
    # DRAM must be materially slower than the smallest (L1-resident) working set.
    assert largest > 5 * smallest


def test_sweep_is_deterministic_for_fixed_seed():
    a = sweep(max_bytes=4 * 1024 * 1024, hops=1 << 18, repeats=2, seed=7)
    b = sweep(max_bytes=4 * 1024 * 1024, hops=1 << 18, repeats=2, seed=7)
    # Same seed ⇒ same WSS grid and ordering; latencies close (timing noise only).
    assert list(a["wss_bytes"]) == list(b["wss_bytes"])
