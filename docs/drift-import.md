# Drift Detection and Import

This repository provides two offline tooling scripts for comparing live BIG-IP state against Git-declared configuration and for importing existing BIG-IP estates into the repository's var tree format.

Intent trees such as `vars/ltm/intents/clusters/...` are authoring abstractions. These helper tools operate on the canonical BIG-IP object families that the intent layer compiles into, not on the intent files directly.

## Prerequisites

Both tools use the same environment variables for authentication:

| Variable | Default | Description |
|---|---|---|
| `F5_HOST` | — | BIG-IP hostname or IP address (required) |
| `F5_USERNAME` | `admin` | BIG-IP username |
| `F5_PASSWORD` | — | BIG-IP password (required) |
| `F5_SERVER_PORT` | `443` | BIG-IP REST API port |

Python 3.10+ and the `requests` package are required. Install with:

```sh
pip install requests
```

## Drift Detection

`tools/drift-check.py` queries the live BIG-IP running configuration, compares it against objects declared in the repository's var trees, and reports differences.

### Usage

```sh
# Check all object types
F5_HOST=10.0.0.1 F5_PASSWORD=secret python3 tools/drift-check.py

# Check specific object types only
F5_HOST=10.0.0.1 F5_PASSWORD=secret python3 tools/drift-check.py --types ltm_nodes ltm_pools ltm_virtual_servers

# Output as JSON for CI integration
F5_HOST=10.0.0.1 F5_PASSWORD=secret python3 tools/drift-check.py --json
```

### Report Categories

The tool reports drift in three categories:

- **ON DEVICE BUT NOT IN GIT** — objects that exist on the BIG-IP but have no corresponding declaration in `vars/`. These may be manually configured objects that should be imported or removed.

- **IN GIT BUT NOT ON DEVICE** — objects declared in `vars/` but not found on the BIG-IP. These may need to be applied via playbook execution.

- **VALUE DRIFT** — objects that exist in both places but have differing values for tracked fields (description, load balancing method, monitor assignments, etc.).

### Supported Object Types

| Type | API Endpoint |
|---|---|
| `ltm_nodes` | `/mgmt/tm/ltm/node` |
| `ltm_pools` | `/mgmt/tm/ltm/pool` |
| `ltm_virtual_servers` | `/mgmt/tm/ltm/virtual` |
| `ltm_monitors` | `/mgmt/tm/ltm/monitor` |
| `ltm_profiles` | `/mgmt/tm/ltm/profile` |
| `ltm_persistence_profiles` | `/mgmt/tm/ltm/persistence` |
| `ltm_irules` | `/mgmt/tm/ltm/rule` |
| `ltm_data_groups` | `/mgmt/tm/ltm/data-group` |
| `ltm_policies` | `/mgmt/tm/ltm/policy` |
| `gtm_datacenters` | `/mgmt/tm/gtm/datacenter` |
| `gtm_servers` | `/mgmt/tm/gtm/server` |
| `gtm_pools` | `/mgmt/tm/gtm/pool` |
| `gtm_wide_ips` | `/mgmt/tm/gtm/wideip` |
| `gtm_topology_regions` | `/mgmt/tm/gtm/region` |
| `gtm_topology_records` | `/mgmt/tm/gtm/topology` |
| `gtm_monitors` | `/mgmt/tm/gtm/monitor` |
| `network_vlans` | `/mgmt/tm/net/vlan` |
| `network_trunks` | `/mgmt/tm/net/trunk` |
| `network_self_ips` | `/mgmt/tm/net/self` |
| `network_routes` | `/mgmt/tm/net/route` |
| `network_route_domains` | `/mgmt/tm/net/route-domain` |
| `network_snat_translations` | `/mgmt/tm/ltm/snat-translation` |
| `network_snats` | `/mgmt/tm/ltm/snatpool` |
| `network_nats` | `/mgmt/tm/ltm/nat` |
| `afm_address_lists` | `/mgmt/tm/security/firewall/address-list` |
| `afm_port_lists` | `/mgmt/tm/security/firewall/port-list` |
| `afm_rules` | `/mgmt/tm/security/firewall/rule` |
| `afm_policies` | `/mgmt/tm/security/firewall/rule-list` |
| `waf_policies` | `/mgmt/tm/asm/policies` |
| `waf_server_technologies` | `/mgmt/tm/asm/policies` with per-policy `serverTechnologyReference` subcollection traversal |
| `apm_acls` | `/mgmt/tm/access/policy/acl` |
| `apm_auth_servers` | `/mgmt/tm/auth/remote-server` |
| `apm_sso_configs` | `/mgmt/tm/apm/sso` |
| `apm_resources` | `/mgmt/tm/apm/resource` |
| `apm_access_profiles` | `/mgmt/tm/access/profile` |
| `apm_per_session_policies` | `/mgmt/tm/access/per-session-policy` |
| `apm_macros` | `/mgmt/tm/access/macro` |
| `apm_policy_nodes` | `/mgmt/tm/apm/policy/access-policy` with `items` array traversal |
| `tls_keys` | `/mgmt/tm/sys/crypto/key` |
| `tls_certificates` | `/mgmt/tm/sys/crypto/cert` |
| `tls_ca_bundles` | `/mgmt/tm/sys/crypto/ca-bundle` |
| `tls_client_ssl_profiles` | `/mgmt/tm/ltm/profile/client-ssl` |
| `tls_server_ssl_profiles` | `/mgmt/tm/ltm/profile/server-ssl` |

