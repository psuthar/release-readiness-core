# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:09Z  
**Base ref:** `af00644b33f3eb44e56ea709fafe25617ac0553d`  

> Medium risk (score 38). Some risk factors are present but are manageable. Review the factors below before merging.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **38.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **80** / 100 |
| Files changed | 5 |
| LOC churn (add+del) | 753 |
| Test files in diff | 2 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 38/100); merge only after completing checklist items and review. |
| Evidence | 0 pass · 0 missing · 0 fail · 3 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include reviewer familiar with creator orchestration recommendations and draft-approval flows.
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
- test: targeted regression for path prefixes with several recent commits overlapping this diff
- process: PR description with scoped, evidence-backed review plan

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 0 missing · ❌ 0 fail · 📋 3 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_hotspot_regression_focus` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note detected; targeted regression coverage cannot be confirmed from diff alone — requires human review. |
| `pr_review_summary` | 📋 not evaluated (requires CI/reviewer confirmation) | intent | PR description quality could not be confirmed from available signals — requires human review. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **38.0** |
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **38.0** |
| Floor minimum (when rules apply) | **20** |
| Floor applied | **no** |
| Floor reasons | Large diff cannot score in the low band (floor applies) |
| **Final score** | **38.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `co_located` — Tests in this diff are mostly next to or under the same directories as changed production files. Behavioral depth: adequate for this diff’s risk class (E2E/domain overlap with sensitive areas, or non-sensitive production changes).
- **Behavioral coverage depth:** `adequate`
- Non-test files: **3** with nearby test in diff: **3** (ratio **100%**)

### Change concentration

- **Mode:** `focused` — Most churn (~89%) sits under `web/src`.
- Top area: `web/src` (~89% of churn); **2** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/src`** — 33 distinct commits (sampled) — Prefix touched in 33 of the last 50 sampled commits — sustained activity; extra regression care.
- **`web/tests`** — 19 distinct commits (sampled) — Prefix touched in 19 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-212: collapse pending-row actions into one dropdown
- **Domains in diff (non-test):** orchestration, web
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| orchestration | 1 |
| tests | 2 |
| web | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 38.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 20.0 | 80 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| Sensitive domains changed | -10 |
| E2E tests present in diff | +40 |

**Final confidence score: 80 / 100**

## Risk factors

### Large diff (`diff_large`)

- **Points:** 12.0
- **Detail:** total LOC churn=753 (threshold 400)

### Creator orchestration/recommendation flow changed (`domain_orchestration`)

- **Points:** 10.0
- **Detail:** 1 file(s)

### Large frontend change (`web_large`)

- **Points:** 12.0
- **Detail:** estimated web LOC churn≈753 (threshold 400)

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 33 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `web/src` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

### [ supporting ] Make PR review scoped and evidence-backed

- Add a PR description summary: what changed and why.
- Group changes by subsystem so reviewers can validate quickly.

## Mitigations

### `diff_large`

- Review commit-by-commit; consider feature flags for risky paths.

### `domain_orchestration`

- Validate creator orchestration flows (recommendation list/sync, draft approve/reject).
- Verify orchestration remains human-in-the-loop (no autonomous send/post actions).

### `web_large`

- Run `npm run build` and spot-check creator/participant UIs.
- Cross-browser smoke if CSS/layout changed.

### `context_hotspot_overlap`

- Run focused regression on the overlapping prefix; several recent commits touched it, so regressions are likelier.
- Scan related modules for unintended behavior changes.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 38.0/100 (medium) · base `af00644b33f3eb44e56ea709fafe25617ac0553d`

**PR risk assessment:** **WARN** — Risk band is medium (score 38/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 0 fail · 3 not evaluated

**Top risk drivers:**
- Large diff (12 pts): total LOC churn=753 (threshold 400)
- Creator orchestration/recommendation flow changed (10 pts): 1 file(s)
_…and 2 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Run targeted regression for path prefixes with sustained recent commit activity
_…and 1 more in `pr_risk.md`_

**Review routing:**
- Include reviewer familiar with creator orchestration recommendations and draft-approval flows.
- Include frontend review for web/ UI and client behavior.
_…and 2 more in `pr_risk.md`_

**Score math:** factors 38.0 − reducers 0.0 → 38.0 · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
