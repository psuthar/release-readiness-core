"""Synthetic-config tests for the Phase 2 config-driven classifier (SCRUM-240).

These tests prove the classifier wiring works by loading a hand-rolled config
that has nothing in common with the bundled default. If the runtime threads
the config through correctly, paths classify per the synthetic config — not
per the bundled default.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from release_readiness_core.pr_risk._runtime import PRRiskRuntime
from release_readiness_core.pr_risk.classify import (
    classify_area,
    classify_domain,
    touches_sensitive_code_without_tests,
)
from release_readiness_core.pr_risk.types import FileChange, Signals


CUSTOM_CONFIG = dedent("""
    version: 1
    domains:
      - id: payments
        label: payments
        patterns:
          - { prefix: "billing/" }
          - { contains: "/stripe/" }
          - and:
              - { contains: "checkout" }
              - { any_contains: ["api/v1/", "api/v2/"] }
      - id: ml
        label: ml
        patterns:
          - { prefix: "ml/" }
          - { exact: "model.bin" }
      - id: docs
        label: docs
        patterns:
          - { endswith: ".md" }
          - { prefix: "docs/" }
    sensitive_domains:
      - payments
      - ml
""").lstrip()


@pytest.fixture
def runtime(tmp_path: Path) -> PRRiskRuntime:
    p = tmp_path / "pr-risk-config.yaml"
    p.write_text(CUSTOM_CONFIG, encoding="utf-8")
    return PRRiskRuntime.from_config(p)


@pytest.mark.parametrize(
    "path,expected_domain",
    [
        # Payments — three pattern variants.
        ("billing/invoices.py", "payments"),
        ("services/stripe/webhook.py", "payments"),
        ("api/v1/checkout/session.py", "payments"),
        ("api/v2/checkout/refund.py", "payments"),
        # ML — prefix and exact.
        ("ml/training/run.py", "ml"),
        ("model.bin", "ml"),
        # Docs — endswith and prefix.
        ("README.md", "docs"),
        ("docs/architecture/overview.md", "docs"),
        ("docs/architecture/diagram.png", "docs"),
        # No matching domain — falls back to "other".
        ("scripts/build.sh", "other"),
        ("services/foo/bar.py", "other"),
        ("", "other"),
    ],
)
def test_classify_area_with_custom_config(
    runtime: PRRiskRuntime, path: str, expected_domain: str
) -> None:
    assert classify_area(path, runtime=runtime) == expected_domain
    # And via the runtime accessor directly.
    assert runtime.classify_area(path) == expected_domain


def test_classify_domain_test_path_short_circuits(runtime: PRRiskRuntime) -> None:
    """Test paths return DOMAIN_TESTS regardless of config — language heuristic."""
    assert classify_domain("billing/invoices_test.go", runtime=runtime) == "tests"
    assert classify_domain("ml/training_test.go", runtime=runtime) == "tests"
    # Non-test path uses the config.
    assert classify_domain("billing/invoices.go", runtime=runtime) == "payments"


def test_first_matching_domain_in_declared_order_wins() -> None:
    """When two domains both match a path, declared order wins."""
    config = dedent("""
        version: 1
        domains:
          - id: first
            label: first
            patterns: [{ prefix: "src/" }]
          - id: second
            label: second
            patterns: [{ prefix: "src/" }]
    """).lstrip()
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "cfg.yaml"
        p.write_text(config, encoding="utf-8")
        runtime = PRRiskRuntime.from_config(p)
        assert runtime.classify_area("src/foo.py") == "first"


def test_touches_sensitive_code_without_tests_uses_config(runtime: PRRiskRuntime) -> None:
    """sensitive_domains is config-driven — payments / ml are sensitive in the
    custom config; the bundled-default 'auth' is not."""
    # Payments is sensitive in the custom config.
    s = Signals(files=[FileChange(path="billing/foo.py")])
    assert touches_sensitive_code_without_tests(s, runtime=runtime) is True

    # 'auth' (bundled-default sensitive) is NOT sensitive under the custom
    # config — touches_sensitive_code_without_tests returns False because
    # internal/auth/ classifies to "other" here.
    s = Signals(files=[FileChange(path="internal/auth/session.go")])
    assert touches_sensitive_code_without_tests(s, runtime=runtime) is False

    # If a test file is in the diff, the rule short-circuits regardless.
    s = Signals(test_files=1, files=[FileChange(path="billing/foo.py")])
    assert touches_sensitive_code_without_tests(s, runtime=runtime) is False


def test_default_runtime_classifies_everything_as_other():
    """Phase 5 (SCRUM-243) stripped the bundled default of project-specific
    domain mappings: with no adopter-authored pr-risk-config.yaml, every
    non-test path classifies to ``"other"``. Test paths still classify to
    ``"tests"`` because that's a language heuristic, not project policy."""
    assert classify_area("internal/auth/session.go") == "other"
    assert classify_area("web/src/App.tsx") == "other"
    assert classify_area("README.md") == "other"
    assert classify_domain("internal/auth/session_test.go") == "tests"
    assert classify_domain("README.md") == "other"
