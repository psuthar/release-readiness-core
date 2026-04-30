"""Bundled-default ``PRRiskConfig`` (SCRUM-239 / Phase 1 of SCRUM-238).

This module is the single source of truth for the data shape that today's
hardcoded behavior in ``classify.py`` / ``actions.py`` / ``validations.py`` /
``actions_priority.py`` / ``evidence.py`` produces. Phase 1 ships it without
wiring it in: the existing modules continue to drive runtime behavior, and the
parity-fixture YAML at ``tests/pr_risk/fixtures/pr-risk-corpus-config.yaml``
must round-trip to a deeply-equal ``PRRiskConfig``.

Phase 5 (SCRUM-243) will replace this with a minimal language-agnostic config.
Until then, this is the bundled default that ``PRRiskRuntime.from_default()``
returns.
"""

from __future__ import annotations

from typing import Any, Dict, List

from release_readiness_core.pr_risk._config import (
    ChecklistItem,
    Domain,
    Gate,
    GateEvidence,
    GateVariant,
    PRRiskConfig,
)


def default_pr_risk_config() -> PRRiskConfig:
    """Return a ``PRRiskConfig`` mirroring today's hardcoded behavior."""
    return PRRiskConfig(
        version=1,
        domains=_default_domains(),
        sensitive_domains=_default_sensitive_domains(),
        gates=_default_gates(),
    )


# ---------------------------------------------------------------------------
# Domains.
#
# Order is significant: the classifier returns the first domain whose patterns
# match. This mirrors the switch order in the current ``classify.classify_area``
# implementation.

def _default_domains() -> List[Domain]:
    return [
        Domain(id="migrations", label="migrations", patterns=[
            {"prefix": "db/migrations/"},
            {"prefix": "internal/migrations/"},
        ]),
        Domain(id="auth", label="auth", patterns=[
            {"prefix": "internal/auth/"},
            {"prefix": "internal/invitations/"},
            {"and": [
                {"contains": "internal/handlers/"},
                {"any_contains": [
                    "login",
                    "session_invite",
                    "invitations",
                    "session_participant",
                    "zoom_auth",
                    "teams_auth",
                    "auth",
                    "invite",
                ]},
            ]},
        ]),
        Domain(id="rag", label="rag", patterns=[
            {"prefix": "internal/rag/"},
            {"contains": "internal/utils/qa.go"},
            {"any_contains": [
                "internal/handlers/session_ask",
                "internal/handlers/session_questions",
                "internal/handlers/session_reindex",
            ]},
        ]),
        Domain(id="processing", label="processing", patterns=[
            {"prefix": "internal/processing/"},
            {"any_contains": [
                "internal/handlers/transcript_",
                "internal/handlers/transcript",
                "internal/handlers/video_url_ingestion",
                "internal/handlers/video_upload",
                "internal/handlers/session_materials",
                "internal/handlers/transcript_job_status",
                "internal/handlers/transcript_jobs",
            ]},
        ]),
        Domain(id="storage", label="storage", patterns=[
            {"prefix": "internal/storage/"},
        ]),
        Domain(id="orchestration", label="orchestration", patterns=[
            {"prefix": "internal/orchestration/"},
            {"contains": "internal/handlers/session_orchestration"},
            {"contains": "internal/database/orchestration_recommendations"},
            {"contains": "internal/database/orchestration_recommendation_audit"},
            {"contains": "web/src/modes/creatormode"},
        ]),
        Domain(id="database", label="database", patterns=[
            {"prefix": "internal/database/"},
        ]),
        Domain(id="web", label="web", patterns=[
            {"prefix": "web/"},
        ]),
        Domain(id="workflows", label="workflows", patterns=[
            {"prefix": ".github/workflows/"},
        ]),
        Domain(id="deploy", label="deploy", patterns=[
            {"prefix": "deploy/"},
            {"exact": "dockerfile"},
            {"endswith": "/dockerfile"},
            {"endswith": "render.yaml"},
            {"contains": "/render.yaml"},
        ]),
        Domain(id="api", label="api", patterns=[
            {"prefix": "internal/handlers/"},
            {"prefix": "cmd/"},
            {"prefix": "internal/"},
        ]),
        Domain(id="scripts", label="scripts", patterns=[
            {"prefix": "scripts/"},
        ]),
    ]


def _default_sensitive_domains() -> List[str]:
    """Domains used by ``touches_sensitive_code_without_tests`` to decide whether
    the ``tests_missing`` factor fires when the diff has no test files. Mirrors
    the ``sensitive`` set in ``classify.touches_sensitive_code_without_tests``.
    """
    return [
        "auth",
        "api",
        "database",
        "rag",
        "processing",
        "orchestration",
        "web",
        "migrations",
    ]


# ---------------------------------------------------------------------------
# Gates.

# Domains the ``proximity_distant_with_sensitive`` predicate inspects. Mirrors
# ``actions._has_sensitive_domain_hit`` (no ``web``).
_PROXIMITY_SENSITIVE_DOMAINS: List[str] = [
    "auth",
    "rag",
    "processing",
    "orchestration",
    "migrations",
    "api",
    "database",
]


