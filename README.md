# ansible-bigip

Declarative BIG-IP playbooks organized for GitOps-style management.

## Playbooks

- `network.yml`: VLANs and self IPs
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

## Hybrid Model

The preferred authoring model is hybrid:

- embed app-local objects when a single file should describe one service clearly
- promote shared or reused objects into first-class trees when multiple apps depend on them

Examples:

- LTM virtual servers can embed their own pool definitions
- GTM Wide IPs can embed their own GTM pools
- shared nodes, pools, datacenters, and TLS objects can live in first-class trees

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

## TLS Notes

The TLS examples use inline `content` fields for keys, certificates, and CA bundles.
Replace the placeholder PEM blocks in:

- `vars/tls/keys/*.yml`
- `vars/tls/certificates/*.yml`
- `vars/tls/ca_bundles/*.yml`

with real material before applying to a device.
