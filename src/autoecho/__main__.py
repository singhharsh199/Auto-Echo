import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Auto-Echo: Automated Discovery of Memory Hierarchy Latency Patterns")
    parser.add_argument("--samples", type=int, default=50000, help="Number of memory access samples to collect")
    parser.add_argument("--output-dir", type=str, default="data", help="Directory to save plots and reports")
    parser.add_argument("--mode", type=int, default=0, choices=[0, 1], help="0 for natural cache eviction, 1 for clflush forced deep memory accesses")
    
    args = parser.parse_args()
    
    print("=== Auto-Echo Framework ===")
    
    try:
        from autoecho.probe import collect
        from autoecho.preprocessing import preprocess_pipeline
        from autoecho.clustering import discover_memory_levels_kmeans, map_clusters_to_levels
        from autoecho.report import plot_latency_distribution, generate_report
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Please ensure you have installed the package using 'pip install -e .'")
        sys.exit(1)
        
    print(f"\n[1/4] Collecting {args.samples} memory latency samples...")
    raw_df = collect(args.samples, args.mode)
    
    print("\n[2/4] Preprocessing raw latencies...")
    clean_df = preprocess_pipeline(raw_df, use_lof=False)
    
    if len(clean_df) < 100:
        print("Error: Too few data points remain after preprocessing. Try increasing --samples.")
        sys.exit(1)
        
    print("\n[3/4] Running Clustering Engine to discover memory levels...")
    clustered_df, model = discover_memory_levels_kmeans(clean_df, max_k=6)
    
    print("\n[4/4] Mapping clusters and generating reports...")
    stats_df = map_clusters_to_levels(clustered_df)
    
    os.makedirs(args.output_dir, exist_ok=True)
    report_path = os.path.join(args.output_dir, "validation_report.md")
    plot_path = os.path.join(args.output_dir, "latency_distribution.png")
    
    generate_report(stats_df, report_path)
    plot_latency_distribution(clustered_df, output_path=plot_path)
    
    print("\nDone! Auto-Echo pipeline completed successfully.")

if __name__ == "__main__":
    main()
