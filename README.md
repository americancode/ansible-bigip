# ansible-bigip

Declarative BIG-IP playbooks organized for GitOps-style management.

For first boot through AWX handoff, follow the numbered operator path:
[docs/01-initial-setup-and-handoff.md](docs/01-initial-setup-and-handoff.md),
[docs/02-bootstrap-playbook.md](docs/02-bootstrap-playbook.md),
[docs/03-cli-bootstrap.md](docs/03-cli-bootstrap.md),
[docs/04-awx-operation.md](docs/04-awx-operation.md), and
[docs/05-awx-ha-bootstrap.md](docs/05-awx-ha-bootstrap.md).

## Current Coverage

The repo already manages the main BIG-IP runtime domains through Git:

- day-0 bootstrap for licensing and first management reachability
- network, system, HA, LTM, GTM, TLS, and security playbooks
- split var trees with per-directory `settings.yml` and explicit deletion trees
- dedicated intent/compiler authoring for opinionated patterns such as RKE2 LTM clusters, organized under category-first trees like `vars/ltm/intents/clusters/...` with layered `settings.yml` support
- Python-backed prep helpers split by concern under `filter_plugins/bigip_filters/`, with `filter_plugins/bigip_var_filters.py` kept as the thin Ansible entrypoint
- shared prep snippets under `playbooks/shared/prep/` for fragment discovery, settings-aware aggregation, and present/delete classification across the standard domains
- offline validation, drift detection, and brownfield import tooling

Current lifecycle boundaries:

- `bootstrap` is intentionally `runtime+validation` only
- `system` and `ha` are currently `runtime+validation`
- the broader service domains are generally `runtime+validation+helper-tools`, usually at `basic field drift` fidelity for helper-tool comparisons

## Quick Links

| Topic | Doc |
|---|---|
| Playbook layout | [docs/playbook-structure.md](docs/playbook-structure.md) |
| Variables and precedence | [docs/var-layout.md](docs/var-layout.md) |
| Hybrid authoring | [docs/hybrid-authoring.md](docs/hybrid-authoring.md) |
| Intent authoring | [docs/intent-authoring.md](docs/intent-authoring.md) |
| Deletion workflows | [docs/deletion-workflows.md](docs/deletion-workflows.md) |
| AWX and HA operation | [docs/04-awx-operation.md](docs/04-awx-operation.md) |
| Validation | [docs/validation.md](docs/validation.md) |
| 01 Initial setup | [docs/01-initial-setup-and-handoff.md](docs/01-initial-setup-and-handoff.md) |
| 02 Bootstrap playbook | [docs/02-bootstrap-playbook.md](docs/02-bootstrap-playbook.md) |
| TLS secrets | [docs/tls-secrets.md](docs/tls-secrets.md) |
| Network objects | [docs/network-objects.md](docs/network-objects.md) |
| System management | [docs/system-management.md](docs/system-management.md) |
| HA lifecycle | [docs/ha.md](docs/ha.md) |
| LTM advanced fields | [docs/ltm-advanced.md](docs/ltm-advanced.md) |
| GTM advanced fields | [docs/gtm-advanced.md](docs/gtm-advanced.md) |
| AFM security | [docs/security.md](docs/security.md) |
| WAF/ASM | [docs/waf.md](docs/waf.md) |
| APM access | [docs/apm.md](docs/apm.md) |
| Authentication | [docs/authentication.md](docs/authentication.md) |
| Kerberos SSO | [docs/kerberos-sso.md](docs/kerberos-sso.md) |
| 05 AWX HA bootstrap | [docs/05-awx-ha-bootstrap.md](docs/05-awx-ha-bootstrap.md) |
| Drift and import | [docs/drift-import.md](docs/drift-import.md) |
| Promotion workflows | [docs/promotion-workflows.md](docs/promotion-workflows.md) |
| Rollback patterns | [docs/rollback-patterns.md](docs/rollback-patterns.md) |
| 03 CLI bootstrap | [docs/03-cli-bootstrap.md](docs/03-cli-bootstrap.md) |
| Example models | [docs/example-models.md](docs/example-models.md) |
| Roadmap | [ROADMAP.md](ROADMAP.md) |

## Playbooks

Canonical playbooks live under `playbooks/`. Root-level `*.yml` files are compatibility wrappers.

| Playbook | Domain |
|---|---|
| `playbooks/network.yml` | VLANs, trunks, route domains, self IPs, routes, SNATs, NATs |
| `playbooks/bootstrap.yml` | device licensing and initial management IP/default-route bootstrap |
| `playbooks/system.yml` | hostname, DNS, NTP, provisioning, users, management-plane admin auth, login banners |
| `playbooks/ha.yml` | device connectivity, device trust, device groups, HA groups, traffic groups, config sync |
| `playbooks/ltm.yml` | monitors, profiles, nodes, pools, virtual servers |
| `playbooks/gtm.yml` | monitors, datacenters, servers, pools, Wide IPs, topology |
| `playbooks/tls.yml` | keys, certificates, CA bundles, SSL profiles |
| `playbooks/security.yml` | AFM address lists, port lists, firewall rules, policies; WAF policies, server technologies; APM ACLs, auth servers, SSO configs, resources, policy nodes, access profiles, per-session policies, macros |

## Current Priorities

The main remaining roadmap items are:

- finishing the specialized LTM/GTM prep refactor where loader/build logic still does more than the new shared fragment/classification helpers cover
- deciding whether `system` and `ha` should gain full drift/import support
- lower-priority lifecycle work such as UCS backup/export and certificate rotation automation

## Validation

```sh
make validate
```

See [docs/validation.md](docs/validation.md) for details.
