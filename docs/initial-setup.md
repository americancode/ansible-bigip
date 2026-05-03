# Initial Setup and Handoff

This guide documents the full path from a brand-new BIG-IP appliance to normal Git-managed operation with this repository.

It exists to answer a different question than the narrower bootstrap docs:

- [bootstrap.md](bootstrap.md) explains the day-0 playbook itself
- [cli-bootstrap.md](cli-bootstrap.md) explains how to run bootstrap from a terminal
- [awx-ha-bootstrap.md](awx-ha-bootstrap.md) explains how to run HA setup from AWX once BIG-IP is reachable

This document is the high-level sequence that ties those pieces together.

## Intended Outcome

At the end of this process:

- the BIG-IP is licensed
- the management interface is reachable on its long-lived IP
- inventory or AWX host vars point at that stable management endpoint
- base system settings are managed through Git
- HA is established if the device belongs to a pair
- routine `network`, `system`, `tls`, `ltm`, `gtm`, and `security` changes are made through GitOps workflows instead of ad hoc device edits

## Phase 0: First-Boot Prerequisites

Before this repo can manage a brand-new appliance, a few things still need to be true on the box itself.

These are outside the repo’s current automation boundary:

- the device is powered on and reachable on some temporary management address
- you can authenticate with an administrative account
- the REST API is reachable from your jump host or controller
- any platform-specific hypervisor, cloud, or hardware bring-up steps are already complete

For this repo, the practical minimum is:

- a temporary or factory management IP you can reach
- admin credentials you can use for the first run
- a jump host or terminal environment with Ansible and the F5 collection installed

## Phase 1: Choose the First Control Plane

Decide whether the first run should be:

- CLI-first
- AWX-first

Use CLI-first when:

- AWX is not reachable yet
- AWX itself depends on BIG-IP being configured first
- you are bringing up a new lab, VE, or isolated pair

Use AWX-first only when:

- BIG-IP is already reachable on a stable management endpoint
- AWX can safely connect to it now
- the chicken-and-egg problem does not apply

In most brand-new environments, CLI-first is the correct choice.

## Phase 2: Day-0 Bootstrap

Use `playbooks/bootstrap.yml` to seed the minimum stable state:

- licensing
- first management IP CIDR
- first management default route

Author the day-0 vars in:

- `vars/bootstrap/license/`
- `vars/bootstrap/management/`

Run the bootstrap from the CLI path in [cli-bootstrap.md](cli-bootstrap.md).

Important cutover rule:

- if `bootstrap_management[*].address` changes the management IP, update the inventory host var `f5_host` before running the next playbook

That management address becomes the durable endpoint this repo should target going forward.

## Phase 3: Base Device Configuration

Once the management endpoint is stable, move to `playbooks/system.yml`.

This is where the day-1/day-2 device baseline begins:

- hostname
- DNS
- NTP
- provisioning
- local users
- optional centralized admin auth providers for BIG-IP operator login
- config save behavior

Author those objects in:

- `vars/system/hostname/`
- `vars/system/dns/`
- `vars/system/ntp/`
- `vars/system/provisioning/`
- `vars/system/users/`
- `vars/system/auth/`
- `vars/system/config/`

Important boundary:

- `vars/system/auth/` is for BIG-IP management-plane administrator login
- APM end-user identity, access policy, and backend SSO stay under `vars/security/apm/`

This is the point where the repo stops being a narrow bootstrap tool and starts becoming the system of record.

## Phase 4: HA Setup If Applicable

If the appliance belongs to an HA pair, establish HA next with `playbooks/ha.yml`.

Author HA state in:

- `vars/ha/device_trust/`
- `vars/ha/device_groups/`
- `vars/ha/device_group_members/`
- `vars/ha/traffic_groups/`
- `vars/ha/configsync_actions/`

Operational rule:

- apply HA from one designated execution target
- keep that same sync-owner target for most shared configuration afterward

If the device is standalone, skip this phase.

## Phase 5: Shared Service Configuration

After bootstrap and base system setup are complete, apply the service domains as needed:

- `playbooks/network.yml`
- `playbooks/tls.yml`
- `playbooks/ltm.yml`
- `playbooks/gtm.yml`
- `playbooks/security.yml`

At this point, most ongoing configuration change should be Git-driven:

- update var files
- validate locally or in CI
- apply from the correct execution target
- let HA sync handle peer replication where appropriate

## Handoff to AWX

Move to AWX after all of the following are true:

- BIG-IP is licensed
- the stable management IP is known
- AWX can route to that management endpoint
- credentials are stored in the AWX BIG-IP auth credential
- inventory host vars set `f5_host` to the stable management endpoint

Recommended handoff model:

1. CLI runs `playbooks/bootstrap.yml`
2. CLI optionally runs `playbooks/system.yml` and `playbooks/ha.yml` for first stabilization
3. AWX takes over for routine operations after reachability and ownership are clear

See:

- [awx-operation.md](awx-operation.md)
- [awx-ha-bootstrap.md](awx-ha-bootstrap.md)

## What Is Still Manual

Even with the new bootstrap playbook, this repo does not yet automate every possible first-boot action.

Still outside current automation scope:

- appliance power-on and platform provisioning
- hypervisor or cloud instance creation
- factory credential recovery
- any console-only recovery path if the management API is not reachable at all

That boundary is intentional. The repo begins at the point where Ansible can talk to the BIG-IP management API.

## Recommended Operator Sequence

For a brand-new pair, the practical sequence is:

1. perform the platform-specific first-boot steps until the management API is reachable
2. use the CLI path to run `playbooks/bootstrap.yml`
3. update `f5_host` if the management IP changed
4. run `playbooks/system.yml`
5. run `playbooks/ha.yml` from the designated bootstrap/sync-owner device
6. verify trust, sync health, and management reachability
7. hand off routine operations to AWX
8. manage ongoing changes through Git-backed playbook runs

## Source of Truth Boundary

After the handoff point, the repo should be treated as the authoritative source of intended state.

That means:

- avoid manual edits on the BIG-IP unless you are in a break-glass scenario
- if emergency manual changes are made, reconcile them back into Git
- use drift tooling where available for the domains that already have helper-tool coverage

The bootstrap domain remains the exception: it is a day-0 setup mechanism, not a normal ongoing lifecycle surface.
