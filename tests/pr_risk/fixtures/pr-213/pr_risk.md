# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:07Z  
**Base ref:** `64645d8088d6c0e575928e768ba5a569aeb0530c`  

> Medium risk (score 20). Some risk factors are present but are manageable. Review the factors below before merging. A risk floor raised the score from 12 to 20 so trust-critical signals are not masked by reducers.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **20.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **85** / 100 |
| Files changed | 1 |
| LOC churn (add+del) | 32 |
| Test files in diff | 0 |
| Config-ish files (CI/deploy/mod) | 1 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 20/100); merge only after completing checklist items and review. |
| Evidence | 0 pass · 0 missing · 0 fail · 2 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include CI/infra review for workflow or deploy config changes.
- Focus primary review on `.github/workflows` (majority of churn).

### Blocking / elevated review reasons

- Elevated review: risk band "medium" — complete listed validations before merge.
- Risk floor applied so trust-critical changes are not masked by reducers.

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required validations are distinct from mitigations: validations are merge gates; mitigations are factor-specific guidance.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- config: workflow / deploy / go.mod changes validated against required checks

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 0 missing · ❌ 0 fail · 📋 2 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `workflow_config_validation` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note in commit; CI result not confirmable from repo-local signals — requires human review. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **12.0** |
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **12.0** |
| Floor minimum (when rules apply) | **20** |
| Floor applied | **yes** |
| Floor reasons | CI workflow changes cannot score in the low band (floor applies) |
| **Final score** | **20.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `n_a` — Diff contains only config/tooling files (YAML, shell, docs…); test proximity is not applicable.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **0** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `focused` — Most churn (~100%) sits under `.github/workflows`.
- Top area: `.github/workflows` (~100% of churn); **1** distinct path prefixes.

### Hotspots (recent git activity)

_No overlapping hotspot prefixes detected (or git history unavailable)._

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-219: start unoconv listener in CI to speed PPTX conversions
- **Keywords matched:** ci
- **Domains implied by text:** workflows
- **Domains in diff (non-test):** workflows
- **Aligned:** yes — Keywords in the title/body align with domains touched in the diff.

## Domain hits

| Domain | Files |
|--------|-------|
| workflows | 1 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 0.0 |  |
| Workflow / deployment changes | 12.0 |  |
| Test confidence | 15.0 | 85 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| No sensitive domains changed | +35 |

**Final confidence score: 85 / 100**

## Risk factors

### CI/GitHub Actions workflows changed (`ci_workflows`)

- **Points:** 12.0
- **Detail:** 1 workflow file(s)


## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

### [ medium ] Validate workflow / deploy config changes

- Confirm required checks and env parity before merge.
- If CI fails, identify whether it is test flakiness vs behavior change and update evidence accordingly.

## Mitigations

### `ci_workflows`

- Validate workflow YAML in a fork or `act` where possible.
- Confirm secrets and required checks still match branch protection.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 20.0/100 (medium) · base `64645d8088d6c0e575928e768ba5a569aeb0530c`

**PR risk assessment:** **WARN** — Risk band is medium (score 20/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 0 fail · 2 not evaluated

**Top risk drivers:**
- CI/GitHub Actions workflows changed (12 pts): 1 workflow file(s)

**Top required validations:**
1. Required status checks must pass before merge
2. Validate workflow, deploy, or go.mod changes against required checks

**Review routing:**
- Include CI/infra review for workflow or deploy config changes.
- Focus primary review on `.github/workflows` (majority of churn).

**Score math:** factors 12.0 − reducers 0.0 → 20.0 (floor 20 applied) · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
