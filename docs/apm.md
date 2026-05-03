# APM Playbook

## Overview

APM (Access Policy Manager) objects are managed under the `security.yml` playbook. All APM object types use a unified, type-driven model with declarative YAML var files.

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
│   ├── settings.yml
│   └── vpn-acls.yml
├── auth_servers/                   # Authentication servers (all types)
│   ├── settings.yml
│   └── all-servers.yml             # AD, LDAP, RADIUS, TACACS, RSA, cert, SAML, OAuth
├── sso_configs/                    # SSO configurations (all types)
│   ├── settings.yml
│   └── all-sso.yml                 # Kerberos, Form, HTTP Basic, NTLM, SAML, OAuth, Citrix
├── resources/                      # APM resources (network access, webtop, etc.)
│   ├── settings.yml
│   └── vpn-resources.yml
├── policy_nodes/                   # VPE flow nodes within access policies
│   ├── settings.yml
│   └── ldap-kerberos-flow.yml
├── access_profiles/                # Access profile definitions
│   ├── settings.yml
│   └── corp-profiles.yml
├── per_session_policies/           # Per-session policy definitions
│   ├── settings.yml
│   └── session-policies.yml
├── macros/                         # Reusable VPE macro definitions
│   ├── settings.yml
│   └── common-macros.yml
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

### APM ACLs

Managed via `bigip_apm_acl`. See cross-references in policy docs.

### Auth Servers

Type-driven auth server definitions. The `type` field determines required fields. See `docs/authentication.md` for full type reference.

| Type | Description |
|---|---|
| `active_directory` | AD domain authentication |
| `ldap` | Generic LDAP directory authentication |
| `radius` | RADIUS authentication |
| `tacacs` | TACACS+ authentication |
| `rsa_securid` | RSA SecurID token authentication |
| `cert` | Client certificate authentication |
| `localdb` | BIG-IP local user database |
| `saml` | SAML IdP authentication |
| `oauth` | OAuth/OIDC authentication |

### SSO Configurations

Type-driven SSO method definitions. The `type` field determines required fields. See `docs/authentication.md` for full type reference.

| Type | Description |
|---|---|
| `kerberos` | Kerberos/KCD SSO |
| `form_based` | Form-based SSO |
| `http_basic` | HTTP Basic Auth SSO |
| `ntlm` | NTLM SSO |
| `saml` | SAML SP SSO |
| `oauth` | OAuth client SSO |
| `citrix` | Citrix StoreFront SSO |
| `domain_join` | Domain-joined backend SSO |

### APM Resources

Resource objects assigned within access policies.

| Type | Description |
|---|---|
| `network_access` | VPN network access configuration |
| `webtop` | Webtop resource (full or links) |
| `remote_desktop` | RDP resource |
| `portal_access` | Portal access resource |

### Policy Nodes

Nodes define the VPE flow within an access policy. Each node has a `type` and optional `properties`.

Common types: `logon_page`, `ad_auth`, `ldap_auth`, `kerberos_auth`, `kcd_sso`, `branch`, `allow`, `deny`, `fallback`, `macro`, `variable_assign`.

### Access Profiles

Access profiles bind the declarative APM building blocks together. They reference an access policy, an optional per-session policy, and an optional SSO object, then set the primary session controls used at runtime.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Profile name |
| `partition` | string | no | Partition (default: Common) |
| `description` | string | no | Human-readable description |
| `default_access_policy` | string | no | Parent access policy name referenced from `vars/security/apm/policy_nodes/` |
| `default_per_session_policy` | string | no | Parent per-session policy name referenced from `vars/security/apm/per_session_policies/` |
| `sso_configuration` | string | no | SSO object name or fully qualified path referenced from `vars/security/apm/sso_configs/` |
| `domain` | string | no | Cookie or domain scope used by the access profile |
| `agent_cap` | bool | no | Enable or disable agent cap support |
| `session_timeout` | integer | no | Maximum session lifetime in seconds |
| `idle_timeout` | integer | no | Inactivity timeout in seconds |
| `max_sessions` | integer | no | Maximum concurrent sessions |
| `cookie_fallback` | bool | no | Allow fallback cookie behavior |

### Per-Session Policies

