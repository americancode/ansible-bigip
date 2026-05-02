# AWX HA Bootstrap

This guide shows one practical way to bring up HA for two brand-new BIG-IP devices with this repository.

If you need to initialize BIG-IP before AWX can safely depend on it, use the terminal-first guide in [docs/cli-bootstrap.md](/Users/nathanielchurchill/source/ansible-bigip/docs/cli-bootstrap.md) first and then adopt this AWX model afterward.

Example topology:

- east device: `bigip-east.example.com`
- west device: `bigip-west.example.com`
- east management IP: `192.0.2.10`
- west management IP: `192.0.2.20`
- HA pair name: `east-west-prod`

The key design rule is simple:

- run `playbooks/ha.yml` against one designated bootstrap device
- after HA is established, run normal shared-config playbooks against one sync-owner device per pair
- keep host selection on the selected AWX inventory host, not in the credential

## AWX Inventory Model

Use one execution target host per HA domain for routine shared configuration.

### Minimum Working Inventory

Only one host var is required by the repo for target selection:

```yaml
f5_host: 192.0.2.10
```

Minimum AWX inventory shape:

```text
Inventory: prod-bigip
Host: bigip-east-sync-owner
Host Variables:
  f5_host: 192.0.2.10
```

Everything else in the richer examples below is optional metadata for clarity and future maintainability.

### AWX UI Steps

In AWX:

1. Create or open the inventory.
2. Add a host, for example `bigip-east-sync-owner`.
3. Open that host.
4. Put this in Host Variables:

```yaml
f5_host: 192.0.2.10
```

That is the normal place to tell this repository which BIG-IP to target.

Recommended inventory:

```text
prod-bigip
├── east_west_prod_pair
│   └── bigip-east-sync-owner
└── ha_peers_reference
    ├── bigip-east-device
    └── bigip-west-device
```

The `ha_peers_reference` group is optional. It is useful for documentation and operator clarity, but should not be the default execution target for shared-config templates.

### Host Vars for the Execution Target

Example host vars for `bigip-east-sync-owner`:

```yaml
f5_host: 192.0.2.10
f5_pair_name: east-west-prod
f5_role: sync_owner
f5_dc: east
f5_ha_peer_host: 192.0.2.20
f5_ha_peer_name: bigip-west.example.com
f5_self_name: bigip-east.example.com
```

Only `f5_host` is required by the playbooks today.

- `f5_pair_name`
- `f5_role`
- `f5_dc`
- `f5_ha_peer_host`
- `f5_ha_peer_name`
- `f5_self_name`

are optional metadata fields for operator clarity and future inventory organization.

Optional reference-only host vars:

```yaml
# bigip-east-device
f5_host: 192.0.2.10
f5_device_name: bigip-east.example.com

# bigip-west-device
f5_host: 192.0.2.20
f5_device_name: bigip-west.example.com
```

## AWX Credential Injection

This repository reads BIG-IP connection details from [vars/common.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/common.yml):

- inventory or template var `f5_host`
- `F5_USERNAME`
- `F5_PASSWORD`
- optional `F5_SERVER_PORT`
- optional `F5_VALIDATE_CERTS`

Recommended pattern:

- store username and password in the AWX credential
- do not store the BIG-IP host in the credential
- set the target BIG-IP in the selected inventory host var `f5_host`
- let `vars/common.yml` resolve `provider.server` from that inventory value

The sample credential type in [bigip-credential-config.yaml](/Users/nathanielchurchill/source/ansible-bigip/bigip-credential-config.yaml) is auth-only and injects:

- `F5_USERNAME`
- `F5_PASSWORD`
- optional `F5_SERVER_PORT`
- optional `F5_VALIDATE_CERTS`

## AWX Job Templates

Recommended templates:

- `BIG-IP HA Bootstrap`
  - playbook: `playbooks/ha.yml`
  - inventory target: `east_west_prod_pair`
  - intended initial target host: `bigip-east-sync-owner`
- `BIG-IP Network Apply`
  - playbook: `playbooks/network.yml`
  - inventory target: one sync-owner host per pair
