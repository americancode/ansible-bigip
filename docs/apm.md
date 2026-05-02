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
└── deletions/                      # Explicit deletion trees
    ├── acls/
    ├── auth_servers/
    ├── sso_configs/
    ├── resources/
    └── policy_nodes/
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

## Cross-File Linkages

- Auth servers (``vars/security/apm/auth_servers/``) are referenced by policy nodes via `ad_server` or `ldap_server` properties.
- SSO configs (``vars/security/apm/sso_configs/``) are referenced by policy nodes via `kerberos_sso_object` or similar properties.
- Resources (``vars/security/apm/resources/``) are assigned within policy nodes or referenced by webtop items.
- ACLs (``vars/security/apm/acls/``) enforce L4/L7 access control in APM profiles.

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

## Dependency Order

**Apply:** Auth Servers → SSO Configs → Resources → Policy Nodes → ACLs

**Delete:** ACLs → Policy Nodes → Resources → SSO Configs → Auth Servers (reverse dependency)

The `security.yml` playbook handles this ordering automatically.

## Validation

`tools/validate-vars` validates:
- Auth servers: required fields by type, supported types, server list validation, encryption validation
- SSO configs: required fields by type, supported types
- Resources: type-specific field validation (address_spaces for network_access, items for webtops)
- Policy nodes: cross-reference validation against declared auth servers and SSO configs
- ACLs: type validation, entry structure validation
- No duplicate objects within the same partition

## Drift Detection

`tools/drift-check` compares live BIG-IP APM state against declared var trees:
- ACLs via `access/policy/acl` endpoint
- Auth servers via `auth/remote-server` endpoint
- SSO configs via `apm/sso/kerberos` endpoint
- Resources via `apm/resource` endpoint

## Import

`tools/import-from-bigip` can import live APM objects:

```sh
F5_HOST=bigip.example.com F5_PASSWORD=secret python3 tools/import-from-bigip --out imported/ --types apm_acls apm_auth_servers apm_sso_configs apm_resources
```

## Related Docs

- `docs/authentication.md` — Comprehensive reference for all auth server types and SSO configs
