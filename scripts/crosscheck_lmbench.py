#!/usr/bin/env python3
"""Convert lmbench ``lat_mem_rd`` output into an Auto-Echo ``wss_curve.csv``.

lmbench is the established external tool that performs the same pointer-chasing
load-latency sweep. Running it on the same machine and overlaying its curve on
Auto-Echo's (via compare_curves.py) validates the probe against trusted prior
art -- a strong external cross-check for the dissertation's evaluation.

Usage on a Linux machine with lmbench installed:
    lat_mem_rd -N 5 -t 512 128 > lmbench_raw.txt     # 512 MiB max, 128-byte stride
    python crosscheck_lmbench.py lmbench_raw.txt -o data_linux/lmbench_curve.csv
    python compare_curves.py data_linux/wss_curve.csv data_linux/lmbench_curve.csv \
        --labels "Auto-Echo,lmbench lat_mem_rd" --annotate -o crosscheck.png

lat_mem_rd emits lines of "<size_in_MB> <latency_ns>" (size may be fractional),
optionally interleaved with stride header lines that this parser skips.
"""

import argparse
import csv
import sys


def parse_lmbench(path):
    rows = []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) != 2:
                continue
            try:
                size_mb = float(parts[0])
                latency_ns = float(parts[1])
            except ValueError:
                continue  # skip "stride=..." and other header lines
            if size_mb <= 0 or latency_ns <= 0:
                continue
            wss_bytes = int(round(size_mb * 1024 * 1024))
            rows.append((wss_bytes, wss_bytes / 1024.0, latency_ns))
    return rows


def main():
    ap = argparse.ArgumentParser(
        description="Convert lmbench lat_mem_rd output to wss_curve.csv"
    )
    ap.add_argument("input", help="lat_mem_rd stdout captured to a file")
    ap.add_argument("-o", "--output", default="lmbench_curve.csv")
    args = ap.parse_args()

    rows = parse_lmbench(args.input)
    if not rows:
        sys.exit(
            "No valid '<size_MB> <latency_ns>' rows found — is this lat_mem_rd output?"
        )
    rows.sort(key=lambda r: r[0])
    with open(args.output, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["wss_bytes", "wss_kib", "latency_ns"])
        w.writerows(rows)
    print(
        f"Wrote {len(rows)} points to {args.output} "
        f"(WSS {rows[0][0]//1024} KiB .. {rows[-1][0]//1024//1024} MiB)"
    )


if __name__ == "__main__":
    main()
