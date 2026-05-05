# BIG-IP Enterprise GitOps Roadmap
TASK [Create manual GTM virtual servers for pool members] **********************
fatal: [lab-f5]: FAILED! => {"msg": "The task includes an option with an undefined variable. The error was: 'dict object' has no attribute 'address'. 'dict object' has no attribute 'address'\n\nThe error appears to be in '/runner/project/playbooks/gtm/tasks/apply.yml': line 209, column 3, but may\nbe elsewhere in the file depending on the exact syntax problem.\n\nThe offending line appears to be:\n\n# object is explicitly materialized before its parent pool is created.\n- name: Create manual GTM virtual servers for pool members\n  ^ here\n"}

python3 tools/validate-vars.py
ERROR: vars/ltm/intents/inline/k8s-clusters/dc1-rsc-cib-1.yml: LTM inline compiled virtual server `vs_dc1_rsc_cib_1_kubeapi_6443` references undefined pool `/K8s/pool_dc1_rsc_cib_1_kubeapi_6443`
ERROR: vars/ltm/intents/inline/k8s-clusters/dc1-rsc-cib-1.yml: LTM inline compiled virtual server `vs_dc1_rsc_cib_1_registration_9345` references undefined pool `/K8s/pool_dc1_rsc_cib_1_registration_9345`
ERROR: vars/ltm/intents/inline/k8s-clusters/dc1-rsc-cib-1.yml: LTM inline compiled virtual server `vs_dc1_rsc_cib_1_traefik_443` references undefined pool `/K8s/pool_dc1_rsc_cib_1_traefik_443`
ERROR: vars/gtm/pools/k8s-pools/dcx-cib-1.yml: GTM pool `pool_dcx-rsc-cib-1` member 0 cannot resolve repo-known LTM virtual `/Common/dc1-rsc-cib-1-traefik`
ERROR: vars/gtm/pools/k8s-pools/dcx-cib-1.yml: GTM member 0 must define `address`
ERROR: vars/gtm/pools/k8s-pools/dcx-cib-1.yml: GTM member 0 must define `port`
Validation failed with 6 error(s).
make: *** [Makefile:11: validate-vars] Error 1


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
