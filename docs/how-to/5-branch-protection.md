# Make `release-readiness` required on PRs

Once the readiness check has stabilized (no false BLOCKs for at least one full release cycle, ideally a couple of weeks), gate merges on it. This guide walks the GitHub configuration in two ways: the UI and the `gh api` equivalent.

> Prerequisite: a green `release-readiness` run on the default branch. If the check has never succeeded on `main`, GitHub won't list it as available to require.

---

## 1. The GitHub UI path

1. Navigate to **Settings → Branches → Branch protection rules**.
2. Edit the rule for `main` (create one if it doesn't exist).
3. Under **Require status checks to pass before merging**, ensure the box is checked.
4. In the **status checks search box**, type `release-readiness` and select the check.
5. Save.

Best practice: also enable **Require branches to be up to date before merging**. Without it, a PR can merge against an old `main` whose readiness verdict no longer reflects current state.

---

## 2. The `gh api` path (scriptable / IaC)

If you manage branch protection from code, here's the equivalent `gh api` call:

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

- **`contexts: ["release-readiness"]`** — the name must match the `name` you used in the GitHub Check creation step (or the workflow job name if you're not creating a Check). Mismatch is the #1 reason branch protection silently does nothing.
- **`strict: true`** is the "branches up to date" toggle. Required for meaningful enforcement.
- **`enforce_admins: false`** lets repo admins bypass the gate in emergencies. Set to `true` if your team agrees no one should bypass.

Verify with:

```bash
gh api /repos/<owner>/<repo>/branches/main/protection --jq '.required_status_checks'
```

You should see `release-readiness` listed in `contexts`.

---

## 2.5. Rulesets (recommended for new setups)

Classic branch protection still works, but [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets) are the current default. Rulesets are layered (rather than singular), targetable across multiple branches with one config, and reusable at the org level. Prefer rulesets unless you have a reason to stay on classic protection.

### UI path

1. **Settings → Rules → Rulesets → New branch ruleset**.
2. Name: `require-release-readiness`. Enforcement: **Active**.
3. Target branches: include `Default branch` (or `main` explicitly).
4. Rules:
   - **Require a pull request before merging** (any approval count you want; for sample/demo repos, `0` is fine — the readiness check is the gate).
   - **Require status checks to pass** → add `release-readiness`. Tick **Require branches to be up to date before merging**.
5. **Bypass list**: add the `Repository admin` role with **Always** mode. (See §4.5 for who else belongs here.)
6. Save.

### `gh api` path

```bash
gh api -X POST /repos/<owner>/<repo>/rulesets --input - <<'JSON'
{
  "name": "require-release-readiness",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          { "context": "release-readiness" }
        ]
      }
    }
  ],
  "bypass_actors": [
    { "actor_type": "RepositoryRole", "actor_id": 5, "bypass_mode": "always" }
  ]
}
JSON
```

`actor_id: 5` is the built-in admin role. For team-scoped bypass, use `"actor_type": "Team"` with the team's numeric id (find it via `gh api orgs/<org>/teams/<slug>`).

Verify:

```bash
gh api /repos/<owner>/<repo>/rulesets --jq '.[] | {id, name, enforcement}'
gh api /repos/<owner>/<repo>/rulesets/<id> --jq '.rules, .bypass_actors'
```

### Don't run both layers by accident

If a repo has *both* a classic branch protection rule and a ruleset that target `main`, GitHub layers them — the most-restrictive combination wins. That's surprising if you forget about the older rule. When migrating from classic to rulesets, delete the classic rule (`gh api -X DELETE /repos/<owner>/<repo>/branches/main/protection`) once the ruleset is verified.

---

## 3. Phased rollout (recommended)

Don't flip required-check on the first day. Rollout pattern that preserves team trust:

| Phase | Duration | Configuration |
|---|---|---|
| 0. Soft observability | 1 week | Workflow runs, posts comment, doesn't appear in branch protection. |
| 1. Visible non-blocking | 1–2 release cycles | Check appears in PR UI as a yellow/green badge. Reviewers see it. Not required. `warn-conclusion: neutral` (Tier 1) or `WARN: 'neutral'` mapping (Tier 3). |
| 2. Required, block-only | 1 release cycle | `enforcement-mode: block_only`, listed in branch protection. WARN does not block; BLOCK does. Same `neutral` mapping as Phase 1. |
| 3. Required, warn-and-block | open-ended | `enforcement-mode: warn_and_block` **plus** a WARN-blocking conclusion. See "Promoting to Phase 3" below. |

If a regression surfaces in any phase, drop back **one phase**, fix the underlying issue, and resume. Skipping phases or removing the gate entirely both damage trust more than the original failure did.

### Promoting to Phase 3

`--enforcement-mode warn_and_block` only changes the *evaluator's process exit code* (so the workflow job goes red on WARN). It does **not** change how GitHub interprets the Check Run conclusion. To make WARN actually block the merge button via the required-status-check rule, the conclusion mapping must also be non-neutral:

- **Tier 1** (reusable workflow): pass `warn-conclusion: action_required` (default, blocks merge but keeps workflow green) or `warn-conclusion: failure` (blocks merge AND turns workflow red — strict). Setting `enforcement-mode: warn_and_block` alone with the default `warn-conclusion: action_required` is enough — the default is Phase-3-compatible.
- **Tier 3** (own publish step): you must edit your `conclusionMap` literal — change `WARN: 'neutral'` to `WARN: 'action_required'` or `WARN: 'failure'`. Both must change together: enforcement-mode flag + conclusion mapping. This pair is the "two-edit dance" — one without the other silently leaves WARN merges enabled.

See `docs/how-to/3-ci-integration.md` §3.5 for the full table and the trade-offs between the three WARN conclusions. The reference samples at `release-readiness-sample-app` (Phase 2) and `release-readiness-node-js-sample-app` (Phase 3) demonstrate both ends of the rollout.

---

## 4. CODEOWNERS interaction

If your repo uses CODEOWNERS, the `release-readiness` workflow may need write access to PR comments and Checks even when CODEOWNERS restricts other writes. The workflow YAML's `permissions:` block covers this:

```yaml
permissions:
  contents: read
  pull-requests: write   # for sticky comments
  checks: write          # for Check Run creation
```

These are *workflow-level* permissions, separate from CODEOWNERS.

---

## 4.5. Human intervention: bypass mechanics

A required check that *cannot* be bypassed is a footgun. CI infrastructure has outages; readiness adapters have bugs; a regression in `release-readiness-core` can WARN-storm a whole afternoon of legitimate PRs. You need a documented escape hatch — but a narrow one, with an audit trail.

### Who should be a bypass actor

Pick a small, named set:

- **Repository admins** — sufficient for most teams. (`actor_type: RepositoryRole`, `actor_id: 5` in the ruleset payload.)
- **A `release-managers` team** — better at organizations where "admin" is a much wider role than "person trusted to override the gate". Create the team in the org, add the trusted humans, reference it in `bypass_actors` with `actor_type: Team`.
- **Specific named users** — fine for very small teams; doesn't scale and rotates poorly.

Anti-pattern: granting bypass to *everyone with write access*. That turns "required check" into a suggestion.

### How the bypass surfaces in the UI

When the required check fails on a PR:

- **Non-bypass actors** see a disabled merge button with "Required check has failed".
- **Bypass actors** see an extra link: **"Merge without waiting for requirements to be met (bypass branch protections)"**. Clicking it merges and records the bypass.

The button is identical for both classic protection (with `enforce_admins: false`) and rulesets (with the actor in `bypass_actors`).

### Audit trail

Every bypass is logged. Pull recent bypasses with:

```bash
gh api /repos/<owner>/<repo>/audit-log \
  -F phrase='action:protected_branch.policy_override OR action:repo.override_required_status_check' \
  --jq '.[] | {actor, action, created_at, ref}'
```

Or in the UI: **Settings → Audit log** (org-level audit log, filterable by repo). For rulesets specifically, `Insights → Rule insights` shows pass/fail/bypass counts per rule and is the better long-term signal.

### When to bypass — and when not to

**Bypass is appropriate when:**

- The CI infrastructure is broken (Actions outage, registry unreachable, evaluator panic on a bug). The gate is wrong, not the code.
- An incident hotfix needs to ship and the gate is failing on something the hotfix doesn't actually touch (e.g. a flaky e2e in an unrelated module).
- A `release-readiness-core` upgrade introduced a behavior change that's affecting all PRs and the rollback or pin-fix is in flight.

**Bypass is NOT appropriate when:**

- The check failed because the change actually broke something. Fix the code.
- You're impatient or under deadline pressure. Schedule pressure is the most common reason a gate gets eroded.
- A reviewer asked for changes you don't want to make. Push back in the PR; don't merge around them.

### Required follow-up after a bypass

A bypass without follow-up is the gate quietly dying. After every bypass:

1. File an issue (or a comment on the merged PR) capturing: the bypassed commit SHA, what the gate said, why bypass was the right call, and the corrective action taken or planned.
2. If the bypass was due to a tooling failure: confirm the tool is fixed before the next bypass-able window opens.
3. Track bypass frequency over time (Rule insights does this for you). Rising frequency means either the gate is too strict or the team is normalizing bypass — both call for action.

---

## 5. Common pitfalls

### "Branch protection lists the check but PRs merge anyway"

The required-check name in branch protection doesn't match the actual Check name. Run a sample PR, click into Checks, and copy the exact name (including capitalization) into the protection rule.

### "Required-check passes locally but the merge button is gray"

Either `strict: true` is on and the PR isn't up to date with `main`, or another required check (CODEOWNERS approvals, signed commits) is unsatisfied. Check the PR's "Why can't I merge?" expander.

### "My PR is stuck waiting for `release-readiness` that's already done"

The Check name on the PR isn't the one branch protection requires. Two ways this happens:

- The workflow renamed the job from `release-readiness` to `release-readiness-check` mid-PR. Branch protection still wants the old name.
- The Check was created with `actions/github-script` using a different `name:` than expected.

Edit the protection rule to match the new name, or rename the workflow job back. Don't merge with bypass — that defeats the gate.

### "We made it required, then a 0.x.y release of `release-readiness-core` changed behavior"

Pin a SHA in the composite-action `package-ref` input. SHAs are immutable; tags are not. See `RELEASE.md` for the full versioning and SHA-pin policy.

---

## 5.5. Verifying enforcement actually blocks

Don't trust the configuration — prove it. Most "branch protection silently does nothing" cases (§5) survive both UI inspection and `gh api` readback because the misconfiguration is in a name, not a missing field. The only reliable check is a live failure drill.

### The drill

On a scratch branch, intentionally break a smoke or e2e validation that flows into `release-readiness`:

```bash
git checkout -b drill/readiness-gate
# Edit a smoke test so it asserts an impossible condition (e.g. status 999).
# Or: temporarily flip a `--baseline-percent` to 100 in the workflow so coverage fails.
git commit -am "drill: deliberately fail readiness to test the gate"
git push -u origin drill/readiness-gate
gh pr create --fill --draft
```

Wait for the workflow to publish a failed `release-readiness` Check, then verify on the PR page:

- ✅ Merge button is disabled with "Required check has failed".
- ✅ The "Merge without waiting for requirements" link appears for bypass actors only — confirm by viewing as a non-admin user (or asking a teammate without bypass).
- ✅ `gh pr view <pr> --json mergeable,mergeStateStatus` reports `mergeStateStatus: BLOCKED` (or `BEHIND` if `strict: true` and the branch isn't current).

If the merge button is still enabled, the gate is misconfigured. Most often it's a name mismatch (§5) — re-read the actual Check name on the PR and copy it byte-for-byte into the rule.

### Test the bypass path too

In the same drill PR, exercise the bypass path:

1. As a bypass actor, click "Merge without waiting for requirements".
2. Confirm the audit log records it: `gh api /repos/<owner>/<repo>/audit-log -F phrase='action:protected_branch.policy_override' --jq '.[0]'`.
3. Immediately revert the merge so the drill doesn't pollute `main`.

### When to repeat the drill

- After any change to the workflow's Check Run name or job structure.
- After bumping `release-readiness-core` past a minor version.
- Once a release cycle as a smoke test that nobody silently weakened the rule.

This drill is the single highest-value check in this doc. Configurations rot quietly; a failed drill turns rot into a loud signal.

---

## 6. Cross-references

- `docs/how-to/3-ci-integration.md` — the workflow + Check publishing setup that branch protection relies on.
- `docs/how-to/6-migrate-from-existing-gate.md` — recommended flow if there's an existing required check this is replacing.
- `RELEASE.md` — SHA-pin policy.
