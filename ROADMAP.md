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

The repository is already a viable GitOps control plane for BIG-IP runtime configuration:

- declarative `network`, `system`, `ha`, `ltm`, `gtm`, `security`, and `tls` playbooks
- canonical playbooks organized under `playbooks/` with root-level wrapper entrypoints
- all canonical playbooks use the split model: `<domain>.yml`, `prep.yml`, `tasks/manage.yml`, `tasks/apply.yml`, `tasks/delete.yml`
- split var trees for scale across all domains
- per-directory `settings.yml` inheritance with object-level override → sibling settings → playbook fallback precedence
- object-level partition overrides with `Common` fallback
- inventory-driven BIG-IP target selection through `f5_host` with `F5_HOST` env fallback
- hybrid object modeling:
  - embedded pools under LTM virtual servers
  - embedded pools under GTM Wide IPs
  - first-class shared trees for reusable objects
  - first-class persistence profiles, iRules, data groups, and LTM policies
  - first-class GTM topology regions and topology records
  - hybrid readability shortcuts (`pool_defaults`, `member_defaults`, `monitor_sets`)
- explicit deletion trees under `vars/*/deletions` and `state: absent` inline pattern
- reusable monitor definitions
- universal `enabled: true` default where modules support admin state
- offline validation through `tools/validate-vars` with `make validate` wrapper
- modular documentation under `docs/` covering playbook structure, var layout, hybrid authoring, deletion workflows, AWX operation, validation, TLS secrets, network objects, system management, LTM advanced fields, GTM advanced fields, and bootstrap paths

The repo is not yet at full GitOps parity for every lifecycle path. The main remaining work falls into three buckets:

- stabilize feature parity across runtime, validation, drift detection, import tooling, examples, and docs
- close day-0 and operator-lifecycle gaps so initial setup and long-term maintenance are both Git-driven
- expand deeper platform lifecycle coverage where runtime support is still missing

## Immediate Stabilization Priorities

These items are the top priority before more feature expansion.

1. audit every checked-off roadmap item against actual code, examples, validator coverage, drift tooling, and import tooling
2. fix helper-tool object mappings where newer coverage was added against the wrong BIG-IP endpoints or wrong repo var keys
3. align runtime, validator, docs, and example vars where the current field models drifted apart
4. finish helper-tool parity for newer object trees where runtime playbook support exists but drift/import parity is still partial
5. decide explicitly which domains are considered runtime-complete but not yet drift/import-complete, and document that boundary clearly

## Next Major Gaps

- deepen drift tooling from basic existence checks to field-level comparison for newer object families
- add true day-0 onboarding for brand-new BIG-IPs so Git can drive licensing, initial management bootstrap, and first secure API handoff
- add explicit initial-setup documentation for first-boot prerequisites, pre-AWX appliance preparation, and cutover into repo-managed state
- deeper HA lifecycle (connection mirroring, failover metadata, automated testing)
- UCS backup/export workflow
- certificate rotation automation
- auth provider integration for system users
- login banner management

## Current Implementation Audit

This section is the roadmap-to-repo check.

Implemented today:

- `network.yml`
  - VLANs
  - trunks
  - route domains
  - self IPs
  - static routes
  - SNAT translations
  - SNAT pools
  - NATs via validated `tmsh` workflow
  - deletion trees
  - per-directory `settings.yml`
  - canonical playbook entrypoint at `playbooks/network.yml`
  - internal split between canonical playbook wrapper, `prep.yml`, `tasks/manage.yml`, `tasks/delete.yml`, and `tasks/apply.yml`
- `system.yml`
  - hostname
  - DNS
  - NTP/timezone
  - provisioning
  - users
  - config save
  - canonical playbook entrypoint at `playbooks/system.yml`
  - internal split between canonical playbook wrapper, `prep.yml`, `tasks/manage.yml`, `tasks/delete.yml`, and `tasks/apply.yml`
- `ha.yml`
  - device trust
  - device groups
  - device group members
  - traffic groups
  - config sync actions
  - canonical playbook entrypoint at `playbooks/ha.yml`
  - internal split between canonical playbook wrapper, `prep.yml`, `tasks/manage.yml`, `tasks/delete.yml`, and `tasks/apply.yml`
