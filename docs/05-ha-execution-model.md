# HA Execution Model

This guide explains how HA should be executed once AWX can safely reach the devices.

This is not a separate control-plane story. It is the HA-specific part of the normal AWX operating model:

1. start with [01-awx-operating-model-and-handoff.md](01-awx-operating-model-and-handoff.md)
2. if the device still needs day-0 reachability work, use [cli-bootstrap-and-recovery.md](cli-bootstrap-and-recovery.md) and [02-bootstrap-playbook.md](02-bootstrap-playbook.md) first
3. use [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md) and [04-awx-job-execution.md](04-awx-job-execution.md) to set up safe AWX execution boundaries
4. then use this guide for the HA sequence itself

## Example Topology

- east device: `bigip-east.example.com` / `192.0.2.10`
- west device: `bigip-west.example.com` / `192.0.2.20`
- HA pair name: `east-west-prod`
- designated sync-owner target: east

## Step 1: Set Up AWX Inventory

See [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md) for the full inventory pattern. Minimum working shape:

```text
Inventory: prod-bigip
Host: bigip-east-sync-owner
Host Variables:
  f5_host: 192.0.2.10
  # optional if API is not on 443
  # f5_server_port: 8443
```

Richer host vars with optional metadata:

```yaml
f5_host: 192.0.2.10
f5_pair_name: east-west-prod
f5_role: sync_owner
f5_dc: east
f5_ha_peer_host: 192.0.2.20
f5_ha_peer_name: bigip-west.example.com
f5_self_name: bigip-east.example.com
```

Only `f5_host` is required. Use `f5_server_port` only when that host uses a non-default BIG-IP API port.

## Step 2: Set Up AWX Credential

Create a custom credential type using `bigip-credential-config.yaml` and attach a credential instance to your job template. See [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md) for credential design details.
The credential is auth-only (username/password plus optional cert validation). Host targeting must come from inventory host vars (`f5_host`, optional `f5_server_port`).

## Step 3: Create the HA Template

In AWX:

1. Create a job template named `BIG-IP HA Apply`
2. Playbook: `playbooks/ha.yml`
3. Inventory: `prod-bigip`
4. Host: `bigip-east-sync-owner` (the designated sync-owner target)
5. Credential: attach your BIG-IP auth credential

See [04-awx-job-execution.md](04-awx-job-execution.md) for the broader template model.

## Step 4: Write the Repo HA Vars

The repo-side HA vars should be written from the current execution target perspective (east → west in this example).

### Device Connectivity

Optional but recommended when you want config sync, failover transport, and connection mirroring to be declared in Git.

`vars/ha/device_connectivity/foundation-connectivity.yml`:

```yaml
---
ha_device_connectivity:
  - config_sync_ip: "10.10.20.11"
    mirror_primary_address: "10.10.20.11"
    unicast_failover:
      - address: "management-ip"
      - address: "10.10.20.11"
        port: 1026
```

### Device Trust

`vars/ha/device_trust/foundation-peer.yml`:

```yaml
---
ha_device_trusts:
  - peer_server: "192.0.2.20"
    peer_hostname: "bigip-west.example.com"
    type: "peer"
```

### Device Group

`vars/ha/device_groups/foundation-groups.yml`:

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

`vars/ha/device_group_members/foundation-members.yml`:

```yaml
---
ha_device_group_members:
  - device_group: "dg_platform_sync_failover"
    name: "bigip-east.example.com"

  - device_group: "dg_platform_sync_failover"
    name: "bigip-west.example.com"
```

### Traffic Group

`vars/ha/traffic_groups/foundation-traffic-groups.yml`:

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

### Optional HA Score Group

Use this when you want a traffic group to prefer the unit with healthier pools or trunk members instead of using a fixed `ha_order`.

`vars/ha/ha_groups/foundation-ha-groups.yml`:

```yaml
---
ha_groups:
  - name: "hg_apps_prefer_healthy_pools"
    active_bonus: 15
    pools:
      - pool_name: "vm-apps-main"
        weight: 60
        minimum_threshold: 1
    trunks:
      - trunk_name: "trunk-uplink-a"
        weight: 40
        minimum_threshold: 1
```

### Initial Config Sync Action

`vars/ha/configsync_actions/manual-sync.yml`:

```yaml
---
ha_configsync_actions:
  - device_group: "dg_platform_sync_failover"
    sync_device_to_group: true
    overwrite_config: false
```

## Step 5: Run the HA Apply

Launch the `BIG-IP HA Apply` or equivalent HA-specific template from AWX.

This will:

- configure device-local HA connectivity on east if declared
- establish device trust from east to west
- create the sync-failover device group
- add both devices as members
- create any HA score groups referenced by traffic groups
- create the traffic group with failover ordering
- push config from east into the device group

## Step 6: Verify

Check on the BIG-IP UI or CLI:

- device trust exists between east and west
- sync-failover group exists with both members
- traffic group ordering is correct
- config sync status is healthy

## Step 7: Apply Shared Config

After the pair is healthy, use the same `bigip-east-sync-owner` execution target for routine playbooks:

- `BIG-IP Network Apply`
- `BIG-IP TLS Apply`
- `BIG-IP LTM Apply`
- `BIG-IP System Apply`
- `BIG-IP GTM Apply`

Do not target both peers for routine shared-config jobs. Let config sync replicate changes to the peer.

## After HA Exists

- continue using one execution target host per pair
- for multiple datacenters, create one execution target per HA pair and run one job per pair
