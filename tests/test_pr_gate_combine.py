"""Unit tests for ``release_readiness_core.pr_gate_combine``.

Covers the contract for ``release-readiness-combine``: BLOCK > WARN > PASS
precedence, missing-input handling, ``workflow_should_fail`` flag, and
deterministic / sort_keys=True JSON output.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from release_readiness_core import pr_gate_combine as comb


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _pr_risk_pass(tmp_path: Path) -> Path:
    p = tmp_path / "pr-risk.json"
    _write(p, {
        "merge_recommendation": "PASS",
        "score": 12,
        "band": "low",
        "test_confidence": 90,
        "required_validations": [],
        "top_risk_factors": [],
    })
    return p


def _readiness_pass(tmp_path: Path) -> Path:
    p = tmp_path / "release-readiness.json"
    _write(p, {"outcome": "PASS", "score": 100, "warnings": 0, "blockers": 0})
    return p


def _readiness_warn(tmp_path: Path) -> Path:
    p = tmp_path / "release-readiness.json"
    _write(p, {"outcome": "WARN", "score": 75, "warnings": 1, "blockers": 0})
    return p


def _readiness_block(tmp_path: Path) -> Path:
    p = tmp_path / "release-readiness.json"
    _write(p, {"outcome": "BLOCK", "score": 30, "warnings": 1, "blockers": 1})
    return p


# ---------------------------------------------------------------------------
# Status precedence
# ---------------------------------------------------------------------------


def test_compute_gate_status_block_wins():
    assert comb.compute_gate_status("PASS", "BLOCK") == "BLOCK"
    assert comb.compute_gate_status("BLOCK", "PASS") == "BLOCK"
    assert comb.compute_gate_status("WARN", "BLOCK") == "BLOCK"


def test_compute_gate_status_warn_beats_pass():
    assert comb.compute_gate_status("PASS", "WARN") == "WARN"
    assert comb.compute_gate_status("WARN", "PASS") == "WARN"


def test_compute_gate_status_pass_when_both_pass():
    assert comb.compute_gate_status("PASS", "PASS") == "PASS"


def test_normalize_status_rejects_unknown():
    with pytest.raises(ValueError):
        comb.normalize_status("MAYBE")


def test_normalize_status_handles_case_and_padding():
    assert comb.normalize_status("  pass ") == "PASS"
    assert comb.normalize_status("Block") == "BLOCK"


# ---------------------------------------------------------------------------
# End-to-end run() — happy path
# ---------------------------------------------------------------------------


def test_run_pass_writes_summary_files(tmp_path: Path):
    pr_risk = _pr_risk_pass(tmp_path)
    rr = _readiness_pass(tmp_path)
    out = tmp_path / "out"

    gate_json, exit_code = comb.run(pr_risk, rr, None, out)

    assert exit_code == 0
    assert gate_json["final_gate"]["status"] == "PASS"
    assert gate_json["final_gate"]["workflow_should_fail"] is False
    assert (out / "pr-gate-summary.json").exists()
    assert (out / "pr-gate-summary.md").exists()


def test_run_warn_when_readiness_warns(tmp_path: Path):
    pr_risk = _pr_risk_pass(tmp_path)
    rr = _readiness_warn(tmp_path)

    gate_json, exit_code = comb.run(pr_risk, rr, None, tmp_path / "out")

    assert exit_code == 0
    assert gate_json["final_gate"]["status"] == "WARN"
    assert gate_json["final_gate"]["workflow_should_fail"] is False


def test_run_block_when_readiness_blocks(tmp_path: Path):
    pr_risk = _pr_risk_pass(tmp_path)
    rr = _readiness_block(tmp_path)

    gate_json, exit_code = comb.run(pr_risk, rr, None, tmp_path / "out")

    assert exit_code == 0
    assert gate_json["final_gate"]["status"] == "BLOCK"
    assert gate_json["final_gate"]["workflow_should_fail"] is True


def test_run_block_when_pr_risk_blocks(tmp_path: Path):
    pr_risk = tmp_path / "pr-risk.json"
    _write(pr_risk, {
        "merge_recommendation": "BLOCK",
        "score": 80,
        "band": "high",
        "required_validations": ["Validate auth flow"],
        "top_risk_factors": ["auth_endpoints"],
    })
    rr = _readiness_pass(tmp_path)

    gate_json, exit_code = comb.run(pr_risk, rr, None, tmp_path / "out")

    assert exit_code == 0
    assert gate_json["final_gate"]["status"] == "BLOCK"
    assert "Validate auth flow" in gate_json["required_actions"]


# ---------------------------------------------------------------------------
# Missing / malformed inputs
# ---------------------------------------------------------------------------


def test_run_with_missing_pr_risk_returns_block_and_exit_1(tmp_path: Path):
    rr = _readiness_pass(tmp_path)
    out = tmp_path / "out"

    gate_json, exit_code = comb.run(tmp_path / "missing.json", rr, None, out)

    assert exit_code == 1
    assert gate_json["final_gate"]["status"] == "BLOCK"
    assert gate_json["final_gate"]["workflow_should_fail"] is True
    # Partial summary must still be written.
    assert (out / "pr-gate-summary.json").exists()
    assert (out / "pr-gate-summary.md").exists()


def test_run_with_missing_readiness_returns_block_and_exit_1(tmp_path: Path):
    pr_risk = _pr_risk_pass(tmp_path)
    out = tmp_path / "out"

    gate_json, exit_code = comb.run(pr_risk, tmp_path / "missing.json", None, out)

    assert exit_code == 1
    assert gate_json["final_gate"]["status"] == "BLOCK"


def test_run_with_invalid_status_returns_block(tmp_path: Path):
    pr_risk = tmp_path / "pr-risk.json"
    _write(pr_risk, {"merge_recommendation": "MAYBE", "score": 10, "band": "low"})
    rr = _readiness_pass(tmp_path)

    gate_json, exit_code = comb.run(pr_risk, rr, None, tmp_path / "out")

    assert exit_code == 1
    assert gate_json["final_gate"]["status"] == "BLOCK"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_run_is_byte_deterministic(tmp_path: Path):
    pr_risk = _pr_risk_pass(tmp_path)
    rr = _readiness_warn(tmp_path)

    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    comb.run(pr_risk, rr, None, out1)
    comb.run(pr_risk, rr, None, out2)

    a = (out1 / "pr-gate-summary.json").read_bytes()
    b = (out2 / "pr-gate-summary.json").read_bytes()
    assert a == b


# ---------------------------------------------------------------------------
# Required actions: dedupe + ordering
# ---------------------------------------------------------------------------


def test_required_actions_deduplicate_case_insensitively(tmp_path: Path):
    pr_risk = tmp_path / "pr-risk.json"
    _write(pr_risk, {
        "merge_recommendation": "WARN",
        "score": 50,
        "band": "medium",
        "required_validations": ["Run auth E2E", "run auth e2e"],
    })
    rr = _readiness_warn(tmp_path)

    gate_json, _ = comb.run(pr_risk, rr, None, tmp_path / "out")
    actions = gate_json["required_actions"]
    # Standard items first, then "Run auth E2E" once.
    assert actions[0] == "CI checks must pass"
    assert actions.count("Run auth E2E") + actions.count("run auth e2e") == 1


def test_required_actions_pull_blockers_from_report(tmp_path: Path):
    pr_risk = _pr_risk_pass(tmp_path)
    rr = _readiness_block(tmp_path)
    report = tmp_path / "report.json"
    _write(report, {
        "blockers": ["E2E auth_login spec failed"],
        "warnings": ["Coverage regression"],
        "recommended_actions": ["Re-run smoke job"],
    })

    gate_json, _ = comb.run(pr_risk, rr, report, tmp_path / "out")
    actions = gate_json["required_actions"]
    assert "E2E auth_login spec failed" in actions
    assert "Coverage regression" in actions
    assert "Re-run smoke job" in actions
    assert gate_json["report_enriched"] is True


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def test_main_returns_zero_on_pass(tmp_path: Path):
    pr_risk = _pr_risk_pass(tmp_path)
    rr = _readiness_pass(tmp_path)
    out = tmp_path / "out"

    rc = comb.main([
        "--pr-risk-json", str(pr_risk),
        "--readiness-json", str(rr),
        "--readiness-report-json", str(tmp_path / "no-report.json"),
        "--output-dir", str(out),
    ])
    assert rc == 0


def test_main_returns_one_on_missing_input(tmp_path: Path):
    rr = _readiness_pass(tmp_path)
    out = tmp_path / "out"

    rc = comb.main([
        "--pr-risk-json", str(tmp_path / "missing.json"),
        "--readiness-json", str(rr),
        "--readiness-report-json", str(tmp_path / "no-report.json"),
        "--output-dir", str(out),
    ])
    assert rc == 1
