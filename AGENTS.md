# Agent Instructions

These rules apply to any AI agent working in this repository.

## Project Overview

This repository manages F5 BIG-IP through declarative Ansible playbooks organized for GitOps-style operations. It targets AWX as the primary control plane with CLI fallback for bootstrap and recovery.

## Core Structure

- `playbooks/` — canonical playbooks (network, system, ha, ltm, gtm, tls, security)
- `vars/` — split var trees organized by domain with `settings.yml` inheritance
- `docs/` — all operational documentation
- `tools/` — validation and utility scripts
- `ROADMAP.md` — implementation status, backlog, and execution plan

## Documentation Rules

These are binding. Do not skip any of these steps when implementing a feature.

## Implementation Integrity Rules

These are also binding. A feature is not complete just because syntax-check passes or because `apply.yml` has tasks.

- Do not mark a roadmap item complete unless the feature is operationally complete across the repo model:
  - `prep.yml` loads and classifies the data the runtime tasks actually consume
  - `tasks/apply.yml` supports create/update behavior
  - `tasks/delete.yml` supports reverse-order deletion behavior
  - `tasks/manage.yml` preserves repo-standard ordering and config save behavior
  - `tools/validate-vars` validates the tree and its references
  - `tools/drift-check` and `tools/import-from-bigip` are updated when the repo expects GitOps lifecycle coverage for that object family
  - docs and example var files describe the same field model that the runtime tasks actually use

- Do not claim “feature coverage” for an object family if only one half exists.
  Examples of incomplete work that must not be described as complete:
  - create/update exists but delete is missing
  - var examples describe fields that the playbook does not consume
  - validator accepts a structure that runtime tasks never read
  - docs describe an older model (for example import bundles) while runtime has moved to first-class object management

- Preserve repo-wide contracts when adding a new domain or refactoring an existing one:
  - use the repo-wide `provider` variable from `vars/common.yml`
  - keep `tasks/manage.yml` as delete-first then apply-second unless ROADMAP explicitly documents an exception
  - keep example var files, docs, and helper tools aligned with the canonical playbook behavior

- If a helper tool cannot yet support a newly added object family well, record that explicitly in `ROADMAP.md` as a remaining gap instead of silently implying full GitOps parity.

### Inline Var File Documentation

Every example var file must begin with a YAML comment block that documents:

- **purpose**: what this file demonstrates and which domain it belongs to
- **cross-file linkages**: which other var files reference objects defined here, and which files the objects here reference (use backtick-quoted relative paths like `` `vars/ltm/pools/vm-applications.yml` ``)
- **supported fields**: a brief list of the top-level fields the objects in this file accept, especially non-obvious ones

Example header:

```yaml
---
# AFM address list examples for network firewall policy enforcement.
# Address lists are referenced by AFM firewall rules in `vars/security/afm/rules/platform-rules.yml`.
# Supported fields: `addresses` (individual IPs/CIDRs), `address_ranges` (start-end format),
# `address_lists` (nested references), `geo_locations`, and `fqdns`.
```

### Per-Domain Documentation

Every new domain/playbook must produce a `docs/<domain>.md` file that covers:

- overview of what the playbook manages
- playbook structure diagram (entrypoint, prep, tasks)
- var tree layout with directory paths
- object type reference table with fields, types, and whether required
- authoring patterns (defaults, deletions, hybrid model)
- dependency order for apply and delete operations

Update existing `docs/` files when an existing domain changes:

- `docs/playbook-structure.md` — add new playbooks to the playbook list and split layout mention
- `docs/var-layout.md` — add new var trees to the domain trees list
- `docs/example-models.md` — add a section explaining the new domain's authoring model and cross-file linkages
- `docs/hybrid-authoring.md` — update if a new hybrid pattern is introduced
- `docs/security.md` — update when AFM, WAF, or APM object types are added or changed

### README.md Updates

When a new playbook is added or an existing playbook gains new object coverage:

- add a row to the quick links table pointing to the new `docs/<domain>.md` (or update the existing row)
- add or update a row in the playbooks table with the domain name and object coverage
- verify any renamed or consolidated docs still have valid README quick links

### Bootstrap and Setup Documentation

When changing the bootstrap story, onboarding flow, or target-selection model:

- update the relevant setup docs under `docs/` such as:
  - `docs/cli-bootstrap.md`
  - `docs/awx-ha-bootstrap.md`
  - `docs/awx-operation.md`
  - `docs/system-management.md`
- if the change affects first-run or brand-new appliance setup, record any remaining documentation gaps in `ROADMAP.md` instead of assuming existing bootstrap docs are sufficient

