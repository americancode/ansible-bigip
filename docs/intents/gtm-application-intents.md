# GTM Application Intents

Intent class path:
- `vars/gtm/intents/applications/...`
- deletions: `vars/gtm/deletions/intents/applications/...`

Compiler flow:
- `playbooks/gtm/prep/intents/inline/build-application-intents.yml`
- Python compiler: `filter_plugins/bigip_filters/intent_gtm.py`

Authoring model:
- one application intent owns a canonical GTM Wide IP
- each pool binding must declare `pool_mode: reference|inline`
- `pool_mode: reference` points at an existing canonical GTM pool via `pool_ref`
- `pool_mode: inline` embeds a canonical GTM pool under `pool`
- inline pool members can reference existing GTM servers or emit inline servers
- inline servers can reference existing datacenters or emit inline datacenters

Emitted canonical objects:
- `gtm_wide_ips`
- `gtm_pools` (only for `pool_mode: inline`)
- `gtm_servers` (when inline-owned members use `server_mode: inline`)
- `gtm_datacenters` (when inline-owned servers use `datacenter_mode: inline`)

Ownership model:
- `pool_mode: reference|inline` on each pool binding
- `server_mode: reference|inline` on inline pool members
- `datacenter_mode: reference|inline` for inline servers

Validation expectations:
- compiled pools/servers/datacenters must not collide with canonical trees
- canonical pool references from `pool_ref` must resolve after compilation
- member monitor and server refs must resolve

Use this class for application-level DNS intent where the Wide IP, its GTM pools, and optional GTM server/datacenter ownership should be authored together without pushing shortcut logic into runtime tasks.
