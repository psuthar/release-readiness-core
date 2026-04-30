"""Compact unit tests for validations, routing, integrations, semantic_json."""

from release_readiness_core.pr_risk.context.types import (
    ConcentrationInsight,
    ContextInsights,
    HotspotInsight,
    IntentInsight,
    ProximityInsight,
)
from release_readiness_core.pr_risk.integrations import build_integrations
from release_readiness_core.pr_risk.routing import compute_routing_hints, join_comma_sorted
from release_readiness_core.pr_risk.semantic_json import (
    semantic_payload_for_test,
    top_factor_labels,
)
from release_readiness_core.pr_risk.types import (
    Enforcement,
    RecommendedReview,
    RequiredAction,
    Result,
    RiskCategory,
    RiskFactor,
    ScoreMath,
    Signals,
    CATEGORY_TEST_CONFIDENCE,
)
from release_readiness_core.pr_risk.validations import compute_required_validations


# ---------------------------------------------------------------------------
# validations

def test_required_validations_baseline_when_no_git_error() -> None:
    out = compute_required_validations(Signals(), [])
    assert any("required status checks" in v for v in out)


def test_required_validations_baseline_when_git_error() -> None:
    out = compute_required_validations(Signals(git_error="bad"), [])
    assert any("restore reliable git diff" in v for v in out)


def test_required_validations_dedupes() -> None:
    actions = [
        RequiredAction(id="auth_e2e_gate", title="x"),
        RequiredAction(id="auth_e2e_gate", title="y"),
    ]
    out = compute_required_validations(Signals(), actions)
    auth_lines = [v for v in out if "auth/session/invite" in v]
    assert len(auth_lines) == 1


def test_required_validations_validation_note_appended() -> None:
    out = compute_required_validations(Signals(validation_note_found=True), [])
    assert any("validation note present" in v for v in out)


# ---------------------------------------------------------------------------
# routing

def test_join_comma_sorted_empty() -> None:
    assert join_comma_sorted([]) == ""


def test_join_comma_sorted_basic() -> None:
    assert join_comma_sorted(["b", "a", "c"]) == "a, b, c"


def test_routing_hint_for_auth_domain() -> None:
    s = Signals(domain_hits={"auth": 1})
    out = compute_routing_hints(s, [], None)
    assert any("auth" in h for h in out)


def test_routing_hint_for_focused_concentration() -> None:
    ci = ContextInsights(
        concentration=ConcentrationInsight(mode="focused", top_prefix="internal/auth"),
    )
    s = Signals(domain_hits={"auth": 1}, file_count=3)
    out = compute_routing_hints(s, [], ci)
    assert any("internal/auth" in h for h in out)


def test_routing_default_hint_when_no_signals() -> None:
    s = Signals(file_count=1)
    out = compute_routing_hints(s, [], None)
    assert any("CODEOWNERS" in h for h in out)


# ---------------------------------------------------------------------------
# integrations

def _enf() -> Enforcement:
    return Enforcement(
        merge_recommendation="warn",
        rationale="medium risk",
        recommended_review=RecommendedReview(routing_hints=["look at auth"]),
        required_validations=["ci: must pass"],
    )


def test_build_integrations_writes_score_math_section() -> None:
    sm = ScoreMath(factors_subtotal=14.0, reducers_subtotal=4.0, final_score=10.0, final_band="low")
    out = build_integrations([], 10.0, "main", "", [], sm, _enf())
    assert "Score math" in out.pr_comment_markdown
    assert "factors 14.0" in out.pr_comment_markdown


def test_build_integrations_includes_jira_when_set() -> None:
    out = build_integrations([], 5.0, "main", "JIRA-123", [], ScoreMath(), _enf())
    assert "JIRA-123" in out.pr_comment_markdown
    assert out.jira_issue_key == "JIRA-123"


def test_build_integrations_truncates_long_factor_list() -> None:
    factors = [RiskFactor(id=f"f{i}", label=f"F{i}", points=float(i)) for i in range(5)]
    out = build_integrations(factors, 10.0, "main", "", [], ScoreMath(), _enf())
    assert "and 3 more in `pr_risk.md`" in out.pr_comment_markdown


# ---------------------------------------------------------------------------
# semantic_json

def test_top_factor_labels_orders_by_points_desc_then_id_asc() -> None:
    factors = [
        RiskFactor(id="b", label="Bb", points=5),
        RiskFactor(id="a", label="Aa", points=10),
        RiskFactor(id="c", label="Cc", points=10),
    ]
    out = top_factor_labels(factors, 5)
    # 10-pts come first; tie broken by id alphabetic; then 5-pts.
    assert out == ["Aa", "Cc", "Bb"]


def test_top_factor_labels_truncates_to_n() -> None:
    factors = [RiskFactor(id=f"f{i}", label=f"F{i}", points=float(10 - i)) for i in range(10)]
    out = top_factor_labels(factors, 3)
    assert len(out) == 3


def test_semantic_payload_uppercases_recommendation() -> None:
    r = Result(
        report_version="v2.8",
        risk_score=42.0,
        risk_band="medium",
        enforcement=Enforcement(merge_recommendation="warn", required_validations=["x"]),
    )
    payload = semantic_payload_for_test(r)
    assert payload["merge_recommendation"] == "WARN"


def test_semantic_payload_includes_test_confidence_when_present() -> None:
    cat = RiskCategory(key=CATEGORY_TEST_CONFIDENCE, label="x", risk_score=20.0, confidence=80.0)
    r = Result(
        report_version="v2.8",
        risk_score=20.0,
        risk_band="medium",
        categories=[cat],
        enforcement=Enforcement(merge_recommendation="warn"),
    )
    payload = semantic_payload_for_test(r)
    assert payload["test_confidence"] == 80


def test_semantic_payload_omits_top_risk_factors_when_empty() -> None:
    r = Result(report_version="v2.8")
    payload = semantic_payload_for_test(r)
    assert "top_risk_factors" not in payload