### Empty Directories

If an empty directory must exist intentionally (e.g., a deletions tree with no entries yet), include a `.gitkeep`.

## Roadmap Maintenance

- update `ROADMAP.md` Current State section when new features are implemented
- update the backlog checklist (`Recommended Near-Term Backlog`) when work is completed
- update milestone checklists (`Issue-Sized Execution Plan`) when work is completed
- update the Implementation Audit section when new objects or playbooks are added
- update the Not Implemented Yet list when gaps are filled
- if a playbook is intentionally kept monolithic instead of split, record the reason in ROADMAP.md

## Mandatory Post-Change Checklist

These updates are **required after every feature change** (new object types, new fields, new var trees, new playbooks). Do not skip any item.

### Playbooks (when adding or modifying a domain)

- [ ] `playbooks/<domain>.yml` or root wrapper — add or update entrypoint
- [ ] `playbooks/<domain>/prep.yml` — discovery, `include_vars`, defaults loading, aggregation for new var trees
- [ ] `playbooks/<domain>/tasks/apply.yml` — `state: present` tasks for new object types
- [ ] `playbooks/<domain>/tasks/delete.yml` — `state: absent` tasks for new object types (reverse dependency order)
- [ ] `playbooks/<domain>/tasks/manage.yml` — update `bigip_config` save conditions to include new present/delete variables
- [ ] confirm any nested example data structures are flattened or transformed in `prep.yml` if runtime tasks require flattened loops
- [ ] confirm example field names match the fields actually consumed by runtime tasks

### Var Trees (when adding a new object type)

- [ ] `vars/<domain>/<type>/` — create directory with example var file and `settings.yml`
- [ ] `vars/<domain>/deletions/<type>/` — create directory with `.gitkeep`
- [ ] Every example var file must have the inline YAML comment header (purpose, cross-file linkages, supported fields)

### Validation

- [ ] `tools/validate-vars` — add `TreeSpec` entry, type-specific validation in `validate_<domain>()`, duplicate checks, cross-reference validation, and field validation
- [ ] `Makefile` — ensure `validate-ansible` target includes the affected playbook
- [ ] run `make validate` and confirm it passes

### Drift Detection

- [ ] `tools/drift-check` — add a `load` entry in `VarTreeLoader.load()` for the new var tree directory
- [ ] `tools/drift-check` — add a BIG-IP REST endpoint mapping in `DriftChecker.BIGIP_ENDPOINTS`
- [ ] `tools/drift-check` — add non-standard name fields to `DriftChecker.NAME_FIELDS` if applicable
- [ ] `tools/drift-check` — add value drift comparisons in `_find_value_drift` for the new type's fields

### Import Tooling

- [ ] `tools/import-from-bigip` — add an `ImportSpec` entry in `IMPORT_SPECS` with endpoint, output directory, top-level key, and field extraction
- [ ] `tools/import-from-bigip` — add type-specific transformation logic in `_transform_item` (pool members, virtual server references, etc.) if needed

### Documentation

- [ ] `docs/<domain>.md` — create for new domains, update for existing domains with changed object types
- [ ] `docs/playbook-structure.md` — add new playbooks to the playbook list
- [ ] `docs/var-layout.md` — add new var trees to the domain trees list
- [ ] `README.md` — update quick links table and playbooks table
- [ ] `ROADMAP.md` — update Current State, Implementation Audit, backlog, milestone checklists, and Not Implemented Yet
- [ ] verify docs do not describe superseded implementation models
- [ ] verify example var files still match the documented and implemented field model

### Docker and CI

- [ ] `Dockerfile.validation` — add any new Python packages or system tools required by new imports in validation/drift/import scripts
- [ ] `.gitlab-ci.yml` — update `before_script` if new Python packages were added
- [ ] verify `docker build -f Dockerfile.validation .` succeeds

## Playbook Structure

- keep canonical playbooks under `playbooks/` and keep root-level wrapper playbooks working during transitions
- default to the split canonical playbook model:
  - `playbooks/<domain>.yml` — entrypoint
  - `playbooks/<domain>/prep.yml` — discovery, `include_vars`, defaults loading, aggregation
  - `playbooks/<domain>/tasks/manage.yml` — task ordering
  - `playbooks/<domain>/tasks/delete.yml` — destructive tasks
  - `playbooks/<domain>/tasks/apply.yml` — present-state tasks
- if a future playbook stays small enough that splitting adds no value, document the reason in ROADMAP.md

## Commit Messages

- at the end of every implementation prompt, after changes are made and validated, print a suggested commit message
- do not run `git commit` unless explicitly asked
