"""Reducers (port of internal/prrisk/reducers.go).

Detects deterministic risk-lowering signals (validation notes, test evidence,
style-only commits, test-only / test-heavy diffs). Reducers are only emitted
when their corresponding risky factors are present.
"""

from __future__ import annotations

from typing import Iterable, List

from release_readiness_core.pr_risk._internal import factor_ids, ok_bool
from release_readiness_core.pr_risk._round import round_half_away
from release_readiness_core.pr_risk.types import (
    CATEGORY_CODE,
    CATEGORY_TEST_CONFIDENCE,
    CATEGORY_WORKFLOW,
    DOMAIN_API,
    DOMAIN_AUTH,
    DOMAIN_DATABASE,
    DOMAIN_MIGRATIONS,
    DOMAIN_ORCHESTRATION,
    DOMAIN_PROCESSING,
    DOMAIN_RAG,
    RiskFactor,
    RiskReducer,
    ScoreWeights,
    Signals,
)


def reducer_ids(reducers: Iterable[RiskReducer]) -> set:
    return {r.id for r in reducers}


def validation_note_strength(snippet: str) -> str:
    """Classify validation note strength: strong / moderate / basic."""
    lower = snippet.lower()
    if (
        "e2e" in lower
        or "smoke" in lower
        or "playwright" in lower
        or "end-to-end" in lower
    ):
        return "strong"
    if (
        "staging" in lower
        or "dispatch" in lower
        or "deploy" in lower
        or " ci " in lower
        or "pipeline" in lower
    ):
        return "moderate"
    return "basic"


def short_snippet(s: str) -> str:
    s = s.strip()
    if s == "":
        return ""
    if len(s) <= 80:
        return s
    return s[:77] + "..."


_DOMAIN_SPECS = (
    ("domain_auth", DOMAIN_AUTH),
    ("domain_rag", DOMAIN_RAG),
    ("domain_processing", DOMAIN_PROCESSING),
    ("domain_orchestration", DOMAIN_ORCHESTRATION),
    ("domain_migrations", DOMAIN_MIGRATIONS),
)


def detect_reducers(
    s: Signals, factors: Iterable[RiskFactor], w: ScoreWeights
) -> List[RiskReducer]:
    factors_list = list(factors)
    has = factor_ids(factors_list)
    reducers: List[RiskReducer] = []

    # Validation note reducer — tiered by evidence quality.
    if s.validation_note_found:
        if (
            ok_bool(has, "ci_workflows")
            or ok_bool(has, "deploy_config")
            or ok_bool(has, "go_mod_deps")
        ):
            strength = validation_note_strength(s.validation_note_snippet)
            if strength == "strong":
                rid, label = "validation_note_strong", "Strong validation note (E2E/smoke evidence)"
                pts = w.validation_note_reducer_points
            elif strength == "moderate":
                rid, label = (
                    "validation_note_moderate",
                    "Moderate validation note (staging/CI evidence)",
                )
                pts = w.workflow_partial_reducer_points
            else:
                rid, label = "validation_note_basic", "Basic validation note"
                pts = w.workflow_partial_reducer_points / 2
            reducers.append(
                RiskReducer(
                    id=rid,
                    label=label,
                    points=pts,
                    evidence=short_snippet(s.validation_note_snippet),
                    category_key=CATEGORY_WORKFLOW,
                )
            )

    # Domain-specific test evidence reducers.
    for factor_id, domain in _DOMAIN_SPECS:
        if not ok_bool(has, factor_id):
            continue
        if s.test_e2e_domain_hits.get(domain, 0) > 0:
            reducers.append(
                RiskReducer(
                    id=factor_id + "_e2e_evidence",
                    label="E2E test evidence present",
                    points=w.e2e_test_evidence_reducer_points,
                    evidence="Found E2E tests targeting the domain in the diff",
                    category_key=CATEGORY_TEST_CONFIDENCE,
                )
            )
            continue
        if s.test_unit_domain_hits.get(domain, 0) > 0:
            reducers.append(
                RiskReducer(
                    id=factor_id + "_unit_evidence",
                    label="Unit test evidence present",
                    points=w.unit_test_evidence_reducer_points,
                    evidence="Found unit tests targeting the domain in the diff",
                    category_key=CATEGORY_TEST_CONFIDENCE,
                )
            )

    # Style-only frontend change.
    if s.style_only_note_found and w.style_only_reducer_points > 0:
        backend_hit = (
            s.domain_hits.get(DOMAIN_AUTH, 0) > 0
            or s.domain_hits.get(DOMAIN_API, 0) > 0
            or s.domain_hits.get(DOMAIN_DATABASE, 0) > 0
            or s.domain_hits.get(DOMAIN_RAG, 0) > 0
            or s.domain_hits.get(DOMAIN_PROCESSING, 0) > 0
            or s.domain_hits.get(DOMAIN_MIGRATIONS, 0) > 0
        )
        if not backend_hit:
            reducers.append(
                RiskReducer(
                    id="style_only_note",
                    label="Style-only frontend change (commit note)",
                    points=w.style_only_reducer_points,
                    evidence=short_snippet(s.style_only_note_snippet),
                    category_key=CATEGORY_TEST_CONFIDENCE,
                )
            )

    # Test-only diff.
    sensitive_in_diff = (
        s.domain_hits.get(DOMAIN_AUTH, 0) > 0
        or s.domain_hits.get(DOMAIN_RAG, 0) > 0
        or s.domain_hits.get(DOMAIN_PROCESSING, 0) > 0
        or s.domain_hits.get(DOMAIN_ORCHESTRATION, 0) > 0
        or s.domain_hits.get(DOMAIN_MIGRATIONS, 0) > 0
    )
    if (
        not sensitive_in_diff
        and s.test_files > 0
        and s.file_count > 0
        and s.test_files == s.file_count
    ):
        reducers.append(
            RiskReducer(
                id="test_only_diff",
                label="Test-only diff",
                points=w.test_only_diff_reducer_points,
                evidence="All changed files are classified as tests",
                category_key=CATEGORY_CODE,
            )
        )

    # Test-heavy diff.
    if (
        w.test_heavy_loc_ratio_threshold > 0
        and s.test_loc_ratio >= w.test_heavy_loc_ratio_threshold
        and s.file_count > 0
        and s.test_files < s.file_count
    ):
        reducers.append(
            RiskReducer(
                id="test_heavy_diff",
                label="Test-heavy diff",
                points=w.test_heavy_reducer_points,
                evidence=f"{int(round_half_away(s.test_loc_ratio * 100))}% of LOC churn is in test files",
                category_key=CATEGORY_TEST_CONFIDENCE,
            )
        )

    return reducers
