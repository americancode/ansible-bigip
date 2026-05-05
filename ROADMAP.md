# BIG-IP Enterprise GitOps Roadmap

## To Do


8. Improve helper-tool fidelity where `basic field drift` is no longer sufficient.
   - Define the target fidelity per object family before coding:
     - keep `identity-only` only where the repo model intentionally manages name/existence only
     - keep `basic field drift` only where flat field comparison is operationally enough
     - promote to `model-aware` where nested runtime structures, references, child collections, or compiler output affect correctness
   - Audit current `basic field drift` families and classify which need promotion:
     - network: route domains, trunks, SNAT translations, SNAT pools, NATs
     - GTM: topology regions, topology records, pools, Wide IP intent output
     - TLS: CA bundles, client SSL profiles, server SSL profiles
     - APM: SSO configs, access profiles, policy nodes
     - LTM: pools, virtual servers, persistence profiles, policies, data groups where nested fields matter
   - Upgrade `tools/drift-check.py` fidelity for promoted families:
     - compare nested members, profiles, monitors, policies, rules, VLAN bindings, SNAT/persistence references, and profile references using normalized repo field names
     - normalize BIG-IP live values before comparison (fully-qualified names, partition defaults, booleans, integers, lists, generated defaults)
     - compare intent-compiled canonical objects, not raw intent files, for LTM inline virtual-server intents and GTM Wide IP intents
     - report field-level drift in a way that points to the repo field that should be changed
   - Upgrade `tools/import-from-bigip.py` fidelity for promoted families:
     - reconstruct nested repo shapes instead of flat identity stubs where runtime supports nested data
     - import child collections such as pool members, virtual profiles, virtual policies, topology members, APM policy node properties, SSL profile cert/key chains, and WAF/APM subcollections where supported
     - emit canonical object trees by default; only emit intent-shaped files when the importer can reconstruct that intent model accurately
     - preserve explicit limitations in generated comments when live state cannot round-trip cleanly
   - Add shared helper modules used by both drift and import:
     - reference normalization helpers for `/Partition/name`, default partition handling, and short-name comparison
     - list/set normalization helpers for monitors, profiles, VLANs, members, and policies
     - BIG-IP boolean/integer/default normalization helpers
     - object identity helpers for non-name identities such as GTM topology records and WAF server technologies
   - Add validation guardrails for helper-tool changes:
     - fixture-style unit tests for normalizers and transforms where practical
     - sample live REST payloads for at least one promoted family per domain
     - a no-device test path that verifies import/drift transform logic without requiring BIG-IP connectivity
   - Update docs after each fidelity promotion:
     - `docs/drift-import.md` must state the new fidelity level and remaining gaps
     - domain docs must stop claiming `basic field drift` once `model-aware` support exists
     - `ROADMAP.md` must keep any families that remain shallow listed explicitly

## Proposals

1. Split high-risk `system` functionality into narrower playbooks if AWX blast radius still feels too broad.
   - `system-auth`
   - `system-identity`
   - `system-provisioning`
   - `system-users`
   - `system-partitions`
   - `system-banner`

2. Split `ha` into narrower playbooks if shared vs device-local operations need harder execution boundaries.
   - `ha-device-local`
   - `ha-shared`

3. If selector-based targeting becomes too noisy or risky, prefer host-scoped var files or host-specific overlays instead of embedding `target_hosts` and `target_groups` on every object.

4. Add future dedicated domains only if they become operationally distinct enough to justify them.
   - backup or snapshot workflows
   - certificate lifecycle workflows
   - observability workflows
   - deeper WAF content lifecycle
   - brownfield onboarding or promotion workflows

5. Add an `observability` domain if logging, telemetry, and diagnostic workflows need first-class GitOps coverage.
   - system syslog and remote syslog
   - SNMP global settings, communities, and traps
   - log destinations and log publishers
   - SMTP settings used by alerting workflows
   - QKView generation/fetch patterns where operationally useful
   - TMM daemon log settings

6. Add a `device-access` domain if management-plane hardening needs to be managed separately from general `system`.
   - HTTPD settings
   - SSHD settings
   - password policy
   - remote users and remote roles
   - CLI aliases and CLI scripts
   - device certificates

7. Add a `dns-services` domain for non-GTM DNS service objects.
   - DNS cache resolvers
   - DNS resolvers
   - LTM DNS nameservers
   - DNS zones

8. Add a `software-lifecycle` domain if image, backup, and recovery workflows become part of normal automation.
   - software image management
   - software install/update workflows
   - UCS upload/install/remove/fetch
   - file copy workflows
   - device wait/readiness checks

9. Add an `ipsec` domain if BIG-IP terminates or participates in IPsec services.
   - IKE peers
   - IPsec policies
   - traffic selectors
   - tunnels

10. Add an `advanced-network` domain only if these lower-level network features become operationally important.
    - physical interfaces
    - management routes
    - network globals
    - CGNAT LSN pools
    - vCMP guests
    - additional tunnel lifecycle beyond IPsec

11. Add a `message-routing` domain if BIG-IP message routing is used.
    - message routing peers
    - message routing protocols
    - message routing routes
    - message routing routers
    - message routing transport configs

12. Add an `iapps-and-extensions` domain only if legacy iApps or LX packages are still part of the managed estate.
    - iApp templates
    - iApp services
    - LX packages

13. Expand existing domains for deeper module coverage where a new playbook would be unnecessary.
    - `ltm`: virtual addresses, explicit pool member lifecycle, more profile types, service policies, timer policies, analytics profiles
    - `security/afm`: DoS profiles/vectors, global rules, firewall schedules, AFM log profiles
    - `security/waf`: ASM advanced settings, ASM DoS application settings, signature sets, policy import/fetch
    - `security/apm`: network access resources and APM policy import/fetch
    - `system`: sys db, sys global, SMTP, HTTPD/SSHD, password policy, remote user/role if not split into `device-access`

14. Keep BIG-IQ module coverage out of scope unless this repo becomes responsible for BIG-IQ itself.
    - BIG-IQ applications
    - BIG-IQ device discovery/info
    - BIG-IQ registration key and utility license pools
    - BIG-IQ license assignment workflows
