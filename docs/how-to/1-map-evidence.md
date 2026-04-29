# Map CI evidence to readiness validations

This guide is the deepest part of adopting `release-readiness-core`. It
explains how the engine decides whether a given **validation key** is
satisfied — i.e., whether a given guarantee about your release has been
demonstrated by CI.

If you only read one section, read **§3 Two ways to evidence a key** —
that's where almost all adopter friction lives.

> **Worked example throughout:** the `examples/second-project/` fixture
> in this repo. Its `config.yaml` declares the validation keys
> referenced below, and `evidence/{smoke,e2e,coverage,prod_health}.json`
> contains the exact JSON shapes the engine consumes.

---

## 1. What is a validation key?

A **validation key** is a short, opinionated name for a guarantee your
release should provide. Examples:

- `auth_login` — login flow returns a valid token.
- `db_migrations` — schema migrations applied and verified.
- `todo_crud` — full create/read/update/delete cycle of a core entity.

Validation keys live under `validations:` in `config.yaml`:

```yaml
validations:
  auth_login:
    description: Login flow issues valid tokens for known users.
  db_migrations:
    description: Database migrations applied and verified in CI.
  todo_crud:
    description: Create/read/update/delete a todo end-to-end.
```

The `description` is human-readable and surfaces in remediation tables
when the validation is required but missing.

A validation is **required** for a given run when changed files match a
risk pattern that maps to it (see `risk_from_paths` in the schema and
`docs/how-to/2-tune-scoring.md`). A validation that's *not required* but
has evidence still appears in the report — labeled `not_required` —
giving reviewers extra signal without gating.

---

## 2. The two evidence sources

The engine reads two artifact types as the canonical sources of
validation evidence:

| Artifact | CLI flag | What goes in it |
|---|---|---|
| Smoke results | `--smoke-results path/to/smoke.json` | High-level pass/fail of the smoke suite, plus optional per-key booleans. |
| E2E results | `--e2e-results path/to/e2e.json` | Detailed per-spec pass/fail, retry counts, and (optionally) per-validation booleans. |

Both are plain JSON. Both are optional — but a missing artifact triggers
a soft-penalty warning that suppresses PASS.

`coverage` and `prod_health` are also consumed but are not
validation-evidence sources; they affect the score, not the validation
map.

---

## 3. Two ways to evidence a key

When the engine builds its `val_map: dict[str, bool]`, it merges
two channels. Both can be active in the same run.

### 3a. Explicit JSON validation booleans

In your smoke or e2e JSON, include either a top-level boolean or a
nested `validations` block:

```json
{
  "status": "passed",
  "passed": true,

  "auth_login": true,

  "validations": {
    "todo_crud": true,
    "search_filtering": false
  }
}
```

How the engine merges this:

| Where the value lives | When the engine treats it as evidence |
|---|---|
| Top-level boolean — *only* keys named in `evidence_boolean_keys` | `true` → satisfied. Other values ignored. |
| Nested `validations: { key: true \| false }` | `true` → satisfied. `false` → **explicitly failed**, cannot be re-promoted by inference. |

`evidence_boolean_keys` is the gate: top-level booleans whose names
aren't in that list are ignored. This prevents accidental collision
with arbitrary stats fields. A typical config:

```yaml
evidence_boolean_keys:
  - api_health
  - db_migrations
  - auth_login
  - todo_crud
  - search_filtering
```

> **Important:** if you omit `evidence_boolean_keys` entirely the engine
> falls back to a TalkBack-flavored default tuple. Always set this
> explicitly for non-TalkBack projects.

**Explicit `false` always wins.** Inference cannot upgrade a
`validations: { auth_login: false }` to `true`.

### 3b. Pass-implies inference (`infer_validations_when_pass`)

For projects whose smoke / e2e suites don't emit per-key booleans,
inference lets you say "if the whole smoke suite passes, treat these
keys as satisfied."

```yaml
infer_validations_when_pass:
  smoke:
    - api_health
  e2e:
    - auth_login
    - todo_crud
    - search_filtering
```

The engine sets a key to `true` only when the corresponding suite is
*actually passing* (per `_smoke_passed` / `_e2e_passed`) and the key
isn't already marked `false` by an explicit JSON entry.

**When to use which:**

