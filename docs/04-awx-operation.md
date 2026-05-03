# AWX and HA Operation

## Targeting Model

This repository talks to one BIG-IP management endpoint per run.

- the playbooks use the `provider` object in `vars/common.yml`
- canonical playbooks target AWX inventory hosts with `connection: local`
- `provider.server` prefers the inventory host var `f5_host`
- `F5_HOST` is an environment fallback for local testing or one-off runs
- if `f5_host` or `F5_HOST` points at one BIG-IP, only that BIG-IP is directly configured by that job

## HA Operating Rule

For a normal BIG-IP sync-failover pair, most shared configuration should be applied to one designated device in the HA domain and then replicated through config sync.

Safe defaults:

- for `playbooks/network.yml`, `playbooks/ltm.yml`, and `playbooks/tls.yml`, target one sync-owner device per HA pair
- use `playbooks/ha.yml` to establish or change device connectivity, trust, device groups, members, HA groups, traffic groups, and config sync actions
- do not target both peers in the same HA pair for routine shared-config jobs unless you explicitly mean to

## HA Vars Perspective

The HA example vars under `vars/ha/...` are written from the target device perspective:

- `device_trust` examples are authored from the current target device toward its peer
- `device_connectivity` examples are authored from the current target device's local management and failover-network perspective
- `device_groups`, `device_group_members`, and `traffic_groups` describe shared HA state, but are meant to be applied from one designated device in the sync domain
- `ha_groups` are shared HA score objects that traffic groups may reference through `ha_group`
- `configsync_actions.sync_device_to_group: true` means "push from the device currently selected as the execution target"

## AWX Inventory Pattern

Use one execution target host per HA domain for routine shared configuration.

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

## Credential Design

This repository reads connection details from `vars/common.yml`:

- `f5_host` comes from inventory or template vars
- `F5_USERNAME`, `F5_PASSWORD` come from AWX credentials or environment
- optional `F5_SERVER_PORT`
- optional `F5_VALIDATE_CERTS`

Recommended pattern:

- store username and password in an AWX custom credential type
- do not store the BIG-IP host in the credential
- set the target BIG-IP in the selected inventory host var `f5_host`
- let `vars/common.yml` resolve `provider.server` from that inventory value

The sample credential type in `bigip-credential-config.yaml` is auth-only and injects:

- `F5_USERNAME`
- `F5_PASSWORD`
- optional `F5_SERVER_PORT`
- optional `F5_VALIDATE_CERTS`

## AWX Job Templates

| Template | Playbook | Target |
|---|---|---|
| `BIG-IP HA Bootstrap` | `playbooks/ha.yml` | one sync-owner host per pair |
| `BIG-IP Network Apply` | `playbooks/network.yml` | one sync-owner host per pair |
| `BIG-IP LTM Apply` | `playbooks/ltm.yml` | one sync-owner host per pair |
| `BIG-IP TLS Apply` | `playbooks/tls.yml` | one sync-owner host per pair |
| `BIG-IP System Apply` | `playbooks/system.yml` | one sync-owner host per pair |
| `BIG-IP GTM Apply` | `playbooks/gtm.yml` | one sync-owner host per pair |

Safe default: do not target both peers in the pair for normal shared configuration. If you later create a secondary sync-owner host for disaster recovery, do not make it the default target for routine jobs.

## Multi-Datacenter

Treat each datacenter HA pair as its own execution boundary. Run one job per pair, not one job per appliance.

## What This Repo Does Not Do Automatically

- discover the active device automatically
- elect a sync owner automatically
- prevent a mis-scoped AWX template from targeting both peers

That control belongs in AWX inventory and template design. The safe pattern is to make the inventory target itself represent the intended execution boundary.

## Bootstrap Guides

- primary first-boot path: [01-initial-setup-and-handoff.md](01-initial-setup-and-handoff.md)
- day-0 bootstrap domain reference: [02-bootstrap-playbook.md](02-bootstrap-playbook.md)
- CLI-first execution path: [03-cli-bootstrap.md](03-cli-bootstrap.md)
- AWX HA step-by-step after bootstrap: [05-awx-ha-bootstrap.md](05-awx-ha-bootstrap.md)
