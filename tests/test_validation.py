"""Tests for ground-truth validation and machine labelling."""
from autoecho.validation import get_machine_label, validate


def test_validate_exact_match_is_zero_error():
    gt = {"L1": 32 * 1024, "L2": 256 * 1024}
    result = validate([32 * 1024, 256 * 1024], ground_truth=gt)
    assert result["accuracy"] == 1.0
    assert result["n_matched"] == 2
    for m in result["matches"]:
        assert m["match"] is True
        assert abs(m["pct_error"]) < 1e-6


def test_validate_percentage_error_sign_and_magnitude():
    gt = {"L1": 100_000}
    result = validate([120_000], ground_truth=gt)  # 20% over
    m = result["matches"][0]
    assert m["match"] is True
    assert abs(m["pct_error"] - 20.0) < 1e-6


def test_validate_out_of_tolerance_is_no_match():
    gt = {"L1": 32 * 1024}
    # 32 KiB vs 4 MiB is far more than one octave apart.
    result = validate([4 * 1024 * 1024], ground_truth=gt, tolerance_octaves=1.0)
    assert result["accuracy"] == 0.0
    assert result["matches"][0]["match"] is False


def test_validate_ignores_nan_and_nonpositive():
    gt = {"L1": 32 * 1024}
    result = validate([float("nan"), -5, 32 * 1024], ground_truth=gt)
    assert result["n_matched"] == 1


def test_validate_empty_ground_truth_is_zero_accuracy():
    result = validate([1024], ground_truth={})
    assert result["accuracy"] == 0.0
    assert result["n_ground_truth"] == 0


def test_machine_label_is_nonempty_string():
    label = get_machine_label()
    assert isinstance(label, str) and len(label) > 0
