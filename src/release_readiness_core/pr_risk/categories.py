"""Category breakdown (port of internal/prrisk/categories.go).

Splits risk factors and reducers into three lanes (code, workflow, test
confidence) and computes a deterministic per-lane risk score. The
test_confidence lane has its own scoring with proximity-driven adjustments.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from release_readiness_core.pr_risk._internal import clamp_100 as _clamp100_internal
from release_readiness_core.pr_risk.context.types import ContextInsights
from release_readiness_core.pr_risk.types import (
    CATEGORY_CODE,
    CATEGORY_TEST_CONFIDENCE,
    CATEGORY_WORKFLOW,
    DOMAIN_AUTH,
    DOMAIN_MIGRATIONS,
    DOMAIN_ORCHESTRATION,
    DOMAIN_PROCESSING,
    DOMAIN_RAG,
    ConfidenceAdjustment,
    ConfidenceBreakdown,
    RiskCategory,
    RiskFactor,
    RiskReducer,
    Signals,
)


def lane_for_factor_id(factor_id: str) -> str:
    """Return the category lane key for a factor ID."""
    if factor_id.startswith("context_"):
        return CATEGORY_CODE
    if factor_id in {
        "git_unavailable",
        "diff_very_large",
        "diff_large",
        "many_files",
        "domain_auth",
        "domain_migrations",
        "domain_rag",
        "domain_processing",
        "domain_orchestration",
        "web_large",
    }:
        return CATEGORY_CODE
    if factor_id in {"ci_workflows", "deploy_config", "go_mod_deps"}:
        return CATEGORY_WORKFLOW
    if factor_id == "tests_missing":
        return CATEGORY_TEST_CONFIDENCE
    return CATEGORY_CODE  # default for any new factor IDs


def _clamp(x: float) -> float:
    """Local clamp matching Go's score.go::clamp100 (with single-decimal rounding)."""
    # Avoid circular import: re-implement here to keep categories.py self-contained.
    from release_readiness_core.pr_risk._round import round_half_away

    if x < 0:
        return 0.0
    if x > 100:
        return 100.0
    return round_half_away(x * 10) / 10


def test_confidence_score(
    s: Signals, ci: Optional[ContextInsights]
) -> Tuple[float, ConfidenceBreakdown]:
    """Compute test-confidence sub-score and its breakdown."""
    base = 50.0
    bd = ConfidenceBreakdown(base_score=base)
    score = base

    sensitive_changed = (
        s.domain_hits.get(DOMAIN_AUTH, 0) > 0
        or s.domain_hits.get(DOMAIN_RAG, 0) > 0
        or s.domain_hits.get(DOMAIN_PROCESSING, 0) > 0
        or s.domain_hits.get(DOMAIN_ORCHESTRATION, 0) > 0
        or s.domain_hits.get(DOMAIN_MIGRATIONS, 0) > 0
    )

    if not sensitive_changed:
        delta = 35.0
        bd.adjustments.append(ConfidenceAdjustment(reason="No sensitive domains changed", delta=delta))
        score += delta
    else:
        bd.adjustments.append(ConfidenceAdjustment(reason="Sensitive domains changed", delta=-10.0))
        score += -10.0
        if s.e2e_test_files > 0:
            bd.adjustments.append(
                ConfidenceAdjustment(reason="E2E tests present in diff", delta=40.0)
            )
            score += 40.0
        elif s.unit_test_files > 0 or s.test_files > 0:
            bd.adjustments.append(
                ConfidenceAdjustment(reason="Unit tests present in diff", delta=20.0)
            )
            score += 20.0
        else:
            bd.adjustments.append(
                ConfidenceAdjustment(
                    reason="No tests for sensitive domain changes", delta=-15.0
                )
            )
            score += -15.0

    # Proximity-driven confidence adjustments.
    if ci is not None and ci.proximity.mode != "" and ci.proximity.mode != "n_a":
        align = ci.proximity.structural_alignment
        if align == "distant":
            bd.adjustments.append(
                ConfidenceAdjustment(
                    reason="Tests structurally distant from changed code", delta=-15.0
                )
            )
            score += -15.0
        elif align == "partial":
            bd.adjustments.append(
                ConfidenceAdjustment(
                    reason="Tests only partially aligned with changed code", delta=-8.0
                )
            )
            score += -8.0

        if ci.proximity.behavioral_coverage == "shallow":
            bd.adjustments.append(
                ConfidenceAdjustment(
                    reason="Behavioral coverage depth is shallow", delta=-3.0
                )
            )
            score += -3.0

        if ci.proximity.behavioral_coverage == "unknown":
            bd.adjustments.append(
                ConfidenceAdjustment(
                    reason="Behavioral coverage depth unknown", delta=-5.0
                )
            )
            score += -5.0
            if sensitive_changed:
                bd.adjustments.append(
                    ConfidenceAdjustment(
                        reason="Behavioral coverage depth unknown for sensitive domain changes",
                        delta=-5.0,
                    )
                )
                score += -5.0

        # Nearby-test-ratio penalty.
        if ci.proximity.non_test_files > 0:
            ratio = ci.proximity.ratio
            if ratio == 0:
                bd.adjustments.append(
                    ConfidenceAdjustment(
                        reason="No changed files have nearby tests in diff", delta=-10.0
                    )
                )
                score += -10.0
            elif ratio < 0.3:
                bd.adjustments.append(
                    ConfidenceAdjustment(
                        reason="Few changed files have nearby tests in diff", delta=-5.0
                    )
                )
                score += -5.0
            elif ratio < 0.6:
                bd.adjustments.append(
                    ConfidenceAdjustment(
                        reason="Some changed files lack nearby tests", delta=-2.0
                    )
                )
                score += -2.0

    bd.final_score = _clamp(score)
    return _clamp(score), bd


