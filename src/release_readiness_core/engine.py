"""Deterministic release-readiness evaluation primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Sequence


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


@dataclass(frozen=True)
class ValidationMergeConfig:
    """Config-driven key handling for merging evidence into validation booleans."""

    evidence_boolean_keys: Sequence[str] = field(default_factory=tuple)
    risk_category_to_required_validation: Mapping[str, str] = field(default_factory=dict)


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


def merge_validations(
    evidence: Mapping[str, object],
    risk_categories: Sequence[str],
    config: ValidationMergeConfig,
) -> Dict[str, bool]:
    """Merge explicit validations + configured evidence keys into a bool map."""
    merged: Dict[str, bool] = {}

    explicit = evidence.get("validations")
    if isinstance(explicit, dict):
        for key, value in explicit.items():
            if isinstance(value, bool):
                merged[key] = value

    for key in config.evidence_boolean_keys:
        if evidence.get(key) is True:
            merged[key] = True

    for risk in risk_categories:
        required_key = config.risk_category_to_required_validation.get(risk, risk)
        merged.setdefault(required_key, False)

    return merged
