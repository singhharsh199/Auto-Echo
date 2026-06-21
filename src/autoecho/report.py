import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

def plot_latency_distribution(df: pd.DataFrame, column: str = 'latency_ns', output_path: str = None):
    """
    Generate a 1D scatter plot of the latencies over time, mimicking Figure 7 from the paper.
    Colors the data points based on their assigned cluster.
    """
    plt.figure(figsize=(12, 6))
    
    if 'cluster' in df.columns:
        sns.scatterplot(data=df, x=column, y='access_index', hue='cluster', palette='viridis', s=10, alpha=0.5, legend='full')
    else:
        sns.scatterplot(data=df, x=column, y='access_index', color='blue', s=10, alpha=0.5)
        
    plt.xscale('log')
    plt.xlabel('Access Time (ns) [Log Scale]')
    plt.ylabel('Access Instance (Order)')
    plt.title('Memory Access Latencies Across Different Levels of the Hierarchy')
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_path}")
    else:
        plt.show()

def generate_report(cluster_stats: pd.DataFrame, output_path: str = None):
    """
    Generate a markdown report mapping latency ranges to inferred memory locations.
    """
    report = "# Auto-Echo Validation Report\n\n"
    report += "## Latency Ranges and Corresponding Memory Locations\n\n"
    
    report += "| Inferred Level | Latency Range [ns] | Mean Latency [ns] | Data Points |\n"
    report += "|---|---|---|---|\n"
    
    for _, row in cluster_stats.iterrows():
        level_name = row['Level_Name']
        min_ns = int(row['min'])
        max_ns = int(row['max'])
        mean_ns = row['mean']
        count = int(row['count'])
        report += f"| **{level_name}** | {min_ns} - {max_ns} | {mean_ns:.2f} | {count} |\n"
        
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)
        print(f"Report saved to {output_path}")
    else:
        print(report)
