# BIG-IP Enterprise GitOps Roadmap

## Objective

Evolve this repository from a focused set of `network`, `ltm`, and `gtm` playbooks into an enterprise GitOps control plane for BIG-IP.

Target outcome:

- most BIG-IP changes are made through Git
- object ownership is clear by directory and team boundary
- destructive changes are explicit and reviewable
- validation happens before Ansible talks to a device
- platform, service, DNS, security, and lifecycle operations are all covered

## Current State

The repository already supports:

- declarative `network`, `ltm`, and `gtm` playbooks
- split var trees for scale
- per-directory `settings.yml` inheritance
- object-level partition overrides with `Common` fallback
- hybrid object modeling:
  - embedded pools under LTM virtual servers
  - embedded pools under GTM Wide IPs
  - first-class shared trees for reusable objects
- explicit deletion trees under `vars/*/deletions`
- reusable monitor definitions
- universal `enabled: true` default where modules support admin state
- offline validation through `tools/validate-vars`
- `make validate` wrapper
- `system.yml` for hostname, DNS, NTP, provisioning, users, and config save

The main remaining gaps are:

- deeper HA lifecycle beyond trust, groups, traffic groups, and config sync
- deeper LTM object coverage beyond pools/nodes/virtuals/monitors
- deeper GTM object coverage beyond datacenters/servers/pools/Wide IPs/monitors
- NATs and trunks
- security module coverage
- drift detection and promotion workflows

## Current Implementation Audit

This section is the roadmap-to-repo check.

Implemented today:

- `network.yml`
  - VLANs
  - route domains
  - self IPs
  - static routes
  - SNAT translations
  - SNAT pools
  - deletion trees
  - per-directory `settings.yml`
- `system.yml`
  - hostname
  - DNS
  - NTP/timezone
  - provisioning
  - users
  - config save
- `ha.yml`
  - device trust
  - device groups
  - device group members
  - traffic groups
  - config sync actions
- `tls.yml`
  - SSL keys
  - certificates
  - CA bundles
  - client SSL profiles
  - server SSL profiles
- `ltm.yml`
  - custom LTM monitors
  - first-class nodes
  - first-class pools
  - virtual-server-centric embedded pools
  - per-object and per-directory partition handling
  - enabled/disabled semantics where supported
  - deletion trees
- `gtm.yml`
  - custom GTM monitors
  - first-class datacenters
  - first-class servers
  - first-class pools
  - Wide-IP-centric embedded pools
  - static server model
  - optional LTM virtual resolution for GTM pool members
  - per-object and per-directory partition handling
  - enabled/disabled semantics where supported
  - deletion trees
- validation/tooling
  - YAML/schema/reference validation
  - duplicate detection
  - Ansible syntax-check wrapper

Not implemented yet:

- NATs and trunks
- LTM profiles, persistence, policies, iRules, data groups
- GTM topology and regions
- security modules
- live drift/import/promotion tooling

## Target Repo Shape

This is the recommended end-state layout.

```text
.
├── network.yml
├── ltm.yml
├── gtm.yml
├── system.yml
├── ha.yml
├── security.yml
├── tls.yml
├── tools/
├── docs/
└── vars/
    ├── common.yml
    ├── network/
    │   ├── vlans/
    │   ├── self_ips/
    │   ├── routes/
    │   ├── route_domains/
    │   ├── snats/
    │   ├── nats/
    │   └── deletions/
    ├── system/
    │   ├── dns/
    │   ├── ntp/
    │   ├── users/
    │   ├── auth/
    │   ├── banners/
    │   ├── provisioning/
    │   └── deletions/
    ├── ha/
    │   ├── device_trust/
    │   ├── sync_groups/
    │   ├── traffic_groups/
    │   └── deletions/
    ├── tls/
    │   ├── certificates/
    │   ├── keys/
    │   ├── ca_bundles/
    │   ├── client_ssl_profiles/
    │   ├── server_ssl_profiles/
    │   └── deletions/
    ├── ltm/
    │   ├── nodes/
    │   ├── monitors/
    │   ├── pools/
    │   ├── virtual_servers/
    │   ├── profiles/
    │   ├── persistence/
    │   ├── policies/
    │   ├── irules/
    │   ├── data_groups/
    │   └── deletions/
    ├── gtm/
    │   ├── datacenters/
    │   ├── monitors/
    │   ├── servers/
    │   ├── pools/
    │   ├── wide_ips/
    │   ├── topology/
    │   ├── regions/
    │   └── deletions/
    └── security/
        ├── afm/
        ├── waf/
        ├── apm/
        └── deletions/
```

