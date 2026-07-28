# Auto-Echo Validation Report

**Machine:** 13th Gen Intel Core i5-13450HX (x86-64, Windows)

**Chase-buffer allocation:** default 4 KiB pages

## 1. Discovered Memory Hierarchy

| Level | Inferred capacity | Median latency | p5–p95 latency | WSS range | Points |
|---|---|---|---|---|---|
| **L1 Cache** | 55.7 KiB | 3.59 ns | 3.14–3.75 ns | 0–55 KiB | 70 |
| **L2 Cache** | 1.2 MiB | 10.88 ns | 10.30–15.46 ns | 59–1260 KiB | 45 |
| **L3 Cache** | 9.8 MiB | 64.30 ns | 44.58–104.36 ns | 1351–10085 KiB | 30 |
| **DRAM** | - | 188.23 ns | 140.90–228.70 ns | 10809–131072 KiB | 37 |

## 2. Level-Count Agreement Across Estimators

The productive hybrid discovered **4 levels** (count chosen by K-Means + Silhouette, boundaries localised by change-point). The estimators below are *independent* cross-checks of that count — the change-point row uses the cost-knee criterion, which is **not** seeded by the Silhouette k, so its agreement is genuine rather than circular.

| Estimator (independent) | Levels detected |
|---|---|
| Change-point (cost-knee) | 2 |
| K-Means + Silhouette | 4 (score 0.860) |
| K-Means + Elbow | 2 |
| GMM + Silhouette | 4 (score 0.835) |
| DBSCAN | 3 |

### 2.1 Change-Point Penalty Sensitivity

| Penalty | 1.0 | 2.0 | 3.0 | 4.0 | 6.0 | 8.0 | 10.0 |
|---|---|---|---|---|---|---|---|
| Levels | 5 | 4 | 4 | 4 | 4 | 4 | 4 |

## 3. Level-Count Estimator Comparison (Agreement & Stability)

Ranked over 1 independent sweeps by count correctness then stability (lower std = more consistent). Note: this ranks the level *counters*. The framework's productive pipeline uses the most accurate and stable counter — K-Means + Silhouette — to choose the number of levels, and change-point to *localise* each cache's capacity (see Section 4).

| Rank | Method | Mean levels | Std | Agreement | Modal | Expected | Count error | Count OK |
|---|---|---|---|---|---|---|---|---|
| 1 | K-Means + Silhouette | 4.0 | 0.0 | 1.0 | 4 | 4 | +0 | ✅ |
| 2 | GMM + Silhouette | 4.0 | 0.0 | 1.0 | 4 | 4 | +0 | ✅ |
| 3 | DBSCAN | 3.0 | 0.0 | 1.0 | 3 | 4 | -1 | ❌ |
| 4 | Change-point (cost-knee) | 2.0 | 0.0 | 1.0 | 2 | 4 | -2 | ❌ |
| 5 | K-Means + Elbow | 2.0 | 0.0 | 1.0 | 2 | 4 | -2 | ❌ |

## 4. Validation Against Hardware Ground Truth

**Recall:** 66.7% (2/3 documented caches found within a factor of 2). **Precision:** 66.7% (2/3 detected knees are documented caches; 1 false positive(s), e.g. TLB-transition artefacts). **F1:** 0.67.

Mean absolute capacity error (matched caches, 1 sweeps): **8.8%**.

| Cache | Ground truth | Detected | Error (octaves) | Error (%) | Match |
|---|---|---|---|---|---|
| L1 | 48 KiB | 56 KiB | 0.21 | +16.0% | ✅ |
| L2 | 1280 KiB | 1261 KiB | 0.02 | -1.5% | ✅ |
| L3 | 20480 KiB | — | — | — | ❌ |
