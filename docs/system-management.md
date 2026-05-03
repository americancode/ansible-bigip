# System Management

The `playbooks/system.yml` playbook manages base BIG-IP device settings after the device is already reachable through a stable management endpoint: hostname, DNS, NTP, module provisioning, local users, management-plane admin authentication providers, login banner compliance messaging, and config persistence.

For day-0 licensing and the first management IP/default route, use [02-bootstrap-playbook.md](02-bootstrap-playbook.md) and `playbooks/bootstrap.yml` first.

## Object Types

### Hostname

Location: `vars/system/hostname/`

```yaml
system_hostnames:
  - hostname: "bigip-east.example.com"
```

Only one hostname entry is needed. This sets the device hostname via `bigip_hostname`.

### DNS

Location: `vars/system/dns/`

```yaml
system_dns:
  - name_servers:
      - "192.0.2.53"
      - "192.0.2.54"
    search:
      - "my.domain.com"
      - "corp.my.domain.com"
    cache: "enabled"
    ip_version: 4
```

Common fields: `name_servers`, `search`, `cache` (enabled/disabled), `ip_version`.

### NTP

Location: `vars/system/ntp/`

```yaml
system_ntp:
  - ntp_servers:
      - "0.pool.ntp.org"
      - "1.pool.ntp.org"
    timezone: "America/New_York"
```

Common fields: `ntp_servers`, `timezone`.

### Provisioning

Location: `vars/system/provisioning/`

Controls which BIG-IP modules are provisioned and at what level:

```yaml
system_provisioning:
  - module: "ltm"
    level: "dedicated"

  - module: "gtm"
    level: "nominal"

  - module: "asm"
    level: "nominal"
```

Required: `module`. Common fields: `level` (none, minimum, nominal, dedicated). Modules provisioned at `none` or with `state: absent` are deprovisioned.

### Users

Location: `vars/system/users/`

```yaml
system_users:
  - name: "automation-admin"
    full_name: "Automation Admin"
    partition_access:
      - "all:admin"
    shell: "tmsh"
    update_password: "on_create"
    password_credential: "ChangeMe-Immediately-123!"
```

Required: `name`. Common fields: `full_name`, `partition_access`, `shell`, `password_credential`, `update_password`. The `update_password` field controls when passwords are changed: `on_create` sets it only on first creation, `always` updates on every run.

### Management-Plane LDAP / Active Directory Auth

Location: `vars/system/auth/ldap/`

This configures how BIG-IP administrators log in to the appliance itself. It is separate from APM end-user authentication in [apm.md](apm.md).

```yaml
system_auth_ldap:
  - name: "corp-ad-admins"
    source_type: "active-directory"
    servers:
      - "ad01.example.com"
      - "ad02.example.com"
    bind_dn: "CN=svc-bigip,OU=Svc,DC=example,DC=com"
    bind_password: !vault |
      $ANSIBLE_VAULT;1.1;AES256
      61333363356166323839396436313537326461346238656462613039373161626538393061656434
    remote_directory_tree: "DC=example,DC=com"
    user_template: "%s@example.com"
    login_ldap_attr: "sAMAccountName"
    ssl: "start-tls"
    use_for_auth: true
    fallback_to_local: true
```

Required: `name`, `servers`. Common fields: `source_type`, `bind_dn`, `bind_password`, `remote_directory_tree`, `user_template`, `login_ldap_attr`, `ssl`, `scope`, `use_for_auth`, `fallback_to_local`.

### Management-Plane TACACS+

Location: `vars/system/auth/tacacs/`

```yaml
system_auth_tacacs:
  - name: "corp-tacacs"
    servers:
      - address: "192.0.2.61"
        port: 49163
      - address: "192.0.2.62"
    secret: !vault |
      $ANSIBLE_VAULT;1.1;AES256
      36373433643035616266303536386461613665363566633361663434366563303962616464326362
    authentication: "use-all-servers"
    accounting: "send-to-all-servers"
    protocol_name: "ip"
    service_name: "system"
    use_for_auth: false
```

Common fields: `servers`, `secret`, `authentication`, `accounting`, `protocol_name`, `service_name`, `update_secret`, `use_for_auth`.

### Management-Plane RADIUS Servers

Location: `vars/system/auth/radius_servers/`

```yaml
system_auth_radius_servers:
  - name: "radius_dc1"
    partition: "Common"
    ip: "192.0.2.71"
    port: 1812
    secret: !vault |
      $ANSIBLE_VAULT;1.1;AES256
      65663563323663353562656434383762613631353939656435623336353330383232626539653864
    timeout: 5
```

Required: `name`, `ip`. Common fields: `partition`, `description`, `port`, `secret`, `timeout`, `update_secret`.

### Management-Plane RADIUS Auth Profile

Location: `vars/system/auth/radius/`

```yaml
system_auth_radius:
  - name: "corp-radius"
    servers:
      - "radius_dc1"
      - "radius_dc2"
    retries: 3
    service_type: "administrative"
    fallback_to_local: true
    use_for_auth: false
```

The `servers` list points at objects defined in `vars/system/auth/radius_servers/`. Use `/Partition/name` when a referenced server is not in `Common`.

Common fields: `servers`, `retries`, `service_type`, `accounting_bug`, `fallback_to_local`, `use_for_auth`.

### Login Banner

Location: `vars/system/login_banners/`

This manages the BIG-IP GUI security banner shown before administrator login. It is device-scoped and normally only one active declaration should exist for a target BIG-IP.

```yaml
system_login_banners:
  - name: "authorized-use-banner"
    enabled: true
    text: |
      WARNING: This system is for authorized use only.
      Activity may be monitored, recorded, and subject to audit.
```

Supported fields: `enabled`, `text`, and optional `name` for repo-side labeling. A deletion entry or `state: absent` disables the banner.

### Config Save

Location: `vars/system/config/`

Persists the running configuration to disk after other system changes:

```yaml
system_config:
  - save: true
```

This runs `bigip_config` to save the running config. It is the last task in the system playbook.

## Execution Order

1. Hostname
2. DNS
3. NTP
4. Provisioning
5. Users
6. Management-plane auth providers
7. Login banner
8. Config save

## Partition and Naming Conventions

System objects are device-scoped, not partition-scoped, with two practical exceptions:

- users support `partition_access` for role assignment
- RADIUS server objects can still live in a partition, usually `Common`

For environments with multiple auth methods defined in Git, only one of LDAP, TACACS, or RADIUS should set `use_for_auth: true` for a given target BIG-IP.

For environments with multiple HA pairs, system settings are typically applied per device rather than synced. Run `system.yml` against each device individually when settings differ between peers.

## Current Lifecycle Boundary

The `system` domain is intentionally `runtime+validation` for the current phase.

- runtime playbook support is first-class
- `tools/validate-vars.py` supports the tree and references
- helper-tool drift/import support is intentionally not implemented yet for `system`

Treat `system.yml` as the Git-authored runtime source of truth, but do not expect `tools/drift-check.py` or `tools/import-from-bigip.py` to round-trip these objects today.

## Deletion

Users, management-plane auth objects, and login banners can be removed with `state: absent` or the matching `vars/system/deletions/...` tree. DNS and NTP objects use a present-state model where the last declaration wins. See [deletion-workflows.md](deletion-workflows.md).
