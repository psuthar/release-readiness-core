"""Loader tests for the pr-risk config (SCRUM-239)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from release_readiness_core.pr_risk._config import (
    PRRiskConfig,
    PRRiskConfigError,
    config_to_dict,
    load_pr_risk_config,
    parse_pr_risk_config,
)


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "pr-risk-config.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_minimal_config_loads(tmp_path: Path):
    p = _write(tmp_path, "version: 1\n")
    cfg = load_pr_risk_config(p)
    assert isinstance(cfg, PRRiskConfig)
    assert cfg.version == 1
    assert cfg.domains == []
    assert cfg.sensitive_domains == []
    assert cfg.gates == []


def test_missing_version_rejected(tmp_path: Path):
    p = _write(tmp_path, "domains: []\n")
    with pytest.raises(PRRiskConfigError, match="missing required top-level key"):
        load_pr_risk_config(p)


def test_unsupported_version_rejected(tmp_path: Path):
    p = _write(tmp_path, "version: 2\n")
    with pytest.raises(PRRiskConfigError, match="unsupported version"):
        load_pr_risk_config(p)


def test_unknown_top_level_key_rejected(tmp_path: Path):
    p = _write(tmp_path, "version: 1\nbogus: 42\n")
    with pytest.raises(PRRiskConfigError, match="Unknown top-level key"):
        load_pr_risk_config(p)


def test_unknown_top_level_key_with_typo_suggestion(tmp_path: Path):
    p = _write(tmp_path, "version: 1\ndomian: []\n")
    with pytest.raises(PRRiskConfigError) as exc:
        load_pr_risk_config(p)
    msg = str(exc.value)
    assert "domian" in msg
    assert "did you mean" in msg
    assert "domains" in msg


def test_duplicate_gate_id_rejected(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        gates:
          - id: g1
            title: T1
            priority: high
            fix_type: test
          - id: g1
            title: T1-dup
            priority: medium
            fix_type: test
    """))
    with pytest.raises(PRRiskConfigError, match="duplicate gate id"):
        load_pr_risk_config(p)


def test_unknown_evidence_template_rejected(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        gates:
          - id: g1
            title: T1
            priority: high
            fix_type: test
            evidence:
              template: not_a_real_template
    """))
    with pytest.raises(PRRiskConfigError, match="must be one of"):
        load_pr_risk_config(p)


def test_malformed_path_pattern_zero_keys(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        domains:
          - id: d1
            patterns:
              - {}
    """))
    with pytest.raises(PRRiskConfigError, match="pattern is empty"):
        load_pr_risk_config(p)


def test_malformed_path_pattern_two_primary_keys(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        domains:
          - id: d1
            patterns:
              - { prefix: "a/", contains: "b" }
    """))
    with pytest.raises(PRRiskConfigError, match="must contain exactly one"):
        load_pr_risk_config(p)


def test_malformed_path_pattern_unknown_key(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        domains:
          - id: d1
            patterns:
              - { regex: "^a/$" }
    """))
    with pytest.raises(PRRiskConfigError, match="must contain exactly one"):
        load_pr_risk_config(p)


def test_path_pattern_and_requires_two_subpatterns(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        domains:
          - id: d1
            patterns:
              - and:
                  - { prefix: "a/" }
    """))
    with pytest.raises(PRRiskConfigError, match="at least two"):
        load_pr_risk_config(p)


def test_malformed_gate_predicate_zero_keys(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        gates:
          - id: g1
            title: T1
            priority: high
            fix_type: test
            applies_when:
              - {}
    """))
    with pytest.raises(PRRiskConfigError, match="predicate is empty"):
        load_pr_risk_config(p)


def test_malformed_gate_predicate_unknown_primary_key(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        gates:
          - id: g1
            title: T1
            priority: high
            fix_type: test
            applies_when:
              - { foo: bar }
    """))
    with pytest.raises(PRRiskConfigError, match="must contain exactly one"):
        load_pr_risk_config(p)


def test_invalid_priority_rejected(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        gates:
          - id: g1
            title: T1
            priority: urgent
            fix_type: test
    """))
    with pytest.raises(PRRiskConfigError, match="priority"):
        load_pr_risk_config(p)


