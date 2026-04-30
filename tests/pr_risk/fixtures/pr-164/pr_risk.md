# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:31Z  
**Base ref:** `9a9cf74654bd64e7228524ab0834dc8f4ba0c4fe`  

> Medium risk (score 20). Some risk factors are present but are manageable. Review the factors below before merging. A risk floor raised the score from 12 to 20 so trust-critical signals are not masked by reducers.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **20.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **55** / 100 |
| Files changed | 4 |
| LOC churn (add+del) | 602 |
| Test files in diff | 0 |
| Config-ish files (CI/deploy/mod) | 0 |

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

- Assign reviewers using changed paths and domain hits; use CODEOWNERS if configured.

### Blocking / elevated review reasons

- Elevated review: risk band "medium" — complete listed validations before merge.
- Risk floor applied so trust-critical changes are not masked by reducers.

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required validations are distinct from mitigations: validations are merge gates; mitigations are factor-specific guidance.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- process: PR description with scoped, evidence-backed review plan

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 0 missing · ❌ 0 fail · 📋 2 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `pr_review_summary` | 📋 not evaluated (requires CI/reviewer confirmation) | intent | PR description quality could not be confirmed from available signals — requires human review. |

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
| Floor reasons | Large diff cannot score in the low band (floor applies) |
| **Final score** | **20.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — No test files in diff; proximity of tests to changed code cannot be established from this diff alone.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **4** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `balanced` — Churn is spread across several areas in a typical way.
- Top area: `scripts/qa_eval_judge.py` (~44% of churn); **4** distinct path prefixes.

### Hotspots (recent git activity)

_No overlapping hotspot prefixes detected (or git history unavailable)._

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-136: strict JSON LLM judge for eval scoring
- **Domains in diff (non-test):** scripts
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| scripts | 4 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 12.0 |  |
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
- **Detail:** total LOC churn=602 (threshold 400)


## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

### [ supporting ] Make PR review scoped and evidence-backed

- Add a PR description summary: what changed and why.
- Group changes by subsystem so reviewers can validate quickly.

## Mitigations

### `diff_large`

- Review commit-by-commit; consider feature flags for risky paths.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 20.0/100 (medium) · base `9a9cf74654bd64e7228524ab0834dc8f4ba0c4fe`

**PR risk assessment:** **WARN** — Risk band is medium (score 20/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 0 fail · 2 not evaluated

**Top risk drivers:**
- Large diff (12 pts): total LOC churn=602 (threshold 400)

**Top required validations:**
1. Required status checks must pass before merge
2. Ensure PR includes a clear, scoped review plan

**Review routing:**
- Assign reviewers using changed paths and domain hits; use CODEOWNERS if configured.

**Score math:** factors 12.0 − reducers 0.0 → 20.0 (floor 20 applied) · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
