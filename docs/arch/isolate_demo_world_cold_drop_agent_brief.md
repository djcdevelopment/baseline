# Isolate Demo World / Tutorial World — Cold-Drop Builder Brief

## Mission
Design the smallest durable Demo World foundation for Comfy Quest + Isolate. This comes before expanding AI-assisted semantic/world-scanning features. Establish a stable, resettable Valheim world shipped with or provisioned by Isolate and use it to dogfood the real creator loop.

Assume: Comfy Quest owns Studio, Quest Lab/Runtime, contracts, creator tooling, package generation and artifact lifecycle. Isolate is the disposable Docker workbench containing tooling, telemetry, MCP services and utilities. Valheim remains a normal host-installed game/client. The Demo World bridges the disposable tooling environment and the real game.

## Human-readable summary
A creator should be able to provision Isolate, obtain a known-good Demo World, load it with normal Valheim, and immediately have a controlled place to learn, experiment, break things, reset, and build quests.

The world should evolve into a small Quest Zone: a portal-linked collection of intentionally designed areas where each area demonstrates one quest primitive or composition. A creator can play an example, inspect its Studio artifact, change something, reload it, and see the consequence.

> play it -> inspect it -> tweak it -> understand it -> build with it -> share/fork it

The world is simultaneously onboarding, dogfood environment, acceptance surface, example corpus, future evaluation/training corpus, MCP/file-transfer playground, and community starter world.

## Core product decision
Do not make a playable GPU-connected Valheim client inside Docker a requirement.

Treat the system as three layers:

1. **Isolate = workshop.** Owns Studio support, MCP, telemetry, schema/compiler/validation tooling, artifact exchange, provisioning/reset helpers, and canonical Demo World assets.
2. **Host Valheim = execution surface.** The user runs the actual game normally, preserving normal GPU/game behavior.
3. **Demo World = curriculum + stable test artifact.** A versioned save distributed/provisioned through Isolate containing the physical spaces needed to demonstrate creator concepts.

The world must remain useful when MCP is unavailable.

## Primary objective
Prove a creator can go from fresh/reprovisioned Isolate to a playable known-good Demo World with a simple workflow and then use it for normal Comfy Quest authoring/testing. Optimize first for reliability, inspectability, resetability and low setup friction—not maximum automation.

## Transport model: file first, MCP richer
### File transfer / exchange directory
This is the portability baseline and must be sufficient for core use.

```text
Isolate / Studio
      |
      | quest JSON / packages / receipts / scan artifacts
      v
shared exchange directory
      |
      v
local Valheim + Comfy Quest mod
```

Use a predictable host-visible exchange directory. Studio/compiler writes normal versioned quest artifacts; the mod consumes them through supported activation/import; Runtime can return receipts/results. Use atomic writes where needed. Do not create an AI- or MCP-specific quest format.

### MCP
MCP is the richer agent/development path and may support live inspection, world scanning, artifact discovery, validation, hotload/dev activation, telemetry, receipts, semantic request decomposition and agent iteration.

MCP must operate on the same contracts/artifacts as file mode. MCP is transport/control, not truth.

## Demo World design thesis
Use a compact hub-and-spoke world, not a giant showcase. Start with a recognizable Creator Hub and portals to small isolated teaching/test zones. Each zone answers one clear question and is cheap to reset. Users should experience a working example before needing to understand its structure.

Do not build twenty zones immediately. Establish the topology and prove the pattern.

```text
                     +--------------------+
                     |   CREATOR HUB      |
                     | portals + signage  |
                     +---------+----------+
                               |
       +-----------------------+-----------------------+
       |                       |                       |
       v                       v                       v
+--------------+        +--------------+        +--------------+
| BASIC EVENT  |        | TIMED EVENT  |        | WORLD TARGET |
| simple beat  |        | countdown    |        | bind/cast    |
+--------------+        +--------------+        +--------------+
```

## Candidate zones — backlog, not first-landing requirements
- **Creator Hub:** orientation, portal navigation, play/inspect/modify loop, safe return/reset instructions.
- **Minimal event:** smallest creator interaction with an observable result; change one value/copy and see it immediately.
- **Timed event:** countdown, duration, success/failure timing, visible Runtime feedback; later grace periods.
- **Defense/escalation:** waves, escalation, threshold/progress, timer, completion/failure.
- **Mercy/retry:** failure, retry/grace, altered second attempt, explanation of what changed.
- **World target/Charm binding:** identify object, CHECK/CAST or equivalent, target legibility, behavior tied to concrete world state.
- **World scan playground — future:** deliberately known object counts/arrangements, e.g. Black marble tile: 26; Wood: 2; Portal: 6; Kiln: 1. This becomes scanner acceptance terrain later; do not block the foundation on scanning.

## World/save artifact contract
Treat the Demo World as a versioned product artifact, not an informal developer save. Determine and document:

- exact Valheim world/save files required;
- whether character state is needed or independent;
- expected world name;
- Valheim version compatibility assumptions;
- canonical source location in Isolate/release assets;
- checksum/hash strategy;
- existing-copy detection;
- overwrite/version/fresh-copy policy;
- reset procedure;
- upgrade/migration behavior.

