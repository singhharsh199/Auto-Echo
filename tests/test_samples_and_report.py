"""Smoke tests for the two paths not covered elsewhere: the primary WSS
report-generation glue, and the legacy sample-based baseline pipeline. Both run
on synthetic data with no compiled C extension and no particular hardware."""
import numpy as np
import pandas as pd

from autoecho.analysis import analyze
from autoecho.validation import validate, get_ground_truth
from autoecho.report import generate_wss_report, generate_report
from autoecho.clustering import discover_memory_levels_kmeans, map_clusters_to_levels
from autoecho.preprocessing import preprocess_pipeline


def test_wss_report_generation(make_curve, tmp_path):
    """analyze() + generate_wss_report() on a synthetic curve writes a report
    with the expected sections (covers report.generate_wss_report end-to-end)."""
    curve = make_curve([(64 * 1024, 1.5), (2 * 1024 * 1024, 8.0),
                        (32 * 1024 * 1024, 20.0)])
    result = analyze(curve)
    caps = result["levels"]["capacity_bytes"].dropna().tolist()
    val = validate(caps, ground_truth=get_ground_truth())
    out = tmp_path / "report.md"
    generate_wss_report(result["levels"], result, val, str(out))

    assert out.exists()
    text = out.read_text()
    assert "Discovered Memory Hierarchy" in text
    assert "Validation Against Hardware Ground Truth" in text
    assert len(result["levels"]) >= 2  # a clean multi-tier curve yields >=2 levels
    # the deepest level must be DRAM and must appear exactly once (label bug guard)
    names = result["levels"]["level_name"].tolist()
    assert names[-1] == "DRAM" and names.count("DRAM") == 1


def test_legacy_samples_pipeline(tmp_path):
    """The naive sample-based baseline (clustering + report) runs on synthetic
    multi-tier latency samples without the C probe."""
    rng = np.random.default_rng(0)
    tiers = np.concatenate([
        rng.normal(1.5, 0.1, 300),
        rng.normal(9.0, 0.4, 300),
        rng.normal(130.0, 3.0, 300),
    ])
    df = pd.DataFrame({"latency_ns": np.abs(tiers),
                       "access_index": np.arange(tiers.size)})

    clustered, _ = discover_memory_levels_kmeans(df, max_k=6)
    clustered, stats = map_clusters_to_levels(clustered)
    assert "level_name" in clustered.columns
    assert len(stats) >= 2  # multiple tiers recovered

    out = tmp_path / "baseline.md"
    generate_report(stats, str(out))
    assert out.exists() and "Memory Hierarchy" in out.read_text()


def test_preprocess_pipeline_runs():
    """preprocessing.preprocess_pipeline cleans a noisy frame without error."""
    rng = np.random.default_rng(1)
    df = pd.DataFrame({"latency_ns": np.abs(rng.normal(10.0, 2.0, 500))})
    cleaned = preprocess_pipeline(df, use_lof=False)
    assert len(cleaned) > 50 and "latency_ns" in cleaned.columns
