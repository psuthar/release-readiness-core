# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:06Z  
**Base ref:** `469664ea0806dfc6f03b0517835fe24f0e382d49`  

> Medium risk (score 20). Some risk factors are present but are manageable. Review the factors below before merging. A risk floor raised the score from 18 to 20 so trust-critical signals are not masked by reducers.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **20.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **82** / 100 |
| Files changed | 5 |
| LOC churn (add+del) | 403 |
| Test files in diff | 2 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 20/100); merge only after completing checklist items and review. |
| Evidence | 1 pass · 0 missing · 1 fail · 2 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Focus primary review on `internal/database` (majority of churn).
- Extra reviewer attention on `internal/handlers` (several recent commits touched this area).
- Confirm scope with author: PR text implies domains api, auth but diff may differ.

### Blocking / elevated review reasons

- Elevated review: risk band "medium" — complete listed validations before merge.
- Risk floor applied so trust-critical changes are not masked by reducers.
- Evidence FAIL [context_align_pr_description]: PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required validations are distinct from mitigations: validations are merge gates; mitigations are factor-specific guidance.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- process: PR title/body aligned with actual diff (intent match)
- test: targeted regression for path prefixes with several recent commits overlapping this diff
- process: PR description with scoped, evidence-backed review plan

### Evidence status (repo-local signals)

> ✅ 1 pass · ⚠️ 0 missing · ❌ 1 fail · 📋 2 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |
| `context_hotspot_regression_focus` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note detected; targeted regression coverage cannot be confirmed from diff alone — requires human review. |
| `pr_review_summary` | ✅ pass | intent | PR title/body has strong keywords aligned with the diff. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **22.0** |
| Reducers subtotal (points subtracted) | **4.0** |
| Net before floor | **18.0** |
| Floor minimum (when rules apply) | **20** |
| Floor applied | **yes** |
| Floor reasons | Large diff cannot score in the low band (floor applies) |
| **Final score** | **20.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `co_located` — Tests in this diff are mostly next to or under the same directories as changed production files. Behavioral depth: unit-level overlap with sensitive domains but no matching E2E evidence in this diff — consider deeper tests where applicable.
- **Behavioral coverage depth:** `shallow`
- Non-test files: **3** with nearby test in diff: **3** (ratio **100%**)

### Change concentration

- **Mode:** `focused` — Most churn (~74%) sits under `internal/database`.
- Top area: `internal/database` (~74% of churn); **2** distinct path prefixes.

### Hotspots (recent git activity)

- **`internal/handlers`** — 6 distinct commits (sampled) — Prefix touched in 6 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-221: extend GET /api/sessions with member_count and created_by_display_name
- **Keywords matched:** session
- **Domains implied by text:** auth, api
- **Domains in diff (non-test):** database
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| database | 3 |
| tests | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 22.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 18.0 | 82 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| No sensitive domains changed | +35 |
| Behavioral coverage depth is shallow | -3 |

**Final confidence score: 82 / 100**

## Risk factors

### Large diff (`diff_large`)

- **Points:** 12.0
- **Detail:** total LOC churn=403 (threshold 400)

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 6 of the last 50 sampled commits — sustained activity; extra regression care.

### PR title/body keywords do not align with paths in the diff (`context_intent_mismatch`)

- **Points:** 6.0
- **Detail:** Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.


## Reducers (what lowers risk)

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 70% of LOC churn is in test files


## Required actions before merge

### [ medium ] Align PR title/description with the diff

- Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent.
- If the scope is intentional, explain why expected domains are not touched.

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `internal/handlers` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

### [ supporting ] Make PR review scoped and evidence-backed

- Add a PR description summary: what changed and why.
- Group changes by subsystem so reviewers can validate quickly.

## Mitigations

### `diff_large`

- Review commit-by-commit; consider feature flags for risky paths.

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

**Score:** 20.0/100 (medium) · base `469664ea0806dfc6f03b0517835fe24f0e382d49`

**PR risk assessment:** **WARN** — Risk band is medium (score 20/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 1 pass · 0 missing · 1 fail · 2 not evaluated

**Top risk drivers:**
- Large diff (12 pts): total LOC churn=403 (threshold 400)
- Diff overlaps a path prefix touched in multiple recent commits (4 pts): Prefix touched in 6 of the last 50 sampled commits — sustained activity; extra regression care.
_…and 1 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Align PR title and body with the actual diff (intent match)
_…and 2 more in `pr_risk.md`_

**Review routing:**
- Focus primary review on `internal/database` (majority of churn).
- Extra reviewer attention on `internal/handlers` (several recent commits touched this area).
_…and 1 more in `pr_risk.md`_

**Score math:** factors 22.0 − reducers 4.0 → 20.0 (floor 20 applied) · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
