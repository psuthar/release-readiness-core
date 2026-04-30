"""Tests for pr_risk.floors (port of Go floors_test.go)."""

from release_readiness_core.pr_risk.floors import (
    FLOOR_MIN_NOT_LOW_BAND,
    apply_risk_floor,
    compute_floor_threshold,
)
from release_readiness_core.pr_risk.types import RiskFactor


def _fac(id_: str, points: float = 12.0) -> RiskFactor:
    return RiskFactor(id=id_, label=id_.replace("_", " "), points=points)


def test_workflow_factor_not_low_band() -> None:
    factors = [_fac("ci_workflows", 12)]
    final, applied, floor_min, _ = apply_risk_floor(6, factors)
    assert floor_min == FLOOR_MIN_NOT_LOW_BAND
    assert applied is True
    assert final == FLOOR_MIN_NOT_LOW_BAND


def test_no_floor_rule() -> None:
    factors = [_fac("domain_auth", 14)]
    final, applied, floor_min, reasons = apply_risk_floor(5, factors)
    assert floor_min == 0
    assert applied is False
    assert reasons == []
    assert final == 5


def test_very_large_diff_floor() -> None:
    factors = [_fac("diff_very_large", 22)]
    final, applied, floor_min, _ = apply_risk_floor(2, factors)
    assert floor_min == FLOOR_MIN_NOT_LOW_BAND
    assert applied is True
    assert final == FLOOR_MIN_NOT_LOW_BAND


def test_large_diff_floor() -> None:
    factors = [_fac("diff_large", 12)]
    final, applied, floor_min, reasons = apply_risk_floor(5, factors)
    assert floor_min == FLOOR_MIN_NOT_LOW_BAND
    assert applied is True
    assert final == FLOOR_MIN_NOT_LOW_BAND
    assert len(reasons) > 0


def test_many_files_floor() -> None:
    factors = [_fac("many_files", 14)]
    final, applied, floor_min, _ = apply_risk_floor(3, factors)
    assert floor_min == FLOOR_MIN_NOT_LOW_BAND
    assert applied is True
    assert final == FLOOR_MIN_NOT_LOW_BAND


def test_deploy_config_floor() -> None:
    factors = [_fac("deploy_config", 12)]
    final, applied, floor_min, _ = apply_risk_floor(8, factors)
    assert floor_min == FLOOR_MIN_NOT_LOW_BAND
    assert applied is True
    assert final == FLOOR_MIN_NOT_LOW_BAND


def test_go_mod_deps_floor() -> None:
    factors = [_fac("go_mod_deps", 8)]
    final, applied, floor_min, _ = apply_risk_floor(4, factors)
    assert floor_min == FLOOR_MIN_NOT_LOW_BAND
    assert applied is True
    assert final == FLOOR_MIN_NOT_LOW_BAND


def test_floor_present_but_not_applied_when_above_floor() -> None:
    """Floor rule fires (ci_workflows) but net is already above the floor.

    floor_min must be set, but applied must be False, and reasons present."""
    factors = [_fac("ci_workflows", 12)]
    net = FLOOR_MIN_NOT_LOW_BAND + 5
    final, applied, floor_min, reasons = apply_risk_floor(net, factors)
    assert floor_min == FLOOR_MIN_NOT_LOW_BAND
    assert applied is False
    assert final == net
    assert len(reasons) > 0


def test_compute_floor_threshold_aggregates_all_reasons() -> None:
    factors = [
        _fac("ci_workflows"),
        _fac("deploy_config"),
        _fac("go_mod_deps"),
        _fac("diff_very_large"),
        _fac("diff_large"),
        _fac("many_files"),
    ]
    floor_min, reasons = compute_floor_threshold(factors)
    assert floor_min == FLOOR_MIN_NOT_LOW_BAND  # max() across all rules is the same
    # All six unique rules each add a reason.
    assert len(reasons) == 6


def test_compute_floor_threshold_no_factors() -> None:
    assert compute_floor_threshold([]) == (0.0, [])


def test_apply_risk_floor_clamps_to_100() -> None:
    factors = [_fac("ci_workflows")]
    final, applied, _, _ = apply_risk_floor(150, factors)
    assert final == 100
    assert applied is False  # 150 was already above floor


def test_apply_risk_floor_no_factors_no_floor() -> None:
    final, applied, floor_min, reasons = apply_risk_floor(50, [])
    assert applied is False
    assert floor_min == 0.0
    assert reasons == []
    assert final == 50
