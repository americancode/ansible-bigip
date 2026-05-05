# How To Build Intents

This is the single implementation guide for building new intent types.

Intent authoring is an abstraction layer. Runtime playbooks still apply and delete canonical BIG-IP objects.

## Rules

- Keep runtime tasks canonical-only (`tasks/apply.yml`, `tasks/delete.yml`).
- Add convenience behavior in prep/compiler layers, not runtime module tasks.
- Put intent vars under `vars/<domain>/intents/<category>/...`.
- Put intent deletion vars under `vars/<domain>/deletions/intents/<category>/...`.
- Make ownership explicit in schema (`inline` vs `reference` style fields).
- Reject ownership collisions in validation; do not silently dedupe.

## Implementation Path

1. Define intent schema and examples under `vars/<domain>/intents/<category>/...`.
2. Add layered defaults with `settings.yml` where needed.
3. Implement compiler logic in `filter_plugins/bigip_filters/` and expose via `filter_plugins/bigip_var_filters.py`.
4. Add prep snippets under `playbooks/<domain>/prep/intents/<category>/`:
   - `load-*.yml` for discovery/aggregation
   - `build-*.yml` for compilation into canonical objects
5. Merge compiled output into canonical runtime collections used by apply/delete.
6. Extend `tools/validate-vars.py` coverage for:
   - intent schema shape
   - ownership/reference constraints
   - compiled canonical collision rules
7. Update intent class docs in this folder.

## Required Structure

- `vars/<domain>/intents/<category>/...`
- `vars/<domain>/deletions/intents/<category>/...`
- `playbooks/<domain>/prep/intents/<category>/load-*.yml`
- `playbooks/<domain>/prep/intents/<category>/build-*.yml`
- `docs/intents/<intent-class>.md`

## Current Intent Classes

- [LTM Inline Virtual Server Intents](ltm-inline-virtual-server-intents.md)
- [GTM Wide IP Intents](gtm-wide-ip-intents.md)
