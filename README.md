# ansible-bigip

Declarative BIG-IP playbooks organized for GitOps-style management.

## Binding Repo Rules

These are binding maintenance rules for anyone changing this repository, including future AI agents:

- keep `ROADMAP.md` in sync with actual implementation state and remaining backlog items
- update docs and example var files whenever a feature changes authoring patterns or references
- explain cross-file linkages and reference strings inline where operators will read them
- if an empty directory must exist intentionally, keep it with a `.gitkeep`
- validate after each major change before moving to the next implementation step
- print or suggest a commit name only after implementation and validation are complete

## Playbooks

Canonical playbooks live under `playbooks/`. Root-level `*.yml` files remain as compatibility wrappers that import the canonical playbooks.

- `playbooks/network.yml`: VLANs, trunks, route domains, self IPs, static routes, SNAT translations, SNAT pools, and NATs
- `playbooks/system.yml`: base system settings like hostname, DNS, NTP, provisioning, users
- `playbooks/ha.yml`: device trust, device groups, traffic groups, config sync actions
- `playbooks/ltm.yml`: LTM monitors, non-TLS profiles, nodes, pools, virtual servers
- `playbooks/gtm.yml`: GTM monitors, datacenters, servers, pools, Wide IPs
- `playbooks/tls.yml`: SSL keys, certificates, CA bundles, client SSL profiles, server SSL profiles

## Playbook Layout

Canonical playbooks use a consistent split so the entrypoint stays small and the discovery and execution logic remain easy to follow:

- `playbooks/<domain>.yml` is the canonical entrypoint
- `playbooks/<domain>/prep.yml` contains fragment discovery, `include_vars`, defaults loading, and aggregation logic
- `playbooks/<domain>/tasks/manage.yml` orchestrates task execution order
- `playbooks/<domain>/tasks/delete.yml` contains destructive tasks
- `playbooks/<domain>/tasks/apply.yml` contains present-state create/update tasks

This pattern is the default for `network`, `system`, `ha`, `tls`, `ltm`, and `gtm`. If a future playbook stays small enough that splitting it adds no value, document that choice in the roadmap before keeping it monolithic.

Path handling inside canonical playbooks is anchored from `playbook_dir`, so moving playbooks under `playbooks/` does not break references to `vars/`.
The canonical playbooks target AWX inventory hosts with `connection: local`, so inventory host vars such as `f5_host` are available even though the BIG-IP API calls are made from the controller.

## Var Layout

The repo uses split trees under `vars/` so large estates can be managed by domain.

- `vars/network/...`
- `vars/system/...`
- `vars/ha/...`
- `vars/ltm/...`
- `vars/gtm/...`
- `vars/tls/...`

Each subtree can use a sibling `settings.yml`.

Precedence is:

1. object-level value
2. sibling `settings.yml`
3. playbook fallback

For partitions, the fallback is `Common`.

The network examples include:

- local and floating self IP patterns
- route-domain-scoped routing
- reusable SNAT translations and SNAT pools
- trunk examples plus NAT examples using a validated `tmsh` command workflow because the installed collection does not provide a first-class NAT module

## Hybrid Model

The preferred authoring model is hybrid:

- embed app-local objects when a single file should describe one service clearly
- promote shared or reused objects into first-class trees when multiple apps depend on them

Examples:

- LTM virtual servers can embed their own pool definitions
- GTM Wide IPs can embed their own GTM pools
- shared nodes, pools, datacenters, and TLS objects can live in first-class trees
- shared non-TLS LTM profiles can live in `vars/ltm/profiles/...` and be attached by name from virtual servers
- GTM pool members can resolve `address` and `port` from repo-known LTM virtual servers when `virtual_server` names already match

Example walkthroughs live in [docs/example-models.md](/Users/nathanielchurchill/source/ansible-bigip/docs/example-models.md). The example var files also carry inline comments that point to related files and explain how cross-file linkages work.

## Deletions

Missing from vars does not mean delete.

Supported deletion patterns:

- put `state: absent` on an object in its normal tree
- place objects in `vars/*/deletions/...`

Deletion trees are the preferred destructive workflow because they make review clearer.

## AWX and HA Operation

This repository talks to one BIG-IP management endpoint per run.

