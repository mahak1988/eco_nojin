# GitHub release governance runbook

**Status:** prepared, not executed. The commands below require repository administration and must be reviewed before use.

## Scope

Repository: `mahak1988/eco_nojin`
Integration branch: `main`
Release tag pattern: `vX.Y.Z`

This runbook configures GitHub environments, required status checks, release-tag protection, and GHCR promotion. It does not contain secrets or a registry credential.

## 1. Preflight

```bash
gh auth status
gh api repos/mahak1988/eco_nojin --jq '{default_branch,visibility,permissions}'
gh workflow list --repo mahak1988/eco_nojin
```

Required permission: repository administration. Confirm the required reviewer account before applying environment rules.

## 2. Required checks

Use the current workflow job names:

- `generate-api`
- `Lint & Format`
- `type-check`
- `unit`
- `i18n`
- `build`
- `a11y`
- `e2e`
- `lighthouse`

Verify which jobs run on pull requests before enabling strict branch requirements. A required check that never reports makes pull requests permanently unmergeable.

## 3. Environments

```bash
gh api --method PUT repos/mahak1988/eco_nojin/environments/staging \
  --input - <<'JSON'
{
  "wait_timer": 0,
  "prevent_self_review": true,
  "reviewers": [
    { "type": "User", "id": 1 }
  ],
  "deployment_branch_policy": {
    "protected_branches": true,
    "custom_branch_policies": false
  }
}
JSON

gh api --method PUT repos/mahak1988/eco_nojin/environments/production \
  --input - <<'JSON'
{
  "wait_timer": 0,
  "prevent_self_review": true,
  "reviewers": [
    { "type": "User", "id": 1 },
    { "type": "Team", "id": 2 }
  ],
  "deployment_branch_policy": {
    "protected_branches": true,
    "custom_branch_policies": false
  }
}
JSON
```

Replace numeric reviewer/team IDs. Do not apply the example values.

Environment secrets must come from the repository secret system or External Secrets; they must not be committed.

## 4. Main-branch ruleset

Create a ruleset with a maintainer preview first. Substitute the exact check names after verifying a recent green CI run.

```bash
gh api --method POST repos/mahak1988/eco_nojin/rulesets \
  --input - <<'JSON'
{
  "name": "main-quality-gate",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": { "include": ["~DEFAULT_BRANCH"] }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "required_linear_history",
      "parameters": { "allow_squash_merge": true, "allow_merge_commit": false, "allow_rebase_merge": false }
    },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true,
        "require_last_push_approval": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "do_not_enforce_on_create": true,
        "required_status_checks": [
          { "context": "generate-api" },
          { "context": "Lint & Format" },
          { "context": "type-check" },
          { "context": "unit" },
          { "context": "i18n" },
          { "context": "build" },
          { "context": "a11y" },
          { "context": "e2e" },
          { "context": "lighthouse" }
        ]
      }
    }
  ],
  "bypass_actors": []
}
JSON
```

Use `enforcement: "disabled"` for the first run. After one successful pull request and one green push, set it to `active`.

## 5. Release-tag protection

```bash
gh api --method POST repos/mahak1988/eco_nojin/rulesets \
  --input - <<'JSON'
{
  "name": "immutable-semver-tags",
  "target": "tag",
  "enforcement": "active",
  "conditions": {
    "ref_name": { "include": ["refs/tags/v*"] }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "update" },
    { "type": "creation" }
  ],
  "bypass_actors": []
}
JSON
```

Legacy tags `v0.1-baseline` and `v0.2-clean` are not valid `vX.Y.Z` tags. Do not rewrite them; start enforcement with a new semver tag.

## 6. GHCR and promotion contract

- CI publishes an image by immutable commit SHA.
- Staging deploys the tested digest.
- Production deploys the same digest; it must not rebuild.
- Tag names are labels, not deployment selectors.
- A production deployment records the commit SHA, image digest, Git tag, actor, and reviewer.

Example evidence record:

```text
git_tag=vX.Y.Z
git_sha=<full-sha>
image=ghcr.io/<namespace>/frontend@sha256:<digest>
environment=production
reviewer=<github-user>
```

The namespace decision is still pending. Do not choose `eco-nojin` versus `mahak1988` inside automation until the owner confirms it.

## 7. Verification

```bash
gh api repos/mahak1988/eco_nojin/rulesets
gh api repos/mahak1988/eco_nojin/environments
gh run list --repo mahak1988/eco_nojin --branch main --limit 10
```

Verification checklist:

- a test pull request cannot merge without all required green checks;
- a direct push to main is rejected when required status checks are enforced;
- a `vX.Y.Z` tag cannot be updated or deleted;
- staging/production require human review;
- production uses the digest tested in staging;
- a rollback selects a previous digest without rebuilding.

## 8. Rollback

1. Disable the failing production environment job or choose a previous reviewed digest.
2. Keep the failed digest and logs for incident analysis.
3. Do not move or delete the release tag to hide the failed build.
4. Create a new forward-fix tag only after the digest passes the full gate.
