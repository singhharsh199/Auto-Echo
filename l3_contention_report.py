#!/usr/bin/env python3
"""Quiesced-vs-loaded L3-contention comparison (Auto-Echo Task B, §5.3.2).

For each condition's multi-sweep curve (``wss_curves_all.csv``), this detects the
memory levels **per sweep** with a fixed change-point penalty (4 levels:
L1/L2/L3/DRAM), so the "detected L3 capacity" is extracted by an identical,
count-stable rule in every condition. It reports the L3 knee (effective L3
capacity) as median [min-max] over the sweeps, plus the L3 and DRAM median
latencies -- the numbers the §5.3.2 contention test turns on.

The L3 *knee* (a working-set-size where the plateau ends) is frequency-invariant:
uniform DVFS scaling shifts every latency but does not move the knee, so a knee
that moves between conditions is a *capacity* effect (contention), not a clock
effect. Absolute latencies are reported too but carry the DVFS caveat when the
loaded condition runs the other cores hot.

Usage::

    python l3_contention_report.py \
        "quiesced=data/intel_l3_quiesced128/wss_curves_all.csv" \
        "loaded=data/intel_l3_loaded/wss_curves_all.csv"
"""
import argparse

import numpy as np
import pandas as pd

from autoecho.analysis import detect_levels_changepoint

PENALTY = 3.0  # PELT penalty that yields the 4-level L1/L2/L3/DRAM split (Table 9)


def _per_sweep(all_csv: str):
    df = pd.read_csv(all_csv)
    group_col = "run" if "run" in df.columns else None
    groups = df.groupby(group_col) if group_col else [(0, df)]
    l3_mib, l3_med, dram_med, nlev = [], [], [], []
    for _, g in groups:
        curve = g[["wss_bytes", "latency_ns"]].sort_values("wss_bytes")
        lv = detect_levels_changepoint(curve, penalty=PENALTY)
        nlev.append(len(lv))
        caps = lv.dropna(subset=["capacity_bytes"])  # cache levels (DRAM cap is NaN)
        if len(caps):
            l3 = caps.iloc[-1]  # last cache level before DRAM = L3
            l3_mib.append(l3["capacity_bytes"] / (1024 * 1024))
            l3_med.append(l3["latency_ns_median"])
        dram_med.append(lv.iloc[-1]["latency_ns_median"])
    return l3_mib, l3_med, dram_med, nlev


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("conditions", nargs="+", help="label=wss_curves_all.csv pairs")
    args = ap.parse_args()

    print(f"L3-contention comparison (per-sweep, PELT penalty={PENALTY}, 4-level split)\n")
    print(f"{'condition':<14}{'L3 knee MiB (med [min-max])':<30}"
          f"{'L3 lat ns':<12}{'DRAM lat ns':<12}{'levels':<8}")
    print("-" * 76)
    for spec in args.conditions:
        label, path = spec.split("=", 1)
        l3_mib, l3_med, dram_med, nlev = _per_sweep(path)
        if l3_mib:
            knee = (f"{np.median(l3_mib):.1f} "
                    f"[{min(l3_mib):.1f}-{max(l3_mib):.1f}]")
        else:
            knee = "n/a"
        l3l = f"{np.median(l3_med):.1f}" if l3_med else "n/a"
        draml = f"{np.median(dram_med):.1f}" if dram_med else "n/a"
        levs = "/".join(str(n) for n in nlev)
        print(f"{label:<14}{knee:<30}{l3l:<12}{draml:<12}{levs:<8}")


if __name__ == "__main__":
    main()
