# Studio ↔ Live Valheim --- Closed Creator Loop

## Objective

Make creation feel like a live development loop rather than disconnected
tools.

`Describe/Edit → Validate → Rehearse → Play Revision → Hot-load → Observe → Revise → Update in Game`

Normal revisions should not require restarting Valheim.

## Existing Foundation

The pieces already exist in partial form: structured artifacts,
validation/publication, Studio graph and certified JSON, mod-side
loading, runtime content-update lifecycle, Arcane Sight,
versions/rollback concepts, Quest Lab, Playwright, and broader automated
tests.

This is primarily integration and attenuation.

## Rehearse as Development Deployment

Separate:

**Author:** mutable work in progress.

**Rehearse:** a specific revision activated for a development
player/world/session and rapidly supersedable.

**Publish:** an explicit durable revision intended for others.

Development revisions must not pollute the public catalog.

## Primary Action

Studio should eventually offer **Play this revision**.

Underneath it may validate, compile/package, identify the development
target, transfer content, activate the revision, receive
acknowledgement, and correlate Arcane Sight evidence. The creator should
not need to know those internal steps.

## Revision Contract

Define artifact ID, immutable revision ID, active development revision,
published revision, runtime instance/run ID, replacement semantics,
restart/resume semantics, and rollback.

Prefer immutable revisions plus explicit activation.

## Runtime Receipt

A successful push should produce evidence such as:

``` text
Artifact: palisade-defense
Revision: r18
Target: local Valheim / current world
Validation: PASS
Transfer: PASS
Activation: PASS
Runtime observed: PASS
Previous revision: r17
```

Failures should preserve the previous known-good state where possible.

## Return Path

Studio/Rehearse should eventually know which revision is active, whether
the game is connected, current stage, recent important event, and
whether runtime rejected anything.

Do not duplicate all Arcane Sight telemetry immediately. Start with
correlation/status and promote evidence only when real authoring laps
show value.

## AI-Assisted Loop

Example request: "Change wave two from five greydwarfs to eight and give
relief if combat lasts more than eight minutes."

Agent modifies canonical artifact, validates, creates a semantic diff
and revision. Studio shows the change and offers Play this revision.
Runtime activates it without restart.

## End-to-End Test

Automate: validate r1, activate it, observe expected behavior, create
r2, activate r2 without restart, verify r2, roll back to r1, verify
rollback, then publish a selected revision independently.

## Scope Control

Do not generalize into a fleet deployment platform yet.

First prove: **one creator, one active Valheim development session, one
Event, repeated revisions, seconds-scale feedback, trustworthy
receipts.**

## Success Condition

The creator can spend an hour iterating on an Event without restarting
Valheim, manually moving files, remembering hotkeys, or wondering which
revision is running.
