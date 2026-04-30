"""Tests for release_readiness_core.readiness_engine."""

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


def test_risk_category_mapping_uses_config_when_present():
    """SCRUM-207: a config-supplied mapping replaces identity for that category."""
    cfg = {
        **BASE_CONFIG,
        "risk_category_to_required_validation": {"migrations": "migrations_validated"},
    }
    # No evidence at all for migrations_validated → BLOCK with the mapped key required.
    res = compute_readiness(
        config=cfg,
        changed_files=["db/migrations/000099_add_thing.up.sql"],
        smoke=smoke_passed(),
        e2e=e2e_passed(),
        coverage={"line_percent": 50, "baseline_percent": 50},
        prod_health={"ok": True},
        migration_validated_cli=False,
    )
    assert res.outcome == "BLOCK"
    assert "migrations_validated" in res.validations_required
    assert "migrations" not in res.validations_required


def test_risk_category_mapping_satisfied_via_cli_flag():
    """When the mapping points at migrations_validated, --migration-validated still satisfies it."""
    cfg = {
        **BASE_CONFIG,
        "risk_category_to_required_validation": {"migrations": "migrations_validated"},
    }
    res = compute_readiness(
        config=cfg,
        changed_files=["db/migrations/000099_add_thing.up.sql"],
        smoke=smoke_passed(),
        e2e=e2e_passed(),
        coverage={"line_percent": 50, "baseline_percent": 50},
        prod_health={"ok": True},
        migration_validated_cli=True,
    )
    assert res.outcome == "PASS"


def test_risk_category_non_identity_mapping():
    """SCRUM-207: an unrelated project can map auth_endpoints risk → auth_login validation."""
    cfg = {
        **BASE_CONFIG,
        "validations": {**BASE_CONFIG["validations"], "auth_login": {"description": "auth"}},
        "risk_from_paths": [
            {"categories": ["auth_endpoints"], "patterns": ["src/auth/**"]},
        ],
        "risk_category_to_required_validation": {"auth_endpoints": "auth_login"},
    }
    # auth_login satisfied via explicit nested validation evidence.
    res = compute_readiness(
        config=cfg,
        changed_files=["src/auth/login.py"],
        smoke=smoke_passed(),
        e2e=e2e_passed(validations={"auth_login": True}),
        coverage={"line_percent": 50, "baseline_percent": 50},
        prod_health={"ok": True},
        migration_validated_cli=False,
    )
    assert res.outcome == "PASS"
    assert "auth_login" in res.validations_required
    assert "auth_endpoints" not in res.validations_required


def test_risk_category_falls_back_to_identity_when_mapping_absent():
    """Without risk_category_to_required_validation, identity mapping still applies."""
    cfg = {
        **BASE_CONFIG,
        "risk_from_paths": [
            {"categories": ["custom_area"], "patterns": ["src/custom/**"]},
        ],
    }
    res = compute_readiness(
        config=cfg,
        changed_files=["src/custom/thing.py"],
        smoke=smoke_passed(),
        e2e=e2e_passed(validations={"custom_area": True}),
        coverage={"line_percent": 50, "baseline_percent": 50},
        prod_health={"ok": True},
        migration_validated_cli=False,
    )
    assert res.outcome == "PASS"
    assert "custom_area" in res.validations_required


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


def test_optional_prod_health_not_declared_warns():
    """Default behavior preserved: missing prod_health → warning + penalty."""
    res = compute_readiness(
        config=BASE_CONFIG,
        changed_files=[],
        smoke=smoke_passed(),
        e2e=e2e_passed(),
        coverage={"line_percent": 50, "baseline_percent": 50},
        prod_health=None,
        migration_validated_cli=False,
    )
    assert any("Production health snapshot" in w for w in res.warnings)
    assert res.score < 100  # penalty fired


def test_optional_prod_health_declared_no_warning_no_penalty():
    """SCRUM-208: when prod_health is opted-in via optional_artifacts, missing it is silent."""
    cfg = {**BASE_CONFIG, "optional_artifacts": ["prod_health"]}
    res = compute_readiness(
        config=cfg,
        changed_files=[],
        smoke=smoke_passed(),
        e2e=e2e_passed(),
        coverage={"line_percent": 50, "baseline_percent": 50},
        prod_health=None,
        migration_validated_cli=False,
    )
    assert not any("Production health" in w for w in res.warnings)
    assert res.outcome == "PASS"
    assert res.score == 100.0


def test_optional_coverage_declared_no_warning_no_penalty():
    """SCRUM-208: same opt-in path covers coverage."""
    cfg = {**BASE_CONFIG, "optional_artifacts": ["coverage", "prod_health"]}
    res = compute_readiness(
        config=cfg,
        changed_files=[],
        smoke=smoke_passed(),
        e2e=e2e_passed(),
        coverage=None,
        prod_health=None,
        migration_validated_cli=False,
    )
    assert not any("Coverage" in w for w in res.warnings)
    assert not any("Production health" in w for w in res.warnings)
    assert res.outcome == "PASS"
    assert res.score == 100.0


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
