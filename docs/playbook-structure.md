# Playbook Structure

Canonical playbooks live under `playbooks/`. Root-level `*.yml` files are compatibility wrappers that import the canonical playbooks.

## Playbook List

- `playbooks/network.yml`: VLANs, trunks, route domains, self IPs, static routes, SNAT translations, SNAT pools, and NATs
- `playbooks/bootstrap.yml`: BIG-IP day-0 licensing and first management reachability
- `playbooks/system.yml`: base system settings like hostname, DNS, NTP, provisioning, users
- `playbooks/ha.yml`: device trust, device groups, traffic groups, config sync actions
- `playbooks/ltm.yml`: LTM monitors, non-TLS profiles, nodes, pools, virtual servers
- `playbooks/gtm.yml`: GTM monitors, datacenters, servers, pools, Wide IPs, regions, and topology records
- `playbooks/tls.yml`: SSL keys, certificates, CA bundles, client SSL profiles, server SSL profiles
- `playbooks/security.yml`: AFM address lists, port lists, firewall rules, firewall policies; WAF policies and server technologies; APM ACLs, auth servers, SSO configs, resources, policy nodes, access profiles, per-session policies, and macros

## Split Layout

Canonical playbooks use a consistent split so the entrypoint stays small and the discovery and execution logic remain easy to follow:

- `playbooks/<domain>.yml` is the canonical entrypoint
- `playbooks/<domain>/prep.yml` contains fragment discovery, `include_vars`, defaults loading, and aggregation logic
- `playbooks/<domain>/tasks/manage.yml` orchestrates task execution order
- `playbooks/<domain>/tasks/delete.yml` contains destructive tasks
- `playbooks/<domain>/tasks/apply.yml` contains present-state create/update tasks

This pattern is the default for `bootstrap`, `network`, `system`, `ha`, `tls`, `ltm`, `gtm`, and `security`. `bootstrap` is the explicit exception where `tasks/delete.yml` is intentionally empty because the domain is apply-only. If a future playbook stays small enough that splitting it adds no value, document that choice in [ROADMAP.md](../ROADMAP.md) before keeping it monolithic.

## Path Handling

Path handling inside canonical playbooks is anchored from `playbook_dir`, so moving playbooks under `playbooks/` does not break references to `vars/`.

## Connection Model

The canonical playbooks target AWX inventory hosts with `connection: local`, so inventory host vars such as `f5_host` are available even though the BIG-IP API calls are made from the controller.

For details on targeting and HA operation, see [awx-operation.md](awx-operation.md).