- `tls.yml`
  - SSL keys
  - certificates
  - CA bundles
  - client SSL profiles
  - server SSL profiles
  - canonical playbook entrypoint at `playbooks/tls.yml`
  - internal split between canonical playbook wrapper, `prep.yml`, `tasks/manage.yml`, `tasks/delete.yml`, and `tasks/apply.yml`
- `ltm.yml`
  - custom LTM monitors
  - first-class non-TLS LTM profiles (`tcp`, `udp`, `fastl4`, `http`, `http2`, `oneconnect`)
  - first-class nodes
  - first-class pools
  - virtual-server-centric embedded pools
  - first-class persistence profiles (`cookie`, `source_addr`, `universal`)
  - first-class iRules
  - first-class data groups (`string`, `ip`, `integer`)
  - first-class LTM policies with rules, conditions, and actions
  - virtual server attachments for persistence, iRules, and policies
  - virtual server VLAN filtering, metadata, and log profiles
  - per-object and per-directory partition handling
  - enabled/disabled semantics where supported
  - deletion trees
  - canonical playbook entrypoint at `playbooks/ltm.yml`
  - internal split between canonical playbook wrapper, `prep.yml`, `tasks/manage.yml`, `tasks/delete.yml`, and `tasks/apply.yml`
- `gtm.yml`
  - custom GTM monitors
  - first-class datacenters
  - first-class servers
  - first-class pools
  - Wide-IP-centric embedded pools
  - static server model
  - optional LTM virtual resolution for GTM pool members
  - topology regions
  - topology records
  - per-object and per-directory partition handling
  - enabled/disabled semantics where supported
  - deletion trees
  - canonical playbook entrypoint at `playbooks/gtm.yml`
  - internal split between canonical playbook wrapper, `prep.yml`, `tasks/manage.yml`, `tasks/delete.yml`, and `tasks/apply.yml`
- `security.yml`
  - AFM address lists (addresses, ranges, nested lists, geo locations, FQDNs)
  - AFM port lists (ports, ranges, nested lists)
  - AFM firewall rules (actions, protocol, source/destination endpoints)
  - AFM firewall policies (ordered rule lists)
  - WAF/ASM policies (built-in templates, active/apply flags)
  - WAF server technologies (parent policy references)
  - APM ACLs (L4/L7 entries, actions, host/path/scheme matching)
  - APM authentication servers (AD, LDAP, RADIUS, TACACS, RSA, cert, localdb, SAML, OAuth)
  - APM SSO configurations (Kerberos, form-based, HTTP Basic, NTLM, SAML, OAuth, Citrix, domain-join)
  - APM resources (network access, webtop, remote desktop, portal access)
  - APM policy nodes (VPE flow nodes with auth/SSO/resource references)
  - APM access profiles (runtime support present; validator alignment still pending)
  - APM per-session policies (session-level authentication flows)
  - APM macros (reusable VPE building blocks)
  - per-directory `settings.yml` inheritance
  - deletion trees for all object types
  - canonical playbook entrypoint at `playbooks/security.yml`
  - internal split between canonical playbook wrapper, `prep.yml`, `tasks/manage.yml`, `tasks/delete.yml`, and `tasks/apply.yml`
- validation/tooling
  - YAML/schema/reference validation
  - duplicate detection
  - Ansible syntax-check wrapper
- drift detection and import tooling
  - `tools/drift-check` for live-vs-Git comparison
  - `tools/import-from-bigip` for brownfield import
  - CI-ready JSON output for dashboards
  - LTM, GTM, network, AFM, WAF, APM, and TLS object type support
  - partial newer-object coverage added for network route domains, trunks, SNATs, NATs, GTM topology, TLS CA bundles/client SSL/server SSL, WAF server technologies, and APM policy nodes/SSO configs
  - exhaustive parity still requires verified endpoint/key mappings and model-accurate extraction

Not implemented yet:

