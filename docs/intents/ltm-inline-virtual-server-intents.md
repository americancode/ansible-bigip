# LTM Inline Virtual Server Intents

Intent class path:
- `vars/ltm/intents/inline/...`
- deletions: `vars/ltm/deletions/intents/inline/...`

Compiler flow:
- `playbooks/ltm/prep/intents/inline/load-virtual-server-intents.yml`
- `playbooks/ltm/prep/intents/inline/build-virtual-server-intents.yml`
- Python compiler: `filter_plugins/bigip_filters/intent_ltm.py`

Authoring model:
- virtual server must declare pool ownership explicitly with `pool_mode`
- `pool_mode: inline` embeds pool/member data under `pool`
- `pool_mode: reference` points to canonical pools via `pool_ref`
- prep compiles inline pool shape into canonical `ltm_pools`
- virtual server is rewritten to canonical pool reference before runtime

Emitted canonical objects:
- `ltm_virtual_servers`
- `ltm_pools` (only for `pool_mode: inline`)

Validation expectations:
- embedded/compiled pools must have valid members
- monitor references must resolve
- compiled pool names must not collide with canonical pools
- virtual server references must resolve against final pool set

Use this class for concise app-local LTM declarations where service and pool should live together in one file.
