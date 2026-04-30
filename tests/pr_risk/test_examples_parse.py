"""Phase 5: every YAML under examples/pr-risk/ parses and validates."""

from __future__ import annotations

from pathlib import Path

import pytest

from release_readiness_core.pr_risk._config import (
    PRRiskConfig,
    PRRiskConfigError,
    load_pr_risk_config,
)
from release_readiness_core.pr_risk._runtime import PRRiskRuntime


EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples" / "pr-risk"


def _example_paths() -> list[Path]:
    if not EXAMPLES_DIR.is_dir():
        return []
    return sorted(EXAMPLES_DIR.glob("*.yaml"))


def test_examples_directory_exists():
    assert EXAMPLES_DIR.is_dir(), f"missing {EXAMPLES_DIR}"
    assert _example_paths(), "examples/pr-risk/ has no .yaml files"


@pytest.mark.parametrize("path", _example_paths(), ids=lambda p: p.name)
def test_example_loads(path: Path):
    cfg = load_pr_risk_config(path)
    assert isinstance(cfg, PRRiskConfig)
    assert cfg.version == 1
    # Examples are realistic — non-empty domains and gates.
    assert cfg.domains, f"{path.name}: domains list must not be empty"
    assert cfg.gates, f"{path.name}: gates list must not be empty"


@pytest.mark.parametrize("path", _example_paths(), ids=lambda p: p.name)
def test_example_runtime_classify_smoke(path: Path):
    """The example's domains can drive a classifier without crashing."""
    runtime = PRRiskRuntime.from_config(path)
    runtime.classify("README.md")
    runtime.classify_area("src/main.py")
    runtime.classify_area("")  # empty path → "other"


@pytest.mark.parametrize("path", _example_paths(), ids=lambda p: p.name)
def test_example_detector_for_resolves(path: Path):
    """Every gate's evidence template resolves to a callable."""
    runtime = PRRiskRuntime.from_config(path)
    for gate in runtime.gates:
        if gate.evidence is None:
            continue
        fn = runtime.detector_for(gate.id)
        assert callable(fn), f"{path.name}: detector for {gate.id!r} must be callable"
