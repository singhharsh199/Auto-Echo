# Auto-Echo Validation Report

**Machine:** Intel64 Family 6 Model 183 Stepping 1, GenuineIntel (AMD64, Windows)

## 1. Discovered Memory Hierarchy

| Level | Inferred capacity | Median latency | p5–p95 latency | WSS range | Points |
|---|---|---|---|---|---|
| **L1 Cache** | 55.7 KiB | 1.62 ns | 1.57–2.12 ns | 0–55 KiB | 70 |
| **L2 Cache** | 1.2 MiB | 5.15 ns | 4.77–7.10 ns | 59–1260 KiB | 45 |
| **L3 Cache** | 3.5 MiB | 29.12 ns | 17.70–54.14 ns | 1351–3565 KiB | 15 |
| **DRAM** | - | 143.46 ns | 105.19–153.43 ns | 3821–65536 KiB | 42 |

## 2. Level-Count Agreement Across Estimators

| Estimator | Levels detected |
|---|---|
| Change-point (auto) | 4 |
| K-Means + Silhouette | 4 (score 0.885) |
| K-Means + Elbow | 2 |
| GMM + Silhouette | 5 (score 0.842) |
| DBSCAN | 4 |

### 2.1 Change-Point Penalty Sensitivity

| Penalty | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 10.0 |
|---|---|---|---|---|---|---|---|
| Levels | 4 | 4 | 4 | 4 | 4 | 4 | 4 |

## 3. Level-Count Estimator Comparison (Agreement & Stability)

Ranked over 3 independent sweeps by count correctness then stability (lower std = more consistent). Note: this ranks the level *counters*. The framework's productive pipeline uses the most accurate and stable counter — K-Means + Silhouette — to choose the number of levels, and change-point to *localise* each cache's capacity (see Section 4).

| Rank | Method | Mean levels | Std (stability) | Modal | Expected | Count error | Count OK |
|---|---|---|---|---|---|---|---|
| 1 | GMM + Silhouette | 4.33 | 1.7 | 5 | 4 | +1 | ✅ |
| 2 | Change-point (cost-knee) | 2.0 | 0.0 | 2 | 4 | -2 | ❌ |
| 3 | K-Means + Elbow | 2.0 | 0.0 | 2 | 4 | -2 | ❌ |
| 4 | K-Means + Silhouette | 2.67 | 0.943 | 2 | 4 | -2 | ❌ |
| 5 | DBSCAN | 2.67 | 1.247 | 3 | 4 | -1 | ❌ |

## 4. Validation Against Hardware Ground Truth

Overall accuracy: **0.0%** (0/3 documented caches matched within a factor of 2).

| Cache | Ground truth | Detected | Error (octaves) | Error (%) | Match |
|---|---|---|---|---|---|
| L1 | 288 KiB | 1261 KiB | 2.13 | +337.7% | ❌ |
| L2 | 7680 KiB | 3566 KiB | 1.11 | -53.6% | ❌ |
| L3 | 20480 KiB | 3566 KiB | 2.52 | -82.6% | ❌ |
