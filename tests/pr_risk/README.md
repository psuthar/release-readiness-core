# PR Risk Parity Test Corpus

Fixtures here are **byte-for-byte references** captured from the upstream
reference implementation of the PR Risk scorer (the Go binary at
`internal/prrisk@v2.8` that the Python port in this package was derived
from). They drive the parity gate that proves the Python implementation
computes identical results for the same diff.

## Layout

```
tests/pr_risk/fixtures/
├── pr-1234/
│   ├── meta.json        # { pr_number, merge_sha, parent_sha, base_ref, pr_title, schema_version }
│   ├── pr_risk.json     # Full Result struct emitted by Go
│   ├── pr-risk.json     # Lean semantic file emitted by Go (matches docs/contracts/pr-risk-input-v1.schema.json)
│   ├── pr_risk.md       # Markdown report emitted by Go
│   └── capture.log      # stdout/stderr from the capture run (debugging aid)
├── pr-1245/
│   └── ...
```

`meta.json.schema_version` is `"1.0"` for the capture format. The `report_version`
inside `pr_risk.json` reflects the Go scorer version (`v2.8` at port time).

## Capture

Goldens are produced by `scripts/capture_pr_risk_fixtures.sh`. It:

1. **Pre-flight**: aborts unless the source repo's tracked tree is clean.
2. **Snapshots** the source repo's current ref, then for each PR:
   - `git checkout --detach <merge_sha>` (never touches branches)
   - Runs the Go `prrisk` binary into a temp dir outside the source repo
   - Copies the three output files into `tests/pr_risk/fixtures/pr-N/`
3. **Restores** the original ref on success, error, or interrupt.

The script's mutating-command set is restricted to `git fetch`, `git checkout
--detach`, `git rev-parse`, `git log`, `git show`. It never runs `stash`,
`reset`, `clean`, `commit`, `push`, `branch`, or `config` against the source
repo.

### Re-running

```bash
# Build the upstream prrisk binary once (faster than re-compiling per PR).
( cd /path/to/source-repo && go build -o /tmp/prrisk-bin ./cmd/prrisk )

# Capture from a list of PR numbers on stdin.
gh -R <owner>/<repo> pr list --state merged --limit 80 \
    --json number --jq '.[].number' \
  | scripts/capture_pr_risk_fixtures.sh \
      --target /path/to/source-repo \
      --output tests/pr_risk/fixtures \
      --prrisk-cmd /tmp/prrisk-bin \
      --repo-slug <owner>/<repo>
```

Re-running on the same input is idempotent: existing `pr-N/` directories with a
`pr-risk.json` are skipped. To re-capture a specific PR, delete its directory.

## Parity scope

`PR_RISK_PARITY_SCOPE` env var gates which assertions run:

| Value     | Live in story | Asserts                                   |
| --------- | ------------- | ----------------------------------------- |
| `none`    | SCRUM-232     | corpus loads + CLI stub responds          |
| `context` | SCRUM-234     | + ContextInsights subtree byte-identical  |
| `score`   | SCRUM-235     | + score / band / score_math / categories  |
| `full`    | SCRUM-236     | + entire pr_risk.json + pr-risk.json      |

`uv run pytest tests/pr_risk` defaults to `PR_RISK_PARITY_SCOPE=none`; CI in
later phases pins the appropriate value.
