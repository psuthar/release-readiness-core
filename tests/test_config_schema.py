"""Tests for SCRUM-209 config schema validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from release_readiness_core.readiness_io import (
    ConfigSchemaError,
    KNOWN_TOP_LEVEL_CONFIG_KEYS,
    load_yaml_config,
)


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_minimal_known_config_loads(tmp_path: Path):
    p = _write(tmp_path, "version: 1\nvalidations: {}\n")
    cfg = load_yaml_config(p)
    assert cfg["version"] == 1


def test_unknown_top_level_key_raises_with_suggestion(tmp_path: Path):
    """Misspelling a known key triggers a 'did you mean' hint."""
    p = _write(
        tmp_path,
        "version: 1\ninfer_validations_when_pas:\n  smoke: []\n  e2e: []\n",
    )
    with pytest.raises(ConfigSchemaError) as exc:
        load_yaml_config(p)
    msg = str(exc.value)
    assert "infer_validations_when_pas" in msg
    assert "infer_validations_when_pass" in msg
    assert "did you mean" in msg


def test_unknown_top_level_key_without_close_match(tmp_path: Path):
    p = _write(tmp_path, "wibble: 42\nversion: 1\n")
    with pytest.raises(ConfigSchemaError) as exc:
        load_yaml_config(p)
    msg = str(exc.value)
    assert "wibble" in msg
    assert "Known keys:" in msg


def test_wrong_type_for_scoring_raises(tmp_path: Path):
    p = _write(tmp_path, "version: 1\nscoring: not-a-dict\n")
    with pytest.raises(ConfigSchemaError) as exc:
        load_yaml_config(p)
    assert "scoring" in str(exc.value)
    assert "expected dict" in str(exc.value)


def test_wrong_type_for_evidence_boolean_keys_raises(tmp_path: Path):
    p = _write(tmp_path, "version: 1\nevidence_boolean_keys: not-a-list\n")
    with pytest.raises(ConfigSchemaError):
        load_yaml_config(p)


def test_all_known_keys_pass(tmp_path: Path):
    """Every documented top-level key together: smoke check that the closed set is consistent."""
    blob = """
version: 1
validations: {}
evidence_boolean_keys: []
infer_validations_when_pass:
  smoke: []
  e2e: []
risk_category_to_required_validation: {}
risk_from_paths: []
risky_config_patterns: []
scoring: {}
remediation: {}
e2e_critical_name_patterns: []
optional_artifacts: []
report_title: anything
pr_risk: {}
"""
    p = _write(tmp_path, blob.lstrip())
    load_yaml_config(p)


def test_known_keys_set_is_documented():
    """If a contributor adds a new top-level key, this test reminds them to update KNOWN_TOP_LEVEL_CONFIG_KEYS."""
    # This test exists as a checkpoint; it's intentionally trivial.
    assert "scoring" in KNOWN_TOP_LEVEL_CONFIG_KEYS
    assert "optional_artifacts" in KNOWN_TOP_LEVEL_CONFIG_KEYS
