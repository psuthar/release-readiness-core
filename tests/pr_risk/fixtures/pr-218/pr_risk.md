# TalkBack PR Risk Report (v2.8)

**Generated:** 2026-04-30T21:19:04Z  
**Base ref:** `89bad3783c950933492ecdc28a150542c79c78dc`  

> Low risk. The diff is small and does not touch sensitive areas. Standard review is sufficient.

## Summary

| Metric | Value |
|--------|-------|
| Risk score | **9.0** / 100 |
| Band | **low** |
| Report version | **v2.8** |
| Test confidence | **60** / 100 |
| Files changed | 4 |
| LOC churn (add+del) | 251 |
| Test files in diff | 2 |
| Config-ish files (CI/deploy/mod) | 0 |
| Validation note | yes (Validation:) |

## PR risk assessment

> _This report evaluates PR risk only. It does not replace branch protection, required CI checks, code review, or targeted testing._

| Item | Value |
|------|-------|
| **PR risk assessment** | **PASS (low risk)** |
| Rationale | PR risk is low (score 9/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging. |
| Evidence | 1 pass · 0 missing · 0 fail · 1 not evaluated |

### Recommended review strategy

Single-pass review is enough; spot-check touched paths if helpful.

### Review routing (recommended)

- Include a reviewer familiar with auth, sessions, and invitations.
- Focus primary review on `internal/handlers` (majority of churn).
- Extra reviewer attention on `web/tests` (several recent commits touched this area).

### Blocking / elevated review reasons

_None._

### Policy trace (deterministic)

- Deterministic policy: merge recommendation derives from risk band, git availability, and tests_missing in low band.
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
| Factors subtotal (sum of factor points) | **18.0** |
| Reducers subtotal (points subtracted) | **9.0** |
| Net before floor | **9.0** |
| Floor rules | _none_ |
| **Final score** | **9.0** |
| **Final band** | **low** |

## Context insights

### Test–code proximity

- **Structural alignment:** `partial` — Some production changes lack adjacent tests in the same diff; spot-check coverage.
- **Behavioral coverage depth:** `unknown`
- Non-test files: **2** with nearby test in diff: **1** (ratio **50%**)

### Change concentration

- **Mode:** `focused` — Most churn (~61%) sits under `internal/handlers`.
- Top area: `internal/handlers` (~61% of churn); **3** distinct path prefixes.

### Hotspots (recent git activity)

- **`web/tests`** — 25 distinct commits (sampled) — Prefix touched in 25 of the last 50 sampled commits — sustained activity; extra regression care.
- **`internal/handlers`** — 7 distinct commits (sampled) — Prefix touched in 7 of the last 50 sampled commits — sustained activity; extra regression care.
- **`internal/database`** — 5 distinct commits (sampled) — Prefix touched in 5 of the last 50 sampled commits — sustained activity; extra regression care.

### PR intent vs diff

- **Intent strength:** `unknown`
- **Subject line (source):** SCRUM-225: source live membership role in invitations listing; drop dual-write
- **Domains in diff (non-test):** auth, database
- **Aligned:** n/a — No strong intent keywords matched; alignment not scored.

## Domain hits

| Domain | Files |
|--------|-------|
| auth | 1 |
| database | 1 |
| tests | 2 |

## Risk categories (decision lanes)

| Category | Risk score | Confidence |
|----------|------------:|------------:|
| Code changes | 18.0 |  |
| Workflow / deployment changes | 0.0 |  |
| Test confidence | 40.0 | 60 |

### Test confidence breakdown

Base score: 50

| Reason | Δ |
|--------|---:|
| Sensitive domains changed | -10 |
| E2E tests present in diff | +40 |
| Tests only partially aligned with changed code | -8 |
| Behavioral coverage depth unknown | -5 |
| Behavioral coverage depth unknown for sensitive domain changes | -5 |
| Some changed files lack nearby tests | -2 |

**Final confidence score: 60 / 100**

## Risk factors

### Auth/session/invite area changed (`domain_auth`)

- **Points:** 14.0
- **Detail:** 1 file(s) in auth-related paths

### Diff overlaps a path prefix touched in multiple recent commits (`context_hotspot_overlap`)

- **Points:** 4.0
- **Detail:** Prefix touched in 25 of the last 50 sampled commits — sustained activity; extra regression care.


## Reducers (what lowers risk)

### `domain_auth_unit_evidence` (-5.0 points)

- Unit test evidence present
- Primarily affects: `test_confidence`
- Evidence: Found unit tests targeting the domain in the diff

### `test_heavy_diff` (-4.0 points)

- Test-heavy diff
- Primarily affects: `test_confidence`
- Evidence: 81% of LOC churn is in test files


## Required actions before merge

### [ supporting ] Extra regression focus on active path (recent commits)

- Prefix `web/tests` is active in recent history; run targeted smoke for behavior touching this area.
- Watch for unintended side effects in adjacent modules.

## Mitigations

### `domain_auth`

- Run auth/session flows manually or via E2E (login, invite, participant).
- Verify cookie/session settings in staging (SameSite, HTTPS).

### `context_hotspot_overlap`

- Run focused regression on the overlapping prefix; several recent commits touched it, so regressions are likelier.
- Scan related modules for unintended behavior changes.

## Integrations

- **Jira:** _(set `PRRISK_JIRA_ISSUE_KEY` for optional linkage)_

## Suggested PR comment (markdown)

```markdown
## PR Risk (v2.8)

**Score:** 9.0/100 (low) · base `89bad3783c950933492ecdc28a150542c79c78dc`

**PR risk assessment:** **PASS (low risk)** — PR risk is low (score 9/100). Normal prerequisites — CI checks, required reviews, and any targeted testing — still apply before merging.

_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted testing) still apply regardless of this assessment._

**Evidence:** 1 pass · 0 missing · 0 fail · 1 not evaluated

**Top risk drivers:**
- Auth/session/invite area changed (14 pts): 1 file(s) in auth-related paths
- Diff overlaps a path prefix touched in multiple recent commits (4 pts): Prefix touched in 25 of the last 50 sampled commits — sustained activity; extra regression care.

**Top required validations:**
1. Required status checks must pass before merge
2. Run targeted regression for path prefixes with sustained recent commit activity
_…and 1 more in `pr_risk.md`_

**Review routing:**
- Include a reviewer familiar with auth, sessions, and invitations.
- Focus primary review on `internal/handlers` (majority of churn).
_…and 1 more in `pr_risk.md`_

**Score math:** factors 18.0 − reducers 9.0 → 9.0 · low

_Full checklist and analysis in artifact `pr_risk.md`._

```
