#!/usr/bin/env python3
"""Test whether the selected level count depends on the sweep's sampling density.

Motivation (dissertation §3.2.1). The Silhouette coefficient weights every
observation equally, so its value depends on how many points fall in each cluster
-- and that is fixed by the experimenter's geometric sampling grid, not by the
hardware. A level spanning more octaves receives proportionally more points. The
selected level count is therefore, in principle, a function of the sweep density.
That confound is untested by the penalty-sensitivity analyses (which vary a
different hyperparameter), so this script varies it directly.

Two modes:

* ``measure`` -- re-run the probe at each density on the current machine. This is
  the real experiment and requires the built C extension.
* ``subsample`` -- derive lower densities from an existing curve. Because the
  sweep is geometric at ``SAMPLES_PER_OCTAVE`` points per octave, taking every
  m-th point yields *exactly* the grid a sweep at ``SAMPLES_PER_OCTAVE / m``
  points per octave would have visited, so no interpolation is involved and no
  value is invented. Used for machines that are not to hand.

Usage:
    python sampling_density_sweep.py measure --densities 5 10 20 --max-mb 256
    python sampling_density_sweep.py subsample data/intel_i5_13450hx/wss_curve.csv
"""

from __future__ import annotations

import argparse

import pandas as pd

from autoecho import analysis


def _report(rows: list[dict], title: str) -> None:
    print(f"\n=== {title} ===")
    print(
        f"{'pts/octave':>11} {'points':>7} {'selected k':>11} {'silhouette':>11} "
        f"{'elbow':>6} {'DBSCAN':>7} {'cp-knee':>8}"
    )
    for r in rows:
        print(
            f"{r['density']:>11} {r['points']:>7} {r['k']:>11} {r['sil']:>11.4f} "
            f"{r['elbow']:>6} {r['dbscan']:>7} {r['cp']:>8}"
        )
    ks = {r["k"] for r in rows}
    verdict = (
        "STABLE -- the selected count does not depend on sampling density"
        if len(ks) == 1
        else f"UNSTABLE -- selected k varies across densities: {sorted(ks)}"
    )
    print(f"  => {verdict}")


def _score(curve: pd.DataFrame, density, label: str) -> dict:
    k, sil = analysis.cluster_level_count(curve)
    return {
        "density": density,
        "points": len(curve),
        "k": k,
        "sil": sil,
        "elbow": analysis.elbow_method(curve)[0],
        "dbscan": analysis.cluster_level_count_dbscan(curve),
        "cp": analysis.changepoint_level_count(curve),
        "label": label,
    }


def cmd_measure(args) -> None:
    from autoecho import wss

    use_huge = False
    if args.huge_pages:
        # Verify rather than assume: the provenance of every row depends on it.
        from autoecho import wss_probe_c

        use_huge = bool(wss_probe_c.hugepages_available())
        if not use_huge:
            raise SystemExit(
                "--huge-pages requested but 2 MiB large pages are unavailable "
                "(needs the 'Lock pages in memory' right and an elevated shell). "
                "Refusing to run: the resulting rows would silently be 4 KiB-page "
                "measurements labelled as huge-page ones."
            )

    rows = []
    for density in args.densities:
        wss.SAMPLES_PER_OCTAVE = density  # read by default_wss_sizes at call time
        curve = wss.sweep(
            max_bytes=args.max_mb * 1024 * 1024, seed=args.seed, huge_pages=use_huge
        )
        rows.append(_score(curve, density, f"{density}/octave"))
        if args.save:
            path = f"{args.save}/wss_curve_density{density}.csv"
            curve.to_csv(path, index=False)
            print(f"  wrote {path} ({len(curve)} points)")
    pages = "2 MiB large pages" if use_huge else "OS default pages"
    _report(
        rows,
        f"Measured on this machine (max {args.max_mb} MiB, "
        f"seed {args.seed}, {pages})",
    )


def cmd_subsample(args) -> None:
    base = pd.read_csv(args.curve)
    rows = []
    for m in args.strides:
        sub = base.iloc[::m].reset_index(drop=True)
        rows.append(_score(sub, f"{args.base_density / m:g}", f"every {m}th"))
    _report(rows, f"Subsampled from {args.curve}")
    print(
        "  note: densities above the source grid cannot be subsampled -- they "
        "need a fresh sweep on the machine."
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("measure", help="re-run the probe at each density")
    m.add_argument("--densities", type=int, nargs="+", default=[5, 10, 20])
    m.add_argument("--max-mb", type=int, default=256)
    m.add_argument("--seed", type=int, default=42)
    m.add_argument(
        "--huge-pages",
        action="store_true",
        help="request a 2 MiB large-page chase buffer (Windows only); "
        "aborts rather than silently falling back to 4 KiB pages",
    )
    m.add_argument("--save", default=None, help="directory to write per-density CSVs")
    m.set_defaults(func=cmd_measure)

    s = sub.add_parser("subsample", help="derive lower densities from a curve")
    s.add_argument("curve")
    s.add_argument("--strides", type=int, nargs="+", default=[4, 2, 1])
    s.add_argument("--base-density", type=float, default=10.0)
    s.set_defaults(func=cmd_subsample)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