- Use **3a (explicit)** when your test runner can directly emit per-key
  booleans (e.g. you own the smoke harness, or you wrap Playwright with
  a custom converter).
- Use **3b (inference)** when your runner can only emit overall
  pass/fail. This is the simplest path for new adopters.
- You can mix: declare `evidence_boolean_keys` and
  `infer_validations_when_pass` in the same config. Explicit `false`
  values always trump inference; explicit `true` is equivalent to
  inferred `true`.

---

## 4. Adapter CLIs — convert common CI artifacts

Three adapters convert popular tool-specific outputs to the readiness
JSON shapes:

| Adapter | Reads | Writes | When to use |
|---|---|---|---|
| `playwright-to-readiness` | Playwright JSON reporter | `e2e.json` | You use Playwright. |
| `junit-to-readiness` | JUnit XML | `e2e.json` (or `smoke.json`) | You use Cypress, Jest, pytest, Mocha, Karma, or anything that emits JUnit XML. |
| `lcov-to-readiness` | LCOV `info` text | `coverage.json` | You generate LCOV (most JS / Python / Go coverage tooling does). |

You don't need adapters at all — you can hand-write JSON in the
documented shapes. The adapters exist because most teams already have
runners that emit one of the formats above.

### `junit-to-readiness`

```bash
junit-to-readiness \
  --input test-results.xml \
  --output evidence/e2e.json \
  --validation-map ops/release-readiness/validation_map.yaml
```

JUnit's `<testcase>` elements give us classnames like
`auth.LoginFlow` and test names like `logs_in`. The validation map
matches against either:

- the full classname (`auth.LoginFlow`)
- the last segment of the classname (`LoginFlow`)
- the test name (`logs_in`)

So you can group tests by suite (most common) or by individual name as
needed:

```yaml
auth_login:
  - LoginFlow
  - oauth.OAuthCallback   # full classname when LoginFlow alone is too broad
todo_crud:
  - todo-crud-create
  - todo-crud-edit
  - todo-crud-delete
```

`<failure>` and `<error>` both count as failures; `<skipped>` is
counted but doesn't fail the run.

### `lcov-to-readiness`

```bash
lcov-to-readiness \
  --input coverage/lcov.info \
  --output evidence/coverage.json \
  --baseline-percent 85
```

`--baseline-percent` is the threshold below which the engine fires the
`coverage_regression` warning (and applies the configured penalty). Omit
it to ship coverage as informational without a regression check.

### `playwright-to-readiness`

If your project uses Playwright, the `playwright-to-readiness` CLI
converts Playwright's JSON reporter output into the e2e schema this
engine expects:

```bash
playwright-to-readiness \
  --input playwright-results.json \
  --output e2e_results.json \
  --validation-map ops/release-readiness/e2e_validation_map.yaml
```

The validation map is **project-supplied** YAML — a flat mapping from
validation key to a list of test file *stems*:

```yaml
auth_login:
  - login-flow
  - oauth-callback
todo_crud:
  - todo-create
  - todo-edit
  - todo-delete
search_filtering:
  - search-results
```

### Stem matching rules

A "stem" is the test file name with spec extensions stripped. By
default the converter strips `.ts`, `.js`, `.mjs`, `.e2e` (iteratively,
so `login-flow.e2e.ts` collapses to `login-flow`). Override with
`--spec-extensions ts,js,mjs,spec,e2e`.

A test "belongs to" a validation group when its stripped stem appears
in that group's list. A validation is `true` iff every test belonging
to it ran and passed; `false` if any test in the group failed. The key
is **omitted** when no tests from the group ran at all — which keeps
quiet runs from looking falsely passing.

Without a `--validation-map`, the converter still produces a valid
`e2e_results.json` (counts, failures, status) — but the `validations`
object will be empty. You'll then need to use
`infer_validations_when_pass.e2e` if you want validation keys
satisfied.

---

## 5. Special validations that need explicit evidence

Two validation keys behave differently from the rest because they
encode hard-to-infer guarantees:

### `migrations_validated`

The engine has a hard-coded shortcut: a `--migration-validated` CLI
flag sets `val_map["migrations_validated"] = true`. Use this when CI
has run migrations against a real DB outside the smoke/e2e suites
(e.g. an Alembic dry-run in a separate job).

