"""Phase 5: the bundled-default config is language-agnostic.

Asserts the bundled default emits no project-specific gates and no
project-specific domain hits when running without an adopter-authored
``pr-risk-config.yaml``. Also asserts the proof-of-decoupling guard:
``grep -rn "internal/auth\\|internal/rag\\|...\\|web/src/modes/creatormode" src/``
returns nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from release_readiness_core.pr_risk._default_config import default_pr_risk_config
from release_readiness_core.pr_risk._runtime import PRRiskRuntime
from release_readiness_core.pr_risk.classify import classify_area
from release_readiness_core.pr_risk.score import score
from release_readiness_core.pr_risk.types import (
    FileChange,
    Signals,
    default_weights,
)


SRC_DIR = Path(__file__).resolve().parents[2] / "src"


def test_bundled_default_has_no_domains():
    cfg = default_pr_risk_config()
    assert cfg.domains == []


def test_bundled_default_has_no_sensitive_domains():
    cfg = default_pr_risk_config()
    assert cfg.sensitive_domains == []


def test_bundled_default_has_only_generic_gates():
    cfg = default_pr_risk_config()
    assert {g.id for g in cfg.gates} == {
        "ci_fetch_depth_zero",
        "pr_review_summary",
        "workflow_config_validation",
        "add_tests_or_evidence",
        "context_align_pr_description",
        "context_scattered_review_plan",
        "context_improve_test_proximity",
        "context_hotspot_regression_focus",
    }


def test_classify_area_returns_other_for_every_path():
    """Without an adopter-authored config, every path classifies to ``other``."""
    paths = [
        "internal/auth/session.go",
        "internal/rag/qa.go",
        "internal/processing/whisper.go",
        "internal/orchestration/evaluator.go",
        "web/src/App.tsx",
        "web/src/modes/CreatorMode.jsx",
        "src/myproject/api/views.py",
        "alembic/versions/0001_x.py",
        "README.md",
    ]
    for p in paths:
        assert classify_area(p) == "other", p


def test_score_emits_no_project_specific_gates_with_default_runtime():
    """A diff that classifies to ``other`` produces no domain factors and no
    project-specific gates. Generic gates (pr_review_summary, etc.) may still
    fire based on diff size / context insights."""
    s = Signals(
        file_count=1,
        total_added=10,
        total_loc=10,
        files=[FileChange(path="internal/auth/session.go", added=10)],
        # No domain_hits — bundled default doesn't classify auth as a domain.
    )
    r = score(s, default_weights())
    factor_ids = {f.id for f in r.factors}
    assert "domain_auth" not in factor_ids
    assert "domain_rag" not in factor_ids
    assert "domain_migrations" not in factor_ids

    action_ids = {a.id for a in r.required_actions}
    assert "auth_e2e_gate" not in action_ids
    assert "rag_qna_citations_gate" not in action_ids
    assert "migrations_validation_gate" not in action_ids
    assert "materials_processing_gate" not in action_ids
    assert "orchestration_creator_gate" not in action_ids


def test_score_with_default_runtime_emits_only_generic_gates():
    """When generic factors fire (e.g. diff_large), only generic gates emit."""
    s = Signals(
        file_count=50,
        total_added=2000,
        total_loc=2000,
        files=[FileChange(path=f"src/file_{i}.py", added=40) for i in range(50)],
    )
    r = score(s, default_weights())
    action_ids = {a.id for a in r.required_actions}
    # Generic gates can fire (diff size is large).
    project_specific = {
        "auth_e2e_gate", "rag_qna_citations_gate", "migrations_validation_gate",
        "materials_processing_gate", "orchestration_creator_gate",
    }
    assert action_ids.isdisjoint(project_specific)


def test_runtime_from_default_smoke_sanity():
    runtime = PRRiskRuntime.from_default()
    assert runtime.config.domains == []
    assert runtime.config.sensitive_domains == []
    assert runtime.classify("internal/auth/foo.go") == "other"


def test_no_project_specific_path_strings_in_src():
    """Phase 5 acceptance criterion (the literal grep guard from the ticket):
    project-specific path patterns must not appear in any file under src/.

    The corpus parity-fixture YAML lives under tests/, so it's not in scope.
    """
    # Patterns from the ticket. \b prevents matching `auth_e2e_gate`'s "auth".
    forbidden = [
        re.compile(r"internal/auth"),
        re.compile(r"internal/rag"),
        re.compile(r"internal/processing"),
        re.compile(r"internal/orchestration"),
        re.compile(r"web/src/modes/creatormode"),
    ]
    matches: list[tuple[str, str]] = []
    for path in SRC_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pat in forbidden:
            if pat.search(text):
                matches.append((str(path.relative_to(SRC_DIR)), pat.pattern))
    assert not matches, (
        f"Project-specific path patterns leaked into src/:\n  "
        + "\n  ".join(f"{p} :: {q}" for p, q in matches)
    )
