# Native Valheim networking replacement landscape

**Assessed:** 2026-07-30
**Development topology:** headless dedicated server on AM4; native Windows clients on
OMEN (Tugcorp, RTX 5070) and i5 (Durracktu, Intel Iris Xe).
**Reference deployment:** P7 remains the production-reference server and was used for
the retained acceptance runs below.

This is a present-tense boundary inventory, not a restatement of the historical I0-I7
ladder. “Swapped” means the live payload crosses Lumberjacks and the corresponding
native delivery is suppressed. “Partial” names the native work that remains in the
same path. Confidence is tied to source, live configuration, and real-client evidence.

## Executive result

The replacement is not 100% complete.

- ZDO **carriage** is swapped: P7 removes all selected ZDOs from native `ZDOData`
  sends, publishes them through Lumberjacks, and both clients consume the Lumberjacks
  stream.
- ZDO **selection and application semantics** remain Valheim: `CreateSyncList` decides
  what becomes a candidate, and clients feed Lumberjacks payloads back through
  `RPC_ZDOData`.
- Handshake **admission logic** is Lumberjacks-fronted, but Steam connection setup,
  ticket/password crypto, `PeerInfo`, and `AddPeer` remain vanilla.
- Routed RPC, direct peer-control RPC, player ownership, world bootstrap, and the
  underlying Steam socket are still native.
- Motion has a Lumberjacks observe/apply lane, but production apply is off. Native
  player replication therefore remains authoritative.
- Co-presence fan-out's ack-without-emit defect is corrected and proven on the AM4
  development lane with two physical clients. It remains off on P7 until that build
  is promoted.

The shortest honest description is: **ZDO transport is swapped; connection, control,
ownership, world bootstrap, and motion authority are not.**

## Live configuration observed on P7

Read directly from the server config on 2026-07-30:

| Setting | Value | Meaning |
| --- | --- | --- |
| `lumberjacksCutoverMode` | `lumberjacks-primary` | Declared operating mode |
| `zdoRedirectEnabled` / `zdoRedirectPrefabs` | `true` / `*` | Every selected ZDO is removed from the native send list |
| `zdoBandShapingEnabled` | `true` | Lumberjacks redirect is recipient/band shaped |
| `zdoPlayerFastLaneEnabled` | `true` | Player ZDOs bypass ordinary thinning |
| `zdoAuthoritativeConsumerEnabled` | `false` on server | Expected: consumers are the clients |
| `zdoCoPresenceShadowEnabled` | `false` | Disabled after the live pickup/roughness defect |
| `zdoCoPresenceFanoutEnabled` | `false` | Disabled after the live pickup/roughness defect |
| `handshakeResponderEnabled` | `true` | Lumberjacks admission decision is active |
| `handshakeResponderStrictMode` | `false` | Authority faults still fail open to vanilla |
| `lumberjacksMotionEnabled` | `true` | Motion lane observes/publishes |
| `lumberjacksMotionApplyEnabled` | `false` | Native motion remains the applied path |
| `zdoSendCadenceOverrideEnabled` | `false` | Valheim still drives send cadence |

Both retained client logs report `zdoAuthoritativeConsumerEnabled=true`,
manifest `p7-primary-v1`, and an armed consumer.

## Per-path replacement table