There is also a `risk_from_paths` rule (see `tune-scoring.md`) that
auto-requires `migrations_validated` whenever changes touch
`migrations/**`. The CLI flag is the easiest way to satisfy that
requirement.

### Anything you've named in `risk_category_to_required_validation`

When risk patterns trigger, the engine builds a list of required
validations. The mapping is config-driven — declare your risk
categories under `risk_from_paths` using whatever vocabulary fits the
*change* (e.g. `schema_changes`, `auth_endpoints`), then map those
categories to the validation keys that prove the change is safe:

```yaml
risk_from_paths:
  - categories: [schema_changes]
    patterns: ["migrations/**", "alembic/**"]
  - categories: [auth_endpoints]
    patterns: ["src/auth/**"]

risk_category_to_required_validation:
  schema_changes: db_migrations
  auth_endpoints: auth_login
```

Risk categories not listed in
`risk_category_to_required_validation` fall back to identity mapping
(the validation key has the same name as the risk category), which is
fine when your vocabulary is consistent across the two.

---

## 6. Worked example

Walking through `examples/second-project/` end-to-end.

**`config.yaml` excerpt:**

```yaml
validations:
  api_health:
    description: Liveness and readiness endpoints respond with 200.
  auth_login:
    description: Login flow issues valid tokens for known users.
  todo_crud:
    description: Create/read/update/delete a todo end-to-end.

evidence_boolean_keys:
  - api_health
  - db_migrations
  - auth_login
  - todo_crud
  - search_filtering

infer_validations_when_pass:
  smoke:
    - api_health
  e2e:
    - auth_login
    - todo_crud
    - search_filtering
```

**`evidence/smoke.json`:**

```json
{
  "status": "passed",
  "passed": true,
  "api_health": true
}
```

`api_health` flows through *both* paths — it's in
`evidence_boolean_keys` (top-level boolean satisfies it directly) and in
`infer_validations_when_pass.smoke` (smoke pass would also satisfy it).
Either alone suffices.

**`evidence/e2e.json`:**

```json
{
  "status": "passed",
  "failed_count": 0,
  "total_count": 12,
  "retries": 0,
  "failures": [],
  "validations": {
    "auth_login": true,
    "todo_crud": true,
    "search_filtering": true
  }
}
```

E2E uses the **explicit nested `validations`** form. `auth_login`,
`todo_crud`, `search_filtering` are all satisfied directly. The
`infer_validations_when_pass.e2e` list happens to name the same keys —
inference would also satisfy them via the overall pass — but the
explicit booleans are authoritative.

**Run:**

```bash
cd examples/second-project
release-readiness-evaluate \
  --repo-root . \
  --config config.yaml \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json \
  --prod-health evidence/prod_health.json \
  --empty-diff \
  --output-dir artifacts/release-readiness
```

**Result:** `PASS, score=100/100`. The validations panel shows
`api_health`, `auth_login`, `search_filtering`, `todo_crud` as
`not_required` (no risk patterns triggered for this run, so they're
informational). To see them as `satisfied`, change a file matching a
risk pattern (e.g. `migrations/foo.sql`) and rerun without
`--empty-diff`.

---

## 7. Debugging an unexpected validation status

When the report says a validation is `missing` or `not_evaluated`:

1. **`missing`** — the key was required (a risk pattern triggered) and no evidence satisfied it. Check both channels: is the key in `evidence_boolean_keys` with a `true` in your smoke/e2e JSON, or does `infer_validations_when_pass` cover it?
2. **`not_evaluated`** — the key was required but no smoke or e2e artifact was provided at all. The package can't disprove or prove it. Provide at least one artifact, even a stub.
3. **`not_required`** — the key was satisfied, but no risk pattern required it. Informational; not a problem.
4. **Key not appearing at all** — the key isn't in `validations:` in your config and isn't required and isn't evidenced. Add it to `validations:` if you want it tracked.

The `report.json` file carries the full `val_map` under
`validations` — check that to see what the engine actually computed
before the rendering layer trimmed it.

---

## 8. Cross-references

- `docs/how-to/0-quickstart.md` — broader walkthrough; minimum config.
- `docs/how-to/2-tune-scoring.md` — penalties, thresholds, and the
  `risk_from_paths` block that decides which validations become
  *required*.
- `docs/contracts/validation-config-v1.schema.json` — full schema for
  every `config.yaml` field referenced here.
