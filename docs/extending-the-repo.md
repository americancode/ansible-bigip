# Extending the Repository

Use this guide when you need to change the repo model itself, not just author another object in an existing tree.

This guide is for four cases:

- add a new object type to an existing runtime domain
- add a new convenience pattern or intent
- add a new runtime domain
- extend helper-tool coverage for an existing object family

## Decide What You Are Adding

Start with this decision rule:

### Another canonical object family in an existing domain

Use this path when the new thing is just another BIG-IP runtime object family that belongs beside the existing domain objects.

Examples:

- another `ltm` object family
- another `network` object family
- another `security` object family

### A convenience bundle or higher-level authoring model

Use an intent when the new thing is a simpler authoring surface that should compile into canonical objects before runtime apply/delete.

Examples:

- service bundles
- platform templates
- concise app-local declarations that expand into multiple canonical objects

Intent vars belong under:

- `vars/<domain>/intents/<category>/...`
- `vars/<domain>/deletions/intents/<category>/...`

See [intents/how-to-build-intents.md](intents/how-to-build-intents.md).

### A genuinely new runtime domain

Create a new playbook only when the object family is operationally distinct enough to justify its own runtime lifecycle, docs, and execution boundary.

## Mandatory Repo Surfaces

When you add a new object family or domain, the implementation is not complete until the surrounding repo surfaces are either updated or explicitly documented as intentionally unsupported.

### Runtime playbooks

- `playbooks/<domain>.yml`
- `playbooks/<domain>/prep.yml`
- `playbooks/<domain>/tasks/manage.yml`
- `playbooks/<domain>/tasks/apply.yml`
- `playbooks/<domain>/tasks/delete.yml`
- `playbooks/<domain>/tasks/audit.yml`

### Var tree

- `vars/<domain>/<type>/`
- `vars/<domain>/deletions/<type>/`
- example files with comment headers that explain purpose, cross-file linkages, and supported fields

### Validation

- `tools/validate-vars.py`
- split validator modules under `tools/validate_vars/`
- `Makefile` coverage through `make validate`

### Helper tools

- `tools/drift-check.py`
- `tools/import-from-bigip.py`

If drift/import is intentionally incomplete for that object family, record that limitation explicitly in the relevant domain doc and in [ROADMAP.md](../ROADMAP.md) instead of implying full parity.

### Docs

- domain doc in `docs/`
- [playbook-structure.md](playbook-structure.md)
- [var-layout.md](var-layout.md)
- [README.md](../README.md)

## Completion Classes

State the real implementation level in repo terms:

- `runtime-only`
- `runtime+validation`
- `runtime+validation+helper-tools`
- `full parity`

Do not silently imply a stronger class than the repo actually supports.

## Helper-Tool Fidelity Levels

If drift/import exists, describe the actual fidelity:

- `identity-only`
- `basic field drift`
- `model-aware`

Be explicit when helper tooling only covers the core runtime-managed fields.

## New Object Type Checklist

Use this when extending an existing domain:

1. add the var tree and deletion tree
2. load and normalize the tree in `prep.yml`
3. add `state: present` handling in `tasks/apply.yml`
4. add reverse-order `state: absent` handling in `tasks/delete.yml`
5. expose the new runtime collections in `tasks/audit.yml`
6. update config-save conditions in `tasks/manage.yml`
7. extend validation and duplicate/reference checks
8. update drift/import or explicitly document why they remain unsupported
9. update the domain doc, [playbook-structure.md](playbook-structure.md), [var-layout.md](var-layout.md), and [README.md](../README.md)
10. run `make validate`

## New Intent Checklist

Use this when you are adding a convenience model:

1. define the schema under `vars/<domain>/intents/<category>/...`
2. add intent `settings.yml` layers where needed
3. add compiler helpers under `filter_plugins/bigip_filters/`
4. add `playbooks/<domain>/prep/intents/<category>/load-*.yml`
5. add `playbooks/<domain>/prep/intents/<category>/build-*.yml`
6. merge compiled output into the canonical runtime collections
7. reject ownership collisions in validation
8. document the intent class in `docs/intents/`
9. run `make validate`

Keep runtime tasks canonical-only. Do not keep adding intent-specific branching to `tasks/apply.yml` or `tasks/delete.yml`.

## New Runtime Domain Checklist

Use this when the repo really needs a new playbook:

1. create `playbooks/<domain>.yml`
2. create `playbooks/<domain>/prep.yml`
3. create `playbooks/<domain>/tasks/manage.yml`
4. create `playbooks/<domain>/tasks/apply.yml`
5. create `playbooks/<domain>/tasks/delete.yml`
6. create `playbooks/<domain>/tasks/audit.yml`
7. create `vars/<domain>/...` and `vars/<domain>/deletions/...`
8. add validator coverage
9. add drift/import or document the explicit exception
10. create `docs/<domain>.md`
11. update [playbook-structure.md](playbook-structure.md), [var-layout.md](var-layout.md), and [README.md](../README.md)
12. run `make validate`

## What Good Docs Must Answer

Every domain or extension doc should answer:

- what the playbook manages
- where the vars live
- what the object types are
- which files reference which other files
- what apply and delete order is
- whether helper tools cover the domain, and at what fidelity
- whether the model is canonical runtime data or intent data

## Related Docs

- [playbook-structure.md](playbook-structure.md)
- [var-layout.md](var-layout.md)
- [validation.md](validation.md)
- [drift-import.md](drift-import.md)
- [intents/how-to-build-intents.md](intents/how-to-build-intents.md)