## Delivery Principles

- Missing from vars does not mean delete.
- `/deletions` trees are the preferred destructive workflow.
- Object-level values override sibling `settings.yml`.
- Sibling `settings.yml` overrides playbook defaults.
- Shared objects should be modeled as first-class trees, not only nested under applications.
- The preferred authoring model is hybrid:
  - embed app-local objects for readability
  - promote shared or reused objects into first-class trees
- Validation must fail fast before playbook execution.
- Runtime drift should be detectable against live BIG-IP state.

## Execution Discipline

These are binding repo maintenance rules for every feature change, including future AI agents working in this repository.

- Update `ROADMAP.md` current state, backlog items, and milestone checklists when scope changes.
- Update example var files when a feature adds or changes an authoring pattern.
- Update docs alongside code so linkages and reference strings are explained where operators read them.
- Validate after each major change before moving to the next implementation step.
- Include a suggested commit name only after the implementation and validation are complete.

## Program Phases

## Phase 1: GitOps Foundation

Goal: make the repository safe to scale before adding major coverage.

### Deliverables

- schema validation for every object tree
- cross-file reference validation
- duplicate object detection
- partition and naming policy checks
- docs for active config vs deletion config
- consistent contributor conventions

### Work Items

- Create `tools/validate-vars` entrypoint
- Define validation rules for:
  - required keys
  - allowed keys
  - object identity fields
  - partition defaults
  - reference fields requiring fully-qualified names
- Add duplicate detection for:
  - LTM virtual server names
  - LTM pool names
  - GTM Wide IP names
  - GTM server names
  - network object names
- Add reference checks for:
  - pool monitor references
  - GTM pool monitor references
  - Wide IP to GTM pool references
  - LTM virtual server to pool references
- Add CI entrypoints for:
  - YAML parse
  - Ansible syntax check
  - schema/reference validation

### Exit Criteria

- broken references are caught before playbook runtime
- duplicate objects cannot merge unnoticed
- contributor guidance exists for adding new trees and `settings.yml`

## Phase 2: Platform and HA

Goal: manage base device configuration and cluster behavior through Git.

### Scope

- system settings
- users and auth
- licensing and provisioning
- HA trust and config sync
- device groups and traffic groups
- save/backup workflows

### Deliverables

- `system.yml`
- `ha.yml`
- var trees for base platform objects
- explicit config save workflow

### Work Items

- Add system management for:
  - hostname
  - DNS
  - NTP
  - timezone
  - login banners
  - local users
  - auth provider integration
- Add module provisioning and license handling where supported
- Add HA management for:
  - device trust
  - sync-failover groups
  - traffic groups
  - mirroring and failover metadata
- Add backup hooks:
  - `bigip_config` save
  - optional UCS export workflow

### Exit Criteria

- a new device or pair can be brought to a managed baseline from Git
- config persistence is explicit and repeatable

## Phase 3: Network Expansion

Goal: complete the layer below LTM so traffic plumbing is fully managed.

### Scope

- routes
- route domains
- trunks
- SNATs and NATs
- floating/non-floating self IP patterns

### Deliverables

- first-class route and routing object trees
- network examples for multi-VLAN and multi-route-domain designs

### Work Items

- Add `vars/network/routes`
- Add `vars/network/route_domains`
- Add `vars/network/snats`
- Add `vars/network/nats`
- Add support for:
  - floating self IP examples
  - partitioned network ownership
  - route-domain aware object validation

### Exit Criteria

- enterprise network constructs no longer require UI-only changes

## Phase 4: LTM Shared Object Model

Goal: support both app-centric and shared-object-centric LTM authoring cleanly.

### Scope

