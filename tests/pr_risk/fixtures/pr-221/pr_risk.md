# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:03Z  
**Base ref:** `c3d705a1f252268508105cd2b2bd6f2b623e4986`  

> Medium risk (score 34). Some risk factors are present but are manageable. Review the factors below before merging.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **34.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **77** / 100 |
| Files changed | 9 |
| LOC churn (add+del) | 328 |
| Test files in diff | 2 |
| Config-ish files (CI/deploy/mod) | 0 |
| Validation note | yes (Validation:) |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 34/100); merge only after completing checklist items and review. |
| Evidence | 1 pass · 0 missing · 0 fail · 1 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include a reviewer familiar with auth, sessions, and invitations.
- Route processing/RAG changes to someone who owns ingestion, jobs, and Q&A quality.
- Include reviewer familiar with creator orchestration recommendations and draft-approval flows.
- Focus primary review on `internal/handlers` (majority of churn).
- Extra reviewer attention on `web/tests` (several recent commits touched this area).

### Blocking / elevated review reasons

- Elevated review: risk band "medium" — complete listed validations before merge.

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
- Required validations are distinct from mitigations: validations are merge gates; mitigations are factor-specific guidance.
- Required actions prioritized as high / medium / supporting by action ID and risk class.

### Required validations before merge

- ci: required status checks must pass before merge
- test: targeted regression for path prefixes with several recent commits overlapping this diff
- process: validation note present in commit — confirm it matches what was run

### Evidence status (repo-local signals)

> ✅ 1 pass · ⚠️ 0 missing · ❌ 0 fail · 📋 1 not evaluated (requires CI/reviewer confirmation)

| Action / Validation | Status | Source | Rationale |
|---------------------|--------|--------|-----------|
| `ci_baseline` | 📋 not evaluated (requires CI/reviewer confirmation) | git_signals | CI pass/fail cannot be confirmed from diff signals alone; requires human/pipeline review. |
| `context_hotspot_regression_focus` | ✅ pass | git_signals | Validation note present in commit: Validation: |

### Manual merge prerequisites

- At least one approving review on the changed code.


## Score math

| Step | Value |
|------|------:|
| Factors subtotal (sum of factor points) | **38.0** |
| Reducers subtotal (points subtracted) | **4.0** |
| Net before floor | **34.0** |
| Floor rules | _none_ |
| **Final score** | **34.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `co_located` — Tests in this diff are mostly next to or under the same directories as changed production files. Behavioral depth: unit-level overlap with sensitive domains but no matching E2E evidence in this diff — consider deeper tests where applicable.
- **Behavioral coverage depth:** `shallow`
- Non-test files: **7** with nearby test in diff: **7** (ratio **100%**)

### Change concentration

- **Mode:** `focused` — Most churn (~81%) sits under `internal/handlers`.
- Top area: `internal/handlers` (~81% of churn); **2** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/tests`** — 27 distinct commits (sampled) — Prefix touched in 27 of the last 50 sampled commits — sustained activity; extra regression care.
- **`internal/handlers`** — 9 distinct commits (sampled) — Prefix touched in 9 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `strong`
- **Subject line (source):** SCRUM-227: route editor authz through session_memberships role, not email match
- **Keywords matched:** auth, session
- **Domains implied by text:** auth, api
- **Domains in diff (non-test):** api, auth, orchestration, rag
- **Aligned:** yes — Keywords in the title/body align with domains touched in the diff.

## Domain hits

| Domain | Files |
|--------|-------|
| api | 3 |
| auth | 1 |
| orchestration | 2 |
| rag | 1 |
| tests | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 38.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 23.0 | 77 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| Sensitive domains changed | -10 |
| E2E tests present in diff | +40 |
| Behavioral coverage depth is shallow | -3 |

**Final confidence score: 77 / 100**

## Risk factors

### Auth/session/invite area changed (`domain_auth`)

- **Points:** 14.0
- **Detail:** 1 file(s) in auth-related paths

### RAG pipeline changed (`domain_rag`)

- **Points:** 10.0
- **Detail:** 1 file(s)

### Creator orchestration/recommendation flow changed (`domain_orchestration`)

- **Points:** 10.0
- **Detail:** 2 file(s)

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 27 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 51% of LOC churn is in test files


## Required actions before merge

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `web/tests` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

## Mitigations

### `domain_auth`

- Run auth/session flows manually or via E2E (login, invite, participant).
- Verify cookie/session settings in staging (SameSite, HTTPS).

### `domain_rag`

- Smoke-test Q&A with citations on a session with materials.
- Watch embedding/index job logs after deploy.

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

**Score:** 34.0/100 (medium) · base `c3d705a1f252268508105cd2b2bd6f2b623e4986`

**PR risk assessment:** **WARN** — Risk band is medium (score 34/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 1 pass · 0 missing · 0 fail · 1 not evaluated

**Top risk drivers:**
- Auth/session/invite area changed (14 pts): 1 file(s) in auth-related paths
- RAG pipeline changed (10 pts): 1 file(s)
_…and 2 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Run targeted regression for path prefixes with sustained recent commit activity
_…and 1 more in `pr_risk.md`_

**Review routing:**
- Include a reviewer familiar with auth, sessions, and invitations.
- Route processing/RAG changes to someone who owns ingestion, jobs, and Q&A quality.
_…and 3 more in `pr_risk.md`_

**Score math:** factors 38.0 − reducers 4.0 → 34.0 · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