- HA connection mirroring and failover metadata
- Automated failover testing workflows
- UCS backup/export workflow
- Certificate rotation automation
- Auth provider integration for BIG-IP admin users
- Login banner management

## Coverage Status By Layer

This is the expected interpretation of feature status going forward.

- Runtime complete:
  - playbook `prep.yml`, `tasks/delete.yml`, and `tasks/apply.yml` exist and match the intended var model
- Validation complete:
  - `tools/validate-vars` understands the tree, required fields, references, and duplicate semantics
- Drift/import complete:
  - `tools/drift-check` and `tools/import-from-bigip` use the correct BIG-IP endpoints, correct repo var keys, and enough field extraction to reconstruct the repo model without misleading output
- Documentation/example complete:
  - `README.md`, domain docs, roadmap state, and example var files all describe the actual runtime field model and linkage behavior

Checked-off roadmap items should only be treated as fully complete when all four layers above are true, unless the roadmap explicitly says the item is runtime-only.

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
├── playbooks/
│   ├── network.yml
│   ├── ltm.yml
│   ├── gtm.yml
│   ├── system.yml
│   ├── ha.yml
│   ├── tls.yml
│   ├── network/
│   │   ├── prep.yml
│   │   └── tasks/
│   │       ├── manage.yml
│   │       ├── delete.yml
│   │       └── apply.yml
│   ├── system/
│   │   ├── prep.yml
│   │   └── tasks/
│   │       ├── manage.yml
│   │       ├── delete.yml
│   │       └── apply.yml
│   ├── ha/
│   │   ├── prep.yml
│   │   └── tasks/
│   │       ├── manage.yml
│   │       ├── delete.yml
│   │       └── apply.yml
│   ├── tls/
│   │   ├── prep.yml
│   │   └── tasks/
│   │       ├── manage.yml
│   │       ├── delete.yml
│   │       └── apply.yml
│   ├── ltm/
│   │   ├── prep.yml
│   │   └── tasks/
│   │       ├── manage.yml
│   │       ├── delete.yml
│   │       └── apply.yml
│   └── gtm/
│       ├── prep.yml
│       └── tasks/
│           ├── manage.yml
│           ├── delete.yml
│           └── apply.yml
├── tools/
├── docs/
└── vars/
    ├── common.yml
    ├── network/
    │   ├── vlans/
    │   ├── self_ips/
    │   ├── routes/
    │   ├── route_domains/
    │   ├── trunks/
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

### Documentation and Examples

- update `docs/` alongside every code change so linkages and reference strings are explained where operators read them
- update `README.md` when a feature changes the high-level playbook list, validation commands, or quick links table
- update example var files under `vars/` when a feature adds or changes an authoring pattern
- do not add documentation to `README.md` that belongs in `docs/`; the README stays minimal with a table of doc links
- if an empty directory must exist intentionally, include a `.gitkeep`

### Roadmap Maintenance

- update `ROADMAP.md` Current State section when new features are implemented
- update the backlog item checklist (`Recommended Near-Term Backlog`) when work is completed
- update milestone checklists in `Issue-Sized Execution Plan` when work is completed
- update the Implementation Audit section when new objects or playbooks are added
- update the Not Implemented Yet list when gaps are filled
- if a playbook is intentionally kept monolithic instead of split, record the reason here

### Playbook Structure

- keep canonical playbooks under `playbooks/` and keep root-level wrapper playbooks working during transitions
- default to the split canonical playbook model: keep discovery/default aggregation in `playbooks/<domain>/prep.yml`, keep `tasks/manage.yml` as the ordering wrapper, and separate destructive tasks into `tasks/delete.yml` from present-state tasks in `tasks/apply.yml`

### Validation and Commits

- validate after each major change before moving to the next implementation step
- at the end of every implementation prompt, after changes are made and validated, print a suggested commit message

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
7. [x] Add NAT and trunk support to complete network expansion
8. [x] Add hybrid readability shortcuts:
   - [x] `pool_defaults`
   - [x] `member_defaults`
   - [x] `monitor_sets`
   - [x] subdirectory maintenance defaults via `settings.yml` object defaults
