"""Top-level context analyzer (port of internal/prrisk/context/analyze.go)."""

from __future__ import annotations

from typing import List, Tuple

from release_readiness_core.pr_risk.context.concentration import analyze_concentration
from release_readiness_core.pr_risk.context.hotspots import analyze_hotspots
from release_readiness_core.pr_risk.context.input import Input
from release_readiness_core.pr_risk.context.intent import analyze_intent
from release_readiness_core.pr_risk.context.proximity import analyze_proximity
from release_readiness_core.pr_risk.context.types import (
    ContextInsights,
    FactorContribution,
    ProximityInsight,
    Weights,
)


def default_weights() -> Weights:
    """Built-in v2.4 contextual weights (mirrors Go DefaultWeights())."""
    return Weights(
        proximity_low_points=5,
        scattered_points=5,
        hotspot_points=4,
        intent_mismatch_points=6,
    )


def has_sensitive_domain(h: dict) -> bool:
    if h is None:
        return False
    return any(h.get(k, 0) > 0 for k in ("auth", "rag", "processing", "migrations", "api", "database"))


def should_flag_proximity(in_: Input, prox: ProximityInsight) -> bool:
    if prox.mode != "distant" or prox.non_test_files < 2:
        return False
    if not has_sensitive_domain(in_.domain_hits):
        return False
    return True


def analyze(in_: Input, w: Weights) -> Tuple[ContextInsights, List[FactorContribution]]:
    """Run all contextual analyzers; return insights + optional score factors."""
    prox = analyze_proximity(in_)
    conc = analyze_concentration(in_)
    hotspots, hotspots_skip = analyze_hotspots(in_)
    intent = analyze_intent(in_)

    insights = ContextInsights(
        proximity=prox,
        concentration=conc,
        hotspots=hotspots,
        hotspots_skip_reason=hotspots_skip,
        intent=intent,
    )

    factors: List[FactorContribution] = []

    if should_flag_proximity(in_, prox) and w.proximity_low_points > 0:
        factors.append(
            FactorContribution(
                id="context_test_proximity_distant",
                label="Tests not co-located with changed code in this diff",
                points=w.proximity_low_points,
                detail=prox.detail,
            )
        )

    if conc.mode == "scattered" and len(in_.files) >= 10 and w.scattered_points > 0:
        factors.append(
            FactorContribution(
                id="context_change_scattered",
                label="Change concentration is scattered across many areas",
                points=w.scattered_points,
                detail=conc.detail,
            )
        )

    if len(hotspots) > 0 and w.hotspot_points > 0:
        factors.append(
            FactorContribution(
                id="context_hotspot_overlap",
                label="Diff overlaps a path prefix touched in multiple recent commits",
                points=w.hotspot_points,
                detail=hotspots[0].detail,
            )
        )

    if intent.mismatch and len(intent.domains_expected) > 0 and w.intent_mismatch_points > 0:
        factors.append(
            FactorContribution(
                id="context_intent_mismatch",
                label="PR title/body keywords do not align with paths in the diff",
                points=w.intent_mismatch_points,
                detail=intent.detail,
            )
        )

    return insights, factors
