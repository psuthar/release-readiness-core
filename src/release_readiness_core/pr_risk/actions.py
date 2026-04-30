"""Required actions (port of actions.go)."""

from __future__ import annotations

from typing import List, Optional

from release_readiness_core.pr_risk._internal import factor_ids, ok_bool
from release_readiness_core.pr_risk.actions_priority import (
    priority_for_action_id,
    sort_required_actions,
)
from release_readiness_core.pr_risk.context.types import ContextInsights
from release_readiness_core.pr_risk.types import (
    DOMAIN_API,
    DOMAIN_AUTH,
    DOMAIN_DATABASE,
    DOMAIN_MIGRATIONS,
    DOMAIN_ORCHESTRATION,
    DOMAIN_PROCESSING,
    DOMAIN_RAG,
    RequiredAction,
    RiskFactor,
    RiskReducer,
    Signals,
)


def _has_sensitive_domain_hit(s: Signals) -> bool:
    """Sensitive domains: auth, rag, processing, orchestration, migrations, api, database."""
    return (
        s.domain_hits.get(DOMAIN_AUTH, 0) > 0
        or s.domain_hits.get(DOMAIN_RAG, 0) > 0
        or s.domain_hits.get(DOMAIN_PROCESSING, 0) > 0
        or s.domain_hits.get(DOMAIN_ORCHESTRATION, 0) > 0
        or s.domain_hits.get(DOMAIN_MIGRATIONS, 0) > 0
        or s.domain_hits.get(DOMAIN_API, 0) > 0
        or s.domain_hits.get(DOMAIN_DATABASE, 0) > 0
    )


def _evidence_level(s: Signals, domain: str) -> str:
    if s.test_e2e_domain_hits.get(domain, 0) > 0:
        return "e2e"
    if s.test_unit_domain_hits.get(domain, 0) > 0:
        return "unit"
    return "none"


