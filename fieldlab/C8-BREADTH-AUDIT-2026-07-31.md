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
| `RPC_TeleportPlayer` (routed) | needs-lane P1 | **deferred-with-poison-guard [VERIFY]** | Registered by `Chat.Awake` — the chat/command path; portal travel rides `RPC_TeleportTo` (instance). Reopen if poison trips in normal play. |
| `UseStamina` (instance) | needs-lane P1 | **needs-lane P3 [VERIFY]** | Registered by `Player.Awake`; stamina spend is normally owner-local. The remote-invoke paths are rare. |
| `RequestControl` / `ReleaseControl` / `RequestRespons` (instance) | superseded by ownership-lease | **needs-lane P2 via ownership-lease [VERIFY]** | Registered by `Sadle.Awake` + `ShipControlls.Awake`. The lease lane is the right home, but it is proven on `Pickable` only — vehicle-control leases are design-compatible, unbuilt work, not superseded. |
| `RPC_RequestOwn` (instance) | superseded | superseded (kept) | This is the exact mechanism the C4 lease lane replaced and poisoned (`ItemDrop.RequestOwn`); the other registrants (`ArmorStand`, `ItemStand`, `Vagon`) ride the same replaced dance. |

## Summary counts (post-review)

| Bucket | Routed | Direct | Instance | Total |
|---|---|---|---|---|
| superseded-by-design | 7 | 13 | 1 | **21** |
| admitted | 0 | 0 | 1 | **1** |
| needs-lane-before-C10 | 11 | 0 | 118 | **129** |
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
| ChatMessage | needs-lane | target-ZDO (P1) | Core player communication (`Chat.Awake`, sig `Vector3,Int32,UserInfo,String`) |
| DestroyZDO | superseded | ZDO journal | ZDO lifecycle owned by the journal (tombstones proven in C8 gates) |
| GlobalKeys | superseded | world-zone/descriptor | World bootstrap carried by the descriptor lane |
| LocationIcons | superseded | world-zone/descriptor | Map pins bootstrapped via descriptor lane |
| Ping | superseded | logical-peer session | Liveness owned by gateway session plumbing |
| Pong | superseded | logical-peer session | Liveness owned by gateway session plumbing |
| RPC_DamageText | needs-lane | target-ZDO (P2) | Combat feedback HUD broadcast |
| RPC_DiscoverClosestLocation | needs-lane | target-ZDO (P2) | Vegvisir/cartography exploration |
| RPC_DiscoverLocationResponse | needs-lane | target-ZDO (P2) | Exploration response |
| RPC_SetConnection | needs-lane | target-ZDO (P2) [VERIFY] | Portal linking |
| RPC_TeleportPlayer | deferred | poison-guarded [VERIFY] | `Chat.Awake` command path; portals use RPC_TeleportTo |
| RemoveGlobalKey | superseded | world-zone/descriptor | Descriptor lane |
| RequestZDO | superseded | ZDO journal | Journal replaces on-demand ZDO sync |
| SetEvent | needs-lane | target-ZDO (P2) | Base raids / random events |
| SetGlobalKey | superseded | world-zone/descriptor | Descriptor lane |
| ShowMessage | needs-lane | target-ZDO (P1) | Server/system HUD messages |
| SleepStart | needs-lane | target-ZDO (P1) | Night skip / bed logic |
| SleepStop | needs-lane | target-ZDO (P1) | Night skip / bed logic |
| SpawnObject | needs-lane | target-ZDO (P2) | `ZNetScene.Awake` — core spawn broadcast, not admin |

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

1. **Vehicles/mounts (`Ship`, `ShipControlls`, `Sadle`, `Vagon`, …)** — owner-
   authoritative physics; requires lease-lane extension + explicit tug-of-war
   verification. This is the largest genuinely novel ownership work left.
2. **Containers/stations (`Container`, `Smelter`, `CookingStation`, …)** —
   inventory mutations must be strictly ordered through the lease/journal to
   prevent duping; needs a targeted two-client container gate.
3. **AI/creatures (`MonsterAI`, `AnimalAI`, `Tameable`, …)** — server-to-client
   ownership handoff must not stall AI; needs a targeted verification cell.

Players/motion ride the motion-authority lane (C6, accepted); pickables,
destructibles, structures, world-systems, effects ride the generic
journal+lease substrate already proven by the C4/C5/C8 gates for their
respective shapes.

## What this resolves and what remains

- Resolves the root `DECISIONS-PENDING.md` "Lumberjacks RPC Admission Gaps"
  entry: the evaluate-before-freeze decision is made per-RPC above. Owner
  (Derek) can reopen any single row without reopening the audit.
- The **C10 fallback-deletion entry criteria** gain a concrete work queue: the
  P1 admission backlog (29 methods) must be admitted + contract-tested before
  native fallback deletion; P2/P3 may ship behind the poison tripwire with the
  deferred bucket documented in the C10 gate.
- Nothing here reopens C0–C8 architecture: every needs-lane row is an
  allow-list + payload-contract admission on proven lanes. The three [VERIFY]
  flags and the three component-family gates are the C9/C10-adjacent
  verification work.
