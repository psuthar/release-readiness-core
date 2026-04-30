# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:33Z  
**Base ref:** `e1ed5c481a047e1c5b7c830966c187e91bfd12c0`  

> Medium risk (score 20). Some risk factors are present but are manageable. Review the factors below before merging. A risk floor raised the score from 18 to 20 so trust-critical signals are not masked by reducers.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **20.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **55** / 100 |
| Files changed | 4 |
| LOC churn (add+del) | 746 |
| Test files in diff | 0 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 20/100); merge only after completing checklist items and review. |
| Evidence | 1 pass · 0 missing · 1 fail · 1 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Focus primary review on `scripts/run_qa_eval.py` (majority of churn).
- Confirm scope with author: PR text implies domains api, auth, rag but diff may differ.

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
- process: PR description with scoped, evidence-backed review plan

### Evidence status (repo-local signals)

> ✅ 1 pass · ⚠️ 0 missing · ❌ 1 fail · 📋 1 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |
| `pr_review_summary` | ✅ pass | intent | PR title/body has strong keywords aligned with the diff. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **18.0** |
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **18.0** |
| Floor minimum (when rules apply) | **20** |
| Floor applied | **yes** |
| Floor reasons | Large diff cannot score in the low band (floor applies) |
| **Final score** | **20.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — No test files in diff; proximity of tests to changed code cannot be established from this diff alone.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **4** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `focused` — Most churn (~73%) sits under `scripts/run_qa_eval.py`.
- Top area: `scripts/run_qa_eval.py` (~73% of churn); **4** distinct path prefixes.

### Hotspots (recent git activity)

_No overlapping hotspot prefixes detected (or git history unavailable)._

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-134: Q&A eval runner (SessionAsk) + artifact logging
- **Keywords matched:** session, ask
- **Domains implied by text:** auth, api, rag
- **Domains in diff (non-test):** other, scripts
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| other | 2 |
| scripts | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 18.0 |  |
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

### Large diff (`diff_large`)

- **Points:** 12.0
- **Detail:** total LOC churn=746 (threshold 400)

### PR title/body keywords do not align with paths in the diff (`context_intent_mismatch`)

- **Points:** 6.0
- **Detail:** Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.


## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

### [ medium ] Align PR title/description with the diff

- Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent.
- If the scope is intentional, explain why expected domains are not touched.

### [ supporting ] Make PR review scoped and evidence-backed

- Add a PR description summary: what changed and why.
- Group changes by subsystem so reviewers can validate quickly.

## Mitigations

### `diff_large`

- Review commit-by-commit; consider feature flags for risky paths.

### `context_intent_mismatch`

- Update the PR title/body to match the diff, or adjust the diff to match the stated intent.
- If intentional, explain the scope change explicitly for reviewers.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 20.0/100 (medium) · base `e1ed5c481a047e1c5b7c830966c187e91bfd12c0`

**PR risk assessment:** **WARN** — Risk band is medium (score 20/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 1 pass · 0 missing · 1 fail · 1 not evaluated

**Top risk drivers:**
- Large diff (12 pts): total LOC churn=746 (threshold 400)
- PR title/body keywords do not align with paths in the diff (6 pts): Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

**Top required validations:**
1. Required status checks must pass before merge
2. Align PR title and body with the actual diff (intent match)
_…and 1 more in `pr_risk.md`_

**Review routing:**
- Focus primary review on `scripts/run_qa_eval.py` (majority of churn).
- Confirm scope with author: PR text implies domains api, auth, rag but diff may differ.

**Score math:** factors 18.0 − reducers 0.0 → 20.0 (floor 20 applied) · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
