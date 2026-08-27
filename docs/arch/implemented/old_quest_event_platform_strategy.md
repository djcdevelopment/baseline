# Quest / Event Platform --- Remaining Strategy

## Purpose

The next phase is not about turning the workflow editor into an
increasingly elaborate visual IDE. The core capability already exists:
structured content can be authored, validated, published, loaded by the
Valheim mod, and exercised in game.

The remaining work should convert those proven capabilities into a
coherent creation loop while preventing UI refinement from becoming an
open-ended product-development trap.

> Make executable player experiences easy to generate, inspect,
> validate, rehearse in a real Valheim world, revise, and publish.

Optimize for the shortest trustworthy path from an idea to a player
interacting with it.

## Domain boundaries

**Quest:** principally describes what a player should accomplish:
gather, kill, visit, deliver, progress, receive rewards, or unlock
content.

**Event / Scenario:** principally describes what the runtime should do:
observe triggers, spawn entities, branch, wait, display messages, alter
world state, advance quests, succeed, or fail.

**Charm:** retain where it means a reusable runtime experience/behavior.
Do not make it a catch-all synonym for Quest.

> If an artifact principally describes what the player must accomplish,
> it is a Quest. If it principally describes what the runtime should do,
> it is an Event/Charm.

A Quest may reference an Event and an Event may advance a Quest. They do
not need to be the same artifact.

## Product boundary

Studio should not require creativity to originate inside Studio.

> Studio is where executable creativity becomes inspectable,
> trustworthy, testable, and publishable.

Content may originate from human authoring, imported quests, AI
generation, modifications, or templates. All paths should converge on
the same canonical structured artifact and deterministic validation
pipeline.

JSON remains canonical. Base64/string forms are transport and sharing
formats.

`Intent → Structured Artifact → Validation → Inspection → Rehearsal → Runtime Evidence → Revision → Publication`

## First-user strategy

Start building real playable content now. Heavy AI assistance is not a
workaround; it tests whether the artifact contract is explicit enough.

Classify failed authoring laps:

1.  Artifact contract ambiguity.
2.  Validator missed an invalid state.
3.  Missing runtime primitive.
4.  Ordinary model error.
5.  Studio made behavior difficult to understand.
6.  Game integration made iteration unnecessarily expensive.

Items 1, 2, 3, 5, and 6 are platform work. Item 4 usually is not.

## Persona attenuation

Three intents are enough for this phase:

-   **Consumer / Configurator:** discovers, selects, configures, or runs
    existing content. Should not need graph/runtime internals.
-   **Quest Author:** defines objectives, progression, text, rewards,
    and prerequisites.
-   **Experience / Event Author:** orchestrates runtime behavior and may
    need triggers, branches, actions, timing, topology, and runtime
    evidence.

Complexity should be progressively disclosed.

## Progressive inspection

Do not force every artifact through the graph editor.

1.  **Simple view** --- readable explanation of what happens.
2.  **Structured view** --- stages, conditions, actions, dependencies,
    outcomes.
3.  **Graph view** --- topology and branching where topology matters.
4.  **Certified JSON** --- canonical artifact and advanced debugging.
5.  **Runtime/history** --- evidence of what actually happened.

The graph is an important diagnostic and surgical editing surface, not
necessarily the default creation surface.

## Primary remaining work

### AI-authorable artifact contract

Create a compact, model-independent package containing schema,
semantics, examples, fixtures, validation commands, and onboarding
instructions. Do not build a proprietary AI engine unless evidence
demands one.

### Rehearse as a deployment lane

Turn Rehearse into the bridge between authored content and a real
Valheim player/world. Push a development revision, observe runtime
evidence, revise, and push again without polluting published content.

### Web ↔ Valheim closed loop

Remove operational seams requiring insider knowledge:

`Create/Generate → Validate → Rehearse → Play this revision → Hot-load → Observe → Modify → Update in game`

Game restarts should not be normal iteration.

### Inspection and drill-down

Default to concise information, with drill-down for validation, runtime
events, graph execution, raw JSON, catalog resolution, and revision
history.

### Build real content

Use the platform to create actual player-facing experiences. Real
creation is now the primary requirements-discovery mechanism.

## Development gates

Before adding an editor capability:

> Which author is blocked, during which workflow, from accomplishing
> what?

Before adding AI infrastructure:

> Is intelligence actually required, or can a documented contract plus
> deterministic tools allow existing agents to do it?

Before adding manual authoring controls:

> Did a real content-building lap expose this need?

Prefer observed friction over anticipated friction.

## Testing

Keep Playwright, but recognize its boundary: it proves the interface
behaves as implemented, not that an unfamiliar creator understands what
to do.

Preserve/add schema and semantic tests, known-good/bad fixtures,
serialization round trips, runtime integration tests, hot-load/revision
replacement tests, creator-flow tests, and actual content-building laps.

## Scope control

Avoid spending this phase on perfecting every dropdown, general-purpose
node-editor features without demonstrated need, an AI orchestration
platform, converting every Quest into an Event, exposing every runtime
concept to novices, or treating visual polish as evidence of readiness.

## Measures of progress

Measure creator-loop performance:

-   Time from idea to first playable revision.
-   Manual cross-application steps.
-   Game restarts required.
-   Time from edit to updated in-game behavior.
-   Percentage of generated artifacts repaired from deterministic
    feedback.
-   Concepts required before first success.
-   Ability to explain runtime behavior from captured evidence.
-   Number and quality of actual playable experiences created.

## Near-term success condition

> An unfamiliar capable AI agent can enter the repository, read one
> onboarding path, create a nontrivial Event from natural language,
> validate and repair it using deterministic tooling, load it into
> Studio, push it to an active Valheim development session, receive
> runtime evidence, revise it, and produce a publishable artifact
> without undocumented knowledge.

At that point, the next priority is not more platform construction by
default. It is creating things with it.
