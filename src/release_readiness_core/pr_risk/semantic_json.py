"""Semantic pr-risk.json writer (port of semantic_json.go)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from release_readiness_core.pr_risk._round import round_half_away
from release_readiness_core.pr_risk.types import (
    CATEGORY_TEST_CONFIDENCE,
    Result,
    RiskFactor,
)


_SEMANTIC_TOP_FACTORS = 5


@dataclass
class SemanticPRRiskFile:
    report_version: str = ""
    score: float = 0.0
    band: str = ""
    merge_recommendation: str = ""  # PASS | WARN | BLOCK
    required_validations: List[str] = field(default_factory=list)
    top_risk_factors: List[str] = field(default_factory=list)
    test_confidence: Optional[int] = None


def top_factor_labels(factors: List[RiskFactor], n: int) -> List[str]:
    if not factors or n <= 0:
        return []
    cp = sorted(factors, key=lambda f: (-f.points, f.id))
    if len(cp) > n:
        cp = cp[:n]
    out: List[str] = []
    for f in cp:
        label = f.label.strip()
        if label == "":
            label = f.id
        out.append(label)
    return out


def _semantic_payload(r: Result) -> dict:
    enf = r.enforcement
    rec = (enf.merge_recommendation or "").strip().upper() or "UNKNOWN"
    top = top_factor_labels(r.factors, _SEMANTIC_TOP_FACTORS)
    test_conf: Optional[int] = None
    for c in r.categories:
        if c.key == CATEGORY_TEST_CONFIDENCE:
            test_conf = int(round_half_away(c.confidence))
            break

    payload = {
        "report_version": r.report_version,
        "score": r.risk_score,
        "band": r.risk_band,
        "merge_recommendation": rec,
        "required_validations": list(enf.required_validations),
    }
    # Match Go's omitempty behavior for top_risk_factors and test_confidence.
    if top:
        payload["top_risk_factors"] = top
    if test_conf is not None:
        payload["test_confidence"] = test_conf
    return payload


def write_semantic_pr_risk_json(path: str, r: Result) -> None:
    """Write the semantic pr-risk.json file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = _semantic_payload(r)
    with open(path, "w") as fh:
        # Go's json.MarshalIndent uses 2-space indent; match that.
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def semantic_payload_for_test(r: Result) -> dict:
    """Public form of _semantic_payload for parity tests."""
    return _semantic_payload(r)
