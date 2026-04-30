"""Tests for ``release-readiness-doctor``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from release_readiness_core.doctor import Finding, _summarize, main, run


def _f(target_severity: str, findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == target_severity]


def _write_yaml(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(body, encoding="utf-8")
    return p


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_run_with_no_args_runs_install_checks_only():
    findings = run()
    # Install check always runs; no config or evidence supplied
    assert any(f.severity == "OK" and "importable" in f.message for f in findings)
    assert _summarize(findings)["ERROR"] == 0


def test_run_reports_error_for_missing_config(tmp_path: Path):
    findings = run(config_path=tmp_path / "missing.yaml")
    assert any(f.severity == "ERROR" and "config not found" in f.message for f in findings)


def test_run_reports_error_for_config_typo(tmp_path: Path):
    """A misspelled top-level key surfaces as an ERROR via the schema validator."""
    cfg = _write_yaml(tmp_path, "version: 1\ninfer_validations_when_pas:\n  smoke: []\n  e2e: []\n")
    findings = run(config_path=cfg)
    err = _f("ERROR", findings)
    assert err
    assert "schema error" in err[0].message
    assert "did you mean" in err[0].message


def test_run_warns_when_risk_categories_unmapped(tmp_path: Path):
    """A risk category without a mapping or matching validation key surfaces as WARN."""
    cfg = _write_yaml(
        tmp_path,
        """
version: 1
validations: {}
risk_from_paths:
  - categories: [some_thing_unmapped]
    patterns: ["src/**"]
""".strip(),
    )
    findings = run(config_path=cfg)
    warns = _f("WARN", findings)
    assert any("some_thing_unmapped" in w.message for w in warns)


def test_run_smoke_status_passed_with_failed_count_warns(tmp_path: Path):
    smoke = _write_json(
        tmp_path / "evidence" / "smoke.json",
        {"status": "passed", "failed_count": 2},
    )
    findings = run(smoke_path=smoke)
    assert any("smoke_failed" in f.message for f in _f("WARN", findings))


def test_run_e2e_failed_count_with_empty_failures_warns(tmp_path: Path):
    e2e = _write_json(
        tmp_path / "evidence" / "e2e.json",
        {"status": "failed", "failed_count": 1, "failures": []},
    )
    findings = run(e2e_path=e2e)
    assert any("e2e_unlisted_failures" in f.message for f in _f("WARN", findings))


def test_run_e2e_skipped_warns(tmp_path: Path):
    e2e = _write_json(
        tmp_path / "evidence" / "e2e.json",
        {"status": "skipped", "failed_count": 0, "total_count": 0, "failures": []},
    )
    findings = run(e2e_path=e2e)
    assert any("E2E was skipped" in f.message for f in _f("WARN", findings))


def test_run_coverage_below_baseline_info(tmp_path: Path):
    cov = _write_json(tmp_path / "coverage.json", {"line_percent": 70, "baseline_percent": 80})
    findings = run(coverage_path=cov)
    assert any(
        "coverage_regression" in f.message
        for f in _f("INFO", findings) + _f("WARN", findings)
    )


def test_run_coverage_with_invalid_line_percent_errors(tmp_path: Path):
    cov = _write_json(tmp_path / "coverage.json", {"line_percent": "not-a-number"})
    findings = run(coverage_path=cov)
    assert any("line_percent" in f.message for f in _f("ERROR", findings))


def test_run_evidence_file_not_json_errors(tmp_path: Path):
    bad = tmp_path / "smoke.json"
    bad.write_text("not json at all", encoding="utf-8")
    findings = run(smoke_path=bad)
    assert any("not valid JSON" in f.message for f in _f("ERROR", findings))


def test_run_prod_health_missing_with_optional_artifacts_is_info(tmp_path: Path):
    cfg = _write_yaml(
        tmp_path,
        "version: 1\nvalidations: {}\noptional_artifacts: [prod_health]\n",
    )
    findings = run(config_path=cfg, prod_health_path=None)
    msgs = [f.message for f in _f("INFO", findings)]
    assert any("optional_artifacts" in m for m in msgs)


def test_main_exits_zero_when_no_errors(tmp_path: Path, capsys: pytest.CaptureFixture):
    cfg = _write_yaml(tmp_path, "version: 1\nvalidations: {}\n")
    code = main(["--config", str(cfg)])
    assert code == 0
    out = capsys.readouterr().out
    assert "release-readiness-doctor" in out
    assert "Summary:" in out


def test_main_exits_one_when_any_error(tmp_path: Path, capsys: pytest.CaptureFixture):
    code = main(["--config", str(tmp_path / "nope.yaml")])
    assert code == 1


def test_finding_render_format():
    assert Finding("OK", "hi").render() == "[OK   ] hi"
    assert Finding("ERROR", "boom").render() == "[ERROR] boom"


def test_doctor_against_second_project_fixture_passes_clean():
    """The shipped second-project example must pass doctor with zero errors."""
    repo_root = Path(__file__).resolve().parents[1]
    example = repo_root / "examples" / "second-project"
    findings = run(
        config_path=example / "config.yaml",
        smoke_path=example / "evidence" / "smoke.json",
        e2e_path=example / "evidence" / "e2e.json",
        coverage_path=example / "evidence" / "coverage.json",
        prod_health_path=None,
    )
    counts = _summarize(findings)
    assert counts["ERROR"] == 0, [f.render() for f in findings if f.severity == "ERROR"]
