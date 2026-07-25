# Lumberjacks creative runtime envelope

Status: proposed integration direction; CRE-E01 through CRE-E03 lab proofs supported, 2026-07-24

This note integrates the performance-gate and mod-author experience ideas with the
current M7 authority discovery work. It is a design direction and experiment queue,
not authorization to change P7 gameplay authority.

## The opportunity

Lumberjacks now sits at an unusually useful junction:

```text
Valheim / Unity hot path
        |
 Harmony patch seams       mod intent and lifecycle
        |                           |
        +------ runtime envelope ---+
                    |
          budget | route | observe
                    |
       UDP / WebSocket / native / JSONL
                    |
          replay | dashboard | MCP
```

The product opportunity is not to hide complexity from modders. It is to make the
complexity legible and bounded so a creative mod author can answer:

- What work did my feature request?
- What did the runtime defer, simplify, or preserve under pressure?
- Which transport carried the result?
- Did the decision change gameplay state, presentation only, or neither?
- Can I replay the same pressure and get the same decision?

That is a practical abstraction that most game modding stacks do not preserve long
enough to become an expert system: an explainable, reversible execution envelope.

## Proposed shape: measure, decide, route

The envelope has three responsibilities.

### Measure

Capture the minimum facts needed to explain cost and outcome:

- patch and call-site identity;
- hot-path call count and body time;
- frame budget and queue pressure;
- eligible recipient count and projected delivery fanout;
- object/event class and criticality;
- selected transport and fallback;
- result, reason, and rollback state.

The existing JSONL stream, `NetworkSensePerfProbe`, authority envelope, Companion
workbench, and MCP receipts are the foundation. Do not create a second telemetry
system for this.

### Decide

Make a bounded decision at a known seam:

```text
full -> reduced -> deferred -> dropped
```

The decision must be made by a policy with an explicit budget and an explicit
criticality class. A decision row should be explainable without reconstructing IL:

```json
{
  "schema_version": 1,
  "event_type": "performance.gate_decision",
  "trace_id": "opaque",
  "work_id": "projectile.trail",
  "policy": "combat-budget-v1",
  "pressure_band": "red",
  "requested_mode": "full",
  "selected_mode": "reduced",
  "reason": "frame_budget_exceeded",
  "criticality": "presentation",
  "transport": "udp",
  "rollback_enabled": true
}
```

This is intentionally a decision record, not an authorization token. Gameplay
authority remains on the current M7 ladder until a claim earns promotion.

CRE-E03 established that selected source work is not the whole cost. Ten accepted
motion frames produced ten deliveries to one observer but eighteen aggregate
deliveries as the eligible region topology grew. A practical budget therefore needs
both local execution cost and projected downstream fanout:

```text
estimated work = local call cost + (selected payload cost x eligible recipients)
```

That estimate can remain crude at first, but source acceptance, setup traffic,
primary-target delivery, and aggregate fanout must remain separate evidence.

CRE-E04 adds a placement rule to that cost model. The same latest-wins policy has
different value depending on where it runs:

| Placement | Work reduced | Authority risk |
|---|---|---|
| client before Unity apply | local apply calls only | low; opt-in presentation seam |
| Gateway per recipient after AoI | delivery plus apply calls | medium; keyed recipient queue |
| Gateway before fanout | shared route plus delivery work | higher; one fidelity choice affects every recipient |

The deterministic fixture reduced 19 direct applies to 14 with latest-wins and 12
with expiry while preserving the final fresh sequence. This is policy-shape evidence,
not smoothness or capacity evidence. Captured timing and Unity observation must decide
whether removed intermediate samples help or hurt perceived motion.

### The current client seam is already latest-wins

Source inspection and CRE-E05 narrowed the next optimization target. The checked-in
`LumberjacksMotionRunner`:

1. enqueues decoded UDP/WebSocket motion;
2. drains the queue during `Update`;
3. retains only the newest sequence per remote ZDO;
4. iterates every fresh remote during every `LateUpdate`;
5. resolves its Unity object and exponentially Lerps/Slerps toward the last snapshot.

It does not extrapolate velocity. At the default 20 Hz send rate, a 60 FPS client
models three render applications per accepted snapshot per fresh remote entity. This
is not automatically three times too much work—smooth interpolation needs render
evaluation—but lookup/binding and interpolation are currently coupled in the same
inner loop.