| Path | Current state | What crosses Lumberjacks now | What is still native | Confidence |
| --- | --- | --- | --- | --- |
| Steam connection and packet transport | **Native** | Nothing that can establish or maintain the Valheim peer | `ZSteamSocket`, Steamworks identity/session, UDP/P2P connection state, reliability and packet framing | **Verified:** source map plus live Steam connection logs |
| Handshake and admission | **Partial; off-thread authority proven on AM4, prior build still live on P7** | Server prefix defers decoded `PeerInfo` fields to Lumberjacks and enforces accept/reject on Unity's main thread after the worker verdict | `ServerHandshake`/`ClientHandshake`, Steam ticket verification, password crypto, vanilla checks on accept, `SendPeerInfo`, `AddPeer` | **Verified:** delayed fail-open and normal ACCEPT both reached vanilla AddPeer and world entry; the 2,034 ms authority wait produced no ≥250 ms wall hitch |
| ZDO candidate selection and cadence | **Native with Lumberjacks policy layered on** | Rank, landmark, band and recipient policy run after Valheim builds `toSync` | `ZDOMan.Update`, `CreateSyncList`, sector query, `ShouldSend`, force-send and base priority ordering | **Verified:** redirect is a `CreateSyncList` postfix; cadence override is off |
| ZDO outbound carriage | **Swapped** | Selected `*` prefabs are serialized to Lumberjacks recipient envelopes; native entries are removed and acknowledged | Valheim still supplies the candidate and serialization fields | **Verified:** live config, source suppression path, prior redirect receipts, and working real-client state |
| ZDO inbound carriage/apply | **Partial** | Clients poll/drain recipient-scoped Lumberjacks envelopes | The consumer reconstructs a `ZPackage` and invokes Valheim `RPC_ZDOData` for revision checks, object creation, ownership fields and deserialize/apply | **Verified:** source plus both clients armed on the live pair run |
| Co-presence ZDO fan-out | **Corrected and integration-proven on AM4; disabled on P7 pending promotion** | Emits native-selected revisions to the exposing recipient and any in-band observer that is behind | Candidate discovery and delivered-revision bookkeeping remain native | **Verified:** two unattended physical clients, 1,340/1,340 native-selected `Emit`, zero non-emit, and successful inventory return on both clients |
| Routed gameplay RPC (`ZRoutedRpc`) | **Native** | Some mod events are mirrored or originated as side effects | `InvokeRoutedRPC`, `RouteRPC`, `RPC_RoutedRPC`, server relay and `ZNetView` dispatch carry gameplay calls | **Verified:** no suppression/replacement patch exists; current producers call `ZRoutedRpc` |
| Direct peer/control RPC | **Native except handshake decision hook** | Handshake verdict only | Error, player/global/admin lists, reference position and the remaining `ZRpc` control exchange | **Verified:** source map and absence of a replacement interceptor |
| Player motion | **Partial, observe-only in production** | Client motion can publish over Lumberjacks WebSocket/UDP and can be resolved to a Valheim player | Apply is off; visible authoritative movement still arrives through native player/ZDO replication | **Verified:** live config and motion runner apply gate |
| ZDO ownership transfer | **Native** | Owner metadata is carried in redirected envelopes | Assignment/release, owner revision and action authority remain `ZDOMan`/`ZDO` decisions | **Verified:** no active `ReleaseNearbyZDOS` replacement in the current mod |
| World identity/bootstrap | **Native** | No complete Lumberjacks world bootstrap | Server-shaped `PeerInfo` supplies world name/seed/uid/version/time; vanilla initializes the connected world | **Verified:** handshake source and live vanilla AddPeer path |
| Zone/interest lifecycle | **Native with post-selection shaping** | Lumberjacks band shaping filters already-selected ZDOs | Reference positions, sector discovery, zone load/generation, object instantiation and unload remain Valheim | **Verified:** source map and current redirect altitude |
| Server save/persistence | **Native** | Gateway/event services retain their own records | Valheim world/ZDO save is still canonical game persistence | **Verified:** current architecture; not itself a transport swap |

## One boundary slice for every incomplete path

These are integration slices. Each has one payload, one direction, and a failure
mode. None requires two humans driving game windows.

