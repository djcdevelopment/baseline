# Community Artifact Ecosystem --- Palettes, Patterns, Versions, and Remixing

## Vision

The long-term community value is not merely distributing finished
Quests. It is distributing progressively larger units of authored
behavior.

The relevant lesson from community artifact ecosystems is portability,
inspectability, versioning, attribution, ranking, forking, and community
support.

The structured JSON/string representation already provides the technical
substrate.

## Artifact Ladder

A useful conceptual hierarchy:

-   **Primitive:** canonical runtime fact/action such as combat
    duration, area entry, chat sent, spawn group, item consumed.
-   **Pattern:** reusable combination such as Prolonged Combat Relief,
    Proximity Ambush, Gate Failure, or Wave Completion.
-   **Charm:** reusable authored behavioral component.
-   **Event:** composed runtime experience using patterns/charms.
-   **Quest / Scenario Pack:** player-facing objectives, Events,
    narrative, progression, and dependencies.

Names may evolve; composability and granularity matter more.

## Community Manifest

Future artifacts should support stable ID, name/description, type,
author/maintainer, version, compatibility, dependencies, required
primitives, validation status, media, tags, attribution/sharing policy,
import representation, version history, fork lineage, ratings/usage,
changelog, and deprecation/replacement information.

## Creator-Controlled Sharing

Creators should not face all-or-nothing disclosure. A flagship Event can
remain private while its author shares beginner palettes, selected
patterns, reusable Charms, educational examples, or remixable templates.

## Portable Representation

Canonical structured artifacts remain truth. Compact
strings/hex/Base64-style representations can support clipboard transfer,
chat/forum sharing, and import/export, but must always resolve back to a
validated structured artifact.

## Version and Provenance

Track original artifact, fork parent, imported version, local
modifications, upstream updates, attribution, and compatibility changes.

Prefer semantic diff:

``` text
Forked from Progressive Relief 1.3
Local changes:
- Threshold 10m → 8m
- Added food-cache action
- Removed death-count condition
Upstream 1.4 available
```

## Adaptive Patterns

Explicit adaptive dramaturgy is especially shareable:

``` text
combat_duration > 8m
AND enemies_remaining > threshold
→ suppress next reinforcement
```

or:

``` text
wave_clear_time < 90s
→ enable elite reinforcement
```

The creator defines permissible adaptations; runtime evidence chooses
the authored path.

## Economic Model --- Defer

A popular repository could eventually support itself through ads,
sponsorship, donations, premium tooling, or another model. Do not
optimize around monetization yet.

First prove people create, reuse, share, fork, care about versions, and
return for updates.

## First Implementation Slice

Make local artifacts community-ready before building the public
repository:

1.  Stable IDs.
2.  Version metadata.
3.  Attribution.
4.  Dependencies.
5.  Export/import.
6.  Semantic diff.
7.  Fork/provenance fields.
8.  Shareability metadata.
9.  Notebook references.
10. Known-good manifest format.

## Success Condition

One creator can publish a reusable pattern; another can import a
specific version, modify it with provenance preserved, use it inside a
different Event, and later understand both local changes and upstream
updates.