The current motion apply is also an overlay: enabling it does not remove native
Valheim presentation updates. Until measured otherwise, treat native/Lumberjacks
transform competition as a separate plausible source of oscillation or correction.

The next implementation should observe before optimizing:

| Phase | Minimum evidence |
|---|---|
| receive | source transport, sequence accepted/stale, inter-arrival bucket |
| drain | queue depth, rows drained, snapshots replaced before render |
| bind | lookup attempts/hit path, elapsed time, cache/rebind reason |
| render | fresh remotes, transform writes, elapsed time, target error before/after |
| next frame | deviation from the prior Lumberjacks write, labeled as possible—not proven—native overwrite |

Rows should be bounded rollups, not per-frame disk spam. The first candidate after
measurement is a two-snapshot interpolation timeline with current chase-latest kept as
the instant rollback. Caching object bindings can be tested independently from visual
math.

### Route

Use semantics to choose carriage rather than choosing UDP because something is
frequent:

| Class | Preferred carriage | Fallback | Example |
|---|---|---|---|
| transient/presentation | session-bound UDP | binary WebSocket | projectile trail, remote pose sample |
| ordered state | binary WebSocket | native/compatibility path | acknowledged ZDO update |
| critical world mutation | reliable ordered path | stop/retry | death, build, inventory mutation |
| operator/control | local MCP/HTTP | refuse safely | capture, benchmark, rollback |
| evidence | append-only JSONL | bounded local buffer | gate decision, comparison, receipt |

The current implementation already has a WebSocket plus UDP motion lane and a
separate declared ZDO delivery boundary. The envelope must keep those facts visible;
it must not imply that all Valheim traffic has crossed to Lumberjacks.

## Corrections to the supplied model

Several ideas are valuable, but should be narrowed before implementation.

### Do not insert a generic `BRFALSE` around arbitrary mod logic

A transpiler can safely redirect one known call site when the stack shape and method
identity are verified. It cannot generically skip an already-executed Prefix, undo a
mod's side effects, or safely wrap an unknown chain of patches. The first gate should
therefore be one of:

1. a cooperative mod callback that explicitly accepts a mode;
2. a known wrapper around a noncritical presentation operation; or
3. a surgical call-site redirect with a no-op fallback when the IL match changes.

The current Harmony policy is correct: transpilers are for narrow call-site swaps,
must degrade to the original instruction stream, and must report availability.

### Treat Harmony ordering as an implementation detail, not the mod API

Patch priority and skip behavior can be load-bearing, but a general prefix chain is
not a reliable negotiation protocol for independent mod authors. The framework should
offer an explicit budget-aware callback/manifest instead of asking unrelated mods to
coordinate through prefix ordering.

### Do not call a higher-rate shadow simulation “truth” yet

A 20 Hz or higher Game.Simulation loop can become a valuable deterministic oracle,
but it is initially a shadow model. It becomes gameplay authority only after the
relevant state, ownership, correction, and rollback claims pass their independent
M7 ladders. The lab should compare it to native behavior before allowing it to drive
clients.

### Do not assume projectile traffic belongs on UDP

The right split is semantic. A visual projectile trail can tolerate loss and late
replacement. A hit result, damage application, inventory mutation, or world change
cannot. Each event class needs ordering, revision, expiry, and fallback rules.

### Measure “5x overhead”; do not encode it as folklore

The patch-load A/B runbook already measures body time and whole-frame deltas. Add
trampoline and call-rate interpretation only after the first data exists. The likely
optimization target may be enumeration, serialization, queueing, or fan-out rather
than Harmony itself.

## Mod-author contract

The first public-facing artifact should be a small manifest, not a large SDK:

```json
{
  "schema_version": 1,
  "mod_id": "example.projectilefx",
  "version": "0.1.0",
  "patches": [
    {
      "target": "Projectile.Update",
      "kind": "cooperative_callback",
      "hot_path": true,
      "criticality": "presentation",
      "modes": ["full", "reduced", "deferred"],
      "default_mode": "full",
      "fallback": "native",
      "telemetry_event": "mod.projectilefx.update"
    }
  ]
}
```

The manifest can later generate:

