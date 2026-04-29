# Make `release-readiness` required on PRs

Once the readiness check has stabilized (no false BLOCKs for at least
one full release cycle, ideally a couple of weeks), gate merges on it.
This guide walks the GitHub configuration in two ways: the UI and the
`gh api` equivalent.

> Prerequisite: a green `release-readiness` run on the default branch.
> If the check has never succeeded on `main`, GitHub won't list it as
> available to require.

---

## 1. The GitHub UI path

1. Navigate to **Settings → Branches → Branch protection rules**.
2. Edit the rule for `main` (create one if it doesn't exist).
3. Under **Require status checks to pass before merging**, ensure the
   box is checked.
4. In the **status checks search box**, type `release-readiness` and
   select the check.
5. Save.

Best practice: also enable **Require branches to be up to date before
merging**. Without it, a PR can merge against an old `main` whose
readiness verdict no longer reflects current state.

---

## 2. The `gh api` path (scriptable / IaC)

If you manage branch protection from code, here's the equivalent
`gh api` call:

```bash
gh api -X PUT \
  /repos/<owner>/<repo>/branches/main/protection \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["release-readiness"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_deletions": false,
  "allow_force_pushes": false
}
JSON
```

Notes on the payload:

- **`contexts: ["release-readiness"]`** — the name must match the
  `name` you used in the GitHub Check creation step (or the workflow
  job name if you're not creating a Check). Mismatch is the #1 reason
  branch protection silently does nothing.
- **`strict: true`** is the "branches up to date" toggle. Required for
  meaningful enforcement.
- **`enforce_admins: false`** lets repo admins bypass the gate in
  emergencies. Set to `true` if your team agrees no one should bypass.

Verify with:

```bash
gh api /repos/<owner>/<repo>/branches/main/protection --jq '.required_status_checks'
```

You should see `release-readiness` listed in `contexts`.

---

## 3. Phased rollout (recommended)

Don't flip required-check on the first day. Rollout pattern that
preserves team trust:

| Phase | Duration | Configuration |
|---|---|---|
| 0. Soft observability | 1 week | Workflow runs, posts comment, doesn't appear in branch protection. |
| 1. Visible non-blocking | 1–2 release cycles | Check appears in PR UI as a yellow/green badge. Reviewers see it. Not required. |
| 2. Required, block-only | 1 release cycle | `enforcement-mode: block_only`, listed in branch protection. WARN does not block; BLOCK does. |
| 3. Required, warn-and-block | open-ended | Promote to `enforcement-mode: warn_and_block` once WARN false-positives are rare. |

If a regression surfaces in any phase, drop back **one phase**, fix
the underlying issue, and resume. Skipping phases or removing the
gate entirely both damage trust more than the original failure did.

---

## 4. CODEOWNERS interaction

If your repo uses CODEOWNERS, the `release-readiness` workflow may
need write access to PR comments and Checks even when CODEOWNERS
restricts other writes. The workflow YAML's `permissions:` block
covers this:

```yaml
permissions:
  contents: read
  pull-requests: write   # for sticky comments
  checks: write          # for Check Run creation
```

These are *workflow-level* permissions, separate from CODEOWNERS.

---

## 5. Common pitfalls

### "Branch protection lists the check but PRs merge anyway"

The required-check name in branch protection doesn't match the actual
Check name. Run a sample PR, click into Checks, and copy the exact
name (including capitalization) into the protection rule.

### "Required-check passes locally but the merge button is gray"

Either `strict: true` is on and the PR isn't up to date with `main`,
or another required check (CODEOWNERS approvals, signed commits) is
unsatisfied. Check the PR's "Why can't I merge?" expander.

### "My PR is stuck waiting for `release-readiness` that's already done"

The Check name on the PR isn't the one branch protection requires.
Two ways this happens:

- The workflow renamed the job from `release-readiness` to
  `release-readiness-check` mid-PR. Branch protection still wants the
  old name.
- The Check was created with `actions/github-script` using a different
  `name:` than expected.

Edit the protection rule to match the new name, or rename the workflow
job back. Don't merge with bypass — that defeats the gate.

### "We made it required, then a 0.x.y release of `release-readiness-core` changed behavior"

Pin a SHA in the composite-action `package-ref` input. SHAs are
immutable; tags are not. See `RELEASE.md` for the full versioning and
SHA-pin policy.

---

## 6. Cross-references

- `docs/how-to/ci-integration.md` — the workflow + Check publishing
  setup that branch protection relies on.
- `docs/how-to/migrate-from-existing-gate.md` — recommended flow if
  there's an existing required check this is replacing.
- `RELEASE.md` — SHA-pin policy.
