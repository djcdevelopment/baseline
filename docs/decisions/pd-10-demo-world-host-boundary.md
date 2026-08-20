# PD-10 — The Demo World is a versioned bridge to host Valheim

- Status: Accepted
- Owner: Derek
- Date: 2026-08-20

## Decision

The Comfy Quest Demo World has three deliberately separate authorities:

1. `isolate` is the workshop and distribution owner. It holds the immutable
   canonical world artifact, its manifest, the host-visible exchange seam, and the
   bounded provision/status/reset tooling.
2. `comfy-quest` owns Studio, Quest Lab, Runtime, the editable tutorial source, the
   compiled experience, the production Runtime package, and expected receipt
   contracts.
3. A normal host-installed Valheim client is the execution surface. A graphical or
   GPU-connected game client inside Docker is not a dependency of the creator loop.

File transfer is the portability floor. MCP may discover, validate, or move the same
versioned artifacts, but it does not introduce another quest or world format.
The named shared exchange is `COMFY_QUEST_RUNTIME_HOST_DIR`: normally the installed
mod's `BepInEx/config/comfy-quest-runtime` root. Isolate Compose mounts those exact
host bytes at `/lab/comfy-quest-runtime` and exposes that container path as
`COMFY_QUEST_RUNTIME_DIR`. It is the existing Runtime v2 inbox/receipt/state contract,
not a generic file browser or a second Quest Lab mailbox.

The canonical world is immutable. Provisioning creates a disposable local deployment;
ordinary play may change that deployment but never its canonical source. Reset is an
explicit, receipted, recoverable replacement of that one world pair. It never sweeps a
Valheim save directory.

The first adapter supports only the Windows Steam default build `0.221.12` (Steam
build `21981559`) and the classic `<basename>.db` plus `<basename>.fwl` save pair.
Unknown builds and the new chunk-directory format fail closed. A later format requires
a separate adapter and a new physical acceptance run; it is not inferred from this
contract.

No character save is part of the artifact. A world reset resets world bytes only. It
does not reset character inventory, skills, map, bed/logout/spawn state, or Comfy Quest
Runtime progress. Arrival at the world start is guaranteed only for a character new to
the world UID. Until Comfy Quest has a content-scoped replay operation with live proof,
a repeated canonical tutorial lap uses a demonstrably fresh world/character/binding/
content identity rather than deleting broad Runtime or character state.

## Why

The host game is the only representative proof of Unity, BepInEx/Harmony, live ZDO
ownership, portal behavior, and in-game legibility. Putting the client in the disposable
container topology would add GPU, Steam-session, input, and rendering failure modes
without strengthening the artifact contract.

Conversely, an informal save copied by name is unsafe. Valheim groups logical world
names case-insensitively across cloud, local, legacy, and backup saves; a cloud save may
silently remain primary over a newly dropped local pair. Valheim also writes the classic
pair asynchronously. Provision and reset therefore require a stopped game, collision
inventory across all known save sources, exact identity and hashes, an external
deployment receipt, bounded recovery copies, and a transaction journal.

The product boundary matters just as much as the filesystem boundary. Quest source and
Runtime packages remain Comfy Quest artifacts. Isolate may vendor a pushed artifact
only with its immutable upstream revision, byte count, and SHA-256 digest. That keeps a
fresh Isolate useful without turning it into a second writable quest authority.

## Rejected alternatives

1. **Run the playable Valheim client in Docker.** Rejected because it makes GPU and
   graphical container support a prerequisite while still failing to replace a real
   host-game acceptance run.
2. **Ship an informal developer save and copy instructions.** Rejected because it has
   no immutable identity, collision handling, reset boundary, or reproducible proof.
3. **Create an MCP-specific quest format.** Rejected because transport would become a
   second source of truth and file-only use would drift.
4. **Ship or overwrite a tutorial character.** Rejected because character state is
   personal, cross-world, and broader than the Demo World lifecycle.
