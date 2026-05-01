# release-readiness-core contracts

This directory contains versioned JSON contracts used by the standalone package.

## Available contracts

### Inputs (consumed by `release-readiness-evaluate`)

- `smoke-input-v1.schema.json` — shape for `--smoke-results`.
- `e2e-input-v1.schema.json` — shape for `--e2e-results`.
- `coverage-input-v1.schema.json` — shape for `--coverage`.
- `pr-risk-input-v1.schema.json` — shape for the optional `<output-dir>/pr_risk.json` artifact.

### Output

- `release-readiness-output-v1.schema.json` — shape for `release-readiness.json` (the lean machine summary). See `docs/reference/outputs.md` for the full field-by-field glossary including the larger `report.json` payload.

### Unified PR gate (consumed and produced by the new combiner CLIs)

- `pr-gate-summary-v1.schema.json` — shape for `pr-gate-summary.json`, the deterministic merge of `pr-risk.json` + `release-readiness.json` produced by `release-readiness-combine`. Carries `final_gate.{status, confidence, summary, workflow_should_fail}` plus the input snapshots and the deduplicated `required_actions[]`.
- `pr-gate-check-v1.schema.json` — shape for `pr-gate-check.json`, the GitHub Checks API payload produced by `release-readiness-check-payload`. Read by `actions/github-script` to call `github.rest.checks.create` / `checks.update`.

**Combiner precedence (deterministic):**

| Inputs | `final_gate.status` |
|---|---|
| Either input is BLOCK (or input parse failed) | BLOCK |
| Either input is WARN, neither is BLOCK | WARN |
| Both inputs are PASS | PASS |

**Status → Checks-API mapping:**

| `final_gate.status` | `check_conclusion` | `workflow_should_fail` |
|---|---|---|
| PASS | `success` | false |
| WARN | `action_required` | false |
| BLOCK / parse error | `failure` | true |

`action_required` keeps the workflow green but blocks GitHub's `mergeable_state`. `workflow_should_fail` is the canonical signal a calling workflow's enforcement step reads to decide whether to exit non-zero — it is set independently of `check_conclusion` (so adopters who don't publish a Check can still enforce).

### Configuration

- `validation-config-v1.schema.json` — shape for `config.yaml`. Note: the closed set of top-level keys actually enforced at load time lives in `release_readiness_core.readiness_io.KNOWN_TOP_LEVEL_CONFIG_KEYS`; the JSON schema is intentionally permissive (`additionalProperties: true`) to allow project-specific extensions.

## Versioning policy

- Contract files are immutable once released for a version line.
- Backward-compatible additions use a new minor schema version file.
- Breaking changes require a new major schema version file and migration notes.

## Usage guidance

- Keep schema files in source control and review them like public APIs.
- Reference these contracts from ticket docs and adopter documentation.
- Validate adapter payloads against the relevant schema in tests where practical.