Prefer immutable canonical source assets plus disposable deployed copies. Normal play must never modify the canonical source.

## Provisioning target
Aim approximately for:

```text
clone/pull Isolate
 -> run setup/provision
 -> config/secrets handled
 -> Demo World materialized to documented local location
 -> exchange path created/configured
 -> launch normal Valheim
 -> select Demo World
 -> Creator Hub ready
```

Always surface where files were placed. If automatic installation into Valheim saves is brittle or dangerous, prefer a clearly identified deployable artifact plus a small explicit copy/install step.

## Reset philosophy
Resetability is a product feature. Encourage experimentation because destroying the environment is cheap.

Target two reset levels if practical:

- **Tooling reset:** reprovision Isolate without affecting unrelated user data.
- **Demo World reset:** replace only the active Demo World copy with canonical known-good bytes.

Never broadly delete a user's Valheim save directory. Use explicit world identity, expected filenames, hashes, sentinel metadata or similarly strong boundaries.

## Quest artifact pairing
Each tutorial zone should eventually have a canonical creator artifact:

```text
zone/
  manifest/readme
  quest source/project artifact
  compiled/certified quest JSON
  expected behavior
  expected receipts/assertions
  optional screenshots/reference
```

The world and quest must not become inseparable. Creators must be able to fork/edit the quest independently. Give zones stable IDs/names where possible.

## Dogfooding requirement
The primary creator should build future tutorial simulations using the same public creator loop users receive. Avoid privileged developer-only paths when normal Studio/Runtime can perform the operation.

If tutorial construction repeatedly requires bypassing Studio, hidden Runtime edits, or undocumented machinery, treat that as evidence that the creator loop needs refinement. Capture the friction rather than normalizing it.

## Human validation points
Human judgment is expected at these boundaries:

1. **Physical composition:** navigation clarity, visual hierarchy, arrival comprehension, zone separation, signage density, whether it feels like a playground rather than a fixture.
2. **Tutorial sequencing:** whether progression actually teaches the system; machine-valid ordering is not sufficient.
3. **Creator friction:** tedious steps, unclear terminology, excessive UI switching, unexpected documentation dependence, scary reset/retry behavior, poor feedback.
4. **Live Runtime proof:** browser/synthetic tests cannot prove Unity, BepInEx/Harmony, live ZDO state, ownership/network behavior, in-game legibility or pacing.

## UI integration guidance
Do not build a separate Demo World editor/UI unless evidence demands it. Prefer small additions to existing Studio surfaces: identify tutorial-zone artifacts, show zone purpose, distinguish canonical source from user fork, expose expected behavior/receipts and reset/reload guidance, and later link scan observations.

The Demo World should primarily be navigated in-game. Studio explains and edits the artifact behind what the player just experienced. Do not duplicate the portal map as a large Studio navigation product without evidence.

## Container / Windows / GPU bounds
Assume:

- Isolate runs Dockerized services/tooling.
- A dedicated Valheim server may run headless/containerized later, but is not required here.
- The playable Valheim client remains outside Docker.
- Windows Docker GPU passthrough/graphical game execution is not a dependency.
- Tailscale/remote hosting is optional future capability, not local tutorial infrastructure.
- Multiplayer/server-hosted Demo World support comes after the local creator loop is stable.

Prefer a simpler recoverable local workflow over an impressive fragile topology.

## Verification strategy
### Machine-testable
- canonical world assets and manifest exist;
- hashes match;
- provisioning writes only to bounded destinations;
- reset restores expected canonical files;
- exchange directory is correct;
- canonical quest artifacts validate;
- file-transfer round trips work;
- MCP/file paths use equivalent schemas;
- zone manifests/IDs are consistent.

### Live/manual
- world loads in Valheim;
- player arrives at expected hub;
- portals resolve;
- tutorial quest actually runs;
- Studio edits reach Runtime through intended creator path;
- reset produces a clean replayable state;
- instructions work without developer knowledge.

Keep live-only claims live-only until a real test seam exists.

## First vertical slice
Prove exactly this journey before expanding:

> Fresh Isolate checkout/provision -> canonical Demo World materialized -> user loads it in normal Valheim -> arrives at Creator Hub -> enters one portal -> plays one minimal quest -> opens matching artifact in Studio -> changes one obvious property -> transfers/activates revision -> replays and sees the change -> resets Demo World/artifact to known-good state.

That proves the foundation. Everything else is expansion.

