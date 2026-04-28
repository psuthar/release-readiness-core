# release-readiness-core contracts

This directory contains versioned JSON contracts used by the standalone package.

## Available contracts

- `pr-risk-input-v1.schema.json`
  - Input payload contract for PR risk adapter data consumed by core workflows.
- `release-readiness-output-v1.schema.json`
  - Output payload contract for deterministic PASS/WARN/BLOCK readiness results.
- `validation-config-v1.schema.json`
  - Runtime validation/config contract for key handling and policy wiring.

## Versioning policy

- Contract files are immutable once released for a version line.
- Backward-compatible additions use a new minor schema version file.
- Breaking changes require a new major schema version file and migration notes.

## Usage guidance

- Keep schema files in source control and review them like public APIs.
- Reference these contracts from ticket docs and adopter documentation.
- Validate adapter payloads against the relevant schema in tests where practical.