- `BIG-IP LTM Apply`
  - playbook: `playbooks/ltm.yml`
  - inventory target: one sync-owner host per pair
- `BIG-IP TLS Apply`
  - playbook: `playbooks/tls.yml`
  - inventory target: one sync-owner host per pair
- `BIG-IP System Apply`
  - playbook: `playbooks/system.yml`
  - inventory target: one sync-owner host per pair unless you intentionally need device-local differences

Safe default:

- do not target both peers in the pair for normal shared configuration
- if you later create a `bigip-west-sync-owner` host for disaster recovery procedures, do not make it the default execution target for routine jobs

## Repo Vars for Initial HA Bring-Up

For a new pair, the repo-side HA vars should be written from the bootstrap device perspective.

If AWX will run `playbooks/ha.yml` against `bigip-east-sync-owner`, then the trust file should point from east to west.

### Device Trust

[vars/ha/device_trust/foundation-peer.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/ha/device_trust/foundation-peer.yml)

```yaml
---
ha_device_trusts:
  - peer_server: "192.0.2.20"
    peer_hostname: "bigip-west.example.com"
    type: "peer"
```

Meaning:

- current target device = east
- peer to trust = west

### Device Group

[vars/ha/device_groups/foundation-groups.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/ha/device_groups/foundation-groups.yml)

```yaml
---
ha_device_groups:
  - name: "dg_platform_sync_failover"
    type: "sync-failover"
    auto_sync: true
    network_failover: true
    save_on_auto_sync: true
    full_sync: false
    description: "Primary sync-failover device group for the platform estate"
```

### Device Group Members

[vars/ha/device_group_members/foundation-members.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/ha/device_group_members/foundation-members.yml)

```yaml
---
ha_device_group_members:
  - device_group: "dg_platform_sync_failover"
    name: "bigip-east.example.com"

  - device_group: "dg_platform_sync_failover"
    name: "bigip-west.example.com"
```

### Traffic Group

[vars/ha/traffic_groups/foundation-traffic-groups.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/ha/traffic_groups/foundation-traffic-groups.yml)

```yaml
---
ha_traffic_groups:
  - name: "traffic-group-apps"
    partition: "Common"
    ha_order:
      - "/Common/bigip-east.example.com"
      - "/Common/bigip-west.example.com"
    auto_failback: true
    auto_failback_time: 60
    ha_load_factor: 10
```

### Initial Config Sync Action

[vars/ha/configsync_actions/manual-sync.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/ha/configsync_actions/manual-sync.yml)

```yaml
---
ha_configsync_actions:
  - device_group: "dg_platform_sync_failover"
    sync_device_to_group: true
    overwrite_config: false
```

Meaning:

- push configuration from the current target device
- with the example inventory above, that means push from east into the device group

## Bootstrap Workflow

For two brand-new devices:

1. Ensure both appliances have base management reachability and working admin credentials.
2. Create the AWX inventory and credential.
3. Put `f5_host: 192.0.2.10` on `bigip-east-sync-owner`.
4. Point the `BIG-IP HA Bootstrap` template at the one bootstrap target host, for example `bigip-east-sync-owner`.
5. Attach the auth-only BIG-IP credential to the template.
6. Run `playbooks/ha.yml`.
7. Verify trust, device group membership, traffic groups, and config sync status on the pair.
8. Use the same sync-owner execution target for `network.yml`, `ltm.yml`, and `tls.yml`.

## After HA Exists

Once the pair is healthy:

- continue to use one execution target host per pair for shared configuration
- let config sync or auto-sync move shared config to the peer
- only run against both devices intentionally, not by default

For multiple datacenters:

- create one execution target per HA pair
- run one job per pair
- do not treat every appliance in every datacenter as the same execution group

## What This Repo Does Not Do Automatically

This repository does not currently:

- discover the active device automatically
- elect a sync owner automatically
- prevent a mis-scoped AWX template from targeting both peers

That control belongs in AWX inventory and template design. The safe pattern is to make the inventory target itself represent the intended execution boundary.
