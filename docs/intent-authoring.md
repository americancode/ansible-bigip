# Intent Authoring and Compiler Design

This document defines how the repo should support higher-level convenience authoring without turning the canonical runtime playbooks into unmaintainable special-case engines.

The design goal is:

- keep runtime playbooks stable and object-focused
- allow simpler authoring for common service patterns
- compile convenience intent into the same canonical BIG-IP object model already used for apply and delete operations

## Why This Exists

The repo was designed for enterprise-scale, first-class BIG-IP object management. That is the right long-term model for reuse, ownership boundaries, drift tooling, and reviewability.

However, operators also need a simpler path for known patterns such as:

- "I just need a standard app VIP with a pool and members"
- "I just need a Wide IP with a reasonable default pool model"
- "I do not want to hand-author every related child object for a very common case"

The existing LTM and GTM shortcut paths solve some of that today, but they should not keep expanding inside runtime task logic.

## Design Principles

### Canonical Runtime Stays Canonical

`playbooks/ltm.yml`, `playbooks/gtm.yml`, and other runtime playbooks should operate on normalized first-class BIG-IP objects only.

That means runtime tasks should continue to manage objects such as:

- `ltm_virtual_servers`
- `ltm_pools`
- `ltm_nodes`
- `gtm_wide_ips`
- `gtm_pools`
- `gtm_servers`

Runtime `apply.yml` and `delete.yml` files should not keep gaining more branches for every convenience model.

### Intent Is Optional And Compiles Ahead Of Runtime

Convenience authoring belongs in an intent layer that is expanded before runtime execution.

The intended flow is:

1. load canonical var trees
2. load intent var trees
3. compile intent into canonical objects
4. merge the compiled objects into the same normalized data structures the runtime tasks already consume
5. run runtime apply/delete tasks against canonical objects only

### Canonical Objects Remain The Apply/Delete Contract

Intent is an authoring convenience, not a second runtime surface.

The canonical object model remains:

- the only thing runtime tasks should manage
- the only thing delete ordering should be based on
- the stable contract for future helper-tool lifecycle work

## Proposed Repo Structure

The recommended first structure is:

- `vars/ltm/intents/`
- `vars/gtm/intents/`

If later needed for cross-domain compositions:

- `vars/platform_apps/`

The expected implementation boundary is:

- var files describe intent
- `prep.yml` discovers them
- focused `prep/*.yml` snippets can own individual compilers for specific patterns
- a compiler layer normalizes them into canonical objects
- runtime tasks remain unchanged except for consuming the normalized canonical sets

## Compiler Layer

The preferred compiler location is a dedicated Python normalization layer, not more Jinja branching in runtime tasks.

Good homes for this logic are:

- `filter_plugins/bigip_var_filters.py` if the compiler remains small and close to playbook prep
- a dedicated Python helper module if the compiler surface grows and needs clearer structure

The compiler should:

- accept a high-level intent object
- emit canonical BIG-IP objects
- keep object naming deterministic
- keep partition behavior explicit
- avoid mutating runtime semantics

## Naming And Ownership Rules

Intent compilers must not hide ownership too aggressively.

Required behaviors:

- generated canonical object names must be deterministic and documented
- generated objects must still be traceable back to the source intent file
- docs and examples must show which canonical objects are emitted
- settings precedence must remain explicit

If a team needs strict control of object names, monitors, profiles, or reuse boundaries, they should keep using the canonical object trees directly.

## Validation Model

Validation should eventually cover both layers:

- validate the intent input shape
- validate the compiled canonical object shape
- validate cross-object references after compilation

The important rule is that a convenience model must compile into canonical objects that would also pass validation if authored directly.

## Drift And Import Expectations

Helper tools should continue to treat the canonical object model as the primary lifecycle surface unless the roadmap explicitly expands them to understand intent directly.

That means the default expectation is:

- drift/import work is based on canonical objects
- intent is an authoring abstraction, not a separate live BIG-IP object family

If helper tools later gain intent awareness, that should be explicitly documented as additional fidelity rather than assumed.

## Existing Shortcuts

The current concise LTM and GTM patterns are transitional and should be treated as early intent-like behavior:

- LTM inline pool/member authoring under a virtual server
- GTM inline pool authoring under a Wide IP
- GTM pool member address/port derivation from repo-known LTM virtual servers

The roadmap direction is to refactor those patterns into the new intent/compiler design rather than extending them in-place inside runtime logic.

## First Refactor Targets

The first two refactor targets were:

1. LTM concise inline app-service behavior
2. GTM concise inline Wide IP / pool behavior

Those paths now compile into canonical pools, virtual servers, and Wide IP pool references during `prep.yml` instead of depending on mixed-shape runtime task logic.

The next goal is not to add more convenience cases first. The next goal is to reuse this compiler pattern for any future simple-mode authoring without expanding runtime branching again.

## When To Use Which Model

Use the canonical object trees when:

- shared objects matter
- teams own different layers
- explicit object naming and reuse are important
- drift/import clarity is more important than brevity

Use intent authoring when:

- one common service pattern should be easy to declare
- the operator wants fewer files and less raw BIG-IP object ceremony
- the emitted canonical object model is still acceptable for review and lifecycle management

## Non-Goals

This design is not trying to:

- replace the canonical object model
- make every possible use case "simple mode"
- bypass the repo's delete ordering, validation, or object ownership rules
- create a separate runtime playbook for every convenience pattern

## Implementation Rule

Before adding another convenience shortcut directly into `ltm` or `gtm` runtime logic:

- either refactor the current shortcut path into the intent/compiler layer first
- or document in the roadmap why the runtime exception is justified
