# Release process

`release-readiness-core` is published to **PyPI** as [`release-readiness-core`](https://pypi.org/project/release-readiness-core/). Adopters who do not need the GitHub source can install a **pinned version** with `pip install release-readiness-core==X.Y.Z`. Git installs from this repository remain supported for forks and bleeding-edge pins.

## Versioning

The project follows Semantic Versioning (semver):

- **MAJOR** — breaking change to the `compute_readiness` API, the `release-readiness.json` summary schema, or any documented JSON contract under `docs/contracts/`.
- **MINOR** — backwards-compatible additions: new adapters, new CLI flags, new config keys with safe defaults, new contract fields with safe defaults.
- **PATCH** — bug fixes, doc-only changes, internal refactors.

Until `1.0.0`, **minor versions may include backwards-incompatible changes** if they unblock generalization correctness (this is the spirit of pre-1.0 in semver). Each such change is called out in `CHANGELOG.md` under "Changed" or "Removed" with the migration steps.

## Install sources for adopters

### PyPI (recommended when consumers lack access to this git repository)

```bash
pip install "release-readiness-core==X.Y.Z"
```

Published versions are **immutable** on PyPI — pinning `==X.Y.Z` is the analogue of SHA-pinning for git installs.

### Git (forks, unreleased commits, or when you need a specific SHA)

```bash
pip install "git+https://github.com/psuthar/release-readiness-core.git@<sha>"
```

**Always pin a SHA**, not a branch or tag, when using git. SHAs are immutable; tags can be moved. This matters because `release-readiness-core` is itself the gate for an adopter's release pipeline — a moving install target would make the gate non-deterministic.

You can find the SHA for a given version in `CHANGELOG.md`'s commit log or via `git log` on this repo.

**Note:** GitHub composite actions and reusable workflows in this repo are still referenced with `uses: …@<sha>` — that SHA pins the **workflow/action YAML**, not necessarily the Python wheel. Use `install-source: pypi` and `pypi-version` on those actions when you want the **Python package** from PyPI while keeping the action definition pinned to a SHA (see `docs/how-to/9-adoption-tiers.md`).

## PyPI trusted publishing (one-time maintainer setup)

Publishing from CI uses **PyPI Trusted Publishing** (OIDC) — no long-lived PyPI password in GitHub secrets.

1. Create the [`release-readiness-core`](https://pypi.org/project/release-readiness-core/) project on PyPI (or claim the name if unused).
2. In PyPI project **Settings → Publishing**, add a **trusted publisher**:
   - **Publisher:** GitHub
   - **Owner / repository:** the GitHub repo that hosts this code (e.g. `psuthar/release-readiness-core`)
   - **Workflow name:** `publish-pypi.yml`
   - **Environment name:** `pypi`
3. In GitHub: **Settings → Environments →** create an environment named **`pypi`** (optional: add protection rules / required reviewers).
4. Confirm [`.github/workflows/publish-pypi.yml`](.github/workflows/publish-pypi.yml) uses `environment: name: pypi` and `permissions: id-token: write`.

After this, pushing an annotated tag `vX.Y.Z` whose commit matches `pyproject.toml` `version = "X.Y.Z"` triggers a build and upload.

## Release checklist (maintainer)

1. Land all PRs targeting the next version on `main`.
2. Update `pyproject.toml`'s `version = "..."` field.
3. Update `CHANGELOG.md`:
   - Move "Unreleased" entries under a new `## [X.Y.Z] — YYYY-MM-DD` section.
   - Confirm "Added" / "Changed" / "Removed" / "Fixed" categories cover everything.
4. Commit with message `release: vX.Y.Z` and push to `main`.
5. Tag the commit: `git tag -a vX.Y.Z -m "release X.Y.Z"; git push origin vX.Y.Z`.
6. Wait for the **Publish to PyPI** GitHub Actions workflow to finish; confirm the files appear on PyPI.

**Builds vs uploads:** ordinary PR/push CI runs tests and `uv build` but does **not** upload to PyPI. Only the publish workflow uploads. If a release is faulty, **yank** it on PyPI and ship a **new patch version** — you cannot replace files for an existing version.

## What counts as a contract

The following are public contracts. Changes here require a major-version bump (or a minor with explicit migration notes pre-1.0):

- The CLI flag set of every `[project.scripts]` entry in `pyproject.toml`.
- The shape of `release-readiness.json` (the lean machine summary).
- The shape of `report.json` (the full structured payload).
- The keys recognized in `config.yaml` (see `release_readiness_core.readiness_io.KNOWN_TOP_LEVEL_CONFIG_KEYS`).
- The schemas under `docs/contracts/`.

Adapters' input shapes (Playwright, JUnit, LCOV) are best-effort — they're consumed from project tooling we don't control.

## Compatibility guarantees pre-1.0

- We will not break `compute_readiness` callers within a minor version.
- We will not break the `release-readiness.json` schema within a minor version.
- We **may** add new top-level config keys; adopters' configs always remain forward-compatible.
- We **may** rename internal modules; do not import from `release_readiness_core` submodules other than the documented ones in `docs/contracts/README.md`.
