# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:12Z  
**Base ref:** `83bd86d986ebfd5577a46b353d876d108fae9985`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **7.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **60** / 100 |
| Files changed | 5 |
| LOC churn (add+del) | 319 |
| Test files in diff | 1 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **PASS (low risk)** |
| Rationale | PR risk is low (score 7/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging. |
| Evidence | 0 pass · 1 missing · 1 fail · 1 not evaluated |

### Recommended review strategy

Single-pass review is enough; spot-check touched paths if helpful.

### Review routing (recommended)

- Focus primary review on `internal/handlers` (majority of churn).
- Confirm scope with author: PR text implies domains workflows but diff may differ.

### Blocking / elevated review reasons

_None._

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- process: PR title/body aligned with actual diff (intent match)
- test: tests co-located or explicitly linked for changed code

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 1 missing · ❌ 1 fail · 📋 1 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |
| `context_improve_test_proximity` | ⚠️ missing | proximity | Structural alignment is "distant" with no test coverage evidence for this diff. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **11.0** |
| Reducers subtotal (points subtracted) | **4.0** |
| Net before floor | **7.0** |
| Floor rules | _none_ |
| **Final score** | **7.0** |
| **Final band** | **low** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — Many changed production files have no test file in the same directory or an obvious sibling path in this diff.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **4** with nearby test in diff: **1** (ratio **25%**)

### Change concentration

- **Mode:** `focused` — Most churn (~84%) sits under `internal/handlers`.
- Top area: `internal/handlers` (~84% of churn); **3** distinct path prefixes.

### Hotspots (recent git activity)

_No overlapping hotspot prefixes detected (or git history unavailable)._

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-203: expose Decision Maker readiness in stance responses
- **Keywords matched:** ci
- **Domains implied by text:** workflows
- **Domains in diff (non-test):** api, database
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| api | 2 |
| database | 2 |
| tests | 1 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 11.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 40.0 | 60 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| No sensitive domains changed | +35 |
| Tests structurally distant from changed code | -15 |
| Behavioral coverage depth unknown | -5 |
| Few changed files have nearby tests in diff | -5 |

**Final confidence score: 60 / 100**

## Risk factors

### Tests not co-located with changed code in this diff (`context_test_proximity_distant`)

- **Points:** 5.0
- **Detail:** Many changed production files have no test file in the same directory or an obvious sibling path in this diff.

### PR title/body keywords do not align with paths in the diff (`context_intent_mismatch`)

- **Points:** 6.0
- **Detail:** Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.


## Reducers (what lowers risk)

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 77% of LOC churn is in test files


## Required actions before merge

### [ medium ] Align PR title/description with the diff

- Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent.
- If the scope is intentional, explain why expected domains are not touched.

### [ supporting ] Improve test proximity for changed code

- Add or reference tests in the same package or directory as changed production files.
- If tests live elsewhere, link them in the PR description.

## Mitigations

### `context_test_proximity_distant`

- Add tests next to changed packages or link existing tests in the PR description.
- Prefer package-local *_test.go over only end-to-end coverage for the same change.

### `context_intent_mismatch`

- Update the PR title/body to match the diff, or adjust the diff to match the stated intent.
- If intentional, explain the scope change explicitly for reviewers.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 7.0/100 (low) · base `83bd86d986ebfd5577a46b353d876d108fae9985`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 7/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 1 missing · 1 fail · 1 not evaluated

**Top risk drivers:**
- Tests not co-located with changed code in this diff (5 pts): Many changed production files have no test file in the same directory or an obvious sibling path in this diff.
- PR title/body keywords do not align with paths in the diff (6 pts): Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

**Top required validations:**
1. Required status checks must pass before merge
2. Align PR title and body with the actual diff (intent match)
_…and 1 more in `pr_risk.md`_

**Review routing:**
- Focus primary review on `internal/handlers` (majority of churn).
- Confirm scope with author: PR text implies domains workflows but diff may differ.

**Score math:** factors 11.0 − reducers 4.0 → 7.0 · low

_Full checklist and analysis in artifact `pr_risk.md`._

```
