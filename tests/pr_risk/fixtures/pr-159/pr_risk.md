# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:34Z  
**Base ref:** `8c087b8fd6a9ea6772316a015a96b83d6515bd3d`  

> Medium risk (score 29). Some risk factors are present but are manageable. Review the factors below before merging.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **29.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **55** / 100 |
| Files changed | 15 |
| LOC churn (add+del) | 701 |
| Test files in diff | 5 |
| Config-ish files (CI/deploy/mod) | 3 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 29/100); merge only after completing checklist items and review. |
| Evidence | 0 pass · 1 missing · 0 fail · 3 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include CI/infra review for workflow or deploy config changes.

### Blocking / elevated review reasons

- Elevated review: risk band "medium" — complete listed validations before merge.

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required validations are distinct from mitigations: validations are merge gates; mitigations are factor-specific guidance.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- config: workflow / deploy / go.mod changes validated against required checks
- test: tests co-located or explicitly linked for changed code
- process: PR description with scoped, evidence-backed review plan

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 1 missing · ❌ 0 fail · 📋 3 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `workflow_config_validation` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note in commit; CI result not confirmable from repo-local signals — requires human review. |
| `context_improve_test_proximity` | ⚠️ missing | proximity | Structural alignment is "distant" with no test coverage evidence for this diff. |
| `pr_review_summary` | 📋 not evaluated (requires CI/reviewer confirmation) | intent | PR description quality could not be confirmed from available signals — requires human review. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **29.0** |
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **29.0** |
| Floor minimum (when rules apply) | **20** |
| Floor applied | **no** |
| Floor reasons | CI workflow changes cannot score in the low band (floor applies); Large diff cannot score in the low band (floor applies) |
| **Final score** | **29.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — Many changed production files have no test file in the same directory or an obvious sibling path in this diff.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **10** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `balanced` — Churn is spread across several areas in a typical way.
- Top area: `eval/qa` (~56% of churn); **12** distinct path prefixes.

### Hotspots (recent git activity)

_No overlapping hotspot prefixes detected (or git history unavailable)._

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-139: Q&A fixture-fact inventory and validation tests
- **Domains in diff (non-test):** api, other, scripts, workflows
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| api | 1 |
| other | 2 |
| scripts | 4 |
| tests | 5 |
| workflows | 3 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 17.0 |  |
| Workflow / deployment changes | 12.0 |  |
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
- **Detail:** total LOC churn=701 (threshold 400)

### CI/GitHub Actions workflows changed (`ci_workflows`)

- **Points:** 12.0
- **Detail:** 3 workflow file(s)

### Tests not co-located with changed code in this diff (`context_test_proximity_distant`)

- **Points:** 5.0
- **Detail:** Many changed production files have no test file in the same directory or an obvious sibling path in this diff.


## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

### [ medium ] Validate workflow / deploy config changes

- Confirm required checks and env parity before merge.
- If CI fails, identify whether it is test flakiness vs behavior change and update evidence accordingly.

### [ supporting ] Improve test proximity for changed code

- Add or reference tests in the same package or directory as changed production files.
- If tests live elsewhere, link them in the PR description.

### [ supporting ] Make PR review scoped and evidence-backed

- Add a PR description summary: what changed and why.
- Group changes by subsystem so reviewers can validate quickly.

## Mitigations

### `diff_large`

- Review commit-by-commit; consider feature flags for risky paths.

### `ci_workflows`

- Validate workflow YAML in a fork or `act` where possible.
- Confirm secrets and required checks still match branch protection.

### `context_test_proximity_distant`

- Add tests next to changed packages or link existing tests in the PR description.
- Prefer package-local *_test.go over only end-to-end coverage for the same change.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 29.0/100 (medium) · base `8c087b8fd6a9ea6772316a015a96b83d6515bd3d`

**PR risk assessment:** **WARN** — Risk band is medium (score 29/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 1 missing · 0 fail · 3 not evaluated

**Top risk drivers:**
- Large diff (12 pts): total LOC churn=701 (threshold 400)
- CI/GitHub Actions workflows changed (12 pts): 3 workflow file(s)
_…and 1 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Validate workflow, deploy, or go.mod changes against required checks
_…and 2 more in `pr_risk.md`_

**Review routing:**
- Include CI/infra review for workflow or deploy config changes.

**Score math:** factors 29.0 − reducers 0.0 → 29.0 · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
