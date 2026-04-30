"""Tests for the JUnit XML adapter."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from release_readiness_core.adapters.junit_xml import (
    _case_stems,
    _case_title,
    convert,
    main,
)


def _parse(s: str) -> ET.Element:
    return ET.fromstring(s.strip())


JUNIT_PASS = """
<testsuites>
  <testsuite name="suite_a" tests="2" failures="0">
    <testcase classname="auth.LoginFlow" name="logs_in" />
    <testcase classname="auth.LoginFlow" name="rejects_bad_password" />
  </testsuite>
</testsuites>
""".strip()


JUNIT_FAILURE = """
<testsuites>
  <testsuite name="suite_a" tests="2" failures="1">
    <testcase classname="cart.Checkout" name="adds_item" />
    <testcase classname="cart.Checkout" name="charges_card">
      <failure message="boom">card declined</failure>
    </testcase>
  </testsuite>
</testsuites>
""".strip()


JUNIT_ERROR_AND_SKIP = """
<testsuites>
  <testsuite name="mixed" tests="3" failures="1" errors="1">
    <testcase classname="api" name="health" />
    <testcase classname="api" name="error_path">
      <error message="500">internal</error>
    </testcase>
    <testcase classname="api" name="legacy_path">
      <skipped />
    </testcase>
  </testsuite>
</testsuites>
""".strip()


def test_convert_all_passing():
    out = convert(_parse(JUNIT_PASS))
    assert out["status"] == "passed"
    assert out["total_count"] == 2
    assert out["failed_count"] == 0
    assert out["failures"] == []
    assert out["validations"] == {}


def test_convert_with_failures():
    out = convert(_parse(JUNIT_FAILURE))
    assert out["status"] == "failed"
    assert out["total_count"] == 2
    assert out["failed_count"] == 1
    assert out["failures"][0]["title"] == "cart.Checkout.charges_card"


def test_convert_treats_errors_as_failures_and_counts_skipped():
    out = convert(_parse(JUNIT_ERROR_AND_SKIP))
    assert out["status"] == "failed"
    assert out["total_count"] == 3
    assert out["failed_count"] == 1
    assert out["failures"][0]["title"] == "api.error_path"


def test_convert_only_skipped_marked_skipped():
    only_skip = """
    <testsuites>
      <testsuite name="s" tests="1">
        <testcase classname="x" name="y"><skipped /></testcase>
      </testsuite>
    </testsuites>
    """
    out = convert(_parse(only_skip))
    assert out["status"] == "skipped"


def test_convert_empty_root_skipped():
    out = convert(_parse("<testsuites />"))
    assert out["status"] == "skipped"
    assert out["total_count"] == 0


def test_convert_validation_map_assigns_groups_when_passing():
    val_map = {"auth_login": ["LoginFlow"], "checkout": ["Checkout"]}
    out = convert(_parse(JUNIT_PASS), validation_map=val_map)
    assert out["validations"] == {"auth_login": True}


def test_convert_validation_map_marks_failure():
    out = convert(_parse(JUNIT_FAILURE), validation_map={"checkout": ["Checkout"]})
    assert out["validations"] == {"checkout": False}


def test_convert_validation_map_omits_groups_with_no_matches():
    out = convert(_parse(JUNIT_PASS), validation_map={"missing_group": ["Nope"]})
    assert out["validations"] == {}


def test_case_stems_includes_classname_segments_and_name():
    case = _parse('<testcase classname="auth.LoginFlow" name="logs_in" />')
    stems = _case_stems(case)
    assert "auth.LoginFlow" in stems
    assert "LoginFlow" in stems
    assert "logs_in" in stems


def test_case_title_falls_back_to_name_when_no_classname():
    case = _parse('<testcase name="standalone" />')
    assert _case_title(case) == "standalone"


def test_main_reads_input_writes_output(tmp_path: Path):
    inp = tmp_path / "report.xml"
    out = tmp_path / "e2e.json"
    inp.write_text(JUNIT_FAILURE, encoding="utf-8")
    code = main(["--input", str(inp), "--output", str(out)])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["failed_count"] == 1


def test_main_missing_input_writes_skipped_placeholder(tmp_path: Path):
    out = tmp_path / "e2e.json"
    code = main(["--input", str(tmp_path / "nope.xml"), "--output", str(out)])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "skipped"
    assert "note" in payload


def test_main_invalid_xml_writes_failure(tmp_path: Path):
    inp = tmp_path / "bad.xml"
    inp.write_text("<not xml", encoding="utf-8")
    out = tmp_path / "e2e.json"
    code = main(["--input", str(inp), "--output", str(out)])
    assert code == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["failures"][0]["title"] == "junit_parse_error"


def test_main_with_validation_map(tmp_path: Path):
    inp = tmp_path / "report.xml"
    out = tmp_path / "e2e.json"
    map_path = tmp_path / "map.yaml"
    inp.write_text(JUNIT_PASS, encoding="utf-8")
    map_path.write_text("auth_login:\n  - LoginFlow\n", encoding="utf-8")
    code = main(
        [
            "--input",
            str(inp),
            "--output",
            str(out),
            "--validation-map",
            str(map_path),
        ]
    )
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["validations"] == {"auth_login": True}
