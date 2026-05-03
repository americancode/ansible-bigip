# Promotion Workflows

This document describes how configuration changes move through environments in this repository. The repo is designed around Git as the source of truth, so promotion is fundamentally a Git operation — not a manual copy between BIG-IP devices.

## Environment Model

Each environment maps to a Git branch with its own inventory and optional var tree overrides:

| Environment | Branch | BIG-IP Target | Purpose |
|---|---|---|---|
| `dev` | `dev` | Lab / staging BIG-IP | Validate changes before wider release |
| `test` | `test` | Pre-production BIG-IP | Integration testing, load validation |
| `prod` | `main` | Production BIG-IP | Live traffic |

The shared `vars/` tree lives on all branches. Environment-specific overrides (e.g., different IP addresses, partition assignments) can be handled through:

- **Inventory host vars**: AWX inventory per environment defines `f5_host` and any environment-specific addresses or metadata
- **Branch-specific var files**: override files only present on certain branches (e.g., `vars/ltm/virtual_servers/prod-specific.yml` on `main`)
- **Conditional playbook logic**: use `when` clauses keyed off inventory variables

## Promotion Flow

Changes flow through environments via Git merges:

```
feature branch  →  dev  →  test  →  main (prod)
```

### Step 1: Feature Branch

All changes start on a feature branch:

```sh
git checkout -b feat/add-new-pool
# edit var files
# run validation
make validate
# commit
git commit -m "feat: add pool and virtual server for new-app"
```

Before merging to `dev`:

- `make validate` must pass
- `tools/drift-check.py` should be run against the dev BIG-IP to surface existing drift
- PR review by at least one other team member

### Step 2: Promote to Dev

Merge the feature branch into `dev` and run the playbook against the dev BIG-IP:

```sh
git checkout dev
git merge feat/add-new-pool --no-ff
git push origin dev
# Trigger AWX job template targeting dev inventory group
```

Validate on the dev BIG-IP:

- Test application traffic
- Run `tools/drift-check.py` to confirm the device matches Git

### Step 3: Promote to Test

Once validated in dev, merge to `test`:

```sh
git checkout test
git merge dev --no-ff
git push origin test
# Trigger AWX job template targeting test inventory group
```

The same var files apply, but the test inventory points at different BIG-IP addresses. Any environment-specific values should be defined in inventory host vars, not in `vars/`.

### Step 4: Promote to Prod

After test validation, merge to `main`:

```sh
git checkout main
git merge test --no-ff
# Tag the release
git tag -a v2026.05.02 -m "Release: new-app pool and VS"
git push origin main --tags
# Trigger AWX job template targeting prod inventory group
```

Production changes should be:

- Tagged with a semantic version
- Deployed during a change window
- Monitored for a stabilization period before closing the change ticket

## AWX Integration

Each environment should have a separate AWX job template or survey that targets the correct inventory group:

| Job Template | Inventory Group | Branch |
|---|---|---|
| `Deploy LTM - Dev` | `bigip-dev` | `dev` |
| `Deploy LTM - Test` | `bigip-test` | `test` |
| `Deploy LTM - Prod` | `bigip-prod` | `main` |

AWX project source control can be pointed at the repo with branch selection per job template. Use webhook triggers on merge to automate dev and test deployment.

## Hotfix Flow

For urgent production fixes, the flow reverses:

```
hotfix branch  →  main (prod)  →  test  →  dev
```

1. Create a hotfix branch from `main`
2. Apply the fix, validate, merge to `main`
3. Deploy immediately via AWX prod job template
4. After stabilization, merge `main` back down to `test` and `dev`

```sh
git checkout -b hotfix/correct-pool-members main
# fix
make validate
git commit -m "fix: correct pool member port for inventory-east"
git checkout main
git merge hotfix/correct-pool-members --no-ff
git push origin main
# Deploy to prod immediately
# Then back-propagate:
git checkout test
git merge main
git push origin test
git checkout dev
git merge main
git push origin dev
```

## Drift Detection in Promotion

Run `tools/drift-check.py` at key points in the promotion flow:

| Stage | Action | Purpose |
|---|---|---|
| Before feature merge to dev | `drift-check` against dev BIG-IP | Confirm dev is in sync before introducing changes |
| After dev deployment | `drift-check` against dev BIG-IP | Verify deployment succeeded, no unexpected drift |
| Before prod merge | `drift-check` against test BIG-IP | Confirm test environment reflects the intended state |
| After prod deployment | `drift-check` against prod BIG-IP | Final verification |

## Branch Protection Rules

Recommended branch protection settings:

- `main`: require PR, require passing CI (validation + drift), require code owner review
- `test`: require PR or direct merge from `dev`, require passing CI
- `dev`: allow direct push from team leads, require passing CI on push

## Importing from Production

When onboarding an existing BIG-IP estate, use `tools/import-from-bigip.py` to seed the initial var tree:

```sh
F5_HOST=prod-bigip F5_PASSWORD=secret python3 tools/import-from-bigip.py --out imported/
```

Review the imported files, merge them into the appropriate `vars/` locations, commit to `main`, and apply to the device to establish the baseline. After this point, all changes go through the promotion flow.
