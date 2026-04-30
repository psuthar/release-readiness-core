# PR Risk Port — Locked Decisions

Status: Ratified at the start of the pr_risk port (Phase 0).
Scope: Decisions that constrain the entire Go→Python port. Anything not
covered here is open and should be raised before introducing variance.

The Go reference is `talkback/internal/prrisk` + `talkback/cmd/prrisk` at
report version `v2.8`. Files cited below refer to that tree.

---

## 1. Parity contract

**Bar.** For every captured fixture, the Python implementation must produce:

| File | Comparison | Tolerance |
|------|------------|-----------|
| `pr-risk.json` (lean semantic) | byte-identical after `jq -S` canonicalization | none |
| `pr_risk.json` (full result) | structural deep-equal across every field | none on numbers; ordering matches Go |
| `pr_risk.md` (markdown) | structural diff | whitespace-only differences allowed; no semantic deltas |

A fixture is **passing** only if all three comparisons hold. Markdown
whitespace tolerance exists because rendering libraries differ; semantic
content (every score, every list item, every line label) must match.

The **report version field** stays at `v2.8` throughout the port. We bump
to `v2.9` only after the Go binary is retired (out of scope for this Epic).

## 2. Rounding

Go's `math.Round` is **half-away-from-zero** (`Round(0.5) == 1`,
`Round(-0.5) == -1`, `Round(2.5) == 3`). Python's built-in `round()` uses
**banker's rounding** (`round(2.5) == 2`).

Decision: every `math.Round` site in Go is mirrored in Python by
`release_readiness_core.pr_risk._round.round_half_away`. The helper is
parity-tested in `tests/pr_risk/test_round.py` against the boundary cases
that appear in score computation.

Affected Go sites identified at port time (non-exhaustive; verify per file
when porting):
- `score.go` final score rounding
- `categories.go` test_confidence_score integer cast
- `floors.go` floor min computation
- `semantic_json.go` `score` field (cast to integer in places)

If a Go site uses an integer cast (`int(x + 0.5)` or `math.Floor(x+0.5)`)
rather than `math.Round`, the Python port mirrors *that* operation, not
the helper. Read each site individually before porting.

## 3. Sort and order

Go map iteration is unordered. The Go scorer sorts before output at every
site where order is observable. Python `dict` preserves insertion order
but **the Python port must replicate every Go-side sort** rather than relying on
insertion order. Audited sort sites (verify per file when porting):

- `semantic_json.go` `topFactorLabels` — sort risk factors by points desc, then label asc, take top 5
- `actions.go` `SortRequiredActions` — sort by priority then ID
- `mitigate.go` deduped action lists
- `routing.go` `joinCommaSorted` — comma-join sorted strings
- `report.go` markdown table emit — factors sorted by points desc

Tie-breaking rule: when Go sorts by a primary key with ties, the Python
port uses the same secondary key. Where Go uses `sort.SliceStable`, Python
uses `sorted(..., key=...)` (Python `sorted` is stable, matching). Where
Go uses `sort.Slice` (unstable), the Python port adds an explicit
secondary key to make the order deterministic.

## 4. Float comparison

Both Go and Python use IEEE-754 doubles. Within a single arithmetic
sequence the operations match exactly when:
- the same rounding helper is used (see §2)
- multiplication/addition order is preserved
- no intermediate string round-tripping is introduced

Decision: parity tests assert **exact equality** on all numeric fields
(`==`). Any near-but-not-equal failure is a bug to fix at the source, not
to paper over with `pytest.approx`.

## 5. Package layout

```
src/release_readiness_core/pr_risk/
  __init__.py
  _round.py         Half-away-from-zero helper.
  cli.py            Phase 0: stub. Phase 4: full CLI body.
  version.py        VERSION=2, VERSION_MINOR=8.
  # lands: types.py, classify.py, gitdiff.py, floors.py, interpret.py, mitigate.py
  # lands: reducers.py, _context_bridge.py, context/ subpackage
  # lands: score.py, categories.py, policy.py
  # lands: actions.py, evidence.py, validations.py, routing.py,
  #                  integrations.py, report.py, semantic_json.py
```

