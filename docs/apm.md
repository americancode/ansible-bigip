# APM Playbook

## Overview

APM (Access Policy Manager) objects are managed under the `security.yml` playbook alongside AFM and WAF. This covers APM ACLs (L4/L7 access control entries), Network Access resources (VPN configuration), and APM policy imports from exported VPE configurations.

## Playbook Structure

```
security.yml                        # Root wrapper entrypoint
playbooks/security/
├── prep.yml                        # Discovery, include_vars, defaults loading, aggregation
└── tasks/
    ├── manage.yml                  # Task ordering + config save
    ├── apply.yml                   # state: present tasks
    └── delete.yml                  # state: absent tasks
```

## Var Tree

```
vars/security/apm/
├── acls/                           # APM ACL objects (L4/L7)
│   ├── settings.yml                # Directory defaults
│   └── vpn-acls.yml                # Example ACLs
├── network_access/                 # Network Access resource objects
│   ├── settings.yml
│   └── remote-access.yml           # Example VPN configurations
├── policies/                       # APM policy import objects
│   ├── settings.yml
│   └── access-policies.yml         # Example policy imports
└── deletions/                      # Explicit deletion trees
    ├── acls/
    ├── network_access/
    └── policies/
```

## Object Types

### APM ACLs

Managed by `bigip_apm_acl`. Fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | ACL name |
| `partition` | string | no | Partition (default: `Common`) |
| `acl_order` | int | no | Order in the policy |
| `type` | string | no | `l4` or `l7` |
| `entries` | list | no | ACL entries (L4 or L7 format) |

#### L4 Entry Fields

| Field | Type | Description |
|---|---|---|
| `action` | string | `allow`, `deny`, or `discard` |
| `dst_addr` | string | Destination address/CIDR |
| `dst_port` | string | Destination port |
| `src_addr` | string | Source address/CIDR |
| `src_port` | string | Source port |
| `src_mask` | string | Source subnet mask |
| `protocol` | string | `tcp`, `udp`, `all`, etc. |

#### L7 Entry Fields

| Field | Type | Description |
|---|---|---|
| `action` | string | `allow`, `deny`, or `reject` |
| `host_name` | string | Hostname to match |
| `paths` | string | Comma-separated URL paths |
| `scheme` | string | `http`, `https`, `any` |
| `path_match` | bool | Enable path matching |
| `path_match_case` | bool | Case-sensitive path matching |
| `log` | string | Logging level (e.g., `packet`) |

### Network Access

Managed by `bigip_apm_network_access`. Fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Network Access resource name |
| `partition` | string | no | Partition (default: `Common`) |
| `ip_version` | string | no | `ipv4` or `ipv6` |
| `split_tunnel` | bool | no | Enable split tunneling |
| `snat_pool` | string | no | SNAT pool for NAT |
| `ipv4_address_space` | list | no | Address space subnets |
| `excluded_ipv4_adresses` | list | no | Excluded subnets |
| `ipv4_lease_pool` | string | no | DHCP lease pool |
| `allow_local_subnet` | bool | no | Allow access to local subnet |
| `allow_local_dns` | bool | no | Allow local DNS resolution |

### Policy Imports

Managed by `bigip_apm_policy_import`. Fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Policy/profile name |
| `partition` | string | no | Partition (default: `Common`) |
| `source` | string | yes | Local path to tar.gz export |
| `type` | string | no | `access_policy` or `access_profile` |
| `force` | bool | no | Override existing policy |
| `reuse_objects` | bool | no | Reuse existing objects on BIG-IP |

## Authoring Patterns

### Defaults

Directory-level `settings.yml` files provide defaults:

```yaml
# vars/security/apm/acls/settings.yml
apm_acl_defaults:
  partition: Common

# vars/security/apm/network_access/settings.yml
apm_network_access_defaults:
  partition: Common

# vars/security/apm/policies/settings.yml
apm_policy_defaults:
  partition: Common
```

### Example ACL

```yaml
# vars/security/apm/acls/vpn-acls.yml
---
# APM ACL examples for L4 and L7 access control in APM policies.
# Supported fields: `name`, `partition`, `acl_order`, `type` (l4 or l7), `entries`, and `state`.
apm_acls:
  - name: vpn-l4-acl
    acl_order: 10
    type: l4
    entries:
      - action: allow
        dst_addr: 10.0.1.0/24
        dst_port: "443"
        protocol: tcp
```

### Example Network Access

```yaml
# vars/security/apm/network_access/remote-access.yml
---
# APM Network Access examples for remote-access VPN configuration.
# Supported fields: `name`, `partition`, `ip_version`, `split_tunnel`, `snat_pool`,
# `ipv4_address_space`, `excluded_ipv4_adresses`, `ipv4_lease_pool`,
# `allow_local_subnet`, `allow_local_dns`, and `state`.
apm_network_access:
  - name: corporate-remote-access
    ip_version: ipv4
    split_tunnel: true
    ipv4_address_space:
      - subnet: 10.10.1.0/24
```

### Example Policy Import

```yaml
# vars/security/apm/policies/access-policies.yml
---
# APM policy import examples.
# The source file path must exist on the Ansible control host.
# Supported fields: `name`, `partition`, `source` (local tar.gz path), `type`,
# `force`, `reuse_objects`, and `state`.
apm_policies:
  - name: remote-access-policy
    source: /opt/apm-policies/remote-access-policy.tar.gz
    type: access_policy
    reuse_objects: true
```

## Dependency Order

**Apply:** APM ACLs → APM Network Access → APM Policy Imports

**Delete:** APM Policy Imports → APM Network Access → APM ACLs (reverse dependency)

The `security.yml` playbook handles this ordering automatically.

## Validation

`tools/validate-vars` validates:
- Required fields (`name` for all types, `source` for policy imports)
- ACL `type` must be `l4` or `l7`
- ACL entries must define `action`
- Network Access `ip_version` must be `ipv4` or `ipv6`
- Network Access address space entries must define `subnet`
- Policy import `type` must be `access_policy` or `access_profile`
- `force` and `reuse_objects` must be booleans
- No duplicate objects within the same partition

## Drift Detection

`tools/drift-check` compares live BIG-IP APM state against declared var trees:
- ACLs via `access/policy/acl` endpoint
- Network Access via `access/profile/network-access` endpoint

## Import

`tools/import-from-bigip` can import live APM objects:

```sh
F5_HOST=bigip.example.com F5_PASSWORD=secret python3 tools/import-from-bigip --out imported/ --types apm_acls apm_network_access
```
