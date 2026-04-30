"""Plain-English interpretation of a Result (port of internal/prrisk/interpret.go).

Output strings match Go fmt.Sprintf("%.0f", ...) formatting exactly.
"""

from __future__ import annotations

from release_readiness_core.pr_risk._round import round_half_away
from release_readiness_core.pr_risk.types import Result


def _fmt0(x: float) -> str:
    """Format like Go's '%.0f': zero-decimal, half-away-from-zero rounding."""
    return str(int(round_half_away(x)))


def build_interpretation(r: Result) -> str:
    """Return a plain-English summary of the risk result."""
    floor_note = ""
    if r.score_math.floor_applied:
        floor_note = (
            f" A risk floor raised the score from {_fmt0(r.score_math.net_before_floor)} "
            f"to {_fmt0(r.score_math.final_score)} so trust-critical signals are not "
            f"masked by reducers."
        )
    band = r.risk_band
    if band == "low":
        return (
            "Low risk. The diff is small and does not touch sensitive areas. "
            "Standard review is sufficient."
        )
    if band == "medium":
        return (
            f"Medium risk (score {_fmt0(r.risk_score)}). Some risk factors are "
            f"present but are manageable. Review the factors below before merging.{floor_note}"
        )
    if band == "high":
        return (
            f"High risk (score {_fmt0(r.risk_score)}). Significant risk factors detected. "
            f"Complete all required actions before merging.{floor_note}"
        )
    if band == "critical":
        return (
            f"Critical risk (score {_fmt0(r.risk_score)}). Multiple high-impact areas "
            f"changed. All required actions are mandatory before merge.{floor_note}"
        )
    return ""
