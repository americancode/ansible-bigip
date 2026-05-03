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

1. Refactor existing LTM and GTM shortcut patterns onto the documented intent-layer design
   - migrate current inline/nested shortcut handling out of runtime-task logic and into the proposed normalization/compiler layer
   - preserve the existing canonical object model as the apply/delete contract

2. Helper-tool maturity decisions for `system` and `ha`
   - either add drift/import coverage
   - or keep them explicitly documented as `runtime+validation` for the current phase

3. Configuration snapshot and recovery workflows
   - UCS backup/export workflow
   - explicit operational guidance for snapshot use in change and rollback paths

4. Certificate lifecycle automation
   - certificate rotation workflows
   - renewal/expiry detection

## Open Backlog

These are the concrete remaining backlog items.

1. Refactor existing LTM and GTM shortcut models onto the intent/compiler design
   - move the current LTM inline pool/member shortcut behavior into the new design
   - move the current GTM inline/derived shortcut behavior into the new design
   - keep `playbooks/ltm.yml` and `playbooks/gtm.yml` structurally simpler after the refactor
   - the architecture target is documented in `docs/intent-authoring.md`

2. Decide the helper-tool lifecycle target for `system` and `ha`
   - either implement drift/import support
   - or document them as intentional `runtime+validation` boundaries in long-term steady state

3. UCS backup/export workflow for configuration snapshots
   - priority: lower than management-plane auth, compliance, and current repo-boundary decisions
   - completion target: `runtime+validation`

4. Certificate rotation automation with renewal detection
   - priority: lower than management-plane auth, compliance, and current repo-boundary decisions
   - completion target: `runtime+validation+helper-tools` where practical

5. Future deeper helper-tool fidelity
   - if needed, promote selected object families from `basic field drift` toward `model-aware`
   - only pursue this when the operational value is clear

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
