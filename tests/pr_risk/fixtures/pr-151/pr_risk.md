# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:38Z  
**Base ref:** `265f98b85763cf8a74bb299ea56caa30c2317764`  

> High risk (score 45). Significant risk factors detected. Complete all required actions before merging.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **45.0** / 100 |
| Band | **high** |
| Report version | **v2.8** |
| Test confidence | **30** / 100 |
| Files changed | 10 |
| LOC churn (add+del) | 504 |
| Test files in diff | 2 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **BLOCK** |
| Rationale | Risk band is high (score 45/100); treat as merge-blocked until required actions and validations are satisfied. |
| Evidence | 1 pass · 2 missing · 1 fail · 2 not evaluated |

### Recommended review strategy

Do not merge until required validations pass and reviewers confirm mitigation of listed risks. Re-run prrisk after substantive changes.

### Review routing (recommended)

- Include frontend review for web/ UI and client behavior.
- Include database/migrations review before merge.
- Extra reviewer attention on `web/src` (several recent commits touched this area).
- Confirm scope with author: PR text implies domains api, auth but diff may differ.

### Blocking / elevated review reasons

- Merge-block policy: risk band "high" (score 45) requires completing high-priority actions before merge.
- Evidence MISSING [migrations_validation_gate]: 2 migration file(s) changed; no validation note or E2E coverage detected.
- Evidence FAIL [context_align_pr_description]: PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required validations are distinct from mitigations: validations are merge gates; mitigations are factor-specific guidance.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- db: migrations validated with rollback/reversal plan documented
- process: PR title/body aligned with actual diff (intent match)
- test: targeted regression for path prefixes with several recent commits overlapping this diff
- test: tests co-located or explicitly linked for changed code
- process: PR description with scoped, evidence-backed review plan

### Evidence status (repo-local signals)

> ✅ 1 pass · ⚠️ 2 missing · ❌ 1 fail · 📋 2 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `migrations_validation_gate` | ⚠️ missing | git_signals | 2 migration file(s) changed; no validation note or E2E coverage detected. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |
| `context_hotspot_regression_focus` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note detected; targeted regression coverage cannot be confirmed from diff alone — requires human review. |
| `context_improve_test_proximity` | ⚠️ missing | proximity | Structural alignment is "distant" with no test coverage evidence for this diff. |
| `pr_review_summary` | ✅ pass | intent | PR title/body has strong keywords aligned with the diff. |

### Manual merge prerequisites

- At least one approving review on the changed code.
- Explicit sign-off that required actions and validations are complete before merge.
- Prefer a reviewer familiar with the touched subsystems (see recommended_review.routing_hints).
- Confirm CI is green for all required checks tied to this branch.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **49.0** |
| Reducers subtotal (points subtracted) | **4.0** |
| Net before floor | **45.0** |
| Floor minimum (when rules apply) | **20** |
| Floor applied | **no** |
| Floor reasons | Large diff cannot score in the low band (floor applies) |
| **Final score** | **45.0** |
| **Final band** | **high** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — Many changed production files have no test file in the same directory or an obvious sibling path in this diff.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **8** with nearby test in diff: **2** (ratio **25%**)

### Change concentration

- **Mode:** `balanced` — Churn is spread across several areas in a typical way.
- Top area: `web/src` (~57% of churn); **5** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/src`** — 20 distinct commits (sampled) — Prefix touched in 20 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-125: allow creators to set display titles for session videos
- **Keywords matched:** session
- **Domains implied by text:** auth, api
- **Domains in diff (non-test):** api, database, migrations, web
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| api | 3 |
| database | 1 |
| migrations | 2 |
| tests | 2 |
| web | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 49.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 70.0 | 30 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| Sensitive domains changed | -10 |
| Unit tests present in diff | +20 |
| Tests structurally distant from changed code | -15 |
| Behavioral coverage depth unknown | -5 |
| Behavioral coverage depth unknown for sensitive domain changes | -5 |
| Few changed files have nearby tests in diff | -5 |

**Final confidence score: 30 / 100**

## Risk factors

### Large diff (`diff_large`)

- **Points:** 12.0
- **Detail:** total LOC churn=504 (threshold 400)

### Database migrations present (`domain_migrations`)

- **Points:** 22.0
- **Detail:** 2 migration file(s)

### Tests not co-located with changed code in this diff (`context_test_proximity_distant`)

- **Points:** 5.0
- **Detail:** Many changed production files have no test file in the same directory or an obvious sibling path in this diff.

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 20 of the last 50 sampled commits — sustained activity; extra regression care.

### PR title/body keywords do not align with paths in the diff (`context_intent_mismatch`)

- **Points:** 6.0
- **Detail:** Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.


## Reducers (what lowers risk)

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 46% of LOC churn is in test files


## Required actions before merge

### [ high ] Validate database migrations before merge

- Run migrations with validation evidence and confirm expected schema/data behavior.
- Verify rollback plan (or migration reversal strategy) is documented and executable.

### [ medium ] Align PR title/description with the diff

- Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent.
- If the scope is intentional, explain why expected domains are not touched.

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `web/src` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

### [ supporting ] Improve test proximity for changed code

- Add or reference tests in the same package or directory as changed production files.
- If tests live elsewhere, link them in the PR description.

### [ supporting ] Make PR review scoped and evidence-backed

- Add a PR description summary: what changed and why.
- Group changes by subsystem so reviewers can validate quickly.

## Mitigations

### `diff_large`

- Review commit-by-commit; consider feature flags for risky paths.

### `domain_migrations`

- Run migrations against a copy of prod-like data; verify rollback plan.
- Coordinate deploy order (API before/after migration as required).

### `context_test_proximity_distant`

- Add tests next to changed packages or link existing tests in the PR description.
- Prefer package-local *_test.go over only end-to-end coverage for the same change.

### `context_hotspot_overlap`

- Run focused regression on the overlapping prefix; several recent commits touched it, so regressions are likelier.
- Scan related modules for unintended behavior changes.

### `context_intent_mismatch`

- Update the PR title/body to match the diff, or adjust the diff to match the stated intent.
- If intentional, explain the scope change explicitly for reviewers.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 45.0/100 (high) · base `265f98b85763cf8a74bb299ea56caa30c2317764`

**PR risk assessment:** **BLOCK** — Risk band is high (score 45/100); treat as merge-blocked until required actions and validations are satisfied.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 1 pass · 2 missing · 1 fail · 2 not evaluated

**Top risk drivers:**
- Large diff (12 pts): total LOC churn=504 (threshold 400)
- Database migrations present (22 pts): 2 migration file(s)
_…and 3 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Validate migrations with rollback/reversal plan documented
_…and 4 more in `pr_risk.md`_

**Review routing:**
- Include frontend review for web/ UI and client behavior.
- Include database/migrations review before merge.
_…and 2 more in `pr_risk.md`_

**Score math:** factors 49.0 − reducers 4.0 → 45.0 · high

_Full checklist and analysis in artifact `pr_risk.md`._

```
