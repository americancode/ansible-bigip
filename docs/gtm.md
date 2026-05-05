# GTM Playbook

## Overview

`playbooks/gtm.yml` manages canonical BIG-IP GTM/DNS objects:

- monitors
- datacenters
- servers
- pools
- Wide IPs
- regions
- topology records

This domain also supports application-oriented GTM intents under `vars/gtm/intents/`, but runtime apply/delete still operates on canonical GTM objects.

## Playbook Structure

```text
playbooks/gtm.yml
playbooks/gtm/
├── prep.yml
├── prep/load-gtm-vars.yml
├── prep/load-repo-ltm-virtuals.yml
├── prep/build-gtm-runtime.yml
├── prep/build-repo-ltm-virtuals.yml
├── prep/intents/inline/
│   ├── load-repo-ltm-inline-virtual-server-intents.yml
│   └── build-application-intents.yml
└── tasks/
    ├── manage.yml
    ├── audit.yml
    ├── delete.yml
    └── apply.yml
```

`prep.yml` loads canonical GTM trees, imports the repo-known LTM virtual-server context GTM needs for member resolution, compiles supported intents, and publishes the final runtime collections.

## Var Tree

```text
vars/gtm/
├── monitors/
├── datacenters/
├── servers/
├── pools/
├── intents/
│   └── applications/
├── regions/
├── topology/
└── deletions/
    ├── monitors/
    ├── datacenters/
    ├── servers/
    ├── pools/
    ├── intents/
    │   └── applications/
    ├── regions/
    └── topology/
```

## Canonical Object Types

| Type | Location | Purpose |
|---|---|---|
| `gtm_monitors` | `vars/gtm/monitors/` | GTM monitor objects |
| `gtm_datacenters` | `vars/gtm/datacenters/` | datacenter identities |
| `gtm_servers` | `vars/gtm/servers/` | GTM server objects |
| `gtm_pools` | `vars/gtm/pools/` | DNS answer pools |
| `gtm_application_intents` | `vars/gtm/intents/applications/` | Application-intent authoring that compiles into canonical Wide IPs |
| `gtm_wide_ips` | canonical trees after compilation | Wide IP runtime definitions |
| `gtm_topology_regions` | `vars/gtm/regions/` | region definitions |
| `gtm_topology_records` | `vars/gtm/topology/` | topology decision rules |

## Cross-File Linkages

- `gtm_servers[*].datacenter` points at `vars/gtm/datacenters/*.yml`
- `gtm_pools[*].members[*].server` points at `vars/gtm/servers/*.yml`
- `gtm_pools[*].members[*].virtual_server` points at repo-known LTM virtual servers in `vars/ltm/virtual_servers/*.yml`
- `gtm_application_intents[*].pools[*].pool_ref` points at `vars/gtm/pools/*.yml` when `pool_mode: reference`
- monitor aliases expand through sibling `settings.yml` files in the GTM trees

When a GTM pool member omits `address` and `port`, the playbook can resolve them from the referenced repo-known LTM virtual server.

## Authoring Patterns

### Canonical first-class GTM objects

Use canonical datacenters, servers, and pools when they are shared or need independent lifecycle ownership.

### Application intent layer

Use `vars/gtm/intents/applications/` when one application-oriented file should compile into a Wide IP and, when owned inline, the related GTM pools, servers, or datacenters.

See:

- [intents/gtm-application-intents.md](intents/gtm-application-intents.md)
- [example-models.md](example-models.md)

## Dependency Order

Apply order:

1. monitors
2. datacenters
3. servers
4. pools
5. Wide IPs
6. regions
7. topology records

Delete order is the reverse.

## Validation

`tools/validate-vars.py` validates:

- schema and required fields
- duplicate names
- datacenter, server, and pool references
- GTM member linkage to repo-known LTM virtual servers where used
- intent ownership and collision rules for compiled application-intent convenience models

## Drift And Import

GTM canonical object families are covered by `tools/drift-check.py` and `tools/import-from-bigip.py`.

Current helper-tool boundary:

- helper-tool coverage is generally `runtime+validation+helper-tools`
- fidelity for several GTM families is `basic field drift`
- topology and newer nested fields should still be treated review-first rather than as a perfect round-trip model
- intent files are not first-class drift/import targets; helper tools operate on canonical GTM objects

See [drift-import.md](drift-import.md) for exact supported types.

## Supplemental Docs

- [gtm-advanced.md](gtm-advanced.md)
- [intents/gtm-application-intents.md](intents/gtm-application-intents.md)
- [example-models.md](example-models.md)
