# Release process

`release-readiness-core` is currently distributed as an installable git
repository, not a PyPI package. This document is the policy adopters
should rely on until a `1.0.0` PyPI release lands.

## Versioning

The project follows Semantic Versioning (semver):

- **MAJOR** — breaking change to the `compute_readiness` API, the
  `release-readiness.json` summary schema, or any documented JSON
  contract under `docs/contracts/`.
- **MINOR** — backwards-compatible additions: new adapters, new CLI
  flags, new config keys with safe defaults, new contract fields with
  safe defaults.
- **PATCH** — bug fixes, doc-only changes, internal refactors.

Until `1.0.0`, **minor versions may include backwards-incompatible
changes** if they unblock generalization correctness (this is the spirit
of pre-1.0 in semver). Each such change is called out in `CHANGELOG.md`
under "Changed" or "Removed" with the migration steps.

## SHA pinning until PyPI

Adopters install via:

```bash
pip install "git+https://github.com/psuthar/release-readiness-core.git@<sha>"
```

**Always pin a SHA**, not a branch or tag. SHAs are immutable; tags can
be moved. This matters because `release-readiness-core` is itself the
gate for an adopter's release pipeline — a moving install target would
make the gate non-deterministic.

You can find the SHA for a given version in `CHANGELOG.md`'s commit log
or via `git log` on this repo.

## Release checklist (maintainer)

1. Land all PRs targeting the next version on `main`.
2. Update `pyproject.toml`'s `version = "..."` field.
3. Update `CHANGELOG.md`:
   - Move "Unreleased" entries under a new `## [X.Y.Z] — YYYY-MM-DD` section.
   - Confirm "Added" / "Changed" / "Removed" / "Fixed" categories cover everything.
4. Commit with message `release: vX.Y.Z` and push to `main`.
5. Tag the commit: `git tag -a vX.Y.Z -m "release X.Y.Z"; git push --tags`.
6. (Future, after PyPI publishing is set up) `python -m build && twine upload dist/*`.

## What counts as a contract

The following are public contracts. Changes here require a major-version
bump (or a minor with explicit migration notes pre-1.0):

- The CLI flag set of every `[project.scripts]` entry in `pyproject.toml`.
- The shape of `release-readiness.json` (the lean machine summary).
- The shape of `report.json` (the full structured payload).
- The keys recognized in `config.yaml` (see
  `release_readiness_core.readiness_io.KNOWN_TOP_LEVEL_CONFIG_KEYS`).
- The schemas under `docs/contracts/`.

Adapters' input shapes (Playwright, JUnit, LCOV) are best-effort —
they're consumed from project tooling we don't control.

## Compatibility guarantees pre-1.0

- We will not break `compute_readiness` callers within a minor version.
- We will not break the `release-readiness.json` schema within a minor
  version.
- We **may** add new top-level config keys; adopters' configs always
  remain forward-compatible.
- We **may** rename internal modules; do not import from
  `release_readiness_core` submodules other than the documented ones in
  `docs/contracts/README.md`.
