"""Level-discovery engine for the working-set-size latency curve.

Two complementary, unsupervised approaches are provided and reconciled:

1. Change-point detection (primary). A cache of capacity C keeps latency flat
   while the working set fits (wss <= C) and steps up once it overflows. The
   number of memory levels therefore equals the number of plateaus in the
   latency-vs-log(wss) curve, and each cache's capacity is the working-set size
   at the plateau-to-rise transition. This is detected with the ``ruptures``
   PELT algorithm on the log-latency signal, which auto-selects the number of
   breakpoints. Working on log-latency (not raw ns) keeps the small L1->L2 step
   and the large L2->DRAM step comparable in magnitude.

2. Clustering (K-Means / GMM / DBSCAN) of the per-size latency values, with the
   number of clusters chosen by the Silhouette Score. This satisfies the
   project's unsupervised-ML objective and provides an independent estimate of
   the level count to cross-check against (1).

Boundaries use robust percentile statistics rather than raw min/max, so a
single mis-measured point cannot drag a cache boundary.
"""
import warnings

import numpy as np
import pandas as pd
from scipy.signal import medfilt
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture

import ruptures as rpt

warnings.filterwarnings("ignore")

# Latency-ordered cache names. The deepest level is always relabelled "DRAM", so
# "DRAM" is deliberately NOT in this list -- otherwise a run with more plateaus
# than names would emit two "DRAM" rows. No "WPQ" (a persistent-memory concept
# from Klimis et al.'s Optane setup that does not exist on a commodity CPU cache
# hierarchy). Cache levels beyond this list get a generic "Ln Cache" name.
LEVEL_NAMES = ["L1 Cache", "L2 Cache", "L3 Cache", "L4 Cache", "L5 Cache"]

# Single search ceiling for the number of levels, shared by every model-selection
# routine (K-Means/GMM silhouette, elbow, change-point cost-knee, and the
# productive hybrid) so the count that drives discovery and the counts reported
# for cross-check search the same k range.
DEFAULT_MAX_K = 8


def _human_bytes(n: float) -> str:
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if abs(n) < 1024.0:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TiB"


def _plateau_is_flat(lat, tol: float = 0.15) -> bool:
    """True if a plateau's latency spread (p90/p10) is within ``tol`` (i.e. the
    plateau is genuinely flat, not sloping). The onset estimator is only
    meaningful on a flat plateau."""
    lo = float(np.percentile(lat, 10))
    hi = float(np.percentile(lat, 90))
    return lo > 0 and (hi / lo - 1.0) <= tol


def _onset_capacity(wss, lat, tau: float = 0.15, floor_pct: int = 10) -> float:
    """Capacity as the *onset* of the rise: the last size still on the plateau
    floor before latency first departs it by ``tau``. Exact on a flat plateau
    with a sharp knee; use only when :func:`_plateau_is_flat`."""
    floor = float(np.percentile(lat, floor_pct))
    thresh = floor * (1.0 + tau)
    onset = float(wss[0])
    for w, x in zip(wss, lat):
        if x <= thresh:
            onset = float(w)
        else:
            break  # first sustained departure
    return onset


def _level_capacity(wss, lat, method: str) -> float:
    """Estimate a cache's capacity from its plateau's working-set sizes/latencies.

    ``edge`` (default): the plateau's upper edge -- stable, but biased +16-23%
    upward (soft-knee effect). ``onset``: the departure point -- exact on flat
    plateaus, catastrophic on sloping ones. ``hybrid``: onset on a flat plateau,
    edge otherwise -- recovers the nominal size where the knee is sharp (e.g. the
    M1 L1) without the onset's instability elsewhere. See the §6.5
    capacity-estimator comparison."""
    wss = np.asarray(wss, dtype=float)
    lat = np.asarray(lat, dtype=float)
    if method == "onset":
        return _onset_capacity(wss, lat)
    if method == "hybrid":
        return _onset_capacity(wss, lat) if _plateau_is_flat(lat) else float(wss.max())
    return float(wss.max())  # "edge" (default)


def _knee_index(xs, ys) -> int:
    """Index of the knee of ``(xs, ys)``: the point of maximum perpendicular
    distance from the chord joining the first and last points, on min-max
    normalised axes (the standard parameter-free knee/elbow heuristic)."""
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    x = (xs - xs.min()) / (np.ptp(xs) or 1.0)
    y = (ys - ys.min()) / ((ys.max() - ys.min()) or 1.0)
    x1, y1, x2, y2 = x[0], y[0], x[-1], y[-1]
    denom = np.hypot(y2 - y1, x2 - x1) or 1.0
    dist = np.abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / denom
    return int(np.argmax(dist))


