# AWX Job Execution

This document explains how to turn the repo targeting model into safe AWX job templates.

Read this after [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md). Use [05-ha-execution-model.md](05-ha-execution-model.md) for the HA-specific sequence and perspective rules.

## Core Rule

The safest boundary in this repo is the AWX job template target, not ad hoc operator judgment at launch time.

That means:

- keep inventory hosts intentional
- keep job templates narrow
- use selectors only where multi-host runs are genuinely useful
- do not make "all peers in the pair" the default target for shared configuration

## Recommended Template Targets

| Template | Playbook | Default target model |
|---|---|---|
| `BIG-IP Bootstrap` | `playbooks/bootstrap.yml` | one device at a time |
| `BIG-IP System Apply` | `playbooks/system.yml` | one device or one intentionally scoped group |
| `BIG-IP HA Apply` | `playbooks/ha.yml` | one designated sync-owner host per pair unless the change is explicitly device-local |
| `BIG-IP Network Apply` | `playbooks/network.yml` | one designated sync-owner host per pair |
| `BIG-IP TLS Apply` | `playbooks/tls.yml` | one designated sync-owner host per pair |
| `BIG-IP LTM Apply` | `playbooks/ltm.yml` | one designated sync-owner host per pair |
| `BIG-IP GTM Apply` | `playbooks/gtm.yml` | one designated sync-owner host per pair |
| `BIG-IP Security Apply` | `playbooks/security.yml` | one designated sync-owner host per pair |

## Device-Local vs Shared Runs

Use this rule set:

- `bootstrap.yml` is device-local
- `system.yml` can be device-local or group-scoped, depending on selectors in the var model
- `ha.yml` contains both device-local and shared HA concerns, so keep the execution target deliberate
- `network.yml`, `ltm.yml`, `tls.yml`, `gtm.yml`, and most `security.yml` work should normally run from one sync-owner device per HA domain

If a playbook run targets more than one AWX inventory host:

- the play executes once per selected host
- selector-aware objects may match one host and skip another
- prep logs which objects matched or were skipped for each host

## Safe AWX Pattern

The default pattern should be:

1. one AWX inventory host per execution target
2. one `f5_host` per inventory host
3. one sync-owner target per HA pair for shared configuration
4. device-local templates only where that operational boundary is intentional

Example:

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

## What To Avoid

- do not use one broad template that targets every peer in a sync-failover pair by default
- do not store BIG-IP host targeting in the credential
- do not assume HA sync-owner election is automatic
- do not rely on selectors as a substitute for bad inventory design

Selectors are a safety valve for mixed-scope playbooks. AWX inventory and template boundaries are still the first line of control.
