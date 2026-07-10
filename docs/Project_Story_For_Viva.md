# Auto-Echo: Initial Architecture & Methodology
*A guide for your Professor / Viva Defense regarding the Phase 1 implementation*

This document breaks down the current state of the Auto-Echo project as it stands in this initial version. It explains the core architecture, the methodology used, and the challenges discovered during testing.

---

## 1. The Genesis: The Research Problem
**The Inspiration:** The project was inspired by recent systems-level research into empirical memory discovery, such as the Klimis ECOOP 2025 paper on Memory Echolocation. 
**The Goal:** The objective was to build a tool that could automatically discover a computer's memory hierarchy purely from user-space, without needing admin privileges or looking up hardware documentation.
**The Challenge:** Bridging highly precise, low-level systems programming (to measure nanosecond-level access times) with Unsupervised Machine Learning (to classify those raw timings into actual cache levels).

## 2. Building the Foundation: The Architecture
We built the fundamental pipeline into four distinct phases:

### Phase 1: The Probe (C-Extension)
*   **Goal:** Collect raw memory access latencies.
*   **Implementation:** We wrote a native C module (`probe.c`) that allocates an array in memory. It uses a `for` loop to sequentially read through the array and times how long the reads take using `clock_gettime` or `mach_absolute_time`.
*   **Cache Management:** We attempted to clear the cache between reads using the `clflush` assembly instruction to ensure we were getting fresh data rather than cached data.

### Phase 2: Data Preprocessing (Python)
*   **Goal:** Clean the noisy systems data before feeding it to the ML.
*   **Implementation:** We built `preprocessing.py` which applies three filters:
    1.  **IQR (Interquartile Range) Filtering:** To remove extreme timing spikes caused by the OS scheduling background tasks.
    2.  **LOF (Local Outlier Factor):** A density-based machine learning algorithm to remove isolated noisy points.
    3.  **Moving Average:** To smooth the final data curve.

### Phase 3: The Machine Learning Engine
*   **Goal:** Automatically classify the cleaned latencies into discrete cache levels (e.g., L1, L2, DRAM).
*   **Implementation:** We integrated the **K-Means clustering** algorithm. The framework dynamically tests multiple values of $K$ (from 2 to 6) and uses the **Silhouette Score** to mathematically determine which $K$ best separates the data points.

### Phase 4: Reporting
*   **Goal:** Present the findings.
*   **Implementation:** We created `report.py` to output the discovered clusters into a structured Markdown report (`data/validation_report.md`) and plot a PNG graph of the S-Curve.

---

## 3. Current Findings and Limitations (The Reality Check)
As we tested this initial architecture, we successfully built the end-to-end ML pipeline, but we discovered that the physical hardware on Apple Silicon (M-Series chips) behaves differently than traditional x86 machines, leading to flawed data collection.

If your professor asks about the limitations of this current phase, you can explain:

1. **Architecture Lock-in (`clflush`):** The `clflush` instruction used to manually clear caches is an x86-specific instruction. On ARM architectures like Apple Silicon, it is ignored in user-space, meaning our probe struggles to properly evict data from the cache.
2. **Hardware Prefetchers:** Because the C-probe reads the array sequentially (index 0, 1, 2...), the modern CPU prefetcher detects the pattern and pre-loads the data into the fast L1 cache before we even ask for it, which artificially hides the slower L2 and L3 latencies.
3. **Timer Quantization:** The system timer (`mach_absolute_time`) only updates roughly every 8 nanoseconds. Because an L1 cache hit only takes ~2-3ns, timing a single read operation results in heavily quantized numbers (e.g., snapping to 0ns, 8ns, 16ns) rather than a smooth latency curve.

### Next Steps / Conclusion
This initial architecture successfully demonstrates the integration of a C-based system probe with a Python unsupervised machine learning pipeline. The data cleaning and Silhouette Score selection function perfectly. The next phase of research would require pivoting the C-probe to a "pointer-chasing" sweep to defeat the hardware prefetchers and timer limits discovered in this phase.