9. [x] Add optional LTM virtual resolution
10. [x] Define TLS secret handling approach
 11. [x] Complete missing documentation
 12. [x] Add LTM persistence, iRules, data groups, and policies
 13. [x] Add virtual server VLAN filtering, metadata, and log profiles
 14. [x] Add GTM topology regions and topology records
 15. [x] Add WAF/ASM policies and server technologies to security playbook
 16. [x] Add APM ACLs and tmsh-driven resource objects to security playbook
 17. [x] Add APM auth servers, SSO configs, and policy nodes (tmsh-driven)
18. [x] Add APM access profiles, per-session policies, and macros
19. [ ] Audit checked-off roadmap items against runtime, validation, drift/import tooling, docs, and examples
20. [ ] Correct drift/import endpoint and var-key mappings for newly added object families
21. [ ] Align runtime, validator, docs, and example vars where field models drifted apart
22. [ ] Complete exhaustive drift/import parity for every newest object tree
23. [ ] Deepen drift detection to compare meaningful fields for newly added object families
24. [ ] Add day-0 BIG-IP onboarding for licensing and initial management bootstrap
25. [ ] Document initial setup from first boot through handoff to Git-managed operation

## Extended Backlog

These are valuable enhancements identified during implementation:

26. [ ] Deeper HA lifecycle management (connection mirroring, failover metadata, automated failover testing)
27. [ ] UCS backup/export workflow for configuration snapshots
28. [ ] Certificate rotation automation with renewal detection
29. [ ] Auth provider integration for system users (LDAP/AD/RADIUS for BIG-IP admin auth)
30. [ ] Login banner management for system compliance

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

### Milestone 7: LTM Expansion

- [x] Add `vars/ltm/persistence` for first-class persistence profiles
- [x] Add `vars/ltm/irules` for first-class iRules
- [x] Add `vars/ltm/data_groups` for first-class data groups
- [x] Add `vars/ltm/policies` for first-class LTM policies
- [x] Update `ltm.yml` apply/delete tasks for new object types
- [x] Add virtual server fields: `default_persistence_profile`, `fallback_persistence_profile`, `irules`, `policies`
- [x] Add virtual server fields: `vlans`, `vlans_enabled`, `metadata`, `log_profiles`
- [x] Add deletion trees for all new object types

### Milestone 8: GTM Topology

- [x] Add `vars/gtm/regions` for first-class topology regions
- [x] Add `vars/gtm/topology` for first-class topology records
- [x] Update `gtm.yml` apply/delete tasks for regions and topology records
- [x] Add deletion trees for topology regions and records
- [x] Add cross-validation: topology records reference declared regions

### Milestone 9: AFM Security

- [x] Add `vars/security/afm/address_lists` for AFM address lists
- [x] Add `vars/security/afm/port_lists` for AFM port lists
- [x] Add `vars/security/afm/rules` for AFM firewall rules
- [x] Add `vars/security/afm/policies` for AFM firewall policies
- [x] Add `security.yml` playbook with split task structure
- [x] Add deletion trees for all AFM object types
- [x] Add validation for address/port lists, rules, and policies
- [x] Add cross-validation: policy rules reference declared rules
- [x] Add cross-validation: rule endpoints reference declared address lists

### Milestone 10: Drift Detection and Import

- [x] Create `tools/drift-check` for live-vs-Git comparison
- [x] Create `tools/import-from-bigip` for brownfield import
- [x] Support LTM, GTM, network, AFM, WAF, and TLS object types
- [x] Provide JSON output for CI integration
- [x] Document drift and import workflows
- [ ] Add exhaustive drift/import parity for all object trees (network route_domains, trunks, snats, nats; gtm topology; tls ca_bundles, client_ssl_profiles, server_ssl_profiles; waf server_technologies; apm policy_nodes, sso_configs full coverage)

### Milestone 11: Promotion and Rollback

- [x] Document environment promotion flow (dev → test → prod)
- [x] Document hotfix flow (main → test → dev back-propagation)
- [x] Document rollback strategies: git revert, playbook re-apply, UCS restore
- [x] Document rollback checklist for production incidents
- [x] Document drift detection integration at promotion gates
- [x] Document AWX job template pattern per environment