| Remaining boundary | Smallest useful slice | Failure mode that makes the result legible | Estimated build + real-run cost |
| --- | --- | --- | --- |
| Steam transport | Put one allow-listed control message through a Lumberjacks client transport while deliberately suppressing its native socket send; prove receipt and response on a joined client | Gateway remains healthy but the native copy is absent; no response means the new transport did not cross | 2-3 days; foundational |
| Handshake completion | Configure one Lumberjacks-only rejection for an otherwise admissible seeded client, observe the exact client error, remove it, then autojoin successfully | Dead/unparseable authority must produce the configured strict result without freezing the server | 1 day after off-thread decision plumbing |
| ZDO selection/cadence | Add a Lumberjacks-owned changed-object queue for one prefab and deliver an update that Valheim `CreateSyncList` did not select | Native candidate count stays zero while the recipient applies the Lumberjacks revision | 2-3 days |
| ZDO apply semantics | Deliver one recipient revision through a typed Lumberjacks apply adapter rather than invoking `RPC_ZDOData`; compare object/revision/owner state to the existing path | Malformed or stale revision is rejected without entering native RPC dispatch | 2 days |
| Routed gameplay RPC | Replace one idempotent request/response RPC (a bounded boundary echo) in both directions and suppress only that native method hash | Drop the Lumberjacks response and require a deterministic timeout; no native fallback for the selected hash | 1-2 days |
| Direct peer/control RPC | Replace one post-AddPeer control message, such as a bounded server pulse, and suppress its native invocation | Client must mark the pulse stale when the Lumberjacks copy is withheld | 1 day |
| Player motion authority | For one source player and one short allow-listed movement command, suppress native motion delivery and enable Lumberjacks apply on the observer | Withhold a numbered motion frame and prove bounded stale/drop behavior instead of native correction | 2-3 days; do before any smoothing/tuning |
| Ownership | Assign one spawned item through a Lumberjacks ownership lease while suppressing the matching native transfer trigger; perform one pickup | Expired/wrong lease must reject the action and must not mutate inventory | 2-3 days |
| World bootstrap | Supply a minimal server-shaped world descriptor from Lumberjacks and prove the client reaches the same world identity without consuming vanilla server `PeerInfo` world fields | Wrong network/world version must stop before scene entry with a deterministic reason | 3-5 days and depends on connection/control work |
| Zone/interest | Make Lumberjacks the source of one zone’s object membership while the native sector candidate list is empty for that zone | Remove the Lumberjacks membership and require deterministic unload/no-spawn | 3-5 days |

## Blocker status

### 1. Co-presence ack-without-emit: corrected and proven on AM4

The original P7 symptom remains verified: with shadow and fan-out enabled, harvesting
credited the action but did not put the item in inventory; movement also became rough.
The shadow recorded 183/183 observers as `AlreadyDelivered` with zero `Emit`.

The source mechanism was verified and corrected. Fan-out now reads both data and
owner revisions, records whether the observer supplied Valheim's native-selected
candidate, forces that native-selected pass to `Emit`, and falls back to the
single-recipient redirect if a fan-out plan somehow emits to nobody.

The AM4 machine cell produced 2,634/2,634 native-selected `Emit` decisions and zero
native-selected non-emit decisions. Its sharp `Pickable_Mushroom` case had
`data_rev=0`, `owner_rev=1`: four native-selected observers emitted, while four
non-exposing observers whose data and owner revisions were current were correctly
classified `AlreadyDelivered`. A second touch cell produced 1,340/1,340
native-selected emits and successful inventory return after an OMEN raspberry pickup
and an i5 blueberry pickup. Movement feel was not reported, so that datum remains
unverified. P7 still runs the prior build with fan-out off.

### 2. Handshake authority I/O: moved off-thread and proven on AM4

The prefix now clones and banks `RPC_PeerInfo`, returns immediately, and starts the
bounded HTTP request on a worker. `Update` drains completed decisions, applies rejects
on Unity's main thread, or re-enters vanilla `RPC_PeerInfo` through a one-shot bypass
for accept/fail-open. Pending requests have a five-second state-machine deadline and
responder generations prevent a verdict from an old endpoint/window being enforced
after a live reconfiguration.