Per-session policies define session-level authentication and authorization logic with node-based flows.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Policy name |
| `partition` | string | no | Partition (default: Common) |
| `description` | string | no | Human-readable description |
| `nodes` | list | no | Ordered list of policy nodes |

Each node in `nodes` has:
- `ordinal` (integer): Execution order
- `name` (string): Node identifier
- `type` (string): Node type (logon_page, ad_auth, variable_assign, ending, etc.)
- `config` (dict): Node-specific configuration

### Macros

Reusable VPE flow building blocks that can be embedded in access policies or per-session policies.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Macro name |
| `partition` | string | no | Partition (default: Common) |
| `description` | string | no | Human-readable description |
| `nodes` | list | no | Ordered list of policy nodes |

Each node in `nodes` has the same structure as per-session policy nodes.

## Cross-File Linkages

- Auth servers (``vars/security/apm/auth_servers/``) are referenced by policy nodes via `ad_server` or `ldap_server` properties, and by per-session policy nodes.
- SSO configs (``vars/security/apm/sso_configs/``) are referenced by policy nodes via `kerberos_sso_object` or similar properties.
- Resources (``vars/security/apm/resources/``) are assigned within policy nodes or referenced by webtop items.
- ACLs (``vars/security/apm/acls/``) enforce L4/L7 access control in APM profiles.
- Macros (``vars/security/apm/macros/``) are referenced by access policies and per-session policies via `macro` node types.
- Access profiles (``vars/security/apm/access_profiles/``) reference VPE policies whose nodes are defined in `vars/security/apm/policy_nodes/`.

## Authoring Patterns

### Defaults

Directory-level `settings.yml` files provide defaults:

```yaml
# vars/security/apm/auth_servers/settings.yml
apm_auth_server_defaults:
  partition: Common
  encryption: ssl

# vars/security/apm/sso_configs/settings.yml
apm_sso_config_defaults:
  partition: Common

# vars/security/apm/resources/settings.yml
apm_resource_defaults:
  partition: Common
```

### Example Auth Server (AD)

```yaml
---
# Auth server examples for all supported auth types.
# Auth servers are referenced by policy nodes in `vars/security/apm/policy_nodes/`.
# Supported types: active_directory, ldap, radius, tacacs, rsa_securid, cert, localdb, saml, oauth.
# See docs/authentication.md for type-specific fields.
apm_auth_servers:
  - name: corp-ad
    type: active_directory
    domain: corp.example.com
    servers:
      - 10.0.1.10
      - 10.0.1.11
    bind_dn: svc-bigip@corp.example.com
    bind_pw: "{{ vault_ad_bind_password }}"
    base_dn: DC=corp,DC=example,DC=com
```

### Example SSO Config (Kerberos)

```yaml
---
# SSO config examples for all supported SSO methods.
# SSO configs are referenced by policy nodes in `vars/security/apm/policy_nodes/`.
# Supported types: kerberos, form_based, http_basic, ntlm, saml, oauth, citrix, domain_join.
# See docs/authentication.md for type-specific fields.
apm_sso_configs:
  - name: kcd-backend-app
    type: kerberos
    method: kcd
    keytab: /config/filestore/files_d/Common_d/keytab_d/bigip.keytab
    spn: HTTP/app-backend.corp.example.com@CORP.EXAMPLE.COM
    kdc: 10.0.1.10
    realm: CORP.EXAMPLE.COM
```

### Example Policy Node

```yaml
---
apm_policy_nodes:
  - name: lp-start
    policy: ldap-kerberos-sso
    type: logon_page
    properties:
      username_prompt: "Username"
      password_prompt: "Password"

  - name: ad-auth
    policy: ldap-kerberos-sso
    type: ad_auth
    properties:
      ad_server: corp-ad

  - name: kcd-sso
    policy: ldap-kerberos-sso
    type: kcd_sso
    properties:
      kerberos_sso_object: kcd-backend-app

  - name: allow-access
    policy: ldap-kerberos-sso
    type: allow
```

### Example Access Profile

