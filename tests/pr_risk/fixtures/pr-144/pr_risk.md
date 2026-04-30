# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:41Z  
**Base ref:** `eba5fb9bc739eb5f27e1d1a8420cf3f4f5e5a2d1`  

> Medium risk (score 26). Some risk factors are present but are manageable. Review the factors below before merging.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **26.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **55** / 100 |
| Files changed | 8 |
| LOC churn (add+del) | 1353 |
| Test files in diff | 0 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 26/100); merge only after completing checklist items and review. |
| Evidence | 1 pass · 0 missing · 0 fail · 3 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include frontend review for web/ UI and client behavior.
- Focus primary review on `web/src` (majority of churn).
- Extra reviewer attention on `web/src` (several recent commits touched this area).

### Blocking / elevated review reasons

- Elevated review: risk band "medium" — complete listed validations before merge.

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required validations are distinct from mitigations: validations are merge gates; mitigations are factor-specific guidance.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- test: tests or recorded evidence for sensitive paths
- test: targeted regression for path prefixes with several recent commits overlapping this diff
- process: PR description with scoped, evidence-backed review plan

### Evidence status (repo-local signals)

> ✅ 1 pass · ⚠️ 0 missing · ❌ 0 fail · 📋 3 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `add_tests_or_evidence` | ✅ pass | git_signals | Style-only commit note present: purely cosmetic frontend change, no test required. |
| `context_hotspot_regression_focus` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note detected; targeted regression coverage cannot be confirmed from diff alone — requires human review. |
| `pr_review_summary` | 📋 not evaluated (requires CI/reviewer confirmation) | intent | PR description quality could not be confirmed from available signals — requires human review. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **46.0** |
| Reducers subtotal (points subtracted) | **20.0** |
| Net before floor | **26.0** |
| Floor minimum (when rules apply) | **20** |
| Floor applied | **no** |
| Floor reasons | Large diff cannot score in the low band (floor applies) |
| **Final score** | **26.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `distant` — No test files in diff; proximity of tests to changed code cannot be established from this diff alone.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **8** with nearby test in diff: **0** (ratio **0%**)

### Change concentration

- **Mode:** `focused` — Most churn (~100%) sits under `web/src`.
- Top area: `web/src` (~100% of churn); **1** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/src`** — 14 distinct commits (sampled) — Prefix touched in 14 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-119: migrate component inline styles to CSS modules
- **Domains in diff (non-test):** web
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| web | 8 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 28.0 |  |
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
- **Detail:** total LOC churn=1353 (threshold 400)

### Large frontend change (`web_large`)

- **Points:** 12.0
- **Detail:** estimated web LOC churn≈1353 (threshold 400)

### Sensitive areas changed without test file changes in this diff (`tests_missing`)

- **Points:** 18.0
- **Detail:** no *_test.go / web test paths in diff; consider adding or updating tests

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 14 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

### `style_only_note` (-20.0 points)

- Style-only frontend change (commit note)
- Primarily affects: `test_confidence`
- Evidence: Style-only: extract static inline styles in QAPanel, MaterialsTreePanel,


## Required actions before merge

### [ high ] Add/update tests before merge

- Add or update tests for changed code paths and confirm `go test ./...` passes.

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `web/src` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

### [ supporting ] Make PR review scoped and evidence-backed

- Add a PR description summary: what changed and why.
- Group changes by subsystem so reviewers can validate quickly.

## Mitigations

### `diff_large`

- Review commit-by-commit; consider feature flags for risky paths.

### `web_large`

- Run `npm run build` and spot-check creator/participant UIs.
- Cross-browser smoke if CSS/layout changed.

### `tests_missing`

- Add or update unit/integration tests for changed packages.
- If behavior is unchanged refactor-only, note that in the PR description.

### `context_hotspot_overlap`

- Run focused regression on the overlapping prefix; several recent commits touched it, so regressions are likelier.
- Scan related modules for unintended behavior changes.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 26.0/100 (medium) · base `eba5fb9bc739eb5f27e1d1a8420cf3f4f5e5a2d1`

**PR risk assessment:** **WARN** — Risk band is medium (score 26/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 1 pass · 0 missing · 0 fail · 3 not evaluated

**Top risk drivers:**
- Large diff (12 pts): total LOC churn=1353 (threshold 400)
- Large frontend change (12 pts): estimated web LOC churn≈1353 (threshold 400)
_…and 2 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Add tests or recorded evidence for sensitive paths
_…and 2 more in `pr_risk.md`_

**Review routing:**
- Include frontend review for web/ UI and client behavior.
- Focus primary review on `web/src` (majority of churn).
_…and 1 more in `pr_risk.md`_

**Score math:** factors 46.0 − reducers 20.0 → 26.0 · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
