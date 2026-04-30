# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:27Z  
**Base ref:** `6703df8ba19a89ccba007e402311dede361efce7`  

> Medium risk (score 34). Some risk factors are present but are manageable. Review the factors below before merging.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **34.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **85** / 100 |
| Files changed | 8 |
| LOC churn (add+del) | 1156 |
| Test files in diff | 3 |
| Config-ish files (CI/deploy/mod) | 0 |
| Validation note | yes (Validation: Targeted regression for participant DecisionBar flow ran locally — vitest 229/229 pass (incl. new Decision) |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 34/100); merge only after completing checklist items and review. |
| Evidence | 2 pass · 0 missing · 1 fail · 1 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include frontend review for web/ UI and client behavior.
- Focus primary review on `web/src` (majority of churn).
- Extra reviewer attention on `web/src` (several recent commits touched this area).
- Confirm scope with author: PR text implies domains workflows but diff may differ.

### Blocking / elevated review reasons

- Elevated review: risk band "medium" — complete listed validations before merge.
- Evidence FAIL [context_align_pr_description]: PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required validations are distinct from mitigations: validations are merge gates; mitigations are factor-specific guidance.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- process: PR title/body aligned with actual diff (intent match)
- test: targeted regression for path prefixes with several recent commits overlapping this diff
- process: PR description with scoped, evidence-backed review plan
- process: validation note present in commit — confirm it matches what was run

### Evidence status (repo-local signals)

> ✅ 2 pass · ⚠️ 0 missing · ❌ 1 fail · 📋 1 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |
| `context_hotspot_regression_focus` | ✅ pass | git_signals | Validation note present in commit: Validation: Targeted regression for participant DecisionBar flow ran locally —… |
| `pr_review_summary` | ✅ pass | intent | PR title/body has strong keywords aligned with the diff. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **34.0** |
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **34.0** |
| Floor minimum (when rules apply) | **20** |
| Floor applied | **no** |
| Floor reasons | Large diff cannot score in the low band (floor applies) |
| **Final score** | **34.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `co_located` — Tests in this diff are mostly next to or under the same directories as changed production files. Behavioral depth: adequate for this diff’s risk class (E2E/domain overlap with sensitive areas, or non-sensitive production changes).
- **Behavioral coverage depth:** `adequate`
- Non-test files: **5** with nearby test in diff: **5** (ratio **100%**)

### Change concentration

- **Mode:** `focused` — Most churn (~98%) sits under `web/src`.
- Top area: `web/src` (~98% of churn); **2** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/src`** — 27 distinct commits (sampled) — Prefix touched in 27 of the last 50 sampled commits — sustained activity; extra regression care.
- **`web/tests`** — 6 distinct commits (sampled) — Prefix touched in 6 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-148: add persistent Decision Bar with member-level vote tooltips
- **Keywords matched:** ci
- **Domains implied by text:** workflows
- **Domains in diff (non-test):** web
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| tests | 3 |
| web | 5 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 34.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 15.0 | 85 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| No sensitive domains changed | +35 |

**Final confidence score: 85 / 100**

## Risk factors

### Large diff (`diff_large`)

- **Points:** 12.0
- **Detail:** total LOC churn=1156 (threshold 400)

### Large frontend change (`web_large`)

- **Points:** 12.0
- **Detail:** estimated web LOC churn≈1156 (threshold 400)

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 27 of the last 50 sampled commits — sustained activity; extra regression care.

### PR title/body keywords do not align with paths in the diff (`context_intent_mismatch`)

- **Points:** 6.0
- **Detail:** Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.


## Reducers (what lowers risk)

_No reducers matched._

## Required actions before merge

### [ medium ] Align PR title/description with the diff

- Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent.
- If the scope is intentional, explain why expected domains are not touched.

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

### `context_hotspot_overlap`

- Run focused regression on the overlapping prefix; several recent commits touched it, so regressions are likelier.
- Scan related modules for unintended behavior changes.

### `context_intent_mismatch`

- Update the PR title/body to match the diff, or adjust the diff to match the stated intent.
- If intentional, explain the scope change explicitly for reviewers.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 34.0/100 (medium) · base `6703df8ba19a89ccba007e402311dede361efce7`

**PR risk assessment:** **WARN** — Risk band is medium (score 34/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 2 pass · 0 missing · 1 fail · 1 not evaluated

**Top risk drivers:**
- Large diff (12 pts): total LOC churn=1156 (threshold 400)
- Large frontend change (12 pts): estimated web LOC churn≈1156 (threshold 400)
_…and 2 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Align PR title and body with the actual diff (intent match)
_…and 3 more in `pr_risk.md`_

**Review routing:**
- Include frontend review for web/ UI and client behavior.
- Focus primary review on `web/src` (majority of churn).
_…and 2 more in `pr_risk.md`_

**Score math:** factors 34.0 − reducers 0.0 → 34.0 · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
