#!/usr/bin/env python3
"""Quantitative cross-check: Auto-Echo vs lmbench ``lat_mem_rd`` (dissertation §5.3.1).

Three analyses, in increasing strength of evidence:

1. **Per-plateau latency agreement.** Auto-Echo's own level discovery
   (``detect_levels_changepoint``) defines the four plateau regions
   (L1 / L2 / L3 / DRAM) as working-set-size ranges. For each range this reports
   Auto-Echo's median latency, lmbench's median over the *same* range, and their
   ratio -- turning the visual overlay of ``compare_curves.py`` into a number
   (Table 13).

2. **Per-band ratio spread.** A single median per band hides *shape*
   disagreement: two curves can share a median while diverging monotonically
   across the band. This reports min/median/max of the point-wise
   lmbench/Auto-Echo ratio, which is what exposes the L2-band divergence
   attributable to 4 KiB-page TLB pressure.

3. **Inference transfer (the strongest check).** Analysis 1 summarises lmbench
   *inside Auto-Echo's own plateau ranges*, so by construction it cannot detect
   disagreement about **where** the boundaries lie -- only about their level. So
   this additionally runs the whole unsupervised pipeline (exact 1-D k-means
   count + change-point localisation) on lmbench's curve as if it were a fresh
   measurement, and validates the recovered hierarchy against the same per-core
   ground truth. That tests the dissertation's actual contribution -- the
   inference layer -- on a foreign tool's data.

Usage::

    python crosscheck_plateaus.py \
        data/intel_i5_13450hx/wss_curve.csv \
        data/intel_i5_13450hx/lmbench_curve.csv
"""
import argparse

import numpy as np
import pandas as pd

from autoecho import validation
from autoecho.analysis import (
    changepoint_level_count,
    cluster_level_count,
    cluster_level_count_dbscan,
    detect_levels_changepoint,
    elbow_method,
)

# Documented per-core sizes for the Intel i5-13450HX P-core (§5.1). Passed
# explicitly rather than read from the OS so the cross-check is reproducible on
# any machine from the committed CSVs.
INTEL_GT = {"L1": 48 * 1024, "L2": 1280 * 1024, "L3": 20480 * 1024}


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


