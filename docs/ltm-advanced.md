# LTM Advanced Fields

The `playbooks/ltm.yml` playbook supports advanced pool, member, and virtual server fields beyond the basic name/address/port model.

## Pool Advanced Fields

### Load Balancing Methods

```yaml
ltm_pools:
  - name: "pool_app"
    lb_method: "least-connections-member"
```

Common methods: `round-robin`, `least-connections-member`, `least-connections-node`, `ratio-member`, `ratio-session`, `fastest-app-response`, `fastest-node`, `observed-member`, `observed-node`, `predictive-member`, `predictive-node`.

### Minimum Active Members

```yaml
ltm_pools:
  - name: "pool_app"
    min_up_members: 1
    min_up_members_action: "reselect"
    min_up_members_checking: "enabled"
```

- `min_up_members`: minimum number of members that must be up
- `min_up_members_action`: `reselect` (pick another pool), `failover` (trigger HA failover), `return` (return 503)
- `min_up_members_checking`: `enabled` or `disabled`

### Priority Group Activation

```yaml
ltm_pools:
  - name: "pool_app"
    priority_group_activation: 1
```

Enables priority-based member selection. Members with higher `priority_group` values receive traffic first. Set to `0` to disable.

### Service Down Action

```yaml
ltm_pools:
  - name: "pool_app"
    service_down_action: "reset"
```

Actions: `none`, `reset`, `reject`, `drop`, `reselect`.

### Slow Ramp Time

```yaml
ltm_pools:
  - name: "pool_app"
    slow_ramp_time: 300
```

Gradually increases connections to a newly available member over N seconds.

### Reselect Tries

```yaml
ltm_pools:
  - name: "pool_app"
    reselect_tries: 3
```

Number of times to try another pool member when the selected member fails.

### Monitor Configuration

```yaml
ltm_pools:
  - name: "pool_app"
    monitors:
      - "standard_https"
    monitor_type: "and_list"
    quorum: 2
```

Monitor aliases (e.g., `standard_https`) expand through sibling `settings.yml`. Use fully-qualified names like `/Common/https` for built-in monitors.

- `monitor_type`: `and_list`, `m_of_n`, `single`
- `quorum`: number of monitors that must pass (used with `m_of_n`)

### Metadata

```yaml
ltm_pools:
  - name: "pool_app"
    metadata:
      - key: "owner"
        value: "platform-team"
```

## Member Advanced Fields

### Priority Group

```yaml
ltm_pools:
  - name: "pool_app"
    members:
      - name: "node-primary"
        host: "10.201.40.11"
        port: 8443
        priority_group: 10
      - name: "node-fallback"
        host: "10.201.40.12"
        port: 8443
        priority_group: 5
```

### Ratio

```yaml
ltm_pools:
  - name: "pool_app"
    members:
      - name: "node-a"
        host: "10.201.40.11"
        port: 8443
        ratio: 3
      - name: "node-b"
        host: "10.201.40.12"
        port: 8443
        ratio: 1
```

### Connection Limit and Rate Limit

```yaml
ltm_pools:
  - name: "pool_app"
    members:
      - name: "node-a"
        host: "10.201.40.11"
        port: 8443
        connection_limit: 1000
        rate_limit: "enabled"
```

### Availability Requirements (for members)

```yaml
ltm_pools:
  - name: "pool_app"
    members:
      - name: "node-a"
        host: "10.201.40.11"
        port: 8443
        availability_requirements:
          type: "all"
```

### FQDN Nodes

```yaml
ltm_pools:
  - name: "pool_app"
    members:
      - name: "node-fqdn"
        fqdn: "app.example.com"
        fqdn_auto_populate: true
        port: 8443
```

### Forced Offline Semantics

Set `state: "disabled"` or `enabled: false` to mark a member as administratively down:

```yaml
ltm_pools:
  - name: "pool_app"
    members:
      - name: "node-maintenance"
        host: "10.201.40.15"
        port: 8443
        enabled: false
```

## Virtual Server Advanced Fields

The current implementation covers the core virtual server fields:

```yaml
ltm_virtual_servers:
  - name: "vs_app_443"
    destination: "10.201.0.80"
    destination_port: 443
    pool: "pool_app"
    snat: "Automap"
    profiles:
      - "/Common/tcp"
      - "http_platform_standard"
    description: "Application VIP"
    enabled: true
```

### Supported Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | string | required | Virtual server name |
| `destination` | string | required | Virtual address |
| `destination_port` | int | required | Virtual port |
| `pool` | string or mapping | required | Pool name or embedded pool |
| `snat` | string | `Automap` | SNAT configuration |
| `profiles` | list | `["tcp"]` | Profile list (mix built-in and custom) |
| `description` | string | - | Description |
| `enabled` | bool | `true` | Admin state |

### Not Yet Implemented

The following virtual server fields are roadmap items:

- persistence profiles
- fallback persistence
- source address translation (custom CIDR)
- VLAN filtering/allow list
- iRule attachments
- LTM policy attachments
- metadata
- log profile references

These will be added as the LTM coverage expands per Phase 4 of the roadmap.

### Profiles

The `profiles` list accepts both built-in BIG-IP profiles (fully-qualified names like `/Common/tcp`) and repo-managed custom profiles (by name, resolving to `vars/ltm/profiles/`):

```yaml
profiles:
  - "/Common/tcp"
  - "http_platform_standard"
  - "oneconnect_platform_standard"
```

See [hybrid-authoring.md](hybrid-authoring.md) for the custom profile model.
