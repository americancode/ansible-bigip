# Intent Extension Guide

This guide covers how to add a new higher-level intent or customization pattern without bloating the canonical runtime playbooks.

Use this when you want to support a new convenience pattern such as:

- a known application bundle
- a platform cluster pattern
- a repeated DNS/service pattern
- a small domain-specific customization that should compile into canonical BIG-IP objects before runtime apply/delete

The target design is always the same:

1. author intent data under `vars/<domain>/intents/<category>/...`
2. load it during `prep.yml`
3. build it into canonical BIG-IP objects
4. merge those canonical objects into the same runtime sets already consumed by `tasks/delete.yml` and `tasks/apply.yml`

## The Fast Decision Path

Use this before adding anything new.

1. Is this a brand-new BIG-IP runtime domain?
   - If yes, a new canonical playbook/domain may be justified.
   - If no, do not create a new playbook just to support a convenience pattern.

2. Is this just another first-class BIG-IP object family inside an existing domain?
   - If yes, extend the existing canonical domain and var tree.
   - Example: another LTM object type belongs in `playbooks/ltm.yml`, not a new playbook.

3. Is this a convenience pattern that should emit existing canonical objects?
   - If yes, add an intent/customization path under the existing domain.
   - Example: a cluster or application bundle that emits pools and virtual servers belongs under `vars/ltm/intents/...`.

4. Is this only a tiny one-file convenience for an already-supported inline shortcut?
   - If yes, consider whether the existing hybrid model is enough.
   - If the pattern becomes more opinionated or repeated, promote it to a dedicated intent.

Short version:

- new runtime domain: new canonical playbook only when truly necessary
- new object family in an existing domain: extend the canonical domain
- new convenience bundle: add intent/customization under the existing domain

## What New Contributors Should Usually Do

For most future additions, the correct answer is one of these:

- add first-class canonical object support to an existing playbook/domain
- add a dedicated intent/customization under an existing playbook/domain

What they should usually not do:

- create a new playbook with embedded data just because a pattern is easier to describe that way
- fork `ltm` or `gtm` behavior into a parallel “easy mode” playbook
- put domain-specific convenience logic into runtime task files

## Golden Rule

Do not teach `tasks/apply.yml` or `tasks/delete.yml` about your new shortcut shape.

Runtime tasks should continue to consume canonical objects only.

If your new pattern needs custom logic, that logic belongs in:

- `playbooks/<domain>/prep/intents/<category>/...`
- `filter_plugins/bigip_filters/...`
- `tools/validate-vars`

Also: do not create a new playbook for a convenience pattern unless you are truly introducing a new runtime domain. Convenience belongs under the existing canonical domain.

## When To Add A New Intent

Add a dedicated intent when all of these are true:

- the pattern is common enough to justify first-class support
- the operator benefit is real
- the emitted canonical objects are predictable
- the generated names and references can be deterministic
- the pattern is more opinionated than a simple inline convenience field

Do not add a dedicated intent when:

- the user really just needs first-class canonical objects
- the pattern is too open-ended to emit a stable canonical shape
- the result would hide too much ownership or reuse detail

## Directory Layout

Intent trees are category-first.

Example:

```text
vars/ltm/intents/
├── settings.yml
└── clusters/
    ├── settings.yml
    ├── rke2-east/
    │   ├── settings.yml
    │   └── platform-cluster.yml
    └── rke2-west/
        └── platform-cluster.yml
```

Matching deletion tree:

```text
vars/ltm/deletions/intents/
└── clusters/
    ├── .gitkeep
    └── rke2-east/
        └── platform-cluster.yml
```

Use category names that explain the pattern family:

- `clusters/`
- `applications/`
- `dns_services/`
- another clearly documented family name

## Settings Layering

Intent trees support layered `settings.yml` inheritance.

Valid placement points:

- `vars/<domain>/intents/settings.yml`
- `vars/<domain>/intents/<category>/settings.yml`
- `vars/<domain>/intents/<category>/<service>/settings.yml`

Precedence is:

1. object-level values in the intent file
2. deepest matching `settings.yml`
3. broader category/root intent settings
4. compiler fallback logic

Use settings for shared defaults such as:

- partition
- naming prefixes/suffixes
- common monitor/profile aliases
- common worker service defaults

Do not use settings to hide critical one-off behavior that reviewers need to see directly in the intent file.

## Implementation Steps

### 1. Define The Intent Var Tree

Create:

- `vars/<domain>/intents/<category>/settings.yml` when category defaults are useful
- one or more example files with the required YAML comment header
- matching deletion tree with `.gitkeep`

Be explicit in the example file header:

- purpose
- cross-file linkages
- supported fields
- canonical objects emitted by the compiler

### 2. Add Or Extend The Python Compiler

Put compiler logic in the split helper modules under `filter_plugins/bigip_filters/`.

Typical locations:

- `intent_ltm.py`
- `intent_gtm.py`
- a new focused module if the category is large enough

Keep `filter_plugins/bigip_var_filters.py` thin. It should only expose the filter.

Good compiler responsibilities:

- validate the minimum shape needed for compilation
- generate deterministic canonical object names
- rewrite shorthand references into canonical object references
- attach source-trace metadata like `__source_file` where useful
- preserve deletion behavior by emitting canonical objects with `state: absent`

Do not put playbook orchestration or module calls into the compiler.

### 3. Expose The Filter

Export the new function from:

- `filter_plugins/bigip_filters/__init__.py`
- `filter_plugins/bigip_var_filters.py`

The playbook should call the filter through normal Ansible/Jinja usage, not by invoking Python directly.

