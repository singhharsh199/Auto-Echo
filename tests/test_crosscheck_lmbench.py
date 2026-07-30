"""Tests for the lmbench `lat_mem_rd` converter.

The external cross-check in the evaluation depends on parsing lmbench output
correctly. lmbench is not available on every development machine, so the parser
is tested against captured-format fixtures rather than a live run.

The fixture reproduces the documented `lat_mem_rd` stdout format: a "stride=N"
header line followed by "<size_in_MB> <latency_ns>" pairs, with sizes as
fractional megabytes.
"""

import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "crosscheck_lmbench", ROOT / "scripts" / "crosscheck_lmbench.py"
)
crosscheck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crosscheck)


LAT_MEM_RD_OUTPUT = """\
"stride=128
0.00049 1.ollocate
0.00098 1.588
0.00195 1.591
0.00391 1.587
0.01562 1.590
0.06250 4.742
0.25000 4.751
1.00000 4.769
2.00000 22.930
8.00000 23.014
16.00000 98.221
64.00000 123.240
"stride=512
0.00098 1.601
"""


@pytest.fixture()
def raw(tmp_path):
    p = tmp_path / "lmbench_raw.txt"
    p.write_text(LAT_MEM_RD_OUTPUT)
    return p


def test_parses_size_latency_pairs(raw):
    rows = crosscheck.parse_lmbench(str(raw))
    # The "stride=" headers and the malformed "1.ollocate" line are skipped.
    assert len(rows) == 12
    assert all(len(r) == 3 for r in rows)


def test_converts_megabytes_to_bytes_and_kib(raw):
    rows = crosscheck.parse_lmbench(str(raw))
    by_latency = {round(r[2], 3): r for r in rows}
    one_mb = by_latency[4.769]
    assert one_mb[0] == 1024 * 1024  # wss_bytes
    assert one_mb[1] == pytest.approx(1024)  # wss_kib


def test_skips_header_and_nonnumeric_lines(raw):
    rows = crosscheck.parse_lmbench(str(raw))
    assert not any(r[2] <= 0 for r in rows)
    # 0.00049 MB pairs with a non-numeric latency and must not appear.
    assert all(r[0] != int(round(0.00049 * 1024 * 1024)) for r in rows)


def test_output_csv_matches_wss_curve_schema(raw, tmp_path, monkeypatch):
    out = tmp_path / "lmbench_curve.csv"
    monkeypatch.setattr("sys.argv", ["crosscheck_lmbench.py", str(raw), "-o", str(out)])
    crosscheck.main()

    with open(out) as f:
        reader = csv.DictReader(f)
        # Must match the schema compare_curves.py and the dashboard consume.
        assert reader.fieldnames == ["wss_bytes", "wss_kib", "latency_ns"]
        rows = list(reader)

    assert len(rows) == 12
    sizes = [int(r["wss_bytes"]) for r in rows]
    assert sizes == sorted(sizes), "rows must be emitted in ascending WSS order"


def test_rejects_input_with_no_valid_rows(tmp_path, monkeypatch):
    empty = tmp_path / "junk.txt"
    empty.write_text("not lat_mem_rd output at all\n")
    monkeypatch.setattr("sys.argv", ["crosscheck_lmbench.py", str(empty)])
    with pytest.raises(SystemExit):
        crosscheck.main()
