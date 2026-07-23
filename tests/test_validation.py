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


def test_validate_reports_precision_and_false_positives():
    # One real cache + one spurious deep knee (e.g. a TLB artefact) that matches
    # no ground-truth cache: recall stays 100% but precision must drop and the
    # false positive must be counted (recall-only accuracy would hide it).
    gt = {"L1": 32 * 1024}
    result = validate([32 * 1024, 5 * 1024 * 1024], ground_truth=gt)
    assert result["recall"] == 1.0
    assert result["n_detected"] == 2
    assert result["n_false_positive"] == 1
    assert abs(result["precision"] - 0.5) < 1e-9


def test_validate_optimal_matching_beats_greedy():
    # GT L2=2 MiB, L3=6 MiB; knees at 1.1 MiB and 3.0 MiB. Greedy nearest-first
    # would pair L2->3.0 MiB and strand L3; optimal assignment matches BOTH.
    gt = {"L2": 2 * 1024 * 1024, "L3": 6 * 1024 * 1024}
    result = validate([1.1 * 1024 * 1024, 3.0 * 1024 * 1024], ground_truth=gt,
                      tolerance_octaves=1.0)
    assert result["n_matched"] == 2
    assert result["recall"] == 1.0


def test_machine_label_is_nonempty_string():
    label = get_machine_label()
    assert isinstance(label, str) and len(label) > 0


def test_machine_label_normalises_amd64_to_x86_64():
    # 'AMD64' (Windows' x86-64 ISA token) must never leak into a label as a
    # vendor; it is normalised to 'x86-64'.
    from autoecho.validation import _clean_brand, _normalize_arch
    assert _normalize_arch("AMD64") == "x86-64"
    assert _normalize_arch("x86_64") == "x86-64"
    assert _clean_brand("Intel(R) Core(TM)  i5-13450HX") == "Intel Core i5-13450HX"
