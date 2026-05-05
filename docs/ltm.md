# LTM Playbook

## Overview

`playbooks/ltm.yml` manages canonical BIG-IP Local Traffic Manager objects:

- monitors
- non-TLS profiles
- data groups
- iRules
- persistence profiles
- policies
- nodes
- pools
- virtual servers

This domain also supports higher-level authoring through the dedicated intent layer under `vars/ltm/intents/`, but runtime apply/delete remains canonical-object driven.

## Playbook Structure

```text
playbooks/ltm.yml
playbooks/ltm/
├── prep.yml
├── prep/load-vars.yml
├── prep/build-runtime.yml
├── prep/intents/inline/
│   ├── load-virtual-server-intents.yml
│   └── build-virtual-server-intents.yml
└── tasks/
    ├── manage.yml
    ├── audit.yml
    ├── delete.yml
    └── apply.yml
```

`prep.yml` loads canonical trees, compiles supported intents, and publishes the runtime collections that `audit`, `delete`, and `apply` consume.

## Var Tree

```text
vars/ltm/
├── monitors/
├── profiles/
├── data_groups/
├── irules/
├── persistence/
├── policies/
├── nodes/
├── pools/
├── virtual_servers/
├── intents/
│   └── inline/
└── deletions/
    ├── monitors/
    ├── profiles/
    ├── data_groups/
    ├── irules/
    ├── persistence/
    ├── policies/
    ├── nodes/
    ├── pools/
    ├── virtual_servers/
    └── intents/
        └── inline/
```

## Canonical Object Types

| Type | Location | Purpose |
|---|---|---|
| `ltm_monitors` | `vars/ltm/monitors/` | health monitors |
| `ltm_profiles` | `vars/ltm/profiles/` | reusable non-TLS LTM profiles |
| `ltm_data_groups` | `vars/ltm/data_groups/` | string/IP/value lookup groups |
| `ltm_irules` | `vars/ltm/irules/` | traffic logic |
| `ltm_persistence_profiles` | `vars/ltm/persistence/` | persistence behavior |
| `ltm_policies` | `vars/ltm/policies/` | LTM policy objects |
| `ltm_nodes` | `vars/ltm/nodes/` | backend node identities |
| `ltm_pools` | `vars/ltm/pools/` | backend pools and members |
| `ltm_virtual_servers` | `vars/ltm/virtual_servers/` | front-end virtual servers |

## Cross-File Linkages

- `ltm_pools[*].members[*].name` points at `vars/ltm/nodes/*.yml`
- `ltm_pools[*].monitors` can use aliases from sibling `settings.yml` or fully qualified BIG-IP monitor names
- `ltm_virtual_servers[*].pool` points at `vars/ltm/pools/*.yml`
- `ltm_virtual_servers[*].profiles` can point at `vars/ltm/profiles/*.yml` or built-in BIG-IP profiles such as `/Common/tcp`
- `ltm_virtual_servers[*].irules` points at `vars/ltm/irules/*.yml`
- `ltm_virtual_servers[*].policies` points at `vars/ltm/policies/*.yml`
- `ltm_virtual_servers[*].default_persistence_profile` and `fallback_persistence_profile` point at `vars/ltm/persistence/*.yml`

## Authoring Patterns

### Canonical first-class objects

Use the canonical trees when objects are shared, reused, or owned separately.

Example path:

- virtual servers in `vars/ltm/virtual_servers/`
- pools in `vars/ltm/pools/`
- nodes in `vars/ltm/nodes/`

### Intent compiler layer

Use `vars/ltm/intents/inline/` for concise service-oriented authoring that should compile into canonical virtual servers and pools before runtime tasks execute.

See:

- [intents/ltm-inline-virtual-server-intents.md](intents/ltm-inline-virtual-server-intents.md)
- [example-models.md](example-models.md)

## Dependency Order

Apply order:

1. monitors
2. profiles
3. data groups
4. iRules
5. persistence profiles
6. policies
7. nodes
8. pools
9. virtual servers

Delete order is the reverse.

## Validation

`tools/validate-vars.py` validates:

- schema and required fields
- duplicate names
- pool-to-node references
- virtual-server references to pools, profiles, policies, iRules, and persistence profiles
- intent ownership and collision rules where the inline intent layer is used

## Drift And Import

LTM canonical objects are covered by `tools/drift-check.py` and `tools/import-from-bigip.py`.

Current helper-tool boundary:

- helper-tool coverage for the main LTM object families is generally `runtime+validation+helper-tools`
- fidelity is usually `basic field drift`, not full semantic round-trip parity for every advanced live attribute
- intent files are not first-class drift/import targets; the tools operate on the compiled canonical object families

See [drift-import.md](drift-import.md) for exact object coverage.

## Supplemental Docs

- [ltm-advanced.md](ltm-advanced.md)
- [intents/ltm-inline-virtual-server-intents.md](intents/ltm-inline-virtual-server-intents.md)
- [example-models.md](example-models.md)
