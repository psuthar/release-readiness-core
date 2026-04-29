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

### Gap 3 — `--smoke-results` and friends resolve from `cwd`, not `--repo-root`

**Severity:** low (DX, but easy to trip on)
**File:** `src/release_readiness_core/readiness_evaluate.py` — `read_json(args.smoke_results)` is called with the raw `Path` argument.

Running from the package root with `--repo-root examples/second-project --smoke-results evidence/smoke.json` produces "Smoke results artifact missing" because the artifact path is interpreted relative to `cwd` (`/code/release-readiness-core`), not `examples/second-project`. The CLI silently produces a BLOCK and the user has to read source to figure out why.

The README example sidesteps this because `--repo-root .` makes `cwd == repo-root`. Once you try to drive the package from outside the project tree, behavior diverges from intuition.

**Suggested fix:** when an artifact path is relative, resolve it under `--repo-root` (consistent with how `--config` is resolved). Or add an explicit warning when a path argument was provided but the file isn't found.

### Gap 4 — `validations` table renders even when empty

**Severity:** low (cosmetic)
**File:** `readiness_markdown.py`

The first run (no inferred validations) rendered:

```
### Validations

| Key | Status |
|-----|--------|
```

— an empty table with no rows. Empty sections should be omitted or replaced with "(none)" for consistency with the "Risks from changed paths" section.

### Gap 5 — "Validation note: no" in the report header is unexplained

**Severity:** low (docs)
**Where:** report header.

Adopters reading their first report won't know what a "Validation note" is or what `yes` would mean. The concept is documented obliquely (commit-message convention), but not on the report itself or in the README quickstart.

**Suggested fix:** tooltip-style footnote, or just remove this row from the default header until the docs how-to (SCRUM-180/181) explains the concept.

### Gap 6 — `DEFAULT_EVIDENCE_BOOLEAN_KEYS` constant still has TalkBack vocabulary

**Severity:** low (correctness, latent)
**File:** `readiness_engine.py` — the `("auth_session", "upload_extraction", "nav_assets", "viewer_materials", "qa_rag", "migrations_validated")` tuple.

If a config omits `evidence_boolean_keys` entirely, the engine falls back to TalkBack's keys. For a non-TalkBack project this is benign-ish (their evidence won't have those top-level booleans, so nothing happens), but it bakes TalkBack vocabulary into the "library defaults." A non-TalkBack adopter who forgets to set `evidence_boolean_keys` and uses keys that happen to collide ("auth_session" is plausible) will get unintended behavior.

**Suggested fix:** make the default empty tuple (`()`); require config to opt in. TalkBack supplies the list explicitly via SCRUM-167 anyway.

### Gap 7 — `--empty-diff` is mandatory for non-git use cases, but the help text doesn't say so

**Severity:** low (docs)
**File:** `readiness_evaluate.py` arg help.

Without `--empty-diff`, the package shells out to `git diff <base-ref> -- <repo-root>` to compute changed files. If the project isn't a git repo, or if the user is running against a checked-out fixture, this produces empty changed-files silently (or errors, depending on git's mood). The flag is described only as "Treat changed-files list as empty (skip git diff)"; there's no hint that this is the right flag for "I'm not running this inside git CI."

**Suggested fix:** README should call out `--empty-diff` for non-CI/local invocations; help text should mention it as the alternative path.

## Outcome

- The package **does** run end-to-end against an unrelated project and produces a PASS report. Generalization basically holds.
- Two gaps (1, 2) are correctness/DX issues that adopters will hit on day one and should be fixed before declaring a v1 stable API.
- Gaps 3–7 are friction items. None block adoption; all warrant follow-up tickets.

## Triage recommendation

Before SCRUM-165 closes, file follow-ups for gaps 1 and 2 at least. Gaps 3–7 can ride along with the documentation tickets (SCRUM-179/180/181/182) since most of them are clarified by good prose.
