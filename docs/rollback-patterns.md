# Rollback Patterns

This document describes how to undo changes in this repository. Because all BIG-IP configuration is declarative and Git-driven, rollback is primarily a Git operation — not a manual reversal on the device.

## Primary Rollback: Git Revert

The standard rollback for any declarative change is `git revert`:

```sh
# Find the commit to revert
git log --oneline -- vars/ltm/pools/vm-applications.yml

# Revert the specific commit
git revert <commit-hash>

# Push and redeploy
git push origin main
# Trigger AWX job template to apply reverted state
```

`git revert` creates a new commit that undoes the changes from the target commit. This is preferred over `git reset` because:

- it preserves history (the revert is auditable)
- it works cleanly on branches with multiple contributors
- it does not require force-push

## Playbook Re-Apply

If drift has occurred on the device (someone changed something manually), the simplest fix is often to re-apply the last known good state:

```sh
# If the latest Git commit is correct, just re-run the playbook
ansible-playbook playbooks/ltm.yml
```

This will reconcile the device back to the declared state. It is not a true rollback (it does not undo the change that was in Git), but it is the fastest way to recover from unauthorized manual drift.

## Rollback by Object Type

### Non-Destructive Changes (create/update)

For changes that only create or modify objects (no deletions):

1. `git revert` the commit that introduced the change
2. Redeploy via AWX or CLI playbook execution
3. BIG-IP objects will be restored to their previous state

### Destructive Changes (deletions)

For changes that deleted objects (via deletion trees or `state: absent`):

1. `git revert` the commit that introduced the deletion
2. The reverted commit restores the object declarations to `vars/`
3. Redeploy via AWX or CLI playbook execution
4. BIG-IP objects will be recreated

**Important**: If the deleted objects had runtime state (active connections, session persistence data), those will not be recovered by re-creation. Coordinate rollback with application teams to minimize disruption.

### Mixed Changes

Commits that both create and delete objects can be partially rolled back using `git revert --no-commit` followed by selective staging:

```sh
# Start revert but don't auto-commit
git revert <commit-hash> --no-commit

# Unstage the parts you want to keep
git reset HEAD vars/ltm/virtual_servers/new-apps.yml

# Keep the virtual server changes, revert only the pool deletion
git checkout HEAD -- vars/ltm/virtual_servers/new-apps.yml
git add vars/ltm/pools/deletions/
git commit -m "revert(partial): restore deleted pool, keep new virtual server"
```

## Emergency Rollback: UCS Restore

If Git rollback fails or the BIG-IP is in an unrecoverable state, restore from a UCS backup:

```sh
# List available UCS backups on the BIG-IP
tmsh show sys ucs

# Restore from UCS (requires reboot)
tmsh load sys ucs /var/local/ucs/backup.ucs

# Or use the Ansible module
# bigip_ucs_install:
#   ucs: /var/local/ucs/backup.ucs
#   state: present
```

UCS restore should be the last resort. Prefer Git revert + playbook re-apply whenever possible.

## Rollback Checklist

Before rolling back a production change:

- [ ] Confirm the incident is caused by the recent change (check `tools/drift-check.py`)
- [ ] Identify the exact commit(s) to revert
- [ ] Review the revert diff: `git revert <commit> --no-commit` then `git diff --cached`
- [ ] Notify the team and open an incident ticket
- [ ] Execute the revert during the change window
- [ ] Redeploy and verify via `tools/drift-check.py`
- [ ] Validate application traffic and health checks
- [ ] Document the rollback in the incident ticket
- [ ] After stabilization, investigate root cause on the feature branch

## Config Save and Rollback Safety

The playbooks include a `bigip_config` save step after changes. This means each playbook run saves the running configuration to disk. To preserve rollback points:

- Create a UCS backup before major changes:
  ```yaml
  - name: Pre-change UCS backup
    bigip_ucs_fetch:
      dest: "/backups/pre-change-{{ ansible_date_time.date }}.ucs"
      provider: "{{ provider }}"
    delegate_to: localhost
  ```

- The BIG-IP `load sys ucs` command can restore any previously saved UCS, providing a device-level rollback independent of Git

## Rollback and Drift Detection

After a rollback, run `tools/drift-check.py` to confirm the device matches the reverted Git state:

```sh
F5_HOST=prod-bigip F5_PASSWORD=secret python3 tools/drift-check.py
```

If drift is still reported, investigate whether:
- the revert did not apply to all affected object types
- someone made additional manual changes after the problematic commit
- the playbook failed to apply some objects during the rollback deployment
