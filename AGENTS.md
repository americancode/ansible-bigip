# Agent Instructions

These rules apply to any AI agent working in this repository.

## Project Overview

This repository manages F5 BIG-IP through declarative Ansible playbooks organized for GitOps-style operations. It targets AWX as the primary control plane with CLI fallback for bootstrap and recovery.

## Core Structure

- `playbooks/` — canonical playbooks (network, system, ha, ltm, gtm, tls)
- `vars/` — split var trees organized by domain with `settings.yml` inheritance
- `docs/` — all operational documentation
- `tools/` — validation and utility scripts
- `ROADMAP.md` — implementation status, backlog, and execution plan

## Documentation Rules

- update `docs/` alongside every code change
- keep `README.md` minimal: only project overview, quick links table, playbook list, and validation command
- do not add operational detail to `README.md`; put it in `docs/`
- update example var files under `vars/` when a feature adds or changes an authoring pattern
- explain cross-file linkages and reference strings inline where operators will read them
- if an empty directory must exist intentionally, include a `.gitkeep`

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
- update `tools/validate-vars` when adding new var trees or object types:
  - add a `TreeSpec` entry for every new active and deletion directory
  - add type-specific validation in the appropriate `validate_*` method
  - add duplicate checks for all new object types
  - validate new fields (type, required keys, cross-references) where applicable
- never introduce a new var tree without corresponding validation coverage

## Commit Messages

- at the end of every implementation prompt, after changes are made and validated, print a suggested commit message
- do not run `git commit` unless explicitly asked