### 4. Add Focused Prep Snippets

Create intent prep snippets under:

```text
playbooks/<domain>/prep/intents/<category>/
```

Typical files:

- `load-<intent-name>.yml`
- `build-<intent-name>.yml`

Keep responsibilities split:

- `load-*.yml` discovers and aggregates raw intent objects
- `build-*.yml` emits canonical objects

Use shared recursive discovery and layered settings behavior. Do not re-introduce one-off loader patterns.

### 5. Patch The Main Prep Flow

Wire the new snippets into the main domain prep orchestrator.

Typical pattern:

1. load canonical objects
2. load intent objects
3. build intent into canonical objects
4. rebuild any lookup structures that need the compiled objects
5. publish final `*_present` and `*_delete` runtime collections

The repo filename convention is `build-*.yml` even when the step is conceptually “compiling” intent into canonical objects.

The top-level `prep.yml` comment block should mention the resulting runtime sets if they materially change.

### 6. Merge Into Canonical Runtime Sets

The compiler output must end up merged into the canonical collections already used by runtime tasks, such as:

- `ltm_virtual_servers`
- `ltm_pools`
- `gtm_wide_ips`
- `gtm_pools`

Do not create a second runtime surface like `ltm_rke2_virtual_servers_present` for task execution.

Intent output should disappear into the canonical model before runtime task files are reached.

### 7. Update Validation

Update `tools/validate-vars` to cover:

- the new intent tree itself
- field validation for the intent shape
- post-compilation reference expectations where appropriate

The validator should stay aligned with the compiler logic. If possible, share the same Python helper functions rather than duplicating the rules in two places.

### 8. Update Docs

At minimum update:

- `docs/intent-authoring.md`
- `docs/example-models.md`
- `docs/playbook-structure.md`
- `docs/var-layout.md`
- `README.md`
- `AGENTS.md` if the new category or pattern changes the repo-wide rule set

If the pattern is large or likely to be reused as a template for future work, add a dedicated doc section or example walkthrough.

## Recommended File Pattern

For a new `applications` intent under LTM:

```text
vars/ltm/intents/applications/
├── settings.yml
└── storefront/
    └── app.yml

playbooks/ltm/prep/intents/applications/
├── load-application-intents.yml
└── build-application-intents.yml

filter_plugins/bigip_filters/
└── intent_ltm.py
```

## Compiler Design Rules

### Keep Names Deterministic

Generated object names must be reproducible from the same input.

Avoid:

- random suffixes
- environment-dependent naming
- hidden counters based on load order

Prefer explicit formulas like:

- `pool_<intent.name>_api_6443`
- `vs_<intent.name>_console_443`

### Keep Ownership Visible

Reviewers should still be able to answer:

- what canonical objects will exist
- which intent file emitted them
- how the generated names are formed

If the pattern hides too much, it is probably too magical.

### Keep Delete Behavior Symmetric

Every intent that emits canonical objects must preserve deletion behavior.

That means deletion entries under `vars/<domain>/deletions/intents/...` must compile into the same generated canonical objects, but with `state: absent`.

### Keep Shared Objects Honest

If the pattern really needs reusable shared pools, profiles, or monitors owned elsewhere, do not force them into the intent.

Use canonical trees directly when shared ownership matters more than convenience.

## When To Use Python vs YAML

Use Python when the logic answers:

- what objects should exist
- how names are generated
- how defaults are layered into emitted objects
- how shorthand expands into canonical references

Keep logic in playbooks when it answers:

- when to load a tree
- when to compile it
- when to rebuild a lookup
- in what order prep steps should run

Short version:

- playbooks orchestrate
- Python transforms

## Example Patch Sequence

For a new GTM intent:

1. add `vars/gtm/intents/dns_services/...`
2. add `settings.yml` for the category if useful
3. extend `filter_plugins/bigip_filters/intent_gtm.py`
4. expose the filter through `__init__.py` and `bigip_var_filters.py`
5. add `playbooks/gtm/prep/intents/dns_services/load-*.yml`
6. add `playbooks/gtm/prep/intents/dns_services/build-*.yml`
7. import those snippets from `playbooks/gtm/prep.yml` or the relevant sub-flow
8. merge compiled output into `gtm_pools` and `gtm_wide_ips`
9. update `tools/validate-vars`
10. update example docs and README links
11. run validation

## Validation Commands

After adding a new intent/customization path, run at least:

```sh
python3 tools/validate-vars
ansible-playbook --syntax-check playbooks/<domain>.yml
make validate
```

If Python helpers changed, also run:

```sh
python3 -m py_compile filter_plugins/bigip_var_filters.py filter_plugins/bigip_filters/*.py tools/validate-vars
```

## Anti-Patterns

Avoid these:

- adding new runtime task branches for every shortcut
- putting compiler logic into `tasks/apply.yml`
- emitting non-deterministic names
- creating intent trees without deletion support
- documenting only the intent input but not the emitted canonical objects
- writing a convenience model that validator or docs do not understand

## Current Working Example

Use the implemented RKE2 intent as the working reference:

- var tree:
  - `vars/ltm/intents/clusters/rke2-east/platform-cluster.yml`
  - `vars/ltm/intents/clusters/settings.yml`
- prep wiring:
  - `playbooks/ltm/prep/intents/clusters/load-rke2-server-intents.yml`
  - `playbooks/ltm/prep/intents/clusters/build-rke2-server-intents.yml`
- compiler:
  - `filter_plugins/bigip_filters/intent_ltm.py`

That path is the template future intent work should follow unless the repo documents a reason to differ.
