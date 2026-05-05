# Documentation Index

Use this page when you know what you need to do but do not yet know which document owns it.

## Start Here

| Goal | Read This First | Then |
|---|---|---|
| Run the platform through AWX | [01-awx-operating-model-and-handoff.md](01-awx-operating-model-and-handoff.md) | [awx-setup.md](awx-setup.md), [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md), [04-awx-job-execution.md](04-awx-job-execution.md), [05-ha-execution-model.md](05-ha-execution-model.md) |
| Bootstrap or recover when AWX cannot be first | [02-bootstrap-playbook.md](02-bootstrap-playbook.md) | [cli-bootstrap-and-recovery.md](cli-bootstrap-and-recovery.md) |
| Understand repo structure | [playbook-structure.md](playbook-structure.md) | [var-layout.md](var-layout.md), [example-models.md](example-models.md) |
| Edit objects in an existing domain | domain doc for that playbook | [validation.md](validation.md), [deletion-workflows.md](deletion-workflows.md) |
| Add a new intent | [intents/how-to-build-intents.md](intents/how-to-build-intents.md) | [extending-the-repo.md](extending-the-repo.md) |
| Add a new object type or runtime domain | [extending-the-repo.md](extending-the-repo.md) | [playbook-structure.md](playbook-structure.md), [var-layout.md](var-layout.md) |
| Check helper-tool coverage or brownfield workflow | [drift-import.md](drift-import.md) | [validation.md](validation.md) |

## AWX-First Operator Path

AWX is the primary control plane for normal operations.

1. [01-awx-operating-model-and-handoff.md](01-awx-operating-model-and-handoff.md)
2. [awx-setup.md](awx-setup.md)
3. [03-awx-inventory-and-targeting.md](03-awx-inventory-and-targeting.md)
4. [04-awx-job-execution.md](04-awx-job-execution.md)
5. [05-ha-execution-model.md](05-ha-execution-model.md)

Use [cli-bootstrap-and-recovery.md](cli-bootstrap-and-recovery.md) only when AWX cannot safely be the first control plane or when you are in a break-glass path.

## Domain Guides

| Playbook | Domain Doc | Supplemental Docs |
|---|---|---|
| `playbooks/bootstrap.yml` | [02-bootstrap-playbook.md](02-bootstrap-playbook.md) | [01-awx-operating-model-and-handoff.md](01-awx-operating-model-and-handoff.md) |
| `playbooks/network.yml` | [network-objects.md](network-objects.md) | [deletion-workflows.md](deletion-workflows.md) |
| `playbooks/system.yml` | [system-management.md](system-management.md) | [authentication.md](authentication.md) |
| `playbooks/ha.yml` | [ha.md](ha.md) | [05-ha-execution-model.md](05-ha-execution-model.md) |
| `playbooks/ltm.yml` | [ltm.md](ltm.md) | [ltm-advanced.md](ltm-advanced.md), [intents/ltm-inline-virtual-server-intents.md](intents/ltm-inline-virtual-server-intents.md) |
| `playbooks/gtm.yml` | [gtm.md](gtm.md) | [gtm-advanced.md](gtm-advanced.md), [intents/gtm-wide-ip-intents.md](intents/gtm-wide-ip-intents.md) |
| `playbooks/tls.yml` | [tls.md](tls.md) | [tls-secrets.md](tls-secrets.md) |
| `playbooks/security.yml` | [security.md](security.md) | [waf.md](waf.md), [apm.md](apm.md), [authentication.md](authentication.md), [kerberos-sso.md](kerberos-sso.md) |

## Contributor Paths

### I need to change an existing domain

1. Read the domain doc.
2. Check [playbook-structure.md](playbook-structure.md) for the split layout contract.
3. Check [var-layout.md](var-layout.md) for tree shape, settings inheritance, and deletions.
4. Run [validation.md](validation.md) before and after the change.
5. If helper-tool coverage should exist for that object family, update [drift-import.md](drift-import.md)-covered tooling too.

### I need to add a new convenience model

1. Decide whether it is a canonical object family or an intent.
2. If it is a convenience layer, start with [intents/how-to-build-intents.md](intents/how-to-build-intents.md).
3. Use [extending-the-repo.md](extending-the-repo.md) to update validation, docs, and helper-tool expectations.

### I need to add a new runtime domain

Start with [extending-the-repo.md](extending-the-repo.md). That guide covers the required repo surfaces and the expected documentation, validation, drift, and import updates.
