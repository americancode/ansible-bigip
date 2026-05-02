# GTM Advanced Fields

The `playbooks/gtm.yml` playbook manages GTM/DNS traffic: monitors, datacenters, servers, pools, and Wide IPs.

## Wide IP Advanced Fields

### Record Types

```yaml
gtm_wide_ips:
  - name: "app.example.com"
    record_type: "a"
```

Supported record types: `a`, `aaaa`, `cname`, `mx`, `naptr`, `srv`.

### Pool Load Balancing

```yaml
gtm_wide_ips:
  - name: "app.example.com"
    record_type: "a"
    pool_lb_method: "topology"
```

Common methods: `topology`, `global-availability`, `round-robin`.

### Aliases

Wide IPs can have CNAME aliases pointing to other Wide IPs:

```yaml
gtm_wide_ips:
  - name: "app.example.com"
    record_type: "a"
    aliases:
      - "www.example.com"
    pools:
      - name: "pool_app_east"
```

### Persistence

Wide IP-level DNS persistence keeps clients directed to the same pool:

```yaml
gtm_wide_ips:
  - name: "app.example.com"
    record_type: "a"
    persistence: "persist-cidr-ipv4"
    pools:
      - name: "pool_app_east"
```

### Last Resort Pool

When all pools are down, the last resort pool serves as a fallback:

```yaml
gtm_wide_ips:
  - name: "app.example.com"
    record_type: "a"
    last_resort_pool: "pool_fallback"
    pools:
      - name: "pool_app_east"
```

### Load Balancing Policy Combinations

Wide IPs support three-tier LB method selection:

```yaml
gtm_wide_ips:
  - name: "app.example.com"
    record_type: "a"
    pool_lb_method: "topology"
    pools:
      - name: "pool_app_east"
        preferred_lb_method: "global-availability"
        alternate_lb_method: "round-robin"
        fallback_lb_method: "round-robin"
```

## GTM Pool Advanced Fields

### Record Type and Load Balancing

```yaml
gtm_pools:
  - name: "pool_app_global"
    record_type: "a"
    preferred_lb_method: "topology"
    alternate_lb_method: "global-availability"
    fallback_lb_method: "round-robin"
```

### TTL and Max Answers

```yaml
gtm_pools:
  - name: "pool_app_global"
    record_type: "a"
    ttl: 30
    max_answers_returned: 5
```

### Fallback IP

```yaml
gtm_pools:
  - name: "pool_app_global"
    record_type: "a"
    fallback_ip: "192.0.2.100"
```

Returns this IP when all members are down.

### Monitor Configuration

```yaml
gtm_pools:
  - name: "pool_app_global"
    monitors:
      - "inventory_https"
```

Monitor aliases expand through `vars/gtm/pools/settings.yml`. Pools can also use `default_monitors` for member-level overrides.

### Availability Requirements

```yaml
gtm_pools:
  - name: "pool_app_global"
    availability_requirements:
      type: "all"
```

## GTM Pool Members

### Server and Virtual Server Linkage

```yaml
gtm_pools:
  - name: "pool_app_global"
    record_type: "a"
    members:
      - server: "bigip-east"
        virtual_server: "vs_app_east_443"
```

The `server` field references a GTM server in `vars/gtm/servers/`. The `virtual_server` field references a repo-known LTM virtual server in `vars/ltm/virtual_servers/`.

### LTM Virtual Resolution

When `address` and `port` are omitted, `gtm.yml` resolves them from the referenced LTM virtual server:

```yaml
gtm_pools:
  - name: "pool_app_global"
    record_type: "a"
    members:
      - server: "bigip-east"
        virtual_server: "vs_app_east_443"
      - server: "bigip-west"
        virtual_server: "vs_app_west_443"
```

Explicit override when GTM member name differs from LTM virtual server name:

```yaml
      - server: "bigip-west"
        virtual_server: "vs_app_west_443"
        ltm_virtual_server: "vs_app_west_443"
        address: "10.202.0.80"
        port: 443
```

### Explicit Address and Port

```yaml
gtm_pools:
  - name: "pool_app_global"
    record_type: "a"
    members:
      - server: "bigip-east"
        virtual_server: "vs_app_east_443"
        address: "10.201.0.80"
        port: 443
```

### Member-Level Monitors

```yaml
      - server: "bigip-east"
        virtual_server: "vs_app_east_443"
        monitors:
          - "custom_https"
```

## GTM Servers

