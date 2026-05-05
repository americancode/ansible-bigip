# GTM Wide IP Intents

Intent class path:
- `vars/gtm/intents/applications/...`
- deletions: `vars/gtm/deletions/intents/applications/...`

Compiler flow:
- `playbooks/gtm/prep/intents/inline/build-wide-ip-intents.yml`
- Python compiler: `filter_plugins/bigip_filters/intent_gtm.py`

Authoring model:
- Wide IPs can include inline pool/member declarations
- members can reference existing GTM servers or emit inline servers
- inline servers can reference or emit datacenters

Emitted canonical objects:
- `gtm_wide_ips`
- `gtm_pools`
- `gtm_servers` (when inline-owned)
- `gtm_datacenters` (when inline-owned)

Ownership model:
- `server_mode: reference|inline` on members
- `datacenter_mode: reference|inline` for inline servers

Validation expectations:
- compiled pools/servers/datacenters must not collide with canonical trees
- Wide IP pool refs must resolve after compilation
- member monitor and server refs must resolve

Use this class for application-level DNS intent where Wide IP, pools, and optional inline ownership should be authored together.
