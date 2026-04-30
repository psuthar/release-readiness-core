"""Risk floor (port of internal/prrisk/floors.go).

When trust-critical factors are present (CI workflows, deploy, migrations,
go.mod/sum, very-large diff, large diff, many-files), the final score
cannot drop into the low band. This is what stops a few well-placed
reducers from masking high-blast-radius signals.
"""

from __future__ import annotations

from typing import Iterable, List, Tuple

from release_readiness_core.pr_risk._internal import (
    clamp_100,
    factor_ids,
    max_float,
    ok_bool,
)
from release_readiness_core.pr_risk.types import RiskFactor


# Bands: low < 20, medium 20-44.9, ... — so 20 prevents "low" for trust-critical signals.
FLOOR_MIN_NOT_LOW_BAND = 20.0


def compute_floor_threshold(
    factors: Iterable[RiskFactor],
) -> Tuple[float, List[str]]:
    """Return (min_score, reasons) when any trust floor factor is present."""
    has = factor_ids(factors)
    floor_min = 0.0
    reasons: List[str] = []

    if ok_bool(has, "ci_workflows"):
        floor_min = max_float(floor_min, FLOOR_MIN_NOT_LOW_BAND)
        reasons.append("CI workflow changes cannot score in the low band (floor applies)")
    if ok_bool(has, "deploy_config"):
        floor_min = max_float(floor_min, FLOOR_MIN_NOT_LOW_BAND)
        reasons.append("Deploy/hosting config changes cannot score in the low band (floor applies)")
    if ok_bool(has, "go_mod_deps"):
        floor_min = max_float(floor_min, FLOOR_MIN_NOT_LOW_BAND)
        reasons.append(
            "Go module/dependency lockfile changes cannot score in the low band (floor applies)"
        )
    if ok_bool(has, "diff_very_large"):
        floor_min = max_float(floor_min, FLOOR_MIN_NOT_LOW_BAND)
        reasons.append("Very large diff cannot score in the low band (floor applies)")
    if ok_bool(has, "diff_large"):
        floor_min = max_float(floor_min, FLOOR_MIN_NOT_LOW_BAND)
        reasons.append("Large diff cannot score in the low band (floor applies)")
    if ok_bool(has, "many_files"):
        floor_min = max_float(floor_min, FLOOR_MIN_NOT_LOW_BAND)
        reasons.append("Many files touched cannot score in the low band (floor applies)")

    return floor_min, reasons


def apply_risk_floor(
    net_before_floor: float, factors: Iterable[RiskFactor]
) -> Tuple[float, bool, float, List[str]]:
    """Raise net_before_floor to the floor threshold when applicable.

    Returns (final, applied, floor_min, reasons). Mirrors Go applyRiskFloor.
    """
    floor_min, reasons = compute_floor_threshold(factors)
    if floor_min <= 0:
        return clamp_100(net_before_floor), False, 0.0, []
    if net_before_floor < floor_min:
        return clamp_100(floor_min), True, floor_min, reasons
    return clamp_100(net_before_floor), False, floor_min, reasons
