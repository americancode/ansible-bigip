# ansible-bigip

Declarative BIG-IP playbooks organized for GitOps-style management.

## Quick Links

| Topic | Doc |
|---|---|
| Playbook layout | [docs/playbook-structure.md](docs/playbook-structure.md) |
| Variables and precedence | [docs/var-layout.md](docs/var-layout.md) |
| Hybrid authoring | [docs/hybrid-authoring.md](docs/hybrid-authoring.md) |
| Deletion workflows | [docs/deletion-workflows.md](docs/deletion-workflows.md) |
| AWX and HA operation | [docs/awx-operation.md](docs/awx-operation.md) |
| Validation | [docs/validation.md](docs/validation.md) |
| TLS secrets | [docs/tls-secrets.md](docs/tls-secrets.md) |
| Network objects | [docs/network-objects.md](docs/network-objects.md) |
| System management | [docs/system-management.md](docs/system-management.md) |
| LTM advanced fields | [docs/ltm-advanced.md](docs/ltm-advanced.md) |
| GTM advanced fields | [docs/gtm-advanced.md](docs/gtm-advanced.md) |
| AFM security | [docs/security.md](docs/security.md) |
| AWX bootstrap | [docs/awx-ha-bootstrap.md](docs/awx-ha-bootstrap.md) |
| CLI bootstrap | [docs/cli-bootstrap.md](docs/cli-bootstrap.md) |
| Example models | [docs/example-models.md](docs/example-models.md) |
| Roadmap | [ROADMAP.md](ROADMAP.md) |

## Playbooks

Canonical playbooks live under `playbooks/`. Root-level `*.yml` files are compatibility wrappers.

| Playbook | Domain |
|---|---|
| `playbooks/network.yml` | VLANs, trunks, route domains, self IPs, routes, SNATs, NATs |
| `playbooks/system.yml` | hostname, DNS, NTP, provisioning, users |
| `playbooks/ha.yml` | device trust, device groups, traffic groups, config sync |
| `playbooks/ltm.yml` | monitors, profiles, nodes, pools, virtual servers |
| `playbooks/gtm.yml` | monitors, datacenters, servers, pools, Wide IPs, topology |
| `playbooks/tls.yml` | keys, certificates, CA bundles, SSL profiles |
| `playbooks/security.yml` | AFM address lists, port lists, firewall rules, policies |

## Validation

```sh
make validate
```

See [docs/validation.md](docs/validation.md) for details.