### Current Boundaries

Runtime playbook coverage is broader than helper-tool coverage. The following object families are still runtime-managed only and are not yet handled accurately enough for drift/import:

- `system` and `ha` domain objects

For several newer supported families, drift/import is present but still not full-fidelity. Treat generated output as a starting point for review, not as an authoritative round-trip export of every field.

Current helper-tool fidelity notes:

- `network_route_domains`, `network_trunks`, `network_snat_translations`, `network_snats`, and `network_nats` now have `basic field drift` coverage for the core fields the runtime playbooks manage directly.
- `gtm_topology_regions`, `gtm_topology_records`, `tls_ca_bundles`, `tls_client_ssl_profiles`, `tls_server_ssl_profiles`, `apm_sso_configs`, `apm_access_profiles`, and `apm_policy_nodes` now have `basic field drift` coverage for their core runtime-managed fields.
- `system` and `ha` remain runtime-managed only.
- other newer families may still have helper coverage that is shallower than the runtime field model.

This is especially true for:

- APM SSO configs, where helper tooling compares the main declarative type-specific fields but should still be treated as review-first when secrets or masked values are involved
- APM policy nodes, where helper tooling compares declared `properties` keys with normalized scalar, reference, and `rules` handling but is not a full semantic diff of every possible VPE graph behavior
- any object family where nested child properties or subcollections are represented more richly in runtime than in import output

## Import from BIG-IP

`tools/import-from-bigip.py` queries a live BIG-IP device and generates YAML files matching the repository's var tree structure. Output is written to a target directory for review before committing.

### Usage

```sh
# Import all supported object types
F5_HOST=10.0.0.1 F5_PASSWORD=secret python3 tools/import-from-bigip.py --out imported/

# Import specific object types only
F5_HOST=10.0.0.1 F5_PASSWORD=secret python3 tools/import-from-bigip.py --out imported/ --types ltm_nodes ltm_pools ltm_virtual_servers
```

### Output Structure

Generated files are written under the target directory following the repository's var tree layout:

```
imported/
├── ltm/
│   ├── nodes/
│   │   └── imported-ltm-nodes.yml
│   ├── pools/
│   │   └── imported-ltm-pools.yml
│   └── virtual_servers/
│       └── imported-ltm-virtual-servers.yml
├── gtm/
│   ├── datacenters/
│   │   └── imported-gtm-datacenters.yml
│   └── servers/
│       └── imported-gtm-servers.yml
├── network/
│   └── vlans/
│       └── imported-network-vlans.yml
└── security/
    └── afm/
        └── address_lists/
            └── imported-afm-address-lists.yml
```

### Import Behavior

- Only objects that exist on the device are exported; the tool does not generate placeholders.
- Built-in monitor and profile references are preserved as-is (`/Common/tcp`, `/Common/https`).
- Custom objects retain their fully qualified names.
- Partitions other than `Common` are preserved with an explicit `partition` field.
- Pool members and virtual server profiles/policies/iRules are fetched via sub-queries and included in the generated YAML.
- TLS private key content is not exported (metadata only); keys must be re-encrypted with Ansible Vault.
- `network_snats` refers to SNAT pools under `vars/network/snats/`, not SNAT translation addresses under `vars/network/snat_translations/`.

### Post-Import Workflow

After running the import:

1. Review the generated files for correctness.
2. Merge them into the appropriate locations under `vars/` (replacing the `imported/` prefix with the real var tree paths).
3. Run `make validate` to check for reference integrity.
4. Commit and apply via playbook execution.

## CI Integration

Drift detection can be run as a CI job to surface unauthorized changes:

```yaml
# Example GitLab CI job
drift-check:
  stage: test
  script:
    - pip install requests
    - python3 tools/drift-check.py --json > drift-report.json
  artifacts:
    reports:
      drift: drift-report.json
  allow_failure: true
```

The `--json` flag produces machine-readable output suitable for dashboards and alerting.
