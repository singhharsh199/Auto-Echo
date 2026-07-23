import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os


def plot_memory_mountain(curve, levels=None, output_path=None, sweeps=None,
                         machine=None):
    """Plot the working-set-size latency curve (the 'memory mountain') with
    detected level plateaus shaded and inferred cache capacities marked.

    :param curve: DataFrame with ``wss_bytes`` / ``wss_kib`` and ``latency_ns``.
    :param levels: optional DataFrame from analysis.detect_levels_changepoint,
        used to shade plateaus and draw capacity boundaries.
    :param sweeps: optional list of per-run curve DataFrames; if given, a
        min–max variability band across runs is shaded to show measurement
        stability (error bars).
    :param machine: optional machine label (e.g. 'Apple M1 (arm64, Darwin)');
        rendered as a subtitle so the figure states which machine it is from.
    """
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 6.5))

    wss_kib = curve["wss_bytes"].values / 1024.0

    if sweeps is not None and len(sweeps) > 1:
        # All sweeps share the same deterministic WSS grid -> stack and band.
        mat = np.vstack([
            s.sort_values("wss_bytes")["latency_ns"].values for s in sweeps
        ])
        x = np.sort(curve["wss_bytes"].values) / 1024.0
        ax.fill_between(x, mat.min(axis=0), mat.max(axis=0), color="#1f4e79",
                        alpha=0.15, zorder=1,
                        label=f"min–max over {len(sweeps)} runs")

    ax.plot(wss_kib, curve["latency_ns"].values, "-o", color="#1f4e79",
            markersize=3, linewidth=1.2, zorder=3, label="Measured latency")

    band_colors = ["#ffcccc", "#c8e6c9", "#c7d8ff", "#f5d5c5", "#e0e0e0"]
    if levels is not None and not levels.empty:
        for i, row in levels.reset_index(drop=True).iterrows():
            lo = row["wss_lo_bytes"] / 1024.0
            hi = row["wss_hi_bytes"] / 1024.0
            ax.axvspan(lo, hi, color=band_colors[i % len(band_colors)], alpha=0.45,
                       zorder=1,
                       label=f"{row['level_name']} (~{row['latency_ns_median']:.1f} ns)")
            cap = row.get("capacity_bytes", float("nan"))
            if cap == cap:  # not NaN -> a real cache boundary
                ax.axvline(cap / 1024.0, color="#b00020", linestyle="--",
                           linewidth=1.2, zorder=2)
                # Stagger label heights so adjacent boundaries don't overlap.
                y_frac = 0.92 if i % 2 == 0 else 0.55
                ax.text(cap / 1024.0, ax.get_ylim()[1] * y_frac,
                        f"  {row['capacity_human']}", color="#b00020",
                        fontsize=8, rotation=90, va="top", ha="left")

    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("Working-set size (KiB) [log2]", fontsize=11, fontweight="bold")
    ax.set_ylabel("Average access latency (ns) [log]", fontsize=11, fontweight="bold")
    ax.set_title("Auto-Echo Memory Latency Curve (Pointer-Chase Sweep)",
                 fontsize=13, fontweight="bold", pad=22 if machine else 12)
    if machine:
        ax.text(0.5, 1.012, machine, transform=ax.transAxes, ha="center",
                va="bottom", fontsize=9.5, style="italic", color="#555555")
    ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=9)
    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to {output_path}")
    else:
        plt.show()
    plt.close()


