# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:43Z  
**Base ref:** `816dbcb56a2a7ebc4d927658b13e89af3aae6c30`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **8.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **55** / 100 |
| Files changed | 1 |
| LOC churn (add+del) | 2 |
| Test files in diff | 0 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **PASS (low risk)** |
| Rationale | PR risk is low (score 8/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging. |
| Evidence | 1 pass · 0 missing · 1 fail · 2 not evaluated |

### Recommended review strategy

Single-pass review is enough; spot-check touched paths if helpful.

### Review routing (recommended)

- Include frontend review for web/ UI and client behavior.
- Focus primary review on `web/src` (majority of churn).
- Extra reviewer attention on `web/src` (several recent commits touched this area).
- Confirm scope with author: PR text implies domains api, auth but diff may differ.

### Blocking / elevated review reasons

_None._

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- test: tests or recorded evidence for sensitive paths
- process: PR title/body aligned with actual diff (intent match)
- test: targeted regression for path prefixes with several recent commits overlapping this diff

### Evidence status (repo-local signals)

> ✅ 1 pass · ⚠️ 0 missing · ❌ 1 fail · 📋 2 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `add_tests_or_evidence` | ✅ pass | git_signals | Style-only commit note present: purely cosmetic frontend change, no test required. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |
| `context_hotspot_regression_focus` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note detected; targeted regression coverage cannot be confirmed from diff alone — requires human review. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **28.0** |
| Reducers subtotal (points subtracted) | **20.0** |
| Net before floor | **8.0** |
| Floor rules | _none_ |
| **Final score** | **8.0** |
| **Final band** | **low** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — No test files in diff; proximity of tests to changed code cannot be established from this diff alone.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **1** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `focused` — Most churn (~100%) sits under `web/src`.
- Top area: `web/src` (~100% of churn); **1** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/src`** — 11 distinct commits (sampled) — Prefix touched in 11 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-116: Change "Show All Sessions" button color from red to primary blue
- **Keywords matched:** session
- **Domains implied by text:** auth, api
- **Domains in diff (non-test):** web
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| web | 1 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 10.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 45.0 | 55 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| No sensitive domains changed | +35 |
| Tests structurally distant from changed code | -15 |
| Behavioral coverage depth unknown | -5 |
| No changed files have nearby tests in diff | -10 |

**Final confidence score: 55 / 100**

## Risk factors

### Sensitive areas changed without test file changes in this diff (`tests_missing`)

- **Points:** 18.0
- **Detail:** no *_test.go / web test paths in diff; consider adding or updating tests

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 11 of the last 50 sampled commits — sustained activity; extra regression care.

### PR title/body keywords do not align with paths in the diff (`context_intent_mismatch`)

- **Points:** 6.0
- **Detail:** Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.


## Reducers (what lowers risk)

### `style_only_note` (-20.0 points)

- Style-only frontend change (commit note)
- Primarily affects: `test_confidence`
- Evidence: Style-only: replace destructive red (#f44336) with primary blue (#1976D2) on ...


## Required actions before merge

### [ high ] Add/update tests before merge

- Add or update tests for changed code paths and confirm `go test ./...` passes.

### [ medium ] Align PR title/description with the diff

- Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent.
- If the scope is intentional, explain why expected domains are not touched.

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `web/src` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

## Mitigations

### `tests_missing`

- Add or update unit/integration tests for changed packages.
- If behavior is unchanged refactor-only, note that in the PR description.

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

**Score:** 8.0/100 (low) · base `816dbcb56a2a7ebc4d927658b13e89af3aae6c30`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 8/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 1 pass · 0 missing · 1 fail · 2 not evaluated

**Top risk drivers:**
- Sensitive areas changed without test file changes in this diff (18 pts): no *_test.go / web test paths in diff; consider adding or updating tests
- Diff overlaps a path prefix touched in multiple recent commits (4 pts): Prefix touched in 11 of the last 50 sampled commits — sustained activity; extra regression care.
_…and 1 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Add tests or recorded evidence for sensitive paths
_…and 2 more in `pr_risk.md`_

**Review routing:**
- Include frontend review for web/ UI and client behavior.
- Focus primary review on `web/src` (majority of churn).
_…and 2 more in `pr_risk.md`_

**Score math:** factors 28.0 − reducers 20.0 → 8.0 · low

_Full checklist and analysis in artifact `pr_risk.md`._

```