def _auto_segments(curve, signal, kmax: int = DEFAULT_MAX_K, min_size: int = 3):
    """Architecture-agnostic automatic segmentation, returning breakpoints
    (segment end indices, last == n) with no manual penalty.

    The NUMBER of levels is chosen by K-Means + Silhouette on the per-size
    latency values. Empirically this is the most accurate and stable level
    counter across architectures: it recovers the four L1/L2/L3/DRAM plateaus on
    x86 (Intel/AMD), three on Apple M1 (where the 12 MiB L2 and the ~8 MiB SLC
    blur into one band), and two on a virtualised host -- because it counts
    distinct latency *levels* directly and is unaffected by how unevenly the
    inter-level latency jumps are spaced. A penalty- or cost-knee-based count, by
    contrast, is biased by the largest jump and under-counts a well-separated
    x86 hierarchy.

    The BOUNDARIES are then localised by change-point detection constrained to
    exactly that many segments (dynamic programming with k-1 breakpoints). This
    realises the design principle *clustering counts the levels, change-point
    localises their capacities* directly, and needs no penalty hyper-parameter."""
    k, _ = cluster_level_count(curve, max_k=kmax, algorithm="kmeans")
    k = max(1, min(k, len(signal) // max(min_size, 1)))
    if k <= 1:
        return [len(signal)]
    return rpt.Dynp(model="l2", min_size=min_size).fit(signal).predict(n_bkps=k - 1)


def detect_levels_changepoint(
    curve: pd.DataFrame,
    penalty: float | None = None,
    min_size: int = 3,
    merge_ratio: float = 1.4,
    smooth_kernel: int = 3,
    kmax: int = DEFAULT_MAX_K,
    capacity_method: str = "edge",
) -> pd.DataFrame:
    """Detect memory levels as plateaus in the latency curve.

    :param curve: DataFrame with ``wss_bytes`` and ``latency_ns`` columns,
        sorted by ``wss_bytes``.
    :param penalty: PELT penalty on the log-latency signal (higher = fewer,
        coarser segments). If ``None`` (the default), the level count is chosen
        **automatically and architecture-agnostically** by K-Means + Silhouette
        and the boundaries are localised by change-point constrained to that
        count, with no manual penalty (see :func:`_auto_segments`). An explicit
        value is still honoured -- used by :func:`penalty_sensitivity` and the
        CLI ``--penalty`` override.
    :param merge_ratio: adjacent plateaus whose latency ratio is below this are
        merged (they represent the same physical level, over-segmented by noise).
    :returns: one row per detected level with ``level_name``, latency
        statistics, and ``capacity_bytes`` (the wss at which this level's cache
        overflows -- i.e. the inferred cache capacity; NaN for the final/DRAM
        level, which has no upper cache boundary).
    """
    curve = curve.sort_values("wss_bytes").reset_index(drop=True)
    y = curve["latency_ns"].values.astype(float)

    # Light median smoothing is appropriate here: unlike the i.i.d. sample path,
    # this is a genuine ordered sweep curve, so neighbours share a level.
    k = smooth_kernel if smooth_kernel % 2 == 1 else smooth_kernel + 1
    if len(y) >= k:
        y = medfilt(y, kernel_size=k)

    signal = np.log(np.maximum(y, 1e-6)).reshape(-1, 1)

    if penalty is None:
        # Automatic, architecture-agnostic model selection: K-Means+Silhouette
        # counts the levels, change-point localises them (see _auto_segments).
        bkps = _auto_segments(curve, signal, kmax=kmax, min_size=min_size)
    else:
        algo = rpt.Pelt(model="l2", min_size=min_size).fit(signal)
        bkps = algo.predict(pen=penalty)  # segment ends (exclusive), last == n

    # Build [start, end) segments.
    segments = []
    start = 0
    for end in bkps:
        segments.append((start, end))
        start = end

    # Robust per-segment latency (median), then merge look-alike neighbours.
    def seg_latency(seg):
        return float(np.median(curve["latency_ns"].values[seg[0]:seg[1]]))

    merged = [segments[0]]
    for seg in segments[1:]:
        prev = merged[-1]
        if seg_latency(seg) / max(seg_latency(prev), 1e-9) < merge_ratio:
            merged[-1] = (prev[0], seg[1])  # same level -> extend
        else:
            merged.append(seg)

    n_levels = len(merged)
    rows = []
    for i, (s, e) in enumerate(merged):
        lat = curve["latency_ns"].values[s:e]
        wss = curve["wss_bytes"].values[s:e]
        if i == n_levels - 1:
            name = "DRAM"  # the deepest level is always main memory
        elif i < len(LEVEL_NAMES):
            name = LEVEL_NAMES[i]
        else:
            name = f"L{i + 1} Cache"
        # Capacity of this level's cache (NaN for the final/DRAM level). The
        # estimator is selectable; "edge" (default) is the plateau's upper edge.
        capacity = (_level_capacity(wss, lat, capacity_method)
                    if i < n_levels - 1 else float("nan"))
        rows.append(
            {
                "level_name": name,
                "capacity_bytes": capacity,
                "capacity_human": _human_bytes(capacity) if capacity == capacity else "-",
                "latency_ns_median": float(np.median(lat)),
                "latency_ns_p5": float(np.percentile(lat, 5)),
                "latency_ns_p95": float(np.percentile(lat, 95)),
                "wss_lo_bytes": int(wss.min()),
                "wss_hi_bytes": int(wss.max()),
                "n_points": int(e - s),
            }
        )
    return pd.DataFrame(rows)


def cluster_level_count(
    curve: pd.DataFrame, max_k: int = DEFAULT_MAX_K, algorithm: str = "kmeans"
) -> tuple[int, float]:
    """Independent estimate of the number of levels by clustering the per-size
    latency values. Returns ``(best_k, best_silhouette)``.

    Clustering is performed on log-latency so that widely separated levels
    (L1 ~1.5 ns vs DRAM ~130 ns) do not swamp the finer L1/L2 gap."""
    X = np.log(np.maximum(curve["latency_ns"].values, 1e-6)).reshape(-1, 1)
    n = len(X)
    best_k, best_score = 1, -1.0

    for k in range(2, min(max_k, n - 1) + 1):
        if algorithm == "kmeans":
            labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)
        elif algorithm == "gmm":
            labels = GaussianMixture(n_components=k, random_state=42).fit_predict(X)
        else:
            raise ValueError(f"unknown algorithm {algorithm!r}")
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(X, labels, random_state=42)
        if score > best_score:
            best_k, best_score = k, score
    return best_k, best_score


def elbow_method(curve: pd.DataFrame, max_k: int = DEFAULT_MAX_K) -> tuple:
    """Estimate the number of levels by the Elbow Method on K-Means inertia
    (within-cluster sum of squares) over log-latency.

    The elbow is located automatically as the point of maximum distance from the
    chord joining the first and last (k, inertia) points -- the standard
    knee-detection heuristic, removing the manual "look at the plot" step.

    :returns: ``(elbow_k, [(k, inertia), ...])``.
    """
    X = np.log(np.maximum(curve["latency_ns"].values, 1e-6)).reshape(-1, 1)
    n = len(X)
    ks = list(range(1, min(max_k, n - 1) + 1))
    inertias = []
    for k in ks:
        inertias.append(
            float(KMeans(n_clusters=k, random_state=42, n_init=10).fit(X).inertia_)
        )
    if len(ks) < 3:
        return (ks[-1] if ks else 1), list(zip(ks, inertias))

    ks_a = np.array(ks, dtype=float)
    iner = np.array(inertias, dtype=float)
    # Normalise both axes to [0, 1] so the distance metric is scale-free.
    x = (ks_a - ks_a.min()) / (np.ptp(ks_a) or 1.0)
    y = (iner - iner.min()) / ((iner.max() - iner.min()) or 1.0)
    x1, y1, x2, y2 = x[0], y[0], x[-1], y[-1]
    denom = np.hypot(y2 - y1, x2 - x1) or 1.0
    dist = np.abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / denom
    elbow_k = int(ks_a[int(np.argmax(dist))])
    return elbow_k, list(zip(ks, inertias))


def penalty_sensitivity(curve: pd.DataFrame, penalties=None) -> dict:
    """Report the detected level count across a range of PELT penalties, to show
    the result is not an artefact of one hyper-parameter choice."""
    if penalties is None:
        penalties = [1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0]
    return {p: len(detect_levels_changepoint(curve, penalty=p)) for p in penalties}


def cluster_level_count_dbscan(curve: pd.DataFrame, eps: float = 0.3) -> int:
    """Density-based level-count estimate (DBSCAN). Unlike K-Means/GMM it does
    not need the number of clusters in advance and treats sparse transition
    points as noise. ``eps`` is in log-latency units."""
    X = np.log(np.maximum(curve["latency_ns"].values, 1e-6)).reshape(-1, 1)
    labels = DBSCAN(eps=eps, min_samples=3).fit_predict(X)
    return len(set(labels) - {-1})  # exclude noise label


def changepoint_level_count(
    curve: pd.DataFrame, kmax: int = DEFAULT_MAX_K, min_size: int = 3,
    smooth_kernel: int = 3,
) -> int:
    """Independent change-point estimate of the level *count*, via the knee of
    the segmentation cost curve J(K) (Lavielle's criterion; exact K-segment fits
    by dynamic programming on the smoothed log-latency signal).

    Reported in the estimator comparison to show *why* change-point is used only
    to localise levels, not to count them: on a well-separated x86 L1/L2/L3/DRAM
    hierarchy this cost-knee under-counts (it is biased toward the single largest
    latency jump), whereas K-Means + Silhouette counts correctly on every
    architecture. Kept independent of the productive hybrid so the comparison is
    not circular (the hybrid's count is, by construction, the Silhouette count)."""
    curve = curve.sort_values("wss_bytes").reset_index(drop=True)
    y = curve["latency_ns"].values.astype(float)
    k = smooth_kernel if smooth_kernel % 2 == 1 else smooth_kernel + 1
    if len(y) >= k:
        y = medfilt(y, kernel_size=k)
    signal = np.log(np.maximum(y, 1e-6)).reshape(-1, 1)
    n = len(signal)
    kmax = max(2, min(kmax, n // max(min_size, 1)))
    algo = rpt.Dynp(model="l2", min_size=min_size).fit(signal)
    ks, costs = [], []
    for K in range(1, kmax + 1):
        try:
            bkps = algo.predict(n_bkps=K - 1)
        except Exception:
            break
        ks.append(K)
        costs.append(float(algo.cost.sum_of_costs(bkps)))
    if len(ks) < 3:
        return ks[-1] if ks else 1
    return ks[_knee_index(ks, costs)]


def silhouette_curve(curve: pd.DataFrame, max_k: int = DEFAULT_MAX_K) -> list:
    """Silhouette score at each candidate k, over log-latency. Returned so the
    model-selection figure can plot the actual Silhouette curve (and the k it
    peaks at) rather than only marking the chosen k with a line."""
    X = np.log(np.maximum(curve["latency_ns"].values, 1e-6)).reshape(-1, 1)
    n = len(X)
    out = []
    for k in range(2, min(max_k, n - 1) + 1):
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)
        if len(set(labels)) < 2:
            continue
        out.append((k, float(silhouette_score(X, labels, random_state=42))))
    return out


def analyze(curve: pd.DataFrame, penalty: float | None = None,
            capacity_method: str = "edge") -> dict:
    """Run the full level-discovery analysis and reconcile the estimators.

    ``penalty=None`` (default) selects the *number* of levels by K-Means +
    Silhouette and localises their boundaries by change-point (the productive
    hybrid; see :func:`detect_levels_changepoint`). An explicit penalty overrides
    this with PELT at that penalty. The estimator cross-check additionally reports
    an **independent** change-point count via the cost-knee criterion
    (:func:`changepoint_level_count`), which is *not* seeded by the Silhouette k,
    so the agreement it shows is genuine rather than circular."""
    levels = detect_levels_changepoint(curve, penalty=penalty,
                                       capacity_method=capacity_method)
    k_kmeans, sil_kmeans = cluster_level_count(curve, algorithm="kmeans")
    k_gmm, sil_gmm = cluster_level_count(curve, algorithm="gmm")
    k_dbscan = cluster_level_count_dbscan(curve)
    k_elbow, elbow_curve = elbow_method(curve)
    k_cp_independent = changepoint_level_count(curve)

    return {
        "levels": levels,
        # The productive hybrid's level count (Silhouette-counted, change-point
        # localised) -- this is the number of levels actually discovered.
        "n_levels_hybrid": len(levels),
        "n_levels_changepoint": len(levels),  # kept as alias for compatibility
        # Independent change-point count (cost-knee); NOT the hybrid's Silhouette
        # count, so it is a genuine cross-check in the report's estimator table.
        "n_levels_changepoint_independent": k_cp_independent,
        "n_levels_kmeans": k_kmeans,
        "silhouette_kmeans": sil_kmeans,
        "n_levels_gmm": k_gmm,
        "silhouette_gmm": sil_gmm,
        "n_levels_dbscan": k_dbscan,
        "n_levels_elbow": k_elbow,
        "elbow_curve": elbow_curve,
        "silhouette_curve": silhouette_curve(curve),
        "penalty_sensitivity": penalty_sensitivity(curve),
    }
