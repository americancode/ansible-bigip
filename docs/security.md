# Security Playbook (AFM + WAF + APM)

## Overview

`security.yml` manages BIG-IP Advanced Firewall Manager (AFM), Web Application Firewall (WAF/ASM), and Access Policy Manager (APM) objects through a declarative, split-var-tree model. AFM coverage includes address lists, port lists, firewall rules, and firewall policies. WAF coverage includes ASM policies and server technologies. APM coverage includes ACLs, auth servers, SSO configs, resources, policy nodes, access profiles, per-session policies, and macros. APM objects remain tmsh-driven and are modeled as first-class YAML objects rather than tarball policy imports. See [docs/waf.md](waf.md) for WAF-specific details and [docs/apm.md](apm.md) for APM-specific details.

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
vars/security/
├── afm/
│   ├── address_lists/                  # AFM address list objects
│   │   ├── settings.yml                # Directory defaults
│   │   └── platform-addresses.yml      # Example address lists
│   ├── port_lists/                     # AFM port list objects
│   │   ├── settings.yml
│   │   └── platform-ports.yml          # Example port lists
│   ├── rules/                          # AFM firewall rule objects
│   │   ├── settings.yml
│   │   └── platform-rules.yml          # Example rules
│   ├── policies/                       # AFM firewall policy objects
│   │   ├── settings.yml
│   │   └── platform-policies.yml       # Example policies
│   └── deletions/                      # Explicit deletion trees
│       ├── address_lists/
│       ├── port_lists/
│       ├── rules/
│       └── policies/
├── waf/
│   ├── policies/                       # WAF/ASM policy objects
│   │   ├── settings.yml
│   │   └── vm-applications.yml         # Example policies
│   ├── server_technologies/            # Server technology objects
│   │   ├── settings.yml
│   │   └── vm-applications.yml         # Example server technologies
│   └── deletions/                      # Explicit deletion trees
│       ├── policies/
│       └── server_technologies/
└── apm/
    ├── acls/                           # APM ACL objects (L4/L7)
    │   ├── settings.yml
    │   └── vpn-acls.yml                # Example ACLs
    ├── auth_servers/                   # Authentication server objects
    ├── sso_configs/                    # SSO method objects
    ├── resources/                      # Network access, webtop, portal, and RDP resources
    ├── policy_nodes/                   # Access-policy VPE nodes
    ├── access_profiles/                # APM profile access objects
    ├── per_session_policies/           # Per-session policy containers
    ├── macros/                         # Reusable policy macro containers
    └── deletions/                      # Explicit deletion trees
        ├── acls/
        ├── auth_servers/
        ├── sso_configs/
        ├── resources/
        ├── policy_nodes/
        ├── access_profiles/
        ├── per_session_policies/
        └── macros/
```

## Object Types

### Address Lists

Managed by `bigip_firewall_address_list`. Fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Address list name |
| `partition` | string | no | Partition (default: `Common`) |
| `description` | string | no | Human-readable description |
| `addresses` | list | no | Individual IPs or CIDR networks |
| `address_ranges` | list | no | IP ranges formatted as `start-end` |
| `address_lists` | list | no | Nested address list references |
| `geo_locations` | list | no | Geolocation entries (`country`, `region`) |
| `fqdns` | list | no | Fully qualified domain names |

### Port Lists

Managed by `bigip_firewall_port_list`. Fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Port list name |
| `partition` | string | no | Partition (default: `Common`) |
| `description` | string | no | Human-readable description |
| `ports` | list | no | Individual port numbers |
| `port_ranges` | list | no | Port ranges formatted as `start-end` |
| `port_lists` | list | no | Nested port list references |

### Firewall Rules

Managed by `bigip_firewall_rule`. Fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Rule name |
| `partition` | string | no | Partition (default: `Common`) |
| `description` | string | no | Human-readable description |
| `action` | string | no | `accept`, `drop`, `reject`, or `continue` |
| `protocol` | string | no | Protocol (e.g., `tcp`, `udp`) |
| `source` | dict | no | Source endpoint definition |
| `destination` | dict | no | Destination endpoint definition |
| `logging` | string/bool | no | Enable logging |
| `irule` | string | no | Associated iRule |

#### Rule Endpoints

Both `source` and `destination` support the same nested structure:

| Field | Type | Description |
|---|---|---|
| `address_lists` | list | References to AFM address lists |
| `port_lists` | list | References to AFM port lists |
| `addresses` | list | Inline IP addresses or CIDRs |

Endpoint references to address lists resolve within the `Common` partition by default. Use fully qualified names (`/Partition/name`) for cross-partition references.

### Firewall Policies

Managed by `bigip_firewall_rule_list`. Fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Policy name |
| `partition` | string | no | Partition (default: `Common`) |
| `description` | string | no | Human-readable description |
| `rules` | list | no | Ordered list of rule names |

Rule references in policies resolve within the same partition by default. Use fully qualified names for cross-partition references.

## Authoring Patterns

### Directory Defaults

Each object tree supports a `settings.yml` with directory-level defaults:

```yaml
# vars/security/afm/address_lists/settings.yml
afm_address_list_defaults:
  partition: Common
```

Object-level values override directory defaults.

### Deletion Trees

Place objects under `vars/security/afm/deletions/<type>/` with `state: absent` to remove them:

```yaml
# vars/security/afm/deletions/address_lists/legacy-addresses.yml
afm_address_lists:
  - name: legacy-blocked
    state: absent
```

## Dependency Order

Objects are applied and deleted in this order:

1. **AFM address lists** (foundation, referenced by rules)
2. **AFM port lists** (foundation, referenced by rules)
3. **AFM firewall rules** (reference address/port lists)
4. **AFM firewall policies** (reference rules)
5. **WAF policies** (standalone policy definitions)
6. **WAF server technologies** (reference policies)
7. **APM ACLs** (standalone access control entries)
8. **APM auth servers and SSO configs** (foundation for access-policy nodes)
9. **APM resources** (network access, webtop, portal access, remote desktop)
10. **APM access-policy nodes** (reference auth/SSO/resource objects)
11. **APM access profiles**
12. **APM per-session policies and macros**

Deletion runs in reverse order to respect dependencies.

## Config Save

The playbook includes a `bigip_config` save step that runs when any AFM, WAF, or APM objects are created or deleted.