- nodes
- pools as first-class objects
- profiles
- persistence
- policies
- shared application delivery objects

### Deliverables

- `vars/ltm/nodes`
- `vars/ltm/pools`
- `vars/ltm/profiles`
- `vars/ltm/persistence`
- updated `ltm.yml` or split playbooks by object family
- documented hybrid authoring guidance for embedded vs first-class objects

### Work Items

- Promote LTM nodes to a managed tree
- Promote LTM pools to a managed tree
- Support advanced pool fields:
  - priority groups
  - service down action
  - min active members
  - slow ramp
  - queueing
- Support advanced member fields:
  - ratio
  - connection limits
  - priority group
  - forced offline semantics
- Support virtual server fields:
  - persistence
  - fallback persistence
  - source CIDR
  - VLAN restrictions
  - metadata
  - iRules
  - policy attachments
  - log profiles
  - client/server SSL profiles
- Add hybrid readability shortcuts:
  - subdirectory `pool_defaults`
  - `member_defaults`
  - reusable `monitor_sets`
  - subdirectory maintenance/disable defaults

### Exit Criteria

- most LTM app delivery changes can be expressed in one readable app file when desired
- shared objects are reusable across many applications when needed

## Phase 5: TLS and Certificate Lifecycle

Goal: eliminate manual certificate and SSL profile handling.

### Scope

- cert/key import
- CA bundles
- client/server SSL profiles
- policy standardization

### Deliverables

- `tls.yml`
- `vars/tls/*`
- certificate rotation conventions

### Work Items

- Add certificate and key object trees
- Add bundle and trust object trees
- Add client SSL and server SSL profile trees
- Define secret-handling strategy for private keys
- Add validation for profile-to-certificate references

### Exit Criteria

- TLS onboarding and renewal workflows are Git-driven

## Phase 6: GTM Full Object Model

Goal: move GTM beyond Wide IP centric examples into a complete DNS traffic model.

### Scope

- datacenters
- static servers
- GTM pools as first-class objects
- regions and topology
- advanced Wide IP behavior

### Deliverables

- `vars/gtm/datacenters`
- `vars/gtm/pools`
- `vars/gtm/topology`
- `vars/gtm/regions`

### Work Items

- Promote datacenters to first-class objects
- Split GTM servers into:
  - BIG-IP servers
  - static servers
- Promote GTM pools to first-class objects
- Preserve the hybrid GTM authoring model:
  - inline pools under Wide IPs for app readability
  - first-class GTM pools for shared/reused service definitions
- Support advanced Wide IP fields:
  - aliases
  - persistence
  - last resort pool
  - load-balancing policy combinations
- Add topology and region support
- Add hybrid readability shortcuts:
  - subdirectory `pool_defaults`
  - reusable `monitor_sets`
  - subdirectory maintenance/disable defaults
  - optional deterministic resolution of `address`/`port` from repo-known LTM virtual servers
- Add dependency validation across:
  - Wide IPs
  - GTM pools
  - GTM servers
  - GTM virtual servers

### Exit Criteria

- GTM application routing can be modeled cleanly for large estates
- datacenters and static servers are no longer implicit side effects

## Phase 7: Security Modules

Goal: cover the enterprise controls that often remain UI-managed.

### Scope

- AFM
- WAF/ASM
- APM

### Deliverables

- `security.yml`
- security var trees by module

### Work Items

- Start with AFM if licensed:
  - address lists
  - port lists
  - rule lists
  - policies
- Add WAF policy attachment flows if used
- Add APM/access object support if used
- Define ownership and approval boundaries for security changes

### Exit Criteria

- major security controls can be reviewed and applied through Git

## Phase 8: Drift, Import, and Lifecycle Tooling

Goal: make the system operable at enterprise scale over time.

### Scope

- drift detection
- brownfield import
- promotion workflows
- rollback support

### Deliverables

- live-vs-git comparison tooling
- import helpers for existing BIG-IP estates
- release/promotion guidance

### Work Items

- Build export/import helpers for existing devices
- Build drift detection reports
- Add environment promotion conventions:
  - dev
  - test
  - prod
