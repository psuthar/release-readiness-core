# SCRUM-167 prep — validation-key handling (config-driven)

This document captures everything needed to implement **SCRUM-167** (“Make engine validation-key handling config-driven”) without re-reading TalkBack line-by-line.

## Goal of SCRUM-167

Move **hardcoded validation-key lists** in the readiness merge logic into **configuration**, while preserving deterministic behavior and parity with TalkBack until golden fixtures land (**SCRUM-172**).

Primary upstream reference (TalkBack, today):

- Engine: `scripts/release_readiness_engine.py`
- Merge helper: `merge_validations(smoke, e2e, config)`
- Live config: `ops/release-readiness/config.yaml`

Downstream home for extracted logic:

- Package: `release-readiness-core` (engine + config schema)

## Concepts

| Concept | Meaning |
|--------|---------|
| **Validation key** | String identifier (e.g. `auth_session`) used in evidence maps, required-set logic, and report `validations` dict |
| **`val_map`** | `dict[str, bool]` merged from evidence; `True` = evidenced, `False` = explicitly failed/absent |
| **Known keys** | Keys declared under `config.validations` (descriptions + registry) |
| **Required keys** | Derived from **risk categories** for changed files + migration rule (see below) |
| **Statuses** | Per-key output: `satisfied` \| `missing` \| `not_required` \| `not_evaluated` |

## Config already driven by YAML (no change in SCRUM-167)

These are **already** read from `config` today:

- **`validations`** — map of key → `{ description }` (defines **known_keys** for reporting)
- **`infer_validations_when_pass.smoke`** — keys inferred `True` when smoke artifact passes
- **`infer_validations_when_pass.e2e`** — keys inferred `True` when E2E artifact passes

See `ops/release-readiness/config.yaml` in TalkBack.

## Hardcoded today (SCRUM-167 targets)

### 1. Evidence top-level boolean shortcuts (`merge_validations`)

In `release_readiness_engine.py`, after merging explicit `validations` dicts from JSON, the code treats these **fixed** top-level evidence keys as boolean validators:

```text
auth_session, upload_extraction, nav_assets, viewer_materials, qa_rag, migrations_validated
```

If `evid.get(k) is True`, `val_map[k] = True`.

**SCRUM-167 direction:** Move this list into config, e.g. `evidence_boolean_keys` or nest under `validations.<key>.evidence_aliases`.

### 2. Risk category → required validation (partially implicit)

- For each risk category `r` from `risk_from_paths`, **`r` becomes a required validation key** (must appear in `val_map` as `True` when risks exist).
- Special case: category **`migrations`** maps to required key **`migrations_validated`** (not `migrations`).

**SCRUM-167 direction:** Optionally make the `migrations` → `migrations_validated` mapping explicit in config (e.g. `risk_category_to_validation_key`) so other repos can remap without code forks.

### 3. Registry vs runtime keys

`known_keys = set(config.get("validations", {}).keys())` defines which keys are **first-class** in the YAML registry. Keys that only appear from inference or evidence may still be reported when required or evidenced (`keys_to_report` union).

## TalkBack validation registry (current defaults)

From `ops/release-readiness/config.yaml`:

| Key | Purpose (short) |
|-----|-----------------|
| `auth_session` | Login/session and creator access |
| `upload_extraction` | Upload + extraction pipeline |
| `nav_assets` | Materials tree / asset selection |
| `viewer_materials` | Viewer renders materials |
| `qa_rag` | Q&A / RAG |
| `orchestration` | Orchestration / draft flows |
| *(implicit)* `migrations_validated` | Required when `migrations` risk fires; not always listed under `validations` in YAML but participates in gating |

## Inference lists (current defaults)

When smoke passes, infer keys (subset):

`auth_session`, `upload_extraction`, `qa_rag`, `orchestration`

When E2E passes, infer keys:

`auth_session`, `nav_assets`, `viewer_materials`, `qa_rag`, `orchestration`

Explicit `False` in evidence JSON overrides inference.

## Contract artifact for SCRUM-167

Draft schema (checked into this repo):

- [`docs/contracts/validation-config-v1.schema.json`](../contracts/validation-config-v1.schema.json)

Align loader/parser with TalkBack `config.yaml` structure first; extend only where SCRUM-167 introduces new keys (`evidence_boolean_keys`, etc.).

## Suggested implementation order (SCRUM-167)

1. Add config fields + defaults matching TalkBack behavior (backward compatible).
2. Replace hardcoded tuple in `merge_validations` with config-driven list (same default values).
3. Add unit tests in **release-readiness-core** mirroring `scripts/test_release_readiness_engine.py` cases that touch validations.
4. Run TalkBack golden parity (**SCRUM-172**) before/after to prevent drift.

## References

| Artifact | Location |
|----------|----------|
| TalkBack engine | `talkback/scripts/release_readiness_engine.py` |
| TalkBack engine tests | `talkback/scripts/test_release_readiness_engine.py` |
| TalkBack readiness config | `talkback/ops/release-readiness/config.yaml` |
| PR-risk / readiness spike | [`docs/spikes/SCRUM-166-package-boundary-api-contract.md`](../spikes/SCRUM-166-package-boundary-api-contract.md) |
