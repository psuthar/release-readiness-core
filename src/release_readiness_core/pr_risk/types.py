"""Data types for PR Risk scoring (Python port of internal/prrisk/types.go).

Field names use snake_case. JSON keys preserve the Go camel/snake choices via
``to_dict`` / ``from_dict`` helpers (added in later phases). For Phase 1 the
dataclasses are declarative only; serialization arrives with the report writer
in Phase 4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


# ---------------------------------------------------------------------------
# Domain labels (mirrors Go constants in types.go).
# Centralised here so classify.py can import without circularity.

DOMAIN_AUTH = "auth"
DOMAIN_API = "api"
DOMAIN_DATABASE = "database"
DOMAIN_MIGRATIONS = "migrations"
DOMAIN_RAG = "rag"
DOMAIN_PROCESSING = "processing"
DOMAIN_ORCHESTRATION = "orchestration"
DOMAIN_STORAGE = "storage"
DOMAIN_WEB = "web"
DOMAIN_WORKFLOWS = "workflows"
DOMAIN_DEPLOY = "deploy"
DOMAIN_TESTS = "tests"
DOMAIN_SCRIPTS = "scripts"
DOMAIN_OTHER = "other"


# Category lane keys (mirror Go categories.go).
CATEGORY_CODE = "code"
CATEGORY_WORKFLOW = "workflow"
CATEGORY_TEST_CONFIDENCE = "test_confidence"


# ValidationStatus values (Go: type ValidationStatus = string with named consts).
EVIDENCE_PASS = "pass"
EVIDENCE_MISSING = "missing"
EVIDENCE_UNKNOWN = "unknown"
EVIDENCE_NOT_EVALUATED = "not_evaluated"
EVIDENCE_FAIL = "fail"

ValidationStatus = Literal["pass", "missing", "unknown", "not_evaluated", "fail"]


# ---------------------------------------------------------------------------
# Diff signals.

@dataclass
class FileChange:
    path: str
    added: int = 0
    deleted: int = 0


@dataclass
class Signals:
    base_ref: str = ""
    head_ref: str = ""
    file_count: int = 0
    total_added: int = 0
    total_deleted: int = 0
    total_loc: int = 0
    test_loc_ratio: float = 0.0
    files: List[FileChange] = field(default_factory=list)
    domain_hits: Dict[str, int] = field(default_factory=dict)
    test_domain_hits: Dict[str, int] = field(default_factory=dict)
    test_unit_domain_hits: Dict[str, int] = field(default_factory=dict)
    test_e2e_domain_hits: Dict[str, int] = field(default_factory=dict)
    test_files: int = 0
    unit_test_files: int = 0
    e2e_test_files: int = 0
    config_files: int = 0
    migration_files: int = 0
    git_error: str = ""
    validation_note_found: bool = False
    validation_note_snippet: str = ""
    style_only_note_found: bool = False
    style_only_note_snippet: str = ""
    repo_root: str = ""


# ---------------------------------------------------------------------------
# Risk factors, reducers, mitigations, categories.

@dataclass
class RiskFactor:
    id: str
    label: str
    points: float
    detail: str = ""


@dataclass
class Mitigation:
    factor_id: str
    actions: List[str] = field(default_factory=list)


@dataclass
class ConfidenceAdjustment:
    reason: str
    delta: float  # positive = more confident, negative = less


@dataclass
class ConfidenceBreakdown:
    base_score: float
    adjustments: List[ConfidenceAdjustment] = field(default_factory=list)
    final_score: float = 0.0


@dataclass
class RiskCategory:
    key: str
    label: str
    risk_score: float
    confidence: float = 0.0
    factors: List[str] = field(default_factory=list)
    reducers: List[str] = field(default_factory=list)
    breakdown: Optional[ConfidenceBreakdown] = None


@dataclass
class RiskReducer:
    id: str
    label: str
    points: float  # positive amount that reduces risk
    evidence: str = ""
    category_key: str = ""


@dataclass
class RequiredAction:
    id: str
    title: str
    priority: str = ""           # high | medium | supporting
    fix_type: str = ""           # code | test | config | process | infra | db
    applies_when: str = ""
    checklist: List[str] = field(default_factory=list)


@dataclass
class Integrations:
    jira_issue_key: str = ""
    pr_comment_markdown: str = ""


@dataclass
class RecommendedReview:
    strategy: str = ""
    routing_hints: List[str] = field(default_factory=list)


@dataclass
class ValidationEvidence:
    id: str
    label: str
    status: str  # pass | missing | unknown | not_evaluated | fail
    source: str = ""
    rationale: str = ""


@dataclass
class EvidenceSummary:
    pass_count: int = 0
    missing_count: int = 0
    unknown_count: int = 0
    not_evaluated_count: int = 0
    fail_count: int = 0


@dataclass
class Enforcement:
    merge_recommendation: str = ""  # PASS | WARN | BLOCK
    rationale: str = ""
    recommended_review: RecommendedReview = field(default_factory=RecommendedReview)
    required_validations: List[str] = field(default_factory=list)
    review_requirements: List[str] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    evidence_status: List[ValidationEvidence] = field(default_factory=list)
    evidence_summary: EvidenceSummary = field(default_factory=EvidenceSummary)


@dataclass
class ScoreMath:
    factors_subtotal: float = 0.0
    reducers_subtotal: float = 0.0
    net_before_floor: float = 0.0
    floor_min_score: float = 0.0
    floor_applied: bool = False
    floor_reasons: List[str] = field(default_factory=list)
    final_score: float = 0.0
    final_band: str = ""


# ---------------------------------------------------------------------------
# Result.
# context_insights uses Any here because the context subpackage lands in
# Phase 2. The placeholder allows Phase 1 to land standalone.

@dataclass
class Result:
    version: int = 0
    version_minor: int = 0
    report_version: str = ""
    generated_at: Optional[datetime] = None
    base_ref: str = ""
    signals: Signals = field(default_factory=Signals)
    risk_score: float = 0.0
    risk_band: str = ""
    score_math: ScoreMath = field(default_factory=ScoreMath)
    interpretation: str = ""
    factors: List[RiskFactor] = field(default_factory=list)
    categories: List[RiskCategory] = field(default_factory=list)
    reducers: List[RiskReducer] = field(default_factory=list)
    required_actions: List[RequiredAction] = field(default_factory=list)
    mitigations: List[Mitigation] = field(default_factory=list)
    integrations: Integrations = field(default_factory=Integrations)
    context_insights: Optional["ContextInsights"] = None  # type: ignore[name-defined]
    enforcement: Enforcement = field(default_factory=Enforcement)


# ---------------------------------------------------------------------------
# Scoring weights.

@dataclass
class ScoreWeights:
    large_diff_loc: int = 0
    large_diff_points: float = 0.0
    very_large_diff_loc: int = 0
    very_large_diff_points: float = 0.0
    many_files_threshold: int = 0
    many_files_points: float = 0.0
    auth_points: float = 0.0
    migrations_points: float = 0.0
    rag_points: float = 0.0
    processing_points: float = 0.0
    orchestration_points: float = 0.0
    web_large_loc: int = 0
    web_large_points: float = 0.0
    workflows_points: float = 0.0
    deploy_points: float = 0.0
    config_points: float = 0.0
    tests_missing_points: float = 0.0

    style_only_reducer_points: float = 0.0
    validation_note_reducer_points: float = 0.0
    workflow_partial_reducer_points: float = 0.0
    unit_test_evidence_reducer_points: float = 0.0
    e2e_test_evidence_reducer_points: float = 0.0
    test_only_diff_reducer_points: float = 0.0
    test_heavy_loc_ratio_threshold: float = 0.0
    test_heavy_reducer_points: float = 0.0

    context_proximity_low_points: float = 0.0
    context_scattered_points: float = 0.0
    context_hotspot_points: float = 0.0
    context_intent_mismatch_points: float = 0.0


def default_weights() -> ScoreWeights:
    """Mirrors Go DefaultWeights() exactly, preserving every constant."""
    return ScoreWeights(
        large_diff_loc=400,
        large_diff_points=12,
        very_large_diff_loc=2000,
        very_large_diff_points=22,
        many_files_threshold=35,
        many_files_points=14,
        auth_points=14,
        migrations_points=22,
        rag_points=10,
        processing_points=10,
        orchestration_points=10,
        web_large_loc=400,
        web_large_points=12,
        workflows_points=12,
        deploy_points=12,
        config_points=8,
        tests_missing_points=18,
        style_only_reducer_points=20,
        validation_note_reducer_points=6,
        workflow_partial_reducer_points=4,
        unit_test_evidence_reducer_points=5,
        e2e_test_evidence_reducer_points=10,
        test_only_diff_reducer_points=6,
        test_heavy_loc_ratio_threshold=0.40,
        test_heavy_reducer_points=4,
        context_proximity_low_points=5,
        context_scattered_points=5,
        context_hotspot_points=4,
        context_intent_mismatch_points=6,
    )
