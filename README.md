# ansible-bigip

Declarative BIG-IP playbooks organized for GitOps-style management.

## Binding Repo Rules

These are binding maintenance rules for anyone changing this repository, including future AI agents:

- keep `ROADMAP.md` in sync with actual implementation state and remaining backlog items
- update docs and example var files whenever a feature changes authoring patterns or references
- explain cross-file linkages and reference strings inline where operators will read them
- validate after each major change before moving to the next implementation step
- print or suggest a commit name only after implementation and validation are complete

## Playbooks

- `network.yml`: VLANs, trunks, route domains, self IPs, static routes, SNAT translations, SNAT pools, and NATs
- `system.yml`: base system settings like hostname, DNS, NTP, provisioning, users
- `ha.yml`: device trust, device groups, traffic groups, config sync actions
- `ltm.yml`: LTM monitors, nodes, pools, virtual servers
- `gtm.yml`: GTM monitors, datacenters, servers, pools, Wide IPs
- `tls.yml`: SSL keys, certificates, CA bundles, client SSL profiles, server SSL profiles

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
- GTM pool members can resolve `address` and `port` from repo-known LTM virtual servers when `virtual_server` names already match

Example walkthroughs live in [docs/example-models.md](/Users/nathanielchurchill/source/ansible-bigip/docs/example-models.md). The example var files also carry inline comments that point to related files and explain how cross-file linkages work.

## Deletions

Missing from vars does not mean delete.

Supported deletion patterns:

- put `state: absent` on an object in its normal tree
- place objects in `vars/*/deletions/...`

Deletion trees are the preferred destructive workflow because they make review clearer.

## Validation

Run local validation with:

```sh
make validate
```

This runs:

- `python3 tools/validate-vars`
- `ansible-playbook --syntax-check` for all top-level playbooks

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
