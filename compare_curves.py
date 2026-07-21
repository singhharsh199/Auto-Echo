#!/usr/bin/env python3
"""Overlay several machines' WSS latency curves on one figure.

Each machine's ``wss_curve.csv`` is produced by ``python -m autoecho --method wss
--output-dir <dir>``. This helper plots them together so an M1 vs x86-Linux vs
Windows comparison becomes a single evaluation figure supporting the
"architecture-agnostic" claim.

Usage:
    python compare_curves.py data/wss_curve.csv data_linux/wss_curve.csv \
        --labels "Apple M1,Intel x86 Linux" --output compare_mountain.png

If --labels is omitted, each curve is named after its parent directory.
With --annotate, detected cache boundaries are marked per machine (requires the
autoecho package to be importable).
"""
import argparse
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd

# Colour-blind-friendly qualitative palette (Okabe–Ito).
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]
MARKERS = ["o", "s", "^", "D", "v", "P"]


def _load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "wss_bytes" not in df.columns:
        if "wss_kib" in df.columns:
            df["wss_bytes"] = (df["wss_kib"] * 1024).astype("int64")
        else:
            raise ValueError(f"{path}: missing 'wss_bytes'/'wss_kib' column")
    if "latency_ns" not in df.columns:
        raise ValueError(f"{path}: missing 'latency_ns' column")
    return df.sort_values("wss_bytes").reset_index(drop=True)


def _default_label(path: str) -> str:
    parent = os.path.basename(os.path.dirname(os.path.abspath(path)))
    return parent or os.path.splitext(os.path.basename(path))[0]


def main():
    ap = argparse.ArgumentParser(description="Overlay WSS latency curves from multiple machines.")
    ap.add_argument("csvs", nargs="+", help="one or more wss_curve.csv files")
    ap.add_argument("--labels", default=None, help="comma-separated labels (one per CSV)")
    ap.add_argument("--output", default="compare_mountain.png", help="output image path")
    ap.add_argument("--annotate", action="store_true", help="mark detected cache boundaries per machine")
    ap.add_argument("--penalty", type=float, default=3.0, help="change-point penalty when --annotate")
    args = ap.parse_args()

    if args.labels:
        labels = [s.strip() for s in args.labels.split(",")]
        if len(labels) != len(args.csvs):
            sys.exit(f"--labels has {len(labels)} entries but {len(args.csvs)} CSVs were given")
    else:
        labels = [_default_label(p) for p in args.csvs]

    detect = None
    if args.annotate:
        try:
            from autoecho.analysis import detect_levels_changepoint
            detect = detect_levels_changepoint
        except Exception as e:
            print(f"[warn] --annotate disabled (cannot import autoecho.analysis: {e})")

    fig, ax = plt.subplots(figsize=(11, 6.5))

    for i, (path, label) in enumerate(zip(args.csvs, labels)):
        df = _load(path)
        color = PALETTE[i % len(PALETTE)]
        ax.plot(
            df["wss_bytes"].values / 1024.0,
            df["latency_ns"].values,
            "-",
            marker=MARKERS[i % len(MARKERS)],
            markersize=3,
            linewidth=1.3,
            color=color,
            label=label,
            zorder=3,
        )
        if detect is not None:
            try:
                levels = detect(df, penalty=args.penalty)
                caps = levels["capacity_bytes"].dropna()
                for cap in caps:
                    ax.axvline(cap / 1024.0, color=color, linestyle=":", linewidth=1.0, alpha=0.7, zorder=2)
            except Exception as e:
                print(f"[warn] annotation failed for {label}: {e}")

    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("Working-set size (KiB) [log2]", fontsize=11, fontweight="bold")
    ax.set_ylabel("Average access latency (ns) [log]", fontsize=11, fontweight="bold")
    ax.set_title("Auto-Echo: Memory Latency Curves Across Machines", fontsize=13, fontweight="bold", pad=12)
    ax.grid(True, which="both", linestyle="-", alpha=0.15)
    ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=10, title="Machine")

    plt.tight_layout()
    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(args.output, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved comparison figure to {args.output}  ({len(args.csvs)} curves)")


if __name__ == "__main__":
    main()
