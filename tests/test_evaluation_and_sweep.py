"""Tests for the comparative evaluation and the WSS size grid."""
from autoecho.evaluation import capacity_accuracy, compare_methods
from autoecho.wss import default_wss_sizes


def test_default_wss_sizes_are_sorted_line_aligned_and_bounded():
    line = 64
    max_bytes = 32 * 1024 * 1024
    sizes = default_wss_sizes(line, max_bytes)
    assert len(sizes) > 10
    assert list(sizes) == sorted(sizes)          # ascending
    assert all(s % line == 0 for s in sizes)     # cache-line aligned
    assert sizes[0] >= line * 2
    assert sizes[-1] <= max_bytes


def test_default_wss_sizes_scale_with_max_bytes():
    small = default_wss_sizes(64, 4 * 1024 * 1024)
    large = default_wss_sizes(64, 256 * 1024 * 1024)
    assert large[-1] > small[-1]


def test_compare_methods_ranks_and_flags_correctness(three_level_curve):
    gt = {"L1": 32 * 1024, "L2": 256 * 1024}  # expected levels = 3 (+DRAM)
    ranked = compare_methods([three_level_curve, three_level_curve], gt)
    assert not ranked.empty
    assert list(ranked["rank"]) == list(range(1, len(ranked) + 1))
    # 'modal_agreement' quantifies count stability (1.0 == unanimous across sweeps).
    assert {"method", "mean_levels", "std_levels", "modal_agreement",
            "count_ok"}.issubset(ranked.columns)
    assert (ranked["modal_agreement"] == 1.0).all()  # identical sweeps -> unanimous


def test_capacity_accuracy_default_uses_production_penalty_none(three_level_curve):
    # The default must exercise the SAME hybrid path the CLI ships (penalty=None),
    # not PELT@3.0, so the test guards the headline capacity localisation.
    gt = {"L1": 32 * 1024, "L2": 256 * 1024}
    auto = capacity_accuracy([three_level_curve], gt)              # penalty=None
    pelt = capacity_accuracy([three_level_curve], gt, penalty=3.0)  # legacy path
    assert 0.0 <= auto["mean_accuracy"] <= 1.0
    assert auto["n_sweeps"] == 1 and pelt["n_sweeps"] == 1


def test_capacity_accuracy_reports_error_and_uses_injected_gt(three_level_curve):
    gt = {"L1": 32 * 1024, "L2": 256 * 1024}
    result = capacity_accuracy([three_level_curve], gt)
    assert 0.0 <= result["mean_accuracy"] <= 1.0
    assert result["n_sweeps"] == 1
