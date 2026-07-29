#!/usr/bin/env python3
"""Per-level capacity confidence intervals over repeated sweeps (Auto-Echo Task C).

Loads a multi-sweep ``wss_curves_all.csv``, detects the four-level L1/L2/L3/DRAM
split per sweep with a fixed change-point penalty (count-stable, so the same rule
localises the same three cache boundaries in every sweep), and reports each cache
level's detected capacity as **median with min-max** over the sweeps. Ten sweeps is
too few for a parametric interval, so a non-parametric min-max spread is reported --
no standard error is quoted as if it were one (dissertation §6.5).

The capacity (a working-set-size knee) is frequency-invariant, so this spread
reflects genuine boundary-localisation variability, not clock drift.

Usage::

    python capacity_ci.py data/intel_ci/wss_curves_all.csv
"""
import argparse

import numpy as np
import pandas as pd

from autoecho.analysis import detect_levels_changepoint

PENALTY = 3.0  # yields the 4-level L1/L2/L3/DRAM split (Table 9)
NAMES = ["L1", "L2", "L3", "L4", "L5"]


def _human(n: float) -> str:
    for u in ("B", "KiB", "MiB", "GiB"):
        if abs(n) < 1024.0:
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024.0
    return f"{n:.1f} TiB"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("all_csv", help="wss_curves_all.csv from a --runs N sweep")
    args = ap.parse_args()

    df = pd.read_csv(args.all_csv)
    runs = sorted(df["run"].unique()) if "run" in df.columns else [None]
    per_level: dict[int, list[float]] = {}
    nlevels = []
    for r in runs:
        g = df[df["run"] == r] if r is not None else df
        curve = g[["wss_bytes", "latency_ns"]].sort_values("wss_bytes")
        lv = detect_levels_changepoint(curve, penalty=PENALTY)
        nlevels.append(len(lv))
        caps = lv.dropna(subset=["capacity_bytes"]).reset_index(drop=True)
        for i, row in caps.iterrows():
            per_level.setdefault(i, []).append(float(row["capacity_bytes"]))

    n4 = sum(1 for n in nlevels if n == 4)
    print(f"Per-level detected capacity over {len(runs)} sweeps "
          f"(penalty={PENALTY}; {n4}/{len(runs)} sweeps returned 4 levels)\n")
    print(f"{'level':<6}{'median':>12}{'min':>12}{'max':>12}{'n':>5}")
    print("-" * 41)
    for i in sorted(per_level):
        v = np.array(per_level[i])
        name = NAMES[i] if i < len(NAMES) else f"L{i+1}"
        print(f"{name:<6}{_human(np.median(v)):>12}{_human(v.min()):>12}"
              f"{_human(v.max()):>12}{len(v):>5}")


if __name__ == "__main__":
    main()
