"""Per-factor mitigation actions (port of internal/prrisk/mitigate.go)."""

from __future__ import annotations

import os.path
from typing import Iterable, List

from release_readiness_core.pr_risk.types import Mitigation, RiskFactor, Signals


# Static factor ID -> recommended actions. Order matches Go literal order
# for stability (audit trail), though factor presence/absence is the only
# observable input.
MITIGATION_MAP: dict = {
    "git_unavailable": [
        "Ensure CI checks out enough history (`fetch-depth: 0`) so `git diff base...HEAD` works.",
        "Run `release-readiness-pr-risk --base-ref <ref>` locally with a valid base.",
    ],
    "diff_very_large": [
        "Split the PR into smaller reviews (backend vs frontend vs docs).",
        "Add a high-level summary of behavioral changes in the PR description.",
    ],
    "diff_large": [
        "Review commit-by-commit; consider feature flags for risky paths.",
    ],
    "many_files": [
        "Group changes by subsystem in the PR description for reviewers.",
    ],
    "domain_auth": [
        "Run auth/session flows manually or via E2E (login, invite, participant).",
        "Verify cookie/session settings in staging (SameSite, HTTPS).",
    ],
    "domain_migrations": [
        "Run migrations against a copy of prod-like data; verify rollback plan.",
        "Coordinate deploy order (API before/after migration as required).",
    ],
    "domain_rag": [
        "Smoke-test Q&A with citations on a session with materials.",
        "Watch embedding/index job logs after deploy.",
    ],
    "domain_processing": [
        "Run material upload + processing pipeline smoke on a sample file.",
        "Confirm Whisper/job worker env in target environment.",
    ],
    "domain_orchestration": [
        "Validate creator orchestration flows (recommendation list/sync, draft approve/reject).",
        "Verify orchestration remains human-in-the-loop (no autonomous send/post actions).",
    ],
    "web_large": [
        "Run `npm run build` and spot-check creator/participant UIs.",
        "Cross-browser smoke if CSS/layout changed.",
    ],
    "ci_workflows": [
        "Validate workflow YAML in a fork or `act` where possible.",
        "Confirm secrets and required checks still match branch protection.",
    ],
    "deploy_config": [
        "Review Render/Docker/env parity with production.",
        "Schedule deploy during low-traffic window if infra changes.",
    ],
    "go_mod_deps": [
        "Re-run the project's full test suite and check for transitive license / compatibility issues.",
        "Verify the lockfile integrity in CI (e.g. `go mod verify`, `npm ci`, `pip-compile --strict`).",
    ],
    "tests_missing": [
        "Add or update unit/integration tests for changed packages.",
        "If behavior is unchanged refactor-only, note that in the PR description.",
    ],
    "context_test_proximity_distant": [
        "Add tests next to changed packages or link existing tests in the PR description.",
        "Prefer package-local *_test.go over only end-to-end coverage for the same change.",
    ],
    "context_change_scattered": [
        "Split the PR description by subsystem or commit so reviewers can validate incrementally.",
        "Consider follow-up PRs if the scatter is accidental.",
    ],
    "context_hotspot_overlap": [
        "Run focused regression on the overlapping prefix; several recent commits touched it, "
        "so regressions are likelier.",
        "Scan related modules for unintended behavior changes.",
    ],
    "context_intent_mismatch": [
        "Update the PR title/body to match the diff, or adjust the diff to match the stated intent.",
        "If intentional, explain the scope change explicitly for reviewers.",
    ],
}


_DEFAULT_ACTIONS = [
    "Review this factor in the context of your change and add validation notes to the PR.",
]


def mitigate(factors: Iterable[RiskFactor]) -> List[Mitigation]:
    """Return mitigations for each factor, deduped by factor ID, preserving input order."""
    out: List[Mitigation] = []
    seen: set = set()
    for f in factors:
        if f.id in seen:
            continue
        seen.add(f.id)
        actions = MITIGATION_MAP.get(f.id) or list(_DEFAULT_ACTIONS)
        out.append(Mitigation(factor_id=f.id, actions=list(actions)))
    return out


def go_mod_changed(s: Signals) -> bool:
    """Return True if go.mod or go.sum is in the diff."""
    for f in s.files:
        b = os.path.basename(f.path)
        if b == "go.mod" or b == "go.sum":
            return True
    return False
