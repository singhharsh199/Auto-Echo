#!/usr/bin/env python3
"""Per-level capacity spread over repeated sweeps (dissertation §5.3, Table 9 footnote).

Loads a multi-sweep ``wss_curves_all.csv``, detects the L1/L2/L3/DRAM split in
**each sweep independently**, and reports each cache level's detected capacity as
**median with min-max** over the sweeps. Ten sweeps is too few for a parametric
interval, so a non-parametric min-max spread is reported -- no standard error is
quoted as if it were one (§5.5).

Detection uses the *productive* automatic path by default (exact 1-D k-means +
Silhouette counts the levels, penalty-free ``Dynp`` localises them), so these
capacities are produced by the same estimator as every other number in §5 and no
hand-set penalty enters a reported result. ``--penalty`` overrides it with PELT
for the sensitivity check; on the ten-sweep Intel data both paths return
identical per-sweep capacities, which is why the earlier penalty-3.0 figures
stand unchanged.

Per-sweep detection matters: the aggregate ``wss_curve.csv`` is the *minimum*
over sweeps at each size, and in the noisy deep region that lower envelope pulls
the L3 knee down. Detecting per sweep and then taking the median across sweeps
avoids attributing an aggregation artefact to the hardware (§5.3).

Usage::

    python capacity_ci.py data/intel_ci/wss_curves_all.csv
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from autoecho.analysis import detect_levels_changepoint

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
    ap.add_argument(
        "--penalty",
        type=float,
        default=None,
        help="override the automatic path with PELT at this penalty "
        "(sensitivity check only; omit for the productive path)",
    )
    ap.add_argument(
        "--ground-truth",
        type=float,
        default=None,
        help="nominal size in MiB of the deepest cache, to report the "
        "median capacity's error against it (e.g. 20 for a 20 MiB L3)",
    )
    ap.add_argument(
        "--json",
        type=Path,
        default=None,
        metavar="PATH",
        help="also write the per-sweep spread to PATH as JSON. The React "
        "dashboard reads this so it reports the same per-sweep median "
        "capacities as §5.3 rather than the aggregate-curve knee.",
    )
    args = ap.parse_args()

    df = pd.read_csv(args.all_csv)
    runs = sorted(df["run"].unique()) if "run" in df.columns else [None]
    per_level: dict[int, list[float]] = {}
    nlevels = []
    for r in runs:
        g = df[df["run"] == r] if r is not None else df
        curve = g[["wss_bytes", "latency_ns"]].sort_values("wss_bytes")
        lv = detect_levels_changepoint(curve, penalty=args.penalty)
        nlevels.append(len(lv))
        caps = lv.dropna(subset=["capacity_bytes"]).reset_index(drop=True)
        for i, row in caps.iterrows():
            per_level.setdefault(i, []).append(float(row["capacity_bytes"]))

    modal = max(set(nlevels), key=nlevels.count)
    n_modal = nlevels.count(modal)
    rule = (
        "automatic (Silhouette count + penalty-free Dynp)"
        if args.penalty is None
        else f"PELT penalty={args.penalty}"
    )
    print(f"Per-level detected capacity over {len(runs)} sweeps [{rule}]")
    print(
        f"  level counts per sweep: {nlevels} "
        f"(modal {modal}, in {n_modal}/{len(runs)} sweeps)\n"
    )
    print(
        f"{'level':<6}{'median':>12}{'min':>12}{'max':>12}{'n':>5}"
        f"{'  per-sweep values':<20}"
    )
    print("-" * 62)
    for i in sorted(per_level):
        v = np.array(per_level[i])
        name = NAMES[i] if i < len(NAMES) else f"L{i+1}"
        uniq = sorted({_human(x) for x in v})
        print(
            f"{name:<6}{_human(np.median(v)):>12}{_human(v.min()):>12}"
            f"{_human(v.max()):>12}{len(v):>5}  {', '.join(uniq)}"
        )

    if args.ground_truth and per_level:
        deepest = max(per_level)
        v = np.array(per_level[deepest])
        gt = args.ground_truth * 1024 * 1024
        med = float(np.median(v))
        print(
            f"\nDeepest cache vs nominal {args.ground_truth:g} MiB: "
            f"median {_human(med)} ({100 * (med - gt) / gt:+.1f}%), "
            f"min {_human(v.min())} ({100 * (v.min() - gt) / gt:+.1f}%), "
            f"max {_human(v.max())} ({100 * (v.max() - gt) / gt:+.1f}%)"
        )
        n_at_max = int((v == v.max()).sum())
        print(f"  {n_at_max}/{len(v)} sweeps detected {_human(v.max())}")

    if args.json:
        _write_json(args.json, args.all_csv, rule, runs, nlevels, modal, per_level)
        print(f"\nwrote {args.json}")


def _write_json(
    path: Path,
    source: str,
    rule: str,
    runs: list,
    nlevels: list[int],
    modal: int,
    per_level: dict[int, list[float]],
) -> None:
    """Serialise the spread computed above; performs no detection of its own.

    Emitted so the dashboard can display the *same* statistic the dissertation
    reports. Both raw bytes and the rendered string are written: the string is
    what §5.3's tables show, and re-deriving it downstream would risk a rounding
    disagreement between the two artefacts over a value like 19.7 MiB.
    """
    payload = {
        "source": Path(source).name,
        "sweeps": len(runs),
        "rule": rule,
        "levelCountsPerSweep": [int(n) for n in nlevels],
        "modalLevels": int(modal),
        "levels": [
            {
                "index": i,
                "name": NAMES[i] if i < len(NAMES) else f"L{i + 1}",
                "medianBytes": float(np.median(per_level[i])),
                "minBytes": float(np.min(per_level[i])),
                "maxBytes": float(np.max(per_level[i])),
                "medianText": _human(float(np.median(per_level[i]))),
                "n": len(per_level[i]),
                "perSweepBytes": [float(x) for x in per_level[i]],
            }
            for i in sorted(per_level)
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
