"""Contextual signals (port of internal/prrisk/context/).

Public re-exports keep callers from reaching into the implementation modules.
"""

from release_readiness_core.pr_risk.context.analyze import analyze, default_weights
from release_readiness_core.pr_risk.context.input import FileChange, Input
from release_readiness_core.pr_risk.context.types import (
    ConcentrationInsight,
    ContextInsights,
    FactorContribution,
    HotspotInsight,
    IntentInsight,
    ProximityInsight,
    Weights,
)

__all__ = [
    "ConcentrationInsight",
    "ContextInsights",
    "FactorContribution",
    "FileChange",
    "HotspotInsight",
    "IntentInsight",
    "Input",
    "ProximityInsight",
    "Weights",
    "analyze",
    "default_weights",
]
