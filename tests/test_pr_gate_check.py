"""Unit tests for ``release_readiness_core.pr_gate_check``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from release_readiness_core import pr_gate_check as chk


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _gate_summary(status: str, *, workflow_should_fail: bool | None = None) -> dict:
    fg = {"status": status, "confidence": "moderate", "summary": f"final: {status}"}
    if workflow_should_fail is not None:
        fg["workflow_should_fail"] = workflow_should_fail
    return {
        "version": "v1",
        "pr_risk": {"status": "PASS", "label": "PASS (low risk)", "score": 12.0, "band": "low"},
        "release_readiness": {"status": status, "score": 100.0, "warnings": 0, "blockers": 0},
        "final_gate": fg,
        "required_actions": ["CI checks must pass"],
    }


# ---------------------------------------------------------------------------
# Status → conclusion mapping
# ---------------------------------------------------------------------------


def test_conclusion_for_pass_is_success():
    assert chk.conclusion_for_status("PASS") == "success"


def test_conclusion_for_warn_is_action_required():
    assert chk.conclusion_for_status("WARN") == "action_required"


def test_conclusion_for_block_is_failure():
    assert chk.conclusion_for_status("BLOCK") == "failure"


def test_conclusion_for_unknown_is_failure():
    assert chk.conclusion_for_status("UNKNOWN") == "failure"


@pytest.mark.parametrize(
    "warn_conclusion,expected",
    [
        ("action_required", "action_required"),
        ("failure", "failure"),
        ("neutral", "neutral"),
    ],
)
def test_conclusion_for_warn_respects_override(warn_conclusion, expected):
    assert chk.conclusion_for_status("WARN", warn_conclusion) == expected


def test_conclusion_for_pass_ignores_warn_conclusion():
    # WARN override must not affect non-WARN statuses.
    assert chk.conclusion_for_status("PASS", "failure") == "success"
    assert chk.conclusion_for_status("BLOCK", "neutral") == "failure"


# ---------------------------------------------------------------------------
# Payload from gate JSON
# ---------------------------------------------------------------------------


def test_pass_payload_has_success_and_no_workflow_fail():
    payload = chk.build_payload_from_dict(_gate_summary("PASS", workflow_should_fail=False))
    assert payload["check_conclusion"] == "success"
    assert payload["workflow_should_fail"] is False
    assert payload["final_gate_status"] == "PASS"
    assert payload["title"] == "release-readiness: PASS"


def test_warn_payload_uses_action_required():
    payload = chk.build_payload_from_dict(_gate_summary("WARN", workflow_should_fail=False))
    assert payload["check_conclusion"] == "action_required"
    assert payload["workflow_should_fail"] is False


@pytest.mark.parametrize("warn_conclusion", ["action_required", "failure", "neutral"])
def test_warn_payload_threads_warn_conclusion(warn_conclusion):
    payload = chk.build_payload_from_dict(
        _gate_summary("WARN", workflow_should_fail=False),
        warn_conclusion=warn_conclusion,
    )
    assert payload["check_conclusion"] == warn_conclusion
    # workflow_should_fail is independent — driven by gate.workflow_should_fail.
    assert payload["workflow_should_fail"] is False


def test_block_payload_fails_workflow():
    payload = chk.build_payload_from_dict(_gate_summary("BLOCK", workflow_should_fail=True))
    assert payload["check_conclusion"] == "failure"
    assert payload["workflow_should_fail"] is True


def test_invalid_status_returns_error_payload():
    bad = _gate_summary("PASS")
    bad["final_gate"]["status"] = "MAYBE"
    payload = chk.build_payload_from_dict(bad)
    assert payload["check_conclusion"] == "failure"
    assert payload["workflow_should_fail"] is True
    assert payload["final_gate_status"] == "ERROR"


def test_check_name_is_overrideable():
    payload = chk.build_payload_from_dict(
        _gate_summary("PASS", workflow_should_fail=False), check_name="my-gate"
    )
    assert payload["check_name"] == "my-gate"
    assert payload["title"].startswith("my-gate")


# ---------------------------------------------------------------------------
# run() — file IO
# ---------------------------------------------------------------------------


def test_run_writes_payload(tmp_path: Path):
    gate = tmp_path / "pr-gate-summary.json"
    _write(gate, _gate_summary("PASS", workflow_should_fail=False))
    out = tmp_path / "pr-gate-check.json"

    payload = chk.run(gate, out)

    assert out.exists()
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written == payload
    assert written["check_conclusion"] == "success"


def test_run_handles_missing_file(tmp_path: Path):
    out = tmp_path / "pr-gate-check.json"

    payload = chk.run(tmp_path / "missing.json", out)

    assert payload["check_conclusion"] == "failure"
    assert payload["workflow_should_fail"] is True
    assert "not found" in payload["text"].lower()


def test_run_handles_invalid_json(tmp_path: Path):
    bad = tmp_path / "pr-gate-summary.json"
    bad.write_text("not json {", encoding="utf-8")
    out = tmp_path / "pr-gate-check.json"

    payload = chk.run(bad, out)

    assert payload["check_conclusion"] == "failure"
    assert payload["workflow_should_fail"] is True


def test_run_is_byte_deterministic(tmp_path: Path):
    gate = tmp_path / "pr-gate-summary.json"
    _write(gate, _gate_summary("WARN", workflow_should_fail=False))
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    chk.run(gate, out1)
    chk.run(gate, out2)

    assert out1.read_bytes() == out2.read_bytes()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def test_main_writes_payload(tmp_path: Path):
    gate = tmp_path / "pr-gate-summary.json"
    _write(gate, _gate_summary("BLOCK", workflow_should_fail=True))
    out = tmp_path / "pr-gate-check.json"

    rc = chk.main([
        "--gate-json", str(gate),
        "--output", str(out),
        "--check-name", "release-readiness",
    ])
    assert rc == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["check_conclusion"] == "failure"
    assert payload["workflow_should_fail"] is True


@pytest.mark.parametrize("warn_conclusion", ["action_required", "failure", "neutral"])
def test_main_threads_warn_conclusion_flag(tmp_path: Path, warn_conclusion):
    gate = tmp_path / "pr-gate-summary.json"
    _write(gate, _gate_summary("WARN", workflow_should_fail=False))
    out = tmp_path / "pr-gate-check.json"

    rc = chk.main([
        "--gate-json", str(gate),
        "--output", str(out),
        "--warn-conclusion", warn_conclusion,
    ])
    assert rc == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["check_conclusion"] == warn_conclusion
    assert payload["final_gate_status"] == "WARN"


def test_main_rejects_invalid_warn_conclusion(tmp_path: Path):
    gate = tmp_path / "pr-gate-summary.json"
    _write(gate, _gate_summary("WARN", workflow_should_fail=False))

    with pytest.raises(SystemExit):
        chk.main([
            "--gate-json", str(gate),
            "--output", str(tmp_path / "out.json"),
            "--warn-conclusion", "not_a_valid_conclusion",
        ])
