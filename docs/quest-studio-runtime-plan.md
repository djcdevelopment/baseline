# Quest Studio → Quest Runtime: vision, architecture, and delivery plan

Status: active implementation plan, updated 2026-08-09.

This document is the canonical product and technical plan for moving quest creation out of the
in-game Quest Lab and into a purpose-built browser studio, while keeping execution small, explicit,
safe, and local-first. It records the intended end state, the contracts that hold the products
together, why those boundaries exist, the milestone sequence, acceptance evidence, and the exact
implementation state today.

## Vision

A creator should be able to build a Valheim experience with the clarity of a visual automation
editor and the atmosphere of a Norse grimoire: select witnessed game events, compose them into
bounded logic, connect stages, simulate the result, publish one immutable file, deliberately load it
in Valheim, bind it to a world object, and see the intended action happen exactly once.

The system is three products sharing one behavioral contract:

1. **Quest Studio** is the rich loopback browser authoring environment and Grimoire.
2. **ComfyQuestRuntime** is the small gameplay mod that loads and executes published experiences.
3. **ComfyQuestLab** is the private-world visualization, rehearsal, and learning tool.

**ComfyNetworkSense** remains telemetry and schema-1 quest compatibility. It does not become the
workflow engine. MCP is an optional automation client over the same files and Companion operations;
it is not a required browser-to-game connection.

The complete conceptual view is in [implementation overview](quest-studio-runtime-implementation-overview.svg).

## Product principles

- **Files are the handoff.** Studio produces a `.questpack`; the game consumes it.
- **Loading is deliberate.** Publishing never silently changes a running game. There is no watcher.
- **One contract, several hosts.** Studio, Runtime, Lab, certification, and optional MCP use the same
  Unity-free compiler and evaluator.
- **Canonical identifiers are behavior.** Norse names, prose, colors, and translations are metadata.
- **Bounded composition beats scripting.** V1 has a closed grammar and action registry, not arbitrary code.
- **Authority fails closed.** World mutation happens only where the runtime can prove authority.
- **Identity makes retries safe.** Stable IDs and durable receipts make actions exactly-once.
- **Old content keeps working.** Existing `quests/*.json`, event archives, packs, and NetworkSense
  schema-1 behavior remain compatible.
- **Evidence controls claims.** Headless contract tests, game builds, OMEN visual acceptance, and i5
  peer acceptance prove different things and are never substituted for one another.

## Why the architecture is split this way

The former Quest Lab direction mixed three very different workloads in one in-game panel: rich
authoring, behavioral execution, and live teaching/inspection. That increases UI complexity inside
Unity, makes safe runtime review harder, and encourages browser-to-game coupling.

The split puts each workload in its natural environment:

| Surface | Optimized for | Deliberately excludes |
|---|---|---|
| Quest Studio | search, graph editing, diffs, history, simulation, imports | direct gameplay mutation |
| ComfyQuestRuntime | deterministic evaluation, state, authority, actions | catalog spreadsheets and JSON editing |
| ComfyQuestLab | witnessing, rehearsal, Arcane Sight, teaching | primary pack composition |
| ComfyNetworkSense | telemetry and legacy schema-1 completion | experience execution |
| Companion | loopback, root-confined file transfer | workflow interpretation |

This also creates a narrow trust boundary. A browser asks Companion to write a certified opaque pack
to one confined inbox. Runtime independently validates it and does nothing until the player chooses
Check or Load. Studio can disappear after publication without breaking gameplay.

## System architecture

See the [conceptual data-flow diagram](quest-studio-runtime-dfd.svg) and
[technology stack](quest-studio-runtime-tech-stack.svg).

### Quest Studio

Quest Studio is a new Workbench surface served on loopback. Its durable state contains editable
projects and version history, not installed runtime state. The intended creator surface includes:

- searchable, school-colored Grimoire cards backed by the canonical event catalog;
- visual stage graph, trigger-group palette, and action palette;
- quest, quest-line, and multi-stage experience templates;
- structured target and `where` editors rather than raw JSON;
- synthetic examples and event-archive replay;
- exact compiler diagnostics and graph visualization;
- simulation, version history, diff, import/export, and pack certification;
- schema-1 quest and Spell String compatibility.

