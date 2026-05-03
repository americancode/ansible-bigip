# Variable Layout and Precedence

The repo uses split trees under `vars/` so large estates can be managed by domain.

## Domain Trees

- `vars/network/...`
- `vars/bootstrap/...`
- `vars/system/...`
- `vars/ha/...`
- `vars/ltm/...`
- `vars/gtm/...`
- `vars/tls/...`
- `vars/security/...`
- `vars/common.yml` (shared provider configuration)

## Settings Inheritance

Each subtree can use a sibling `settings.yml` to provide defaults for objects in that directory.

Precedence is:

1. object-level value
2. sibling `settings.yml`
3. playbook fallback

For partitions, the fallback is `Common`.

## Network Tree Examples

The network var tree includes:

- local and floating self IP patterns
- route-domain-scoped routing
- reusable SNAT translations and SNAT pools
- trunk examples using the native `bigip_trunk` module
- NAT examples using a validated `tmsh` command workflow (the installed collection does not provide a first-class NAT module)

## Bootstrap Tree Examples

The bootstrap var tree covers the narrow day-0 layer that exists before normal steady-state management:

- license activation inputs
- first management IP CIDR
- first management default route

After bootstrap, the source of truth moves to `vars/system/...`, `vars/ha/...`, and the other service-domain trees.

## HA Tree Examples

The HA var tree includes:

- device-local HA connectivity settings for config sync, failover transport, and connection mirroring
- shared device trust, device groups, and device group memberships
- HA score groups that reference LTM pools and network trunks
- traffic groups that can use either direct `ha_order` or indirect `ha_group` scoring

## System Tree Examples

The system var tree includes both basic device settings and management-plane administrator login configuration:

- `vars/system/hostname/`, `vars/system/dns/`, `vars/system/ntp/`, `vars/system/provisioning/`, `vars/system/users/`, and `vars/system/config/`
- `vars/system/auth/ldap/` for LDAP or Active Directory admin auth
- `vars/system/auth/tacacs/` for TACACS+ admin auth
- `vars/system/auth/radius_servers/` for reusable RADIUS server objects
- `vars/system/auth/radius/` for the RADIUS auth profile that references those server objects

## Hybrid Authoring

Objects can be embedded directly in parent definitions or promoted to first-class trees. See [hybrid-authoring.md](hybrid-authoring.md) for the full model and examples.

## Deletions

Objects can be removed via deletion trees. See [deletion-workflows.md](deletion-workflows.md).