def plot_model_selection(analysis, output_path=None, machine=None):
    """Plot the Elbow (K-Means inertia) and the Silhouette-score curves together,
    so both automatic model-selection criteria are actually shown and comparable
    (project definition: Elbow Method AND Silhouette Score, applied and compared).
    The Silhouette *curve* is drawn on a twin axis -- not merely marked with a
    vertical line at its peak.

    :param machine: optional machine label rendered as a subtitle so the figure
        states which machine it is from."""
    sns.set_theme(style="whitegrid")
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ks = [k for k, _ in analysis["elbow_curve"]]
    inertias = [v for _, v in analysis["elbow_curve"]]
    l1, = ax1.plot(ks, inertias, "-o", color="#1f4e79",
                   label="K-Means inertia (Elbow)")
    ax1.set_xlabel("Number of clusters k", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Within-cluster sum of squares (inertia)", fontsize=10,
                   color="#1f4e79")
    ax1.set_title("Automatic Model Selection: Elbow vs Silhouette",
                  fontsize=12, fontweight="bold", pad=22 if machine else 6)
    if machine:
        ax1.text(0.5, 1.012, machine, transform=ax1.transAxes, ha="center",
                 va="bottom", fontsize=9, style="italic", color="#555555")
    handles = [l1]
    # Silhouette score at each k on a twin y-axis (higher = better separation).
    sil = analysis.get("silhouette_curve") or []
    if sil:
        ax2 = ax1.twinx()
        l2, = ax2.plot([k for k, _ in sil], [s for _, s in sil], "-s",
                       color="#009E73", label="Silhouette score")
        ax2.set_ylabel("Silhouette score", fontsize=10, color="#009E73")
        ax2.grid(False)
        handles.append(l2)
    handles.append(ax1.axvline(analysis["n_levels_elbow"], color="#b00020",
                   linestyle="--", label=f"Elbow k = {analysis['n_levels_elbow']}"))
    handles.append(ax1.axvline(analysis["n_levels_kmeans"], color="#009E73",
                   linestyle=":",
                   label=f"Silhouette k = {analysis['n_levels_kmeans']}"))
    ax1.legend(handles=handles, loc="upper right", fontsize=9)
    plt.tight_layout()
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to {output_path}")
    else:
        plt.show()
    plt.close()