### Milestone 12: WAF/ASM Policies

- [x] Add `vars/security/waf/policies` for WAF/ASM policies
- [x] Add `vars/security/waf/server_technologies` for server technologies
- [x] Extend `security.yml` playbook with WAF apply/delete tasks
- [x] Add deletion trees for WAF object types
- [x] Add validation for WAF policies and server technologies
- [x] Add cross-validation: server technologies reference declared policies
- [x] Add WAF endpoint to drift detection (`asm/policies`)
- [x] Add WAF import spec for brownfield import
- [x] Add `docs/waf.md` with object reference and authoring patterns

### Milestone 13: APM Access Policy Manager

- [x] Add `vars/security/apm/acls` for APM ACLs (L4/L7)
- [x] Add `vars/security/apm/resources` for tmsh-driven APM resources
- [x] Extend `security.yml` playbook with APM apply/delete tasks
- [x] Add deletion trees for all APM object types
- [x] Add validation for APM ACLs and resource objects
- [x] Add APM endpoints to drift detection (`access/policy/acl`, `apm/resource`)
- [x] Add APM import specs for brownfield import
- [x] Add `docs/apm.md` with object reference and authoring patterns
- [x] Update `docs/security.md` to include APM coverage

### Milestone 14: APM Authentication and SSO

- [x] Add `vars/security/apm/auth_servers` for all authentication types (AD, LDAP, RADIUS, TACACS, RSA, cert, localdb, SAML, OAuth)
- [x] Add `vars/security/apm/sso_configs` for all SSO methods (Kerberos, form-based, HTTP Basic, NTLM, SAML, OAuth, Citrix, domain-join)
- [x] Add `vars/security/apm/resources` for network access, webtops, remote desktop, portal access
- [x] Add `vars/security/apm/policy_nodes` for VPE flow nodes within access policies
- [x] Add `vars/security/apm/access_profiles` for access profile definitions
- [x] Add `vars/security/apm/per_session_policies` for per-session policy definitions
- [x] Add `vars/security/apm/macros` for reusable VPE macro definitions
- [x] Extend `security.yml` playbook with tmsh-driven APM apply/delete tasks
- [x] Add deletion trees for all APM object types
- [x] Add validation for all APM types with cross-reference checking
- [x] Add APM endpoints to drift detection (`access/profile`, `access/per-session-policy`, `access/macro`)
- [x] Add APM import specs for brownfield import
- [x] Add `docs/authentication.md` with comprehensive auth/SSO type reference
- [x] Update `docs/apm.md` with new object types and examples

### Milestone 15: Extended Backlog (Optional Enhancements)

- [ ] Add connection mirroring and failover metadata management to `ha.yml`
- [ ] Add automated failover testing workflows
- [ ] Add UCS backup/export workflow to `system.yml` or dedicated playbook
- [ ] Add certificate rotation automation with expiry detection
- [ ] Add auth provider integration for BIG-IP admin users (LDAP/AD/RADIUS)
- [ ] Add login banner management to `system.yml`

### Milestone 16: Coverage Stabilization

- [ ] Treat correction of previously checked-off but partially implemented items as higher priority than adding new feature coverage
- [ ] Audit each checked-off roadmap item against runtime, validation, drift/import tooling, docs, and example vars
- [ ] Correct network helper-tool mappings for trunks and SNAT pools
- [ ] Correct newer helper-tool mappings for WAF server technologies and APM policy nodes
- [ ] Align runtime, validator, docs, and examples for any feature where the declared field model drifted
- [ ] Decide whether `system` and `ha` should gain drift/import support now or be explicitly documented as runtime-only for the current phase
- [ ] Align APM access-profile validation with the current runtime field model
- [ ] Reconcile the roadmap, README, and docs whenever a checked-off item is found to be only partially complete

## Network Expansion Status

The repo now covers route domains, static routes, SNAT translations, SNAT pools, trunks, and NATs.

Implementation note:

- NAT object management uses a validated `tmsh` command workflow because the installed `f5networks.f5_modules` collection does not provide a first-class NAT module.

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