### BIG-IP Servers

```yaml
gtm_servers:
  - name: "bigip-east"
    datacenter: "us-east"
    address: "10.201.0.1"
```

### Static Servers

```yaml
gtm_servers:
  - name: "static-dns-1"
    datacenter: "us-east"
    server_type: "generic-host"
    addresses:
      - "192.0.2.53"
```

### Server Advanced Fields

```yaml
gtm_servers:
  - name: "bigip-east"
    datacenter: "us-east"
    monitors:
      - "/Common/bigip"
    virtual_server_discovery: "enabled"
    link_discovery: "enabled"
    prober_pool: "prober_pool_east"
    prober_preference: "inside-datacenter"
```

## GTM Topology Regions

Location: `vars/gtm/regions/`

Topology regions define logical geographic or network groupings used by topology-based load balancing. Regions combine continents, countries, datacenters, subnets, or ISPs into named groupings:

```yaml
gtm_topology_regions:
  - name: "us-east"
    description: "US East Coast region"
    region_members:
      - continent: "North America"
      - country: "US"
      - datacenter: "/Common/dc-east"

  - name: "emea"
    description: "Europe, Middle East, and Africa"
    region_members:
      - continent: "Europe"
      - continent: "Africa"
      - country: "GB"
      - country: "DE"
```

### Region Member Keys

| Key | Example | Description |
|---|---|---|
| `continent` | `"North America"` | Geographic continent |
| `country` | `"US"` | ISO country code |
| `datacenter` | `"/Common/dc-east"` | GTM datacenter name |
| `subnet` | `"10.0.0.0/8"` | IP subnet (CIDR) |
| `isp` | `"AOL"` | ISP name |

## GTM Topology Records

Location: `vars/gtm/topology/`

Topology records define source-to-destination weighted mappings for DNS traffic steering. When a GTM pool or Wide IP uses `preferred_lb_method: topology`, the system evaluates these records to determine which pool serves which source:

```yaml
gtm_topology_records:
  - source:
      - region: "us-east"
    destination:
      - pool: "/Common/pool_app_east"
    weight: 100

  - source:
      - region: "emea"
    destination:
      - pool: "/Common/pool_app_europe"
    weight: 100

  - source:
      - subnet: "10.0.0.0/8"
    destination:
      - pool: "/Common/pool_internal"
    weight: 100
```

### Source and Destination Keys

Both `source` and `destination` lists use the same member keys as regions, plus `region` and `pool`:

| Key | Example | Description |
|---|---|---|
| `region` | `"us-east"` | Topology region name |
| `pool` | `"/Common/pool_app"` | GTM pool name |
| `continent` | `"North America"` | Geographic continent |
| `country` | `"US"` | ISO country code |
| `datacenter` | `"/Common/dc-east"` | GTM datacenter name |
| `subnet` | `"10.0.0.0/8"` | IP subnet (CIDR) |
| `isp` | `"AOL"` | ISP name |
| `negate` | `true` | Invert the match (used with any key above) |

### Negation Example

```yaml
gtm_topology_records:
  - source:
      - region: "us-east"
      - negate: true
    destination:
      - pool: "/Common/pool_fallback"
    weight: 50
    description: "All non-US-East traffic to fallback pool"
```

### Weights

Higher weights are preferred. If multiple records match a source, the record with the highest weight wins. Set `weight: 0` to disable a record without deleting it.

## GTM Monitors

The playbook supports these GTM monitor types, selected by `type`:

| Type | Module |
|---|---|
| `bigip` | `bigip_gtm_monitor_bigip` |
| `external` | `bigip_gtm_monitor_external` |
| `firepass` | `bigip_gtm_monitor_firepass` |
| `http` | `bigip_gtm_monitor_http` |
| `https` | `bigip_gtm_monitor_https` |
| `tcp` | `bigip_gtm_monitor_tcp` |
| `tcp_half_open` | `bigip_gtm_monitor_tcp_half_open` |

```yaml
gtm_monitors:
  - name: "platform_https"
    type: "https"
    parent: "/Common/https"
    send: "GET /health HTTP/1.1\r\nHost: platform.example.com\r\n\r\n"
    receive: "200 OK"
    interval: 10
    timeout: 31
```

## Not Yet Implemented

The following GTM fields are roadmap items:

- advanced persistence options beyond basic type
- cname wide IP advanced fields

These will be added as the GTM coverage expands per Phase 6 of the roadmap.