def generate_wss_report(levels, analysis, validation, output_path=None,
                        comparison=None, capacity_acc=None, machine=None):
    """Generate the Markdown validation report for the WSS methodology."""
    r = "# Auto-Echo Validation Report\n\n"
    if machine:
        r += f"**Machine:** {machine}\n\n"
    r += "## 1. Discovered Memory Hierarchy\n\n"
    r += "| Level | Inferred capacity | Median latency | p5–p95 latency | WSS range | Points |\n"
    r += "|---|---|---|---|---|---|\n"
    for _, row in levels.iterrows():
        r += (f"| **{row['level_name']}** | {row['capacity_human']} | "
              f"{row['latency_ns_median']:.2f} ns | "
              f"{row['latency_ns_p5']:.2f}–{row['latency_ns_p95']:.2f} ns | "
              f"{row['wss_lo_bytes']//1024}–{row['wss_hi_bytes']//1024} KiB | "
              f"{row['n_points']} |\n")

    r += "\n## 2. Level-Count Agreement Across Estimators\n\n"
    n_hybrid = analysis.get("n_levels_hybrid", analysis["n_levels_changepoint"])
    r += (f"The productive hybrid discovered **{n_hybrid} levels** (count chosen by "
          "K-Means + Silhouette, boundaries localised by change-point). The "
          "estimators below are *independent* cross-checks of that count — the "
          "change-point row uses the cost-knee criterion, which is **not** seeded "
          "by the Silhouette k, so its agreement is genuine rather than "
          "circular.\n\n")
    r += "| Estimator (independent) | Levels detected |\n|---|---|\n"
    r += f"| Change-point (cost-knee) | {analysis.get('n_levels_changepoint_independent', '—')} |\n"
    r += f"| K-Means + Silhouette | {analysis['n_levels_kmeans']} (score {analysis['silhouette_kmeans']:.3f}) |\n"
    r += f"| K-Means + Elbow | {analysis['n_levels_elbow']} |\n"
    r += f"| GMM + Silhouette | {analysis['n_levels_gmm']} (score {analysis['silhouette_gmm']:.3f}) |\n"
    r += f"| DBSCAN | {analysis['n_levels_dbscan']} |\n"

    ps = analysis.get("penalty_sensitivity")
    if ps:
        r += "\n### 2.1 Change-Point Penalty Sensitivity\n\n"
        r += "| Penalty | " + " | ".join(str(p) for p in ps) + " |\n"
        r += "|---|" + "---|" * len(ps) + "\n"
        r += "| Levels | " + " | ".join(str(v) for v in ps.values()) + " |\n"

    if comparison is not None:
        r += "\n## 3. Level-Count Estimator Comparison (Agreement & Stability)\n\n"
        r += "Ranked over " + (f"{capacity_acc['n_sweeps']} independent sweeps" if capacity_acc else "the sweep")
        r += " by count correctness then stability (lower std = more consistent). "
        r += ("Note: this ranks the level *counters*. The framework's productive "
              "pipeline uses the most accurate and stable counter — K-Means + "
              "Silhouette — to choose the number of levels, and change-point to "
              "*localise* each cache's capacity (see Section 4).\n\n")
        r += ("| Rank | Method | Mean levels | Std | Agreement | Modal | Expected "
              "| Count error | Count OK |\n")
        r += "|---|---|---|---|---|---|---|---|---|\n"
        for _, row in comparison.iterrows():
            agree = row.get("modal_agreement", "—")
            r += (f"| {row['rank']} | {row['method']} | {row['mean_levels']} | "
                  f"{row['std_levels']} | {agree} | {row['modal_levels']} | "
                  f"{row['expected']} | {row['count_error']:+d} | "
                  f"{'✅' if row['count_ok'] else '❌'} |\n")

    r += "\n## 4. Validation Against Hardware Ground Truth\n\n"
    recall = validation.get("recall", validation["accuracy"])
    r += (f"**Recall:** {recall*100:.1f}% "
          f"({validation['n_matched']}/{validation['n_ground_truth']} documented "
          "caches found within a factor of 2). ")
    if "precision" in validation:
        r += (f"**Precision:** {validation['precision']*100:.1f}% "
              f"({validation['n_matched']}/{validation.get('n_detected', validation['n_matched'])} "
              f"detected knees are documented caches; "
              f"{validation.get('n_false_positive', 0)} false positive(s), e.g. "
              f"TLB-transition artefacts). **F1:** {validation.get('f1', 0.0):.2f}.")
    r += "\n"
    if capacity_acc and capacity_acc.get("mean_abs_pct_error") is not None:
        r += (f"\nMean absolute capacity error (matched caches, "
              f"{capacity_acc['n_sweeps']} sweeps): "
              f"**{capacity_acc['mean_abs_pct_error']:.1f}%**.\n")
    r += "\n| Cache | Ground truth | Detected | Error (octaves) | Error (%) | Match |\n"
    r += "|---|---|---|---|---|---|\n"
    for m in validation["matches"]:
        det = f"{m['detected_bytes']/1024:.0f} KiB" if m["detected_bytes"] else "—"
        err = f"{m['error_octaves']:.2f}" if m["error_octaves"] is not None else "—"
        pct = f"{m['pct_error']:+.1f}%" if m.get("pct_error") is not None else "—"
        r += (f"| {m['cache']} | {m['ground_truth_bytes']/1024:.0f} KiB | {det} | "
              f"{err} | {pct} | {'✅' if m['match'] else '❌'} |\n")

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(r)
        print(f"Report saved to {output_path}")
    else:
        print(r)

