# TLS Playbook

## Overview

`playbooks/tls.yml` manages BIG-IP TLS-related canonical objects:

- private keys
- certificates
- CA bundles
- client SSL profiles
- server SSL profiles

This playbook owns object identity, references, and profile wiring. Secret-handling guidance for payload content lives separately in [tls-secrets.md](tls-secrets.md).

## Playbook Structure

```text
playbooks/tls.yml
playbooks/tls/
├── prep.yml
├── prep/load-vars.yml
├── prep/build-runtime.yml
└── tasks/
    ├── manage.yml
    ├── audit.yml
    ├── delete.yml
    └── apply.yml
```

`prep.yml` loads the TLS trees, applies `settings.yml` inheritance, classifies present/delete operations, and publishes the runtime collections used by audit and execution.

## Var Tree

```text
vars/tls/
├── keys/
├── certificates/
├── ca_bundles/
├── client_ssl_profiles/
├── server_ssl_profiles/
└── deletions/
    ├── keys/
    ├── certificates/
    ├── ca_bundles/
    ├── client_ssl_profiles/
    └── server_ssl_profiles/
```

## Canonical Object Types

| Type | Location | Purpose |
|---|---|---|
| `tls_keys` | `vars/tls/keys/` | private key objects |
| `tls_certificates` | `vars/tls/certificates/` | certificate objects |
| `tls_ca_bundles` | `vars/tls/ca_bundles/` | trusted CA bundle objects |
| `tls_client_ssl_profiles` | `vars/tls/client_ssl_profiles/` | client-side TLS termination profiles |
| `tls_server_ssl_profiles` | `vars/tls/server_ssl_profiles/` | server-side TLS re-encryption profiles |

## Cross-File Linkages

- client SSL profiles reference key, certificate, and CA bundle objects by name
- server SSL profiles reference CA bundle and related trust material by name
- LTM virtual servers can attach TLS profiles by using the canonical profile names in their `profiles` lists

Keep TLS identity objects stable so profile references and review history remain clear even when certificate material rotates.

## Authoring Patterns

- keep key, certificate, and CA bundle metadata in the normal var trees
- use inline `!vault` for secret `content` values where required
- keep profile objects separate from the raw key/certificate objects they reference

See [tls-secrets.md](tls-secrets.md) for the secret-handling policy.

## Dependency Order

Apply order:

1. keys
2. certificates
3. CA bundles
4. client SSL profiles
5. server SSL profiles

Delete order is the reverse.

## Validation

`tools/validate-vars.py` validates:

- schema and required fields
- object identity and duplicate names
- profile references to key, certificate, and CA bundle objects
- vaulted YAML payload compatibility

## Drift And Import

TLS canonical object families are covered by `tools/drift-check.py` and `tools/import-from-bigip.py`.

Current helper-tool boundary:

- helper-tool coverage is generally `runtime+validation+helper-tools`
- CA bundles and SSL profile families are currently described at `basic field drift` fidelity
- key import does not export private key content; imported keys are metadata-only and must be re-encrypted before use

See [drift-import.md](drift-import.md) and [tls-secrets.md](tls-secrets.md) for the exact boundaries.

## Supplemental Docs

- [tls-secrets.md](tls-secrets.md)
- [validation.md](validation.md)
