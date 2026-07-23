# Auto-Echo Validation Report

**Machine:** Apple M1 (arm64, Darwin)

## 1. Discovered Memory Hierarchy

| Level | Inferred capacity | Median latency | p5–p95 latency | WSS range | Points |
|---|---|---|---|---|---|
| **L1 Cache** | 157.5 KiB | 1.53 ns | 1.53–1.57 ns | 0–157 KiB | 75 |
| **L2 Cache** | 13.9 MiB | 9.19 ns | 8.73–22.73 ns | 168–14263 KiB | 65 |
| **DRAM** | - | 130.43 ns | 45.21–141.44 ns | 15286–262144 KiB | 42 |

## 2. Level-Count Agreement Across Estimators

The productive hybrid discovered **3 levels** (count chosen by K-Means + Silhouette, boundaries localised by change-point). The estimators below are *independent* cross-checks of that count — the change-point row uses the cost-knee criterion, which is **not** seeded by the Silhouette k, so its agreement is genuine rather than circular.

| Estimator (independent) | Levels detected |
|---|---|
| Change-point (cost-knee) | 3 |
| K-Means + Silhouette | 3 (score 0.894) |
| K-Means + Elbow | 3 |
| GMM + Silhouette | 3 (score 0.783) |
| DBSCAN | 3 |

### 2.1 Change-Point Penalty Sensitivity

| Penalty | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 10.0 |
|---|---|---|---|---|---|---|---|
| Levels | 6 | 6 | 4 | 4 | 4 | 3 | 3 |

## 3. Level-Count Estimator Comparison (Agreement & Stability)

Ranked over 3 independent sweeps by count correctness then stability (lower std = more consistent). Note: this ranks the level *counters*. The framework's productive pipeline uses the most accurate and stable counter — K-Means + Silhouette — to choose the number of levels, and change-point to *localise* each cache's capacity (see Section 4).

| Rank | Method | Mean levels | Std | Agreement | Modal | Expected | Count error | Count OK |
|---|---|---|---|---|---|---|---|---|
| 1 | Change-point (cost-knee) | 3.0 | 0.0 | 1.0 | 3 | 3 | +0 | ✅ |
| 2 | K-Means + Silhouette | 3.0 | 0.0 | 1.0 | 3 | 3 | +0 | ✅ |
| 3 | K-Means + Elbow | 3.0 | 0.0 | 1.0 | 3 | 3 | +0 | ✅ |
| 4 | DBSCAN | 3.33 | 0.471 | 0.667 | 3 | 3 | +0 | ✅ |
| 5 | GMM + Silhouette | 3.67 | 0.943 | 0.667 | 3 | 3 | +0 | ✅ |

## 4. Validation Against Hardware Ground Truth

**Recall:** 100.0% (2/2 documented caches found within a factor of 2). **Precision:** 100.0% (2/2 detected knees are documented caches; 0 false positive(s), e.g. TLB-transition artefacts). **F1:** 1.00.

Mean absolute capacity error (matched caches, 3 sweeps): **19.9%**.

| Cache | Ground truth | Detected | Error (octaves) | Error (%) | Match |
|---|---|---|---|---|---|
| L1 | 128 KiB | 158 KiB | 0.30 | +23.0% | ✅ |
| L2 | 12288 KiB | 14263 KiB | 0.22 | +16.1% | ✅ |