def test_invalid_fix_type_rejected(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        gates:
          - id: g1
            title: T1
            priority: high
            fix_type: science
    """))
    with pytest.raises(PRRiskConfigError, match="fix_type"):
        load_pr_risk_config(p)


def test_invalid_risk_band_value_rejected(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        gates:
          - id: g1
            title: T1
            priority: high
            fix_type: test
            applies_when:
              - { risk_band: [maximal] }
    """))
    with pytest.raises(PRRiskConfigError, match="must be one of"):
        load_pr_risk_config(p)


def test_factor_id_accepts_string(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        gates:
          - id: g1
            title: T1
            priority: high
            fix_type: test
            applies_when:
              - { factor_id: my_factor }
    """))
    cfg = load_pr_risk_config(p)
    assert cfg.gates[0].applies_when == [{"factor_id": "my_factor"}]


def test_factor_id_accepts_list(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        gates:
          - id: g1
            title: T1
            priority: high
            fix_type: test
            applies_when:
              - factor_id: [a, b, c]
    """))
    cfg = load_pr_risk_config(p)
    assert cfg.gates[0].applies_when == [{"factor_id": ["a", "b", "c"]}]


def test_factor_id_empty_list_rejected(tmp_path: Path):
    p = _write(tmp_path, dedent("""
        version: 1
        gates:
          - id: g1
            title: T1
            priority: high
            fix_type: test
            applies_when:
              - factor_id: []
    """))
    with pytest.raises(PRRiskConfigError, match="at least one"):
        load_pr_risk_config(p)


def test_round_trip_yaml_to_dataclass_to_dict(tmp_path: Path):
    """A hand-authored YAML round-trips through PRRiskConfig back to a deeply-equal dict."""
    yaml = pytest.importorskip("yaml")
    blob = dedent("""
        version: 1
        domains:
          - id: backend
            label: backend
            patterns:
              - { prefix: "src/" }
              - { contains: "/handlers/" }
              - and:
                  - { contains: "src/" }
                  - { any_contains: ["foo", "bar"] }
        sensitive_domains:
          - backend
        gates:
          - id: example_gate
            title: "Example gate"
            priority: medium
            fix_type: test
            applies_when:
              - { factor_id: domain_backend }
              - { risk_band: [high, critical] }
            applies_when_extra: "backend changed"
            validation_line: "test: backend smoke"
            checklist:
              - "Run backend smoke before merge."
              - text: "Confirm coverage."
                by_evidence_level:
                  none: "Add backend tests first."
                  unit: "Run unit tests."
                by_validation_note: "Validation note found; double-check checklist."
            evidence:
              template: test_domain
              args:
                domain: backend
            variants:
              - when: { risk_band: [critical] }
                title: "Critical: example gate"
                checklist:
                  - "Critical override checklist line."
    """).lstrip()
    raw = yaml.safe_load(blob)
    cfg = parse_pr_risk_config(raw, source="<inline>")
    rebuilt = config_to_dict(cfg)
    assert rebuilt == raw


def test_round_trip_via_yaml_dump(tmp_path: Path):
    """parse → config_to_dict → yaml.safe_dump → yaml.safe_load → parse round-trips."""
    yaml = pytest.importorskip("yaml")
    p = _write(tmp_path, dedent("""
        version: 1
        domains:
          - id: d1
            label: d1
            patterns:
              - { prefix: "a/" }
        sensitive_domains: [d1]
        gates:
          - id: g1
            title: G1
            priority: high
            fix_type: test
            applies_when:
              - { factor_id: f1 }
            checklist: ["one", "two"]
            evidence:
              template: signal_check
              args: { signal_field: git_error }
    """).lstrip())
    cfg1 = load_pr_risk_config(p)
    dumped = yaml.safe_dump(config_to_dict(cfg1), sort_keys=False)
    cfg2 = parse_pr_risk_config(yaml.safe_load(dumped), source="<reload>")
    assert cfg1 == cfg2
