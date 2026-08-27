# AI-Assisted Authoring and Artifact Contract

## Objective

Make Quest/Event artifacts explicit, deterministic, and inspectable
enough that existing AI coding agents can author them reliably without a
dedicated AI engine.

> Any sufficiently capable agent should be able to learn the artifact
> contract quickly, create or modify an experience, validate its work,
> repair deterministic failures, and hand the resulting artifact to
> Studio.

## Architecture choice

The structure is already machine-readable and documented enough that
multiple AI models can work with it. A dedicated AI engine would add
model coupling, provider decisions, prompt infrastructure, runtime
state, and another debugging/maintenance surface without evidence those
costs are necessary.

Optimize for **agent onboarding**, not agent ownership.

JSON remains the source of truth. Base64/string representations are
transport formats.

## Agent onboarding package

Provide one obvious entry point such as `AGENT_AUTHORING.md`. It should
tell an unfamiliar agent:

1.  What Quest, Event, and Charm mean.
2.  Which artifact type fits a request.
3.  Where schemas live.
4.  Where known-good examples live.
5.  Which runtime signals/actions are legal.
6.  How references resolve.
7.  How to validate.
8.  How to interpret failures.
9.  How to rehearse/simulate.
10. How to load into Studio.
11. What must never be fabricated.
12. What receipts constitute completion.

Keep the onboarding path short enough that an agent does not need to
scan the entire repository.

## Deterministic tooling

Prefer small commands with bounded outputs. Reuse existing tools rather
than creating parallel implementations.

Conceptual surface:

``` text
questctl validate <artifact>
questctl explain <artifact>
questctl compile <artifact>
questctl diff <old> <new>
questctl rehearse <artifact>
```

### Validate

Detect schema violations, invalid transitions, unreachable stages,
missing terminal paths, unknown signals/actions, unresolved references,
invalid parameters, duplicate IDs, contradictions, and unsupported
versions.

Provide machine-readable and human-readable output.

### Explain

Produce a concise semantic interpretation: start behavior, stages,
branches, success/failure paths, external dependencies, consumed runtime
signals, and produced effects. This can also feed Studio's Simple view.

### Compile

Produce the exact runtime artifact expected by the mod/runtime.
Compilation should be deterministic.

### Diff

Prefer semantic differences over raw JSON differences:

``` text
Wave 2 enemy count: 5 → 8
Timeout: unchanged
New failure path: gate_destroyed → failed
No catalog reference changes
```

### Rehearse

Perform runtime-independent checks before live deployment where
possible: path analysis, transition simulation, fixture events, and
expected-outcome checks.

## Fixtures

Maintain:

-   **Minimal known-good:** smallest valid artifact for each construct.
-   **Representative known-good:** realistic collection, kill, location,
    multi-stage, encounter, wave-defense, branching, quest-advancing,
    and world-effect examples.
-   **Intentionally invalid:** common failure modes proving validator
    behavior.

## Model independence

Codex, Claude, Gemini, local models, and future agents should encounter
the same repository contract.

The repository carries durable system knowledge. The model supplies
reasoning and generation.

## Completion receipts

An agent should not claim success because it wrote JSON. Require
evidence such as:

``` text
Artifact created: event/palisade-defense.json
Schema validation: PASS
Semantic validation: PASS
Unresolved references: 0
Unreachable stages: 0
Terminal success paths: 1
Terminal failure paths: 1
Compilation: PASS
Studio load: PASS
```

When live rehearsal exists:

``` text
Development deployment: PASS
Runtime revision observed: r18
Expected start event observed: PASS
```

## Failure taxonomy

**Contract failure:** documentation/schema allowed multiple plausible
interpretations. Improve the contract.

**Validation failure:** an invalid artifact passed validation. Improve
deterministic checks.

**Primitive failure:** requested behavior cannot be expressed cleanly.
Evaluate a new runtime primitive.

**Model failure:** contract and validator worked; the model simply
erred. Let the repair loop work rather than redesigning the platform.

**Inspection failure:** a valid artifact is difficult to understand.
Improve explanation/drill-down.

**Integration failure:** a valid artifact is cumbersome to exercise in
game. Improve Rehearse/hot-load.

## Human and AI symmetry

Humans may author through forms and graphs. AI may author JSON directly.
Both must converge on the same validator, compiler, rehearsal lane,
revision model, and publication process.

Do not create a privileged parallel AI implementation.

## Avoid

Do not build yet:

-   A content-generation agent swarm.
-   Provider-specific prompt infrastructure.
-   A vector database solely to teach the schema.
-   Autonomous publishing.
-   AI-only artifact semantics.
-   Hidden transformations Studio cannot explain.
-   A second source of truth.

## Success test

Give an unfamiliar agent only the repository, onboarding entry point,
and a bounded request:

> Create a three-wave palisade defense. Start when a player enters the
> courtyard. Begin wave two when fewer than three enemies remain. Fail
> if the gate is destroyed. When wave three is cleared, show a
> completion message and advance the associated quest.

It should select the artifact type, discover legal primitives, create
it, validate it, interpret and repair errors, explain it, load it into
Studio, and produce receipts.

If this works across more than one capable model, resist adding an AI
engine until a concrete limitation appears.
