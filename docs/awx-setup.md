# AWX Setup Guide

This is the concrete setup runbook for operating this repository through AWX.

Use this after [01-awx-operating-model-and-handoff.md](01-awx-operating-model-and-handoff.md). The numbered AWX docs explain the model; this page turns that model into an actual AWX build sheet.

## Intended Outcome

At the end of this setup:

- AWX can sync this repository as a project
- AWX inventory hosts represent execution targets, not just peer references
- each execution target host has a correct `f5_host`
- credentials provide authentication only
- job templates map cleanly to canonical playbooks
- operators have a repeatable audit-first launch path

## 1. Create the AWX Project

Create an AWX project that syncs this repository.

Recommended project settings:

- source control: the Git repository for this project
- update revision on launch: enabled for production GitOps workflows
- branch: your normal promotion branch for that environment

The playbooks to expose from this project are:

- `playbooks/bootstrap.yml`
- `playbooks/system.yml`
- `playbooks/ha.yml`
- `playbooks/network.yml`
- `playbooks/tls.yml`
- `playbooks/ltm.yml`
- `playbooks/gtm.yml`
- `playbooks/security.yml`

## 2. Create the BIG-IP Credential

Use a credential type that injects:

- `F5_USERNAME`
- `F5_PASSWORD`
- optional `F5_VALIDATE_CERTS`

Do not put the BIG-IP host in the credential. Targeting belongs to the AWX inventory host var `f5_host`.

See [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md) for the targeting contract.

## 3. Build the Inventory Around Execution Targets

The inventory host is the execution boundary.

- one inventory host should represent one BIG-IP execution target
- one execution target should have one `f5_host`
- for shared configuration in HA, use one designated sync-owner host per pair

### Minimum host vars

```yaml
f5_host: 192.0.2.10
```

### Useful optional host vars

```yaml
f5_host: 192.0.2.10
f5_pair_name: east-west-prod
f5_role: sync_owner
f5_dc: east
```

### Recommended group shape

```text
prod-bigip
├── east_prod
│   └── bigip-east-sync-owner
├── west_prod
│   └── bigip-west-sync-owner
└── all_bigip
    ├── bigip-east-device
    ├── bigip-west-device
    ├── bigip-central-device
    └── bigip-dr-device
```

Use `all_bigip` only when object-level selectors intentionally target a broad fleet. Do not make it the default launch target for shared configuration.

## 4. Decide the Bootstrap Boundary

If the BIG-IP is already reachable on its stable management endpoint and AWX can route to it, start in AWX.

If the device still needs licensing or first management-IP cutover, bootstrap first through the CLI path:

1. run `playbooks/bootstrap.yml` from the terminal path in [cli-bootstrap-and-recovery.md](cli-bootstrap-and-recovery.md)
2. update the AWX inventory host var `f5_host` if bootstrap changed the management IP
3. move the rest of the lifecycle into AWX

## 5. Create the Job Templates

Recommended baseline templates:

| Template | Playbook | Normal target |
|---|---|---|
| `BIG-IP Bootstrap` | `playbooks/bootstrap.yml` | one device at a time |
| `BIG-IP System Apply` | `playbooks/system.yml` | one device or one intentional selector-scoped group |
| `BIG-IP HA Apply` | `playbooks/ha.yml` | one sync-owner host per pair |
| `BIG-IP Network Apply` | `playbooks/network.yml` | one sync-owner host per pair |
| `BIG-IP TLS Apply` | `playbooks/tls.yml` | one sync-owner host per pair |
| `BIG-IP LTM Apply` | `playbooks/ltm.yml` | one sync-owner host per pair |
| `BIG-IP GTM Apply` | `playbooks/gtm.yml` | one sync-owner host per pair |
| `BIG-IP Security Apply` | `playbooks/security.yml` | one sync-owner host per pair |

Attach:

- the Git project
- the correct inventory
- the BIG-IP auth credential

## 6. Use an Audit-First Launch Pattern

Before a production apply:

1. run `make validate`
2. launch the same playbook with `audit_mode=true`
3. review the printed delete/apply collections for the selected host
4. launch the normal apply only after the audit output matches intent

For command-driven flows such as bootstrap management changes, NATs, or the system login banner, use `show_tmsh_commands=true` when you need to inspect the generated commands before execution.

## 7. Recommended Rollout Sequence

### Standalone device

1. bootstrap from CLI if needed
2. `BIG-IP System Apply`
3. `BIG-IP Network Apply`
4. `BIG-IP TLS Apply`
5. `BIG-IP LTM Apply`
6. `BIG-IP GTM Apply` if used
7. `BIG-IP Security Apply` if used

### HA pair

1. bootstrap from CLI if needed
2. `BIG-IP System Apply`
3. `BIG-IP HA Apply` from the designated sync-owner host
4. verify trust and sync health
5. `BIG-IP Network Apply` from the same sync-owner host
6. `BIG-IP TLS Apply` from the same sync-owner host
7. `BIG-IP LTM Apply` from the same sync-owner host
8. `BIG-IP GTM Apply` from the same sync-owner host if used
9. `BIG-IP Security Apply` from the same sync-owner host if used

## 8. What To Avoid

- do not store the BIG-IP host inside the credential
- do not target both peers by default for shared configuration
- do not assume the repo elects a sync owner automatically
- do not use selectors as a substitute for correct AWX inventory design

## Related Docs

- [01-awx-operating-model-and-handoff.md](01-awx-operating-model-and-handoff.md)
- [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md)
- [04-awx-job-execution.md](04-awx-job-execution.md)
- [05-ha-execution-model.md](05-ha-execution-model.md)
- [validation.md](validation.md)
