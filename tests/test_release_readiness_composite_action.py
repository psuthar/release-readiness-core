"""Static tests for .github/actions/release-readiness/action.yml — covers the
existing inputs plus the new run-doctor wire-in."""

from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_PATH = REPO_ROOT / ".github" / "actions" / "release-readiness" / "action.yml"


def _load() -> dict:
    return yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))


def test_action_is_composite():
    assert _load()["runs"]["using"] == "composite"


def test_install_source_inputs_declared():
    inputs = _load()["inputs"]
    assert inputs["install-source"]["default"] == "git"
    assert "pypi-version" in inputs
    assert inputs["package-ref"].get("required", False) is False


def test_run_doctor_input_declared():
    inputs = _load()["inputs"]
    assert "run-doctor" in inputs
    rd = inputs["run-doctor"]
    assert rd["default"] == "false"
    # Required is False (or absent — argparse defaults).
    assert rd.get("required", False) is False


def test_run_doctor_default_preserves_today_behavior():
    """run-doctor must default to 'false' so the action's behavior is
    byte-identical to today when the input isn't passed."""
    text = ACTION_PATH.read_text(encoding="utf-8")
    # Regex-grep for 'default: "false"' near 'run-doctor:'
    rd_idx = text.find("run-doctor:")
    assert rd_idx > 0
    rd_block = text[rd_idx:rd_idx + 1000]
    assert 'default: "false"' in rd_block


def test_doctor_step_gated_on_run_doctor_input():
    steps = _load()["runs"]["steps"]
    doctor_steps = [s for s in steps if "release-readiness-doctor" in (s.get("run") or "")]
    assert doctor_steps, "missing release-readiness-doctor step"
    cond = doctor_steps[0].get("if", "")
    assert "run-doctor" in cond
    assert "true" in cond


def test_doctor_step_runs_before_evaluate_step():
    """The doctor step must run before evaluate so its findings catch
    misconfiguration before the evaluator emits a confusing BLOCK."""
    text = ACTION_PATH.read_text(encoding="utf-8")
    doctor_idx = text.find("release-readiness-doctor")
    evaluate_idx = text.find("release-readiness-evaluate")
    assert 0 < doctor_idx < evaluate_idx, (
        "doctor step must precede evaluate step"
    )


def test_doctor_failure_surfaces_as_error_annotation():
    text = ACTION_PATH.read_text(encoding="utf-8")
    # The doctor step must include a ::error file= annotation on failure.
    assert "::error file=" in text
    # And it must exit non-zero so the workflow fails.
    assert "exit 1" in text