Publishing compiles the project, certifies the package, assigns its semantic version and canonical
content hash, then sends the immutable bytes to Companion. If Valheim cannot be located, Studio
downloads the identical pack for manual copying.

### Companion handoff

Companion exposes a loopback-only, root-confined publish endpoint. It accepts a bounded `.questpack`,
calls the shared certification implementation, and writes only to:

`BepInEx/config/comfy-quest-runtime/inbox/`

It must reject traversal, malformed archives, partial writes, unsupported schema versions, and
same-version/different-content collisions. Publication uses a temporary file plus atomic rename.
Companion does not activate content or interpret gameplay actions.

### ComfyQuestRuntime

Runtime is a dedicated BepInEx plugin. Its compact hotkey drawer ultimately shows:

- active pack, semantic version, canonical hash, and readiness;
- Check, Load latest, choose version, and Rollback;
- binding selection, aim preview, Inscribe, Replace, and Unbind;
- current experience, stage progress, and last actionable error;
- a fixed Open Studio button.

It explicitly excludes the Grimoire spreadsheet, raw JSON editor, full scenario catalog, and pack
composition. Runtime executes only `experiences/*.json`; NetworkSense alone retains schema-1 quest
completion, preventing double execution.

### ComfyQuestLab

After Studio reaches feature parity, Lab's default tabs become **What happened**, **Learn**,
**Arcane Sight**, and **Ready**. It retains event witnessing and one-at-a-time rehearsal. The existing
Spellbook, quest tables, pack composition, and scenario catalog remain temporarily available behind
an Advanced compatibility switch, then move fully to Studio.

### Optional MCP

MCP may list Studio projects, invoke certification, publish a pack, request Check/Load, or read
receipts. Those operations call the same local capabilities and file contract as the browser. MCP
never becomes an alternate evaluator, arbitrary command bridge, or required live connection.

## Shared contracts

The interface map is illustrated in [contract interfaces](quest-studio-runtime-contracts.svg).

### Experience document

Schema identifier: `comfy-quest-experience/v1`.

- An **event clause** matches one canonical Grimoire event plus structured target/where fields.
- A **trigger expression** combines clauses with `ANY`, `ALL`, `COUNT`, or `SEQUENCE`, optionally
  within a bounded timing window. Engine-owned timer signals enter through the same event boundary.
- A **stage** owns entry actions and prioritized transitions.
- A **transition** owns a trigger expression, actions, and exactly one next stage or terminal outcome.
- A **quest** is one stage; a **quest line** is multiple stages; an **experience** is the complete
  bounded acyclic graph; a **binding** is an entry point attached to a world Charm.

V1 bounds are 1 MiB per document, 64 stages, 128 trigger leaves, 256 actions, expression depth three,
unique non-empty stable IDs, bounded count/window values, and an acyclic graph. Repetition is expressed
with bounded `COUNT` or `SEQUENCE`, never arbitrary loops.

### Quest pack

A `.questpack` is a ZIP-compatible immutable artifact:

```text
manifest.json                 comfy-quest-pack/v2; pack ID, SemVer, canonical hash
experiences/<id>.json         comfy-quest-experience/v1 documents
quests/<id>.json              unchanged optional schema-1 compatibility content
```

The canonical content hash is calculated deterministically over sorted experience entry names and
bytes. Package SHA-256 separately identifies the exact archive. The active set records both.

Studio imports a schema-1 quest as a one-stage experience. A sufficiently simple experience may
export schema-1 for NetworkSense. Runtime ignores `quests/` and executes only experience documents.

### Activation and rollback

`Check for new` validates candidates and presents compatibility/diffs without changing the active set.
`Load latest` chooses the highest compatible semantic version. Two candidates with the same pack ID
and version but different canonical hashes fail closed. Activation atomically replaces
`active/active-set.json`, retaining the previous set and package versions for rollback.

### Charm references

A Charm ZDO stores only namespaced references:

