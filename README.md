# ansible-bigip

Declarative BIG-IP playbooks organized for GitOps-style management.

## Binding Repo Rules

These are binding maintenance rules for anyone changing this repository, including future AI agents:

- update `docs/` alongside every code change; keep `README.md` minimal with only high-level links
- update `ROADMAP.md` (Current State, backlog, milestones, implementation audit) whenever scope changes
- update example var files under `vars/` when a feature adds or changes an authoring pattern
- explain cross-file linkages and reference strings inline where operators will read them
- if an empty directory must exist intentionally, keep it with a `.gitkeep`
- validate after each major change before moving to the next implementation step
- at the end of every implementation prompt, after changes are made and validated, print a suggested commit message

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
| `playbooks/gtm.yml` | monitors, datacenters, servers, pools, Wide IPs |
| `playbooks/tls.yml` | keys, certificates, CA bundles, SSL profiles |

## Validation

```sh
make validate
```

See [docs/validation.md](docs/validation.md) for details.
