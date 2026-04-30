# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:30Z  
**Base ref:** `0b0e1174e7531ce42c559e04cc68a830c984d10e`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **0.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **55** / 100 |
| Files changed | 2 |
| LOC churn (add+del) | 153 |
| Test files in diff | 0 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **PASS (low risk)** |
| Rationale | PR risk is low (score 0/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging. |
| Evidence | 0 pass · 0 missing · 0 fail · 1 not evaluated |

### Recommended review strategy

Single-pass review is enough; spot-check touched paths if helpful.

### Review routing (recommended)

- Focus primary review on `scripts/run_qa_eval.py` (majority of churn).

### Blocking / elevated review reasons

_None._

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.

### Required validations before merge

- ci: required status checks must pass before merge

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 0 missing · ❌ 0 fail · 📋 1 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **0.0** |
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **0.0** |
| Floor rules | _none_ |
| **Final score** | **0.0** |
| **Final band** | **low** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — No test files in diff; proximity of tests to changed code cannot be established from this diff alone.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **2** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `focused` — Most churn (~59%) sits under `scripts/run_qa_eval.py`.
- Top area: `scripts/run_qa_eval.py` (~59% of churn); **2** distinct path prefixes.

### Hotspots (recent git activity)

_No overlapping hotspot prefixes detected (or git history unavailable)._

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-140: apply expected-score thresholds and weighted reporting
- **Domains in diff (non-test):** scripts
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| scripts | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 0.0 |  |
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

_No factors triggered._

## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

_No required actions for this risk profile. Review mitigations if helpful._
## Mitigations

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 0.0/100 (low) · base `0b0e1174e7531ce42c559e04cc68a830c984d10e`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 0/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 0 fail · 1 not evaluated

**Top required validations:**
1. Required status checks must pass before merge

**Review routing:**
- Focus primary review on `scripts/run_qa_eval.py` (majority of churn).

_Full checklist and analysis in artifact `pr_risk.md`._

```