def compute_required_actions(
    s: Signals,
    factors: List[RiskFactor],
    reducers: List[RiskReducer],
    risk_score: float,
    risk_band: str,
    insights: Optional[ContextInsights],
) -> List[RequiredAction]:
    """Build the deterministic list of pre-merge required actions, sorted by priority."""
    has = factor_ids(factors)
    has_validation_note = s.validation_note_found
    gate_critical = risk_band == "critical" or risk_score >= 70
    gate_high = risk_band == "high" or risk_score >= 45

    out: List[RequiredAction] = []
    seen: set = set()

    def add(a: RequiredAction) -> None:
        if a.id in seen:
            return
        if a.priority == "":
            a.priority = priority_for_action_id(a.id)
        seen.add(a.id)
        out.append(a)

    if ok_bool(has, "git_unavailable"):
        add(RequiredAction(
            id="ci_fetch_depth_zero",
            title="Ensure git history is available for diff",
            fix_type="infra",
            applies_when="git diff base...HEAD was unavailable",
            checklist=[
                "Confirm CI uses `fetch-depth: 0` (or an equivalent full-history checkout).",
                "Re-run PR risk scoring after the checkout depth fix.",
            ],
        ))

    if ok_bool(has, "diff_large") or ok_bool(has, "diff_very_large") or ok_bool(has, "many_files"):
        add(RequiredAction(
            id="pr_review_summary",
            title="Make PR review scoped and evidence-backed",
            fix_type="process",
            checklist=[
                "Add a PR description summary: what changed and why.",
                "Group changes by subsystem so reviewers can validate quickly.",
            ],
        ))

    if ok_bool(has, "ci_workflows") or ok_bool(has, "deploy_config") or ok_bool(has, "go_mod_deps"):
        msg = "Confirm required checks and env parity before merge."
        if has_validation_note:
            msg = "Validation note is present; confirm required checks and env parity before merge."
        add(RequiredAction(
            id="workflow_config_validation",
            title="Validate workflow / deploy config changes",
            fix_type="config",
            checklist=[
                msg,
                "If CI fails, identify whether it is test flakiness vs behavior change and update evidence accordingly.",
            ],
        ))

    if gate_critical or gate_high:
        if ok_bool(has, "domain_auth"):
            level = _evidence_level(s, DOMAIN_AUTH)
            check = [
                "Ensure auth E2E coverage is green for the affected flow(s).",
                "Spot-check cookie/session behavior changes in staging-like conditions (SameSite, HTTPS).",
            ]
            if level == "none":
                check[0] = "Run auth/session E2E flows before merge (login, invite, participant)."
            elif level == "unit":
                check[0] = "Confirm auth unit tests pass; run auth E2E smoke for login/invite/participant before merge."
            add(RequiredAction(
                id="auth_e2e_gate",
                title="Validate auth/session flows (login, invite, participant)",
                fix_type="test",
                applies_when="auth/session/invite domain changed",
                checklist=check,
            ))

        if ok_bool(has, "domain_rag"):
            level = _evidence_level(s, DOMAIN_RAG)
            checklist = [
                "Run `qa_rag`-targeted E2E smoke and confirm citations attach to answers.",
                "If relevant, re-index or verify embedding job health post-deploy.",
            ]
            if level == "none":
                checklist[0] = "Run Q&A with citations E2E before merge (session ask + citations verification)."
            elif level == "unit":
                checklist[0] = "Confirm unit-level RAG changes pass; run Q&A-with-citations E2E smoke before merge."
            add(RequiredAction(
                id="rag_qna_citations_gate",
                title="Validate Q&A with citations for decision-grade answers",
                fix_type="test",
                applies_when="RAG / Q&A pipelines changed",
                checklist=checklist,
            ))

        if ok_bool(has, "domain_processing"):
            level = _evidence_level(s, DOMAIN_PROCESSING)
            checklist = [
                "Run a materials upload + processing smoke on a representative file.",
                "Confirm transcript/job worker logs look healthy (no silent failures).",
            ]
            if level == "none":
                checklist[0] = "Run materials upload + processing smoke before merge (representative file)."
            elif level == "unit":
                checklist[0] = "Confirm processing unit tests pass; run processing smoke before merge."
            add(RequiredAction(
                id="materials_processing_gate",
                title="Validate materials upload + processing pipeline",
                fix_type="process",
                applies_when="processing/transcription pipeline changed",
                checklist=checklist,
            ))

        if ok_bool(has, "domain_orchestration"):
            level = _evidence_level(s, DOMAIN_ORCHESTRATION)
            checklist = [
                "Run creator orchestration recommendation flow checks (list/sync + approve/reject draft paths).",
                "Confirm no autonomous send/post behavior is introduced in orchestration paths.",
            ]
            if level == "none":
                checklist[0] = "Run orchestration smoke/E2E before merge (recommendations panel + draft approve/reject)."
            elif level == "unit":
                checklist[0] = "Confirm orchestration unit/integration tests pass; run creator orchestration smoke before merge."
            add(RequiredAction(
                id="orchestration_creator_gate",
                title="Validate creator orchestration recommendation flows",
                fix_type="test",
                applies_when="orchestration recommendation/review paths changed",
                checklist=checklist,
            ))

        if ok_bool(has, "domain_migrations"):
            level = _evidence_level(s, DOMAIN_MIGRATIONS)
            checklist = [
                "Run migrations with validation evidence and confirm expected schema/data behavior.",
                "Verify rollback plan (or migration reversal strategy) is documented and executable.",
            ]
            if level == "e2e":
                checklist[0] = "Ensure migration validation tests/evidence are part of CI and are green before merge."
            elif level == "unit":
                checklist[0] = "Confirm unit coverage exists for migrations; run migration validation smoke before merge."
            add(RequiredAction(
                id="migrations_validation_gate",
                title="Validate database migrations before merge",
                fix_type="db",
                applies_when="migration files changed",
                checklist=checklist,
            ))

        if ok_bool(has, "tests_missing"):
            add(RequiredAction(
                id="add_tests_or_evidence",
                title="Add/update tests (or record evidence) before merge",
                fix_type="test",
                applies_when="sensitive code changed without any test file changes in this diff",
                checklist=[
                    "Add or update unit/integration tests for the changed packages.",
                    "Re-run `go test ./...` and ensure E2E smoke covers the sensitive area(s).",
                ],
            ))

    # Medium-band tests_missing reminder (only if not already gated under high).
    if (not gate_high) and ok_bool(has, "tests_missing"):
        add(RequiredAction(
            id="add_tests_or_evidence",
            title="Add/update tests before merge",
            fix_type="test",
            checklist=[
                "Add or update tests for changed code paths and confirm `go test ./...` passes.",
            ],
        ))

    if insights is not None:
        if insights.intent.mismatch:
            add(RequiredAction(
                id="context_align_pr_description",
                title="Align PR title/description with the diff",
                fix_type="process",
                checklist=[
                    "Update the PR title or body so keywords match the areas actually changed, "
                    "or narrow the diff to match the stated intent.",
                    "If the scope is intentional, explain why expected domains are not touched.",
                ],
            ))
        if insights.concentration.mode == "scattered" and s.file_count >= 10:
            add(RequiredAction(
                id="context_scattered_review_plan",
                title="Structure review for a scattered change",
                fix_type="process",
                checklist=[
                    "Add a short map of files grouped by subsystem (or commit) to speed review.",
                    "Call out cross-cutting concerns explicitly (auth, DB, RAG, web).",
                ],
            ))
        if (
            insights.proximity.mode == "distant"
            and insights.proximity.non_test_files >= 2
            and _has_sensitive_domain_hit(s)
        ):
            add(RequiredAction(
                id="context_improve_test_proximity",
                title="Improve test proximity for changed code",
                fix_type="test",
                checklist=[
                    "Add or reference tests in the same package or directory as changed production files.",
                    "If tests live elsewhere, link them in the PR description.",
                ],
            ))
        if len(insights.hotspots) > 0:
            p = insights.hotspots[0].prefix
            add(RequiredAction(
                id="context_hotspot_regression_focus",
                title="Extra regression focus on active path (recent commits)",
                fix_type="process",
                checklist=[
                    f"Prefix `{p}` is active in recent history; run targeted smoke for behavior touching this area.",
                    "Watch for unintended side effects in adjacent modules.",
                ],
            ))

    return sort_required_actions(out)