- pack ID;
- experience ID;
- binding ID;
- semantic version;
- canonical content hash.

It never stores workflow JSON, arbitrary ZDO keys, scripts, commands, URLs, or paths. Missing content
or a hash mismatch produces an unresolved Charm and no execution.

Aim and Inscribe initially accepts only locally owned allowlisted ZDOs in solo/listen-host private
worlds: player-built pieces, signs, item stands, and dedicated Charm objects. Creatures, portals,
terrain, ordinary dropped items, arbitrary containers, and remote-owned objects are excluded.

### Runtime state and receipts

State is durably keyed by world, character, binding ZDO, experience hash, stage, transition, and action.
Each action has a stable action ID. Before and after execution, Runtime records enough state to make
RPC duplicates, overload witnesses, reloads, reconnects, death, and restarts idempotent.

Load, rollback, validation, binding, transition, action, and failure operations emit machine-readable
receipts. Studio reads them on refresh; it does not require a live push channel.

### Closed action registry

V1 permits only:

- message/HUD cue and Arcane Sight effect;
- counter and timer changes;
- stage/experience activate, advance, complete, or fail;
- one allowlisted valid item stack per grant action;
- at most 16 allowlisted creatures, items, or pieces within 30 m of the bound Charm;
- clearing only objects durably marked as spawned by that experience/action.

No arbitrary RPC, console command, reflection, shell execution, URL, path, raw prefab execution, or
unmarked deletion is allowed. Rewards and spawns execute only in solo/listen-host private worlds.
Dedicated or peer multiplayer may load, inspect, and simulate, but mutation fails with an authority
diagnostic. Server-authoritative multiplayer is a later evidence-gated design.

## Delivery milestones

### Milestone 1 — Boundary freeze and shared foundation

Purpose: stop expanding in-game authoring and establish one behavioral core.

- Document the product split and file-first/MCP-optional rule.
- Extract the Unity-free experience schema, validator, graph checks, evaluator, diagnostics, hashes,
  compatibility rules, and pack lifecycle.
- Add the separate Runtime project and preserve schema-1 behavior.
- Pin the boundary with headless tests.

Exit evidence: contracts build without Unity, bounds/cycles/determinism tests pass, NetworkSense legacy
tests remain green, and Runtime builds against the installed game assemblies.

### Milestone 2 — Thin browser-to-world vertical

Purpose: prove the entire loop with the smallest useful experience.

- Studio authors one event clause, one stage, and one terminal transition.
- Companion publishes a certified immutable pack to the confined inbox.
- Runtime Check and Load operate only on explicit input and issue receipts.
- Player inscribes a sign or item stand with one binding.
- One event causes one message, allowlisted reward, or bounded spawn exactly once.
- Studio displays the resulting receipts on refresh.

Exit evidence: complete OMEN browser → file → load → inscribe → event → action trace plus automated
path, malformed-file, authority, ownership, allowlist, and idempotency tests.

### Milestone 3 — Composition and lifecycle

Purpose: graduate from a single quest to bounded experiences.

- Add `ANY`, `ALL`, `COUNT`, `SEQUENCE`, timer signals, branches, priorities, and full graph diagnostics.
- Add visual simulation, version diff, explicit version selection, and rollback.
- Persist stage/transition/action state atomically.
- Add unresolved Charm and Arcane Sight resolution states.

Exit evidence: exact Studio/Runtime/Lab evaluator parity; deterministic branch ordering; timing and
restart tests; version-collision, atomic-activation, and rollback tests.

### Milestone 4 — Creator loop and compatibility

Purpose: make observed play and existing content first-class authoring inputs.

- Event-archive replay and synthetic scenarios.
- Pack certification reports and diagnostics navigation.
- Schema-1 quest and Spell String import; simple schema-1 export.
- Browser project history and immutable published-version history.
- Arcane Sight binding inspection and resolution guidance.

Exit evidence: old archives and quests round-trip without changing NetworkSense behavior; certified
packs reproduce byte-for-byte; malformed and partial imports fail descriptively.

### Milestone 5 — UX migration and live acceptance

