# release-readiness-core contracts

This directory contains versioned JSON contracts used by the standalone package.

## Available contracts

### Inputs (consumed by `release-readiness-evaluate`)

- `smoke-input-v1.schema.json` — shape for `--smoke-results`.
- `e2e-input-v1.schema.json` — shape for `--e2e-results`.
- `coverage-input-v1.schema.json` — shape for `--coverage`.
- `pr-risk-input-v1.schema.json` — shape for the optional
  `<output-dir>/pr_risk.json` artifact.

### Output

- `release-readiness-output-v1.schema.json` — shape for
  `release-readiness.json` (the lean machine summary). See
  `docs/reference/outputs.md` for the full field-by-field glossary
  including the larger `report.json` payload.

### Configuration

- `validation-config-v1.schema.json` — shape for `config.yaml`. Note:
  the closed set of top-level keys actually enforced at load time lives
  in `release_readiness_core.readiness_io.KNOWN_TOP_LEVEL_CONFIG_KEYS`;
  the JSON schema is intentionally permissive
  (`additionalProperties: true`) to allow project-specific extensions.

## Versioning policy

- Contract files are immutable once released for a version line.
- Backward-compatible additions use a new minor schema version file.
- Breaking changes require a new major schema version file and migration notes.

## Usage guidance

- Keep schema files in source control and review them like public APIs.
- Reference these contracts from ticket docs and adopter documentation.
- Validate adapter payloads against the relevant schema in tests where practical.
