# APM Authentication Configuration

## Overview

BIG-IP APM supports multiple authentication server types and SSO methods. All auth objects are managed declaratively under `vars/security/apm/auth_servers/` and `vars/security/apm/sso_configs/` with a unified `type` field to select the method.

## Architecture

```
Client → BIG-IP APM → Auth Server → Session Variables → Policy Nodes → SSO Config → Backend App
```

## Auth Server Types

All auth servers are declared under `vars/security/apm/auth_servers/` with a `type` field:

| Type | TMSH Command | Description |
|---|---|---|
| `active_directory` | `auth remote-server` (service active-directory) | AD domain authentication |
| `ldap` | `auth remote-server` (service ldap) | Generic LDAP directory authentication |
| `radius` | `auth radius-server` | RADIUS authentication |
| `tacacs` | `auth tacacs-server` | TACACS+ authentication |
| `rsa_securid` | `auth rsa-auth-server` | RSA SecurID token authentication |
| `cert` | `apm resource certificate-auth` | Client certificate authentication |
| `localdb` | `apm sso localdb` | BIG-IP local user database |
| `saml` | `apm sso saml` | SAML IdP authentication |
| `oauth` | `apm sso oauth` | OAuth/OIDC authentication |
| `msntlm` | `apm resource msntlm` | MS NTLM backend auth |

## SSO Config Types

All SSO configurations are declared under `vars/security/apm/sso_configs/` with a `type` field:

| Type | TMSH Command | Description |
|---|---|---|
| `kerberos` | `apm sso kerberos` | Kerberos/KCD SSO |
| `form_based` | `apm sso form-based` | Form-based SSO to backend apps |
| `http_basic` | `apm sso http-basic` | HTTP Basic Auth SSO |
| `ntlm` | `apm sso ntlm` | NTLM SSO |
| `saml` | `apm sso saml` | SAML SP SSO |
| `oauth` | `apm sso oauth` | OAuth client SSO |
| `citrix` | `apm sso citrix` | Citrix StoreFront SSO |
| `domain_join` | `apm sso domain-join` | Domain-joined backend SSO |

## Active Directory Auth Server

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Auth server name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `active_directory` |
| `domain` | string | yes | AD domain name |
| `servers` | list | yes | Domain controller IPs/hostnames |
| `port` | int | no | LDAP port (default: 389) |
| `bind_dn` | string | yes | Service account DN (e.g., `svc-bigip@corp.example.com`) |
| `bind_pw` | string | yes | Service account password |
| `base_dn` | string | yes | Search base DN |
| `encryption` | string | no | `none`, `ssl`, or `starttls` |

### Example

```yaml
---
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
    encryption: ssl
```

## LDAP Auth Server

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Auth server name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `ldap` |
| `servers` | list | yes | LDAP server IPs/hostnames |
| `port` | int | no | LDAP port (default: 389, 636 for SSL) |
| `bind_dn` | string | yes | Bind DN |
| `bind_pw` | string | yes | Bind password |
| `base_dn` | string | yes | Search base DN |
| `encryption` | string | no | `none`, `ssl`, or `starttls` |
| `user_template` | string | no | User DN template (e.g., `uid=%{session.logon.last.username},ou=users,...`) |

### Example

```yaml
---
apm_auth_servers:
  - name: ldap-partners
    type: ldap
    servers:
      - 10.0.2.50
    port: 636
    bind_dn: cn=readonly,dc=partners,dc=com
    bind_pw: "{{ vault_ldap_bind_password }}"
    base_dn: OU=Users,DC=partners,dc=com
    encryption: ssl
    user_template: "uid=%{session.logon.last.username},ou=users,dc=partners,dc=com"
```

## RADIUS Auth Server

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Auth server name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `radius` |
| `servers` | list | yes | RADIUS server IPs/hostnames |
| `port` | int | no | RADIUS port (default: 1812) |
| `secret` | string | yes | RADIUS shared secret |
| `protocol` | string | no | `pap`, `chap`, or `mschapv2` |
| `message_authenticator` | bool | no | Enable message authenticator |

### Example

```yaml
---
apm_auth_servers:
  - name: radius-main
    type: radius
    servers:
      - 10.0.3.10
      - 10.0.3.11
    port: 1812
    secret: "{{ vault_radius_secret }}"
    protocol: mschapv2
    message_authenticator: true
```

## TACACS+ Auth Server

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Auth server name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `tacacs` |
| `servers` | list | yes | TACACS+ server IPs/hostnames |
| `port` | int | no | TACACS+ port (default: 49) |
| `secret` | string | yes | TACACS+ shared secret |
| `service` | string | no | Service type (`ppp`, `arap`, `tty`, etc.) |

### Example

```yaml
---
apm_auth_servers:
  - name: tacacs-ops
    type: tacacs
    servers:
      - 10.0.4.10
    port: 49
    secret: "{{ vault_tacacs_secret }}"
    service: tty
```

