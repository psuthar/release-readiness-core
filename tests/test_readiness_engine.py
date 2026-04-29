"""Tests for release_readiness_core.readiness_engine (ported from TalkBack scripts)."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from release_readiness_core.readiness_engine import (
    build_remediation_items,
    compute_readiness,
    merge_validations,
)

BASE_CONFIG = {
    "validations": {
        "auth_session": {"description": "auth"},
        "upload_extraction": {"description": "upload"},
    },
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
    "e2e_critical_name_patterns": ["login", "session", "upload", "material", "invite"],
    "risk_from_paths": [
        {
            "categories": ["upload_extraction"],
            "patterns": ["internal/handlers/session_materials.go"],
        },
        {
            "categories": ["migrations"],
            "patterns": ["db/migrations/**"],
        },
    ],
    "risky_config_patterns": ["Dockerfile"],
    "infer_validations_when_pass": {
        "smoke": ["upload_extraction"],
        "e2e": ["upload_extraction"],
    },
}


def smoke_passed(validations=None):
    return {
        "status": "passed",
        "failed_count": 0,
        "total_count": 1,
        "validations": validations or {},
    }


def e2e_passed(validations=None):
    return {
        "status": "passed",
        "failed_count": 0,
        "total_count": 1,
        "retries": 0,
        "failures": [],
        "validations": validations or {},
    }


def e2e_failed_with_failures(failures, failed_count=1, retries=0):
    return {
        "status": "failed",
        "failed_count": failed_count,
        "total_count": 1,
        "retries": retries,
        "failures": failures,
    }


def test_merge_validations_respects_evidence_boolean_keys_override():
    cfg = {**BASE_CONFIG, "evidence_boolean_keys": ["auth_session"]}
    smoke = {
        "status": "passed",
        "failed_count": 0,
        "validations": {},
        "nav_assets": True,
    }
    out = merge_validations(smoke, None, cfg)
    assert out.get("nav_assets") is not True
    assert "nav_assets" not in out


def test_smoke_failed_blocks():
    res = compute_readiness(
        config=BASE_CONFIG,
        changed_files=["internal/handlers/session_materials.go"],
        smoke={"status": "failed", "failed_count": 1, "total_count": 1},
        e2e=e2e_passed(),
        coverage={"line_percent": 50, "baseline_percent": 51},
        prod_health={"ok": True},
        migration_validated_cli=False,
    )
    assert res.outcome == "BLOCK"
    assert "smoke_failed" in res.failed_checks


def test_critical_e2e_blocks():
    res = compute_readiness(
        config=BASE_CONFIG,
        changed_files=["internal/handlers/session_materials.go"],
        smoke=smoke_passed(),
        e2e=e2e_failed_with_failures([{"title": "login flow failed", "name": "login_flow"}]),
        coverage={"line_percent": 50, "baseline_percent": 51},
        prod_health={"ok": True},
        migration_validated_cli=False,
    )
    assert res.outcome == "BLOCK"
    assert "e2e_critical" in res.failed_checks


def test_migrations_without_validation_blocks():
    res = compute_readiness(
        config=BASE_CONFIG,
        changed_files=["db/migrations/000012_add_video_ingestion_fields.up.sql"],
        smoke=smoke_passed(),
        e2e=e2e_passed(),
        coverage={"line_percent": 50, "baseline_percent": 51},
        prod_health={"ok": True},
        migration_validated_cli=False,
    )
    assert res.outcome == "BLOCK"
    assert "risk_without_validation" in res.failed_checks


def test_happy_path_passes():
    res = compute_readiness(
        config=BASE_CONFIG,
        changed_files=["internal/handlers/session_materials.go"],
        smoke=smoke_passed(),
        e2e=e2e_passed(),
        coverage={"line_percent": 50, "baseline_percent": 50},
        prod_health={"ok": True},
        migration_validated_cli=False,
    )
    assert res.outcome == "PASS"
    assert res.failed_checks == []


def test_build_remediation_items_fallback_for_unknown_key():
    items = build_remediation_items(["unknown_check"], {})
    assert len(items) == 1
    assert items[0]["check"] == "unknown_check"
    assert "unknown_check" in items[0]["recommended_action"]


def test_pr_risk_warn_demotes_to_warn():
    res = compute_readiness(
        config=BASE_CONFIG,
        changed_files=[],
        smoke=smoke_passed(),
        e2e=e2e_passed(),
        coverage={"line_percent": 50, "baseline_percent": 50},
        prod_health={"ok": True},
        migration_validated_cli=False,
        pr_risk={
            "enforcement": {"merge_recommendation": "warn", "evidence_summary": {}},
            "risk_band": "medium",
            "risk_score": 35.0,
        },
    )
    assert res.outcome == "WARN"
    assert "pr_risk_warn" in res.failed_checks


def test_readiness_result_asdict_includes_failed_title_fields():
    res = compute_readiness(
        config=BASE_CONFIG,
        changed_files=[],
        smoke=smoke_passed(),
        e2e=e2e_passed(),
        coverage={"line_percent": 50, "baseline_percent": 50},
        prod_health={"ok": True},
        migration_validated_cli=False,
    )
    payload = asdict(res)
    assert "critical_failed_titles" in payload
    assert "non_critical_failed_titles" in payload
