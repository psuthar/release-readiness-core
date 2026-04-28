"""Deterministic release-readiness evaluation primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class ValidationResult:
    """Single validation outcome used by the readiness evaluator."""

    key: str
    status: str
    detail: str = ""


@dataclass(frozen=True)
class ReadinessReport:
    """Top-level deterministic readiness output contract."""

    status: str
    passed: int
    warnings: int
    blocked: int
    validations: List[ValidationResult]


def evaluate_release_readiness(results: Iterable[ValidationResult]) -> ReadinessReport:
    """Compute deterministic PASS/WARN/BLOCK summary from validation results."""
    validations = list(results)
    blocked = sum(1 for r in validations if r.status.upper() == "BLOCK")
    warnings = sum(1 for r in validations if r.status.upper() == "WARN")
    passed = sum(1 for r in validations if r.status.upper() == "PASS")

    status = "PASS"
    if blocked > 0:
        status = "BLOCK"
    elif warnings > 0:
        status = "WARN"

    return ReadinessReport(
        status=status,
        passed=passed,
        warnings=warnings,
        blocked=blocked,
        validations=validations,
    )
