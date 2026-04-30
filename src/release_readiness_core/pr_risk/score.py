"""Scoring engine (port of internal/prrisk/score.go).

The deterministic core: builds factors from signals, applies context, subtracts
reducers, applies floor, returns Result. Phase 3 lands the score
math and categories; Phase 4 lands required-actions, full
enforcement, integrations. Until Phase 4 is in, those downstream fields are
populated by stub helpers in this module that return empty results.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from release_readiness_core.pr_risk._runtime import PRRiskRuntime

from release_readiness_core.pr_risk._context_bridge import (
    context_input_from_signals,
    risk_context_weights,
)
from release_readiness_core.pr_risk._internal import clamp_100 as _clamp100_internal
from release_readiness_core.pr_risk._round import round_half_away
from release_readiness_core.pr_risk.actions import compute_required_actions
from release_readiness_core.pr_risk.categories import compute_categories
from release_readiness_core.pr_risk.classify import touches_sensitive_code_without_tests
from release_readiness_core.pr_risk.context import analyze as context_analyze_fn
from release_readiness_core.pr_risk.floors import apply_risk_floor
from release_readiness_core.pr_risk.integrations import build_integrations
from release_readiness_core.pr_risk.interpret import build_interpretation
from release_readiness_core.pr_risk.mitigate import go_mod_changed, mitigate
from release_readiness_core.pr_risk.policy import compute_enforcement
from release_readiness_core.pr_risk.reducers import detect_reducers
from release_readiness_core.pr_risk.types import (
    DOMAIN_AUTH,
    DOMAIN_DEPLOY,
    DOMAIN_MIGRATIONS,
    DOMAIN_ORCHESTRATION,
    DOMAIN_PROCESSING,
    DOMAIN_RAG,
    DOMAIN_WORKFLOWS,
    Integrations,
    Result,
    RiskFactor,
    ScoreMath,
    ScoreWeights,
    Signals,
)
from release_readiness_core.pr_risk.version import (
    VERSION,
    VERSION_MINOR,
    report_version_string,
)


# Public helpers exposed for tests / callers.

def band(score: float) -> str:
    """Return risk band label from a score in [0, 100]."""
    if score < 20:
        return "low"
    if score < 45:
        return "medium"
    if score < 70:
        return "high"
    return "critical"


def clamp_100(x: float) -> float:
    """Clamp x to [0, 100], rounded to one decimal (mirrors Go score.go::clamp100).

    Go uses math.Round(x*10)/10 — half-away-from-zero, single decimal. The
    helper in _internal.py is plain clamp; this score-specific clamp also
    rounds. Both names exist because the Go source has them at module level.
    """
    if x < 0:
        return 0.0
    if x > 100:
        return 100.0
    return round_half_away(x * 10) / 10


def web_churn(s: Signals) -> int:
    """Total LOC churn within `web/` paths."""
    n = 0
    for f in s.files:
        if f.path.startswith("web/"):
            n += f.added + f.deleted
    return n


# ---------------------------------------------------------------------------

def score(
    s: Signals,
    w: ScoreWeights,
    jira_key: str = "",
    *,
    runtime: Optional["PRRiskRuntime"] = None,
) -> Result:
    """Apply weighted deterministic factors. jira_key is optional (for Integrations hook).

    ``runtime`` is optional; threaded into the config-driven classifier (Phase 2)
    so adopters with a custom ``pr-risk-config.yaml`` get their domains and
    sensitive-domain set. ``None`` uses the bundled-default runtime.
    """
    now = datetime.now(timezone.utc)
    factors: List[RiskFactor] = []
    factor_sum = 0.0

    def add(id_: str, label: str, pts: float, detail: str) -> None:
        nonlocal factor_sum
        if pts <= 0:
            return
        factors.append(RiskFactor(id=id_, label=label, points=pts, detail=detail))
        factor_sum += pts

    loc = float(s.total_loc)
    if s.git_error != "":
        add(
            "git_unavailable",
            "Git diff unavailable — risk from change size unknown",
            25,
            s.git_error,
        )
    else:
        if loc >= float(w.very_large_diff_loc):
            add(
                "diff_very_large",
                "Very large diff (high churn)",
                w.very_large_diff_points,
                f"total LOC churn (add+del)={s.total_loc} (threshold {w.very_large_diff_loc})",
            )
        elif loc >= float(w.large_diff_loc):
            add(
                "diff_large",
                "Large diff",
                w.large_diff_points,
                f"total LOC churn={s.total_loc} (threshold {w.large_diff_loc})",
            )
        if s.file_count >= w.many_files_threshold:
            add(
                "many_files",
                "Many files touched",
                w.many_files_points,
                f"{s.file_count} files (threshold {w.many_files_threshold})",
            )

    if s.domain_hits.get(DOMAIN_AUTH, 0) > 0:
        add(
            "domain_auth",
            "Auth/session/invite area changed",
            w.auth_points,
            f"{s.domain_hits.get(DOMAIN_AUTH, 0)} file(s) in auth-related paths",
        )
    if s.migration_files > 0 or s.domain_hits.get(DOMAIN_MIGRATIONS, 0) > 0:
        add(
            "domain_migrations",
            "Database migrations present",
            w.migrations_points,
            f"{s.migration_files} migration file(s)",
        )
    if s.domain_hits.get(DOMAIN_RAG, 0) > 0:
        add(
            "domain_rag",
            "RAG pipeline changed",
            w.rag_points,
            f"{s.domain_hits.get(DOMAIN_RAG, 0)} file(s)",
        )
    if s.domain_hits.get(DOMAIN_PROCESSING, 0) > 0:
        add(
            "domain_processing",
            "Processing/transcription pipeline changed",
            w.processing_points,
            f"{s.domain_hits.get(DOMAIN_PROCESSING, 0)} file(s)",
        )
    if s.domain_hits.get(DOMAIN_ORCHESTRATION, 0) > 0:
        add(
            "domain_orchestration",
            "Creator orchestration/recommendation flow changed",
            w.orchestration_points,
            f"{s.domain_hits.get(DOMAIN_ORCHESTRATION, 0)} file(s)",
        )

    web_loc = web_churn(s)
    if web_loc >= w.web_large_loc:
        add(
            "web_large",
            "Large frontend change",
            w.web_large_points,
            f"estimated web LOC churn≈{web_loc} (threshold {w.web_large_loc})",
        )

    if s.domain_hits.get(DOMAIN_WORKFLOWS, 0) > 0:
        add(
            "ci_workflows",
            "CI/GitHub Actions workflows changed",
            w.workflows_points,
            f"{s.domain_hits.get(DOMAIN_WORKFLOWS, 0)} workflow file(s)",
        )
    if s.domain_hits.get(DOMAIN_DEPLOY, 0) > 0:
        add(
            "deploy_config",
            "Deploy / container / hosting config changed",
            w.deploy_points,
            f"{s.domain_hits.get(DOMAIN_DEPLOY, 0)} file(s)",
        )
    if go_mod_changed(s):
        add(
            "go_mod_deps",
            "Go module or dependency lockfile changed",
            w.config_points,
            "go.mod and/or go.sum modified",
        )

    if touches_sensitive_code_without_tests(s, runtime=runtime):
        add(
            "tests_missing",
            "Sensitive areas changed without test file changes in this diff",
            w.tests_missing_points,
            "no *_test.go / web test paths in diff; consider adding or updating tests",
        )

    ctx_in = context_input_from_signals(s, runtime=runtime)
    c_insights, ctx_factors = context_analyze_fn(ctx_in, risk_context_weights(w))
    for cf in ctx_factors:
        add(cf.id, cf.label, cf.points, cf.detail)

    # Reducers deterministically lower risk by subtracting points from factor_sum.
    reducers = detect_reducers(s, factors, w)
    reducer_sum = sum(r.points for r in reducers)

    net_before_floor = clamp_100(factor_sum - reducer_sum)
    final_score, floor_applied, floor_min, floor_reasons = apply_risk_floor(
        net_before_floor, factors
    )

    risk_band = band(final_score)
    cats = compute_categories(s, factors, reducers, c_insights)
    req = compute_required_actions(
        s, factors, reducers, final_score, risk_band, c_insights, runtime=runtime,
    )

    score_math = ScoreMath(
        factors_subtotal=factor_sum,
        reducers_subtotal=reducer_sum,
        net_before_floor=net_before_floor,
        floor_min_score=floor_min,
        floor_applied=floor_applied,
        floor_reasons=floor_reasons,
        final_score=final_score,
        final_band=risk_band,
    )

    mits = mitigate(factors)

    res = Result(
        version=VERSION,
        version_minor=VERSION_MINOR,
        report_version=report_version_string(),
        generated_at=now,
        base_ref=s.base_ref,
        signals=s,
        risk_score=final_score,
        risk_band=risk_band,
        score_math=score_math,
        factors=factors,
        categories=cats,
        reducers=reducers,
        required_actions=req,
        mitigations=mits,
        context_insights=c_insights,
    )
    res.interpretation = build_interpretation(res)
    res.enforcement = compute_enforcement(res, runtime=runtime)
    res.integrations = build_integrations(
        factors, final_score, s.base_ref, jira_key, req, score_math, res.enforcement
    )
    return res
