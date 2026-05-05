# AWX Operating Model and Handoff

This is the primary operator path for bringing a BIG-IP under Git management with this repository.

The broad operating assumption is:

- AWX is the normal control plane
- Git is the source of truth
- the CLI exists for bootstrap, break-glass recovery, or AWX-unavailable situations

Use this document first. The rest of the numbered docs explain the normal AWX operating path in smaller pieces:

- [02-bootstrap-playbook.md](02-bootstrap-playbook.md) explains why `playbooks/bootstrap.yml` exists and what it manages
- [awx-setup.md](awx-setup.md) is the concrete AWX build sheet for projects, inventory, credentials, and templates
- [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md) explains AWX inventory, credentials, and target selectors
- [04-awx-job-execution.md](04-awx-job-execution.md) explains how to structure AWX job templates and execution boundaries
- [05-ha-execution-model.md](05-ha-execution-model.md) explains how HA setup and shared-config execution should work

The CLI fallback path lives outside the numbered operator story in [cli-bootstrap-and-recovery.md](cli-bootstrap-and-recovery.md).

## Intended Outcome

At the end of this process:

- the BIG-IP is licensed and reachable on its stable management IP
- AWX inventory host vars point at that stable management endpoint through `f5_host`
- base system settings are managed through Git
- HA is established if the device belongs to a pair
- routine `network`, `system`, `tls`, `ltm`, `gtm`, and `security` changes are made through AWX-backed GitOps workflows instead of ad hoc device edits

## Short Version

The normal path is:

1. get the factory or temporary management endpoint reachable
2. use `playbooks/bootstrap.yml` only if the device still needs licensing or a stable management IP
3. set or update AWX inventory host var `f5_host` to the stable management endpoint
4. use AWX to apply `playbooks/system.yml` for the device baseline
5. if this is an HA pair, use AWX to apply `playbooks/ha.yml` from one designated sync-owner target
6. verify reachability, trust, and sync health
7. use AWX for ongoing `system`, `network`, `tls`, `ltm`, `gtm`, and `security` changes

That sequence is the reason `bootstrap` is a separate playbook: it handles the one-time cutover into a stable management endpoint before the normal AWX-driven lifecycle begins.

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

## Phase 1: Decide Whether Bootstrap Is Needed

AWX is the preferred control plane, but it cannot be the first hop if the device is still unreachable, unlicensed, or using a temporary management endpoint.

Use bootstrap first when:

- the BIG-IP still needs licensing
- the current management IP is temporary or factory-assigned
- AWX cannot safely route to the device yet
- AWX itself depends on the BIG-IP estate you are standing up

Skip bootstrap and start in AWX only when:

- the BIG-IP is already reachable on its long-lived management endpoint
- AWX can connect to it now
- the day-0 cutover problem does not apply

## Phase 2: Day-0 Bootstrap

Use `playbooks/bootstrap.yml` to seed the minimum stable state:

- licensing
- first management IP CIDR
- first management default route

Author the day-0 vars in:

- `vars/bootstrap/license/`
- `vars/bootstrap/management/`

If AWX cannot safely be the first control plane, run bootstrap from the fallback path in [cli-bootstrap-and-recovery.md](cli-bootstrap-and-recovery.md).

Important cutover rule:

- if `bootstrap_management[*].address` changes the management IP, update the inventory host var `f5_host` before running the next playbook

That management address becomes the durable endpoint this repo should target going forward.

Bootstrap is intentionally narrow. It is not the long-term system baseline playbook. Its job is only to get the device licensed and reachable at the correct management endpoint so the normal lifecycle can begin cleanly.

## Phase 3: Base Device Configuration

Once the management endpoint is stable, move to `playbooks/system.yml`.

This is where the day-1/day-2 device baseline begins:

- hostname
- DNS
- NTP
- provisioning
- local users
- optional centralized admin auth providers for BIG-IP operator login
- optional login banner compliance messaging
- config save behavior

Author those objects in:

- `vars/system/hostname/`
- `vars/system/dns/`
- `vars/system/ntp/`
- `vars/system/provisioning/`
- `vars/system/users/`
- `vars/system/auth/`
- `vars/system/login_banners/`
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
2. inventory host var `f5_host` is updated to the stable management endpoint if bootstrap changed it
3. AWX takes over for `system.yml`, `ha.yml`, and routine service-domain operations after reachability and ownership are clear

Recommended AWX ownership after handoff:

- keep one inventory host per execution target with `f5_host` set to the stable management endpoint
- for an HA pair, keep one default sync-owner target for shared-config jobs
- use AWX for routine `system`, `network`, `tls`, `ltm`, `gtm`, and `security` changes after the bootstrap/sync-owner target is established

See:

- [awx-setup.md](awx-setup.md)
- [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md)
- [04-awx-job-execution.md](04-awx-job-execution.md)
- [05-ha-execution-model.md](05-ha-execution-model.md)

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
2. use the CLI fallback path to run `playbooks/bootstrap.yml`
3. update `f5_host` if the management IP changed
4. move to AWX inventory and templates
5. run `playbooks/system.yml`
6. run `playbooks/ha.yml` from the designated bootstrap/sync-owner device
7. verify trust, sync health, and management reachability
8. manage ongoing changes through AWX

For a standalone device, the same path applies without step 6.

## Source of Truth Boundary

After the handoff point, the repo should be treated as the authoritative source of intended state.

That means:

- avoid manual edits on the BIG-IP unless you are in a break-glass scenario
- if emergency manual changes are made, reconcile them back into Git
- use drift tooling where available for the domains that already have helper-tool coverage

The bootstrap domain remains the exception: it is a day-0 setup mechanism, not a normal ongoing lifecycle surface.
