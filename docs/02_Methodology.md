# Auto-Echo Methodology

## 1. System Architecture
The Auto-Echo framework is designed as a modular Python pipeline that integrates low-level systems programming with high-level machine learning algorithms. The architecture is broadly divided into three stages:
1. **Data Collection (Probe)**
2. **Preprocessing (Noise Filtering)**
3. **Clustering & Discovery (Machine Learning)**

## 2. Memory Latency Data Collection (C-Extension)
To accurately measure memory access times at the nanosecond scale, pure Python is insufficient due to interpreter overhead and garbage collection. Auto-Echo implements the memory probe as a **Python C-Extension** (`src/autoecho/probe/probe.c`).

### The Echolocation Technique
The C-Extension allocates a large (e.g., 64MB) volatile byte array aligned to 64-byte cache line boundaries. During the measurement loop:
- The probe randomly accesses indices within the array.
- For `x86_64` architectures, it utilizes the `rdtscp` instruction to measure the exact CPU clock cycles elapsed during the load operation.
- For `arm64` architectures (e.g., Apple Silicon), it utilizes the `mach_absolute_time()` high-resolution timer.
- To induce fetches from deeper memory levels, the probe conditionally forces evictions by writing to the array and calling explicit flush instructions (e.g., `clflush` on x86) before timing the subsequent load.

This process records tens of thousands of latency "echoes", directly returning them to the Python runtime as a NumPy array, completely avoiding the I/O bottleneck of writing large intermediate CSV files to disk.

## 3. Data Preprocessing
Raw latency data is inherently noisy due to micro-architectural interference, context switching, and OS jitter. The `autoecho.preprocessing` module sanitizes this data:
- **Outlier Removal:** The framework provides filters using the Interquartile Range (IQR) method and the Local Outlier Factor (LOF). LOF is particularly effective at identifying density-based local anomalies in timing data. Extreme outliers (e.g., latencies > 1ms indicative of an OS interrupt) are aggressively pruned.
- **Smoothing:** A rolling moving average window is applied to the time-series data to smooth out transient noise spikes, leaving the dominant structural latencies intact.

## 4. Clustering and Model Selection Engine
The core innovation of Auto-Echo is removing the need for human-defined latency thresholds. The `autoecho.clustering` module employs Unsupervised Machine Learning to discover the natural groupings of memory latencies.

### Unsupervised Algorithms
The framework evaluates the 1-dimensional latency data using two primary algorithms:
1. **K-Means Clustering:** Efficiently partitions the latencies into $k$ distinct spherical clusters.
2. **Gaussian Mixture Models (GMM):** Models the latency distribution as a mixture of multiple Gaussian distributions, accommodating the varying variance often seen across different cache levels.

### Automatic Model Selection
To determine the true number of physical memory levels on the host machine without prior knowledge, the framework implements the **Silhouette Score** optimization method:
- The system iteratively fits K-Means and GMM models for $k \in [2, 6]$ clusters.
- For each $k$, it calculates the Silhouette Score, which measures how similar an object is to its own cluster compared to other clusters.
- The $k$ yielding the highest Silhouette Score is automatically selected as the optimal number of memory hierarchy levels.

### Result Mapping
Finally, the centroids (mean latencies) of the optimal $k$ clusters are sorted ascendingly. Based on their order, they are mapped to logical architectural components: L1 Cache, L2 Cache, L3 Cache, Write Pending Queue (WPQ) / Memory Controller, and DRAM.
