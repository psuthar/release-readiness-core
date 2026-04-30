"""SCRUM-209 friction fixes (originally surfaced in SCRUM-178 spike).

Covers:
- Markdown renderer no longer emits empty validations table (gap #4).
- Markdown renderer omits the Validation note row when none is present (gap #5).
- DEFAULT_EVIDENCE_BOOLEAN_KEYS is empty by default (gap #6).
- Engine messages no longer reference pr_risk.md (gap #20).
- readiness_evaluate resolves relative artifact paths under --repo-root (gap #3).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from release_readiness_core.readiness_engine import (
    DEFAULT_EVIDENCE_BOOLEAN_KEYS,
    ReadinessResult,
    compute_readiness,
)
from release_readiness_core.readiness_markdown import render_readiness_result_markdown

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "examples" / "second-project"


def _trivial_result(**overrides) -> ReadinessResult:
    base = dict(
        outcome="PASS",
        score=100.0,
        max_score=100.0,
        pass_threshold=80.0,
        warn_threshold=60.0,
        reasons=["Score=100/100"],
        warnings=[],
        blockers=[],
        failed_checks=[],
        changed_files=[],
        risks_triggered=[],
        validations={},
        validations_required=[],
        evidence={"validation_note_present": False, "validation_note_source": "none"},
        recommended_actions=[],
        remediation_items=[],
        outcome_overrides=[],
        critical_failed_titles=[],
        non_critical_failed_titles=[],
    )
    base.update(overrides)
    return ReadinessResult(**base)


def test_markdown_omits_empty_validations_table():
    md = render_readiness_result_markdown(_trivial_result(validations={}), config_version=1)
    assert "### Validations" not in md
    # No empty table header should leak through
    assert "| Key | Status |" not in md


def test_markdown_renders_populated_validations_table():
    md = render_readiness_result_markdown(
        _trivial_result(validations={"auth_login": "satisfied"}, validations_required=["auth_login"]),
        config_version=1,
    )
    assert "### Validations" in md
    assert "| auth_login | satisfied *(required)* |" in md


def test_markdown_omits_validation_note_row_when_absent():
    md = render_readiness_result_markdown(_trivial_result(), config_version=1)
    assert "Validation note" not in md


def test_markdown_renders_validation_note_row_when_present():
    md = render_readiness_result_markdown(
        _trivial_result(
            evidence={"validation_note_present": True, "validation_note_source": "commit_message"}
        ),
        config_version=1,
    )
    assert "| Validation note | yes (commit_message) |" in md


def test_default_evidence_boolean_keys_is_empty():
    """SCRUM-209 (gap #6): the engine ships an empty default; projects opt in via config."""
    assert DEFAULT_EVIDENCE_BOOLEAN_KEYS == ()


def test_pr_risk_block_message_does_not_reference_pr_risk_md():
    """SCRUM-209 (gap #20): no dead doc reference in the report."""
    res = compute_readiness(
        config={"scoring": {"max_score": 100, "pass_threshold": 80, "warn_threshold": 60}},
        changed_files=[],
        smoke={"status": "passed", "passed": True},
        e2e={"status": "passed", "failed_count": 0, "total_count": 1, "failures": []},
        coverage={"line_percent": 80, "baseline_percent": 80},
        prod_health={"ok": True},
        migration_validated_cli=False,
        pr_risk={"enforcement": {"merge_recommendation": "BLOCK"}},
    )
    assert res.outcome == "BLOCK"
    blob = "\n".join(res.blockers + res.warnings)
    assert "pr_risk.md" not in blob


def test_pr_risk_warn_message_does_not_reference_pr_risk_md():
    res = compute_readiness(
        config={"scoring": {"max_score": 100, "pass_threshold": 80, "warn_threshold": 60}},
        changed_files=[],
        smoke={"status": "passed", "passed": True},
        e2e={"status": "passed", "failed_count": 0, "total_count": 1, "failures": []},
        coverage={"line_percent": 80, "baseline_percent": 80},
        prod_health={"ok": True},
        migration_validated_cli=False,
        pr_risk={"enforcement": {"merge_recommendation": "WARN"}},
    )
    assert res.outcome == "WARN"
    blob = "\n".join(res.blockers + res.warnings)
    assert "pr_risk.md" not in blob


def test_evaluate_cli_resolves_artifact_paths_under_repo_root(tmp_path: Path):
    """SCRUM-209 (gap #3): when artifact paths are relative, they resolve under --repo-root.

    Drives the CLI from a working directory unrelated to the project root and
    confirms the run succeeds. Before the fix this produced
    "Smoke results artifact missing" because read_json was called with a path
    resolved from cwd.
    """
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()
    artifacts_in = EXAMPLE / "artifacts"
    if artifacts_in.exists():
        shutil.rmtree(artifacts_in)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "release_readiness_core.readiness_evaluate",
            "--repo-root",
            str(EXAMPLE),
            "--config",
            "config.yaml",
            "--smoke-results",
            "evidence/smoke.json",
            "--e2e-results",
            "evidence/e2e.json",
            "--coverage",
            "evidence/coverage.json",
            "--empty-diff",
            "--output-dir",
            "artifacts/release-readiness",
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        assert proc.returncode == 0, f"CLI failed:\nstdout={proc.stdout}\nstderr={proc.stderr}"
        report_json = EXAMPLE / "artifacts" / "release-readiness" / "report.json"
        assert report_json.exists()
        payload = json.loads(report_json.read_text(encoding="utf-8"))
        assert payload["outcome"] == "PASS"
    finally:
        if artifacts_in.exists():
            shutil.rmtree(artifacts_in)
