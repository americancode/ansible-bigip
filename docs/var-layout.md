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

Nested directories are supported. You can organize trees like:

- `vars/ltm/nodes/postgres/`
- `vars/ltm/nodes/postgres/dc1/`
- `vars/gtm/pools/platform/us-east/`

The loaders discover YAML fragments recursively, and the canonical playbooks now apply hierarchical `settings.yml` inheritance from the subtree root down to the leaf directory that contains the fragment.

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
- `vars/system/login_banners/` for device-scoped GUI login banner compliance text

## Hybrid Authoring

Objects can be embedded directly in parent definitions or promoted to first-class trees. See [hybrid-authoring.md](hybrid-authoring.md) for the current model and [intent-authoring.md](intent-authoring.md) for the planned intent/compiler architecture that will absorb the growing shortcut patterns.

The first dedicated intent tree is now live under `vars/ltm/intents/clusters/` for RKE2 server clusters. Intent directories should be category-first under `vars/<domain>/intents/<category>/...`, and `settings.yml` can exist at the intent root, category level, or leaf service directory. These trees are authoring abstractions only: `prep.yml` compiles them into canonical runtime objects before tasks run.

## Deletions

Objects can be removed via deletion trees. See [deletion-workflows.md](deletion-workflows.md).
