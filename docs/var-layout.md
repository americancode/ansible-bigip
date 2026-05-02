# Variable Layout and Precedence

The repo uses split trees under `vars/` so large estates can be managed by domain.

## Domain Trees

- `vars/network/...`
- `vars/system/...`
- `vars/ha/...`
- `vars/ltm/...`
- `vars/gtm/...`
- `vars/tls/...`
- `vars/common.yml` (shared provider configuration)

## Settings Inheritance

Each subtree can use a sibling `settings.yml` to provide defaults for objects in that directory.

Precedence is:

1. object-level value
2. sibling `settings.yml`
3. playbook fallback

For partitions, the fallback is `Common`.

## Network Tree Examples

The network var tree includes:

- local and floating self IP patterns
- route-domain-scoped routing
- reusable SNAT translations and SNAT pools
- trunk examples using the native `bigip_trunk` module
- NAT examples using a validated `tmsh` command workflow (the installed collection does not provide a first-class NAT module)

## Hybrid Authoring

Objects can be embedded directly in parent definitions or promoted to first-class trees. See [hybrid-authoring.md](hybrid-authoring.md) for the full model and examples.

## Deletions

Objects can be removed via deletion trees. See [deletion-workflows.md](deletion-workflows.md).
