"""Validate that pr-gate-summary.json + pr-gate-check.json outputs from the
combiner CLIs conform to the v1 JSON Schemas under docs/contracts/.

These tests are the contract guardrail: any change to the CLI output shape
must either match the existing schema or come with a v2 schema bump."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

from release_readiness_core import pr_gate_check as chk
from release_readiness_core import pr_gate_combine as comb


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "docs" / "contracts"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _pr_risk(tmp_path: Path, status: str = "PASS") -> Path:
    p = tmp_path / "pr-risk.json"
    _write(p, {
        "merge_recommendation": status,
        "score": 25 if status == "PASS" else 75,
        "band": "low" if status == "PASS" else "high",
        "test_confidence": 90,
        "required_validations": ["Validate auth flow"] if status != "PASS" else [],
        "top_risk_factors": [],
    })
    return p


def _readiness(tmp_path: Path, outcome: str = "PASS") -> Path:
    p = tmp_path / "release-readiness.json"
    _write(p, {
        "outcome": outcome,
        "score": 100 if outcome == "PASS" else (75 if outcome == "WARN" else 30),
        "warnings": 0 if outcome == "PASS" else 1,
        "blockers": 1 if outcome == "BLOCK" else 0,
    })
    return p


# ---------------------------------------------------------------------------
# pr-gate-summary-v1.schema.json
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", ["pass", "warn", "block"])
def test_combiner_output_validates_against_summary_schema(tmp_path: Path, scenario: str):
    schema = _load_schema("pr-gate-summary-v1.schema.json")

    if scenario == "pass":
        pr_risk = _pr_risk(tmp_path, "PASS")
        rr = _readiness(tmp_path, "PASS")
    elif scenario == "warn":
        pr_risk = _pr_risk(tmp_path, "PASS")
        rr = _readiness(tmp_path, "WARN")
    else:
        pr_risk = _pr_risk(tmp_path, "PASS")
        rr = _readiness(tmp_path, "BLOCK")

    gate_json, _ = comb.run(pr_risk, rr, None, tmp_path / "out")

    jsonschema.validate(instance=gate_json, schema=schema)


def test_partial_summary_validates_against_schema(tmp_path: Path):
    """When pr-risk.json is missing, partial summary must still match the schema."""
    schema = _load_schema("pr-gate-summary-v1.schema.json")
    rr = _readiness(tmp_path, "PASS")

    gate_json, exit_code = comb.run(tmp_path / "missing.json", rr, None, tmp_path / "out")
    assert exit_code == 1
    jsonschema.validate(instance=gate_json, schema=schema)


# ---------------------------------------------------------------------------
# pr-gate-check-v1.schema.json
# ---------------------------------------------------------------------------


def _build_summary_then_check(
    tmp_path: Path, *, rr_outcome: str, risk_status: str = "PASS"
) -> dict:
    pr_risk = _pr_risk(tmp_path, risk_status)
    rr = _readiness(tmp_path, rr_outcome)
    out = tmp_path / "out"
    comb.run(pr_risk, rr, None, out)
    return chk.run(out / "pr-gate-summary.json", out / "pr-gate-check.json")


@pytest.mark.parametrize("scenario,expected_conclusion", [
    ("pass", "success"),
    ("warn", "action_required"),
    ("block", "failure"),
])
def test_check_payload_validates_against_check_schema(
    tmp_path: Path, scenario: str, expected_conclusion: str
):
    schema = _load_schema("pr-gate-check-v1.schema.json")
    payload = _build_summary_then_check(
        tmp_path,
        rr_outcome={"pass": "PASS", "warn": "WARN", "block": "BLOCK"}[scenario],
    )

    jsonschema.validate(instance=payload, schema=schema)
    assert payload["check_conclusion"] == expected_conclusion


def test_check_payload_for_missing_input_validates_against_check_schema(tmp_path: Path):
    schema = _load_schema("pr-gate-check-v1.schema.json")
    payload = chk.run(tmp_path / "missing.json", tmp_path / "out.json")

    jsonschema.validate(instance=payload, schema=schema)
    assert payload["check_conclusion"] == "failure"
    assert payload["workflow_should_fail"] is True
    assert payload["final_gate_status"] == "ERROR"


# ---------------------------------------------------------------------------
# Schema sanity
# ---------------------------------------------------------------------------


def test_summary_schema_is_well_formed():
    schema = _load_schema("pr-gate-summary-v1.schema.json")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_check_schema_is_well_formed():
    schema = _load_schema("pr-gate-check-v1.schema.json")
    jsonschema.Draft202012Validator.check_schema(schema)
