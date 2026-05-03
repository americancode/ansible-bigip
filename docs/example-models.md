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
- First-class non-TLS profiles: `vars/ltm/profiles/platform-profiles.yml`

Linkage works like this:

- `ltm_virtual_servers[*].pool: "pool_inventory_east_8443"` points at an object in `vars/ltm/pools/vm-applications.yml`
- `ltm_pools[*].members[*].name: "inventory-east-1"` points at a node in `vars/ltm/nodes/vm-applications.yml`
- `ltm_pools[*].monitors: ["standard_https"]` expands through `vars/ltm/pools/settings.yml`
- `ltm_virtual_servers[*].profiles: ["http_platform_standard"]` points at an object in `vars/ltm/profiles/platform-profiles.yml`
- `ltm_virtual_servers[*].profiles: ["/Common/tcp"]` uses an out-of-the-box BIG-IP profile and does not resolve to a repo file

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

## Network Expansion Examples

The network tree also shows both native-module and validated-command patterns.

- Trunks: `vars/network/trunks/foundation-trunks.yml`
  This uses the native `bigip_trunk` module and is the preferred model for link aggregation.
- NATs: `vars/network/nats/foundation-nats.yml`
  This uses a validated `tmsh` command workflow because the installed collection does not provide a first-class NAT module.
- NAT VLAN references such as `external` point at `vars/network/vlans/foundation-vlans.yml`.

## Bootstrap Model

The bootstrap tree is intentionally narrow and operationally staged.

- License input: `vars/bootstrap/license/foundation-license.yml`
- First management endpoint: `vars/bootstrap/management/foundation-management.yml`

Linkage works like this:

- `bootstrap_licenses[*]` is consumed by `playbooks/bootstrap.yml` before the normal system domain is applied
- `bootstrap_management[*].address` becomes the management endpoint that AWX inventory `f5_host` or CLI inventory entries should target after bootstrap
- after that cutover, hostname/DNS/NTP/provisioning/users move into `vars/system/*` and HA setup moves into `vars/ha/*`

## HA Model

The HA tree mixes device-local and shared-pair authoring on purpose.

- Device-local HA connectivity: `vars/ha/device_connectivity/foundation-connectivity.yml`
- Shared HA groups: `vars/ha/ha_groups/foundation-ha-groups.yml`
- Shared traffic groups: `vars/ha/traffic_groups/foundation-traffic-groups.yml`

Linkage works like this:

- `ha_device_connectivity[*]` configures the BIG-IP currently targeted by `f5_host`; it is not a shared pair object
- `ha_groups[*].pools[*].pool_name: "vm-apps-main"` points at a pool in `vars/ltm/pools/`
- `ha_groups[*].trunks[*].trunk_name: "trunk-uplink-a"` points at a trunk in `vars/network/trunks/`
- `ha_traffic_groups[*].ha_group: "hg_apps_prefer_healthy_pools"` points at `vars/ha/ha_groups/foundation-ha-groups.yml`
- `ha_traffic_groups[*].ha_order` is the direct static preference alternative; do not use both `ha_group` and `ha_order` on the same object

## System Admin Auth Model

The system tree uses a mixed direct-and-referenced model for BIG-IP administrator login methods.

- LDAP / AD auth: `vars/system/auth/ldap/foundation-ldap.yml`
- TACACS+ auth: `vars/system/auth/tacacs/foundation-tacacs.yml`
- RADIUS server objects: `vars/system/auth/radius_servers/foundation-radius-servers.yml`
- RADIUS auth profile: `vars/system/auth/radius/foundation-radius.yml`

Linkage works like this:

- `system_auth_radius[*].servers: ["radius_dc1"]` points at `vars/system/auth/radius_servers/foundation-radius-servers.yml`
- `system_auth_ldap[*].servers` is just the remote LDAP or AD server list; it does not point at another repo-managed BIG-IP object tree
- only one of `system_auth_ldap[*].use_for_auth`, `system_auth_tacacs[*].use_for_auth`, or `system_auth_radius[*].use_for_auth` should be `true` for the current BIG-IP target
- this system-auth layer controls how operators log in to BIG-IP itself; it is separate from APM end-user identity under `vars/security/apm/`

## AFM Security Model

The security playbook uses first-class var trees for address lists, port lists, rules, and policies.

- Address lists: `vars/security/afm/address_lists/platform-addresses.yml`
- Port lists: `vars/security/afm/port_lists/platform-ports.yml`
- Firewall rules: `vars/security/afm/rules/platform-rules.yml`
- Firewall policies: `vars/security/afm/policies/platform-policies.yml`

Linkage works like this:

- `afm_rules[*].source.address_lists: ["trusted-clients"]` points at `vars/security/afm/address_lists/platform-addresses.yml`
- `afm_rules[*].destination.port_lists: ["web-ports"]` points at `vars/security/afm/port_lists/platform-ports.yml`
- `afm_policies[*].rules: ["allow-web-internal"]` points at `vars/security/afm/rules/platform-rules.yml`
- Rules are evaluated top-to-bottom by BIG-IP, so the `deny-all` catch-all must appear last in the policy's `rules` list
