"""Bundled-default ``PRRiskConfig`` (SCRUM-243 / Phase 5 of SCRUM-238).

Phase 5 strips the project-specific defaults out of core. The bundled default
here ships only what is genuinely language-agnostic:

- ``domains: []`` — no domains by default. Every changed path classifies to
  ``"other"``. Adopters declare their domains in
  ``ops/release-readiness/pr-risk-config.yaml``.
- ``sensitive_domains: []`` — nothing is sensitive by default. ``tests_missing``
  factor never fires until the adopter declares sensitive domains.
- ``gates:`` — eight generic gates that work without any domain configuration:
  CI fetch depth, PR review summary, workflow / config validation,
  add tests / evidence, intent alignment, scattered review plan, test
  proximity, and hotspot regression focus.

Adopters who want domain-scoped gates (auth / RAG / migrations / etc.) author
those in their YAML config — see ``examples/pr-risk/`` for templates and
``docs/how-to/7-configure-pr-risk.md`` (added in Phase 6) for the walkthrough.
"""

from __future__ import annotations

from typing import List

from release_readiness_core.pr_risk._config import (
    ChecklistItem,
    Domain,
    Gate,
    GateEvidence,
    GateVariant,
    PRRiskConfig,
)


def default_pr_risk_config() -> PRRiskConfig:
    """Return the language-agnostic bundled-default ``PRRiskConfig``.

    Running ``release-readiness-pr-risk`` without an adopter-authored
    ``pr-risk-config.yaml`` produces this config: no project-specific gates,
    no project-specific domain hits, only generic checks.
    """
    return PRRiskConfig(
        version=1,
        domains=[],
        sensitive_domains=[],
        gates=_default_gates(),
    )


def _default_gates() -> List[Gate]:
    """Eight language-agnostic gates that work for any project's diff."""
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
                # No `domains` arg — the predicate has nothing to match against
                # under the bundled default's empty sensitive_domains. Adopters
                # add their own sensitive domains in their config.
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
