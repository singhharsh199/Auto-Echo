import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

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
        '#e1bee7', # WPQ / Memory Controller (Light Purple)
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
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
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
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)
        print(f"Report saved to {output_path}")
    else:
        print(report)

