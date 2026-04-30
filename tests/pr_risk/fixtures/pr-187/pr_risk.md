# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:20Z  
**Base ref:** `63c4a0bb680594038415d8415f5f7fea5ec6bb1e`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **7.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **57** / 100 |
| Files changed | 4 |
| LOC churn (add+del) | 210 |
| Test files in diff | 2 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **PASS (low risk)** |
| Rationale | PR risk is low (score 7/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging. |
| Evidence | 0 pass · 0 missing · 1 fail · 1 not evaluated |

### Recommended review strategy

Single-pass review is enough; spot-check touched paths if helpful.

### Review routing (recommended)

- Route processing/RAG changes to someone who owns ingestion, jobs, and Q&A quality.
- Focus primary review on `internal/handlers` (majority of churn).
- Confirm scope with author: PR text implies domains api, auth, rag but diff may differ.

### Blocking / elevated review reasons

_None._

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- process: PR title/body aligned with actual diff (intent match)

### Evidence status (repo-local signals)

> ✅ 0 pass · ⚠️ 0 missing · ❌ 1 fail · 📋 1 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_align_pr_description` | ❌ fail | intent | PR title/body keywords imply domains not present in diff: Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description. |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **16.0** |
| Reducers subtotal (points subtracted) | **9.0** |
| Net before floor | **7.0** |
| Floor rules | _none_ |
| **Final score** | **7.0** |
| **Final band** | **low** |

## Context insights

### Test–code proximity

- **Structural alignment:** `co_located` — Tests in this diff are mostly next to or under the same directories as changed production files. Behavioral depth: unit-level overlap with sensitive domains but no matching E2E evidence in this diff — consider deeper tests where applicable.
- **Behavioral coverage depth:** `shallow`
- Non-test files: **2** with nearby test in diff: **2** (ratio **100%**)

### Change concentration

- **Mode:** `focused` — Most churn (~60%) sits under `internal/handlers`.
- Top area: `internal/handlers` (~60% of churn); **2** distinct path prefixes.

### Hotspots (recent git activity)

_No overlapping hotspot prefixes detected (or git history unavailable)._

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-184: ground session answers in asker identity context
- **Keywords matched:** session, ask
- **Domains implied by text:** auth, api, rag
- **Domains in diff (non-test):** rag
- **Aligned:** no — Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

## Domain hits

| Domain | Files |
|--------|-------|
| rag | 2 |
| tests | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 16.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 43.0 | 57 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| Sensitive domains changed | -10 |
| Unit tests present in diff | +20 |
| Behavioral coverage depth is shallow | -3 |

**Final confidence score: 57 / 100**

## Risk factors

### RAG pipeline changed (`domain_rag`)

- **Points:** 10.0
- **Detail:** 2 file(s)

### PR title/body keywords do not align with paths in the diff (`context_intent_mismatch`)

- **Points:** 6.0
- **Detail:** Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.


## Reducers (what lowers risk)

### `domain_rag_unit_evidence` (-5.0 points)

- Unit test evidence present
- Primarily affects: `test_confidence`
- Evidence: Found unit tests targeting the domain in the diff

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 63% of LOC churn is in test files


## Required actions before merge

### [ medium ] Align PR title/description with the diff

- Update the PR title or body so keywords match the areas actually changed, or narrow the diff to match the stated intent.
- If the scope is intentional, explain why expected domains are not touched.

## Mitigations

### `domain_rag`

- Smoke-test Q&A with citations on a session with materials.
- Watch embedding/index job logs after deploy.

### `context_intent_mismatch`

- Update the PR title/body to match the diff, or adjust the diff to match the stated intent.
- If intentional, explain the scope change explicitly for reviewers.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 7.0/100 (low) · base `63c4a0bb680594038415d8415f5f7fea5ec6bb1e`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 7/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 1 fail · 1 not evaluated

**Top risk drivers:**
- RAG pipeline changed (10 pts): 2 file(s)
- PR title/body keywords do not align with paths in the diff (6 pts): Title/body suggests certain areas (keywords) but corresponding paths may be missing from this diff — confirm scope or update the PR description.

**Top required validations:**
1. Required status checks must pass before merge
2. Align PR title and body with the actual diff (intent match)

**Review routing:**
- Route processing/RAG changes to someone who owns ingestion, jobs, and Q&A quality.
- Focus primary review on `internal/handlers` (majority of churn).
_…and 1 more in `pr_risk.md`_

**Score math:** factors 16.0 − reducers 9.0 → 7.0 · low

_Full checklist and analysis in artifact `pr_risk.md`._

```