Subpackage `context/` mirrors `internal/prrisk/context/` exactly:
`types.py`, `input.py`, `analyze.py`, `proximity.py`, `concentration.py`,
`hotspots.py`, `intent.py`.

Public API is reachable from `release_readiness_core.pr_risk` at the top
level for the entry-point function and version constants. Every other
symbol is reached via its module path (no flat re-exports — the package
is large enough that flat exports invite collisions).

## 6. CLI

Entry point name: `release-readiness-pr-risk` (registered in `pyproject.toml`).

Flags mirror `cmd/prrisk` exactly:

| Flag | Default | Notes |
|------|---------|-------|
| `--repo-root` | `.` | Path to git worktree |
| `--base-ref` | `origin/main` | git ref to diff against |
| `--output-dir` | `artifacts/release-readiness` | dir for `pr_risk.json`/`pr_risk.md` |
| `--jira-key` | `None` | optional, env fallback `PRRISK_JIRA_ISSUE_KEY` |

Environment variables consumed (mirrored from Go):
- `PRRISK_JIRA_ISSUE_KEY`
- `PRRISK_PR_TITLE`
- `PRRISK_PR_BODY`

Output files (mirrored from Go):
- `<output-dir>/pr_risk.json` — full Result struct
- `<output-dir>/pr_risk.md` — markdown report
- `<output-dir>/../pr-risk.json` — semantic file (parent-of-output-dir convention preserved)

Exit codes: `0` on successful run, non-zero on git/IO errors. The CLI
itself does **not** gate on the computed `merge_recommendation` — that's
the caller's job in CI.

## 7. Schema/report version policy

`VERSION = 2`, `VERSION_MINOR = 8` are frozen for the duration of the port.
The Python port's emitted `report_version` field reads `"v2.8"`. Bumping
to `v2.9` is reserved for the post-port cleanup (Go retirement) and is out
of scope for the port itself.

Adding new fields to `pr_risk.json` or `pr-risk.json` during the port is
**not allowed** even if motivated. Parity is the contract. New fields land
in v2.9+.

## 8. Capture corpus contract

Each fixture under `tests/pr_risk/fixtures/pr-N/`:
- `meta.json` — `{ pr_number, merge_sha, parent_sha, base_ref, pr_title, repo_slug, schema_version: "1.0" }`
- `pr_risk.json` — full Go output
- `pr-risk.json` — semantic Go output
- `pr_risk.md` — markdown Go output
- `capture.log` — captured stdout/stderr from the run

The capture script (`scripts/capture_pr_risk_fixtures.sh`) is the single
authority. Hand-edited fixtures are not allowed; if a captured fixture is
wrong, fix the capture script and re-capture.

`PR_RISK_PARITY_SCOPE` env var gates which test layers run; see
`tests/pr_risk/README.md`.

## 9. Test policy

- `tests/pr_risk/test_round.py` — boundary cases for the rounding helper.
- `tests/pr_risk/test_parity.py` — corpus-driven parity gate. Skips
  layers that haven't landed yet, asserts on layers that have.
- Each Phase 1+ story adds module-specific unit tests under
  `tests/pr_risk/`. Unit tests assert *behavior* (golden tables, edge
  cases); the corpus test asserts *parity*.
- We do **not** hand-translate every Go `*_test.go` file. Most Go test
  cases are absorbed by the fixture corpus; only branches that the
  corpus doesn't exercise (e.g. detector edge cases) need a hand-written
  Python test.

## 10. Safety vs the source repo

The capture script never mutates the source repo. Encoded:
- Pre-flight refuses to run on a dirty tracked tree.
- `git checkout --detach <sha>` only — never creates/touches branches.
- `--output-dir` always points outside the source repo's worktree.
- Original ref restored via `trap` on EXIT/INT/TERM.
- Forbidden command set: `stash`, `reset --hard`, `clean`, `commit`,
  `push`, `branch -D`, `config`, `gc --prune`. The script does not
  invoke any of these.

## 11. Post-decoupling architecture (Phases 1-6)

Before the decoupling, `pr_risk` shipped project-specific path patterns, sensitive-domain set, and gate definitions hardcoded across `classify.py`, `actions.py`, `validations.py`, `actions_priority.py`, and `evidence.py`. Adopters had to fork to retarget the engine.

