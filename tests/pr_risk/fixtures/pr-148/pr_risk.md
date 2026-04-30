# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:39Z  
**Base ref:** `206c55b68c117347a659e65c5f4265c19a1867a6`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **0.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **55** / 100 |
| Files changed | 2 |
| LOC churn (add+del) | 215 |
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

- Include frontend review for web/ UI and client behavior.
- Focus primary review on `web/src` (majority of churn).
- Extra reviewer attention on `web/src` (several recent commits touched this area).

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
| Reducers subtotal (points subtracted) | **4.0** |
| Net before floor | **0.0** |
| Floor rules | _none_ |
| **Final score** | **0.0** |
| **Final band** | **low** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — Many changed production files have no test file in the same directory or an obvious sibling path in this diff.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **1** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `focused` — Most churn (~100%) sits under `web/src`.
- Top area: `web/src` (~100% of churn); **1** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/src`** — 18 distinct commits (sampled) — Prefix touched in 18 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-122: hide empty sections in materials tree panel
- **Domains in diff (non-test):** web
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| tests | 1 |
| web | 1 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 4.0 |  |
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

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 18 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 49% of LOC churn is in test files


## Required actions before merge

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `web/src` is active in recent history; run targeted smoke for behavior touching this area.
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

**Score:** 0.0/100 (low) · base `206c55b68c117347a659e65c5f4265c19a1867a6`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 0/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 0 fail · 2 not evaluated

**Top risk drivers:**
- Diff overlaps a path prefix touched in multiple recent commits (4 pts): Prefix touched in 18 of the last 50 sampled commits — sustained activity; extra regression care.

**Top required validations:**
1. Required status checks must pass before merge
2. Run targeted regression for path prefixes with sustained recent commit activity

**Review routing:**
- Include frontend review for web/ UI and client behavior.
- Focus primary review on `web/src` (majority of churn).
_…and 1 more in `pr_risk.md`_

**Score math:** factors 4.0 − reducers 4.0 → 0.0 · low

_Full checklist and analysis in artifact `pr_risk.md`._

```