def _default_gates() -> List[Gate]:
    return [
        Gate(
            id="ci_fetch_depth_zero",
            title="Ensure git history is available for diff",
            priority="high",
            fix_type="infra",
            applies_when=[{"factor_id": "git_unavailable"}],
            applies_when_extra="git diff base...HEAD was unavailable",
            validation_line="ci: full git history available for diff (fetch-depth: 0 or equivalent)",
            checklist=[
                ChecklistItem(text="Confirm CI uses `fetch-depth: 0` (or an equivalent full-history checkout)."),
                ChecklistItem(text="Re-run PR risk scoring after the checkout depth fix."),
            ],
            evidence=GateEvidence(template="signal_check", args={"signal_field": "git_error"}),
        ),
        Gate(
            id="pr_review_summary",
            title="Make PR review scoped and evidence-backed",
            priority="supporting",
            fix_type="process",
            applies_when=[
                {"factor_id": ["diff_large", "diff_very_large", "many_files"]},
            ],
            validation_line="process: PR description with scoped, evidence-backed review plan",
            checklist=[
                ChecklistItem(text="Add a PR description summary: what changed and why."),
                ChecklistItem(text="Group changes by subsystem so reviewers can validate quickly."),
            ],
            evidence=GateEvidence(template="intent_strength"),
        ),
        Gate(
            id="workflow_config_validation",
            title="Validate workflow / deploy config changes",
            priority="medium",
            fix_type="config",
            applies_when=[
                {"factor_id": ["ci_workflows", "deploy_config", "go_mod_deps"]},
            ],
            validation_line="config: workflow / deploy / go.mod changes validated against required checks",
            checklist=[
                ChecklistItem(
                    text="Confirm required checks and env parity before merge.",
                    by_validation_note="Validation note is present; confirm required checks and env parity before merge.",
                ),
                ChecklistItem(
                    text="If CI fails, identify whether it is test flakiness vs behavior change and update evidence accordingly.",
                ),
            ],
            evidence=GateEvidence(template="validation_note"),
        ),
        Gate(
            id="auth_e2e_gate",
            title="Validate auth/session flows (login, invite, participant)",
            priority="high",
            fix_type="test",
            applies_when=[
                {"risk_band": ["high", "critical"]},
                {"factor_id": "domain_auth"},
            ],
            applies_when_extra="auth/session/invite domain changed",
            validation_line="test: auth/session/invite flows exercised (E2E or equivalent evidence)",
            checklist=[
                ChecklistItem(
                    text="Ensure auth E2E coverage is green for the affected flow(s).",
                    by_evidence_level={
                        "none": "Run auth/session E2E flows before merge (login, invite, participant).",
                        "unit": "Confirm auth unit tests pass; run auth E2E smoke for login/invite/participant before merge.",
                    },
                ),
                ChecklistItem(text="Spot-check cookie/session behavior changes in staging-like conditions (SameSite, HTTPS)."),
            ],
            evidence=GateEvidence(template="test_domain", args={"domain": "auth"}),
        ),
        Gate(
            id="rag_qna_citations_gate",
            title="Validate Q&A with citations for decision-grade answers",
            priority="high",
            fix_type="test",
            applies_when=[
                {"risk_band": ["high", "critical"]},
                {"factor_id": "domain_rag"},
            ],
            applies_when_extra="RAG / Q&A pipelines changed",
            validation_line="test: Q&A with citations validated for RAG-affecting changes",
            checklist=[
                ChecklistItem(
                    text="Run `qa_rag`-targeted E2E smoke and confirm citations attach to answers.",
                    by_evidence_level={
                        "none": "Run Q&A with citations E2E before merge (session ask + citations verification).",
                        "unit": "Confirm unit-level RAG changes pass; run Q&A-with-citations E2E smoke before merge.",
                    },
                ),
                ChecklistItem(text="If relevant, re-index or verify embedding job health post-deploy."),
            ],
            evidence=GateEvidence(template="test_domain", args={"domain": "rag"}),
        ),
        Gate(
            id="materials_processing_gate",
            title="Validate materials upload + processing pipeline",
            priority="medium",
            fix_type="process",
            applies_when=[
                {"risk_band": ["high", "critical"]},
                {"factor_id": "domain_processing"},
            ],
            applies_when_extra="processing/transcription pipeline changed",
            validation_line="test: materials upload + processing smoke for pipeline changes",
            checklist=[
                ChecklistItem(
                    text="Run a materials upload + processing smoke on a representative file.",
                    by_evidence_level={
                        "none": "Run materials upload + processing smoke before merge (representative file).",
                        "unit": "Confirm processing unit tests pass; run processing smoke before merge.",
                    },
                ),
                ChecklistItem(text="Confirm transcript/job worker logs look healthy (no silent failures)."),
            ],
            evidence=GateEvidence(template="test_domain", args={"domain": "processing"}),
        ),
        Gate(
            id="orchestration_creator_gate",
            title="Validate creator orchestration recommendation flows",
            priority="medium",
            fix_type="test",
            applies_when=[
                {"risk_band": ["high", "critical"]},
                {"factor_id": "domain_orchestration"},
            ],
            applies_when_extra="orchestration recommendation/review paths changed",
            validation_line="",
            checklist=[
                ChecklistItem(
                    text="Run creator orchestration recommendation flow checks (list/sync + approve/reject draft paths).",
                    by_evidence_level={
                        "none": "Run orchestration smoke/E2E before merge (recommendations panel + draft approve/reject).",
                        "unit": "Confirm orchestration unit/integration tests pass; run creator orchestration smoke before merge.",
                    },
                ),
                ChecklistItem(text="Confirm no autonomous send/post behavior is introduced in orchestration paths."),
            ],
            evidence=GateEvidence(template="test_domain", args={"domain": "orchestration"}),
        ),
        Gate(
            id="migrations_validation_gate",
            title="Validate database migrations before merge",
            priority="high",
            fix_type="db",
            applies_when=[
                {"risk_band": ["high", "critical"]},
                {"factor_id": "domain_migrations"},
            ],
            applies_when_extra="migration files changed",
            validation_line="db: migrations validated with rollback/reversal plan documented",
            checklist=[
                ChecklistItem(
                    text="Run migrations with validation evidence and confirm expected schema/data behavior.",
                    by_evidence_level={
                        "unit": "Confirm unit coverage exists for migrations; run migration validation smoke before merge.",
                        "e2e": "Ensure migration validation tests/evidence are part of CI and are green before merge.",
                    },
                ),
                ChecklistItem(text="Verify rollback plan (or migration reversal strategy) is documented and executable."),
            ],
            evidence=GateEvidence(template="migrations"),
        ),
        Gate(
            id="add_tests_or_evidence",
            title="Add/update tests before merge",
            priority="high",
            fix_type="test",
            applies_when=[{"factor_id": "tests_missing"}],
            validation_line="test: tests or recorded evidence for sensitive paths",
            checklist=[
                ChecklistItem(text="Add or update tests for changed code paths and confirm the project's test suite passes."),
            ],
            variants=[
                GateVariant(
                    when={"risk_band": ["high", "critical"]},
                    title="Add/update tests (or record evidence) before merge",
                    applies_when_extra="sensitive code changed without any test file changes in this diff",
                    checklist=[
                        ChecklistItem(text="Add or update unit/integration tests for the changed packages."),
                        ChecklistItem(text="Re-run the project's test suite and ensure E2E smoke covers the sensitive area(s)."),
                    ],
                ),
            ],
            evidence=GateEvidence(template="add_tests"),
        ),
        Gate(
            id="context_align_pr_description",
            title="Align PR title/description with the diff",
            priority="medium",
            fix_type="process",
            applies_when=[{"intent_mismatch": True}],
            validation_line="process: PR title/body aligned with actual diff (intent match)",
            checklist=[
                ChecklistItem(text="Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent."),
                ChecklistItem(text="If the scope is intentional, explain why expected domains are not touched."),
            ],
            evidence=GateEvidence(template="intent_alignment"),
        ),
        Gate(
            id="context_scattered_review_plan",
            title="Structure review for a scattered change",
            priority="supporting",
            fix_type="process",
            applies_when=[{"concentration_mode": "scattered", "min_file_count": 10}],
            validation_line="process: structured review map for scattered multi-area change",
            checklist=[
                ChecklistItem(text="Add a short map of files grouped by subsystem (or commit) to speed review."),
                ChecklistItem(text="Call out cross-cutting concerns explicitly (auth, DB, RAG, web)."),
            ],
            evidence=GateEvidence(template="intent_aligned_or_weak"),
        ),
        Gate(
            id="context_improve_test_proximity",
            title="Improve test proximity for changed code",
            priority="supporting",
            fix_type="test",
            applies_when=[{
                "proximity_distant_with_sensitive": True,
                "min_non_test_files": 2,
                "domains": list(_PROXIMITY_SENSITIVE_DOMAINS),
            }],
            validation_line="test: tests co-located or explicitly linked for changed code",
            checklist=[
                ChecklistItem(text="Add or reference tests in the same package or directory as changed production files."),
                ChecklistItem(text="If tests live elsewhere, link them in the PR description."),
            ],
            evidence=GateEvidence(template="proximity"),
        ),
        Gate(
            id="context_hotspot_regression_focus",
            title="Extra regression focus on active path (recent commits)",
            priority="supporting",
            fix_type="process",
            applies_when=[{"hotspots_present": True}],
            validation_line=(
                "test: targeted regression for path prefixes with several recent commits "
                "overlapping this diff"
            ),
            checklist=[
                ChecklistItem(text="Prefix `{prefix}` is active in recent history; run targeted smoke for behavior touching this area."),
                ChecklistItem(text="Watch for unintended side effects in adjacent modules."),
            ],
            evidence=GateEvidence(template="hotspot"),
        ),
    ]