## RSA SecurID Auth Server

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Auth server name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `rsa_securid` |
| `servers` | list | yes | RSA Authentication Manager IPs |
| `config_file` | string | yes | Path to sdconf.rec on BIG-IP |

### Example

```yaml
---
apm_auth_servers:
  - name: rsa-auth
    type: rsa_securid
    servers:
      - 10.0.5.10
    config_file: /config/auth/rsa/sdconf.rec
```

## Local Database Auth

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Auth server name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `localdb` |
| `user_source` | string | yes | Local user database path/name |
| `password_encoding` | string | no | Encoding method (`crypt`, `md5`, `sha1`, `ssha1`, `ssha512`) |

### Example

```yaml
---
apm_auth_servers:
  - name: local-auth
    type: localdb
    user_source: /Common/local-users
    password_encoding: ssha512
```

## Certificate Auth

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Auth server name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `cert` |
| `ca_bundle` | string | yes | CA bundle for client cert validation |
| `crl_file` | string | no | CRL file path |
| `ocsp_responder` | string | no | OCSP responder URL |
| `cert_field` | string | no | Field to extract as username (`subject`, `subject-email`, `subject-cn`, etc.) |

### Example

```yaml
---
apm_auth_servers:
  - name: cert-auth
    type: cert
    ca_bundle: /Common/corp-ca-bundle
    cert_field: subject-cn
    ocsp_responder: http://ocsp.corp.example.com
```

## SAML Auth Server

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Auth server name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `saml` |
| `idp_metadata_url` | string | yes | IdP metadata URL |
| `idp_entity_id` | string | no | IdP entity ID |
| `sp_entity_id` | string | yes | SP entity ID |
| `acs_url` | string | yes | Assertion Consumer Service URL |
| `slo_url` | string | no | Single Logout URL |
| `nameid_format` | string | no | NameID format |
| `sign_authn_request` | bool | no | Sign authentication requests |
| `encrypt_assertion` | bool | no | Encrypt SAML assertions |
| `signing_cert` | string | no | Signing certificate |
| `signing_key` | string | no | Signing private key |

### Example

```yaml
---
apm_auth_servers:
  - name: saml-okta
    type: saml
    idp_metadata_url: "https://corp.okta.com/app/bigip/sso/saml/metadata"
    sp_entity_id: "https://bigip.corp.example.com/saml/sp"
    acs_url: "/my.policy"
    sign_authn_request: true
    encrypt_assertion: true
    signing_cert: /Common/bigip-saml-cert
    signing_key: /Common/bigip-saml-key
```

## OAuth/OIDC Auth Server

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Auth server name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `oauth` |
| `provider_url` | string | yes | OAuth/OIDC provider URL |
| `client_id` | string | yes | OAuth client ID |
| `client_secret` | string | yes | OAuth client secret |
| `authorization_endpoint` | string | no | Authorization endpoint URL |
| `token_endpoint` | string | no | Token endpoint URL |
| `userinfo_endpoint` | string | no | Userinfo endpoint URL |
| `scopes` | list | yes | OAuth scopes |
| `response_type` | string | no | `code`, `id_token`, `token` |
| `use_pkce` | bool | no | Enable PKCE for public clients |

### Example

```yaml
---
apm_auth_servers:
  - name: oidc-azure
    type: oauth
    provider_url: "https://login.microsoftonline.com/tenant-id/v2.0"
    client_id: "{{ vault_azure_client_id }}"
    client_secret: "{{ vault_azure_client_secret }}"
    scopes:
      - openid
      - profile
      - email
    response_type: code
    use_pkce: true
```

## SSO Configurations

### Kerberos SSO

#### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | SSO config name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `kerberos` |
| `method` | string | yes | `kcd` or `negotiate` |
| `keytab` | string | yes | Keytab file path on BIG-IP |
| `spn` | string | yes | Service Principal Name |
| `kdc` | string | no | KDC server IP/hostname |
| `realm` | string | no | Kerberos realm |
| `upn_domain` | string | no | UPN domain override |

#### Example

```yaml
---
apm_sso_configs:
  - name: kcd-backend-app
    type: kerberos
    method: kcd
    keytab: /config/filestore/files_d/Common_d/keytab_d/bigip.keytab
    spn: HTTP/app-backend.corp.example.com@CORP.EXAMPLE.COM
    kdc: 10.0.1.10
    realm: CORP.EXAMPLE.COM
```

### Form-Based SSO

#### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | SSO config name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `form_based` |
| `form_action_url` | string | yes | Backend form action URL |
| `username_field` | string | yes | Backend HTML form username field name |
| `password_field` | string | yes | Backend HTML form password field name |
| `submit_button` | string | no | Submit button selector |
| `extra_fields` | dict | no | Extra form fields to submit |
| `login_success_regex` | string | no | Regex to detect successful login |
| `login_failure_regex` | string | no | Regex to detect failed login |