def plot_latency_distribution(df: pd.DataFrame, cluster_stats: pd.DataFrame = None, column: str = 'latency_ns', output_path: str = None):
    """
    Generate a 1D scatter plot of memory access latencies over time with shaded background bands
    for each discovered memory hierarchy level, matching Figure 7 from the ECOOP 2025 paper.
    """
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(12, 6.5))
    
    # Standard colors for shaded region bands (matching Figure 7 from the paper)
    band_colors = [
        '#ffcccc', # L1 Cache (Light Red / Pink)
        '#c8e6c9', # L2 Cache (Light Green)
        '#c7d8ff', # L3 Cache (Light Blue)
        '#e1bee7', # DRAM / Memory Controller (Light Purple)
        '#f5d5c5', # DRAM (Light Brown / Salmon)
        '#e0e0e0'  # Swap / OS Overhead (Light Gray)
    ]
    
    if cluster_stats is None and 'level_name' in df.columns:
        cluster_stats = df.groupby('level_name')[column].agg(['min', 'max', 'mean', 'count']).reset_index()
        cluster_stats['Level_Name'] = cluster_stats['level_name']
        cluster_stats = cluster_stats.sort_values(by='mean').reset_index(drop=True)
        
    if cluster_stats is not None and not cluster_stats.empty:
        stats_sorted = cluster_stats.sort_values(by='mean').reset_index(drop=True)
        num_tiers = len(stats_sorted)
        means = stats_sorted['mean'].values
        mins = stats_sorted['min'].values
        maxs = stats_sorted['max'].values
        
        # Calculate contiguous boundaries between clusters for continuous shaded bands
        bounds = []
        for i in range(num_tiers):
            if i == 0:
                left = max(0.1, min(mins[0] * 0.85, mins[0] - 2.0) if mins[0] > 0 else 0.1)
            else:
                left = (means[i-1] + means[i]) / 2.0
                
            if i == num_tiers - 1:
                right = max(maxs[-1] * 1.15, maxs[-1] + 5.0)
            else:
                right = (means[i] + means[i+1]) / 2.0
                
            bounds.append((left, right))
            
        for idx, row in stats_sorted.iterrows():
            level_name = row['Level_Name']
            color = band_colors[idx % len(band_colors)]
            left_b, right_b = bounds[idx]
            ax.axvspan(left_b, right_b, color=color, alpha=0.6, label=level_name, zorder=1)
            
    # Scatter plot of blue points over shaded regions
    valid_mask = df[column] > 0
    plot_df = df[valid_mask] if valid_mask.any() else df
    
    ax.scatter(plot_df[column], plot_df['access_index'], color='blue', s=2, alpha=0.5, zorder=2, label='_nolegend_')
    
    ax.set_xscale('log')
    min_x = max(0.5, plot_df[column].min() * 0.85)
    max_x = plot_df[column].max() * 1.15
    ax.set_xlim(min_x, max_x)
    
    from matplotlib.ticker import ScalarFormatter
    ax.xaxis.set_major_formatter(ScalarFormatter())
    
    # Select clean tick values within the data range
    possible_ticks = [1, 2, 5, 8, 10, 15, 20, 25, 33, 40, 50, 60, 75, 100]
    ticks = [t for t in possible_ticks if min_x <= t <= max_x]
    if ticks:
        ax.set_xticks(ticks)
        
    ax.set_xlabel('Access Time (ns) [Log Scale]', fontsize=11, fontweight='bold')
    ax.set_ylabel('Access Instance', fontsize=11, fontweight='bold')
    ax.set_title('Memory Access Latencies Across Different Levels of the Hierarchy', fontsize=13, fontweight='bold', pad=12)
    
    # Custom Legend matching Figure 7
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, loc='upper left', frameon=True, framealpha=0.9, fontsize=9)
        
    plt.tight_layout()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_path}")
    else:
        plt.show()
    plt.close()

def generate_report(cluster_stats: pd.DataFrame, output_path: str = None):
    """
    Generate a markdown report mapping latency ranges to inferred memory locations.
    """
    report = "# Auto-Echo Validation Report\n\n"
    report += "## Discovered Latency Ranges and Memory Hierarchy Tiers\n\n"
    
    report += "| Inferred Memory Tier | Latency Range [ns] | Mean Latency [ns] | Sample Count |\n"
    report += "|---|---|---|---|\n"
    
    for _, row in cluster_stats.iterrows():
        level_name = row['Level_Name']
        min_ns = int(row['min'])
        max_ns = int(row['max'])
        mean_ns = row['mean']
        count = int(row['count'])
        report += f"| **{level_name}** | {min_ns} - {max_ns} ns | {mean_ns:.2f} ns | {count} |\n"
        
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'w', encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {output_path}")
    else:
        print(report)

