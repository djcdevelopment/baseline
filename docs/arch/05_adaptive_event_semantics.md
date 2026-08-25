# Adaptive Event Semantics --- Area Scope, Duration, and Progressive Outcomes

## Objective

Expand runtime vocabulary only where real authored experiences require
richer semantics.

Two important families have emerged:

1.  **Spatial scope:** an event matters because of where it happened.
2.  **Temporal/performance scope:** an Event changes because of how long
    or how successfully players are progressing.

These should become reusable primitives rather than one-off Event logic.

## Spatial Semantics

A raw event such as `chat_sent` is often insufficient.

Creators need statements such as:

> A qualifying shout occurred within 30 meters of the ritual stone.

General form:

`event + actor/target constraints + spatial relation + anchor + radius`

Candidate concepts: within radius, entered area, left area, remained in
area for duration, matching entity count within area, event inside
encounter bounds, nearest matching object, and loaded-scene scope where
appropriate.

Anchors may be authored anchors, structures, ZDOs, players, coordinates,
or runtime instances.

## Temporal Semantics

Creators should be able to express:

-   Combat has lasted N seconds.
-   Player remained in region N seconds.
-   No progress for N seconds.
-   Objective completed within N seconds.
-   Time since last matching event.
-   Time since stage entered.

These must be deterministic and inspectable.

## Performance Semantics

Useful explicit measures may include wave clear time, death count,
remaining enemy count, objective completion pace, repeated failure, and
relevant resource depletion/consumption.

Do not create an opaque global difficulty score prematurely. Prefer
small observable facts creators can compose.

## Progressive Relief / Challenge

Examples:

``` text
IF combat_duration > 8m
AND enemies_remaining > 3
THEN suppress_next_reinforcement
```

``` text
IF player_deaths >= 2
AND stage_duration > 10m
THEN open_relief_route
```

``` text
IF wave_clear_time < 90s
THEN add_elite_reinforcement
```

These are explicit creator-authored alternate paths, not hidden AI
difficulty adjustment.

## Experience-Level Intent

This lets a creator target an experience rather than a rigid script:

> Produce roughly a ten-minute desperate defense.

Bounded authored branches can preserve that dramatic shape across
different player skill levels while leaving taste and allowable
adaptation under creator control.

## Explainability Requirement

Every adaptive decision must be inspectable in Arcane Sight:

``` text
Transition: relief_route
Reason:
- combat_duration = 10m 14s  [> 10m]
- player_deaths = 2          [>= 2]
Result:
- east_gate opened
- reinforcement_4 suppressed
```

If the runtime cannot explain a decision from concrete evidence, the
semantic primitive is not ready.

## Studio Requirement

Studio should present these semantics at multiple levels:

-   Simple: "If the fight runs long, provide relief."
-   Structured: explicit thresholds and actions.
-   Graph: branch topology.
-   JSON: canonical conditions.
-   Runtime: actual values that caused the branch.

## Community Value

These semantics naturally become reusable Patterns: Prolonged Combat
Relief, Skilled Group Escalation, Timed Escape, Last Stand, Area Ritual,
or Crowd Response.

They should therefore be designed with stable IDs, validation,
explanation, and composability from the beginning.

## Implementation Order

1.  Inventory existing event/time/spatial facts already available.
2.  Reuse existing ZDO/client observations.
3.  Define canonical area/anchor representation.
4.  Implement deterministic predicates.
5.  Add validation.
6.  Add Arcane Sight evidence.
7.  Add Studio explanation.
8.  Build one real Event using each primitive.
9.  Only then generalize further.

## Success Condition

A creator can author a spatially scoped, time-sensitive adaptive Event;
Studio can explain it before deployment; Valheim can execute it
deterministically; and Arcane Sight can show exactly why each adaptive
branch fired.
