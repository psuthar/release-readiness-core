"""Tests for the evaluate CLI and IO helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from release_readiness_core.readiness_evaluate import main
from release_readiness_core.readiness_io import detect_validation_note, read_json


MINIMAL_CONFIG = {
    "version": 1,
    "scoring": {
        "max_score": 100,
        "pass_threshold": 80,
        "warn_threshold": 60,
        "block_score": 0,
        "penalties": {
            "missing_smoke_artifact": 25,
            "missing_e2e_artifact": 15,
            "missing_coverage_artifact": 5,
            "missing_prod_health_artifact": 5,
            "non_critical_e2e_failure": 15,
            "e2e_retries_or_flaky": 10,
            "coverage_regression": 12,
            "risky_config_without_note": 10,
        },
    },
    "e2e_critical_name_patterns": [],
    "risk_from_paths": [],
    "infer_validations_when_pass": {"smoke": [], "e2e": []},
}


def test_detect_validation_note_finds_line():
    found, snippet = detect_validation_note(
        ["other", "Validation: checked workflow", "more"]
    )
    assert found is True
    assert "checked workflow" in snippet


def test_read_json_missing_returns_none(tmp_path: Path):
    assert read_json(tmp_path / "nope.json") is None


def test_evaluate_cli_writes_report_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(MINIMAL_CONFIG), encoding="utf-8")
    out = tmp_path / "out"
    # Avoid git subprocess noise in hermetic test env
    monkeypatch.setattr(
        "release_readiness_core.readiness_evaluate.git_commit_messages", lambda *a, **k: []
    )
    rc = main(
        [
            "--repo-root",
            str(tmp_path),
            "--config",
            str(cfg_path),
            "--empty-diff",
            "--output-dir",
            str(out),
        ]
    )
    assert (out / "report.json").is_file()
    data = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert "outcome" in data
    assert "score" in data
    # Missing smoke/e2e/coverage is a weak score but still produces a result
    assert rc in (0, 1)
