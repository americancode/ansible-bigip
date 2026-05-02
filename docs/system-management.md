# System Management

The `playbooks/system.yml` playbook manages base BIG-IP device settings: hostname, DNS, NTP, module provisioning, local users, and config persistence.

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
6. Config save

## Partition and Naming Conventions

System objects are device-scoped, not partition-scoped (with the exception of users, which support `partition_access` for role assignment). Use `Common` partition for user partition access unless you need restricted partitions.

For environments with multiple HA pairs, system settings are typically applied per device rather than synced. Run `system.yml` against each device individually when settings differ between peers.

## Deletion

Users can be removed with `state: absent`. DNS and NTP objects use a present-state model where the last declaration wins. See [deletion-workflows.md](deletion-workflows.md).