5. **Treat world reset as full tutorial reset.** Rejected because both Valheim character
   saves and Comfy Quest Runtime retain state outside the world pair. Claiming otherwise
   would make a byte-perfect reset behaviorally misleading.
6. **Assume the classic pair survives the next game update.** Rejected because Iron
   Gate's `0.221.13` Public Test has already moved worlds to chunk directories.

## Contract consequences

- The world manifest pins basename, display name, signed 64-bit UID as a decimal string,
  save adapter, game/build versions, byte counts, SHA-256 hashes, builder provenance,
  paired quest artifact provenance, and separate machine/live evidence labels.
- Fresh provisioning refuses any same logical name in local, legacy, or Steam Cloud
  storage, including recognized backups, and refuses to assume exact quest activation
  from a nonempty Runtime inbox/active state.
- Provisioning and reset refuse while `valheim` or `valheim_server` is running. A reset
  requires the matching receipt and parsed world identity, preserves the active bytes in
  an external recovery directory, and can recover an interrupted two-file promotion.
- The first tutorial uses the public creator path: a schema-v3 Studio project, a
  certified `comfy-quest-experience/v1` document, and a real
  `comfy-quest-pack/v2` package. Import opens a new fork rather than mutating the
  canonical source.
- Machine validation proves structure, hashes, bounded writes, reset/recovery, package
  validity, and contract drift. Only an actual host-Valheim lap can promote world load,
  arrival, portal, Charm binding, gameplay receipts, visual clarity, and replay claims
  to VERIFIED.

## Current evidence status

- **VERIFIED:** Isolate `b14e2c1` publishes the privacy-scanned canonical
  `ComfyQuestDemo.db`/`.fwl` pair, manifest, production-bundle regression test, and
  deterministic Runtime v2 tutorial package. The final display name is
  `Comfy Quest Demo`, the signed world UID is `-7600395338659582326`, and the
  classic-pair adapter remains pinned to Valheim `0.221.12` / Steam build
  `21981559`.
- **VERIFIED:** stopped-game provisioning completed through the public Isolate CLI.
  The deployed pair matched the canonical hashes, the external deployment receipt
  validated, the exact tutorial package was delivered create-only, and unrelated
  Runtime content was preserved.
- **VERIFIED on the authoring identity:** two ordinary-Valheim laps proved exact
  Runtime activation, fixed-crosshair Charm CHECK/CAST, targetless portal completion,
  and the expected gameplay receipt chain. Comfy Quest `afc7ab8` then rebuilt r28 at
  the previously captured Gallery site with 1,916/1,916 objects loaded and ceiling
  clearance passing.
- **UNVERIFIED:** the renamed final world/UID has not received its first cold load.
  The r28 breadcrumb path has objective topology evidence but not final human visual
  acceptance. A world-only reset still cannot promise clean tutorial replay because
  character state and Runtime workflow state are external.
- **VERIFIED compatibility boundary:** installed/default Valheim `0.221.12` uses the
  classic pair. Iron Gate's `0.221.13` Public Test replaces it with per-world chunk
  directories and warns against manual movement between Public Test and Live; that
  format requires a separate adapter and acceptance run.

## Related

- [PD-4 — What counts as proof](pd-4-evidence-standard.md)
- [PD-8 — Isolated runtime and toolset repository architecture](pd-8-isolated-runtime-and-toolset-repository.md)
- [PD-9 — Sovereign add-on repositories with Baseline as the hub](pd-9-repository-split.md)
- [Isolate Demo World / Tutorial World cold-drop builder brief](../arch/isolate_demo_world_cold_drop_agent_brief.md)
- [Iron Gate save guidance](https://steamcommunity.com/app/892970/discussions/0/591774445091193259/)
- [Iron Gate `0.221.13` Public Test announcement](https://steamcommunity.com/ogg/892970/announcements/detail/508485755865137731)
