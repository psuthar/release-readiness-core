"""Smoke tests for optional adapters."""

from __future__ import annotations

from pathlib import Path

from release_readiness_core.adapters.playwright_results import convert
from release_readiness_core.adapters.pr_risk_semantic import build_semantic_record


def test_playwright_convert_skipped_when_empty():
    out = convert({"stats": {}, "suites": []})
    assert out["status"] == "skipped"


def test_pr_risk_semantic_pass_low_risk():
    rec = build_semantic_record(
        generator_outcome="success",
        pr_risk_path=Path("artifacts/pr-risk.json"),
        pr_risk_raw={
            "merge_recommendation": "PASS",
            "score": 10,
            "band": "low",
            "top_risk_factors": [],
        },
    )
    assert rec["workflow_should_fail"] is False
    assert rec.get("merge_recommendation") == "PASS"
