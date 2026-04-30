"""Tests for pr_risk.types dataclasses and default_weights."""

from release_readiness_core.pr_risk.types import (
    EVIDENCE_PASS,
    EVIDENCE_MISSING,
    EVIDENCE_UNKNOWN,
    EVIDENCE_NOT_EVALUATED,
    EVIDENCE_FAIL,
    Enforcement,
    EvidenceSummary,
    FileChange,
    Mitigation,
    RecommendedReview,
    Result,
    RiskCategory,
    RiskFactor,
    RiskReducer,
    RequiredAction,
    ScoreMath,
    ScoreWeights,
    Signals,
    ValidationEvidence,
    default_weights,
)


def test_default_weights_match_go_defaults() -> None:
    """Every constant in DefaultWeights() in Go must match here exactly."""
    w = default_weights()
    assert w.large_diff_loc == 400
    assert w.large_diff_points == 12
    assert w.very_large_diff_loc == 2000
    assert w.very_large_diff_points == 22
    assert w.many_files_threshold == 35
    assert w.many_files_points == 14
    assert w.auth_points == 14
    assert w.migrations_points == 22
    assert w.rag_points == 10
    assert w.processing_points == 10
    assert w.orchestration_points == 10
    assert w.web_large_loc == 400
    assert w.web_large_points == 12
    assert w.workflows_points == 12
    assert w.deploy_points == 12
    assert w.config_points == 8
    assert w.tests_missing_points == 18
    assert w.style_only_reducer_points == 20
    assert w.validation_note_reducer_points == 6
    assert w.workflow_partial_reducer_points == 4
    assert w.unit_test_evidence_reducer_points == 5
    assert w.e2e_test_evidence_reducer_points == 10
    assert w.test_only_diff_reducer_points == 6
    assert w.test_heavy_loc_ratio_threshold == 0.40
    assert w.test_heavy_reducer_points == 4
    assert w.context_proximity_low_points == 5
    assert w.context_scattered_points == 5
    assert w.context_hotspot_points == 4
    assert w.context_intent_mismatch_points == 6


def test_evidence_status_constants() -> None:
    assert EVIDENCE_PASS == "pass"
    assert EVIDENCE_MISSING == "missing"
    assert EVIDENCE_UNKNOWN == "unknown"
    assert EVIDENCE_NOT_EVALUATED == "not_evaluated"
    assert EVIDENCE_FAIL == "fail"


def test_filechange_construction() -> None:
    fc = FileChange(path="internal/foo.go", added=10, deleted=2)
    assert fc.path == "internal/foo.go"
    assert fc.added == 10
    assert fc.deleted == 2

    fc_zero = FileChange(path="x")
    assert fc_zero.added == 0
    assert fc_zero.deleted == 0


def test_signals_default_empty_collections() -> None:
    s = Signals()
    assert s.files == []
    assert s.domain_hits == {}
    assert s.test_domain_hits == {}
    assert s.test_unit_domain_hits == {}
    assert s.test_e2e_domain_hits == {}
    assert s.file_count == 0
    assert s.git_error == ""


def test_riskfactor_riskreducer_construction() -> None:
    f = RiskFactor(id="domain_auth", label="Auth changes", points=14)
    assert f.id == "domain_auth"
    assert f.detail == ""

    r = RiskReducer(id="style_only", label="Style only", points=20, evidence="x")
    assert r.points == 20.0
    assert r.evidence == "x"
    assert r.category_key == ""


def test_mitigation_default_actions_empty() -> None:
    m = Mitigation(factor_id="x")
    assert m.actions == []


def test_required_action_defaults() -> None:
    a = RequiredAction(id="x", title="t")
    assert a.priority == ""
    assert a.fix_type == ""
    assert a.checklist == []


def test_recommended_review_defaults() -> None:
    r = RecommendedReview()
    assert r.strategy == ""
    assert r.routing_hints == []


def test_evidence_summary_defaults() -> None:
    s = EvidenceSummary()
    assert s.pass_count == 0
    assert s.missing_count == 0
    assert s.unknown_count == 0
    assert s.not_evaluated_count == 0
    assert s.fail_count == 0


def test_validation_evidence_construction() -> None:
    ve = ValidationEvidence(id="ci_baseline", label="CI", status=EVIDENCE_PASS)
    assert ve.status == "pass"
    assert ve.source == ""
    assert ve.rationale == ""


def test_score_math_defaults() -> None:
    sm = ScoreMath()
    assert sm.factors_subtotal == 0.0
    assert sm.floor_applied is False
    assert sm.floor_reasons == []


def test_enforcement_defaults() -> None:
    e = Enforcement()
    assert e.merge_recommendation == ""
    assert isinstance(e.recommended_review, RecommendedReview)
    assert isinstance(e.evidence_summary, EvidenceSummary)
    assert e.evidence_status == []


def test_riskcategory_defaults() -> None:
    c = RiskCategory(key="code", label="Code Risk", risk_score=42.5)
    assert c.factors == []
    assert c.reducers == []
    assert c.breakdown is None


def test_result_defaults() -> None:
    r = Result()
    assert r.version == 0
    assert r.report_version == ""
    assert r.context_insights is None
    assert isinstance(r.signals, Signals)
    assert isinstance(r.score_math, ScoreMath)
    assert isinstance(r.enforcement, Enforcement)
    assert isinstance(r.integrations.jira_issue_key, str)


def test_score_weights_zero_default() -> None:
    """ScoreWeights() with no args is all-zero — proves default_weights() is the canonical source."""
    w = ScoreWeights()
    assert w.large_diff_loc == 0
    assert w.auth_points == 0.0
