# Bootstrap Management

The `playbooks/bootstrap.yml` playbook handles day-0 bootstrap tasks for a brand-new or newly reset BIG-IP before the broader `system`, `ha`, `network`, and service-domain playbooks take over.

This playbook is intentionally narrow:

- license activation or revocation
- first reachable management IP and default management route

It is designed for the chicken-and-egg case where AWX cannot be the first control plane yet.

## Playbook Structure

- `playbooks/bootstrap.yml` — canonical entrypoint
- `playbooks/bootstrap/prep.yml` — discovers and aggregates bootstrap var fragments
- `playbooks/bootstrap/tasks/manage.yml` — ordering wrapper
- `playbooks/bootstrap/tasks/delete.yml` — intentionally empty because bootstrap is apply-only
- `playbooks/bootstrap/tasks/apply.yml` — license and management-reachability tasks

`bootstrap` is the documented exception to the repo’s usual delete/apply semantics. There is no meaningful deletion workflow for initial licensing and management-IP seeding, so the delete phase is intentionally empty and the validator rejects bootstrap deletion entries.

## Var Tree Layout

- `vars/bootstrap/license/`
- `vars/bootstrap/management/`
- `vars/bootstrap/deletions/license/`
- `vars/bootstrap/deletions/management/`

The deletion directories exist only to preserve the repo’s tree shape and to make unsupported deletion intent explicit. Do not place active bootstrap objects under `deletions/`.

## Object Types

### License

Location: `vars/bootstrap/license/`

```yaml
bootstrap_licenses:
  - license_key: "AAAAA-BBBBB-CCCCC-DDDDD-EEEEEEE"
    accept_eula: true
    license_server: "activate.f5.com"
```

Supported fields:

- `license_key` — required for `state: present` and `state: latest`
- `accept_eula` — must be `true` for `present` or `latest`
- `license_server`
- `addon_keys`
- `force`
- `state` — `present`, `latest`, `absent`, or `revoked`

### Management Reachability

Location: `vars/bootstrap/management/`

```yaml
bootstrap_management:
  - address: "192.0.2.10/24"
    gateway: "192.0.2.1"
    route_name: "default"
```

Supported fields:

- `address` — required CIDR for the management interface
- `gateway` — required management default gateway IP
- `route_name` — optional, defaults to `default`

## Execution Notes

The apply order is:

1. license changes
2. config save after license changes
3. management IP and management-route update
4. inline `save sys config` during the management update

The management step intentionally saves within the same `bigip_command` task. If the device’s management IP changes during the run, subsequent API calls to the old address may fail; saving in the same task avoids leaving the device half-changed.

## Operational Boundary

After `bootstrap.yml` succeeds:

1. update the inventory host var `f5_host` to the new management IP if it changed
2. move to `playbooks/system.yml` for hostname, DNS, NTP, provisioning, and users
3. move to `playbooks/ha.yml` if the device is joining an HA pair
4. then apply `network`, `tls`, `ltm`, `gtm`, and `security` as needed

This playbook is currently `runtime+validation`, not helper-tool complete. There is no `drift-check` or brownfield import support for bootstrap objects yet because bootstrap is a day-0, apply-only domain whose primary purpose is to establish first reachability and licensing before the steadier Git-managed lifecycle begins.

For the full first-boot sequence and AWX handoff story, see [initial-setup.md](initial-setup.md).
