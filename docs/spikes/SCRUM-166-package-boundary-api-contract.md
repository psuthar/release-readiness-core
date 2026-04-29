# SCRUM-166 Spike

## Goal

Define the initial `release-readiness-core` package boundary, public API surface, and `pr_risk.json` input contract so extraction work can proceed without interface churn.

## Package Boundary (v0)

In scope for `release-readiness-core`:

- Deterministic readiness engine and report model
- CLI entrypoint for local and CI use
- Input/output contracts and schema docs
- Adapters that transform external evidence into engine-ready validations

Out of scope for `release-readiness-core`:

- TalkBack service runtime, HTTP handlers, and persistence
- TalkBack-specific orchestration scripts
- Hosted workflows and environment-specific deployment logic

## Public API (v0)

Python API:

- `release_readiness_core.engine.ValidationResult`
- `release_readiness_core.engine.ReadinessReport`
- `release_readiness_core.engine.evaluate_release_readiness(results)`

CLI API:

- `release-readiness --input-json '<json-array>'`
- JSON output is printed to stdout and follows the output contract schema.

Stability policy:

- Keep dataclass field names stable within `0.1.x`.
- Additive fields are allowed only when backward-compatible for existing consumers.
- Breaking changes require explicit ticket scope and version bump planning.

## Contract Decisions

`pr_risk.json` contract (input):

- Contract purpose: optional PR-risk signal consumed by adapters before readiness scoring.
- Versioning: contract carries explicit `schema_version`.
- Recommendation enum: `PASS | WARN | BLOCK`.
- Score is numeric and normalized `0..100`.
- Evidence and factors are optional, structured arrays for explainability.

Readiness result contract (output):

- Top-level recommendation: `PASS | WARN | BLOCK`.
- Deterministic counts: `passed`, `warnings`, `blocked`.
- Full validation list includes `key`, `status`, and optional `detail`.

## Open Follow-ups

- Prep for config-driven validation keys: inventory + draft schema in [`docs/prep/SCRUM-167-validation-key-handling.md`](../prep/SCRUM-167-validation-key-handling.md) and [`docs/contracts/validation-config-v1.schema.json`](../contracts/validation-config-v1.schema.json); implement in **SCRUM-167**.
- Bind adapter ownership of `pr_risk.json` ingestion in `SCRUM-171` and `SCRUM-176`.
- Add golden fixture parity checks in `SCRUM-172`.
- Validate second-consumer compatibility in `SCRUM-178`.
