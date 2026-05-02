# Deletion Workflows

Missing from vars does not mean delete. Objects absent from var trees are simply unmanaged, not removed from the device.

## Supported Patterns

### 1. Inline `state: absent`

Put `state: absent` on an object in its normal tree:

```yaml
ltm_pools:
  - name: "deprecated_pool"
    partition: "Common"
    state: absent
```

### 2. Deletion Trees (Preferred)

Place objects in `vars/*/deletions/...`:

```
vars/
  ltm/
    deletions/
      deprecated-pools.yml
  network/
    deletions/
      old-vlans.yml
```

Deletion trees are the preferred destructive workflow because they make review clearer during pull requests and separate intent from active configuration.

## Execution

Each playbook's `tasks/delete.yml` processes deletion trees before `tasks/apply.yml` runs, so removals happen before additions/updates.
