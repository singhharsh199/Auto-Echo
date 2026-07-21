# Auto-Echo Validation Report

## 1. Discovered Memory Hierarchy

| Level | Inferred capacity | Median latency | p5–p95 latency | WSS range | Points |
|---|---|---|---|---|---|
| **L1 Cache** | 157.5 KiB | 1.55 ns | 1.53–1.93 ns | 0–157 KiB | 75 |
| **L2 Cache** | 7.0 MiB | 9.10 ns | 8.95–12.95 ns | 168–7131 KiB | 55 |
| **L3 Cache** | 13.9 MiB | 32.18 ns | 17.03–87.76 ns | 7643–14263 KiB | 10 |
| **DRAM** | - | 119.15 ns | 72.07–128.27 ns | 15286–65536 KiB | 22 |

## 2. Level-Count Agreement Across Estimators

| Estimator | Levels detected |
|---|---|
| Change-point (PELT) | 4 |
| K-Means + Silhouette | 3 (score 0.887) |
| K-Means + Elbow | 3 |
| GMM + Silhouette | 3 (score 0.869) |
| DBSCAN | 2 |

### 2.1 Change-Point Penalty Sensitivity

| Penalty | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 10.0 |
|---|---|---|---|---|---|---|---|
| Levels | 6 | 6 | 4 | 3 | 3 | 3 | 3 |

## 3. Level-Count Estimator Comparison (Agreement & Stability)

Ranked over 1 independent sweeps by count correctness then stability (lower std = more consistent). Note: the clustering estimators only *count* levels; change-point detection additionally *localises* each cache's capacity, so it is the productive method for hierarchy mapping (see Section 4).

| Rank | Method | Mean levels | Std (stability) | Modal | Expected ≥ | Count OK |
|---|---|---|---|---|---|---|
| 1 | K-Means + Silhouette | 3.0 | 0.0 | 3 | 3 | ✅ |
| 2 | GMM + Silhouette | 3.0 | 0.0 | 3 | 3 | ✅ |
| 3 | K-Means + Elbow | 3.0 | 0.0 | 3 | 3 | ✅ |
| 4 | Change-point (PELT) | 4.0 | 0.0 | 4 | 3 | ✅ |
| 5 | DBSCAN | 2.0 | 0.0 | 2 | 3 | ❌ |

## 4. Validation Against Hardware Ground Truth

Overall accuracy: **100.0%** (2/2 documented caches matched within a factor of 2).

Mean absolute capacity error (matched caches, 1 sweeps): **19.6%**.

| Cache | Ground truth | Detected | Error (octaves) | Error (%) | Match |
|---|---|---|---|---|---|
| L1 | 128 KiB | 158 KiB | 0.30 | +23.0% | ✅ |
| L2 | 12288 KiB | 14263 KiB | 0.22 | +16.1% | ✅ |
