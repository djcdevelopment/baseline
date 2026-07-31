# Remote player lifecycle map

This is the C8 architecture gate that the earlier funnel-oriented netcode map
did not provide. `NETCODE-MAP.md` correctly maps transport, handshake, ZDO, routed
RPC, and ownership seams; this document maps the semantic object those seams used
to produce: a remote `Player` that remains valid from admission through teardown.

**Current binary inspected:** local Valheim `assembly_valheim.dll`, dated
2026-07-01, protocol 36 / release 0.221.12.

**External corroboration:**

- [Valheim Networking Wiki](https://github.com/MarvelProgramming/Valheim-Networking-Wiki/wiki)
  inventories `ZNet`, `ZDO`, `ZDOMan`, `ZNetScene`, `ZNetView`, and
  `ZSyncTransform`. It is useful structural documentation, but its pages were last
  edited in 2023 and do not describe the complete player lifecycle.
- [Jötunn's generated 0.221.12 prefab list](https://valheim-modding.github.io/Jotunn/data/prefabs/prefab-list.html)
  shows that `Player` contains `PlayerController`, `Player`, `ZNetView`,
  `ZSyncTransform`, `ZSyncAnimation`, `Talker`, `VisEquipment`, `Skills`, and
  `FootStep`; remote-player realization is not just a transform.
- [Iron Gate's asset-bundle FAQ](https://www.valheim.com/support/modding-faq-for-the-asset-bundle-update-0-217-40/)
  says `ZNetScene` retains its prefab assets in memory. Missing remote players in
  the C8 attempt were therefore lifecycle/state failures, not an asset-load race.

## Vanilla producer graph

```text
authenticated ZNetPeer
  -> Game.SpawnPlayer creates the locally owned Player prefab/ZDO
  -> ZNet.SetCharacterID associates that ZDOID with the peer
  -> ZDO replication creates the same non-owned ZDO on observers
  -> ZDOMan's sector index makes it visible to interest queries
  -> ZNetScene instantiates Player and binds ZNetView to that ZDO
  -> Player + ZSyncTransform + ZSyncAnimation + VisEquipment consume its state
  -> ZDO position changes migrate the sector index
  -> peer/character replacement or interest exit destroys the scene instance
```

Current assembly facts behind that graph:

- `Game.SpawnPlayer` instantiates `m_playerPrefab`, marks it local, loads profile
  data, then calls `ZNet.SetCharacterID(component.GetZDOID())`.
- `ZNet.RPC_CharacterID` only assigns `peer.m_characterID`; it does not create or
  publish the character ZDO.
- `ZDOMan.RPC_ZDOData` creates an absent ZDO, applies identity/owner/revisions,
  calls `InternalSetPosition`, and deserializes its body.
- `ZNetScene.CreateDestroyObjects` selects ZDOs from `ZDOMan.FindSectorObjects`;
  `CreateObject` instantiates the prefab with `ZNetView.m_initZDO`; `RemoveObjects`
  destroys instances absent from the current near/distant sector sets.
- `ZDO.InternalSetPosition` calls private `SetSector`, which removes and re-adds
  the ZDO in `ZDOMan` when it crosses a 64 m zone boundary.
- `Player.FixedUpdate` destroys an owned player that is not
  `Player.m_localPlayer`. An observed player must remain non-owned locally.
- `VisEquipment` reads model, color, hair, beard, armor, held, and stowed item
  fields from the ZDO. `ZSyncAnimation` reads continuous parameters from the ZDO
  and receives triggers through routed RPC.

## C8 replacement/coverage matrix

`PROVEN` means live two-client evidence exists. `PARTIAL` means the required
component exists but does not yet own the complete lifecycle contract. `OPEN`
means no canonical producer currently supplies the vanilla invariant.

The replacement is per-observer, not a region-wide player broadcast. The two
channels carry different clocks:

| Information | Lane | AoI behavior |
|---|---|---|
| Thin roster identity | reliable | Region/session scoped; no render-heavy state |
| Player generation enters interest | reliable | One complete descriptor to each observer entering that player's AoI |
| Appearance/equipment changes | reliable | Delta only to current observers; snapshot is part of later AoI entry |
| Position/rotation/velocity | datagram | Near every tick, mid throttled, far omitted |
| Hard correction/teleport | reliable | Current observers, followed by subscription recomputation |
| Player generation leaves interest | reliable | Per-observer suspend/tombstone; permanent leave retires the generation |

Reliability does not imply broadcast. `InterestManager` currently filters only
datagrams, so the Valheim adapter must use its subscription transitions to target
reliable player descriptors and tombstones. Sending the complete Player state to
every session would merely recreate Valheim's early scaling mistake on a new
transport.

| Lifecycle invariant | Vanilla producer / consumer | Lumberjacks owner now | State | C8 gate |
|---|---|---|---|---|
| Admission and durable principal | handshake -> `ZNetPeer` | authenticated game session + logical peer | PROVEN C7 | Preserve poison/native-zero evidence |
| Local character identity | `Game.SpawnPlayer` -> `SetCharacterID` | local Valheim creation + typed logical control | PROVEN C7 | Preserve exact ZDOID receipt |
| Entity identity authorization | server associates peer and character ZDOID | motion accepts the first ZDOID asserted by an authenticated session | **OPEN** | Motion ZDOID must equal that session's registered character ZDOID |
| Remote player ZDO publication | `RPC_ZDOData` creates/deserializes full body | motion-side seed prototype | **PARTIAL** | Define one canonical descriptor per character generation and deliver it on each observer's AoI entry; do not infer existence from motion |
| Observer ZDO registry | `m_objectsByID` | seed uses current `CreateNewZDO` | PARTIAL | One ZDO per logical character; idempotent create/update |
| Sector membership/residency | `InternalSetPosition` -> `SetSector` -> `ZDOMan` index | seed adds only the initial sector | **OPEN** | Every accepted canonical move updates backing ZDO position/sector |
| Canonical write discrimination | native `ZSyncTransform` owns ZDO position | Harmony mask blocks all known-remote `InternalSetPosition` calls | **OPEN** | Scoped canonical-write bypass; continue rejecting native writers |
| Scene realization | `ZNetScene` prefab lookup/create/bind | delegated to unchanged `ZNetScene` | PROVEN in short canary | Require one stable instance, correct prefab, non-owned view |
| Ownership validity | remote replicated owner -> non-owned observer | seed assigns remote ZDO user as owner | PARTIAL | Prove owner is never local and survives resume/rebind without old-local destruction |
| Server reference position | `ServerSyncedPlayerData` updates `ZNetPeer.m_refPos` every 2 s | logical peer initializes it to `(0,0,0)`; motion does not update it | **OPEN** | Authenticated motion updates server peer ref-pos before interest/ownership work |
| Server character ZDO | server receives player ZDO through replication | server has character ID but no canonical player ZDO | **OPEN** | Decide which server consumers require a player ZDO and supply one descriptor/state owner |
| Player roster | `SendPlayerList` / `RPC_PlayerList` | no complete direct-control replacement | **OPEN** | Both clients and server agree on two names, IDs, public positions, join/leave |
| Server-synced player data | periodic ref-pos/public/base/event data package | no complete replacement | **OPEN** | Classify required gameplay fields; deliver or explicitly retire each |
| Motion presentation | `ZSyncTransform` owner/client sync | numbered motion + reliable hard resync | PROVEN C6 and short C8 canary | Keep native writer and fallback at zero |
| Animation presentation | `ZSyncAnimation` ZDO fields + routed triggers | no canonical animation state | **OPEN for C9** | Walking/running/turning and one trigger render on both observers |
| Equipment/appearance | `VisEquipment` ZDO fields | seed supplies only name/player ID | **OPEN for C9** | Model/colors/hair/beard/equipment have a snapshot + delta owner |
| Gameplay routed RPCs | component registrations on `ZNetView` | routed semantic lane is shape-bounded | PARTIAL | Matrix every Player-prefab consumer; reject unsupported shapes visibly |
| Teleport/large relocation | ZDO position immediately changes sector | GameObject-only motion apply | **OPEN** | Cross at least one 64 m boundary without destroy/reseed |
| Death/respawn character replacement | old Player destroyed; new ZDOID registered | motion session binds its first ZDOID permanently | **OPEN** | Authenticated character-generation transition retires old ID and admits new ID |
| Temporary transport resume | native peer remains semantic identity | durable logical session resumes; current socket loss emits detach first | PARTIAL | No duplicate player, stale ZDO, or false permanent leave |
| Permanent leave/teardown | peer removal + ZDO invalidation/destruction | no observer-facing player tombstone/TTL in motion lane | **OPEN** | AoI leave suspends/removes only that observer's instance; permanent leave retires the generation exactly once |
| Server gameplay consumers | zones, ownership, sleep, random events, range checks use peer/ZDO state | currently see origin, missing ZDO, or empty synced data | **OPEN** | Exercise representative consumers after moving away from origin |

## Immediate implications

The short native-zero canary proved that reusing Valheim's `ZNetScene` and Player
prefab is viable. It did **not** promote the seed prototype:

1. The duplicate `logical_remote_seeded` event is predicted by the missing sector
   update: `RemoveObjects` evicted the instance when its stale ZDO sector fell out
   of the active set.
2. Updating only the Unity transform cannot fix this. The backing ZDO must move,
   and the native-position mask needs an explicit canonical-writer scope so it
   does not block that correct update.
3. Motion must consume an already-authorized character generation. It must not
   create identity by trusting the first ZDOID in a datagram.
4. Remote-player creation and deletion need reliable descriptor/tombstone
   semantics. Datagram motion can update an existing generation but should not be
   the sole source of existence.
5. C8 should first prove identity, descriptor, residency, and teardown with a
   short real canary. Appearance/animation remain visible C9 work, but their
   ownership and snapshot shapes must be named now to avoid another hidden native
   dependency.

## Next short canary

Before the two retained C8 runs, use OMEN and i5 to prove:

1. both registered character IDs match the motion-bound IDs;
2. each observer creates exactly one non-owned remote Player from a reliable
   descriptor;
3. both players cross a zone boundary and return without destroy/reseed;
4. AM4 peer reference positions track both clients away from origin;
5. a forced game-session resume preserves one instance;
6. an explicit permanent leave removes the remote instance;
7. no selected native writer, ZDO delivery, handshake, or socket use occurs.
