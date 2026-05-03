# HA Playbook

## Overview

`playbooks/ha.yml` manages BIG-IP high-availability configuration that is usually applied from one designated device in the sync domain.

This domain covers:

- device connectivity for config sync, failover transport, and connection mirroring
- device trust
- device groups
- device group members
- HA score groups
- traffic groups
- config sync actions

This domain is currently `runtime+validation`, not helper-tool complete. Drift/import support for HA objects is still a separate roadmap decision.

## Playbook Structure

```text
ha.yml                            # Root wrapper entrypoint
playbooks/ha/
├── prep.yml                      # Discovery, include_vars, defaults loading, aggregation
└── tasks/
    ├── manage.yml                # Task ordering + config save
    ├── delete.yml                # state: absent tasks
    └── apply.yml                 # state: present tasks
```

## Var Tree

```text
vars/ha/
├── device_connectivity/
├── device_trust/
├── device_groups/
├── device_group_members/
├── ha_groups/
├── traffic_groups/
├── configsync_actions/
└── deletions/
    ├── device_connectivity/      # intentionally kept for tree shape; deletions are not supported
    ├── device_trust/
    ├── device_groups/
    ├── device_group_members/
    ├── ha_groups/
    ├── traffic_groups/
    └── configsync_actions/       # intentionally kept for tree shape; deletions are not supported
```

## Object Types

### Device Connectivity

Device-local HA transport settings managed with `bigip_device_connectivity`.

Supported fields:

- `config_sync_ip`
- `mirror_primary_address`
- `mirror_secondary_address`
- `unicast_failover`
- `failover_multicast`
- `multicast_interface`
- `multicast_address`
- `multicast_port`
- `cluster_mirroring`

Notes:

- this is device-local state, not shared pair state
- only one active declaration should exist per target BIG-IP
- deletion trees are intentionally not supported for this object family; declare the desired replacement values instead

### Device Trust

Peer trust relationships between BIG-IP devices.

### Device Groups

Shared sync-failover or sync-only groups.

### Device Group Members

Device membership inside a declared device group.

### HA Groups

HA score groups used by traffic groups to prefer the unit with healthier pools or trunks.

Supported fields:

- `name`
- `description`
- `active_bonus`
- `enable`
- `pools`
- `trunks`

Pool entries support:

- `pool_name`
- optional `partition`
- optional `attribute`
- optional `minimum_threshold`
- required `weight`

Trunk entries support:

- `trunk_name`
- optional `attribute`
- optional `minimum_threshold`
- required `weight`

### Traffic Groups

Traffic ownership and failover behavior.

Important constraint:

- set either `ha_order` or `ha_group`
- do not set both on the same traffic group

### Config Sync Actions

One-shot sync operations, such as pushing config from the current target device into a device group.

These are action objects rather than stable long-lived desired state and do not support deletion trees.

## Cross-File Linkages

- `vars/ha/traffic_groups/` may reference `vars/ha/ha_groups/` through `ha_group`
- `vars/ha/ha_groups/` may reference `vars/ltm/pools/` and `vars/network/trunks/`
- `vars/ha/device_group_members/` must reference names declared in `vars/ha/device_groups/`
- `vars/ha/configsync_actions/` must reference names declared in `vars/ha/device_groups/`

## Authoring Pattern

Apply `playbooks/ha.yml` from one designated sync-owner or bootstrap device.

- device connectivity is authored from the current target device's local perspective
- trust is authored from the current target device toward its peer
- device groups, members, HA groups, and traffic groups describe shared HA state, but should still be applied from one designated device in the sync domain

For AWX targeting and operating guidance, see [awx-operation.md](awx-operation.md) and [awx-ha-bootstrap.md](awx-ha-bootstrap.md).
