# LTM Advanced Fields

The `playbooks/ltm.yml` playbook supports advanced pool, member, virtual server, iRule, data group, persistence profile, and policy objects.

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

## Virtual Server Fields

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
    default_persistence_profile: "source_addr_standard"
    irules:
      - "irule_redirect_http_to_https"
    policies:
      - "policy_http_to_https_redirect"
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
| `default_persistence_profile` | string | - | Default persistence profile name |
| `fallback_persistence_profile` | string | - | Fallback persistence profile name |
| `irules` | list | - | iRule names to attach |
| `policies` | list | - | LTM policy names to attach |
| `description` | string | - | Description |
| `enabled` | bool | `true` | Admin state |

### Not Yet Implemented

The following virtual server fields are roadmap items:

- source address translation (custom CIDR)
- VLAN filtering/allow list
- metadata
- log profile references

## Persistence Profiles

Location: `vars/ltm/persistence/`

First-class persistence profiles that can be referenced by virtual servers via `default_persistence_profile` and `fallback_persistence_profile`.

### Cookie Persistence

```yaml
ltm_persistence_profiles:
  - name: "cookie_app_session"
    type: "cookie"
    description: "Cookie-based session affinity"
    cookie_name: "BIGipServer"
    cookie_encryption: true
    cookie_fallback: true
```

### Source Address Persistence

```yaml
ltm_persistence_profiles:
  - name: "source_addr_standard"
    type: "source_addr"
    description: "Source IP persistence"
    match_across_services: true
    match_across_virtuals: false
    override_connection_limit: false
```

### Universal Persistence

```yaml
ltm_persistence_profiles:
  - name: "universal_custom"
    type: "universal"
    description: "Universal persistence for custom key extraction"
    match_across_services: true
```

Supported types: `cookie`, `source_addr`, `universal`.

## iRules

Location: `vars/ltm/irules/`

First-class iRules referenced by name from `ltm_virtual_servers[*].irules`:

```yaml
ltm_irules:
  - name: "irule_redirect_http_to_https"
    description: "Redirect HTTP to HTTPS"
    rule: |
      when HTTP_REQUEST {
          HTTP::redirect "https://[HTTP::host][HTTP::uri]"
      }
```

## Data Groups

Location: `vars/ltm/data_groups/`

Reusable data groups for iRules and policies:

```yaml
ltm_data_groups:
  - name: "dg_internal_subnets"
    type: "ip"
    description: "Trusted internal subnets"
    records:
      - "10.0.0.0/8"
      - "172.16.0.0/12"

  - name: "dg_blocked_uris"
    type: "string"
    description: "Blocked URI paths"
    records:
      - "/admin"
      - "/debug"

  - name: "dg_redirect_map"
    type: "string"
    description: "Old-to-new URL mapping"
    records:
      - name: "/old-app"
        value: "/new-app"
```

Supported types: `string`, `ip`, `integer`. String type supports key/value pairs via the `name`/`value` record format.

## LTM Policies

Location: `vars/ltm/policies/`

First-class policies referenced by name from `ltm_virtual_servers[*].policies`:

```yaml
ltm_policies:
  - name: "policy_http_to_https_redirect"
    description: "Redirect HTTP to HTTPS"
    strategy: "/Common/first-match"
    rules:
      - name: "redirect_http"
        description: "Match and redirect"
        conditions:
          - name: "is_http"
            type: "tcp"
            tcp:
              field: "request"
              present: true
        actions:
          - name: "redirect"
            type: "http"
            http:
              location: "https://[HTTP::host][HTTP::uri]"
              redirect: true
```

### Profiles

The `profiles` list on virtual servers accepts both built-in BIG-IP profiles (fully-qualified names like `/Common/tcp`) and repo-managed custom profiles (by name, resolving to `vars/ltm/profiles/`):

```yaml
profiles:
  - "/Common/tcp"
  - "http_platform_standard"
  - "oneconnect_platform_standard"
```

See [hybrid-authoring.md](hybrid-authoring.md) for the custom profile model.