def _infer_on_foreign_curve(lm: pd.DataFrame, gt: dict) -> None:
    """Run the full unsupervised pipeline on lmbench's curve and validate it.

    This is the inference-transfer test: the count comes from the exact 1-D
    k-means + Silhouette stage and the boundaries from penalty-free ``Dynp``,
    exactly as on Auto-Echo's own curve -- nothing is seeded from the Auto-Echo
    result, so agreement here is evidence about the *inference layer*, not a
    restatement of the probe comparison."""
    levels = detect_levels_changepoint(lm)
    k, sil = cluster_level_count(lm)
    print(f"Productive count (exact 1-D k-means + Silhouette): k = {k} "
          f"(score {sil:.3f})")
    print(f"Cross-checks: Elbow = {elbow_method(lm)[0]}, "
          f"DBSCAN = {cluster_level_count_dbscan(lm)}, "
          f"change-point cost-knee = {changepoint_level_count(lm)}")
    print(f"Segmenter returned {len(levels)} levels:\n")

    print(f"{'Level':<10}{'capacity':>12}{'median':>10}{'p5-p95':>18}{'points':>8}")
    print("-" * 58)
    for _, r in levels.iterrows():
        cap = r["capacity_human"]
        band = f"{r['latency_ns_p5']:.2f}-{r['latency_ns_p95']:.2f} ns"
        print(f"{r['level_name']:<10}{cap:>12}{r['latency_ns_median']:>8.2f}ns"
              f"{band:>18}{int(r['n_points']):>8}")

    caps = [c for c in levels["capacity_bytes"].dropna()]
    res = validation.validate(caps, ground_truth=gt)
    print("\nValidated against documented per-core sizes "
          "(one-octave tolerance, Hungarian matching):")
    for cache in res["matches"]:
        det = cache["detected_bytes"]
        det_s = _fmt_bytes(det) if det else "-"
        err = cache["pct_error"]
        err_s = f"{err:+.1f}%" if err is not None else "-"
        oct_s = f"{cache['error_octaves']:.2f} oct" if det else "-"
        mark = "MATCH" if cache["match"] else "MISS"
        print(f"  {cache['cache']:<4} gt={_fmt_bytes(cache['ground_truth_bytes']):>10}"
              f"  detected={det_s:>10}  {err_s:>8}  {oct_s:>9}  {mark}")
    print(f"  recall={res['recall']:.1%} ({res['n_matched']}/{res['n_ground_truth']})  "
          f"precision={res['precision']:.1%} "
          f"({res['n_matched']}/{res['n_detected']}, "
          f"{res['n_false_positive']} false positive(s))  f1={res['f1']:.2f}")


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

    print("=" * 83)
    print("1. Per-plateau latency agreement (lmbench summarised in Auto-Echo's bands)")
    print("=" * 83)
    hdr = ("Level", "WSS range", "AE median", "lmbench median", "ratio lm/AE", "n(AE/lm)")
    print(f"{hdr[0]:<10}{hdr[1]:>20}{hdr[2]:>12}{hdr[3]:>16}{hdr[4]:>13}{hdr[5]:>12}")
    print("-" * 83)
    bands = []
    for _, r in levels.iterrows():
        lo, hi = int(r["wss_lo_bytes"]), int(r["wss_hi_bytes"])
        ae_seg = ae[(ae["wss_bytes"] >= lo) & (ae["wss_bytes"] <= hi)]
        lm_seg = lm[(lm["wss_bytes"] >= lo) & (lm["wss_bytes"] <= hi)]
        ae_med = float(np.median(ae_seg["latency_ns"])) if len(ae_seg) else float("nan")
        lm_med = float(np.median(lm_seg["latency_ns"])) if len(lm_seg) else float("nan")
        # Reported lmbench/Auto-Echo so the number reads as "how much higher
        # lmbench is", matching the dissertation's Table 13.
        ratio = lm_med / ae_med if ae_med else float("nan")
        rng = f"{_fmt_bytes(lo)}-{_fmt_bytes(hi)}"
        print(f"{r['level_name']:<10}{rng:>20}{ae_med:>10.2f}ns{lm_med:>14.2f}ns"
              f"{ratio:>12.2f}x{len(ae_seg):>7}/{len(lm_seg):<4}")
        bands.append((r["level_name"], lo, hi))

    print()
    print("=" * 83)
    print("2. Point-wise ratio spread per band (what a single median conceals)")
    print("=" * 83)
    # Interpolate Auto-Echo onto lmbench's grid in log-WSS: the two tools sample
    # different sizes, so a point-wise ratio needs a common abscissa.
    ae_at_lm = np.interp(np.log(lm["wss_bytes"].values),
                         np.log(ae["wss_bytes"].values),
                         ae["latency_ns"].values)
    ratio_pt = lm["latency_ns"].values / ae_at_lm
    print(f"{'Level':<10}{'WSS range':>20}{'min':>10}{'median':>10}{'max':>10}{'n':>6}")
    print("-" * 66)
    for name, lo, hi in bands:
        m = ((lm["wss_bytes"].values >= lo) & (lm["wss_bytes"].values <= hi))
        if not m.any():
            continue
        rr = ratio_pt[m]
        rng = f"{_fmt_bytes(lo)}-{_fmt_bytes(hi)}"
        print(f"{name:<10}{rng:>20}{rr.min():>9.2f}x{np.median(rr):>9.2f}x"
              f"{rr.max():>9.2f}x{m.sum():>6}")

    print()
    print("=" * 83)
    print("3. Inference transfer: the whole pipeline run on lmbench's curve")
    print("=" * 83)
    _infer_on_foreign_curve(lm, INTEL_GT)


if __name__ == "__main__":
    main()
