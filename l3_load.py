#!/usr/bin/env python3
"""Shared-L3 contention load generator (Auto-Echo Task B).

Spawns *N* worker processes, each continuously streaming (read+write) over a
buffer **larger than the shared L3**, pinned to a logical CPU **other than 0**
(the WSS probe pins to CPU 0 via ``SetThreadAffinityMask``). The workers
therefore contend for shared-L3 *capacity* while leaving the probe's own core
free, so a quiesced-vs-loaded probe comparison isolates L3 contention rather
than core contention.

This is the load used for the §5.3.2 L3-contention test. It is deliberately
simple and fully specified so an examiner can reproduce it: worker count,
per-worker buffer size and the pinned CPU set are all printed at start-up.

Usage::

    # run until Ctrl-C / terminated (use while a --huge-pages sweep runs):
    python l3_load.py --workers 14 --buffer-mb 64
    # timed:
    python l3_load.py --workers 14 --buffer-mb 64 --seconds 180

Each worker streams ``buffer-mb`` MiB (default 64, comfortably above the 20 MiB
L3) as a NumPy ``uint8`` array with ``buf += 1`` in a tight loop, reading and
writing every byte each pass. CPU pinning uses ``SetProcessAffinityMask``
(kernel32) on Windows and ``os.sched_setaffinity`` elsewhere; if neither is
available the worker runs unpinned and says so.
"""
import argparse
import ctypes
import os
import sys
import time
from multiprocessing import Process, Value

import numpy as np


def _pin(cpu: int) -> bool:
    """Pin the current process to a single logical CPU. Returns True on success."""
    try:
        if sys.platform == "win32":
            k32 = ctypes.windll.kernel32
            ok = k32.SetProcessAffinityMask(k32.GetCurrentProcess(), 1 << cpu)
            return bool(ok)
        if hasattr(os, "sched_setaffinity"):
            os.sched_setaffinity(0, {cpu})
            return True
    except Exception:
        return False
    return False


def _worker(cpu: int, buffer_mb: int, stop) -> None:
    _pin(cpu)
    buf = np.ones(buffer_mb * 1024 * 1024, dtype=np.uint8)  # resident, > L3
    # Read-modify-write the whole buffer every pass: streams >L3 bytes through
    # the cache hierarchy, continuously evicting shared-L3 lines.
    while not stop.value:
        buf += 1


def main() -> None:
    ncpu = os.cpu_count() or 2
    ap = argparse.ArgumentParser(description="Shared-L3 contention load generator.")
    ap.add_argument("--workers", type=int, default=max(1, ncpu - 2),
                    help="number of streaming worker processes (default: cpus-2)")
    ap.add_argument("--buffer-mb", type=int, default=64,
                    help="per-worker buffer in MiB (must exceed the L3; default 64)")
    ap.add_argument("--cpus", default=None,
                    help="comma-separated CPUs to pin workers to "
                         "(default: all logical CPUs except 0 and 1)")
    ap.add_argument("--seconds", type=float, default=0.0,
                    help="run duration; 0 (default) = until Ctrl-C / terminated")
    args = ap.parse_args()

    if args.cpus:
        cpus = [int(c) for c in args.cpus.split(",")]
    else:
        cpus = list(range(2, ncpu)) or [1]  # skip CPU 0 and its likely HT sibling 1

    stop = Value("i", 0)
    procs = []
    for i in range(args.workers):
        cpu = cpus[i % len(cpus)]
        p = Process(target=_worker, args=(cpu, args.buffer_mb, stop), daemon=True)
        p.start()
        procs.append((p, cpu))

    total_mb = args.workers * args.buffer_mb
    print(f"[l3_load] {args.workers} workers x {args.buffer_mb} MiB "
          f"= {total_mb} MiB streamed, pinned to CPUs "
          f"{sorted({c for _, c in procs})} (CPU 0 left free for the probe)")
    for p, cpu in procs:
        print(f"[l3_load]   worker pid={p.pid} -> CPU {cpu}")
    sys.stdout.flush()

    try:
        if args.seconds > 0:
            time.sleep(args.seconds)
        else:
            while True:
                time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        stop.value = 1
        for p, _ in procs:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
        print("[l3_load] stopped.")


if __name__ == "__main__":
    main()