- the playbooks use the `provider` object in [vars/common.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/common.yml)
- the canonical playbooks target AWX inventory hosts with `connection: local`
- `provider.server` prefers the inventory host var `f5_host`
- `F5_HOST` remains an environment fallback for local testing or one-off runs
- if `f5_host` or `F5_HOST` points at one BIG-IP, only that BIG-IP is directly configured by that job

For a normal BIG-IP sync-failover pair, most shared configuration should be applied to one designated device in the HA domain and then replicated through config sync.

Safe default operating rule:

- for `playbooks/network.yml`, `playbooks/ltm.yml`, and `playbooks/tls.yml`, target one sync-owner device per HA pair
- use `playbooks/ha.yml` to establish or change trust, device groups, members, traffic groups, and config sync actions
- do not target both peers in the same HA pair for routine shared-config jobs unless you explicitly mean to

The HA example vars under `vars/ha/...` are written with that same perspective:

- `device_trust` examples are authored from the current target device toward its peer
- `device_groups`, `device_group_members`, and `traffic_groups` describe shared HA state, but are still meant to be applied from one designated device in the sync domain
- `configsync_actions.sync_device_to_group: true` means "push from the device currently selected as the execution target"

Recommended AWX pattern:

- create one inventory per environment, for example `prod-bigip`
- represent each HA sync domain with one execution target host, not one host per appliance for normal shared-config jobs
- store the management endpoint in a host var such as `f5_host`
- use the custom credential for `F5_USERNAME`, `F5_PASSWORD`, and optional port/cert settings
- do not put the host in the credential; let the selected inventory host choose the target

Minimum required inventory host vars:

```yaml
f5_host: bigip-east.example.com
```

Only `f5_host` is required by the playbooks today. Additional fields such as pair name, role, datacenter, or peer metadata are optional inventory metadata.

Example inventory host vars:

```yaml
f5_host: bigip-east.example.com
f5_pair_name: east-prod-pair
f5_role: sync_owner
f5_dc: east
```

Example auth-only credential fields from [bigip-credential-config.yaml](/Users/nathanielchurchill/source/ansible-bigip/bigip-credential-config.yaml):

- `f5_username`
- `f5_password`
- optional `f5_server_port`
- optional `f5_validate_certs`

Example AWX template split:

- `BIG-IP HA Bootstrap` -> `playbooks/ha.yml`
- `BIG-IP Network Apply` -> `playbooks/network.yml`
- `BIG-IP LTM Apply` -> `playbooks/ltm.yml`
- `BIG-IP TLS Apply` -> `playbooks/tls.yml`
- `BIG-IP System Apply` -> `playbooks/system.yml`
- `BIG-IP GTM Apply` -> `playbooks/gtm.yml`

Operationally, treat each datacenter HA pair as its own execution boundary. If you need to update two datacenters, run one job per pair rather than one job per appliance.

For a concrete two-device bootstrap example with AWX inventory layout, template names, auth-only credential injection, and the matching `vars/ha/...` files, see [docs/awx-ha-bootstrap.md](/Users/nathanielchurchill/source/ansible-bigip/docs/awx-ha-bootstrap.md).
For a terminal-first bootstrap path that avoids AWX chicken-and-egg issues, see [docs/cli-bootstrap.md](/Users/nathanielchurchill/source/ansible-bigip/docs/cli-bootstrap.md).

## Validation

Run local validation with:

```sh
make validate
```

This runs:

- `python3 tools/validate-vars`
- `ansible-playbook --syntax-check` for all canonical playbooks under `playbooks/`

The validator accepts Ansible-specific YAML tags such as inline `!vault`, so encrypted TLS material can stay in the same var trees without breaking offline checks.

## TLS Notes

The TLS examples use inline `content` fields for keys, certificates, and CA bundles.
For real environments:

- keep object metadata in Git as normal YAML
- encrypt private key `content` with Ansible Vault
- use Vault for certificate or CA bundle `content` when those artifacts are not meant to be stored in plaintext

Replace the placeholder PEM blocks in:

- `vars/tls/keys/*.yml`
- `vars/tls/certificates/*.yml`
- `vars/tls/ca_bundles/*.yml`

with real material before applying to a device. The recommended format is inline Vault content:

```yaml
content: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...
```

See [docs/tls-secrets.md](/Users/nathanielchurchill/source/ansible-bigip/docs/tls-secrets.md) for the repo convention.