- Add change preview output where possible
- Define rollback patterns for destructive and non-destructive changes

### Exit Criteria

- teams can onboard existing F5 estates without manual re-entry
- unauthorized drift becomes visible

## Recommended Near-Term Backlog

This is the practical next sequence for the current repo.

1. [x] Add validation tooling and CI gates
2. [x] Add `vars/ltm/nodes` and `vars/ltm/pools`
3. [x] Add `vars/gtm/datacenters` and `vars/gtm/pools`
4. [x] Add `system.yml` for base platform settings
5. [x] Add `ha.yml` for trust/sync/failover
6. [x] Add `tls.yml` for certs and SSL profiles
7. [ ] Add NAT and trunk support to complete network expansion
8. [x] Add hybrid readability shortcuts:
   - [x] `pool_defaults`
   - [x] `member_defaults`
   - [x] `monitor_sets`
   - [x] subdirectory maintenance defaults via `settings.yml` object defaults
9. [x] Add optional LTM virtual resolution
10. [x] Define TLS secret handling approach

## Issue-Sized Execution Plan

These are the first concrete tickets I would open.

### Milestone 1: Validation

- [x] Create `tools/validate-vars`
- [x] Add schema checks for `network`, `ltm`, and `gtm`
- [x] Add reference validation across existing object trees
- [x] Add duplicate object detection
- [x] Add `make validate` or equivalent wrapper

### Milestone 2: LTM Shared Objects

- [x] Add `vars/ltm/nodes`
- [x] Add `vars/ltm/pools`
- [x] Refactor `ltm.yml` to support first-class pool and node objects
- [x] Keep hybrid support for virtual-server-centric embedded pools
- [x] Add `pool_defaults`, `member_defaults`, and `monitor_sets`
- [x] Add subdirectory maintenance defaults

### Milestone 3: GTM Shared Objects

- [x] Add `vars/gtm/datacenters`
- [x] Add `vars/gtm/pools`
- [x] Refactor `gtm.yml` so datacenters and pools are explicit managed trees
- [x] Add separate static server model
- [x] Restore hybrid Wide IP embedded-pool support
- [x] Add GTM `pool_defaults`, `member_defaults`, and `monitor_sets`
- [x] Add subdirectory maintenance defaults
- [x] Add optional LTM virtual resolution

### Milestone 4: Platform and HA

- [x] Add `system.yml`
- [x] Add `ha.yml`
- [x] Implement config save workflow
- [x] Add examples for active/standby pair bootstrap

### Milestone 5: TLS

- [x] Add `tls.yml`
- [x] Add certificate, key, and SSL profile trees
- [x] Define secret handling approach

## Network Expansion Status

The repo now covers route domains, static routes, SNAT translations, and SNAT pools.

Remaining network gap:

- NAT object management does not have a first-class module in the installed `f5networks.f5_modules` collection, so this roadmap item remains open until that strategy is defined alongside trunk support.

## TLS Secret Handling Status

The repo now supports inline Ansible Vault content in offline validation and documents Ansible Vault as the default secret-handling approach for TLS private keys.

Recommended convention:

- store TLS object metadata in the normal `vars/tls/*` trees
- encrypt `content` values inline with `!vault`
- keep private keys encrypted at rest in Git
- optionally encrypt certificates and CA bundles when local policy requires it

## Decisions To Make Early

These choices affect almost every later phase.

- whether `system` should remain a separate domain from `network`
- whether LTM should stay in one playbook or split into `ltm-shared.yml` and `ltm-virtuals.yml`
- whether Ansible Vault remains the standard secret mechanism long-term or is replaced by:
  - SOPS
  - external secret manager
- how CI gets device-adjacent test coverage:
  - syntax only
  - mocked validation
  - lab BIG-IP smoke tests
- whether environment separation is directory-based, branch-based, or repo-based

## Success Criteria

This program is succeeding when:

- teams stop using the BIG-IP UI for routine change windows
- app-local objects are readable in one place when that helps operators
- shared objects are reusable and clearly owned when reuse matters
- destructive changes are explicit and reviewable
- drift from Git becomes visible
- new services can be onboarded by adding files, not by inventing playbook logic
