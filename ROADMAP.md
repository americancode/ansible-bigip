# BIG-IP Enterprise GitOps Roadmap

## To Do

3. Refactor `tools/validate-vars.py` into a modular package.

4. Refactor `tools/drift-check.py` into a modular package.

5. Refactor `tools/import-from-bigip.py` into a modular package.

6. Add UCS backup and export workflow support.

7. Add certificate rotation and renewal detection.

8. Improve helper-tool fidelity where `basic field drift` is no longer sufficient.

## Proposals

1. Split high-risk `system` functionality into narrower playbooks if AWX blast radius still feels too broad.
   - `system-auth`
   - `system-identity`
   - `system-provisioning`
   - `system-users`
   - `system-partitions`
   - `system-banner`

2. Split `ha` into narrower playbooks if shared vs device-local operations need harder execution boundaries.
   - `ha-device-local`
   - `ha-shared`

3. If selector-based targeting becomes too noisy or risky, prefer host-scoped var files or host-specific overlays instead of embedding `target_hosts` and `target_groups` on every object.

4. Add future dedicated domains only if they become operationally distinct enough to justify them.
   - backup or snapshot workflows
   - certificate lifecycle workflows
   - observability workflows
   - deeper WAF content lifecycle
   - brownfield onboarding or promotion workflows
