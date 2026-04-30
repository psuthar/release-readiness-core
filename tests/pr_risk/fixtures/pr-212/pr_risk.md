# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:07Z  
**Base ref:** `0333a4a7538a9f64b947de726e8675fd2de483ed`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **0.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **85** / 100 |
| Files changed | 1 |
| LOC churn (add+del) | 9 |
| Test files in diff | 1 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **PASS (low risk)** |
| Rationale | PR risk is low (score 0/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging. |
| Evidence | 0 pass · 0 missing · 0 fail · 2 not evaluated |

### Recommended review strategy

Single-pass review is enough; spot-check touched paths if helpful.

### Review routing (recommended)

- Focus primary review on `web/tests` (majority of churn).
- Extra reviewer attention on `web/tests` (several recent commits touched this area).

### Blocking / elevated review reasons

_None._

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- test: targeted regression for path prefixes with several recent commits overlapping this diff

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 0 missing · ❌ 0 fail · 📋 2 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_hotspot_regression_focus` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note detected; targeted regression coverage cannot be confirmed from diff alone — requires human review. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **4.0** |
| Reducers subtotal (points subtracted) | **6.0** |
| Net before floor | **0.0** |
| Floor rules | _none_ |
| **Final score** | **0.0** |
| **Final band** | **low** |

## Context insights

### Test–code proximity

- **Structural alignment:** `n_a` — only test files in diff
- **Behavioral coverage depth:** `unknown`
- Non-test files: **0** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `focused` — Most churn (~100%) sits under `web/tests`.
- Top area: `web/tests` (~100% of churn); **1** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/tests`** — 22 distinct commits (sampled) — Prefix touched in 22 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-218: bump material-viewers upload waitForResponse to 90s
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| tests | 1 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 0.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 15.0 | 85 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| No sensitive domains changed | +35 |

**Final confidence score: 85 / 100**

## Risk factors

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 22 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

### `test_only_diff` (-6.0 points)

- Test-only diff
- Primarily affects: `code`
- Evidence: All changed files are classified as tests


## Required actions before merge

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `web/tests` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

## Mitigations

### `context_hotspot_overlap`

- Run focused regression on the overlapping prefix; several recent commits touched it, so regressions are likelier.
- Scan related modules for unintended behavior changes.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 0.0/100 (low) · base `0333a4a7538a9f64b947de726e8675fd2de483ed`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 0/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 0 fail · 2 not evaluated

**Top risk drivers:**
- Diff overlaps a path prefix touched in multiple recent commits (4 pts): Prefix touched in 22 of the last 50 sampled commits — sustained activity; extra regression care.

**Top required validations:**
1. Required status checks must pass before merge
2. Run targeted regression for path prefixes with sustained recent commit activity

**Review routing:**
- Focus primary review on `web/tests` (majority of churn).
- Extra reviewer attention on `web/tests` (several recent commits touched this area).

**Score math:** factors 4.0 − reducers 6.0 → 0.0 · low

_Full checklist and analysis in artifact `pr_risk.md`._

```
