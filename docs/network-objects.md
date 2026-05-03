# Network Objects

The `playbooks/network.yml` playbook manages the layer below LTM: VLANs, trunks, route domains, self IPs, static routes, SNAT translations, SNAT pools, and NATs.

## Object Types

### VLANs

Location: `vars/network/vlans/`

```yaml
bigip_vlans:
  - name: "external"
    tag: 110
    mtu: 1500
    description: "External application network"
    interfaces:
      - interface: "1.1"
        tagging: "tagged"
```

Required: `name`, at least one `interface`. Common fields: `tag`, `mtu`, `description`.

### Trunks

Location: `vars/network/trunks/`

Uses the native `bigip_trunk` module for link aggregation.

```yaml
bigip_trunks:
  - name: "trunk01"
    interfaces:
      - "1.1"
      - "1.2"
    lacp_enabled: true
    lacp_mode: "active"
```

Common fields: `lacp_enabled`, `lacp_mode`, `lacp_timeout`, `link_selection_policy`, `frame_distribution_hash`, `qinq_ethertype`, `description`.

### Route Domains

Location: `vars/network/route_domains/`

```yaml
bigip_route_domains:
  - name: "rd_app"
    id: 10
    strict: true
    vlans:
      - "external"
```

Required: `name` or `id`. Common fields: `parent`, `strict`, `vlans`, `connection_limit`, `routing_protocol`, `bwc_policy`, `flow_eviction_policy`, `fw_enforced_policy`, `service_policy`.

### Self IPs

Location: `vars/network/self_ips/`

Supports both local and floating self IP patterns:

```yaml
bigip_self_ips:
  # Local-only self IP (node-scoped)
  - name: "self_external"
    address: "10.10.11.10"
    netmask: "255.255.255.0"
    vlan: "external"
    traffic_group: "traffic-group-local-only"
    allow_service: "default"

  # Floating self IP (HA-shared, fails over with traffic group)
  - name: "self_external_float"
    address: "10.10.11.11"
    netmask: "255.255.255.0"
    vlan: "external"
    traffic_group: "traffic-group-1"
    allow_service: "default"
```

Required: `name`, `address`, `netmask`, `vlan`. Common fields: `traffic_group`, `allow_service`.

### Static Routes

Location: `vars/network/routes/`

```yaml
bigip_static_routes:
  - name: "default_route"
    destination: "default"
    netmask: "0.0.0.0"
    gateway_address: "10.10.11.1"
    route_domain: 0
```

Required: `name`, one of `destination`/`gateway_address`/`reject`. Common fields: `netmask`, `gateway_address`, `pool`, `reject`, `route_domain`, `vlan`, `mtu`, `description`.

### SNAT Translations

Location: `vars/network/snat_translations/`

Maps a single original IP to a single translated IP:

```yaml
bigip_snat_translations:
  - name: "snat_translate_app1"
    address: "203.0.113.10"
    traffic_group: "traffic-group-1"
```

Required: `name`, `address`. Common fields: `arp`, `connection_limit`, `ip_idle_timeout`, `tcp_idle_timeout`, `udp_idle_timeout`, `traffic_group`, `description`.

### SNAT Pools

Location: `vars/network/snats/`

A pool of translated addresses the BIG-IP picks from:

```yaml
bigip_snat_pools:
  - name: "platform-egress"
    description: "Default outbound SNAT pool"
    members:
      - "platform-egress-a"
      - "platform-egress-b"
```

Required: `name`, `members` (list of SNAT translation names or addresses). Common fields: `description`.

### NATs (tmsh Workflow)

Location: `vars/network/nats/`

NAT object management uses a validated `tmsh` command workflow because the `f5networks.f5_modules` collection does not provide a first-class NAT module.

```yaml
bigip_nats:
  - name: "nat_legacy_outbound_app1"
    originating_address: "10.201.40.50"
    translation_address: "203.0.113.50"
    traffic_group: "/Common/traffic-group-1"
    vlans:
      - "external"
    vlans_enabled: true
    auto_lasthop: "default"
    arp: true
    enabled: true
    description: "Legacy one-to-one NAT"
```

Required: `name`, `originating_address`, `translation_address`. Common fields: `traffic_group`, `vlans`, `vlans_enabled`, `auto_lasthop`, `arp`, `enabled`, `description`.

The `vlans` field references VLAN objects defined in `vars/network/vlans/`. The `traffic_group` field references a BIG-IP traffic group name.

## Cross-References

| Object | References | Points To |
|---|---|---|
| NAT | `vlans` | `vars/network/vlans/*.yml` |
| Self IP | `vlan` | `vars/network/vlans/*.yml` |
| Self IP | `traffic_group` | BIG-IP traffic group (local or HA-shared) |
| SNAT pool | `members` | SNAT translation names or addresses |
| Static route | `pool`, `vlan` | LTM pool or network VLAN |
| Route domain | `vlans` | `vars/network/vlans/*.yml` |

## Deletion

NAT deletion uses the same tmsh workflow. The playbook probes NAT existence before attempting deletion. Other network objects use native `state: absent` modules. See [deletion-workflows.md](deletion-workflows.md).

## Execution Order

The apply order reflects dependencies:

1. VLANs
2. Trunks
3. Route domains
4. Self IPs
5. SNAT translations
6. SNAT pools
7. Static routes
8. NATs

The delete order is the reverse.

## Drift and Import

`tools/drift-check` and `tools/import-from-bigip` now cover:

- VLANs
- trunks
- route domains
- self IPs
- static routes
- SNAT translations
- SNAT pools
- NATs

Current limitation:

- helper-tool parity for these network objects is now `basic field drift` for the core route domain, trunk, SNAT translation, SNAT pool, and NAT fields managed by the runtime playbook
- some advanced live-state attributes may still be richer on the device than what helper tooling can round-trip or compare today
