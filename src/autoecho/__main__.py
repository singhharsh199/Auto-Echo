import argparse
import os
import sys


def _positive_int(value):
    """argparse type: accept only strictly positive integers."""
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {value}")
    return ivalue


def _positive_float(value):
    """argparse type: accept only strictly positive floats."""
    fvalue = float(value)
    if fvalue <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive number, got {value}")
    return fvalue


def run_wss(args):
    """Primary pipeline: working-set-size pointer-chase sweep + change-point
    level discovery + comparative evaluation + validation vs ground truth."""
    try:
        from autoecho.wss import sweep
        from autoecho.analysis import analyze
        from autoecho.validation import validate, get_ground_truth, get_machine_label
        from autoecho.evaluation import compare_methods, capacity_accuracy
        from autoecho.report import (plot_memory_mountain, plot_model_selection,
                                     generate_wss_report)
    except ImportError as e:
        print(f"\n[setup error] {e}\n", file=sys.stderr)
        sys.exit(1)

    machine = get_machine_label()
    print(f"Machine: {machine}")

    print(f"\n[1/5] Running {args.runs} pointer-chase sweep(s) up to {args.max_mb} MiB "
          f"({args.repeats} repeats/size, seed={args.seed})...")
    sweeps = []
    for i in range(args.runs):
        # Vary the seed per run so repeat sweeps are independent (stability signal).
        sweeps.append(sweep(max_bytes=args.max_mb * 1024 * 1024, hops=args.hops,
                            repeats=args.repeats, seed=args.seed + i))
    curve = sweeps[0]  # representative curve for the headline figures

    print("[2/5] Discovering memory levels (change-point + clustering)...")
    result = analyze(curve, penalty=args.penalty)
    levels = result["levels"]
    print(f"      change-point: {result['n_levels_changepoint']} | "
          f"k-means(sil): {result['n_levels_kmeans']} | "
          f"k-means(elbow): {result['n_levels_elbow']} | "
          f"gmm: {result['n_levels_gmm']} | dbscan: {result['n_levels_dbscan']}")

    print("[3/5] Comparative evaluation across estimators...")
    gt = get_ground_truth()
    comparison = compare_methods(sweeps, gt, penalty=args.penalty)
    cap_acc = capacity_accuracy(sweeps, gt, penalty=args.penalty)
    if len(comparison):
        top = comparison.iloc[0]
        # This ranks LEVEL-COUNT stability only. Change-point is the productive
        # method: it is the sole estimator that localises cache capacities.
        print(f"      most stable level-count: {top['method']} "
              f"(std={top['std_levels']}); capacities localised by change-point")

    print("[4/5] Validating against hardware ground truth...")
    caps = levels["capacity_bytes"].dropna().tolist()
    val = validate(caps)
    print(f"      accuracy: {val['accuracy']*100:.1f}% "
          f"({val['n_matched']}/{val['n_ground_truth']} caches matched); "
          f"mean |error| {cap_acc['mean_abs_pct_error']:.1f}%"
          if cap_acc.get('mean_abs_pct_error') is not None
          else f"      accuracy: {val['accuracy']*100:.1f}%")

    print("[5/5] Writing report and plots...")
    os.makedirs(args.output_dir, exist_ok=True)
    curve.to_csv(os.path.join(args.output_dir, "wss_curve.csv"), index=False)
    if args.runs > 1:
        import pandas as pd
        allc = pd.concat([s.assign(run=i) for i, s in enumerate(sweeps)],
                         ignore_index=True)
        allc.to_csv(os.path.join(args.output_dir, "wss_curves_all.csv"), index=False)
    generate_wss_report(levels, result, val,
                        os.path.join(args.output_dir, "validation_report.md"),
                        comparison=comparison, capacity_acc=cap_acc, machine=machine)
    plot_memory_mountain(curve, levels,
                         os.path.join(args.output_dir, "memory_mountain.png"),
                         sweeps=sweeps, machine=machine)
    plot_model_selection(result,
                         os.path.join(args.output_dir, "model_selection.png"),
                         machine=machine)
    print("\nDone! Auto-Echo WSS pipeline completed successfully.")


def run_samples(args):
    """Legacy sample-based pipeline, retained as the documented naive baseline
    (write-before-read guarantees L1 residency -- see dissertation Section 5)."""
    try:
        from autoecho.probe import collect
        from autoecho.preprocessing import preprocess_pipeline
        from autoecho.clustering import discover_memory_levels_kmeans, map_clusters_to_levels
        from autoecho.report import plot_latency_distribution, generate_report
    except ImportError as e:
        print(f"\n[setup error] {e}\n", file=sys.stderr)
        sys.exit(1)

    print(f"\n[1/4] Collecting {args.samples} memory latency samples...")
    raw_df = collect(args.samples, args.mode)
    print("[2/4] Preprocessing raw latencies...")
    clean_df = preprocess_pipeline(raw_df, use_lof=False)
    if len(clean_df) < 100:
        print("Error: too few data points after preprocessing. Increase --samples.")
        sys.exit(1)
    print("[3/4] Clustering...")
    clustered_df, _ = discover_memory_levels_kmeans(clean_df, max_k=6)
    clustered_df, stats_df = map_clusters_to_levels(clustered_df)
    os.makedirs(args.output_dir, exist_ok=True)
    generate_report(stats_df, os.path.join(args.output_dir, "validation_report.md"))
    plot_latency_distribution(clustered_df, cluster_stats=stats_df,
                              output_path=os.path.join(args.output_dir,
                                                       "latency_distribution.png"))
    print("\nDone (naive baseline).")


def main():
    parser = argparse.ArgumentParser(
        description="Auto-Echo: Automated Discovery of Memory Hierarchy Latency Patterns")
    parser.add_argument("--method", choices=["wss", "samples"], default="wss",
                        help="wss = pointer-chase sweep (primary); samples = naive baseline")
    parser.add_argument("--output-dir", type=str, default="data")
    # WSS options
    parser.add_argument("--max-mb", type=_positive_int, default=256, help="max working-set size (MiB)")
    parser.add_argument("--hops", type=_positive_int, default=1 << 20, help="min pointer-chase hops per timing window")
    parser.add_argument("--repeats", type=_positive_int, default=5, help="repeats per size (minimum is taken)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducible permutations")
    parser.add_argument("--penalty", type=_positive_float, default=None,
                        help="change-point penalty override (higher = fewer levels); "
                             "omit for automatic model selection (cost-knee)")
    parser.add_argument("--runs", type=_positive_int, default=1, help="independent sweeps for stability/error-bar evaluation")
    # Legacy sample options
    parser.add_argument("--samples", type=_positive_int, default=50000)
    parser.add_argument("--mode", type=int, default=0, choices=[0, 1])

    args = parser.parse_args()
    print("=== Auto-Echo Framework ===")
    if args.method == "wss":
        run_wss(args)
    else:
        run_samples(args)


if __name__ == "__main__":
    main()