- patch/load-order diagnostics;
- a cost and criticality card in the Companion workbench;
- default gate settings;
- dashboard labels and event names;
- compatibility warnings when a target method changes.

This is the leverage point: one small declaration becomes documentation, runtime
telemetry, experiment metadata, and a safer release review.

## Smallest useful experiment train

These experiments build on the current patch-load and M7 authority work.

| Experiment | Question | Driver | Success signal |
|---|---|---|---|
| CRE-0 | What is the standing cost of the existing detour? | seeded headless client | inert vs observer A/B has a measured delta |
| CRE-1 | Can one noncritical callback degrade predictably? | pure driver | **supported:** two 38-row runs matched; all four modes and six invariants passed |
| CRE-2 | Does pressure cause bounded graceful degradation? | Gateway synthetic burst | **supported for selection/carriage:** 9 selected frames routed; 23 suppressed frames absent; queue-pressure behavior remains separate |
| CRE-3 | Does the route preserve freshness and expose delivery cost? | Gateway UDP/WS fault fixtures | **supported after refinement:** duplicate/old frames dropped, gaps/wrap/resume passed, detached token failed closed, and 10 accepted frames produced 18 topology-derived deliveries |
| CRE-4 | Can accepted presentation work be bounded without final-state regression? | pure consumer replay | **supported for policy shape:** direct/latest/expiry applied 19/14/12 samples; both final sequences matched; repeat hash matched |
| CRE-5 | What work does the checked-in apply loop request? | source-derived pure model | **supported as a model:** apply calls scale with FPS x fresh remotes; 20 Hz ingress at 60 FPS yields three render applications per snapshot |
| CRE-6 | Does native presentation remain understandable? | local Valheim shadow | native remains authoritative; no critical omission |
| CRE-7 | Does a human perceive improvement? | one OMEN/i5 window | predicted motion/feel labels match observation |
| CRE-8 | Does a real mod author understand the result? | Companion workbench | author can identify cost, mode, route, and rollback without log archaeology |

CRE-1 was intentionally run with synthetic cost units to prove the policy and evidence
shape without waiting for a client. CRE-0 is now the immediate next technical step
because the other agent's current patch-load work is already aimed at it. CRE-0 must
replace the placeholder costs before CRE-1 informs a live call site.

## Lab artifacts

Every run should leave a compact packet:

```text
run.json
scenario.json
source.json
patch-manifest.json
gate-decisions.jsonl
transport-events.jsonl
perf-patchload.jsonl
benchmark-results.jsonl
comparison.json
operator-notes.md
```

The Companion workbench should present this as a vertical slice rather than a wall
of dashboards:

```text
requested -> gate decision -> route -> applied/acknowledged -> observed feel
```

The most valuable visual is an explainable degradation strip:

```text
GREEN  full      1,240/s   UDP       no shedding
AMBER  reduced     860/s   UDP       presentation budget
RED    deferred    410/s   WebSocket critical-only
```

It should also show what was protected. “Dropped 18%” is not useful by itself;
“dropped presentation updates, preserved hit and world mutation events” is.

## Milestone mapping

- **M3:** add the gate and route event families to the existing append-only stream;
  no new observability platform.
- **M4a:** use recipient and queue invariants to prove that degradation does not
  cause cross-recipient leakage, duplicate application, or revision regression.
- **M4b:** use the local two-client shadow/strict lane for presentation-only gates.
- **M5:** package the manifest, workbench view, rollback controls, and author-facing
  diagnostics for external builders.
- **M7:** treat relevance, ownership, simulation, and RPC changes as separate
  authority claims. The envelope can measure and route them before it is allowed to
  own them.

This makes the proposal additive rather than a new cutover: first expose cost and
decisions, then gate one safe presentation seam, then earn broader authority.

## Deliberate non-goals

For now, do not build:

- a generic IL optimizer or arbitrary transpiler wrapper;
- a universal mod scheduler that can cancel other mods;
- a second authoritative simulation beside Valheim;
- a promise that UDP is suitable for every high-frequency event;
- a full SDK before the manifest and receipts prove their value;
- a dashboard metric whose source cannot be traced to a raw event.

The thesis is simple: modders keep the creative “what”; Lumberjacks makes the
execution “how” observable, budgeted, routable, and reversible.
