# Hybrid Authoring Model

The current preferred authoring model is hybrid: embed app-local objects when a single file should describe one service clearly, and promote shared or reused objects into first-class trees when multiple apps depend on them.

This document describes the current runtime-facing authoring model. The roadmap direction is to evolve the embedded shortcut paths into a dedicated intent/compiler layer documented in [intent-authoring.md](intent-authoring.md), so runtime playbooks do not keep accumulating shortcut-specific logic.

## Embedded Model (Concise)

Use when one file should explain the whole service.

This model is currently supported, but it should be treated as transitional for LTM and GTM convenience cases that may later move into first-class intent trees:

- LTM virtual servers can embed their own pool definitions
- GTM Wide IPs can embed their own GTM pools

Example walkthroughs live in [example-models.md](example-models.md):

- Concise LTM: `vars/ltm/virtual_servers/rke2-east/platform-cluster.yml`
- Concise GTM: `vars/gtm/wide_ips/global-platform/platform.yml`

These concise paths now compile into canonical pools and pool references during `prep.yml`, so runtime `apply.yml` and `delete.yml` operate on normalized first-class objects rather than mixed inline shortcut shapes.

## First-Class Model (Verbose)

Use when objects are reused, owned by another team, or need clearer separation:

- shared nodes, pools, datacenters, and TLS objects live in first-class trees
- shared non-TLS LTM profiles live in `vars/ltm/profiles/...` and are attached by name from virtual servers
- GTM pool members can resolve `address` and `port` from repo-known LTM virtual servers when `virtual_server` names already match

Example walkthroughs live in [example-models.md](example-models.md):

- Verbose LTM: `vars/ltm/virtual_servers/vm-apps/business-apps.yml` + `vars/ltm/pools/vm-applications.yml`
- Verbose GTM: `vars/gtm/wide_ips/vm-applications.yml` + `vars/gtm/pools/vm-applications.yml`

## Linkage Patterns

Cross-file references work by name:

- `ltm_virtual_servers[*].pool: "pool_inventory_east_8443"` points at an object in `vars/ltm/pools/`
- `ltm_pools[*].members[*].name: "inventory-east-1"` points at a node in `vars/ltm/nodes/`
- `gtm_wide_ips[*].pools[*].name: "pool_inventory_global"` points at `vars/gtm/pools/`
- `gtm_pools[*].members[*].virtual_server: "vs_inventory_east_443"` points at `vars/ltm/virtual_servers/`

Monitor aliases (e.g., `standard_https`, `platform_https`) expand through sibling `settings.yml` files. Out-of-the-box BIG-IP references use fully-qualified names such as `/Common/https`.

As the repo grows, do not assume every new convenience case should be added here as more embedded runtime behavior. New "simple mode" patterns should prefer the intent/compiler design in [intent-authoring.md](intent-authoring.md).