def _unique(seq: List[str]) -> List[str]:
    seen: set = set()
    out: List[str] = []
    for s in seq:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def compute_categories(
    s: Signals,
    factors: List[RiskFactor],
    reducers: List[RiskReducer],
    ci: Optional[ContextInsights],
) -> List[RiskCategory]:
    """Build the decision-grade risk category breakdown."""
    base_by_lane: dict = {}
    factors_by_lane: dict = {}
    for f in factors:
        lane = lane_for_factor_id(f.id)
        base_by_lane[lane] = base_by_lane.get(lane, 0.0) + f.points
        factors_by_lane.setdefault(lane, []).append(f.id)

    reducer_by_lane: dict = {}
    reducers_by_lane: dict = {}
    for r in reducers:
        lane = r.category_key or CATEGORY_CODE
        reducer_by_lane[lane] = reducer_by_lane.get(lane, 0.0) + r.points
        reducers_by_lane.setdefault(lane, []).append(r.id)

    code_risk = _clamp(
        base_by_lane.get(CATEGORY_CODE, 0.0) - reducer_by_lane.get(CATEGORY_CODE, 0.0)
    )
    workflow_risk = _clamp(
        base_by_lane.get(CATEGORY_WORKFLOW, 0.0) - reducer_by_lane.get(CATEGORY_WORKFLOW, 0.0)
    )

    conf, bd = test_confidence_score(s, ci)
    test_confidence_risk = _clamp(100 - conf)
    if s.git_error != "":
        # Git issues reduce confidence regardless of test evidence.
        bd.adjustments.append(
            ConfidenceAdjustment(reason="Git error reduces confidence", delta=-10.0)
        )
        test_confidence_risk = _clamp(test_confidence_risk + 10)
        conf = _clamp(conf - 10.0)
        bd.final_score = conf

    return [
        RiskCategory(
            key=CATEGORY_CODE,
            label="Code changes",
            risk_score=code_risk,
            factors=_unique(factors_by_lane.get(CATEGORY_CODE, [])),
            reducers=_unique(reducers_by_lane.get(CATEGORY_CODE, [])),
        ),
        RiskCategory(
            key=CATEGORY_WORKFLOW,
            label="Workflow / deployment changes",
            risk_score=workflow_risk,
            factors=_unique(factors_by_lane.get(CATEGORY_WORKFLOW, [])),
            reducers=_unique(reducers_by_lane.get(CATEGORY_WORKFLOW, [])),
        ),
        RiskCategory(
            key=CATEGORY_TEST_CONFIDENCE,
            label="Test confidence",
            risk_score=test_confidence_risk,
            confidence=_clamp(conf),
            factors=_unique(factors_by_lane.get(CATEGORY_TEST_CONFIDENCE, [])),
            reducers=_unique(reducers_by_lane.get(CATEGORY_TEST_CONFIDENCE, [])),
            breakdown=bd,
        ),
    ]
