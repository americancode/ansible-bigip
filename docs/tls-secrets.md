# TLS Secret Handling

This repository uses Ansible Vault as the default secret-handling approach for TLS material.

## Policy

- Keep TLS object metadata in the normal `vars/tls/*` files.
- Encrypt private key `content` values with inline `!vault`.
- Certificates and CA bundles may stay in plaintext when policy allows, or may also use inline `!vault`.
- Do not move secret material into ad hoc external files that bypass review of object identity and references.

## Recommended Layout

- `vars/tls/keys/*.yml`: key objects with encrypted `content`
- `vars/tls/certificates/*.yml`: certificate objects, encrypted when required
- `vars/tls/ca_bundles/*.yml`: CA bundle objects, encrypted when required
- `vars/tls/*_profiles/*.yml`: profile definitions and references in normal YAML

## Example

```yaml
tls_keys:
  - name: wildcard_platform_example_com
    true_names: true
    content: !vault |
      $ANSIBLE_VAULT;1.1;AES256
      3265666237643835663865313966373462643733633536373539633832313039
      3264653136616335663739643462336636626663333635640a3031653936616436
```

## Validation Behavior

- `tools/validate-vars.py` accepts inline Ansible YAML tags such as `!vault`.
- `make validate` continues to work with vaulted TLS payloads in place.
- Reference validation still operates on object names and profile wiring even when payload content is encrypted.

## Authoring Guidance

- Encrypt only the `content` field unless policy requires broader encryption.
- Keep names and references stable so reviews can still reason about certificate/profile relationships.
- Prefer one object per certificate or key file to keep ownership and rotation history clear.