Purpose: complete the product split and make the new path the normal path.

- Reduce Lab's default UI and place authoring compatibility behind Advanced.
- Update Workbench cards, mod/package documentation, install flows, and retrospective.
- Package Runtime and Studio/Companion updates.
- Run the full OMEN private-world acceptance loop including rollback.
- Run one isolated native multiplayer pass with OMEN as the private listen host and i5 joining through
  Steam Friends. OMEN must execute the complete bounded mutation lifecycle; i5 must load the identical
  version/hash while mutation fails closed.
- Keep AM4, Docker, Gateway, and NetworkSense configuration outside this Quest acceptance harness.

Exit evidence: package hashes, automated suite, OMEN rendered acceptance, and i5 peer authority receipt.

### Later — Server-authoritative multiplayer

This is deliberately outside v1. It begins only after evidence demonstrates the private-world model,
state identities, and action receipts are stable enough to define a server authority protocol without
weakening the existing fail-closed behavior.

## Automated acceptance matrix

| Area | Required proof |
|---|---|
| Schema | size and count bounds, unique IDs, known events/actions, depth and window bounds |
| Graph | deterministic priority, missing destinations, cycle rejection, terminal validation |
| Evaluator | Studio/Runtime/Lab parity for EVENT/ANY/ALL/COUNT/SEQUENCE/timers |
| Files | malformed ZIP/JSON, partial write, traversal, root confinement, canonical hashes |
| Versions | semantic ordering, incompatibility, same-version collision, atomic activation, rollback |
| Binding | missing content, hash mismatch, ZDO allowlist, local ownership, unresolved state |
| Authority | private/listen-host allow; dedicated/peer mutation denial |
| Actions | parameter and prefab allowlists, radius/count caps, marked-only clearing |
| Idempotency | duplicate events/RPCs, reload, reconnect, death, restart, exactly-once receipts |
| Compatibility | unchanged schema-1 quests, archives, packs, and NetworkSense behavior |

## Current implementation state

As of 2026-08-10, Milestone 1 is substantially implemented and verified; Milestones 2 through 5 are
partial and remain evidence-gated rather than shipped as a whole.

### Implemented and verified

- `network/mod/ComfyQuestContracts` exists as a Unity-free `netstandard2.0` library.
- `comfy-quest-experience/v1` models and compiler validation exist.
- Current bounds, stable IDs, known operators/actions, destinations, and cycle rejection are enforced.
- Deterministic event, ANY, ALL, COUNT, and SEQUENCE evaluation exists.
- Quest-pack inspection, canonical experience hash, package SHA-256, semantic-version selection,
  same-version hash collision refusal, and atomic active-set replacement exist.
- `network/mod/ComfyQuestRuntime` exists and builds as a separate BepInEx plugin.
- Runtime creates the inbox and exposes explicit F10 Check and F11 Load latest operations; it has no watcher.
- Runtime has an F9 compact drawer with readiness, explicit Check/Load, fixed Open Studio, and live
  aim/inscription controls. Check and Load emit immutable `comfy-quest-runtime-receipt/v1` files; Studio
  reads the latest bounded set through Companion on refresh without a live game connection.
- Runtime ignores schema-1 quest execution by construction.
- Companion exposes an authenticated Workbench publish endpoint that bounds uploads to 8 MiB, confines
  filenames and destinations, validates through `ComfyQuestContracts`, writes atomically, treats identical
  publication as idempotent, refuses version/hash collisions, and returns a machine-readable receipt.
- A loopback `/quest-studio` thin vertical exists with durable atomic project state, the exact 34-event
  canonical catalog, structured event/target/message fields, live graph preview, shared-contract
  certification, canonical pack construction, and one-click authenticated publication.
- The WeakAura/MCP design spec now states that files are primary and MCP is optional.
- Shared Charm policy now pins private-world authority, local ownership, the four initial allowlisted target
  kinds, excluded target kinds, and strict namespaced reference validation before ZDO integration.
