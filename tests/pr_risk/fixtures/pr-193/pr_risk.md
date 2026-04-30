# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:17Z  
**Base ref:** `e9e4319816d48e466a0ed3b4ba3f24c86eda36ba`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **14.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **25** / 100 |
| Files changed | 4 |
| LOC churn (add+del) | 187 |
| Test files in diff | 1 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **PASS (low risk)** |
| Rationale | PR risk is low (score 14/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging. |
| Evidence | 0 pass · 1 missing · 0 fail · 2 not evaluated |

### Recommended review strategy

Single-pass review is enough; spot-check touched paths if helpful.

### Review routing (recommended)

- Include reviewer familiar with creator orchestration recommendations and draft-approval flows.
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
- test: tests co-located or explicitly linked for changed code

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 1 missing · ❌ 0 fail · 📋 2 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_hotspot_regression_focus` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note detected; targeted regression coverage cannot be confirmed from diff alone — requires human review. |
| `context_improve_test_proximity` | ⚠️ missing | proximity | Structural alignment is "distant" with no test coverage evidence for this diff. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **14.0** |
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **14.0** |
| Floor rules | _none_ |
| **Final score** | **14.0** |
| **Final band** | **low** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — Many changed production files have no test file in the same directory or an obvious sibling path in this diff.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **3** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `focused` — Most churn (~100%) sits under `web/src`.
- Top area: `web/src` (~100% of churn); **1** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/src`** — 34 distinct commits (sampled) — Prefix touched in 34 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-192: primary-action button styling per recommendation type
- **Domains in diff (non-test):** orchestration, web
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| orchestration | 1 |
| tests | 1 |
| web | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 14.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 75.0 | 25 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| Sensitive domains changed | -10 |
| Unit tests present in diff | +20 |
| Tests structurally distant from changed code | -15 |
| Behavioral coverage depth unknown | -5 |
| Behavioral coverage depth unknown for sensitive domain changes | -5 |
| No changed files have nearby tests in diff | -10 |

**Final confidence score: 25 / 100**

## Risk factors

### Creator orchestration/recommendation flow changed (`domain_orchestration`)

- **Points:** 10.0
- **Detail:** 1 file(s)

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 34 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `web/src` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

### [ supporting ] Improve test proximity for changed code

- Add or reference tests in the same package or directory as changed production files.
- If tests live elsewhere, link them in the PR description.

## Mitigations

### `domain_orchestration`

- Validate creator orchestration flows (recommendation list/sync, draft approve/reject).
- Verify orchestration remains human-in-the-loop (no autonomous send/post actions).

### `context_hotspot_overlap`

- Run focused regression on the overlapping prefix; several recent commits touched it, so regressions are likelier.
- Scan related modules for unintended behavior changes.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 14.0/100 (low) · base `e9e4319816d48e466a0ed3b4ba3f24c86eda36ba`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 14/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 1 missing · 0 fail · 2 not evaluated

**Top risk drivers:**
- Creator orchestration/recommendation flow changed (10 pts): 1 file(s)
- Diff overlaps a path prefix touched in multiple recent commits (4 pts): Prefix touched in 34 of the last 50 sampled commits — sustained activity; extra regression care.

**Top required validations:**
1. Required status checks must pass before merge
2. Run targeted regression for path prefixes with sustained recent commit activity
_…and 1 more in `pr_risk.md`_

**Review routing:**
- Include reviewer familiar with creator orchestration recommendations and draft-approval flows.
- Include frontend review for web/ UI and client behavior.
_…and 2 more in `pr_risk.md`_

**Score math:** factors 14.0 − reducers 0.0 → 14.0 · low

_Full checklist and analysis in artifact `pr_risk.md`._

```
