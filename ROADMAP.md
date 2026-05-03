# BIG-IP Enterprise GitOps Roadmap

## Objective

Keep this repository moving toward a practical BIG-IP GitOps control plane:

- most BIG-IP changes are made through Git
- object ownership is clear by directory and team boundary
- destructive changes are explicit and reviewable
- validation happens before Ansible talks to a device
- setup, steady-state operations, and lifecycle work are all covered

## Current Platform Summary

The repo already manages the main BIG-IP runtime domains through canonical playbooks under `playbooks/`:

- `bootstrap` for day-0 licensing and first management reachability
- `network` for VLANs, trunks, route domains, self IPs, routes, SNAT translations, SNAT pools, and NATs
- `system` for hostname, DNS, NTP/timezone, provisioning, users, management-plane admin authentication, login banners, and config save
- `ha` for device connectivity, trust, sync groups, HA groups, traffic groups, and config sync actions
- `ltm` for monitors, profiles, nodes, pools, virtual servers, persistence, iRules, data groups, and policies
  - this now includes dedicated intent/compiler authoring for RKE2 server cluster virtual-server bundles under `vars/ltm/intents/clusters/`
- `gtm` for monitors, datacenters, servers, pools, Wide IPs, regions, and topology records
- `tls` for keys, certificates, CA bundles, and SSL profiles
- `security` for AFM, WAF, and APM objects

The repo structure is standardized:

- canonical playbooks live under `playbooks/`
- root-level `*.yml` files are compatibility wrappers
- each canonical domain uses `prep.yml`, `tasks/manage.yml`, `tasks/delete.yml`, and `tasks/apply.yml`
- `bootstrap` is the documented exception: it is apply-only and keeps `tasks/delete.yml` intentionally empty
- split var trees under `vars/` use per-directory `settings.yml`
- explicit deletion trees live under `vars/*/deletions`

The repo also has first-class helper tooling:

- `tools/validate-vars` for offline validation
- `tools/drift-check` for live-vs-Git comparison
- `tools/import-from-bigip` for brownfield import
- Python-backed prep/compiler helpers under `filter_plugins/bigip_filters/`, with `filter_plugins/bigip_var_filters.py` kept as the Ansible filter entrypoint
- shared prep snippets under `playbooks/shared/prep/` for fragment discovery, settings-aware aggregation, and present/delete classification across the standard domains
- recursive nested var-tree discovery and hierarchical multi-level `settings.yml` inheritance across canonical playbooks, including the older specialized LTM/GTM loaders

## Capability Boundaries

These boundaries must stay explicit.

- `bootstrap` is currently `runtime+validation`
  - it is intentionally day-0 and apply-only
  - drift/import coverage is intentionally not part of its current scope
- `system` and `ha` are currently `runtime+validation`
  - they are operationally useful, but not yet helper-tool complete
  - `ha_device_connectivity` is additionally an apply-oriented sub-surface whose deletion trees remain intentionally unsupported
- the broader service/runtime domains are generally `runtime+validation+helper-tools`
  - helper-tool fidelity varies by object family
- newer families are generally closed at `basic field drift`, not universal full semantic parity
- intent trees are authoring abstractions, not separate live BIG-IP object families; helper tools continue to treat the compiled canonical objects as the lifecycle surface unless documented otherwise
- intent trees should be category-first under `vars/<domain>/intents/<category>/...`, not flat directly under `intents/`
- intent compiler snippets should live under `playbooks/<domain>/prep/intents/<category>/...` when they are part of the dedicated intent layer
- prep refactors that move repeated loading, compiler, or classification logic into Python-backed helpers should be treated as repo-wide architecture work and applied everywhere they make sense across canonical playbooks, not as one-off cleanups in only one domain

## Acceptance Criteria

These rules define what "done" means for roadmap work.

### Completion Classes

- `runtime-only`
  - playbook behavior exists, but validator and/or helper-tool lifecycle support is intentionally incomplete
- `runtime+validation`
  - runtime exists
  - `tools/validate-vars` supports the object tree and references
  - helper-tool lifecycle support is intentionally incomplete and documented
- `runtime+validation+helper-tools`
  - runtime exists
  - validator exists
  - `tools/drift-check` and `tools/import-from-bigip` support the object family at an explicitly stated fidelity level
- `full parity`
  - runtime, validator, helper tools, docs, example vars, README, and roadmap are aligned

### Helper-Tool Fidelity

- `identity-only`
  - helper tools can detect or import object presence by identity, but do not claim meaningful field-level parity
- `basic field drift`
  - helper tools compare or import a limited, explicitly documented field subset
- `model-aware`
  - helper tools reconstruct nested structures and cross-object linkages in the repo's actual field model

### Required Evidence Before Calling Work Complete

- state the completion class being claimed
- state the helper-tool fidelity level where applicable
- name the repo layers updated:
  - runtime playbooks
  - validator
  - drift/import tooling
  - docs
  - example vars
  - roadmap state
- name the validation commands that passed

### Prohibited Completion Behavior

Do not call work complete when any of the following is true:

- runtime exists but delete behavior is missing without an explicit documented exception
- `prep.yml` does not actually load the field model used by runtime tasks
- validator accepts a different model than runtime uses
- docs or examples describe fields the runtime does not consume
- helper tools point at the wrong BIG-IP endpoints or wrong repo var keys
- roadmap wording claims stronger parity than the code actually provides

