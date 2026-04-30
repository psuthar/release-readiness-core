# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:29Z  
**Base ref:** `dff9b5b12e34211a30ae431c16b667c91b4a8f12`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **4.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **55** / 100 |
| Files changed | 4 |
| LOC churn (add+del) | 134 |
| Test files in diff | 0 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **PASS (low risk)** |
| Rationale | PR risk is low (score 4/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging. |
| Evidence | 0 pass · 0 missing · 0 fail · 2 not evaluated |

### Recommended review strategy

Single-pass review is enough; spot-check touched paths if helpful.

### Review routing (recommended)

- Extra reviewer attention on `eval/qa` (several recent commits touched this area).

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
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **4.0** |
| Floor rules | _none_ |
| **Final score** | **4.0** |
| **Final band** | **low** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — No test files in diff; proximity of tests to changed code cannot be established from this diff alone.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **4** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `balanced` — Churn is spread across several areas in a typical way.
- Top area: `scripts/test_run_qa_eval.py` (~40% of churn); **3** distinct path prefixes.

### Hotspots (recent git activity)

- **`eval/qa`** — 7 distinct commits (sampled) — Prefix touched in 7 of the last 50 sampled commits — sustained activity; extra regression care.
- **`scripts/run_qa_eval.py`** — 5 distinct commits (sampled) — Prefix touched in 5 of the last 50 sampled commits — sustained activity; extra regression care.
- **`scripts/test_run_qa_eval.py`** — 5 distinct commits (sampled) — Prefix touched in 5 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-143: complete live pilot baseline with judge/report fixes
- **Domains in diff (non-test):** other, scripts
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| other | 2 |
| scripts | 2 |

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
- **Detail:** Prefix touched in 7 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `eval/qa` is active in recent history; run targeted smoke for behavior touching this area.
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

**Score:** 4.0/100 (low) · base `dff9b5b12e34211a30ae431c16b667c91b4a8f12`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 4/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 0 fail · 2 not evaluated

**Top risk drivers:**
- Diff overlaps a path prefix touched in multiple recent commits (4 pts): Prefix touched in 7 of the last 50 sampled commits — sustained activity; extra regression care.

**Top required validations:**
1. Required status checks must pass before merge
2. Run targeted regression for path prefixes with sustained recent commit activity

**Review routing:**
- Extra reviewer attention on `eval/qa` (several recent commits touched this area).

**Score math:** factors 4.0 − reducers 0.0 → 4.0 · low

_Full checklist and analysis in artifact `pr_risk.md`._

```