- Runtime now implements a 10 m camera aim preview and inscription path for locally owned, creator-marked
  signs, item stands, and player-built pieces. It rejects portals, creatures, containers, non-owned ZDOs,
  non-private sessions, peer clients, tampered active-set sources, content mismatches, and ambiguous packs;
  inscription writes only the five namespaced reference fields and emits a binding receipt.
- The shared test suite passes 351 tests; 26 Companion tests pass under the supported .NET 9 container;
  the Runtime Release build succeeds with zero warnings/errors.
- OMEN has now live-produced Check and Load receipts for the certified inscription fixture and atomically
  activated its exact pack/content hashes. The first attempt exposed and fixed F6/F7 collisions with Quest
  Lab and legacy Comfy Control; Runtime now uses F9/F10/F11 and displays hotkey results on the HUD.
- OMEN live aim, ownership, and inscription are witnessed: the drawer resolved an owned player-built piece
  as ready and emitted exact `bind / inscribed` receipts. Repeated clicks observed during usability testing
  led to an idempotent same-reference check, a large inscription HUD result, and clearer held-camera guidance.
- The message-only executor supports locally attributed `kill` and exact-bound-object `piece_damaged` events,
  re-certifies active content, resolves loaded Charm references, and claims a durable world/player/ZDO/hash/
  stage/transition/action identity before execution.
- OMEN version 1.1.0 replaced the hunting-dependent fixture with `piece_damaged` scoped to the exact bound
  ZDO. A bronze-axe strike rendered "The OMEN Charm feels the blow." and wrote one fully identified executed
  receipt; two later strikes wrote `duplicate_suppressed` receipts for the same world/player/ZDO/hash/stage/
  transition/action identity and did not render again. A relogged strike rendered from a different previously
  inscribed adjacent ZDO (`1:28365` versus `1:28366`), then suppressed its own second strike. The drawer now
  exposes exact aimed ZDO IDs; same-ZDO restart persistence remains the last proof for this slice.
- OMEN version 1.2.0 then proved the explicit hot-load boundary without restarting Valheim: Runtime checked
  three inbox packs as valid, atomically activated content hash
  `d362402d92b6e5069d95ad35556324214df8d242e563d99e3a2e6741e0902eef`, inscribed the surviving sign
  (`1:28403`), and rendered "The hot-loaded sign remembers." on the first punch. The second punch rendered
  no workflow action before ordinary game damage destroyed the sign. The action ledger retains the exact
  world/player/ZDO/hash/stage/transition/action key, confirming the first execution was durably claimed.
- Runtime now lists certified inbox versions, loads an explicitly selected version, and rolls back through the
  previous active set. Rollback re-inspects the immutable package and matches its pack ID, semantic version,
  canonical content hash, and package SHA-256 before an atomic activation; missing, malformed, or changed
  previous content fails closed. OMEN live-selected version 1.1.0 from the three valid packs, then rolled back
  to version 1.2.0; exact `load_selected / activated` and `rollback / activated` receipts match the expected
  content hashes, and `active-set.json` finishes on the certified 1.2.0 package.
- A Unity-free durable workflow store now keys progress by world, character, binding ZDO, and content hash;
  retains at most 128 stage-local events; chooses transitions by priority then stable ID; persists pending
  transitions across reloads; and advances or terminates only after actions are processed. Runtime uses it for
  multi-stage execution, entry actions, transition receipts, and drawer progress. Automated acceptance covers
  pending replay, post-completion suppression, deterministic priority, bounded COUNT accumulation, and restart.
- Version 1.3.0 is installed on OMEN for a non-destructive two-stage acceptance using two edits to one sign:
  `awaken → remember → complete`. Its certified content hash is
  `616df18bb5492cfee036e362bd9926fdc26beb8aa47ad06d38e48210661c711e` and package SHA-256 is
  `2d7f0b19227ec875a16d1cf3872d6e655c38b53fe15bd341ca6ccde5d330ba72`.
- OMEN completed that two-stage pass on sign ZDO `1577613496:53968`: Runtime receipts show the first message
  action executed in `awaken`, transition `first-writing` advanced, the second message executed in `remember`,
  and transition `second-writing` completed. The drawer visibly reported `OMEN Two-Stage Sign: complete`.
