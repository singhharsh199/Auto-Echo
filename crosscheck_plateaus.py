#!/usr/bin/env python3
"""Per-plateau quantitative cross-check: Auto-Echo vs lmbench ``lat_mem_rd``.

Auto-Echo's own level discovery (``detect_levels_changepoint``) defines the four
plateau regions (L1 / L2 / L3 / DRAM) as working-set-size ranges. For each range
this reports Auto-Echo's median latency, lmbench's median over the *same* range,
and the ratio -- turning the visual overlay of ``compare_curves.py`` into a
quantitative agreement check (dissertation §6.3, Task A).

Usage::

    python crosscheck_plateaus.py \
        data/intel_i5_13450hx/wss_curve.csv \
        data/intel_i5_13450hx/lmbench_curve.csv
"""
import argparse

import numpy as np
import pandas as pd

from autoecho.analysis import detect_levels_changepoint


def _load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "wss_bytes" not in df.columns and "wss_kib" in df.columns:
        df["wss_bytes"] = (df["wss_kib"] * 1024).astype("int64")
    return df.sort_values("wss_bytes").reset_index(drop=True)


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(n) < 1024.0:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}TiB"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("autoecho_csv", help="Auto-Echo wss_curve.csv")
    ap.add_argument("lmbench_csv", help="lmbench_curve.csv from crosscheck_lmbench.py")
    args = ap.parse_args()

    ae = _load(args.autoecho_csv)
    lm = _load(args.lmbench_csv)
    levels = detect_levels_changepoint(ae)  # automatic count + localisation

    print(f"Auto-Echo curve : {args.autoecho_csv}  ({len(ae)} points)")
    print(f"lmbench curve   : {args.lmbench_csv}  ({len(lm)} points)")
    print(f"Auto-Echo detected {len(levels)} levels\n")

    hdr = ("Level", "WSS range", "AE median", "lmbench median", "ratio AE/lm", "n(AE/lm)")
    print(f"{hdr[0]:<10}{hdr[1]:>20}{hdr[2]:>12}{hdr[3]:>16}{hdr[4]:>13}{hdr[5]:>12}")
    print("-" * 83)
    for _, r in levels.iterrows():
        lo, hi = int(r["wss_lo_bytes"]), int(r["wss_hi_bytes"])
        ae_seg = ae[(ae["wss_bytes"] >= lo) & (ae["wss_bytes"] <= hi)]
        lm_seg = lm[(lm["wss_bytes"] >= lo) & (lm["wss_bytes"] <= hi)]
        ae_med = float(np.median(ae_seg["latency_ns"])) if len(ae_seg) else float("nan")
        lm_med = float(np.median(lm_seg["latency_ns"])) if len(lm_seg) else float("nan")
        ratio = ae_med / lm_med if lm_med else float("nan")
        rng = f"{_fmt_bytes(lo)}-{_fmt_bytes(hi)}"
        print(f"{r['level_name']:<10}{rng:>20}{ae_med:>10.2f}ns{lm_med:>14.2f}ns"
              f"{ratio:>12.2f}x{len(ae_seg):>7}/{len(lm_seg):<4}")


if __name__ == "__main__":
    main()
