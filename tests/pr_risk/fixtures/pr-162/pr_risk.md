# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:32Z  
**Base ref:** `d315d05e4b451b1293e1dda136c80e6d2466878f`  

> Medium risk (score 20). Some risk factors are present but are manageable. Review the factors below before merging. A risk floor raised the score from 16 to 20 so trust-critical signals are not masked by reducers.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **20.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **55** / 100 |
| Files changed | 7 |
| LOC churn (add+del) | 284 |
| Test files in diff | 0 |
| Config-ish files (CI/deploy/mod) | 1 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 20/100); merge only after completing checklist items and review. |
| Evidence | 0 pass · 0 missing · 0 fail · 3 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include CI/infra review for workflow or deploy config changes.
- Extra reviewer attention on `.github/workflows` (several recent commits touched this area).

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
- test: targeted regression for path prefixes with several recent commits overlapping this diff

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 0 missing · ❌ 0 fail · 📋 3 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `workflow_config_validation` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note in commit; CI result not confirmable from repo-local signals — requires human review. |
| `context_hotspot_regression_focus` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note detected; targeted regression coverage cannot be confirmed from diff alone — requires human review. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **16.0** |
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **16.0** |
| Floor minimum (when rules apply) | **20** |
| Floor applied | **yes** |
| Floor reasons | CI workflow changes cannot score in the low band (floor applies) |
| **Final score** | **20.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — No test files in diff; proximity of tests to changed code cannot be established from this diff alone.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **7** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `balanced` — Churn is spread across several areas in a typical way.
- Top area: `eval/qa` (~51% of churn); **6** distinct path prefixes.

### Hotspots (recent git activity)

- **`.github/workflows`** — 5 distinct commits (sampled) — Prefix touched in 5 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-137: Q&A eval harness docs + FULL_AUTO gate polling policy
- **Domains in diff (non-test):** other, scripts, workflows
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| other | 5 |
| scripts | 1 |
| workflows | 1 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 4.0 |  |
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

### CI/GitHub Actions workflows changed (`ci_workflows`)

- **Points:** 12.0
- **Detail:** 1 workflow file(s)

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 5 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

### [ medium ] Validate workflow / deploy config changes

- Confirm required checks and env parity before merge.
- If CI fails, identify whether it is test flakiness vs behavior change and update evidence accordingly.

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `.github/workflows` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

## Mitigations

### `ci_workflows`

- Validate workflow YAML in a fork or `act` where possible.
- Confirm secrets and required checks still match branch protection.

### `context_hotspot_overlap`

- Run focused regression on the overlapping prefix; several recent commits touched it, so regressions are likelier.
- Scan related modules for unintended behavior changes.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 20.0/100 (medium) · base `d315d05e4b451b1293e1dda136c80e6d2466878f`

**PR risk assessment:** **WARN** — Risk band is medium (score 20/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 0 fail · 3 not evaluated

**Top risk drivers:**
- CI/GitHub Actions workflows changed (12 pts): 1 workflow file(s)
- Diff overlaps a path prefix touched in multiple recent commits (4 pts): Prefix touched in 5 of the last 50 sampled commits — sustained activity; extra regression care.

**Top required validations:**
1. Required status checks must pass before merge
2. Validate workflow, deploy, or go.mod changes against required checks
_…and 1 more in `pr_risk.md`_

**Review routing:**
- Include CI/infra review for workflow or deploy config changes.
- Extra reviewer attention on `.github/workflows` (several recent commits touched this area).

**Score math:** factors 16.0 − reducers 0.0 → 20.0 (floor 20 applied) · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
