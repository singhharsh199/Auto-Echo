"""Comparative evaluation of the level-count estimators across repeated sweeps.

Satisfies the project-definition requirement to identify "which algorithm
combination performs most accurately and consistently" (Milestone 5). Each
estimator is scored on:
  * accuracy   -- does its level count match the expected number of levels?
  * stability  -- how much does that count vary across independent sweeps?
and, for change-point detection, the mean percentage error of the localised
cache capacities against hardware ground truth.
"""
from collections import Counter

import numpy as np
import pandas as pd

from autoecho.analysis import (
    changepoint_level_count,
    cluster_level_count,
    cluster_level_count_dbscan,
    detect_levels_changepoint,
    elbow_method,
)
from autoecho.validation import validate


def _counts_for_sweep(curve: pd.DataFrame, penalty: float = None) -> dict:
    # ``penalty`` is retained for signature compatibility but the change-point
    # entry uses the INDEPENDENT cost-knee counter, not the productive hybrid
    # (whose count is, by construction, the Silhouette count) -- otherwise the
    # comparison would be circular.
    k_kmeans, _ = cluster_level_count(curve, algorithm="kmeans")
    k_gmm, _ = cluster_level_count(curve, algorithm="gmm")
    return {
        "Change-point (cost-knee)": changepoint_level_count(curve),
        "K-Means + Silhouette": k_kmeans,
        "GMM + Silhouette": k_gmm,
        "K-Means + Elbow": elbow_method(curve)[0],
        "DBSCAN": cluster_level_count_dbscan(curve),
    }


def compare_methods(
    sweeps: list, ground_truth: dict, penalty: float = None
) -> pd.DataFrame:
    """Rank the estimators over one or more sweeps.

    :param sweeps: list of curve DataFrames (repeat runs for a stability signal).
    :param ground_truth: dict of documented cache sizes (from validation).
    :param penalty: retained for signature compatibility; the change-point entry
        uses the independent cost-knee counter regardless (see
        :func:`_counts_for_sweep`). Defaults to ``None`` to match the shipped CLI.
    :returns: DataFrame ranked best-first by (accuracy, stability).
    """
    # Expected visible plateaus = documented caches + 1 for DRAM. This is a lower
    # bound: a method may legitimately resolve an extra undocumented level (e.g.
    # the M1 SLC), so we score "count >= expected" as correct and flag extras.
    expected = len(ground_truth) + 1

    per_method = {}
    for curve in sweeps:
        for method, count in _counts_for_sweep(curve, penalty).items():
            per_method.setdefault(method, []).append(count)

    rows = []
    for method, counts in per_method.items():
        int_counts = [int(c) for c in counts]
        arr = np.array(int_counts, dtype=float)
        mean_c = float(arr.mean())
        std_c = float(arr.std())
        # The genuine MODE (most frequent count), not the rounded median -- the
        # median of e.g. [3, 5] is 4, a count that occurred in neither sweep.
        modal = int(Counter(int_counts).most_common(1)[0][0])
        # Quantified stability: fraction of sweeps whose count equals the mode
        # (1.0 = unanimous). This makes "unstable (2-5)" a number, not a phrase.
        agreement = round(sum(c == modal for c in int_counts) / len(int_counts), 3)
        # Correct if the modal count matches the expected number, allowing ONE
        # extra level for a genuinely undocumented tier (e.g. the M1 SLC that
        # sysctl does not report). Gross over-segmentation (many spurious knees)
        # is NOT rewarded -- the previous `modal >= expected` marked a 20-level
        # prediction as correct.
        correct = expected <= modal <= expected + 1
        rows.append(
            {
                "method": method,
                "mean_levels": round(mean_c, 2),
                "std_levels": round(std_c, 3),
                "modal_levels": modal,
                "modal_agreement": agreement,
                "expected": expected,
                "count_error": modal - expected,
                "count_ok": correct,
            }
        )

    df = pd.DataFrame(rows)
    # Rank: correct count first, then most stable (high agreement, low std), then
    # closest to expected.
    df["_dist"] = (df["modal_levels"] - expected).abs()
    df = df.sort_values(
        by=["count_ok", "modal_agreement", "std_levels", "_dist"],
        ascending=[False, False, True, True],
    ).drop(columns="_dist").reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)
    return df


def evaluate_lof_mitigation(penalty: float = 3.0) -> dict:
    """Empirically test the LOF outlier filter that Klimis et al. propose ([1, §8.1])
    as a mitigation for ambiguous timings, applied to the naive sample-based
    baseline it was intended for.

    Returns evidence for the dissertation's claim that the baseline's failure is
    *structural* (write-before-read + timer quantisation), not transient noise:
    LOF removes a fraction of points but the surviving latencies remain pinned to
    integer timer-tick multiples, so filtering cannot recover the hierarchy.
    """
    import numpy as np

    from autoecho.probe import collect
    from autoecho.preprocessing import remove_outliers_lof
    from autoecho.wss import get_timer_resolution_ns

    raw = collect(50000, 0)
    n_raw = len(raw)
    cleaned = remove_outliers_lof(raw, contamination=0.05)
    removed_frac = 1.0 - len(cleaned) / max(n_raw, 1)

    tick = get_timer_resolution_ns()
    vals = cleaned["latency_ns"].values
    # Fraction of cleaned samples lying within 10% of an integer tick multiple.
    nearest_mult = np.round(vals / tick) if tick > 0 else vals
    on_grid = np.mean(np.abs(vals - nearest_mult * tick) < 0.1 * tick) if tick > 0 else 0.0
    n_distinct = int(len(np.unique(np.round(vals / tick)))) if tick > 0 else len(np.unique(vals))

    return {
        "n_raw": n_raw,
        "lof_removed_fraction": float(removed_frac),
        "timer_tick_ns": float(tick),
        "fraction_on_timer_grid_after_lof": float(on_grid),
        "n_distinct_tick_levels_after_lof": n_distinct,
    }


def capacity_accuracy(sweeps: list, ground_truth: dict, penalty: float = None,
                      capacity_method: str = "edge") -> dict:
    """Mean absolute percentage error of change-point cache capacities vs ground
    truth, averaged over sweeps (change-point is the only estimator that
    localises capacities, not just counts).

    ``penalty`` defaults to ``None`` so this exercises the **same** productive
    hybrid path the CLI ships (Silhouette count + change-point localisation); an
    explicit value uses PELT at that penalty instead."""
    errs = []
    accs = []
    for curve in sweeps:
        levels = detect_levels_changepoint(curve, penalty=penalty,
                                           capacity_method=capacity_method)
        caps = levels["capacity_bytes"].dropna().tolist()
        # Reuse the caller's ground-truth reading instead of re-querying the OS.
        v = validate(caps, ground_truth=ground_truth)
        accs.append(v["accuracy"])
        for m in v["matches"]:
            if m["pct_error"] is not None and m["match"]:
                errs.append(abs(m["pct_error"]))
    return {
        "mean_accuracy": float(np.mean(accs)) if accs else 0.0,
        "mean_abs_pct_error": float(np.mean(errs)) if errs else None,
        "n_sweeps": len(sweeps),
    }