- The live comparison also established Quest Lab's F6 panel as the visual-quality reference for Runtime: strong
  dark panel hierarchy, deliberate spacing, section headers, readable status, scalable/resizable layout, and
  contextual help. Runtime remains a separate compact F9 surface but should reuse those presentation patterns.
- The redesigned F9 candidate now implements those patterns with a dark opaque window, section headers,
  readable status/hash rows, explicit Active Content/Charm/Experience hierarchy, title-bar dragging, and
  Escape close. The live review then drove a second pass: window style is pinned across drag/focus states;
  READY and Inscribe are the top green affordance; content update is a four-step Look/Validate/Load/Confirm
  workflow with a context-sensitive explicit action; and version/rollback maintenance is collapsed at the
  bottom. It builds cleanly, is hash-verified on OMEN, and awaits rendered visual acceptance.
- F9 now owns a configurable two-press backquote (`` ` ``) Charm ritual: CHECK captures the exact aimed ZDO and emits
  a receipt; the next press revalidates and CASTS onto that latched object, so later cursor movement cannot
  retarget the write. Rejected targets remain in CHECK mode, and a bounded 20-row scrolling log retains
  captures, casts, duplicates, and failures. Middle mouse was rejected in live usability review because it is
  Valheim's kick/weapon-secondary input, and Ctrl+Space was rejected because it is already roll. Backquote is
  consumed only while F9 owns gameplay input.
- Engine-owned timers now use a Unity-free UTC due/ack store under Runtime state. `timer_start` and
  `timer_cancel` execute through stable action identities; due records survive reload until acknowledged;
  delivery emits the reserved `timer_elapsed` signal with a required stable `timer_id`, without adding it to
  the creator-event catalog. Version 1.4.0 is installed on OMEN for a one-edit, three-second, non-mutating
  timer acceptance. Its content hash is `1ade11f47726d099fd4b8c9490eb722a8b2152ae716d21f3b83d1d8987c3f917`.
- The first timer attempt exposed a binding-contract gap rather than operator error: a `sign_written`
  experience could be inscribed onto a generic wall. Experience bindings now optionally declare closed
  `target_kinds`; certification validates them and Runtime CHECK rejects incompatible targets before CAST.
  Timer version 1.4.1 declares `sign` only, preserving immutable 1.4.0 and using content hash
  `97311079733bcaff401f511d97faff16fd9bb29792d07a73038b06e6ed4def71`.
- OMEN then accepted 1.4.1 exactly: multiple wall CHECKs failed with `binding_target_incompatible`; sign
  `1:28416` was inscribed; one sign edit executed `message-start` and `timer-three`; the workflow advanced
  `ready → waiting`; and 3.10 seconds later `message-finished` executed and `timer-finished` completed.
  `timers.json` is empty after acknowledgement and the terminal workflow ignores later sign edits.
- The next candidate implements the reviewed mutation vertical. Certification uses a closed grant/spawn
  registry with per-item stack caps and the existing 16-object/30-metre bounds. Runtime verifies the live
  prefab component, retains the private solo/listen-host authority gate, marks every spawned ZDO with the
  content hash/action identity, records numeric ZDO IDs atomically, and clears only objects whose durable
  record and live marks still agree. Automated allowlist, cap, and cross-stage ledger tests bring the shared
  suite to 351 passing tests; Runtime builds with zero warnings.
- OMEN accepted 1.5.0 on sign `1:28416`: `message-cast`, `grant-wood`, `raise-floor`, and
  `cleanup-timer` executed; the transition advanced; five seconds later `clear-floor` and
  `message-cleared` executed and the workflow completed. Both timer and spawned-object ledgers finish empty,
  while all six stable action identities remain durably claimed. The live pass also exposed a non-fatal
  collection invalidation after spawning a `WearNTear`; Runtime now snapshots the loaded binding candidates
  before executing any action that can mutate that collection.
- The native peer harness now uses the product's intended v1 authority topology instead of the AM4
  dedicated cutover lab: OMEN hosts an ordinary private listen world and i5 joins through Steam Friends.
  The harness deploys and hashes the same Runtime, Contracts, and immutable pack on both clients, snapshots
  both receipt sets, requires the six-action OMEN lifecycle plus terminal completion, requires i5
  `mutation_authority_unavailable` with zero peer actions, and restores both Quest Runtime configs exactly.
  It contains no AM4, Docker, Gateway, or NetworkSense configuration operations.
- Native run `quest-peer-20260810-native-r2` passed the paired authority gate. OMEN, as an ordinary private
  listen host, activated content hash `1dbfaffa178a920325f19f00e8ba69abd52a82114d9447572afe3ea7a5776a5c`,
  executed `message-cast`, `grant-wood`, `raise-floor`, `cleanup-timer`, `clear-floor`, and
  `message-cleared`, then emitted terminal transition status `complete`. i5 activated the identical version
  and hash, rejected Charm checks with `mutation_authority_unavailable`, and executed zero actions.
- That run exposed a packaging dependency that OMEN already carried: i5 lacked `Newtonsoft.Json.dll`, so
  Runtime loaded but its content UI threw before drawing and F10/F11 could not deserialize content. The
  harness now stages and SHA-256 verifies Runtime, Contracts, and Newtonsoft together; the repaired i5 UI
  rendered normally. The collector also accepts the emitted terminal status `complete` as well as the older
  compatibility spelling `completed`.

### Partially implemented

- Studio now stores immutable content-hash-addressed certified snapshots, lists up to 100 versions, and
  produces a structured field diff between any two snapshots. Rich graph-level visualization remains.
- Action names and closed per-type parameter schemas are validated with bounded message, counter, timer,
  grant, spawn, clear, and lifecycle parameters. Runtime authority/execution/persistence now covers message,
  timers, capped grants, bounded spawns, and marked cleanup; counters, Arcane Sight, and lifecycle actions remain.
- Runtime has the compact drawer, receipts, inscription, version selection, and rollback controls, but not
  Replace/Unbind, Arcane Sight, or stage controls.
- The canonical 34-event catalog now lives in `ComfyQuestContracts`, with an automated parity check against
  the older schema-1 catalog while NetworkSense and Lab compatibility remains in place.

### Not implemented yet

- Rich Quest Studio graph editor, full Grimoire cards, and simulation. The initial one-stage structured page,
  durable project store, immutable version history, and semantic field diff are implemented.
- Companion download fallback UI (the authenticated publish endpoint and certified atomic inbox write exist).
- Replace/Unbind and Arcane Sight resolution; basic Charm references, aim, ownership, and Inscribe exist.
- Counter, Arcane Sight, and lifecycle action executors. Rewards, spawns, marked cleanup, durable timers, and the general stage machine are implemented and automated;
  its two-stage OMEN acceptance is complete. The one-stage message executor, in-session duplicate
  suppression, explicit hot-loading, and rollback are live-witnessed.
- Event archive replay, pack certification UI, schema-1/Spell String import/export.
- Lab default-tab reduction and Advanced migration switch.
- Complete OMEN browser-originated publication and rollback acceptance.
- The paired OMEN-listen-host/i5-Steam-peer live acceptance is complete. Retain it as a regression gate while
  finishing Studio publication and Lab migration.

The milestone coloring in the [implementation overview](quest-studio-runtime-implementation-overview.svg)
uses green for implemented foundations, amber for partial seams, and gray for planned work.

## Immediate next slice

The next work should finish Milestone 1 and then prove Milestone 2 vertically rather than expanding
individual surfaces horizontally:

1. Keep schema-1 compatibility pinned while adding import/export helpers around the shared canonical catalog.
2. Add pack certification UI that surfaces the new archive and action diagnostics directly in Studio.
3. Complete browser-originated publication and receipt refresh, then preserve that evidence through rollback.
4. Reduce Lab's default surface and keep the completed native listen-host/peer run as the multiplayer
   regression gate.

That order keeps every new UI control attached to an executable, testable contract and produces a usable
end-to-end system early, while the safety-sensitive mutation surface remains small.
