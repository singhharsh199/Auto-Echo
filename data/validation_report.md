# Auto-Echo Validation Report

**Machine:** Apple M1 (arm64, Darwin)

## 1. Discovered Memory Hierarchy

| Level | Inferred capacity | Median latency | p5–p95 latency | WSS range | Points |
|---|---|---|---|---|---|
| **L1 Cache** | 157.5 KiB | 1.53 ns | 1.53–1.57 ns | 0–157 KiB | 75 |
| **L2 Cache** | 9.8 MiB | 9.07 ns | 8.71–15.65 ns | 168–10085 KiB | 60 |
| **L3 Cache** | 19.7 MiB | 32.32 ns | 20.66–69.77 ns | 10809–20171 KiB | 10 |
| **DRAM** | - | 131.23 ns | 94.03–141.59 ns | 21618–262144 KiB | 37 |

## 2. Level-Count Agreement Across Estimators

| Estimator | Levels detected |
|---|---|
| Change-point (PELT) | 4 |
| K-Means + Silhouette | 3 (score 0.894) |
| K-Means + Elbow | 3 |
| GMM + Silhouette | 3 (score 0.783) |
| DBSCAN | 3 |

### 2.1 Change-Point Penalty Sensitivity

| Penalty | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 10.0 |
|---|---|---|---|---|---|---|---|
| Levels | 6 | 6 | 4 | 4 | 4 | 3 | 3 |

## 3. Level-Count Estimator Comparison (Agreement & Stability)

Ranked over 1 independent sweeps by count correctness then stability (lower std = more consistent). Note: the clustering estimators only *count* levels; change-point detection additionally *localises* each cache's capacity, so it is the productive method for hierarchy mapping (see Section 4).

| Rank | Method | Mean levels | Std (stability) | Modal | Expected | Count error | Count OK |
|---|---|---|---|---|---|---|---|
| 1 | K-Means + Silhouette | 3.0 | 0.0 | 3 | 3 | +0 | ✅ |
| 2 | GMM + Silhouette | 3.0 | 0.0 | 3 | 3 | +0 | ✅ |
| 3 | K-Means + Elbow | 3.0 | 0.0 | 3 | 3 | +0 | ✅ |
| 4 | DBSCAN | 3.0 | 0.0 | 3 | 3 | +0 | ✅ |
| 5 | Change-point (PELT) | 4.0 | 0.0 | 4 | 3 | +1 | ✅ |

## 4. Validation Against Hardware Ground Truth

Overall accuracy: **100.0%** (2/2 documented caches matched within a factor of 2).

Mean absolute capacity error (matched caches, 1 sweeps): **20.5%**.

| Cache | Ground truth | Detected | Error (octaves) | Error (%) | Match |
|---|---|---|---|---|---|
| L1 | 128 KiB | 158 KiB | 0.30 | +23.0% | ✅ |
| L2 | 12288 KiB | 10086 KiB | 0.28 | -17.9% | ✅ |
