# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:08Z  
**Base ref:** `f9814d423cd835e9211a48cf01173b7261abd8ec`  

> Medium risk (score 43). Some risk factors are present but are manageable. Review the factors below before merging.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **43.0** / 100 |
| Band | **medium** |
| Report version | **v2.8** |
| Test confidence | **77** / 100 |
| Files changed | 12 |
| LOC churn (add+del) | 1183 |
| Test files in diff | 4 |
| Config-ish files (CI/deploy/mod) | 0 |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **WARN** |
| Rationale | Risk band is medium (score 43/100); merge only after completing checklist items and review. |
| Evidence | 0 pass · 0 missing · 0 fail · 3 not evaluated |

### Recommended review strategy

Use a checklist-driven review: walk factors and required actions, then approve when evidence matches.

### Review routing (recommended)

- Include a reviewer familiar with auth, sessions, and invitations.
- Include reviewer familiar with creator orchestration recommendations and draft-approval flows.
- Include frontend review for web/ UI and client behavior.
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
| Factors subtotal (sum of factor points) | **52.0** |
| Reducers subtotal (points subtracted) | **9.0** |
| Net before floor | **43.0** |
| Floor minimum (when rules apply) | **20** |
| Floor applied | **no** |
| Floor reasons | Large diff cannot score in the low band (floor applies) |
| **Final score** | **43.0** |
| **Final band** | **medium** |

## Context insights

### Test–code proximity

- **Structural alignment:** `co_located` — Tests in this diff are mostly next to or under the same directories as changed production files. Behavioral depth: unit-level overlap with sensitive domains but no matching E2E evidence in this diff — consider deeper tests where applicable.
- **Behavioral coverage depth:** `shallow`
- Non-test files: **8** with nearby test in diff: **7** (ratio **88%**)

### Change concentration

- **Mode:** `balanced` — Churn is spread across several areas in a typical way.
- Top area: `internal/handlers` (~46% of churn); **4** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/src`** — 34 distinct commits (sampled) — Prefix touched in 34 of the last 50 sampled commits — sustained activity; extra regression care.
- **`web/tests`** — 20 distinct commits (sampled) — Prefix touched in 20 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-213: PATCH membership role + accepted-row menu
- **Domains in diff (non-test):** api, auth, database, orchestration, web
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| api | 3 |
| auth | 1 |
| database | 1 |
| orchestration | 1 |
| tests | 4 |
| web | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 52.0 |  |
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

### Large diff (`diff_large`)

- **Points:** 12.0
- **Detail:** total LOC churn=1183 (threshold 400)

### Auth/session/invite area changed (`domain_auth`)

- **Points:** 14.0
- **Detail:** 1 file(s) in auth-related paths

### Creator orchestration/recommendation flow changed (`domain_orchestration`)

- **Points:** 10.0
- **Detail:** 1 file(s)

### Large frontend change (`web_large`)

- **Points:** 12.0
- **Detail:** estimated web LOC churn≈542 (threshold 400)

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 34 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

### `domain_auth_unit_evidence` (-5.0 points)

- Unit test evidence present
- Primarily affects: `test_confidence`
- Evidence: Found unit tests targeting the domain in the diff

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 64% of LOC churn is in test files


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

### `domain_auth`

- Run auth/session flows manually or via E2E (login, invite, participant).
- Verify cookie/session settings in staging (SameSite, HTTPS).

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

**Score:** 43.0/100 (medium) · base `f9814d423cd835e9211a48cf01173b7261abd8ec`

**PR risk assessment:** **WARN** — Risk band is medium (score 43/100); merge only after completing checklist items and review.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 0 pass · 0 missing · 0 fail · 3 not evaluated

**Top risk drivers:**
- Large diff (12 pts): total LOC churn=1183 (threshold 400)
- Auth/session/invite area changed (14 pts): 1 file(s) in auth-related paths
_…and 3 more in `pr_risk.md`_

**Top required validations:**
1. Required status checks must pass before merge
2. Run targeted regression for path prefixes with sustained recent commit activity
_…and 1 more in `pr_risk.md`_

**Review routing:**
- Include a reviewer familiar with auth, sessions, and invitations.
- Include reviewer familiar with creator orchestration recommendations and draft-approval flows.
_…and 2 more in `pr_risk.md`_

**Score math:** factors 52.0 − reducers 9.0 → 43.0 · medium

_Full checklist and analysis in artifact `pr_risk.md`._

```
