# Example Models

This repository intentionally shows both concise and verbose authoring models.

## Concise LTM Model

Use the app-local inline model when one file should explain the whole service.

- Example files:
  - `vars/ltm/virtual_servers/rke2-east/platform-cluster.yml`
  - `vars/ltm/virtual_servers/vm-apps/concise-inline-demo.yml`
- Pattern: an LTM virtual server embeds its pool and members directly under `pool`
- Monitor linkage: monitor aliases such as `traefik_https` are expanded from the sibling `settings.yml` in the same directory
- Built-in health check example: `/Common/https` in `vars/ltm/virtual_servers/vm-apps/concise-inline-demo.yml`

## Verbose LTM Model

Use the shared-object model when pools or nodes are reused, owned by another team, or need clearer separation.

- Virtual servers: `vars/ltm/virtual_servers/vm-apps/business-apps.yml`
- First-class pools: `vars/ltm/pools/vm-applications.yml`
- First-class nodes: `vars/ltm/nodes/vm-applications.yml`

Linkage works like this:

- `ltm_virtual_servers[*].pool: "pool_inventory_east_8443"` points at an object in `vars/ltm/pools/vm-applications.yml`
- `ltm_pools[*].members[*].name: "inventory-east-1"` points at a node in `vars/ltm/nodes/vm-applications.yml`
- `ltm_pools[*].monitors: ["standard_https"]` expands through `vars/ltm/pools/settings.yml`

## Concise GTM Model

Use the app-local GTM model when a Wide IP and its pools should be reviewed together.

- Example file: `vars/gtm/wide_ips/global-platform/platform.yml`
- Pattern: `gtm_wide_ips[*].pools[*]` embeds full GTM pool definitions under a Wide IP
- Monitor linkage: aliases such as `platform_https` expand from `vars/gtm/wide_ips/global-platform/settings.yml`

## Verbose GTM Model

Use the shared-object GTM model when the same GTM pools are referenced by standalone Wide IP files or when DNS ownership is separate from application ownership.

- GTM pools: `vars/gtm/pools/vm-applications.yml`
- GTM servers: `vars/gtm/servers/regional-bigips.yml`
- Referencing Wide IPs: `vars/gtm/wide_ips/vm-applications.yml`

Linkage works like this:

- `gtm_wide_ips[*].pools[*].name: "pool_inventory_global"` points at `vars/gtm/pools/vm-applications.yml`
- `gtm_pools[*].members[*].server: "bigip-east"` points at `vars/gtm/servers/regional-bigips.yml`
- `gtm_pools[*].members[*].virtual_server: "vs_inventory_east_443"` points at `vars/ltm/virtual_servers/vm-apps/business-apps.yml`
- when `address` and `port` are omitted, `gtm.yml` resolves them from that repo-known LTM virtual server definition

## Built-In Versus Custom Health Checks

Out-of-the-box BIG-IP monitor references are fully-qualified names such as `/Common/https` or `/Common/bigip`.

Alias-based custom or convenience references work like this:

- `standard_https` in `vars/ltm/pools/settings.yml` expands to `/Common/https`
- `inventory_https` in `vars/gtm/pools/settings.yml` expands to `/Common/mon_gtm_inventory_https`
- `platform_https` in `vars/gtm/wide_ips/global-platform/settings.yml` expands to `/Common/mon_gtm_platform_https`

Use the inline comments in the example var files when you want the shortest path from a reference string to the related object file.
