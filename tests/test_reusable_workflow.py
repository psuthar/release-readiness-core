"""Static tests for the reusable readiness.yml workflow + smoke workflows.

The reusable workflow's runtime behavior (install + composite chain + enforce)
is exercised manually via the smoke workflows. These tests assert structure so
schema regressions surface in this repo's CI before they reach adopters.
"""

from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
REUSABLE = WORKFLOWS / "readiness.yml"
SMOKE_PASS = WORKFLOWS / "smoke-readiness-pass.yml"
SMOKE_BLOCK = WORKFLOWS / "smoke-readiness-block.yml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Reusable workflow structure
# ---------------------------------------------------------------------------


def test_reusable_workflow_exists():
    assert REUSABLE.is_file()


def test_reusable_workflow_uses_workflow_call():
    wf = _load(REUSABLE)
    # PyYAML loads the YAML key `on` as the Python boolean True. Accept both.
    on_block = wf.get("on") if "on" in wf else wf.get(True)
    assert on_block is not None, "missing 'on' block"
    assert "workflow_call" in on_block


def test_reusable_workflow_declares_required_inputs():
    wf = _load(REUSABLE)
    on_block = wf.get("on") if "on" in wf else wf.get(True)
    inputs = on_block["workflow_call"].get("inputs", {})
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
        "enforcement-mode",
        "comment-on-pr",
        "publish-check",
        "combine-with-pr-risk",
        "run-doctor",
        "check-name",
        "output-dir",
    }
    missing = expected - set(inputs.keys())
    assert not missing, f"missing inputs: {missing}"


def test_reusable_workflow_marks_package_ref_required():
    wf = _load(REUSABLE)
    on_block = wf.get("on") if "on" in wf else wf.get(True)
    inputs = on_block["workflow_call"].get("inputs", {})
    assert inputs["package-ref"].get("required") is True


def test_reusable_workflow_exposes_outputs():
    wf = _load(REUSABLE)
    on_block = wf.get("on") if "on" in wf else wf.get(True)
    outputs = on_block["workflow_call"].get("outputs", {})
    assert "gate-status" in outputs
    assert "workflow-should-fail" in outputs


def test_reusable_workflow_chains_composites_in_order():
    """The readiness job must call the pr-gate composite then the publish
    composite then the enforce step."""
    text = REUSABLE.read_text(encoding="utf-8")
    pr_gate_idx = text.find("./.github/actions/release-readiness-pr-gate")
    publish_idx = text.find("./.github/actions/release-readiness-publish")
    enforce_idx = text.find("Enforce gate")
    assert pr_gate_idx > 0
    assert publish_idx > pr_gate_idx, "publish must follow pr-gate"
    assert enforce_idx > publish_idx, "enforce must follow publish"


def test_reusable_workflow_passes_secrets_via_github_token():
    """GitHub token must be threaded through to the publish step."""
    text = REUSABLE.read_text(encoding="utf-8")
    assert "secrets.GITHUB_TOKEN" in text


def test_reusable_workflow_supports_doctor_pre_flight():
    wf = _load(REUSABLE)
    text = REUSABLE.read_text(encoding="utf-8")
    on_block = wf.get("on") if "on" in wf else wf.get(True)
    inputs = on_block["workflow_call"].get("inputs", {})
    assert "run-doctor" in inputs
    assert "release-readiness-doctor" in text


def test_reusable_workflow_supports_combine_with_pr_risk_off():
    """When combine-with-pr-risk is false, the workflow must still produce
    a gate verdict via release-readiness-evaluate alone."""
    text = REUSABLE.read_text(encoding="utf-8")
    assert "release-readiness-evaluate" in text
    assert "evaluate-only-gate" in text


def test_reusable_workflow_enforcement_modes():
    text = REUSABLE.read_text(encoding="utf-8")
    assert "block_only" in text
    assert "warn_and_block" in text


# ---------------------------------------------------------------------------
# Smoke workflows
# ---------------------------------------------------------------------------


def test_smoke_pass_workflow_exists():
    assert SMOKE_PASS.is_file()


def test_smoke_block_workflow_exists():
    assert SMOKE_BLOCK.is_file()


def test_smoke_workflows_call_reusable_at_local_path():
    """Both smoke workflows must call the reusable workflow at ./.github/workflows/readiness.yml
    so they exercise the in-repo version (not a remote SHA)."""
    for path in (SMOKE_PASS, SMOKE_BLOCK):
        text = path.read_text(encoding="utf-8")
        assert "uses: ./.github/workflows/readiness.yml" in text, f"{path.name} does not call local reusable workflow"


def test_smoke_workflows_are_workflow_dispatch_only():
    """Smoke workflows must not run on push/PR (they require live install of the package)."""
    for path in (SMOKE_PASS, SMOKE_BLOCK):
        wf = _load(path)
        on_block = wf.get("on") if "on" in wf else wf.get(True)
        triggers = list(on_block.keys()) if isinstance(on_block, dict) else [on_block]
        assert triggers == ["workflow_dispatch"], (
            f"{path.name} should be workflow_dispatch only, got {triggers}"
        )


def test_smoke_pass_verifies_pass_outcome():
    text = SMOKE_PASS.read_text(encoding="utf-8")
    assert 'if [ "$STATUS" != "PASS" ]' in text


def test_smoke_block_verifies_block_outcome():
    text = SMOKE_BLOCK.read_text(encoding="utf-8")
    assert 'if [ "$STATUS" != "BLOCK" ]' in text
    # Block smoke must use continue-on-error so the verify job sees the BLOCK signal.
    assert "continue-on-error: true" in text
