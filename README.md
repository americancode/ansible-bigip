# ansible-bigip

Declarative BIG-IP playbooks organized for GitOps-style management.

AWX is the primary control plane for normal operations.

Start with [docs/index.md](docs/index.md) when you need to know where to go.

For the normal AWX-first operator path, follow:
[docs/01-awx-operating-model-and-handoff.md](docs/01-awx-operating-model-and-handoff.md),
[docs/awx-setup.md](docs/awx-setup.md),
[docs/03-awx-inventory-and-targeting.md](docs/03-awx-inventory-and-targeting.md),
[docs/04-awx-job-execution.md](docs/04-awx-job-execution.md), and
[docs/05-ha-execution-model.md](docs/05-ha-execution-model.md).

Use [docs/cli-bootstrap-and-recovery.md](docs/cli-bootstrap-and-recovery.md) only for bootstrap fallback or break-glass recovery when AWX cannot be the first control plane.

## Current Coverage

The repo already manages the main BIG-IP runtime domains through Git:

- day-0 bootstrap for licensing and first management reachability
- network, system, HA, LTM, GTM, TLS, and security playbooks
- split var trees with per-directory `settings.yml` and explicit deletion trees
- dedicated intent/compiler authoring for opinionated patterns such as LTM inline virtual-server intents, organized under category-first trees like `vars/ltm/intents/inline/...` with layered `settings.yml` support
- Python-backed prep helpers split by concern under `filter_plugins/bigip_filters/`, with `filter_plugins/bigip_var_filters.py` kept as the thin Ansible entrypoint
- shared prep snippets under `playbooks/shared/prep/` for fragment discovery, settings-aware aggregation, and present/delete classification across the standard domains
- recursive nested var-tree discovery and hierarchical multi-level `settings.yml` inheritance across canonical playbooks, including specialized `ltm` and `gtm` loaders
- offline validation, drift detection, and brownfield import tooling

Current lifecycle boundaries:

- `bootstrap` is intentionally `runtime+validation` only
- `system` and `ha` are intentionally `runtime+validation` for the current phase
- the broader service domains are generally `runtime+validation+helper-tools`, usually at `basic field drift` fidelity for helper-tool comparisons

## Quick Links

| Topic | Doc |
|---|---|
| Where to go | [docs/index.md](docs/index.md) |
| AWX setup runbook | [docs/awx-setup.md](docs/awx-setup.md) |
| Extending the repo | [docs/extending-the-repo.md](docs/extending-the-repo.md) |
| Playbook layout | [docs/playbook-structure.md](docs/playbook-structure.md) |
| Variables and precedence | [docs/var-layout.md](docs/var-layout.md) |
| Hybrid authoring | [docs/hybrid-authoring.md](docs/hybrid-authoring.md) |
| Build new intents | [docs/intents/how-to-build-intents.md](docs/intents/how-to-build-intents.md) |
| Intent class: LTM inline virtual servers | [docs/intents/ltm-inline-virtual-server-intents.md](docs/intents/ltm-inline-virtual-server-intents.md) |
| Intent class: GTM Wide IPs | [docs/intents/gtm-wide-ip-intents.md](docs/intents/gtm-wide-ip-intents.md) |
| Deletion workflows | [docs/deletion-workflows.md](docs/deletion-workflows.md) |
| AWX inventory and targeting | [docs/03-awx-inventory-and-targeting.md](docs/03-awx-inventory-and-targeting.md) |
| AWX job execution | [docs/04-awx-job-execution.md](docs/04-awx-job-execution.md) |
| Validation | [docs/validation.md](docs/validation.md) |
| 01 AWX operating model | [docs/01-awx-operating-model-and-handoff.md](docs/01-awx-operating-model-and-handoff.md) |
| 02 Bootstrap playbook | [docs/02-bootstrap-playbook.md](docs/02-bootstrap-playbook.md) |
| TLS secrets | [docs/tls-secrets.md](docs/tls-secrets.md) |
| Network objects | [docs/network-objects.md](docs/network-objects.md) |
| System management | [docs/system-management.md](docs/system-management.md) |
| HA lifecycle | [docs/ha.md](docs/ha.md) |
| LTM playbook | [docs/ltm.md](docs/ltm.md) |
| LTM advanced fields | [docs/ltm-advanced.md](docs/ltm-advanced.md) |
| GTM playbook | [docs/gtm.md](docs/gtm.md) |
| GTM advanced fields | [docs/gtm-advanced.md](docs/gtm-advanced.md) |
| TLS playbook | [docs/tls.md](docs/tls.md) |
| AFM security | [docs/security.md](docs/security.md) |
| WAF/ASM | [docs/waf.md](docs/waf.md) |
| APM access | [docs/apm.md](docs/apm.md) |
| Authentication | [docs/authentication.md](docs/authentication.md) |
| Kerberos SSO | [docs/kerberos-sso.md](docs/kerberos-sso.md) |
| 05 HA execution model | [docs/05-ha-execution-model.md](docs/05-ha-execution-model.md) |
| Drift and import | [docs/drift-import.md](docs/drift-import.md) |
| Promotion workflows | [docs/promotion-workflows.md](docs/promotion-workflows.md) |
| Rollback patterns | [docs/rollback-patterns.md](docs/rollback-patterns.md) |
| CLI bootstrap and recovery | [docs/cli-bootstrap-and-recovery.md](docs/cli-bootstrap-and-recovery.md) |
| Example models | [docs/example-models.md](docs/example-models.md) |
| Roadmap | [ROADMAP.md](ROADMAP.md) |

## Playbooks

Canonical playbooks live under `playbooks/`. Root-level `*.yml` files are compatibility wrappers.

| Playbook | Domain | Primary Doc |
|---|---|---|
| `playbooks/network.yml` | VLANs, trunks, route domains, self IPs, routes, SNATs, NATs | [docs/network-objects.md](docs/network-objects.md) |
| `playbooks/bootstrap.yml` | device licensing and initial management IP/default-route bootstrap | [docs/02-bootstrap-playbook.md](docs/02-bootstrap-playbook.md) |
| `playbooks/system.yml` | hostname, DNS, NTP, provisioning, administrative partitions, users, management-plane admin auth, login banners | [docs/system-management.md](docs/system-management.md) |
| `playbooks/ha.yml` | device connectivity, device trust, device groups, HA groups, traffic groups, config sync | [docs/ha.md](docs/ha.md) |
| `playbooks/ltm.yml` | monitors, profiles, data groups, iRules, persistence, nodes, pools, virtual servers | [docs/ltm.md](docs/ltm.md) |
| `playbooks/gtm.yml` | monitors, datacenters, servers, pools, Wide IPs, regions, topology | [docs/gtm.md](docs/gtm.md) |
| `playbooks/tls.yml` | keys, certificates, CA bundles, client/server SSL profiles | [docs/tls.md](docs/tls.md) |
| `playbooks/security.yml` | AFM address lists, port lists, firewall rules, policies; WAF policies, server technologies; APM ACLs, auth servers, SSO configs, resources, policy nodes, access profiles, per-session policies, macros | [docs/security.md](docs/security.md) |

## Current Priorities

The main remaining roadmap items are:

- deciding whether `system` and `ha` should gain full drift/import support
- lower-priority lifecycle work such as UCS backup/export and certificate rotation automation

## Validation

```sh
make validate
```

See [docs/validation.md](docs/validation.md) for details.

For a no-change execution preview, run a canonical playbook with `-e audit_mode=true`.
