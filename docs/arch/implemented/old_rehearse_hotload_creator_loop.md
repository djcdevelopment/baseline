# Rehearse, Hot-Load, and the Closed Creator Loop

## Objective

Turn the functional but fragmented web-to-Valheim workflow into a
coherent creator experience.

The capability already exists: create content in the web tooling,
validate it, publish it, invoke the mod controls, load the content, and
exercise it successfully.

The problem is not whether the path works. The problem is that the
creator currently has to know the path.

> Create or generate → Validate → Rehearse → Play this revision →
> Hot-load into Valheim → Observe → Revise → Update in game.

Normal iteration should not require restarting Valheim.

## Reframe Rehearse

Rehearse should become the controlled development deployment lane
between authoring and durable publication.

**Author:** content is being created or modified and may change rapidly.

**Rehearse:** a specific development revision is deployed to a known
player/world/session, can be replaced repeatedly, and returns runtime
evidence to the creator surface.

**Publish:** a validated revision becomes durable content intended for
broader consumption.

This permits aggressive iteration without polluting the published
catalog.

## Core experience

Before deployment:

``` text
Palisade Defense
Revision 18

Validation: Ready
4 stages
3 runtime triggers
1 success outcome
1 failure outcome
All references resolved

[Play this revision]
```

After deployment:

``` text
Active in Valheim
Player: <active character>
World: <development world>
Revision: 18
Loaded: 2 seconds ago
Current stage: Wave 1
```

The creator should not need to know which hotkey rescans files, where a
payload was written, or which subsystem performed the transfer.

## Hot-load as a first-class capability

Hot-loading is central to creator iteration speed.

Target properties:

-   No game restart for ordinary revisions.
-   No relog where avoidable.
-   Explicit revision identity.
-   Positive acknowledgement from the mod/runtime.
-   Clear failure state.
-   Safe replacement of a development revision.
-   Defined behavior when an active revision is replaced.
-   Ability to return to a known-good revision.
-   Separation between development deployment and publication.

Buttons should describe creator intent: **Play this revision**, **Update
in game**, or equivalent. Implementation details belong underneath.

## Close the loop back to web

Web → game is only half the experience. Runtime evidence should return
to Studio/Rehearse.

Useful signals:

-   Connected player and world.
-   Artifact ID and active revision.
-   Load acknowledgement.
-   Current stage/node.
-   Transition taken.
-   Trigger/event observed.
-   Action executed.
-   Validation/runtime error.
-   Terminal outcome.
-   Timestamps and run/correlation ID.

The creator should be able to answer: **What happened, and why?**

## Progressive drill-down

### Level 1 --- Simple

``` text
Revision 18 is active.
Wave 2 is running.
3 enemies remain.
```

### Level 2 --- Structured

Show current stage, satisfied/unsatisfied conditions, recent actions,
next possible transitions, and terminal outcomes.

### Level 3 --- Graph

Highlight the active node/path and recent transitions.

### Level 4 --- Runtime evidence

Expose raw event history, IDs, timestamps, payloads, and diagnostic
details.

The creator should only pay the complexity cost when needed.

## Revision semantics

Define explicitly:

-   Artifact identity versus revision identity.
-   Whether deployed revisions are immutable.
-   How a newer development revision supersedes an older one.
-   Whether active state migrates or rehearsal restarts.
-   How restart/resume is selected.
-   How rollback works.
-   Whether published revisions mutate or are only superseded.

Prefer immutable revisions plus explicit activation over silently
mutating content already under test.

## Session targeting

Avoid accidental deployment to the wrong context. Rehearse should
identify:

-   Player/character.
-   World/server.
-   Mod/runtime connection status.
-   Development versus published lane.
-   Currently active artifact/revision.

Initially, one obvious active development target may be preferable to
generalized deployment management.

## Failure UX

Bad:

``` text
Load failed.
```

Better:

``` text
Revision 18 was not activated.

Runtime rejected action `spawn_group` in stage `wave_2`.
Catalog reference `greydwarf_elite_pack` was not found.

Artifact remains on revision 17.
```

Where possible, link/drill directly to the relevant artifact location.

## AI-assisted iteration

Example request:

> Change wave 2 from five greydwarfs to eight.

The agent changes the canonical artifact, validation runs, Studio shows
the semantic diff, and the creator selects **Update in game**.

Target response:

``` text
Revision 18 active.
Changed: Wave 2 enemy count 5 → 8.
```

AI accelerates creation without hiding what changed.

## Publication boundary

Development revisions can be numerous, disposable, and rapidly
superseded.

Publication should mean something stronger:

-   Validation complete.
-   Intended revision selected.
-   Durable identity.
-   Appropriate metadata.
-   Explicit creator action.
-   Suitable for other players.

Do not make rapid rehearsal revisions equivalent to published content.

## End-to-end tests

Test the actual creator loop:

1.  Load/create known-good artifact.
2.  Validate.
3.  Deploy to development target.
4.  Receive runtime acknowledgement.
5.  Observe expected event.
6.  Modify artifact.
7.  Deploy next revision without restart.
8.  Verify the new revision is active.
9.  Verify the prior revision is not active.
10. Capture runtime evidence.
11. Publish a selected revision separately.

Also test malformed payloads, unavailable client, wrong schema version,
unresolved references, interrupted transfer, duplicate revision,
rollback, and disconnect/reconnect.

## Scope control

Do not turn this immediately into a generalized live-game deployment
platform.

The first objective is narrower:

> One creator can repeatedly change one experience and see that change
> in a real Valheim development session with minimal friction and
> trustworthy evidence.

Generalize only after real content-building laps expose the need.

## Success condition

A creator can:

1.  Describe or edit an experience.
2.  Obtain a valid revision.
3.  Understand at a glance what that revision does.
4.  Push it into an already-running Valheim development session.
5.  Receive positive acknowledgement.
6.  Exercise the content.
7.  See useful runtime evidence in the web UI.
8.  Change the experience.
9.  Push the replacement without restarting the game.
10. Repeat the loop rapidly.
11. Explicitly publish only the revision worth keeping.

Once this works, use it aggressively to create real player-facing
content. The friction discovered during those laps should determine the
next round of product work.
