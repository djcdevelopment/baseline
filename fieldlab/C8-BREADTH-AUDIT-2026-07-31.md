# C8 breadth audit — RPC and prefab surface classification — 2026-07-31

This is the explicit breadth audit C8 carries per the plan ("C8 now includes the
explicit breadth audit"; C5 replan: "reopen the owning slice for any unadmitted
native method"). It classifies every statically discoverable native RPC
registration and every ZNetView/ZSyncTransform-bearing component against the
replacement architecture, and it resolves the root `DECISIONS-PENDING.md` entry
"Lumberjacks RPC Admission Gaps".

## Provenance and method

- Instrument: `tools/synthetic-baseline-extractor` **v2** (adds the
  `ZNetView.Register` instance-RPC scan v1 lacked, registration attribution,
  payload signatures, inherited-field component walk, unresolved-name
  accounting). Deterministic across runs; `unresolved_registrations: []` —
  every registration in the assembly resolved to a literal name.
- Assembly: `assembly_valheim.dll` sha256
  `3b26c8512778f6e0664b5af2a26f3c30993a00f584c1e76d9123a742b67e2004`.
- Output: `tools/synthetic-baseline-extractor/synthetic_baseline_v2.json`
  (19 routed + 21 direct + **120 instance** RPCs, 122 components).
- First-pass classification drafted by HEARTH (`gemini-3.1-pro`, artifact
  `art_40ef58c9015d9d7a343b48f87f7f2916`); every `superseded` claim and all
  priority calls reviewed here against the v2 attribution data. Review deltas
  are listed explicitly below — the machine draft was wrong or overconfident on
  six rows.
- Dynamic cross-check: the native-use ledger classifies by envelope only
  (`RoutedRPC` is one bucket), so observed per-method frequency does not exist;
  the **poison ledger remains the runtime tripwire** for anything classified
  wrongly here. v1's lists (19+21) are confirmed a strict subset of v2's.

## Review deltas from the machine draft

| Row | Draft said | Audit says | Why |
|---|---|---|---|
| `SpawnObject` (routed) | deferred (admin/cheat) | **needs-lane P2** | Registered by `ZNetScene.Awake` — core scene machinery, not a console path. |
| `RPC_TeleportPlayer` (routed) | needs-lane P1 | **verified deferred-with-poison-guard** | The only pinned outbound caller is Terminal's cheat-only, admin-only, non-network `recall` command. Portal travel rides `RPC_TeleportTo` (instance), and both r4 physical clients completed two-way traversal under poison without invoking this method. |
| `UseStamina` (instance) | needs-lane P1 | **needs-lane P3 [VERIFY]** | Registered by `Player.Awake`; stamina spend is normally owner-local. The remote-invoke paths are rare. |
| `RequestControl` / `ReleaseControl` / `RequestRespons` (instance) | superseded by ownership-lease | **verified split: selected typed ship and saddle lanes accepted** | Fresh extractor reproduction confirms all three hashes are registered by both `Sadle.Awake` and `ShipControlls.Awake`, but source proves incompatible semantics: ships separate the profile-identity control token from simulation ownership, while saddles use session identity and transfer ownership in the grant. A method-name contract or generic C4 pickup-lease extension is invalid for one registrant. Exact r27 physically accepts the selected explicit saddle-target canary; exact r28 reconfirms the explicit ship-target contract after repairing atomic helm release/owner handoff. Unknown target kinds remain poison-blocked. |
| `RPC_RequestOwn` (instance) | superseded | superseded (kept) | This is the exact mechanism the C4 lease lane replaced and poisoned (`ItemDrop.RequestOwn`); the other registrants (`ArmorStand`, `ItemStand`, `Vagon`) ride the same replaced dance. |

### C10a verification update — 2026-08-02

`RPC_SetConnection(ZDOID,ZDOID)` is **superseded by the server portal-connection
cache**, not a P2 routed payload. The pinned decompile has one outbound caller in
vanilla `Game.SetConnection`; the enabled server patches suppress both periodic and
load-time vanilla pairing and write server-owned typed portal links directly. Exact r4
boot and physical receipts reconstructed 4,472 pairs, completed both clients' two-way
portal traversal under poison, and recorded zero method rows/native use. Keep the method
unadmitted so a replacement regression trips poison. Retained receipt:
`fieldlab/evidence/c10a-rpc-setconnection-verification/verification-summary.json`.

`RPC_TeleportPlayer(Vector3,Quaternion,Boolean)` is **verified deferred admin
recall**, not the portal-travel lane. `Chat.Awake` registers it and the pinned assembly's
only caller of its outbound wrapper is Terminal's cheat-only, admin-only, non-network
`recall` command. Normal portals call `Player.TeleportTo`; remote ownership dispatches
through the already-admitted instance `RPC_TeleportTo`. Both exact-r4 clients completed
two-way portal traversal under poison with zero `RPC_TeleportPlayer` rows, native use,
or poison trips. Keep the admin method unadmitted until it has an authenticated
Lumberjacks operator-command design. The focused negative admission test preserves that
fail-closed boundary. Retained receipt:
`fieldlab/evidence/c10a-rpc-teleportplayer-verification/verification-summary.json`.

`RequestControl(Int64)`, `ReleaseControl(Int64)`, and
`RequestRespons(Boolean)` are **verified as a registrant-dependent semantic
collision**, not one ownership-lease row. A fresh extractor run reproduced both
`Sadle.Awake` and `ShipControlls.Awake` registrations for each method and the tracked
120-method instance inventory exactly. Ship control does not transfer ZDO ownership and
uses persistent profile identity; saddle control transfers ownership and uses session/ZDO
identity. The generic admission contract therefore deliberately rejects all three names.
Separate typed contracts now admit the three hashes only with explicit ship or saddle
target kinds. Exact r27 physically proved both saddle rider directions, authenticated
owner epochs 1→5, disconnect reclaim to a live peer, server snapshot/rider-edge fan-out,
exact observer attachment, stale frame rejection, native-zero, and exact cleanup. Its
exact ship rerun then exposed a future owner retaining the departed helm user; exact r28
made canonical helm release plus owner transfer atomic and passed both ship directions
with 19/19 machine checks. Unknown target kinds remain rejected. Retained source receipt:
`fieldlab/evidence/c10a-vehicle-control-verification/verification-summary.json`.
Retained physical ship receipt:
`fieldlab/evidence/c10a-ship-physical-acceptance/verification-summary.json`.
Retained ship handoff regression receipt:
`fieldlab/evidence/c10a-ship-physical-acceptance/r28-handoff-reconfirmation.json`.
Retained physical saddle receipt:
`fieldlab/evidence/c10a-mount-physical-acceptance/verification-summary.json`.

## Summary counts (post-review)

| Bucket | Routed | Direct | Instance | Total |
|---|---|---|---|---|
| superseded-by-design | 8 | 13 | 1 | **22** |
| admitted | 0 | 0 | 1 | **1** |
| needs-lane-before-C10 | 10 | 0 | 118 | **128** |
| deferred-with-poison-guard | 1 | 8 | 0 | **9** |
| **Total** | 19 | 21 | 120 | **160** |

The needs-lane bucket is dominated by the instance-RPC surface v1 could not
see. Architecturally these are all one lane: ZNetView instance RPCs travel
through the routed envelope targeted at a ZDO — the already-proven
`RPC_ResetCloth` admission pattern (allow-list entry + payload contract),
repeated per method with the signatures captured in v2.

## RoutedRPCs (19)

| Name | Bucket | Lane / Priority | Rationale |
|---|---|---|---|
| ChatMessage | needs-lane | global-routed (P1) | Core player communication (`Chat.Awake`, sig `Vector3,Int32,UserInfo,String`) |
| DestroyZDO | superseded | ZDO journal | ZDO lifecycle owned by the journal (tombstones proven in C8 gates) |
| GlobalKeys | superseded | world-zone/descriptor | World bootstrap carried by the descriptor lane |
| LocationIcons | superseded | world-zone/descriptor | Map pins bootstrapped via descriptor lane |
| Ping | superseded | logical-peer session | Liveness owned by gateway session plumbing |
| Pong | superseded | logical-peer session | Liveness owned by gateway session plumbing |
| RPC_DamageText | needs-lane | global-routed (P2) | Combat feedback HUD broadcast |
| RPC_DiscoverClosestLocation | needs-lane | global-routed (P2) | Vegvisir/cartography exploration |
| RPC_DiscoverLocationResponse | needs-lane | global-routed (P2) | Exploration response |
| RPC_SetConnection | superseded | server portal-connection cache; poison-guarded | The cache suppresses the only vanilla outbound caller and writes both server-owned links directly; r4 reconstructed 4,472 pairs and both physical clients traversed one pair forward/reverse with zero method rows/native use. |
| RPC_TeleportPlayer | deferred | verified admin recall; poison-guarded | The only outbound caller is Terminal's cheat/admin `recall`; normal portals use instance `RPC_TeleportTo`, and r4 physical traversal produced zero rows/native use. |
| RemoveGlobalKey | superseded | world-zone/descriptor | Descriptor lane |
| RequestZDO | superseded | ZDO journal | Journal replaces on-demand ZDO sync |
| SetEvent | needs-lane | global-routed (P2) | Base raids / random events |
| SetGlobalKey | superseded | world-zone/descriptor | Descriptor lane |
| ShowMessage | needs-lane | global-routed (P1) | Server/system HUD messages |
| SleepStart | needs-lane | global-routed (P1) | Night skip / bed logic |
| SleepStop | needs-lane | global-routed (P1) | Night skip / bed logic |
| SpawnObject | needs-lane | global-routed (P2) | `ZNetScene.Awake` — core spawn broadcast, not admin |

## DirectRPCs (21)

Superseded by the logical-peer session (13): CharacterID, ClientHandshake,
Disconnect, Error, Kicked, NetTime, PeerInfo, PlayerList, RoutedRPC (the raw
envelope itself), Save→(see deferred), SavePlayerProfile, ServerHandshake,
ServerSyncedPlayerData, ZDOData→ZDO journal.

Deferred with poison guard (8): AdminList, Ban, Kick, PrintBanned,
RPC_RemoteCommand, RemotePrint, Save, Unban — admin/moderation/console paths;
acceptable native-poisoned until a dedicated admin lane exists. Any poison trip
in normal play reopens the row.

## InstanceRPCs (120)

118 needs-lane via the routed target-ZDO admission pattern, 1 admitted
(`RPC_ResetCloth`), 1 superseded (`RPC_RequestOwn` → ownership-lease). Priorities
from the machine draft stand except the review deltas above. P1 set (constant
in any session):

`RPC_Damage`, `Hit`, `ApplyOperation`, `UseDoor`, `RequestOpen`, `OpenRespons`,
`RequestTakeAll`, `TakeAllRespons`, `RPC_RequestStack`, `RPC_StackResponse`,
`RPC_MakePiece`, `Pick`, `RPC_Pick`, `RPC_SetPicked`, `RPC_AddFuel`,
`RPC_AddFuelAmount`, `RPC_AddItem`, `RPC_AddOre`, `RPC_AddStatusEffect`,
`RPC_EmptyProcessed`, `RPC_Extract`, `RPC_Heal`, `RPC_RemoveDoneItem`,
`RPC_Remove`, `RPC_Repair`, `RPC_Stagger`, `RPC_TeleportTo`, `Message`, `Say`.

Full per-row table with signatures: `synthetic_baseline_v2.json` plus the
HEARTH draft artifact; rows not listed in the deltas match the draft.

## Component families (122)

Families and coverage per the machine draft, with the three
targeted-verification flags this audit endorses:

1. **Vehicles/mounts (`Ship`, `ShipControlls`, `Sadle`, `Vagon`, …)** — the selected
   typed Karve and run-tagged Lox canaries are physically accepted. Remaining work is
   arbitrary existing untagged target handling plus a third recipient's AoI enter/leave
   and relevance-scoped fan-out; the saddle canary currently uses `Everybody`.
2. **Containers/stations (`Container`, `Smelter`, `CookingStation`, …)** —
   exact r34 physically accepts the selected two-client wood-chest transaction:
   the server held both peers and duplicates before one commit, rejected the stale
   contender, replayed both transaction IDs, journaled the real empty inventory,
   reconstructed it in both fresh processes, and stayed native-zero. This is the
   representative container gate, not proof that every station-specific RPC ran;
   smelter/cooking-station breadth remains admitted/poisoned until exercised or
   contradicted.
3. **AI/creatures (`MonsterAI`, `AnimalAI`, `Tameable`, …)** — exact r36 physically
   accepts the selected autonomous `MonsterAI` boundary on an actual tamed Lox through
   OMEN ownership, i5 transfer, disconnect loss, and AM4 reclaim. Owners executed
   160–161 real `BaseAI.UpdateAI` ticks, replicas executed zero owner ticks and 160
   non-owner blocks, recovery stayed under 0.035 s, all native ledgers stayed zero, and
   exact cleanup passed. Pinned source shows `MonsterAI.UpdateAI` and
   `AnimalAI.UpdateAI` share the `BaseAI` non-owner gate; that classification does not
   claim every species or `Tameable` behavior was physically invoked.

Players/motion ride the motion-authority lane (C6, accepted); pickables,
destructibles, structures, world-systems, effects ride the generic
journal+lease substrate already proven by the C4/C5/C8 gates for their
respective shapes.

## What this resolves and what remains

- Resolves the root `DECISIONS-PENDING.md` "Lumberjacks RPC Admission Gaps"
  entry: the evaluate-before-freeze decision is made per-RPC above. Owner
  (Derek) can reopen any single row without reopening the audit.
- The **C10 fallback-deletion entry criteria** gain a concrete work queue: the
  P1 admission backlog is **33 methods** — 29 instance RPCs plus the four routed
  globals `ChatMessage`, `ShowMessage`, `SleepStart`, and `SleepStop`. All 33 must
  be admitted + contract-tested before native fallback deletion; P2/P3 may ship
  behind the poison tripwire with the deferred bucket documented in the C10 gate.
- Most needs-lane rows are allow-list + payload-contract admissions on proven lanes.
  Vehicle control is the verified exception: one hash has registrant-dependent identity
  and ownership semantics, so ship and saddle require separate typed contracts. The
  selected AI/creature component-family gate is now physically closed by exact r36;
  other species remain explicit source-classified breadth rather than inheriting a
  universal pass. Station-specific breadth remains explicit rather than silently
  inheriting the selected chest pass. Vehicle/mount generalization and relevance remain
  a separate C10 boundary.
