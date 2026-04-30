# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:10Z  
**Base ref:** `d1a3ed61d648db3da3126d0a7da206e5dbb4f465`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **0.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **85** / 100 |
| Files changed | 3 |
| LOC churn (add+del) | 109 |
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

- **Structural alignment:** `co_located` — Tests in this diff are mostly next to or under the same directories as changed production files. Behavioral depth: adequate for this diff’s risk class (E2E/domain overlap with sensitive areas, or non-sensitive production changes).
- **Behavioral coverage depth:** `adequate`
- Non-test files: **2** with nearby test in diff: **2** (ratio **100%**)

### Change concentration

- **Mode:** `balanced` — Churn is spread across several areas in a typical way.
- Top area: `web/tests` (~52% of churn); **2** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/src`** — 32 distinct commits (sampled) — Prefix touched in 32 of the last 50 sampled commits — sustained activity; extra regression care.
- **`web/tests`** — 18 distinct commits (sampled) — Prefix touched in 18 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-211: scope per-button hover so global blue stops hiding text
- **Domains in diff (non-test):** web
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| tests | 1 |
| web | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 4.0 |  |
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
- **Detail:** Prefix touched in 32 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 52% of LOC churn is in test files


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

**Score:** 0.0/100 (low) · base `d1a3ed61d648db3da3126d0a7da206e5dbb4f465`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 0/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 0 fail · 2 not evaluated

**Top risk drivers:**
- Diff overlaps a path prefix touched in multiple recent commits (4 pts): Prefix touched in 32 of the last 50 sampled commits — sustained activity; extra regression care.

**Top required validations:**
1. Required status checks must pass before merge
2. Run targeted regression for path prefixes with sustained recent commit activity

**Review routing:**
- Include frontend review for web/ UI and client behavior.
- Extra reviewer attention on `web/src` (several recent commits touched this area).

**Score math:** factors 4.0 − reducers 4.0 → 0.0 · low

_Full checklist and analysis in artifact `pr_risk.md`._

```
