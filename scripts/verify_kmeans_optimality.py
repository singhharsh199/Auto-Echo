#!/usr/bin/env python3
"""Verify that the reported level counts are not artefacts of K-Means local optima.

K-Means is solved by Lloyd's algorithm, a local-search heuristic with no
optimality guarantee. In *one* dimension, however, the optimal k-partition is
contiguous in sorted order, so the global optimum is computable exactly by
dynamic programming in O(k n^2) (Fisher 1958; Wang & Song 2011, "Ckmeans.1d.dp").

This script computes, for every k in the model-selection search range and for
each measured curve:

  * the within-cluster sum of squares attained by Lloyd (as the pipeline runs it),
  * the globally optimal within-cluster sum of squares by dynamic programming,
  * the Silhouette score of each partition, and hence whether exact optimisation
    would change the selected level count.

It underpins the claim in §3.2.1 of the dissertation. Run:

    python verify_kmeans_optimality.py
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from autoecho.analysis import DEFAULT_MAX_K

# Mirrors analysis.cluster_level_count so the comparison is like-for-like.
RANDOM_STATE = 42
N_INIT = 10


def _prefix_sums(xs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.concatenate([[0.0], np.cumsum(xs)]),
        np.concatenate([[0.0], np.cumsum(xs * xs)]),
    )


def exact_1d_kmeans(x: np.ndarray, k: int) -> tuple[float, np.ndarray]:
    """Globally optimal 1-D k-means by dynamic programming.

    Returns ``(cost, labels)`` where ``cost`` is the minimal within-cluster sum
    of squares and ``labels`` are in the caller's original point order.

    Correctness rests on the contiguity property: in one dimension an optimal
    partition never interleaves clusters, so it suffices to choose k-1 split
    points among the sorted values.
    """
    order = np.argsort(x)
    xs = np.asarray(x, dtype=float)[order]
    n = xs.size
    cs, cs2 = _prefix_sums(xs)

    def sse(i: int, j: int) -> float:
        """Sum of squared deviations of xs[i:j] about its own mean."""
        m = j - i
        if m <= 0:
            return 0.0
        s = cs[j] - cs[i]
        return max(float(cs2[j] - cs2[i] - s * s / m), 0.0)

    cost = np.full((k + 1, n + 1), np.inf)
    split = np.zeros((k + 1, n + 1), dtype=int)
    cost[0, 0] = 0.0
    for c in range(1, k + 1):
        for j in range(1, n + 1):
            for i in range(c - 1, j):
                cand = cost[c - 1, i] + sse(i, j)
                if cand < cost[c, j]:
                    cost[c, j] = cand
                    split[c, j] = i

    sorted_labels = np.empty(n, dtype=int)
    j = n
    for c in range(k, 0, -1):
        i = split[c, j]
        sorted_labels[i:j] = c - 1
        j = i

    labels = np.empty(n, dtype=int)
    labels[order] = sorted_labels
    return float(cost[k, n]), labels


def audit(label: str, csv_path: str, max_k: int = DEFAULT_MAX_K) -> None:
    curve = pd.read_csv(csv_path)
    # The pipeline clusters log-latency; match it exactly.
    X = np.log(np.maximum(curve["latency_ns"].to_numpy(), 1e-6)).reshape(-1, 1)

    print(f"\n=== {label} ({len(X)} points, {csv_path}) ===")
    print(
        f"{'k':>2} {'WCSS Lloyd':>13} {'WCSS exact':>13} {'gap':>9} "
        f"{'Sil Lloyd':>10} {'Sil exact':>10}"
    )

    best_lloyd = (0, -1.0)
    best_exact = (0, -1.0)
    suboptimal: list[int] = []

    for k in range(2, min(max_k, len(X) - 1) + 1):
        lloyd = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=N_INIT).fit(X)
        exact_cost, exact_labels = exact_1d_kmeans(X.ravel(), k)

        gap = (lloyd.inertia_ - exact_cost) / max(exact_cost, 1e-12)
        if gap > 1e-9:
            suboptimal.append(k)

        sil_l = silhouette_score(X, lloyd.labels_, random_state=RANDOM_STATE)
        sil_e = silhouette_score(X, exact_labels, random_state=RANDOM_STATE)
        if sil_l > best_lloyd[1]:
            best_lloyd = (k, sil_l)
        if sil_e > best_exact[1]:
            best_exact = (k, sil_e)

        print(
            f"{k:>2} {lloyd.inertia_:>13.6f} {exact_cost:>13.6f} {gap:>8.2%} "
            f"{sil_l:>10.4f} {sil_e:>10.4f}"
        )

    print(
        f"\n  Lloyd is globally optimal at k = "
        f"{[k for k in range(2, max_k + 1) if k not in suboptimal]}"
    )
    print(f"  Lloyd is sub-optimal at   k = {suboptimal or 'none'}")
    print(
        f"  Selected level count: Lloyd k={best_lloyd[0]} (silhouette "
        f"{best_lloyd[1]:.4f}), exact k={best_exact[0]} "
        f"(silhouette {best_exact[1]:.4f})"
    )
    verdict = (
        "UNCHANGED -- the reported count is not a local-optimum artefact"
        if best_lloyd[0] == best_exact[0]
        else "CHANGED -- the reported count depends on the solver"
    )
    print(f"  => {verdict}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "curves",
        nargs="*",
        default=[
            "Apple M1=data/wss_curve.csv",
            "Intel i5-13450HX=data/intel_i5_13450hx/wss_curve.csv",
        ],
        help="LABEL=path/to/wss_curve.csv (repeatable)",
    )
    args = ap.parse_args()

    for spec in args.curves:
        label, _, path = spec.partition("=")
        audit(label or path, path or label)


if __name__ == "__main__":
    main()
