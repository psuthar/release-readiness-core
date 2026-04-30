# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:05Z  
**Base ref:** `8b308170c7dc095f0bbe6867f074ad864c68d47a`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **6.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **85** / 100 |
| Files changed | 1 |
| LOC churn (add+del) | 29 |
| Test files in diff | 0 |
| Config-ish files (CI/deploy/mod) | 0 |
| Validation note | yes (Validation:) |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **PASS (low risk)** |
| Rationale | PR risk is low (score 6/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging. |
| Evidence | 0 pass · 0 missing · 1 fail · 1 not evaluated |

### Recommended review strategy

Single-pass review is enough; spot-check touched paths if helpful.

### Review routing (recommended)

- Focus primary review on `scripts/run-e2e-local.sh` (majority of churn).
- Confirm scope with author: PR text implies domains web but diff may differ.

### Blocking / elevated review reasons

_None._

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- process: PR title/body aligned with actual diff (intent match)
- process: validation note present in commit — confirm it matches what was run

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 0 missing · ❌ 1 fail · 📋 1 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **6.0** |
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **6.0** |
| Floor rules | _none_ |
| **Final score** | **6.0** |
| **Final band** | **low** |

## Context insights

### Test–code proximity

- **Structural alignment:** `n_a` — Diff contains only config/tooling files (YAML, shell, docs…); test proximity is not applicable.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **0** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `focused` — Most churn (~100%) sits under `scripts/run-e2e-local.sh`.
- Top area: `scripts/run-e2e-local.sh` (~100% of churn); **1** distinct path prefixes.

### Hotspots (recent git activity)

_No overlapping hotspot prefixes detected (or git history unavailable)._

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-224: source repo-root .env in run-e2e-local.sh and improve admin pre-flight error
- **Keywords matched:** e2e
- **Domains implied by text:** web
- **Domains in diff (non-test):** scripts
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| scripts | 1 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 6.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 15.0 | 85 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| No sensitive domains changed | +35 |

**Final confidence score: 85 / 100**

## Risk factors

### PR title/body keywords do not align with paths in the diff (`context_intent_mismatch`)

- **Points:** 6.0
- **Detail:** Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.


## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

### [ medium ] Align PR title/description with the diff

- Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent.
- If the scope is intentional, explain why expected domains are not touched.

## Mitigations

### `context_intent_mismatch`

- Update the PR title/body to match the diff, or adjust the diff to match the stated intent.
- If intentional, explain the scope change explicitly for reviewers.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 6.0/100 (low) · base `8b308170c7dc095f0bbe6867f074ad864c68d47a`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 6/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 1 fail · 1 not evaluated

**Top risk drivers:**
- PR title/body keywords do not align with paths in the diff (6 pts): Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

**Top required validations:**
1. Required status checks must pass before merge
2. Align PR title and body with the actual diff (intent match)
_…and 1 more in `pr_risk.md`_

**Review routing:**
- Focus primary review on `scripts/run-e2e-local.sh` (majority of churn).
- Confirm scope with author: PR text implies domains web but diff may differ.

**Score math:** factors 6.0 − reducers 0.0 → 6.0 · low

_Full checklist and analysis in artifact `pr_risk.md`._

```
