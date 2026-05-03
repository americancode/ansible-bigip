# Validation

Run local validation with:

```sh
make validate
```

This runs:

- `python3 tools/validate-vars.py` — YAML/schema/reference validation and duplicate detection
- `ansible-playbook --syntax-check` — syntax check for all canonical playbooks under `playbooks/`

## What the Validator Checks

- YAML parse for all var files
- Schema validation for object trees (required keys, allowed keys, identity fields)
- Cross-file reference validation (pool monitors, Wide IP to pool references, virtual server to pool references, etc.)
- Duplicate object detection (LTM virtual server names, pool names, GTM Wide IP names, etc.)
- Partition and naming policy checks

## Vault Support

The validator accepts Ansible-specific YAML tags such as inline `!vault`, so encrypted TLS material can stay in the same var trees without breaking offline checks.

See [tls-secrets.md](tls-secrets.md) for the secret-handling convention.

## CI Integration

The GitLab CI pipeline (`.gitlab-ci.yml`) runs the same validation steps. Validation must pass before any playbook execution.
