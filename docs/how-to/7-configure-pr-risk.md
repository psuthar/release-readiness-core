# How to configure PR Risk for your project

`release-readiness-pr-risk` is the deterministic per-PR risk scorer that ships with `release-readiness-core`. Out of the box it produces a generic, language-agnostic score: domain hits all classify to `other`, and only generic gates fire (CI fetch depth, PR review summary, workflow / config validation, add tests / evidence, intent alignment, scattered review plan, test proximity, hotspot regression).

Most projects want more: a PR that touches `src/api/` should fire an "API E2E" gate, a PR that touches `prisma/migrations/` should require a rollback plan, etc. This guide walks you from `release-readiness-init` to a running configured CLI that produces project-specific scores.

References:
- Schema: `docs/contracts/pr-risk-config-v1.schema.json`
- Vocabulary reference: `docs/reference/pr-risk-config.md`
- Examples: `examples/pr-risk/python-service.yaml`, `examples/pr-risk/node-service.yaml`

## 1. Generate the starter

```sh
release-readiness-init .
```

Among the files written is `ops/release-readiness/pr-risk-config.yaml` — a commented-out skeleton that documents the closed-set predicate vocabulary inline.

The starter is valid as-is (the loader accepts a config that only declares `version: 1`). Until you fill it in, `release-readiness-pr-risk` continues to emit only generic gates.

## 2. Declare your domains

Domains group changed paths into product areas. The first matching domain (in declared order) wins; paths that match no domain classify to `other`.

```yaml
version: 1

domains:
  - id: api
    label: api
    patterns:
      - { prefix: "src/myproject/api/" }
      - { contains: "/handlers/" }

  - id: db
    label: db
    patterns:
      - { prefix: "src/myproject/db/" }
      - { prefix: "alembic/versions/" }
      - { contains: "/models/" }
```

Pattern types (closed set):

| Type | Matches when |
|---|---|
| `prefix: "X"` | path starts with `X` |
| `contains: "X"` | `X` appears anywhere in path |
| `exact: "X"` | path equals `X` (lowercased) |
| `endswith: "X"` | path ends with `X` |
| `any_contains: [a, b]` | any of the substrings appears |
| `and: [<pat>, <pat>]` | every subpattern matches |

Order matters when domains overlap. A path under `src/api/handlers/login.go` matches both an `auth` domain (with `contains: login`) and an `api` domain (with `prefix: src/api/`). Put the more specific domain first.

## 3. Pick sensitive domains

The `tests_missing` factor fires when a diff touches "sensitive" code without any test files. Sensitivity is per-project — for one team migrations and auth are sensitive; for another, the analytics pipeline is.

```yaml
sensitive_domains:
  - api
  - db
```

If you don't list a domain here, a diff that only touches that domain's code never fires the `tests_missing` factor (no penalty for "code without tests"). The `add_tests_or_evidence` gate may still fire if a generic factor like `diff_large` is present.

## 4. Declare gates

Gates are the heart of the config. Each gate fires when its `applies_when` predicates match (implicit AND across the list); deduplicated by `id` at emit time.

```yaml
gates:
  - id: api_e2e_gate
    title: "Exercise API endpoints touched by this change"
    priority: high
    fix_type: test
    applies_when:
      - { risk_band: [high, critical] }
      - { factor_id: domain_api }
    applies_when_extra: "API endpoints changed"
    validation_line: "test: API endpoints exercised (E2E or contract test)"
    checklist:
      - text: "Run API E2E suite covering changed endpoints."
        by_evidence_level:
          none: "Add or run API E2E covering this endpoint before merge."
          unit: "Confirm unit tests pass; run API E2E for affected endpoints before merge."
      - "Verify request/response shapes match the API contract."
    evidence:
      template: test_domain
      args:
        domain: api
```

Predicate vocabulary (closed set):

| Predicate | Fires when |
|---|---|
| `factor_id: <id>` or `factor_id: [<id>, ...]` | Factor present (any-of for list) |
| `not_factor_id: <id>` or list | Factor absent |
| `risk_band: [low|medium|high|critical, ...]` | Current band ∈ list |
| `not_risk_band: [...]` | Current band ∉ list |
| `domain_factor: <domain>` | Alias for `factor_id: domain_<domain>` |
| `intent_mismatch: true` | PR title/body keywords don't match the diff |
| `concentration_mode: scattered` plus `min_file_count` | Scattered diff with N+ files |
| `hotspots_present: true` | Recent commits cluster on a path prefix |
| `proximity_distant_with_sensitive: true` plus `min_non_test_files` and `domains` | Distant tests + sensitive domain hit |

Evidence detector templates (closed set):

| Template | What it checks |
|---|---|
| `signal_check` | A named Signals field is empty (PASS) / populated (FAIL). `args.signal_field`. |
| `intent_strength` | PR description quality (strong / weak / unknown). |
| `validation_note` | `Validation:` note in commit message. |
| `test_domain` | Test files for `args.domain` (E2E → PASS; unit-only → NOT_EVALUATED; none → MISSING). |
| `migrations` | E2E migration tests, validation note + migration files, or naked migration files. |
| `add_tests` | Style-only note, adequate proximity, ≥30% test LOC ratio, or "no tests" → MISSING. |
| `intent_alignment` | Mismatch → FAIL; aligned → PASS. |
| `intent_aligned_or_weak` | Strong + aligned → PASS; weak → MISSING. |
| `proximity` | Behavioral coverage adequate / shallow / distant. |
| `hotspot` | Validation note when hotspots are present. |

## 5. Validate with doctor

Once you've authored a config, run the doctor to catch typos, malformed predicates, references to undeclared domains, and unknown evidence templates:

```sh
release-readiness-doctor --pr-risk-config ops/release-readiness/pr-risk-config.yaml
```

Doctor reports:
- Schema-level errors (unknown top-level keys, duplicate gate IDs, malformed predicates).
- Closed-set violations (gate `evidence.template` not in the supported list).
- Semantic mistakes:
  - `evidence.args.domain` references a domain that isn't declared.
  - `applies_when.domain_factor: <X>` when `<X>` isn't in `domains`.
  - `proximity_distant_with_sensitive.domains` references undeclared domains.
  - `sensitive_domains` references undeclared domains.

## 6. Run the CLI

Once the config validates, run the scorer and inspect the output:

```sh
release-readiness-pr-risk --base-ref origin/main \
  --config ops/release-readiness/pr-risk-config.yaml
```

The CLI emits `pr_risk.json` (full result), `pr-risk.json` (lean semantic summary for CI gates), and `pr_risk.md` (human-readable report) under `artifacts/release-readiness/`.

## Reference

- Full predicate vocabulary, template list, and field semantics: [`docs/reference/pr-risk-config.md`](../reference/pr-risk-config.md)
- Schema (machine-checkable): [`docs/contracts/pr-risk-config-v1.schema.json`](../contracts/pr-risk-config-v1.schema.json)
- Worked examples: [`examples/pr-risk/python-service.yaml`](../../examples/pr-risk/python-service.yaml), [`examples/pr-risk/node-service.yaml`](../../examples/pr-risk/node-service.yaml)
- Architecture decisions behind the decoupling: [`docs/spikes/pr-risk-port-decisions.md`](../spikes/pr-risk-port-decisions.md)
