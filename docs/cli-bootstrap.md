# CLI Bootstrap

This guide covers the chicken-and-egg case where AWX is not the right first control plane because AWX itself depends on BIG-IP being available first.

Use this path when:

- AWX is fronted by the BIG-IP estate you are about to build
- you need to initialize one or more new BIG-IP devices from a terminal
- you want a simple, repeatable bootstrap process before shifting to AWX

The goal is to bootstrap BIG-IP from a terminal, then hand normal ongoing operations to AWX later.

## Prerequisites

You need:

- a workstation or jump host with this repository checked out
- Python 3
- Ansible installed
- the `f5networks.f5_modules` collection installed
- network reachability from your terminal host to the BIG-IP management interfaces
- working admin credentials on the new BIG-IP devices

Quick local checks:

```sh
python3 --version
ansible-playbook --version
ansible-galaxy collection list | rg f5networks.f5_modules
```

## How Targeting Works from the CLI

The canonical playbooks run against inventory hosts with `connection: local`.

That means:

- Ansible executes locally on your terminal host
- the target BIG-IP is chosen by the inventory host var `f5_host`
- credentials normally come from environment variables

From [vars/common.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/common.yml):

- `f5_host` is the preferred target source
- `F5_HOST` is only an environment fallback
- `F5_USERNAME`
- `F5_PASSWORD`
- optional `F5_SERVER_PORT`
- optional `F5_VALIDATE_CERTS`

## Minimum Local Inventory

Create a tiny local inventory file, for example `inventory/bootstrap.ini`:

```ini
[bootstrap]
bigip-east-sync-owner f5_host=192.0.2.10
```

For a richer YAML inventory, `inventory/bootstrap.yml` is also fine:

```yaml
all:
  hosts:
    bigip-east-sync-owner:
      f5_host: 192.0.2.10
```

Only `f5_host` is required for target selection.

## Credential Input from the Terminal

Export credentials in the shell:

```sh
export F5_USERNAME='admin'
export F5_PASSWORD='your-password'
export F5_SERVER_PORT='443'
export F5_VALIDATE_CERTS='false'
```

You do not need to export `F5_HOST` if the inventory host already provides `f5_host`.

## Two-Device HA Bootstrap Example

Example topology:

- east management IP: `192.0.2.10`
- west management IP: `192.0.2.20`
- bootstrap target: east

The repo-side HA examples already assume a one-target bootstrap perspective:

- [vars/ha/device_trust/foundation-peer.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/ha/device_trust/foundation-peer.yml)
- [vars/ha/device_groups/foundation-groups.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/ha/device_groups/foundation-groups.yml)
- [vars/ha/device_group_members/foundation-members.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/ha/device_group_members/foundation-members.yml)
- [vars/ha/traffic_groups/foundation-traffic-groups.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/ha/traffic_groups/foundation-traffic-groups.yml)
- [vars/ha/configsync_actions/manual-sync.yml](/Users/nathanielchurchill/source/ansible-bigip/vars/ha/configsync_actions/manual-sync.yml)

Those examples mean:

- target device = east
- peer device = west
- sync action pushes from east into the device group

## Bootstrap Workflow

### 1. Validate the repo first

```sh
python3 tools/validate-vars
```

### 2. Syntax-check the HA playbook

```sh
ansible-playbook --syntax-check -i inventory/bootstrap.ini playbooks/ha.yml
```

### 3. Run HA bootstrap against one device

```sh
ansible-playbook -i inventory/bootstrap.ini playbooks/ha.yml --limit bigip-east-sync-owner
```

This is the important behavior:

- Ansible runs locally on your terminal host
- the selected inventory host supplies `f5_host=192.0.2.10`
- the BIG-IP at `192.0.2.10` receives the API calls
- that device creates trust toward the west peer and pushes config sync if requested

### 4. Verify the pair manually

Check on the BIG-IP UI or CLI:

- device trust exists
- sync-failover group exists
- both members are present
- traffic group ordering looks correct
- config sync status is healthy

### 5. Apply shared config from the same bootstrap target

After HA is healthy, keep using one execution target for shared configuration:

```sh
ansible-playbook -i inventory/bootstrap.ini playbooks/network.yml --limit bigip-east-sync-owner
ansible-playbook -i inventory/bootstrap.ini playbooks/tls.yml --limit bigip-east-sync-owner
ansible-playbook -i inventory/bootstrap.ini playbooks/ltm.yml --limit bigip-east-sync-owner
```

Do not run routine shared-config jobs against both peers unless you explicitly mean to do that.

## Bootstrap Without a Local Inventory File

If you really want a one-liner without creating an inventory file, you can use an inline inventory:

```sh
ansible-playbook -i 'bigip-east-sync-owner,' playbooks/ha.yml -e f5_host=192.0.2.10
```

That works, but a real inventory file is clearer and easier to reuse.

## Minimal Terminal Session Example

```sh
cd /path/to/ansible-bigip

cat > inventory/bootstrap.ini <<'EOF'
[bootstrap]
bigip-east-sync-owner f5_host=192.0.2.10
EOF

export F5_USERNAME='admin'
export F5_PASSWORD='your-password'
export F5_SERVER_PORT='443'
export F5_VALIDATE_CERTS='false'

python3 tools/validate-vars
ansible-playbook --syntax-check -i inventory/bootstrap.ini playbooks/ha.yml
ansible-playbook -i inventory/bootstrap.ini playbooks/ha.yml --limit bigip-east-sync-owner
```

## Hand-Off to AWX Later

Once BIG-IP is initialized and AWX is safely reachable behind it:

1. Create the AWX inventory host with the same `f5_host`
2. Create the auth-only BIG-IP credential from [bigip-credential-config.yaml](/Users/nathanielchurchill/source/ansible-bigip/bigip-credential-config.yaml)
3. Point AWX templates at the same sync-owner execution host model

At that point the CLI bootstrap path and the AWX path use the same repo model:

- inventory host selects the BIG-IP target
- credential or environment provides authentication

## When to Keep Using the CLI Path

The terminal path remains useful for:

- first bring-up
- recovery when AWX is unavailable
- emergency break-glass operations
- pre-AWX lab validation

For ongoing routine operations, AWX should still be the preferred control plane once the estate is stable.
