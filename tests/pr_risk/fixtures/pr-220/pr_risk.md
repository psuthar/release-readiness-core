# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:04Z  
**Base ref:** `929720f790ae705b5154b81e0ee5579135bb23bb`  

> Medium risk (score 37). Some risk factors are present but are manageable. Review the factors below before merging.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **37.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **60** / 100 |
| Files changed | 11 |
| LOC churn (add+del) | 302 |
| Test files in diff | 7 |
| Config-ish files (CI/deploy/mod) | 0 |
| Validation note | yes (Validation:) |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 37/100); merge only after completing checklist items and review. |
| Evidence | 1 pass · 0 missing · 1 fail · 1 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include a reviewer familiar with auth, sessions, and invitations.
- Include database/migrations review before merge.
- Extra reviewer attention on `web/tests` (several recent commits touched this area).
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
- process: validation note present in commit — confirm it matches what was run

### Evidence status (repo-local signals)

> ✅ 1 pass · ⚠️ 0 missing · ❌ 1 fail · 📋 1 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |
| `context_hotspot_regression_focus` | ✅ pass | git_signals | Validation note present in commit: Validation: |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **46.0** |
| Reducers subtotal (points subtracted) | **9.0** |
| Net before floor | **37.0** |
| Floor rules | _none_ |
| **Final score** | **37.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `partial` — Some production changes lack adjacent tests in the same diff; spot-check coverage.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **4** with nearby test in diff: **2** (ratio **50%**)

### Change concentration

- **Mode:** `balanced` — Churn is spread across several areas in a typical way.
- Top area: `internal/handlers` (~41% of churn); **4** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/tests`** — 26 distinct commits (sampled) — Prefix touched in 26 of the last 50 sampled commits — sustained activity; extra regression care.
- **`internal/handlers`** — 8 distinct commits (sampled) — Prefix touched in 8 of the last 50 sampled commits — sustained activity; extra regression care.
- **`internal/database`** — 6 distinct commits (sampled) — Prefix touched in 6 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-226: make session creator a first-class member (single source of truth)
- **Keywords matched:** session
- **Domains implied by text:** auth, api
- **Domains in diff (non-test):** auth, database, migrations
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| auth | 1 |
| database | 1 |
| migrations | 2 |
| tests | 7 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 46.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 40.0 | 60 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| Sensitive domains changed | -10 |
| E2E tests present in diff | +40 |
| Tests only partially aligned with changed code | -8 |
| Behavioral coverage depth unknown | -5 |
| Behavioral coverage depth unknown for sensitive domain changes | -5 |
| Some changed files lack nearby tests | -2 |

**Final confidence score: 60 / 100**

## Risk factors

### Auth/session/invite area changed (`domain_auth`)

- **Points:** 14.0
- **Detail:** 1 file(s) in auth-related paths

### Database migrations present (`domain_migrations`)

- **Points:** 22.0
- **Detail:** 2 migration file(s)

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 26 of the last 50 sampled commits — sustained activity; extra regression care.

### PR title/body keywords do not align with paths in the diff (`context_intent_mismatch`)

- **Points:** 6.0
- **Detail:** Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.


## Reducers (what lowers risk)

### `domain_auth_unit_evidence` (-5.0 points)

- Unit test evidence present
- Primarily affects: `test_confidence`
- Evidence: Found unit tests targeting the domain in the diff

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 60% of LOC churn is in test files


## Required actions before merge

### [ medium ] Align PR title/description with the diff

- Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent.
- If the scope is intentional, explain why expected domains are not touched.

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `web/tests` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

## Mitigations

### `domain_auth`

- Run auth/session flows manually or via E2E (login, invite, participant).
- Verify cookie/session settings in staging (SameSite, HTTPS).

### `domain_migrations`

- Run migrations against a copy of prod-like data; verify rollback plan.
- Coordinate deploy order (API before/after migration as required).

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

**Score:** 37.0/100 (medium) · base `929720f790ae705b5154b81e0ee5579135bb23bb`

**PR risk assessment:** **WARN** — Risk band is medium (score 37/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 1 pass · 0 missing · 1 fail · 1 not evaluated

**Top risk drivers:**
- Auth/session/invite area changed (14 pts): 1 file(s) in auth-related paths
- Database migrations present (22 pts): 2 migration file(s)
_…and 2 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Align PR title and body with the actual diff (intent match)
_…and 2 more in `pr_risk.md`_

**Review routing:**
- Include a reviewer familiar with auth, sessions, and invitations.
- Include database/migrations review before merge.
_…and 2 more in `pr_risk.md`_

**Score math:** factors 46.0 − reducers 9.0 → 37.0 · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
