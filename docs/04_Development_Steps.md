# Development Steps: Building Auto-Echo

This document outlines the step-by-step process undertaken to build the Auto-Echo framework from scratch.

## 1. Project Initialization & Architecture
- Initialized a modular Python package structure within the `src/` directory.
- Created the `setup.py` build script to define dependencies (`numpy`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`) and configure the compilation of the native C-extension.
- Created foundational directories (`tests/`, `data/`, `docs/`) to separate source code, datasets, and written documentation.

## 2. Implementing the Memory Latency Probe (Phase 1)
- **Objective:** Replicate the echolocation probe described in the "Shouting at Memory" paper to gather nanosecond-accurate access latencies.
- **Action:** Wrote a Python C-Extension (`src/autoecho/probe/probe.c`). Instead of writing massive CSV files to disk (which causes severe I/O bottlenecks), the extension loads directly into Python memory.
- **Hardware Abstraction:** The C code dynamically checks the system architecture. If compiled on an Intel machine, it utilizes inline assembly for `rdtscp` and `clflush`. For your Apple Silicon (M-series) Mac, it gracefully falls back to using macOS's native `mach_absolute_time()` to capture high-resolution hardware ticks.
- **Python Wrapper:** Created `src/autoecho/probe/__init__.py` to call the C-extension and convert the raw hardware ticks into a clean Pandas DataFrame in nanoseconds.

## 3. Data Preprocessing Pipeline (Phase 2)
- **Objective:** Clean the raw latency data, stripping away OS-level jitter and context-switching interference.
- **Action:** Implemented `src/autoecho/preprocessing.py`.
- **Filtering Algorithms:** Added functions to remove outliers using both the Interquartile Range (IQR) method and the Local Outlier Factor (LOF) as suggested by the literature.
- **Smoothing:** Applied a rolling window moving average to the time-series data to emphasize distinct latency plateaus.

## 4. Unsupervised ML Clustering Engine (Phase 3)
- **Objective:** Group the cleaned latencies into physical memory tiers (L1, L2, DRAM, etc.) without hardcoding latency thresholds.
- **Action:** Implemented `src/autoecho/clustering.py`.
- **Algorithms Used:** Utilized Scikit-Learn to apply K-Means and Gaussian Mixture Models (GMM) to the 1D latency data.
- **Automatic Model Selection:** Implemented an iterative search that tests different values of $k$ (number of clusters) from 2 to 6. For each $k$, the framework calculates the **Silhouette Score** and automatically selects the $k$ that yields the best mathematical separation. 
- **Mapping:** Added logic to extract the minimum and maximum latencies for each discovered cluster and map them ascendingly to logical names (L1 Cache, L2 Cache, etc.).

## 5. Reporting and Visualization (Phase 4)
- **Objective:** Present the findings clearly.
- **Action:** Wrote `src/autoecho/report.py`.
- **Visualization:** Used `matplotlib` and `seaborn` to generate a 1D scatterplot of the memory accesses, color-coded by their discovered cluster.
- **Reporting:** Implemented a function to output the validation results (latency ranges, mean latencies, and data point counts) into a markdown table.

## 6. End-to-End CLI Integration
- **Action:** Created the `src/autoecho/__main__.py` entry point.
- This ties the entire pipeline together so that the user can trigger data collection, preprocessing, clustering, and report generation sequentially using a single command: `python -m autoecho --samples 50000`.

## 7. Documentation
- **Action:** Drafted the `Literature Review`, `Methodology`, and generated the `Validation Report` into the `docs/` folder to provide the written foundation for the MSc dissertation.
