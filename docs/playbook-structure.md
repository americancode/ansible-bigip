# Playbook Structure

Canonical playbooks live under `playbooks/`. Root-level `*.yml` files are compatibility wrappers that import the canonical playbooks.

## Playbook List

- `playbooks/network.yml`: VLANs, trunks, route domains, self IPs, static routes, SNAT translations, SNAT pools, and NATs
- `playbooks/bootstrap.yml`: BIG-IP day-0 licensing and first management reachability
- `playbooks/system.yml`: base system settings like hostname, DNS, NTP, provisioning, users, management-plane admin auth providers, and login banners
- `playbooks/ha.yml`: device connectivity, device trust, device groups, HA groups, traffic groups, config sync actions
- `playbooks/ltm.yml`: LTM monitors, non-TLS profiles, nodes, pools, virtual servers
- `playbooks/gtm.yml`: GTM monitors, datacenters, servers, pools, Wide IPs, regions, and topology records
- `playbooks/tls.yml`: SSL keys, certificates, CA bundles, client SSL profiles, server SSL profiles
- `playbooks/security.yml`: AFM address lists, port lists, firewall rules, firewall policies; WAF policies and server technologies; APM ACLs, auth servers, SSO configs, resources, policy nodes, access profiles, per-session policies, and macros

## Split Layout

Canonical playbooks use a consistent split so the entrypoint stays small and the discovery and execution logic remain easy to follow:

- `playbooks/<domain>.yml` is the canonical entrypoint
- `playbooks/<domain>/prep.yml` is the documented orchestrator for prep flow and should say which major facts or canonical sets it produces
- when a domain has larger compiler or normalization flows, `prep.yml` may import focused prep snippets such as `playbooks/<domain>/prep/*.yml`
- repeated fragment discovery, settings-aware aggregation, and present/delete classification should be centralized under `playbooks/shared/prep/*.yml` and backed by shared filters in `filter_plugins/bigip_filters/` instead of being rewritten by hand in each domain
- common split points are `load-*.yml`, `build-*.yml`, and `compile-*.yml`
- `playbooks/<domain>/tasks/manage.yml` orchestrates task execution order
- `playbooks/<domain>/tasks/delete.yml` contains destructive tasks
- `playbooks/<domain>/tasks/apply.yml` contains present-state create/update tasks

This pattern is the default for `bootstrap`, `network`, `system`, `ha`, `tls`, `ltm`, `gtm`, and `security`. `bootstrap` is the explicit exception where `tasks/delete.yml` is intentionally empty because the domain is apply-only. If a future playbook stays small enough that splitting it adds no value, document that choice in [ROADMAP.md](../ROADMAP.md) before keeping it monolithic.

When a domain grows a real intent layer, keep those prep snippets under `playbooks/<domain>/prep/intents/<category>/...` instead of leaving them mixed into the prep root.

When Python-backed prep helpers grow beyond a small handful of filters, keep `filter_plugins/bigip_var_filters.py` as the thin Ansible entrypoint and split the implementation by concern under `filter_plugins/bigip_filters/`.

The current preferred split is:

- domain `prep.yml` as the readable orchestrator
- `playbooks/shared/prep/load-fragment-tree.yml` for recursive var-tree discovery and settings-aware aggregation
- `playbooks/shared/prep/classify-operations.yml` for publishing `*_present` and `*_delete` collections from the canonical object lists
- domain-specific `prep/*.yml` snippets only where the prep flow is genuinely specialized, such as intent compilation or lookup-building

Nested directory trees are part of the supported model. Prep loaders should discover fragment files recursively and apply layered `settings.yml` defaults from the relevant subtree root down through intermediate directories before merging the object-level values.

## Path Handling

Path handling inside canonical playbooks is anchored from `playbook_dir`, so moving playbooks under `playbooks/` does not break references to `vars/`.

## Connection Model

The canonical playbooks target AWX inventory hosts with `connection: local`, so inventory host vars such as `f5_host` are available even though the BIG-IP API calls are made from the controller.

For details on targeting and HA operation, see [04-awx-operation.md](04-awx-operation.md).
