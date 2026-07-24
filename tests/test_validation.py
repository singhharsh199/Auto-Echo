"""Tests for ground-truth validation and machine labelling."""
import platform

import pytest

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


@pytest.mark.skipif(platform.system() != "Windows",
                    reason="per-core cache query is Windows-specific")
def test_windows_percore_ground_truth_is_not_aggregate():
    # GetLogicalProcessorInformationEx must return PER-CORE cache sizes, not the
    # per-socket AGGREGATE that Win32_CacheMemory reports (the historical bug:
    # L1 summed to 288 KiB across the P-cores, which zeroed validation recall).
    # Guard the regression structurally so it is not pinned to one CPU model.
    from autoecho.validation import _windows_ground_truth_percore
    gt = _windows_ground_truth_percore()
    if not gt:
        pytest.skip("GetLogicalProcessorInformationEx returned no cache records")
    assert "L1" in gt
    # A single core's L1d is tens of KiB; a summed aggregate is >= 256 KiB.
    assert 16 * 1024 <= gt["L1"] <= 128 * 1024, gt
    # Cache sizes must be strictly increasing with level where present.
    present = [gt[k] for k in ("L1", "L2", "L3") if k in gt]
    assert present == sorted(present) and len(set(present)) == len(present), gt
