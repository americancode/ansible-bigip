# System Management

The `playbooks/system.yml` playbook manages base BIG-IP device settings after the device is already reachable through a stable management endpoint: hostname, DNS, NTP, module provisioning, administrative partitions, local users, management-plane admin authentication providers, login banner compliance messaging, and config persistence.

For day-0 licensing and the first management IP/default route, use [02-bootstrap-playbook.md](02-bootstrap-playbook.md) and `playbooks/bootstrap.yml` first. For normal AWX inventory and targeting guidance, see [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md).

## Targeting Model

System objects are filtered per inventory host before runtime tasks execute.

- every `system_*` object must define at least one of `target_hosts` or `target_groups`
- `target_hosts` matches AWX or CLI `inventory_hostname`
- `target_groups` matches Ansible `group_names`
- prep logs how many objects matched or were skipped for the current host

Safety rules enforced by validation:

- `system_hostnames` must target exactly one explicit host
- if multiple declarations exist for the same device-scoped identity, they must use disjoint `target_hosts`
- if more than one declaration exists for the same identity, `target_groups` are rejected because overlap cannot be proven offline

For the command-driven login banner path, launch with `show_tmsh_commands=true` to print the generated `tmsh` command before execution. This is useful when a banner update is skipped unexpectedly or when the emitted command needs to be compared with a manual `tmsh` test.

Example:

```yaml
system_dns:
  - name_servers:
      - "192.0.2.53"
      - "192.0.2.54"
    target_groups:
      - "all_bigip"
```

## Object Types

### Hostname

Location: `vars/system/hostname/`

```yaml
system_hostnames:
  - hostname: "bigip-east.example.com"
    target_hosts:
      - "bigip-east-device"
```

Only one active hostname declaration may match a given target BIG-IP. This sets the device hostname via `bigip_hostname`.

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
    target_groups:
      - "all_bigip"
```

Common fields: `name_servers`, `search`, `cache` (enabled/disabled), `ip_version`, `target_hosts`, `target_groups`.

### NTP

Location: `vars/system/ntp/`

```yaml
system_ntp:
  - ntp_servers:
      - "0.pool.ntp.org"
      - "1.pool.ntp.org"
    timezone: "America/New_York"
    target_groups:
      - "all_bigip"
```

Common fields: `ntp_servers`, `timezone`, `target_hosts`, `target_groups`.

### Provisioning

Location: `vars/system/provisioning/`

Controls which BIG-IP modules are provisioned and at what level:

```yaml
system_provisioning:
  - module: "ltm"
    level: "dedicated"
    target_groups:
      - "all_bigip"

  - module: "gtm"
    level: "nominal"
    target_groups:
      - "all_bigip"

  - module: "asm"
    level: "nominal"
    target_groups:
      - "all_bigip"
```

Required: `module`. Common fields: `level` (none, minimum, nominal, dedicated), `target_hosts`, `target_groups`. Modules provisioned at `none` or with `state: absent` are deprovisioned.

### Administrative Partitions

Location: `vars/system/partitions/`

This manages BIG-IP administrative partitions with the native `bigip_partition` module. These partitions can then be referenced by user `partition_access` assignments and by partition-scoped runtime objects elsewhere in the repo.

```yaml
system_partitions:
  - name: "apps"
    description: "Application tenant partition"
    route_domain: 0
    target_groups:
      - "all_bigip"
```

Required: `name`. Common fields: `description`, `route_domain`, `target_hosts`, `target_groups`. The object must not define a separate `partition` field because the object itself is the partition.

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
    target_groups:
      - "all_bigip"
```

Required: `name`. Common fields: `full_name`, `partition_access`, `shell`, `password_credential`, `update_password`, `target_hosts`, `target_groups`. The `update_password` field controls when passwords are changed: `on_create` sets it only on first creation, `always` updates on every run. When `partition_access` references custom partitions, declare those partitions in `vars/system/partitions/` so the same playbook run can create them before the user is applied.

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
    target_groups:
      - "all_bigip"
```

Required: `name`, `servers`. Common fields: `source_type`, `bind_dn`, `bind_password`, `remote_directory_tree`, `user_template`, `login_ldap_attr`, `ssl`, `scope`, `use_for_auth`, `fallback_to_local`, `target_hosts`, `target_groups`.

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
    target_groups:
      - "all_bigip"
```

Common fields: `servers`, `secret`, `authentication`, `accounting`, `protocol_name`, `service_name`, `update_secret`, `use_for_auth`, `target_hosts`, `target_groups`.

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
    target_groups:
      - "all_bigip"
```

Required: `name`, `ip`. Common fields: `partition`, `description`, `port`, `secret`, `timeout`, `update_secret`, `target_hosts`, `target_groups`.

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
    target_groups:
      - "all_bigip"
```

The `servers` list points at objects defined in `vars/system/auth/radius_servers/`. Use `/Partition/name` when a referenced server is not in `Common`.

Common fields: `servers`, `retries`, `service_type`, `accounting_bug`, `fallback_to_local`, `use_for_auth`, `target_hosts`, `target_groups`.

### Login Banner

Location: `vars/system/login_banners/`

This manages the BIG-IP GUI security banner shown before administrator login. It is device-scoped and normally only one active declaration should exist for a target BIG-IP.

```yaml
system_login_banners:
  - name: "authorized-use-banner"
    enabled: true
    target_groups:
      - "all_bigip"
    text: |
      WARNING: This system is for authorized use only.
      Activity may be monitored, recorded, and subject to audit.
```

Supported fields: `enabled`, `text`, optional `name`, `target_hosts`, and `target_groups`. A deletion entry or `state: absent` disables the banner.

### Config Save

Location: `vars/system/config/`

Persists the running configuration to disk after other system changes:

```yaml
system_config:
  - save: true
    target_groups:
      - "all_bigip"
```

This runs `bigip_config` to save the running config. It is the last task in the system playbook.

## Execution Order

1. Hostname
2. DNS
3. NTP
4. Provisioning
5. Administrative partitions
6. Users
7. Management-plane auth providers
8. Login banner
9. Config save

## Partition and Naming Conventions

System objects are device-scoped, not partition-scoped, with two practical exceptions:

- administrative partitions are first-class system objects under `vars/system/partitions/`
- users support `partition_access` for role assignment
- RADIUS server objects can still live in a partition, usually `Common`

For environments with multiple auth methods defined in Git, only one of LDAP, TACACS, or RADIUS should set `use_for_auth: true` for a given target BIG-IP.

For environments with multiple HA pairs, system settings are typically applied per device rather than synced. Use `target_hosts` for device-specific settings such as hostname, and use `target_groups` only when one declaration is intentionally meant to apply to every host in that inventory group.

## Current Lifecycle Boundary

The `system` domain is intentionally `runtime+validation` for the current phase.

- runtime playbook support is first-class
- `tools/validate-vars.py` supports the tree and references
- administrative partitions now have helper-tool support at `basic field drift` fidelity
- broader helper-tool drift/import support is still intentionally incomplete for the rest of `system`

Treat `system.yml` as the Git-authored runtime source of truth. Today only administrative partitions have drift/import helper-tool coverage inside this domain.

## Deletion

Administrative partitions, users, management-plane auth objects, and login banners can be removed with `state: absent` or the matching `vars/system/deletions/...` tree. DNS and NTP objects use a present-state model where the last declaration wins. See [deletion-workflows.md](deletion-workflows.md).
