# Auto-Echo Validation Report

**Machine:** 13th Gen Intel Core i5-13450HX (x86-64, Windows)

**Chase-buffer allocation:** 2 MiB large pages

## 1. Discovered Memory Hierarchy

| Level | Inferred capacity | Median latency | p5–p95 latency | WSS range | Points |
|---|---|---|---|---|---|
| **L1 Cache** | 55.7 KiB | 3.62 ns | 3.49–3.99 ns | 0–55 KiB | 70 |
| **L2 Cache** | 1.2 MiB | 11.02 ns | 10.42–15.74 ns | 59–1260 KiB | 45 |
| **L3 Cache** | 3.5 MiB | 65.38 ns | 48.14–85.73 ns | 1351–3565 KiB | 15 |
| **DRAM** | - | 174.51 ns | 161.30–180.16 ns | 3821–131072 KiB | 52 |

## 2. Level-Count Agreement Across Estimators

The productive hybrid discovered **4 levels** (count chosen by K-Means + Silhouette, boundaries localised by change-point). The estimators below are *independent* cross-checks of that count — the change-point row uses the cost-knee criterion, which is **not** seeded by the Silhouette k, so its agreement is genuine rather than circular.

| Estimator (independent) | Levels detected |
|---|---|
| Change-point (cost-knee) | 2 |
| K-Means + Silhouette | 4 (score 0.931) |
| K-Means + Elbow | 2 |
| GMM + Silhouette | 3 (score 0.880) |
| DBSCAN | 4 |

### 2.1 Change-Point Penalty Sensitivity

| Penalty | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 10.0 |
|---|---|---|---|---|---|---|---|
| Levels | 5 | 4 | 4 | 4 | 4 | 4 | 4 |

## 3. Level-Count Estimator Comparison (Agreement & Stability)

Ranked over 3 independent sweeps by count correctness then stability (lower std = more consistent). Note: this ranks the level *counters*. The framework's productive pipeline uses the most accurate and stable counter — K-Means + Silhouette — to choose the number of levels, and change-point to *localise* each cache's capacity (see Section 4).

| Rank | Method | Mean levels | Std | Agreement | Modal | Expected | Count error | Count OK |
|---|---|---|---|---|---|---|---|---|
| 1 | K-Means + Silhouette | 4.0 | 0.0 | 1.0 | 4 | 4 | +0 | ✅ |
| 2 | DBSCAN | 4.0 | 0.0 | 1.0 | 4 | 4 | +0 | ✅ |
| 3 | Change-point (cost-knee) | 2.0 | 0.0 | 1.0 | 2 | 4 | -2 | ❌ |
| 4 | K-Means + Elbow | 2.0 | 0.0 | 1.0 | 2 | 4 | -2 | ❌ |
| 5 | GMM + Silhouette | 4.67 | 2.357 | 0.667 | 3 | 4 | -1 | ❌ |

## 4. Validation Against Hardware Ground Truth

**Recall:** 66.7% (2/3 documented caches found within a factor of 2). **Precision:** 66.7% (2/3 detected knees are documented caches; 1 false positive(s), e.g. TLB-transition artefacts). **F1:** 0.67.

Mean absolute capacity error (matched caches, 3 sweeps): **8.8%**.

| Cache | Ground truth | Detected | Error (octaves) | Error (%) | Match |
|---|---|---|---|---|---|
| L1 | 48 KiB | 56 KiB | 0.21 | +16.0% | ✅ |
| L2 | 1280 KiB | 1261 KiB | 0.02 | -1.5% | ✅ |
| L3 | 20480 KiB | — | — | — | ❌ |
