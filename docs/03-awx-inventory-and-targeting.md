# AWX Inventory and Targeting

This document covers the normal AWX-side targeting contract for this repository.

Use it with:

- [01-awx-operating-model-and-handoff.md](01-awx-operating-model-and-handoff.md) for the overall operator story
- [04-awx-job-execution.md](04-awx-job-execution.md) for job-template execution boundaries
- [05-ha-execution-model.md](05-ha-execution-model.md) for HA-specific sync-owner behavior

## Core Targeting Model

This repository talks to one BIG-IP management endpoint per inventory host execution.

- the playbooks use the `provider` object in `vars/common.yml`
- canonical playbooks target AWX inventory hosts with `connection: local`
- `provider.server` prefers the inventory host var `f5_host`
- `F5_HOST` is an environment fallback for local testing or one-off runs
- each selected inventory host resolves its own BIG-IP target through `f5_host`
- if an AWX job targets more than one inventory host, the playbook runs once per selected host

## AWX Inventory Pattern

Treat AWX inventory names as part of the repo contract.

- `inventory_hostname` is what `target_hosts` matches
- Ansible `group_names` are what `target_groups` matches
- `f5_host` is the actual BIG-IP management endpoint

Use one execution target host per HA domain for routine shared configuration.

When a playbook is used against more than one inventory host, object-level selectors in the repo can become part of the targeting contract:

- `target_hosts` matches AWX `inventory_hostname`
- `target_groups` matches AWX inventory group names
- a shared group such as `all_bigip` should be deliberate and documented, not accidental

### Host Vars

Minimum required:

```yaml
f5_host: bigip-east.example.com
```

Optional metadata for clarity:

```yaml
f5_host: bigip-east.example.com
f5_pair_name: east-prod-pair
f5_role: sync_owner
f5_dc: east
```

Recommended reserved group names when using targeted objects:

```text
all_bigip
east_prod
west_prod
sync_owners
```

### Recommended Inventory Shape

```text
prod-bigip
├── east_west_prod_pair
│   └── bigip-east-sync-owner
└── ha_peers_reference
    ├── bigip-east-device
    └── bigip-west-device
```

The `ha_peers_reference` group is optional for documentation and operator clarity. It should not be the default execution target for shared-config templates.

## Selector-Aware Objects

Object-level selectors are now part of the authoring model when you need one playbook run to target some inventory hosts but not others.

- `target_hosts` matches AWX `inventory_hostname`
- `target_groups` matches AWX inventory group names
- prep logs how many objects matched and how many were skipped for the current host
- validation rejects ambiguous selector patterns before runtime

Example:

```yaml
system_dns:
  - name_servers:
      - "192.0.2.53"
      - "192.0.2.54"
    target_groups:
      - "all_bigip"
```

## Credential Design

This repository reads connection details from `vars/common.yml`:

- `f5_host` must come from AWX inventory host vars for normal AWX operation
- `F5_USERNAME`, `F5_PASSWORD` come from AWX credentials or environment
- optional `F5_VALIDATE_CERTS`

Recommended pattern:

- store username and password in an AWX custom credential type
- do not store the BIG-IP host in the credential
- set the target BIG-IP in the selected inventory host var `f5_host`
- let `vars/common.yml` resolve `provider.server` from that inventory value

The sample credential type in `bigip-credential-config.yaml` is auth-only and injects:

- `F5_USERNAME`
- `F5_PASSWORD`
- optional `F5_VALIDATE_CERTS`

Do not put BIG-IP host or port in the AWX credential. Target selection must come from the inventory host var `f5_host`.

## What This Repo Does Not Do Automatically

- discover the active device automatically
- elect a sync owner automatically
- prevent a mis-scoped AWX template from targeting both peers

That control belongs in AWX inventory and template design. The safe pattern is to make the inventory target itself represent the intended execution boundary.

## Bootstrap Guides

- primary first-boot path: [01-awx-operating-model-and-handoff.md](01-awx-operating-model-and-handoff.md)
- day-0 bootstrap domain reference: [02-bootstrap-playbook.md](02-bootstrap-playbook.md)
- CLI fallback path: [cli-bootstrap-and-recovery.md](cli-bootstrap-and-recovery.md)
- AWX job execution: [04-awx-job-execution.md](04-awx-job-execution.md)
- HA execution model: [05-ha-execution-model.md](05-ha-execution-model.md)
