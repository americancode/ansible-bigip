# AWX HA Bootstrap

This guide walks through bringing up HA for two brand-new BIG-IP devices using AWX.

For the broader first-boot sequence and when to hand off from CLI bootstrap to AWX, see [initial-setup.md](initial-setup.md).

For the general AWX targeting model, inventory patterns, credential design, and template list, see [awx-operation.md](awx-operation.md).

If you need to initialize BIG-IP before AWX can safely reach it (e.g., AWX is fronted by the BIG-IP), use the CLI path in [cli-bootstrap.md](cli-bootstrap.md) and the day-0 runtime in [bootstrap.md](bootstrap.md) first, then adopt this AWX model afterward.

## Example Topology

- east device: `bigip-east.example.com` / `192.0.2.10`
- west device: `bigip-west.example.com` / `192.0.2.20`
- HA pair name: `east-west-prod`
- bootstrap target: east

## Step 1: Set Up AWX Inventory

See [awx-operation.md](awx-operation.md) for the full inventory pattern. Minimum working shape:

```text
Inventory: prod-bigip
Host: bigip-east-sync-owner
Host Variables:
  f5_host: 192.0.2.10
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

Only `f5_host` is required. The rest are for operator clarity.

## Step 2: Set Up AWX Credential

Create a custom credential type using `bigip-credential-config.yaml` and attach a credential instance to your job template. See [awx-operation.md](awx-operation.md) for credential design details.

## Step 3: Create the HA Bootstrap Template

In AWX:

1. Create a job template named `BIG-IP HA Bootstrap`
2. Playbook: `playbooks/ha.yml`
3. Inventory: `prod-bigip`
4. Host: `bigip-east-sync-owner` (the bootstrap device)
5. Credential: attach your BIG-IP auth credential

See [awx-operation.md](awx-operation.md) for the full template list.

## Step 4: Write the Repo HA Vars

The repo-side HA vars should be written from the bootstrap device perspective (east → west).

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

### Initial Config Sync Action

`vars/ha/configsync_actions/manual-sync.yml`:

```yaml
---
ha_configsync_actions:
  - device_group: "dg_platform_sync_failover"
    sync_device_to_group: true
    overwrite_config: false
```

## Step 5: Run the Bootstrap

Launch the `BIG-IP HA Bootstrap` template from AWX.

This will:

- establish device trust from east to west
- create the sync-failover device group
- add both devices as members
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