## Active Priorities

These are the highest-value open items.

1. Code-path documentation hardening for contributors
   - function-level documentation across `filter_plugins/` and `filter_plugins/bigip_filters/`
   - top-level header comments and targeted inline comments across playbook prep/task files
   - prioritize the paths new contributors are most likely to extend incorrectly: intent/compiler wiring, prep loaders/builders, and canonical task ordering

2. Configuration snapshot and recovery workflows
   - UCS backup/export workflow
   - explicit operational guidance for snapshot use in change and rollback paths

3. Certificate lifecycle automation
   - certificate rotation workflows
   - renewal/expiry detection

## Open Backlog

These are the concrete remaining backlog items.

1. Add function-level documentation across `filter_plugins/bigip_var_filters.py` and `filter_plugins/bigip_filters/*.py`
   - document purpose, inputs, outputs, emitted canonical object shapes, and key assumptions
   - add inline comments where normalization or name generation is non-obvious

2. Add top-level header comments across canonical playbook prep/task files
   - cover what each file produces or mutates
   - start with `prep.yml`, `prep/*.yml`, and `tasks/manage.yml`

3. Add targeted inline comments across playbook task/job files in manageable domain batches
   - batch 1: `bootstrap`, `network`, `system`, `ha`, `tls`
   - batch 2: `ltm`, `gtm`
   - batch 3: `security`
   - focus on task ordering, data reshaping, compiler handoff, lookup building, and delete/apply merging

4. UCS backup/export workflow for configuration snapshots
   - priority: lower than management-plane auth, compliance, and current repo-boundary decisions
   - completion target: `runtime+validation`

5. Certificate rotation automation with renewal detection
   - priority: lower than management-plane auth, compliance, and current repo-boundary decisions
   - completion target: `runtime+validation+helper-tools` where practical

6. Future deeper helper-tool fidelity
   - if needed, promote selected object families from `basic field drift` toward `model-aware`
   - only pursue this when the operational value is clear

## Future Domain Candidates

These are possible future domain splits or lifecycle surfaces. They are not committed backlog items yet.

- `backup` or `snapshot`
  - UCS backup/export workflows
  - possibly other operational artifact exports later
- `cert-lifecycle`
  - certificate renewal detection
  - rotation orchestration
  - external PKI workflow integration if needed
- `observability`
  - telemetry streaming
  - logging/export integrations
  - analytics-facing platform configuration
- deeper WAF content lifecycle
  - only if WAF policy/content management grows beyond the current `security` domain scope
- brownfield onboarding/promotion workflow surfaces
  - only if import/reconciliation/promotion grows large enough to justify a clearer lifecycle split

Default rule:

- do not create a new playbook/domain just because a feature exists
- prefer extending `system`, `security`, `tls`, or helper tooling unless a new surface is operationally distinct enough to justify its own domain

## Delivery Principles

- missing from vars does not mean delete
- `/deletions` trees are the preferred destructive workflow
- object-level values override sibling `settings.yml`
- sibling `settings.yml` overrides playbook defaults
- validation must fail before playbook execution
- helper-tool limitations must be documented, not implied away

## Execution Discipline

These are binding repo maintenance rules for every feature change, including future AI agents working in this repository.

### Documentation and Examples

- update `docs/` alongside every code change so linkages and reference strings are explained where operators read them
- update `README.md` when a feature changes the high-level playbook list, current capability summary, validation commands, or quick links
- update example var files under `vars/` when a feature adds or changes an authoring pattern
- do not put detailed domain documentation into `README.md`; keep it high-level and link to `docs/`
- if an empty directory must exist intentionally, include a `.gitkeep`

### Roadmap Maintenance

- keep `Current Platform Summary` accurate when major capability or structure changes land
- keep `Capability Boundaries` accurate when a domain changes completion class or helper-tool expectations
- update `Active Priorities` and `Open Backlog` when work is completed, deferred, or newly discovered
- if a discovered gap changes the real delivery story, record it here before expanding into more feature work
- when marking an item complete in implementation notes or closeouts, state its completion class and helper-tool fidelity explicitly

### Playbook Structure

- keep canonical playbooks under `playbooks/` and keep root-level wrapper playbooks working during transitions
- default to the split canonical playbook model: keep discovery/default aggregation in `playbooks/<domain>/prep.yml`, keep `tasks/manage.yml` as the ordering wrapper, and separate destructive tasks into `tasks/delete.yml` from present-state tasks in `tasks/apply.yml`
- when prep logic becomes large, keep top-level `prep.yml` as a documented orchestrator and split discovery/loading/classification/compiler flows into focused `playbooks/<domain>/prep/*.yml` snippets
- when the same prep mechanics are repeated across domains, prefer shared snippets under `playbooks/shared/prep/` backed by shared Python helpers instead of duplicating the pattern in each domain

### Validation and Commits

- validate after each major change before moving to the next implementation step
- in final closeouts, name the validation commands that actually passed
- at the end of every implementation prompt, after changes are made and validated, print a suggested commit message

## Success Criteria

This roadmap is succeeding when:

- teams stop using the BIG-IP UI for routine changes
- setup and steady-state operations are both Git-driven
- shared objects are reusable and clearly owned
- destructive changes are explicit and reviewable
- helper-tool coverage is honest about its fidelity and limitations
