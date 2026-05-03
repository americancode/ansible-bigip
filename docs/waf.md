# WAF/ASM Playbook

## Overview

WAF (Web Application Firewall) objects are managed under the `security.yml` playbook alongside AFM. This covers ASM/WAF policies and server technologies. WAF policies are attached to LTM virtual servers via the `websecurity` profile in LTM var files.

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
vars/security/waf/
├── policies/                       # WAF/ASM policy objects
│   ├── settings.yml                # Directory defaults
│   └── vm-applications.yml         # Example policies
├── server_technologies/            # Server technology objects
│   ├── settings.yml
│   └── vm-applications.yml         # Example server technologies
└── deletions/                      # Explicit deletion trees
    ├── policies/
    └── server_technologies/
```

## Object Types

### WAF Policies

Managed by `bigip_asm_policy_manage`. Fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Policy name |
| `template` | string | no | Built-in template (e.g., `Comprehensive`, `Rapid Deployment`) |
| `active` | bool | no | Whether policy is active |
| `apply` | bool | no | Apply pending policy changes (TMOS v14+) |

Supported built-in templates: `Comprehensive`, `Fundamental`, `Vulnerability Assessment Baseline`, `Rapid Deployment`, `OWA Exchange 2007 (https)`, `OWA Exchange 2007 (http)`, `SharePoint 2007 (https)`, `SharePoint 2007 (http)`, `Drupal`, `Joomla`, `Wordpress`.

### Server Technologies

Managed by `bigip_asm_policy_server_technology`. Fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Server technology name |
| `policy_name` | string | yes | Parent WAF policy name |

Current limitation:

- the current runtime tasks do not consume a partition field for WAF policies or server technologies
- treat WAF policy names and `policy_name` references as `Common`-scoped unless the runtime is expanded later

## Authoring Patterns

### Defaults

Directory-level `settings.yml` files provide defaults:

```yaml
# vars/security/waf/server_technologies/settings.yml
waf_server_technology_defaults:
  state: present
```

### Example Policy

```yaml
# vars/security/waf/policies/vm-applications.yml
---
# WAF policy examples for web application protection.
# Policies are referenced by server technologies in `vars/security/waf/server_technologies/vm-applications.yml`.
# Supported fields: `name`, `partition`, `template`, `active`, and `apply`.
waf_policies:
  - name: vm-applications-policy
    template: Rapid Deployment
    active: true
    apply: true
```

### Example Server Technologies

```yaml
# vars/security/waf/server_technologies/vm-applications.yml
---
# Server technology examples for WAF policy tuning.
# References parent policy `vm-applications-policy` defined in `vars/security/waf/policies/vm-applications.yml`.
# Supported fields: `name`, `policy_name`.
waf_server_technologies:
  - name: Microsoft IIS
    policy_name: vm-applications-policy
  - name: PHP
    policy_name: vm-applications-policy
```

### Deletions

```yaml
# vars/security/waf/deletions/server_technologies/vm-applications.yml
waf_server_technologies:
  - name: Microsoft IIS
    policy_name: vm-applications-policy
```

```yaml
# vars/security/waf/deletions/policies/vm-applications.yml
waf_policies:
  - name: vm-applications-policy
```

## Dependency Order

**Apply:** WAF policies first, then server technologies (server technologies reference policies).

**Delete:** Server technologies first, then WAF policies (reverse dependency).

The `security.yml` playbook handles this ordering automatically:
1. Apply: AFM objects → WAF policies → WAF server technologies
2. Delete: WAF server technologies → WAF policies → AFM objects

## Cross-Domain References

WAF policies are attached to LTM virtual servers via the `websecurity` profile in LTM var files:

```yaml
# vars/ltm/virtual_servers/vm-applications.yml
ltm_virtual_servers:
  - name: vm-applications-vs
    destination: 10.0.1.100
    destination_port: 443
    pool: vm-applications-pool
    profiles:
      - /Common/websecurity  # Attaches WAF policy
```

## Validation

`tools/validate-vars.py` validates:
- Required fields (`name` for policies, `name` + `policy_name` for server technologies)
- Template names against supported built-in templates
- `active` and `apply` fields must be booleans
- Server technology `policy_name` references an active WAF policy
- No duplicate policies or server technologies within the same policy

## Drift Detection

`tools/drift-check.py` compares:
- WAF policies against live ASM policies using the `asm/policies` endpoint
- WAF server technologies by traversing each policy's `serverTechnologyReference` subcollection and flattening it into the repo's `policy_name` + `name` model

Current limitation:
- helper-tool coverage for WAF server technologies is identity-focused; deeper field-level comparison is not needed yet because the repo model only declares `policy_name` and technology `name`

## Import

`tools/import-from-bigip.py` can import live ASM policies into `vars/security/waf/policies/` using the `waf_policies` type:

```sh
F5_HOST=bigip.example.com F5_PASSWORD=secret python3 tools/import-from-bigip.py --out imported/ --types waf_policies
```

`tools/import-from-bigip.py` can also import WAF server technologies by traversing each policy's server-technology subcollection and generating files under `vars/security/waf/server_technologies/`:

```sh
F5_HOST=bigip.example.com F5_PASSWORD=secret python3 tools/import-from-bigip.py --out imported/ --types waf_policies waf_server_technologies
```