After the decoupling, the package is fully config-driven via a single `ops/release-readiness/pr-risk-config.yaml`. The runtime carries:

- `PRRiskConfig` (frozen dataclass) — schema-validated YAML with three sections: `domains`, `sensitive_domains`, `gates`.
- `PRRiskRuntime` — wraps a `PRRiskConfig` and exposes a compiled `Classifier` (Phase 2), a gate registry consumer (Phase 3), and a detector resolver (Phase 4). `from_default()` returns a minimal language-agnostic runtime; `from_config(path)` loads from YAML.
- Closed-set vocabulary — the schema enumerates the path-pattern predicates (`prefix`, `contains`, `exact`, `endswith`, `any_contains`, `and`), the `applies_when` predicates (`factor_id`, `not_factor_id`, `risk_band`, `not_risk_band`, `domain_factor`, `intent_mismatch`, `concentration_mode`, `hotspots_present`, `proximity_distant_with_sensitive`), and the evidence detector template names (10 templates). The loader rejects anything outside these sets.
- Adopter escape hatch — `PRRiskRuntime.register_detector(template_name, fn)` lets adopters plug in a custom detector callable. Programmatic-only because the schema's `evidence.template` enum rejects unknown names at load time.

### Why closed-set templates instead of a DSL

A general declarative DSL for evidence detection (e.g. boolean expressions over signals + insights + a path-domain map) was on the table. We chose closed-set templates instead because:

- The 10 templates we shipped cover every detector behavior the previous hardcoded `_DETECTORS` dict implemented, with byte-for-byte parity. We have evidence the templates are sufficient for today's needs.
- A DSL that's expressive enough to produce the same wording as the existing detectors (with all their domain-specific phrasing and edge cases) would be substantially larger than the templates registry.
- The `register_detector` escape hatch covers the 1% of adopters who genuinely need a behavior outside the closed set, without dragging the rest of the package into a DSL design.
- The closed set is a public contract: adding new templates is a minor-version change; removing or changing them is breaking. That's tractable; a DSL's surface area is much harder to evolve.

A DSL is a separate, larger project that we may revisit if adopter demand justifies it.

### What stays in code (and why)

- Generic path heuristics in `classify.py`: `is_test_path`, `is_e2e_path`, `is_untestable_path`, `is_config_path`, `is_migration_path`. These are language / framework heuristics, not project policy — every adopter wants the same answer.
- Score math, threshold logic, and band computation in `score.py`. Adopters tune thresholds via the existing `ScoreWeights`; the math itself is stable and shared.
- The `_ev_ci_baseline` detector in `evidence.py`. The CI-baseline check applies regardless of which gates fire.

### Phase summary

- **Phase 1** — schema + loader + runtime skeleton + parity-fixture YAML. No behavior change; loader and runtime are dead code.
- **Phase 2** — `Classifier(config)` replaces the hardcoded path-pattern chain in `classify_area`. Threading: `runtime` kwarg added to `score`, `extract_signals`, `classify_*`, `touches_sensitive_code_without_tests`. Parity tests load corpus YAML explicitly.
- **Phase 3** — gate registry from config. `compute_required_actions` becomes a closed-set predicate evaluator over `runtime.gates`. `compute_required_validations` reads `gate.validation_line`. `priority_for_action_id` reads `runtime.priority_for(id)`.
- **Phase 4** — closed-set evidence detector templates; `evidence_for_action_id` delegates to `runtime.detector_for(id)`. `_DETECTORS` dict and the 10 hand-written `_ev_*` private helpers deleted; templates module owns the wording.
- **Phase 5** — strip the bundled-default project-specific data. `_default_config.py` ships only the eight generic gates; corpus YAML stays as the parity-test fixture. Examples added under `examples/pr-risk/`. Init scaffold writes a starter `pr-risk-config.yaml`.
- **Phase 6** — docs (`docs/how-to/7-configure-pr-risk.md`, `docs/reference/pr-risk-config.md`), README "Configuring PR Risk" section, doctor validation of `pr-risk-config.yaml`.
