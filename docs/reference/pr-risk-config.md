# PR Risk config reference

Source of truth: [`docs/contracts/pr-risk-config-v1.schema.json`](../contracts/pr-risk-config-v1.schema.json).
Walkthrough: [`docs/how-to/7-configure-pr-risk.md`](../how-to/7-configure-pr-risk.md).

The closed sets below match what the loader (`src/release_readiness_core/pr_risk/_config.py`) accepts, what the gate evaluator (`src/release_readiness_core/pr_risk/actions.py`) implements, and what the detector registry (`src/release_readiness_core/pr_risk/_evidence_templates.py`) ships.

## Top-level keys

| Key | Type | Purpose |
|---|---|---|
| `version` | int (required) | Currently `1`. The loader rejects other versions. |
| `domains` | list of `Domain` | Path → domain mapping. First match wins; `other` is the fallback. |
| `sensitive_domains` | list of domain ids | Domains whose changes (without test files) fire the `tests_missing` factor. |
| `gates` | list of `Gate` | Pre-merge gates. Loop-evaluated against current factors / risk band / signals / context. |

## Path-pattern predicates (in `domains[].patterns`)

Exactly one primary key per pattern; `and` is recursive.

| Pattern | Matches when |
|---|---|
| `{ prefix: "X" }` | path starts with `X` (lowercased) |
| `{ contains: "X" }` | `X` appears anywhere in the path |
| `{ exact: "X" }` | path equals `X` |
| `{ endswith: "X" }` | path ends with `X` |
| `{ any_contains: [a, b, ...] }` | any substring appears |
| `{ and: [<pat>, <pat>, ...] }` | every subpattern matches (≥2 required) |

## Gate `applies_when` predicates

Implicit AND across the list. Exactly one primary key per predicate.

| Predicate | Semantics | Optional args |
|---|---|---|
| `factor_id: <id>` or `factor_id: [<id>, ...]` | Factor `<id>` is present in the current diff (any-of for list). | — |
| `not_factor_id: <id>` or list | Factor is absent. | — |
| `risk_band: [low|medium|high|critical, ...]` | Risk band ∈ list. | — |
| `not_risk_band: [...]` | Risk band ∉ list. | — |
| `domain_factor: <domain>` | Alias for `factor_id: domain_<domain>`. | — |
| `intent_mismatch: true|false` | `insights.intent.mismatch` matches. | — |
| `concentration_mode: <mode>` | `insights.concentration.mode == <mode>`. | `min_file_count` (`s.file_count >= N`) |
| `hotspots_present: true|false` | `len(insights.hotspots) > 0` matches. | — |
| `proximity_distant_with_sensitive: true|false` | `insights.proximity.mode == "distant"` AND non-test-files threshold AND any of `domains` has hits. | `min_non_test_files`, `domains` |

## Risk bands

`low | medium | high | critical`. Computed by `score.band()` from the final score.

## Gate `evidence.template` (closed set)

Each template produces a `ValidationEvidence` with status `pass | missing | unknown | not_evaluated | fail`.

| Template | Required args | Returns PASS when | Returns MISSING when | Returns FAIL when | Returns NOT_EVALUATED when | Returns UNKNOWN when |
|---|---|---|---|---|---|---|
| `signal_check` | `signal_field` | The named field is empty/falsy. | — | The named field is non-empty. | — | — |
| `intent_strength` | — | Intent strength is `strong`. | Intent strength is `weak`. | — | Intent strength is `unknown` or other. | No context insights. |
| `validation_note` | — | Commit has a `Validation:` line. | — | — | No validation note. | — |
| `test_domain` | `domain` | E2E tests touch the domain. | No tests touch the domain. | — | Unit-only tests touch the domain. | — |
| `migrations` | — | E2E migrations tests OR validation note + migration files. | Migration files changed but no evidence. | — | — | No migration files. |
| `add_tests` | — | Style-only / adequate behavioral coverage / ≥30% test-LOC ratio. | No test files. | — | Tests present but coverage shallow / depth unconfirmed. | — |
| `intent_alignment` | — | Intent aligned. | — | Intent mismatch (with detail). | Intent neither aligned nor mismatched. | No context insights. |
| `intent_aligned_or_weak` | — | Strong + aligned. | Weak intent. | — | Other / unknown. | No context insights. |
| `proximity` | — | Behavioral coverage adequate. | Distant + unknown coverage. | — | Other proximity / coverage combinations. | No context insights. |
| `hotspot` | — | Validation note present. | — | — | No validation note. | — |

## Gate variants

A gate may carry a `variants:` list. Each variant has a `when:` matcher and overrides for `title`, `applies_when_extra`, and `checklist`. Today the matcher supports `risk_band` and `not_risk_band`; the first matching variant wins.

```yaml
- id: add_tests_or_evidence
  title: "Add/update tests before merge"
  applies_when: [{ factor_id: tests_missing }]
  variants:
    - when: { risk_band: [high, critical] }
      title: "Add/update tests (or record evidence) before merge"
      applies_when_extra: "sensitive code changed without any test file changes in this diff"
```

## Checklist text overrides

Checklist items can be either plain strings or objects with overrides:

| Field | Overrides when |
|---|---|
| `text` | Default text (always required). |
| `by_evidence_level: { none|unit|e2e: <text> }` | The gate's primary domain has matching test coverage. |
| `by_validation_note: <text>` | The commit message includes a `Validation:` note. |

## Adopter escape hatch

`PRRiskRuntime.register_detector(template_name, fn)` lets an adopter plug in a custom callable for a template name. The callable signature is `(action_id: str, label: str, args: dict, result: Result) -> ValidationEvidence`. This is for adopters who fork the closed set in their own runtime and ship gates that reference the new template name; the schema's enum on `evidence.template` rejects unknown names at load time, so this path is programmatic-only.
