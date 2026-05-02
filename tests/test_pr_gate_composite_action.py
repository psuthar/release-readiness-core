"""Static + integration tests for the .github/actions/release-readiness-pr-gate composite.

Static checks: action.yml is well-formed, declares all expected inputs, runs
the four CLIs in the expected order with the right flags.

Integration check: chain the four CLIs end-to-end against synthetic evidence in
a tmp dir and validate the final pr-gate-check.json against the v1 schema.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

jsonschema = pytest.importorskip("jsonschema")

from release_readiness_core import pr_gate_check as chk
from release_readiness_core import pr_gate_combine as comb


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_PATH = REPO_ROOT / ".github" / "actions" / "release-readiness-pr-gate" / "action.yml"
SCHEMA_DIR = REPO_ROOT / "docs" / "contracts"


def _load_action() -> dict:
    return yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Static structure
# ---------------------------------------------------------------------------


def test_action_file_exists():
    assert ACTION_PATH.is_file(), f"missing composite action: {ACTION_PATH}"


def test_action_is_composite():
    action = _load_action()
    assert action.get("runs", {}).get("using") == "composite"


def test_action_declares_required_inputs():
    action = _load_action()
    inputs = action.get("inputs", {})
    expected = {
        "package-ref",
        "install-source",
        "pypi-version",
        "config-path",
        "pr-risk-config",
        "smoke-results",
        "e2e-results",
        "coverage",
        "prod-health",
        "base-ref",
        "output-dir",
        "check-name",
        "run-url",
        "warn-conclusion",
    }
    missing = expected - set(inputs.keys())
    assert not missing, f"missing inputs: {missing}"


def test_action_threads_warn_conclusion_to_check_payload_cli():
    """The composite must pass --warn-conclusion through to release-readiness-check-payload."""
    text = ACTION_PATH.read_text(encoding="utf-8")
    assert "--warn-conclusion" in text
    assert "inputs.warn-conclusion" in text or "inputs['warn-conclusion']" in text


def test_action_marks_package_ref_optional_for_pypi_install():
    action = _load_action()
    pkg = action["inputs"].get("package-ref", {})
    assert pkg.get("required", False) is False
    assert action["inputs"]["install-source"]["default"] == "git"


def test_action_exposes_gate_outputs():
    action = _load_action()
    outputs = action.get("outputs", {})
    assert "gate-status" in outputs
    assert "workflow-should-fail" in outputs


def test_action_runs_the_four_clis_in_order():
    action = _load_action()
    steps = action.get("runs", {}).get("steps", [])
    step_text = "\n".join(json.dumps(s) for s in steps)
    # Each CLI must appear at least once.
    for cli in (
        "release-readiness-pr-risk",
        "release-readiness-evaluate",
        "release-readiness-combine",
        "release-readiness-check-payload",
    ):
        assert cli in step_text, f"composite action does not invoke {cli}"

    # And must appear in the correct sequential order across step run blocks.
    order: list[str] = []
    for step in steps:
        run = step.get("run", "") or ""
        for cli in (
            "release-readiness-pr-risk",
            "release-readiness-evaluate",
            "release-readiness-combine",
            "release-readiness-check-payload",
        ):
            if cli in run and cli not in order:
                order.append(cli)
    assert order == [
        "release-readiness-pr-risk",
        "release-readiness-evaluate",
        "release-readiness-combine",
        "release-readiness-check-payload",
    ]


def test_action_emits_error_annotations_on_failure():
    """The composite must surface CLI failures as ::error file=...:: annotations."""
    text = ACTION_PATH.read_text(encoding="utf-8")
    assert "::error file=" in text


# ---------------------------------------------------------------------------
# Integration: run the four CLIs end-to-end and validate the final output.
# ---------------------------------------------------------------------------


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_chained_clis_produce_valid_pr_gate_check_json(tmp_path: Path):
    """Mirror what the composite action runs in CI: write synthetic
    pr-risk.json + release-readiness.json + report.json, then run combine +
    check-payload, then validate against v1 schemas."""
    parent = tmp_path / "artifacts"
    inner = parent / "release-readiness"
    inner.mkdir(parents=True)

    # Stand in for what release-readiness-pr-risk would emit.
    _write(parent / "pr-risk.json", {
        "merge_recommendation": "PASS",
        "score": 12,
        "band": "low",
        "test_confidence": 90,
        "required_validations": [],
        "top_risk_factors": [],
    })
    # Stand in for what release-readiness-evaluate would emit.
    _write(parent / "release-readiness.json", {
        "outcome": "PASS",
        "score": 100,
        "warnings": 0,
        "blockers": 0,
    })
    _write(inner / "report.json", {
        "blockers": [],
        "warnings": [],
        "recommended_actions": [],
    })

    gate_json, exit_code = comb.run(
        parent / "pr-risk.json",
        parent / "release-readiness.json",
        inner / "report.json",
        parent,
    )
    assert exit_code == 0
    summary_path = parent / "pr-gate-summary.json"
    assert summary_path.exists()

    summary_schema = json.loads((SCHEMA_DIR / "pr-gate-summary-v1.schema.json").read_text())
    jsonschema.validate(instance=gate_json, schema=summary_schema)

    payload = chk.run(summary_path, parent / "pr-gate-check.json")
    assert (parent / "pr-gate-check.json").exists()

    check_schema = json.loads((SCHEMA_DIR / "pr-gate-check-v1.schema.json").read_text())
    jsonschema.validate(instance=payload, schema=check_schema)
    assert payload["check_conclusion"] == "success"
    assert payload["workflow_should_fail"] is False


def test_chained_clis_block_on_blocker(tmp_path: Path):
    parent = tmp_path / "artifacts"
    inner = parent / "release-readiness"
    inner.mkdir(parents=True)

    _write(parent / "pr-risk.json", {
        "merge_recommendation": "BLOCK",
        "score": 80,
        "band": "high",
        "required_validations": ["Validate auth E2E"],
        "top_risk_factors": ["auth_endpoints"],
    })
    _write(parent / "release-readiness.json", {
        "outcome": "BLOCK", "score": 30, "warnings": 1, "blockers": 1,
    })
    _write(inner / "report.json", {
        "blockers": ["E2E auth_login spec failed"],
        "warnings": [],
        "recommended_actions": [],
    })

    gate_json, _ = comb.run(
        parent / "pr-risk.json",
        parent / "release-readiness.json",
        inner / "report.json",
        parent,
    )
    payload = chk.run(parent / "pr-gate-summary.json", parent / "pr-gate-check.json")

    assert gate_json["final_gate"]["status"] == "BLOCK"
    assert gate_json["final_gate"]["workflow_should_fail"] is True
    assert payload["check_conclusion"] == "failure"
    assert payload["workflow_should_fail"] is True