#### Example

```yaml
---
apm_sso_configs:
  - name: form-backend-login
    type: form_based
    form_action_url: "https://app-backend/login"
    username_field: "j_username"
    password_field: "j_password"
    submit_button: "submit"
    login_success_regex: "Welcome"
    login_failure_regex: "Invalid credentials"
```

### HTTP Basic SSO

#### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | SSO config name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `http_basic` |
| `domain` | string | no | Domain for NTLM fallback |
| `use_session_creds` | bool | no | Use session credentials |

#### Example

```yaml
---
apm_sso_configs:
  - name: http-basic-backend
    type: http_basic
    use_session_creds: true
```

### NTLM SSO

#### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | SSO config name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `ntlm` |
| `server` | string | yes | AD server for NTLM auth |
| `domain` | string | yes | AD domain |
| `use_machine_account` | bool | no | Use BIG-IP machine account |

#### Example

```yaml
---
apm_sso_configs:
  - name: ntlm-backend
    type: ntlm
    server: 10.0.1.10
    domain: corp.example.com
    use_machine_account: true
```

### SAML SSO (SP-initiated)

#### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | SSO config name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `saml` |
| `idp_metadata_url` | string | yes | IdP metadata URL |
| `sp_entity_id` | string | yes | SP entity ID |
| `assertion_consumer_url` | string | yes | ACS URL |
| `nameid_format` | string | no | NameID format |
| `sign_assertion` | bool | no | Sign SAML assertion |
| `encrypt_assertion` | bool | no | Encrypt assertion |
| `signing_cert` | string | no | Signing cert |
| `signing_key` | string | no | Signing key |

#### Example

```yaml
---
apm_sso_configs:
  - name: saml-sso-salesforce
    type: saml
    idp_metadata_url: "https://login.salesforce.com/.well-known/samlidp"
    sp_entity_id: "https://bigip.corp.example.com/saml/sp"
    assertion_consumer_url: "https://login.salesforce.com/?saml=1"
    sign_assertion: true
    encrypt_assertion: true
```

### OAuth SSO

#### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | SSO config name |
| `partition` | string | no | Partition (default: `Common`) |
| `type` | string | yes | `oauth` |
| `provider_url` | string | yes | OAuth provider URL |
| `client_id` | string | yes | Client ID |
| `client_secret` | string | yes | Client secret |
| `scopes` | list | yes | OAuth scopes |

#### Example

```yaml
---
apm_sso_configs:
  - name: oauth-backend-api
    type: oauth
    provider_url: "https://auth.corp.example.com"
    client_id: "{{ vault_oauth_client_id }}"
    client_secret: "{{ vault_oauth_client_secret }}"
    scopes:
      - api:read
      - api:write
```

## Cross-File Linkages

- Auth servers are referenced by **policy nodes** in `vars/security/apm/policy_nodes/` (e.g., `ad_server`, `ldap_server` properties).
- SSO configs are referenced by **policy nodes** in `vars/security/apm/policy_nodes/` (e.g., `kerberos_sso_object` property).
- Policy nodes reference both auth servers and SSO configs within a single access policy.

## Session Variables by Auth Type

| Auth Type | Key Session Variables |
|---|---|
| AD | `session.ad.last.attr.*` (memberOf, mail, displayName, etc.) |
| LDAP | `session.ldap.last.attr.*` |
| RADIUS | `session.radius.last.*` |
| Certificate | `session.ssl.cert.*` (subject, issuer, serial, etc.) |
| SAML | `session.saml.last.*` (nameid, attributes, etc.) |
| OAuth/OIDC | `session.oauth.last.*` (id_token, userinfo, etc.) |
| Local DB | `session.localdb.last.*` |

## Dependency Order

**Apply:** Auth Servers → SSO Configs → Resources → Policy Nodes

**Delete:** Policy Nodes → Resources → SSO Configs → Auth Servers (reverse dependency)

## Validation

`tools/validate-vars.py` validates:
- Auth servers: required fields by type, supported types, server lists
- SSO configs: required fields by type, supported types
- Policy nodes: cross-reference validation against declared auth servers and SSO configs
- No duplicate objects within the same partition

## Troubleshooting

### Test LDAP Bind from BIG-IP CLI

```bash
ldapsearch -H ldap://10.0.1.10:389 \
  -D "svc-bigip@corp.example.com" \
  -W \
  -b "DC=corp,DC=example,DC=com" \
  "(sAMAccountName=testuser)"
```

### Test RADIUS Authentication

```bash
radtest username password 10.0.3.10 0 radius-secret
```

### Enable APM Debug Logging

```bash
tmsh modify sys db log.apm.level value debug
tail -f /var/log/apm
```
