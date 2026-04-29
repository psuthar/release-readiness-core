# SCRUM-178 — Generalization spike: second-project validation

**Status:** complete
**Author:** automation (Phase B continuation epic run for SCRUM-165)
**Date:** 2026-04-29
**Time-box used:** ~2 hours (well under the 2-day budget; deliverable is the gap list, not a perfect run).

## Goal

Per the ticket, configure `release-readiness-core` against a second, unrelated project and produce a report end-to-end. Surface assumptions hidden in the package before adopters do.

## Setup

A fictional **`todo-api`** (small Flask REST service) was used as the second project. The fixture lives at `examples/second-project/`:

- `config.yaml` — authored from scratch using only `docs/contracts/` and the README. No TalkBack vocabulary.
  - Validation keys: `api_health`, `db_migrations`, `auth_login`, `todo_crud`, `search_filtering`.
  - Risk categories: `db_migrations`, `auth_login`, `search_filtering`, mapped to source paths under `src/todo_api/**`, `migrations/**`, `alembic/**`.
- `evidence/{smoke,e2e,coverage,prod_health}.json` — synthetic CI evidence in the schema shapes documented under `docs/contracts/`.

The package was invoked exactly as in `README.md`:

```bash
cd examples/second-project
uv run --project ../.. release-readiness-evaluate \
  --repo-root . \
  --config config.yaml \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json \
  --prod-health evidence/prod_health.json \
  --empty-diff \
  --output-dir artifacts/release-readiness
```

Result: `PASS, score=100/100, 0 blockers, 0 warnings`.

A negative case was also exercised programmatically by calling `compute_readiness` with `changed_files=['migrations/0001_init.py']` and no evidence — produced `BLOCK` with `validations_required=['db_migrations']`, as expected.

A regression test (`tests/test_second_project_example.py`) drives the CLI against this fixture end-to-end so the example can't silently rot.

## Gap list

Listed in priority order. Each item is independent and could become a follow-up ticket. The package **is** usable today against an unrelated project — these are friction points, not blockers.

### Gap 1 — `risk_category_to_required_validation` schema knob is silently ignored — **RESOLVED in SCRUM-207**

**Severity:** medium (correctness)
**File:** `src/release_readiness_core/readiness_engine.py` (the loop building `validations_required`)
**Schema reference:** `docs/contracts/validation-config-v1.schema.json` documents `risk_category_to_required_validation` as a configurable mapping.

The engine hardcoded `if r == "migrations": validations_required.add("migrations_validated")` and otherwise used identity mapping. It did not read `risk_category_to_required_validation` from config.

In the second-project fixture this happened to work because risk category names were chosen to match validation keys. Any project that needed `auth_endpoints → auth_session` (or anything other than identity / TalkBack's `migrations → migrations_validated`) silently got the wrong required-validation set.

**Resolution (SCRUM-207):** the engine now reads `risk_category_to_required_validation` from config and falls back to identity for unmapped categories. The hardcoded `migrations` case is gone; TalkBack supplies the equivalent mapping in its config. The second-project fixture now demonstrates a non-identity mapping (`schema_changes → db_migrations`).

### Gap 2 — "Production health snapshot not provided (optional)" warning suppresses PASS — **RESOLVED in SCRUM-208**

**Severity:** medium (DX)
**File:** `readiness_engine.py` — `if prod_health is None: warnings.append(...); score -= penalty`

The engine unconditionally added a warning when `prod_health` was missing, even though the message itself said "(optional)". A warning suppresses PASS via `decide_outcome` (PASS requires `score >= pass_threshold AND no warnings`). So projects without a production-health monitoring source had to either ship a stub `prod_health.json` (what the example did originally) or accept a WARN. Same problem applied to coverage.

**Resolution (SCRUM-208):** added the `optional_artifacts` config knob. Declaring an artifact in that list suppresses both the warning and the score penalty when it's absent at run time. The `examples/second-project/` fixture now declares `optional_artifacts: [prod_health]` and the stub `prod_health.json` was deleted; the regression test still observes PASS without it. Default behavior (warning + penalty) is preserved when `optional_artifacts` is omitted, so TalkBack semantics are unchanged.

### Gap 3 — `--smoke-results` and friends resolve from `cwd`, not `--repo-root` — **RESOLVED in SCRUM-209**

**Severity:** low (DX, but easy to trip on)
**File:** `src/release_readiness_core/readiness_evaluate.py`

Relative artifact paths now resolve under `--repo-root` (consistent with how `--config` resolves). Verified by `tests/test_friction_fixes.py::test_evaluate_cli_resolves_artifact_paths_under_repo_root` which drives the CLI from a working directory unrelated to the project root.

### Gap 4 — `validations` table renders even when empty — **RESOLVED in SCRUM-209**

**Severity:** low (cosmetic)
**File:** `readiness_markdown.py`

The renderer now omits the `### Validations` section entirely when `r.validations` is empty.

### Gap 5 — "Validation note: no" in the report header is unexplained — **RESOLVED in SCRUM-209**

**Severity:** low (docs)
**Where:** report header.

The header row is now suppressed when no validation note is present, since the negative case provides no useful signal to adopters who don't use the convention. When a note IS present the row continues to render, with the source label.

### Gap 6 — `DEFAULT_EVIDENCE_BOOLEAN_KEYS` constant still has TalkBack vocabulary — **RESOLVED in SCRUM-209**

**Severity:** low (correctness, latent)
**File:** `readiness_engine.py`

`DEFAULT_EVIDENCE_BOOLEAN_KEYS` is now an empty tuple. Adopters opt in via `evidence_boolean_keys` in config. TalkBack supplies the historic tuple via its config (SCRUM-167) so its behavior is preserved; non-TalkBack projects no longer inherit unrelated defaults.

### Gap 7 — `--empty-diff` is mandatory for non-git use cases, but the help text doesn't say so — **RESOLVED in SCRUM-209**

**Severity:** low (docs)
**File:** `readiness_evaluate.py` arg help.

Help text expanded to describe the non-CI / non-git use case explicitly.

## Outcome

- The package **does** run end-to-end against an unrelated project and produces a PASS report. Generalization basically holds.
- Two gaps (1, 2) are correctness/DX issues that adopters will hit on day one and should be fixed before declaring a v1 stable API.
- Gaps 3–7 are friction items. None block adoption; all warrant follow-up tickets.

## Triage recommendation

Before SCRUM-165 closes, file follow-ups for gaps 1 and 2 at least. Gaps 3–7 can ride along with the documentation tickets (SCRUM-179/180/181/182) since most of them are clarified by good prose.
