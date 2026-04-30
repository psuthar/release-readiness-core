"""Shared test fixtures for tests/pr_risk/.

Phase 5 stripped the bundled-default ``PRRiskConfig`` of project-specific
domain mappings and gate definitions. Tests that exercise those project
specifics now load the parity-fixture corpus YAML explicitly via this fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest


CORPUS_CONFIG_PATH = Path(__file__).parent / "fixtures" / "pr-risk-corpus-config.yaml"


@pytest.fixture(scope="session")
def corpus_runtime():
    """``PRRiskRuntime`` loaded from the parity-fixture corpus YAML.

    Use this in tests that need the project-specific domains and gate
    definitions that the bundled default no longer ships."""
    from release_readiness_core.pr_risk._runtime import PRRiskRuntime

    return PRRiskRuntime.from_config(CORPUS_CONFIG_PATH)