```yaml
---
apm_access_profiles:
  - name: corp-sso-profile
    description: Corporate SSO access profile with Kerberos
    default_access_policy: ldap-kerberos-sso
    default_per_session_policy: advanced-session-policy
    sso_configuration: /Common/kcd-backend-app
    domain: corp.example.com
    agent_cap: true
    session_timeout: 28800
    idle_timeout: 1800
    max_sessions: 500
    cookie_fallback: true
```

### Example Per-Session Policy

```yaml
---
apm_per_session_policies:
  - name: advanced-session-policy
    description: Per-session policy with conditional branching
    nodes:
      - ordinal: 1
        name: start
        type: logon_page
        config:
          logon_page: /common/custom_logon.php
          auth_server: corp-ad-server
          next_node: check_group
      - ordinal: 2
        name: check_group
        type: variable_assign
        config:
          assignments:
            - variable: session.custom.group
              value: expr{[mcget {session.ad.last.attr.memberOf}]}
          next_node: end
      - ordinal: 3
        name: end
        type: ending
        config:
          ending_type: allow
```

### Example Macro

```yaml
---
apm_macros:
  - name: ldap-auth-macro
    description: Reusable LDAP authentication macro
    nodes:
      - ordinal: 1
        name: ldap_logon
        type: logon_page
        config:
          logon_page: /common/custom_logon.php
          next_node: ldap_auth
      - ordinal: 2
        name: ldap_auth
        type: ad_auth
        config:
          ad_server: corp-ldap-server
          fallback: true
          next_node: ldap_result
      - ordinal: 3
        name: ldap_result
        type: empty
        config:
          branches:
            - name: Success
              next_node: end_allow
            - name: Failure
              next_node: end_deny
      - ordinal: 4
        name: end_allow
        type: ending
        config:
          ending_type: allow
      - ordinal: 5
        name: end_deny
        type: ending
        config:
          ending_type: deny
```

## Dependency Order

**Apply:** Auth Servers → SSO Configs → Resources → Macros → Per-Session Policies → Policy Nodes → Access Profiles → ACLs

**Delete:** ACLs → Access Profiles → Policy Nodes → Per-Session Policies → Macros → Resources → SSO Configs → Auth Servers (reverse dependency)

The `security.yml` playbook handles this ordering automatically.

## Validation

`tools/validate-vars.py` validates:
- Auth servers: required fields by type, supported types, server list validation, encryption validation
- SSO configs: required fields by type, supported types
- Resources: type-specific field validation (address_spaces for network_access, items for webtops)
- Policy nodes: cross-reference validation against declared auth servers and SSO configs
- ACLs: type validation, entry structure validation
- Access profiles: duplicate detection, field typing, and references to declared per-session policies and repo-managed access-policy/SSO objects where applicable
- Per-session policies: node structure validation (name, type required)
- Macros: node structure validation (name, type required)
- No duplicate objects within the same partition

## Drift Detection

`tools/drift-check.py` compares live BIG-IP APM state against declared var trees:
- ACLs via `access/policy/acl` endpoint
- Auth servers via `auth/remote-server` endpoint
- SSO configs via `apm/sso` endpoint
- Resources via `apm/resource` endpoint
- Access profiles via `access/profile` endpoint
- Per-session policies via `access/per-session-policy` endpoint
- Macros via `access/macro` endpoint
- Policy nodes by traversing `apm/policy/access-policy` objects and flattening their `items` arrays into the repo's `policy` + `name` model

Current limitation:
- helper-tool coverage for APM policy nodes currently focuses on existence plus basic `type` drift
- nested `properties` are still runtime-managed and not yet compared or reconstructed exhaustively

## Import

`tools/import-from-bigip.py` can import live APM objects:

```sh
F5_HOST=bigip.example.com F5_PASSWORD=secret python3 tools/import-from-bigip.py --out imported/ --types apm_acls apm_auth_servers apm_sso_configs apm_resources apm_access_profiles apm_per_session_policies apm_macros apm_policy_nodes
```

Current limitation:
- imported APM policy nodes currently include `name`, `policy`, optional `partition`, and basic `type`
- nested `properties` are not reconstructed yet, so imported node files should be treated as a starting point for review, not as a full-fidelity round-trip export

## Related Docs

- `docs/authentication.md` — Comprehensive reference for all auth server types and SSO configs
