# Arcane Sight --- Runtime Observability and Spatial Debugging

## Role

Arcane Sight is the in-world runtime debugger for authored experiences.
It answers: what machinery exists around me, which version is active,
who owns it, what am I bound to, what just happened, which condition
matched, which transition fired, and why?

It is not primarily a tutorial and it is not the main authoring surface.

## Current Gold Baseline

The first pass already demonstrates the correct model: an in-game
runtime drawer, spatial labels, artifact/version/owner information,
active versus other-version distinction, distances, binding counts, the
Look → Validate → Load → Confirm lifecycle, captures/outcomes, and
versions/rollback.

This is enough to begin real usage before deeper refinement.

## Architecture Boundary

Arcane Sight should inspect the existing normalized pipeline:

`Game/ZDO observations → normalized creator events → spatial/generalized semantics → evaluator/runtime`

It must not invent a parallel event model.

## Next Work

### Stable runtime identity

Every visible runtime object should expose artifact ID, immutable
revision/version, instance/run ID, owner, world/server, spatial anchor
or ZDO identity where relevant, and loaded/active/stale state.

### Event evidence

Drill into recent evidence: event observed, source, target, spatial
relationship, condition evaluation, transition selected, action
executed, timestamp, and correlation/run ID.

### Spatial semantics

Formalize area-aware matching: chat/shout within N meters, player
enters/leaves area, combat persists within region, object destroyed
inside encounter bounds, or matching entity count crosses a threshold.

Area-of-effect should be a reusable semantic primitive, not custom logic
for each Event.

### Visual attenuation

Do not solve label density speculatively. Build real Events first. Add
nearest-only, active-only, owned-only, type/radius filters, grouping, or
selected-object focus only when actual use demonstrates the need.

### Studio correlation

Studio and Arcane Sight must share IDs and revision semantics so an
author can move from:

`Studio artifact → live instance → runtime evidence → exact Studio node`

without interpretation.

## Validation Lap

Build a real multi-stage Event and use Arcane Sight for every debugging
decision. Record every moment where the author cannot answer "what
happened and why?" from the current surface. Those failures become the
backlog.

## Success Condition

An author can stand inside a live Event, identify the active
artifact/revision, inspect its spatial/runtime state, see why the last
transition occurred, and correlate that evidence back to authored
structure without restarting the game or opening external logs.
