"""Phase 5: release-readiness-init writes a starter pr-risk-config.yaml."""

from __future__ import annotations

from pathlib import Path

import pytest

from release_readiness_core.init_scaffold import scaffold
from release_readiness_core.pr_risk._config import (
    PRRiskConfig,
    load_pr_risk_config,
)


def test_scaffold_writes_pr_risk_config(tmp_path: Path):
    results = scaffold(tmp_path, workflow="none")
    rel = "ops/release-readiness/pr-risk-config.yaml"
    assert rel in results, "scaffold must include pr-risk-config.yaml"
    assert results[rel] == "created"
    assert (tmp_path / rel).is_file()


def test_scaffolded_pr_risk_config_loads(tmp_path: Path):
    """The starter pr-risk-config.yaml must be a valid input to
    load_pr_risk_config (parses with no errors, even though all sections
    beyond `version` are commented out)."""
    scaffold(tmp_path, workflow="none")
    cfg = load_pr_risk_config(tmp_path / "ops" / "release-readiness" / "pr-risk-config.yaml")
    assert isinstance(cfg, PRRiskConfig)
    assert cfg.version == 1
    # Starter ships commented-out sections only.
    assert cfg.domains == []
    assert cfg.sensitive_domains == []
    assert cfg.gates == []


def test_scaffolded_pr_risk_config_documents_predicate_vocabulary(tmp_path: Path):
    """The starter file references the closed-set predicate vocabulary so
    adopters know what's available without reading the schema."""
    scaffold(tmp_path, workflow="none")
    text = (tmp_path / "ops" / "release-readiness" / "pr-risk-config.yaml").read_text()
    for predicate in (
        "factor_id",
        "risk_band",
        "intent_mismatch",
        "concentration_mode",
        "hotspots_present",
        "proximity_distant_with_sensitive",
    ):
        assert predicate in text, f"starter must document predicate {predicate!r}"
    # Detector templates documented too.
    for template in ("test_domain", "signal_check", "migrations", "add_tests"):
        assert template in text, f"starter must document template {template!r}"
