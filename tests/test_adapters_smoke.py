"""Smoke tests for optional adapters."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from release_readiness_core.adapters.playwright_results import (
    DEFAULT_SPEC_EXTENSIONS,
    convert,
    _load_validation_map,
    _parse_spec_extensions,
    _stem_for_spec,
)
from release_readiness_core.adapters.pr_risk_semantic import build_semantic_record


def test_playwright_convert_skipped_when_empty():
    out = convert({"stats": {}, "suites": []})
    assert out["status"] == "skipped"
    assert out["validations"] == {}


def _spec(file: str, title: str = "t", ok: bool = True) -> dict:
    return {"file": file, "title": title, "ok": ok, "tests": [{"results": [{"status": "passed"}]}]}


def test_playwright_validation_map_assigns_groups_when_passing():
    payload = {
        "stats": {"expected": 2},
        "suites": [
            {"file": "tests/login-flow.e2e.ts", "specs": [_spec("tests/login-flow.e2e.ts", "logs in")]},
            {"file": "tests/cart-checkout.e2e.ts", "specs": [_spec("tests/cart-checkout.e2e.ts", "checks out")]},
        ],
    }
    out = convert(
        payload,
        validation_map={
            "auth_session": ["login-flow"],
            "checkout": ["cart-checkout"],
            "absent_group": ["never-seen"],
        },
    )
    assert out["validations"] == {"auth_session": True, "checkout": True}
    assert out["status"] == "passed"


def test_playwright_validation_map_marks_failure_when_any_test_fails():
    payload = {
        "stats": {"expected": 1, "unexpected": 1},
        "suites": [
            {"file": "tests/login-flow.e2e.ts", "specs": [_spec("tests/login-flow.e2e.ts", "ok")]},
            {
                "file": "tests/login-flow.e2e.ts",
                "specs": [_spec("tests/login-flow.e2e.ts", "broken", ok=False)],
            },
        ],
    }
    out = convert(payload, validation_map={"auth_session": ["login-flow"]})
    assert out["validations"] == {"auth_session": False}
    assert out["status"] == "failed"
    assert out["failed_count"] == 1


def test_playwright_custom_spec_extensions_strip_correctly():
    payload = {
        "stats": {"expected": 1},
        "suites": [
            {"file": "tests/widget.spec.tsx", "specs": [_spec("tests/widget.spec.tsx", "renders")]},
        ],
    }
    out = convert(
        payload,
        validation_map={"ui": ["widget"]},
        spec_extensions=[".tsx", ".spec"],
    )
    assert out["validations"] == {"ui": True}


def test_playwright_no_map_emits_empty_validations():
    payload = {
        "stats": {"expected": 1},
        "suites": [
            {"file": "tests/login-flow.e2e.ts", "specs": [_spec("tests/login-flow.e2e.ts", "ok")]},
        ],
    }
    out = convert(payload)
    assert out["validations"] == {}
    assert out["status"] == "passed"


def test_stem_for_spec_strips_default_extensions():
    assert _stem_for_spec("tests/foo.e2e.ts", DEFAULT_SPEC_EXTENSIONS) == "foo"
    assert _stem_for_spec("tests\\bar.e2e", DEFAULT_SPEC_EXTENSIONS) == "bar"
    assert _stem_for_spec("tests/baz.js", DEFAULT_SPEC_EXTENSIONS) == "baz"


def test_load_validation_map_yaml(tmp_path: Path):
    p = tmp_path / "map.yaml"
    p.write_text(
        "auth:\n  - login-flow\ncheckout:\n  - cart-checkout\n  - cart-empty\n",
        encoding="utf-8",
    )
    loaded = _load_validation_map(p)
    assert loaded == {"auth": ["login-flow"], "checkout": ["cart-checkout", "cart-empty"]}


def test_load_validation_map_rejects_non_mapping(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ValueError):
        _load_validation_map(p)


def test_load_validation_map_rejects_non_string_stems(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text("auth:\n  - 123\n", encoding="utf-8")
    with pytest.raises(ValueError):
        _load_validation_map(p)


def test_parse_spec_extensions_normalizes_leading_dot():
    assert _parse_spec_extensions("ts,.js, mjs") == (".ts", ".js", ".mjs")


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
