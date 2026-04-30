# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:19Z  
**Base ref:** `56458481329e8361903f6081b572b12a82a40a23`  

> Medium risk (score 20). Some risk factors are present but are manageable. Review the factors below before merging.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **20.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **80** / 100 |
| Files changed | 2 |
| LOC churn (add+del) | 168 |
| Test files in diff | 1 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 20/100); merge only after completing checklist items and review. |
| Evidence | 0 pass · 0 missing · 1 fail · 2 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include reviewer familiar with creator orchestration recommendations and draft-approval flows.
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

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 0 missing · ❌ 1 fail · 📋 2 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |
| `context_hotspot_regression_focus` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | No validation note detected; targeted regression coverage cannot be confirmed from diff alone — requires human review. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **20.0** |
| Reducers subtotal (points subtracted) | **0.0** |
| Net before floor | **20.0** |
| Floor rules | _none_ |
| **Final score** | **20.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `co_located` — Tests in this diff are mostly next to or under the same directories as changed production files. Behavioral depth: adequate for this diff’s risk class (E2E/domain overlap with sensitive areas, or non-sensitive production changes).
- **Behavioral coverage depth:** `adequate`
- Non-test files: **1** with nearby test in diff: **1** (ratio **100%**)

### Change concentration

- **Mode:** `focused` — Most churn (~85%) sits under `web/src`.
- Top area: `web/src` (~85% of churn); **2** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/src`** — 34 distinct commits (sampled) — Prefix touched in 34 of the last 50 sampled commits — sustained activity; extra regression care.
- **`web/tests`** — 15 distinct commits (sampled) — Prefix touched in 15 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-188: use shared DecisionBar in creator view; remove sidebar Decisions panel
- **Keywords matched:** ci
- **Domains implied by text:** workflows
- **Domains in diff (non-test):** orchestration
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| orchestration | 1 |
| tests | 1 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 20.0 |  |
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

### Creator orchestration/recommendation flow changed (`domain_orchestration`)

- **Points:** 10.0
- **Detail:** 1 file(s)

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 34 of the last 50 sampled commits — sustained activity; extra regression care.

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

## Mitigations

### `domain_orchestration`

- Validate creator orchestration flows (recommendation list/sync, draft approve/reject).
- Verify orchestration remains human-in-the-loop (no autonomous send/post actions).

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

**Score:** 20.0/100 (medium) · base `56458481329e8361903f6081b572b12a82a40a23`

**PR risk assessment:** **WARN** — Risk band is medium (score 20/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 1 fail · 2 not evaluated

**Top risk drivers:**
- Creator orchestration/recommendation flow changed (10 pts): 1 file(s)
- Diff overlaps a path prefix touched in multiple recent commits (4 pts): Prefix touched in 34 of the last 50 sampled commits — sustained activity; extra regression care.
_…and 1 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Align PR title and body with the actual diff (intent match)
_…and 1 more in `pr_risk.md`_

**Review routing:**
- Include reviewer familiar with creator orchestration recommendations and draft-approval flows.
- Focus primary review on `web/src` (majority of churn).
_…and 2 more in `pr_risk.md`_

**Score math:** factors 20.0 − reducers 0.0 → 20.0 · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
