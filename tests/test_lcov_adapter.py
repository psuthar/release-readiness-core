"""Tests for the LCOV coverage adapter."""

from __future__ import annotations

import json
from pathlib import Path

from release_readiness_core.adapters.lcov_coverage import (
    line_percent,
    main,
    parse_lcov,
)


SINGLE_FILE = """
TN:
SF:src/foo.py
DA:1,1
DA:2,1
DA:3,0
LF:3
LH:2
end_of_record
""".strip()


MULTI_FILE = """
TN:
SF:src/foo.py
LF:10
LH:8
end_of_record
TN:
SF:src/bar.py
LF:20
LH:14
end_of_record
""".strip()


def test_parse_lcov_single_file():
    found, hit = parse_lcov(SINGLE_FILE)
    assert (found, hit) == (3, 2)


def test_parse_lcov_sums_across_files():
    found, hit = parse_lcov(MULTI_FILE)
    assert (found, hit) == (30, 22)


def test_line_percent_basic():
    assert line_percent(SINGLE_FILE) == 66.67


def test_line_percent_multi_file():
    assert line_percent(MULTI_FILE) == 73.33


def test_line_percent_zero_lines_returns_zero():
    assert line_percent("TN:\n") == 0.0


def test_line_percent_skips_non_integer_lf_values():
    """Malformed LF/LH lines are silently dropped — adopters get a partial count, not a crash."""
    text = "LF:not_an_int\nLH:not_an_int\nLF:10\nLH:5\n"
    # Bad pair ignored; only the well-formed pair contributes
    assert line_percent(text) == 50.0


def test_main_writes_coverage_with_baseline(tmp_path: Path):
    inp = tmp_path / "lcov.info"
    out = tmp_path / "coverage.json"
    inp.write_text(MULTI_FILE, encoding="utf-8")
    code = main(["--input", str(inp), "--output", str(out), "--baseline-percent", "70"])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["line_percent"] == 73.33
    assert payload["baseline_percent"] == 70.0


def test_main_writes_coverage_without_baseline(tmp_path: Path):
    inp = tmp_path / "lcov.info"
    out = tmp_path / "coverage.json"
    inp.write_text(SINGLE_FILE, encoding="utf-8")
    code = main(["--input", str(inp), "--output", str(out)])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["line_percent"] == 66.67
    assert payload["baseline_percent"] is None


def test_main_missing_input_writes_zero_with_note(tmp_path: Path):
    out = tmp_path / "coverage.json"
    code = main(["--input", str(tmp_path / "nope.info"), "--output", str(out)])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["line_percent"] == 0.0
    assert "note" in payload
