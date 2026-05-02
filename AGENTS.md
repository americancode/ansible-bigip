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

### README.md Updates

When a new playbook is added:

- add a row to the quick links table pointing to the new `docs/<domain>.md`
- add a row to the playbooks table with the domain name and object coverage

### Empty Directories

If an empty directory must exist intentionally (e.g., a deletions tree with no entries yet), include a `.gitkeep`.

## Roadmap Maintenance

- update `ROADMAP.md` Current State section when new features are implemented
- update the backlog checklist (`Recommended Near-Term Backlog`) when work is completed
- update milestone checklists (`Issue-Sized Execution Plan`) when work is completed
- update the Implementation Audit section when new objects or playbooks are added
- update the Not Implemented Yet list when gaps are filled
- if a playbook is intentionally kept monolithic instead of split, record the reason in ROADMAP.md

## Playbook Structure

- keep canonical playbooks under `playbooks/` and keep root-level wrapper playbooks working during transitions
- default to the split canonical playbook model:
  - `playbooks/<domain>.yml` — entrypoint
  - `playbooks/<domain>/prep.yml` — discovery, `include_vars`, defaults loading, aggregation
  - `playbooks/<domain>/tasks/manage.yml` — task ordering
  - `playbooks/<domain>/tasks/delete.yml` — destructive tasks
  - `playbooks/<domain>/tasks/apply.yml` — present-state tasks
- if a future playbook stays small enough that splitting adds no value, document the reason in ROADMAP.md

## Validation

- run `make validate` after each major change before moving to the next step
- validation must pass before any playbook execution
- on every feature change (new object types, new fields, new var trees):
  - update `tools/validate-vars` with TreeSpec entries, type-specific validation, duplicate checks, and field validation
  - update `Makefile` validate-ansible target to include new playbooks
- never introduce a new var tree without corresponding validation coverage

## Drift Detection

- on every feature change, update `tools/drift-check`:
  - add a `load` entry in `VarTreeLoader.load()` for new var tree directories
  - add a BIG-IP REST endpoint mapping in `DriftChecker.BIGIP_ENDPOINTS`
  - add non-standard name fields to `DriftChecker.NAME_FIELDS` if applicable
  - add value drift comparisons in `_find_value_drift` for the new type's fields
- on every feature change, update `tools/import-from-bigip`:
  - add an `ImportSpec` entry in `IMPORT_SPECS` with endpoint, output directory, top-level key, and field extraction
  - add type-specific transformation logic in `_transform_item` (pool members, virtual server references, etc.)

## Docker and Dependencies

- keep `Dockerfile.validation` up to date with all Python packages and system tools required to run the full validation and drift suite
- any new Python import in `tools/validate-vars`, `tools/drift-check`, or `tools/import-from-bigip` must be added to `Dockerfile.validation` and `.gitlab-ci.yml` `before_script`
- verify the Docker image builds successfully after adding dependencies

## Commit Messages

- at the end of every implementation prompt, after changes are made and validated, print a suggested commit message
- do not run `git commit` unless explicitly asked