The delayed AM4 cell spent 2,034 ms waiting for an unreachable authority, then failed
open and joined. During that authority interval the 250 ms hitch stream contained no
wall-clock hitch and the 25 ms section stream contained no row. A separate live
endpoint cell returned Lumberjacks ACCEPT in 66 ms and also reached vanilla AddPeer
and the character-ZDO marker.

A different 1.969-1.988 second wall block reproduced immediately before the precise
off-thread `DEFERRED` marker in both cells, with no GC-count change. It belongs to the
still-native pre-`PeerInfo`/Steam handshake boundary and is not attributed to
Lumberjacks HTTP. The earlier 107.8-second full-GC/asset-unload stall also remains a
separate capacity pathology.

### 3. Dedicated-server runtime control: proven on AM4

The mod now consumes one atomically staged filesystem command through authenticated
host access. It accepts only seven named networking settings, writes old/effective
values to `runtime-control-receipts.jsonl`, and has no listener or general console
execution. Disabling redirect invokes the owning stop path; changing the handshake
endpoint/window disarms and re-arms its runner in-process.

On AM4, shadow and fan-out were each toggled on/off and the handshake endpoint moved
from a timeout target to the real local Gateway. All changes returned applied
receipts; container start time and PID were unchanged. The next unattended client was
accepted by the new endpoint and entered the world. P7 still requires promotion of
this build before the lane exists there.

## Retained real-client evidence

All paths are under ignored `fieldlab/runs/` test evidence and contain lifecycle JSON,
client logs, autotest receipts, and a Steam-identifier-free P7 correlation:

- `native-valheim/native-20260730-163640-omen/omen/` — failed join correlated to the
  107.8-second P7 stall; useful negative control.
- `native-valheim/native-20260730-163901-omen/omen/` — unattended Tugcorp join on
  RTX 5070 / Direct3D 11; P7 reached Lumberjacks ACCEPT, vanilla AddPeer and character
  ZDOID.
- `native-valheim/native-20260730-164251-i5/i5/` — unattended Durracktu join through
  the interactive scheduled-task seam on Intel Iris Xe / Direct3D 11.
- `native-valheim/native-20260730-164603-pair/` — both clients overlapped in steady
  state and P7 received both character ZDOIDs before the bounded shutdowns.
- `native-valheim/native-20260730-171100-am4-fanout/` — AM4 machine proof:
  2,634/2,634 native-selected fan-out decisions emitted, including the
  `data_rev=0`/`owner_rev=1` pickable case.
- `native-valheim/native-20260730-172100-am4-touch/` — AM4 human boundary proof:
  both native clients received a picked berry in inventory; 1,340/1,340
  native-selected decisions emitted and Gateway receipts were contiguous.
- `native-valheim/native-20260730-173650-am4-handshake-delay/` — 2,034 ms authority
  wait on a worker, zero ≥250 ms wall hitches during that interval, fail-open resume,
  and successful world entry.
- `native-valheim/native-20260730-174850-am4-runtime-control/` — five applied
  old/effective-value receipts with unchanged container start time and PID.
- `native-valheim/native-20260730-174910-am4-handshake-accept/` — off-thread
  Lumberjacks ACCEPT, vanilla AddPeer resume, and successful world entry.

## Replan recommendation

Do not start the motion tuning or transpiling lab yet. The build order supported by
this landscape is:

1. **Completed on AM4:** fix co-presence ack/emit safety and prove real inventory
   updates with the unattended pair; promote only after the remaining evidence is
   reviewed;
2. **Completed on AM4:** remove synchronous handshake HTTP from the main thread and
   prove delayed fail-open plus normal Lumberjacks ACCEPT;
3. **Completed on AM4:** add narrow live flag control and prove applied values without
   a server restart;
4. replace one routed RPC end to end;
5. replace one ownership/action boundary;
6. make Lumberjacks motion authoritative for one player while native motion is
   suppressed;
7. then tackle world/bootstrap and zone membership, which are the expensive
   dependencies for removing the vanilla server peer.

Only after those native paths are gone does transport/transpiling tuning measure the
system intended to ship.