## Suggested implementation sequence
1. Inventory current world/save handling, Quest Lab/Runtime exchange paths, hotload behavior, MCP capabilities, package formats, and old provisioning/test-world scripts.
2. Define the Demo World artifact contract: filenames, version, manifest, hashes, deployed-copy identity, safe reset boundaries.
3. Build provisioning/reset before elaborate content.
4. Create the smallest Creator Hub: one clear arrival area and one portal.
5. Create one tutorial zone using the simplest reliable quest behavior.
6. Pair it with its canonical Studio artifact, compiled output, expected behavior and receipts.
7. Prove file-transfer mode end-to-end.
8. Expose equivalent operations through MCP where useful; do not fork the artifact model.
9. Dogfood the full loop and record friction. Refine Studio/Runtime before adding breadth.
10. Expand curriculum only when the creator loop asks for it: timers, defense, escalation, mercy, world binding, scanning, richer agent assistance.

## Explicit non-goals for this landing
- Graphical Valheim client inside Docker.
- GPU passthrough requirement.
- Tailscale/remote hosting requirement.
- Ward/radius scanner implementation.
- Semantic AI request parser implementation.
- Model training.
- Giant polished tutorial campaign.
- Every quest primitive.
- Unsafe automation of user save directories.
- Second artifact format for MCP.
- Second editor for tutorial content.

## Design principles
1. **Artifacts over services.** Worlds and quests remain useful outside any one runtime/tool.
2. **File mode is the portability floor; MCP is acceleration.**
3. **Canonical source is immutable; deployed copies are disposable.**
4. **Teach through working examples.**
5. **Dogfood public paths.** Friction is evidence.
6. **Machine proof and seat proof are different.**
7. **Reset must be safer than manual cleanup.**
8. **Do not overbuild before the first complete creator journey works.**

## Builder decision rule
When uncertain, choose the implementation that makes the Demo World easier to understand, inspect, reset, fork and use without privileged tooling—even if a more automated solution appears technically impressive.

## Exit condition
This foundation is successful when a cold user can provision a known-good Demo World, load it in ordinary Valheim, experience one tutorial quest, alter that quest through the normal Studio creator path, observe the changed behavior, and safely return both the quest and world to a known-good state.

Only after that loop is trustworthy should the project spend significant effort on richer tutorial zones, world reconstruction/scanning, semantic AI assistance, or autonomous agent creation.

## 2026-08-20 implementation handoff

The foundation is implemented and pushed, but the full exit condition above is not
yet claimed.

### Landed authorities

- `isolate` `b14e2c1` owns the immutable `ComfyQuestDemo` world pair, production
  manifest, deterministic tutorial package, production-bundle regression test, and
  stopped-game provision/status/reset CLI. Earlier safety foundations are `40ce2ca`
  and `bfde1db`.
- `comfy-quest` `f480f5f` owns the importable Studio source, compiled experience,
  deterministic Runtime v2 package, and receipt expectations. `afc7ab8` is the r28
  Gallery builder that reuses the existing captured site rather than rebuilding at
  the player's incidental position.
- Baseline PD-10 is the durable authority for the three-repository/host boundary and
  the intentionally narrow world-only reset meaning.

### Proven

- The canonical pair is privacy-scanned, hash-pinned, format-pinned, and contains no
  character save.
- Stopped-game provisioning is create-only, collision-aware across local/legacy/cloud
  saves, externally receipted, recoverable, and preserves unrelated Runtime content.
- Two live source-identity laps completed the First Portal quest through the public
  Runtime path. The target is an immediately visible `CAST HERE` sign; CHECK and CAST
  use Valheim's fixed center crosshair and require the F9 drawer to remain open.
- r28 keeps the prior Gallery origin, faces the upper ascent portal toward the target,
  removes the birch obstruction, and uses three low Arcane Sight breadcrumbs plus one
  restrained school-colour ground torch. Machine evidence reported 1,916/1,916 loaded
  Gallery objects and passing ceiling clearance.

### Safe shutdown state

- The final `Comfy Quest Demo` pair was provisioned successfully with UID
  `-7600395338659582326`; its deployment receipt validated and the exact
  `demo-world-first-portal` `1.0.0` package was delivered to the existing Runtime
  inbox without deleting unrelated packs.
- Valheim was stopped before this handoff. Canonical repository bytes are immutable;
  do not rebuild or recapture the world merely to resume acceptance.

### Remaining plan

1. Cold-load `Comfy Quest Demo` once with a character new to that world UID and record
   whether arrival and the r28 breadcrumb/sign composition are immediately legible.
   This is one human visual judgment, not another full Charm tutorial lap.
2. If accepted, record the cold-load receipt/evidence without replacing the canonical
   bytes. If rejected, change only the smallest visual composition element and rebuild
   at the captured site.
3. Separately prove the Studio import -> edit -> Play -> automatic same-fork rebind
   loop in ordinary Valheim. Synthetic Studio coverage is already green; it is not a
   substitute for the live creator-friction judgment.
4. Do not claim reset/replay completion until Comfy Quest has a narrowly scoped,
   live-proven Runtime workflow reset or the acceptance procedure deliberately uses a
   fresh world/character/binding/content identity.
5. Add a separate save adapter before supporting Valheim `0.221.13` or newer
   chunk-directory worlds; fail closed meanwhile.

The next operator should automate every repeatable setup/evidence step. Derek's seat
time is reserved for the single visual or interaction judgment that cannot be derived
from receipts.
