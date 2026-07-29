"""Tests for the level-discovery engine (change-point + clustering)."""
import numpy as np
import pytest

from autoecho.analysis import (
    LEVEL_NAMES,
    cluster_level_count,
    cluster_level_count_dbscan,
    detect_levels_changepoint,
    elbow_method,
    penalty_sensitivity,
)


def test_changepoint_finds_all_plateaus(make_curve):
    curve = make_curve([(64 * 1024, 2.0), (2 * 1024 * 1024, 8.0),
                        (16 * 1024 * 1024, 40.0), (256 * 1024 * 1024, 120.0)])
    levels = detect_levels_changepoint(curve, penalty=3.0)
    # Four distinct plateaus should be recovered.
    assert len(levels) == 4
    # Latencies must be strictly increasing across levels.
    med = levels["latency_ns_median"].tolist()
    assert med == sorted(med)


def test_changepoint_capacity_near_step(make_curve):
    cap = 256 * 1024
    curve = make_curve([(cap, 3.0), (64 * 1024 * 1024, 100.0)])
    levels = detect_levels_changepoint(curve, penalty=3.0)
    detected_cap = levels.iloc[0]["capacity_bytes"]
    # The detected first-level capacity should be within an octave of the step.
    assert abs(np.log2(detected_cap / cap)) < 1.0


def test_no_wpq_in_level_names():
    # WPQ is an Optane concept and must never appear in commodity level naming.
    assert not any("WPQ" in name for name in LEVEL_NAMES)


def test_boundaries_are_robust_percentiles(three_level_curve):
    levels = detect_levels_changepoint(three_level_curve)
    for _, row in levels.iterrows():
        assert row["latency_ns_p5"] <= row["latency_ns_median"] <= row["latency_ns_p95"]


def test_elbow_and_silhouette_return_valid_k(three_level_curve):
    k_elbow, curve = elbow_method(three_level_curve, max_k=6)
    assert 1 <= k_elbow <= 6
    assert len(curve) >= 2  # (k, inertia) pairs
    k_sil, score = cluster_level_count(three_level_curve, algorithm="kmeans")
    assert 2 <= k_sil <= 6
    assert -1.0 <= score <= 1.0


def test_dbscan_returns_nonnegative_count(three_level_curve):
    assert cluster_level_count_dbscan(three_level_curve) >= 0


def test_capacity_method_edge_is_default(three_level_curve):
    # The default estimator must be "edge" (unchanged behaviour); the alternatives
    # run without error and keep the same segmentation, only the capacity differs.
    base = detect_levels_changepoint(three_level_curve)
    edge = detect_levels_changepoint(three_level_curve, capacity_method="edge")
    assert (base["capacity_bytes"].fillna(-1).tolist()
            == edge["capacity_bytes"].fillna(-1).tolist())
    for m in ["onset", "hybrid", "midpoint"]:
        lv = detect_levels_changepoint(three_level_curve, capacity_method=m)
        assert len(lv) == len(edge)


def test_midpoint_is_geometric_mean_of_last_fit_and_first_miss(three_level_curve):
    """``midpoint`` must actually bisect the transition, not silently fall back to
    ``edge`` (dissertation §5.4, Table 19). It previously did fall through, which
    made the published midpoint column irreproducible from this code."""
    edge = detect_levels_changepoint(three_level_curve, capacity_method="edge")
    mid = detect_levels_changepoint(three_level_curve, capacity_method="midpoint")
    wss = three_level_curve["wss_bytes"].values

    assert len(mid) == len(edge)
    for i in range(len(edge) - 1):          # every level except DRAM has a capacity
        last_fit = edge["capacity_bytes"].iloc[i]
        first_miss = wss[wss > last_fit].min()
        assert mid["capacity_bytes"].iloc[i] == pytest.approx(
            np.sqrt(last_fit * first_miss))
        # A real bisection sits strictly between the two, hence above the edge.
        assert last_fit < mid["capacity_bytes"].iloc[i] < first_miss


def test_midpoint_degrades_to_edge_without_a_following_level():
    """With no next segment there is nothing to bisect, so the helper must return
    the edge rather than raise or invent a value."""
    from autoecho.analysis import _level_capacity
    wss = np.array([1000.0, 2000.0, 4000.0])
    lat = np.array([1.5, 1.5, 1.5])
    assert _level_capacity(wss, lat, "midpoint", next_wss=None) == 4000.0
    assert _level_capacity(wss, lat, "midpoint", next_wss=0) == 4000.0
    assert _level_capacity(wss, lat, "midpoint", next_wss=16000.0) == pytest.approx(8000.0)


def test_onset_helper_lands_on_flat_plateau_knee():
    from autoecho.analysis import _onset_capacity, _plateau_is_flat
    wss = np.array([1000.0, 2000.0, 4000.0, 8000.0])
    lat = np.array([1.5, 1.5, 1.5, 9.0])          # flat, then a sharp step
    assert _plateau_is_flat(lat[:3])              # the flat part is flat
    assert not _plateau_is_flat(lat)              # including the step, it is not
    assert _onset_capacity(wss, lat) == 4000.0    # onset = last size on the floor


def test_penalty_sensitivity_monotonic_trend(three_level_curve):
    sens = penalty_sensitivity(three_level_curve, penalties=[1.0, 5.0, 20.0])
    # Higher penalty must never yield MORE levels than a lower penalty.
    counts = [sens[p] for p in [1.0, 5.0, 20.0]]
    assert counts == sorted(counts, reverse=True) or len(set(counts)) == 1
