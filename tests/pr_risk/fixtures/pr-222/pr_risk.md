# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:03Z  
**Base ref:** `6fd391e03edd808eb401d00e324537d414275e7a`  

> Medium risk (score 33). Some risk factors are present but are manageable. Review the factors below before merging.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **33.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **33** / 100 |
| Files changed | 4 |
| LOC churn (add+del) | 178 |
| Test files in diff | 1 |
| Config-ish files (CI/deploy/mod) | 0 |
| Validation note | yes (Validation:) |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 33/100); merge only after completing checklist items and review. |
| Evidence | 1 pass · 1 missing · 1 fail · 1 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include database/migrations review before merge.
- Focus primary review on `internal/database` (majority of churn).
- Extra reviewer attention on `internal/database` (several recent commits touched this area).
- Confirm scope with author: PR text implies domains api, auth but diff may differ.

### Blocking / elevated review reasons

- Elevated review: risk band "medium" — complete listed validations before merge.
- Evidence FAIL [context_align_pr_description]: PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required validations are distinct from mitigations: validations are merge gates; mitigations are factor-specific guidance.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- process: PR title/body aligned with actual diff (intent match)
- test: targeted regression for path prefixes with several recent commits overlapping this diff
- test: tests co-located or explicitly linked for changed code
- process: validation note present in commit — confirm it matches what was run

### Evidence status (repo-local signals)

> ✅ 1 pass · ⚠️ 1 missing · ❌ 1 fail · 📋 1 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |
| `context_hotspot_regression_focus` | ✅ pass | git_signals | Validation note present in commit: Validation: |
| `context_improve_test_proximity` | ⚠️ missing | proximity | Structural alignment is "distant" with no test coverage evidence for this diff. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **37.0** |
| Reducers subtotal (points subtracted) | **4.0** |
| Net before floor | **33.0** |
| Floor rules | _none_ |
| **Final score** | **33.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — Many changed production files have no test file in the same directory or an obvious sibling path in this diff.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **3** with nearby test in diff: **1** (ratio **33%**)

### Change concentration

- **Mode:** `focused` — Most churn (~84%) sits under `internal/database`.
- Top area: `internal/database` (~84% of churn); **2** distinct path prefixes.

### Hotspots (recent git activity)

- **`internal/database`** — 7 distinct commits (sampled) — Prefix touched in 7 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-229: anonymise sessions.created_by on user-delete; backfill orphans
- **Keywords matched:** session
- **Domains implied by text:** auth, api
- **Domains in diff (non-test):** database, migrations
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| database | 1 |
| migrations | 2 |
| tests | 1 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 37.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 67.0 | 33 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| Sensitive domains changed | -10 |
| Unit tests present in diff | +20 |
| Tests structurally distant from changed code | -15 |
| Behavioral coverage depth unknown | -5 |
| Behavioral coverage depth unknown for sensitive domain changes | -5 |
| Some changed files lack nearby tests | -2 |

**Final confidence score: 33 / 100**

## Risk factors

### Database migrations present (`domain_migrations`)

- **Points:** 22.0
- **Detail:** 2 migration file(s)

### Tests not co-located with changed code in this diff (`context_test_proximity_distant`)

- **Points:** 5.0
- **Detail:** Many changed production files have no test file in the same directory or an obvious sibling path in this diff.

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 7 of the last 50 sampled commits — sustained activity; extra regression care.

### PR title/body keywords do not align with paths in the diff (`context_intent_mismatch`)

- **Points:** 6.0
- **Detail:** Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.


## Reducers (what lowers risk)

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 62% of LOC churn is in test files


## Required actions before merge

### [ medium ] Align PR title/description with the diff

- Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent.
- If the scope is intentional, explain why expected domains are not touched.

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `internal/database` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

### [ supporting ] Improve test proximity for changed code

- Add or reference tests in the same package or directory as changed production files.
- If tests live elsewhere, link them in the PR description.

## Mitigations

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

**Score:** 33.0/100 (medium) · base `6fd391e03edd808eb401d00e324537d414275e7a`

**PR risk assessment:** **WARN** — Risk band is medium (score 33/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 1 pass · 1 missing · 1 fail · 1 not evaluated

**Top risk drivers:**
- Database migrations present (22 pts): 2 migration file(s)
- Tests not co-located with changed code in this diff (5 pts): Many changed production files have no test file in the same directory or an obvious sibling path in this diff.
_…and 2 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Align PR title and body with the actual diff (intent match)
_…and 3 more in `pr_risk.md`_

**Review routing:**
- Include database/migrations review before merge.
- Focus primary review on `internal/database` (majority of churn).
_…and 2 more in `pr_risk.md`_

**Score math:** factors 37.0 − reducers 4.0 → 33.0 · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
