# Native Valheim networking replacement landscape

**Assessed:** 2026-08-02
**Development topology:** headless dedicated server on AM4; native Windows clients on
OMEN (Tugcorp, RTX 5070) and i5 (Durracktu, Intel Iris Xe).
**Reference deployment:** P7 remains stopped and unchanged; C0-C8, the accepted C10a
paired-release candidate, the selected saddle canary, and the corrected ship/vehicle
handoff are proven on AM4.

This is a present-tense boundary inventory, not a restatement of the historical I0-I7
ladder. “Swapped” means the live payload crosses Lumberjacks and the corresponding
native delivery is suppressed. “Partial” names the native work that remains in the
same path. Confidence is tied to source, live configuration, and real-client evidence.

## Executive result

The replacement is not 100% complete.

- ZDO **carriage** is swapped: P7 removes all selected ZDOs from native `ZDOData`
  sends, publishes them through Lumberjacks, and both clients consume the Lumberjacks
  stream.
- A C3 AM4 boundary now bypasses native ZDO selection and apply: a durable
  Lumberjacks journal delivered one object that `CreateSyncList` never selected,
  and both clients used typed snapshot/delta/tombstone apply without entering
  network `RPC_ZDOData`. Legacy redirect/apply remains outside that gate and on P7,
  so the full prefab surface is still partial.
- C7 replaces the selected connection/bootstrap boundary on AM4. Both clients cold
  joined and rejoined through Lumberjacks without `+connect`, a native socket,
  Steam ticket verification, native handshake, or network `PeerInfo`; all four
  required negative cells failed closed without native fallback.
- Routed RPC is partial on AM4: a fixed registry now carries the complete envelope
  shapes through Lumberjacks and suppresses the selected native methods. Unselected
  method hashes, most direct peer controls, and general ownership/world/zone breadth
  are still native or partial outside the candidate.
- C6 makes Lumberjacks the selected remote-transform authority on AM4. Both physical
  clients applied numbered motion to the real remote player while native transform
  writes were suppressed; a 20-frame gap held without native correction and recovered
  through reliable resync. P7 still runs the earlier observe-only configuration.
- A canonical Lumberjacks game-session control lane is now ordered, acknowledged,
  bounded, and socket-resumable on AM4. C2a now carries one selected typed direct
  control pulse on that lane, applies it on Unity `Update`, and suppresses the matching
  native `ZRpc.Invoke`. Remaining direct controls and gameplay RPC/state semantics have
  not moved.
- Co-presence fan-out's ack-without-emit defect is corrected and proven on the AM4
  development lane with two physical clients. It remains off on P7 until that build
  is promoted.
- C4 now carries one real pickup per client through server-issued Lumberjacks leases
  bound to logical peer and epoch. The selected native ownership, inventory pickup,
  candidate, and destroy paths are poisoned on AM4; general-prefab ownership breadth
  and P7 promotion remain.
- C5 now supplies the selected world descriptor and run-tagged zone membership through
  Lumberjacks on AM4. Both physical clients entered with blank native world fields,
  resumed an interrupted three-object snapshot without duplication, unloaded to zero
  stale objects, and spawned nothing when membership was withheld. C7's logical peer
  now carries the enclosing lifecycle; general-prefab/zone breadth remains for C8.
- C8 composes every boundary above under unconditional client AND server poison:
  the acceptance pair (`native-20260731-c8-full44`/`full45`, accepted 2026-08-01)
  ran the complete 49-action composition twice from clean launches on one frozen
  build with zero poison trips, clean save integrity, and 20/20 coverage — evidence
  in `fieldlab/evidence/c8-native-zero-composition/`. Rows stay Partial where they
  name unselected breadth: the composition proves the selected surface only, and
  Swapped-everywhere remains C10's exit condition (33 P1 admissions — 29 instance plus
  four global — and the component-family gates precede it). Vehicle-control source
  verification split the former one-row assumption into typed ship and saddle contracts.
  Exact r27 physically accepts the selected two-client saddle canary; exact r28
  reconfirms the ship boundary after a real rerun exposed and repaired a stale helm-user
  handoff. Arbitrary untagged mount/vehicle and relevance breadth remain open.
  Recovery5 repeated
  the physical composition and runtime-proved the session-scoped epoch across a real
  AM4 restart; that wall-11 prerequisite no longer remains open.
- The aligned C10a pair `m7-c10a-20260802-r4` passed the same poison-armed 49-action
  physical reducer on OMEN and i5 with zero native use/trips on both clients and AM4.
  This accepts one deployable mod/Gateway pair after three retained falsifiers; it does
  not close full C10a breadth. `RPC_SetConnection` is verified as superseded by the
  enabled server portal cache, and `RPC_TeleportPlayer` is verified as deferred admin
  recall; both remain deliberately unadmitted as poison tripwires. Exact paired r6 then
  closed `UseStamina [VERIFY]` on the real OMEN+i5 pair: both live-player targets satisfied
  `zdo user == owner`, both receivers applied `50 - 1.25 = 48.75`, both sender receipts
  passed, and OMEN/i5/AM4 native totals and poison trips remained zero. Fresh extractor
  verification then proved that `RequestControl`/`ReleaseControl`/`RequestRespons` share
  method hashes across incompatible ship and saddle identity/ownership semantics. Those
  methods remain generically unadmitted and poison-blocked. Exact paired r27 accepted the
  explicit saddle-target contract on one run-tagged real tamed Lox: both clients drove and
  observed, owner epochs advanced through disconnect reclaim, attachment remained exact,
  deliberately stale transfer/snapshot/rider frames rejected, cleanup destroyed the exact
  target, and all native ledgers stayed zero. That artifact's exact ship rerun then exposed
  a future owner retaining the departed helm user; r28 made canonical helm release and
  owner transfer atomic and passed both Karve directions with 19/19 machine checks. The
  container/station, AI/creature, arbitrary untagged target, and third-recipient/AoI
  relevance gates remain.

The shortest honest description is: **the C3 ZDO semantic boundary and selected
control/RPC classes are swapped on AM4, and C3 semantics now ride the canonical
session with process-durable logical peers; C4 also swaps one selected real ownership
and pickup boundary; C5 swaps the selected world descriptor and run-tagged
zone-membership boundary; C6 swaps selected two-player motion authority; C7 swaps the
Steam-free connection/bootstrap boundary; C8 composes that selected surface at
native-zero, the server-session epoch rejects stale bank state after restart, r4
accepts one aligned paired release on that physical surface, r6 physically accepts
the legitimate cross-owner `UseStamina` P3 contract, source verification rejects a
generic vehicle-control contract in favor of split ship/saddle lanes, r27 physically
accepts the selected typed saddle canary, and r28 physically reconfirms the typed ship
lane with atomic helm release plus owner handoff. Remaining component-family and
vehicle/mount relevance breadth, subjective motion acceptance, fallback deletion, and
P7 promotion are not complete.**

## C0 measured baseline and poison gate

C0 is complete on the AM4 development lane. The native-use ledger now names every
remaining native funnel, records exact per-run totals, and can poison those funnels
before their original method runs. It also records connection-stage timing, including
the separate pre-`PeerInfo` native stall. The ledger writer is bounded and
off-main-thread.

The retained `native-20260730-c0-clean` composition used the same plugin artifact on
the server and both physical clients. Both clients joined, executed allow-listed
movement, disconnected, launched a fresh Valheim process, rejoined, and stopped
without an operator driving either game. The exact final native totals were 4,360 on
OMEN, 2,957 on i5, and 12,339 on the server, with zero ledger drops or writer faults.
Those non-zero counts are the measured removal ledger for C1-C7; they are not a claim
that the cutover is complete.

The retained `native-20260730-c0-poison` cell stopped at the first forbidden native
connection boundary and blocked all 76 observed native calls. The poison gate is
therefore capable of falsifying a native-zero claim instead of merely reporting it.
The unattended lane also recovered one completed Steam Cloud `.fch.new` transaction
through Valheim's Cloud API and subsequently rejoined with the final character file.

## C3 durable ZDO semantic boundary

C3 is complete on the AM4 development lane in
`native-20260730-c3-sixth`. The server placed one run-tagged ZDO four zones outside
both native sync rings. The object was absent from all 1,198 observed
`CreateSyncList` selections, but its authoritative revisions entered a durable
Lumberjacks journal. The Gateway restarted after the first mutation and replayed the
object from its WAL. Late-arriving i5 applied a typed snapshot; OMEN and i5 then
rejected stale and malformed entries before mutation, applied the next valid delta,
and applied the tombstone. Network `RPC_ZDOData` and typed-apply failures were zero.

This changes the classification of the selected C3 boundary, not the entire ZDO
surface. The body was synthetic and run-tagged, and mutation capture still observes
the authoritative Valheim server.

C4a subsequently closed C3's identity/carriage limitations in
`native-20260730-c4a-second`. The server, OMEN, and i5 retained one opaque logical
peer each across Gateway and fresh-Valheim-process turnover while transport
connection ids changed. All run-scoped mutation, interest, delivery, receipt, and
ACK frames reported `canonical_session`; six mutations were accepted, the two final
interests drained to zero pending, and no HTTP fallback row appeared. Ownership must
now bind to that logical identity, not a transport incarnation.

## C4 ownership lease and authoritative pickup boundary

C4 is complete at its selected AM4 boundary in `native-20260730-c4b-tenth`.
The server created one real Raspberry ZDO per client. Lumberjacks issued three lease
epochs per object, reclaimed epoch 1 after a forced socket detach, rejected a wrong
epoch and expired epoch 2 before mutation, and authorized epoch 3. The dedicated
server restored canonical ownership, destroyed each target without a native destroy
RPC, sent the action results, and received completed result receipts.

The selected native `CreateSyncList`, release/owner, `ItemDrop.RequestOwn`,
`Humanoid.Pickup`, destroy-request, and destroyed-delivery paths were suppressed.
OMEN inventory changed 9→10 and i5 11→12 exactly once. Both clients acknowledged
their completion frame, completed fresh-process resume on the intended GPU, and
stopped unattended. This promotes the selected real pickup boundary; it does not
claim that every prefab or ownership-bearing gameplay method is admitted yet.

## C5 world descriptor and selected zone-membership boundary

C5 is complete at its selected AM4 boundary in `native-20260730-c5-final`.
The server blanked the native `PeerInfo` world fields. OMEN and i5 accepted the
Lumberjacks descriptor for world generation version 2 and initial zone `0,0`, entered
the intended world, and retained the intended GPU renderer.

For each client, the server published three complete run-tagged typed ZDO bodies for
the entered membership. The client applied chunk 1, deliberately dropped the
canonical socket before ACK, received the same reliable sequence again, treated it
idempotently, applied chunks 2 and 3, and emitted exactly one snapshot-complete
marker. Leave destroyed all three objects with zero stale local membership objects.
The deliberately withheld membership spawned none. AM4 removed every selected C5
object that appeared in native `CreateSyncList` before delivery.

`native-20260730-c5-fault-protocol` and
`native-20260730-c5-fault-worldgen` stopped before scene entry with deterministic
protocol and world-generation mismatch reasons. This promotes the selected
run-tagged descriptor/membership boundary. The enclosing native connection and
`PeerInfo` delivery, arbitrary prefab/zone breadth, and P7 promotion remain.

## C6 selected motion-authority boundary

C6 is complete at its selected AM4 boundary in
`native-20260730-c6-eighth`. OMEN and i5 rendezvoused without operator input,
resolved the real remote player scene instance, and applied numbered Lumberjacks
motion in both directions. After canonical apply, the selected native
`ZSyncTransform` remote writer was suppressed and native position writes for that
canonical remote identity were masked.

OMEN deliberately withheld sequences 600 through 619. i5 held the last valid state
with no native fallback, received a reliable hard resync at sequence 619, applied it,
and queued its ACK. Both clients then relaunched once in fresh Valheim processes and
completed the manifest. OMEN exercised UDP; i5's unreachable advertised UDP endpoint
failed over to binary WebSocket without ending the session.

The Gateway received 1,469 motion frames: 709 over UDP and 760 over WebSocket. It
recorded zero unauthorized and zero stale drops, plus two invalid early frames whose
exact source remains unproven. Subjective feel and all smoothing/tuning remain
unverified and deliberately locked. The enclosing logical peer/scene admission is now
supplied by C7; general breadth/native-zero composition remain C8 work.

## C7 Steam-free connection/bootstrap boundary

C7 is complete on AM4 in `native-20260731-c7-cold-final`. OMEN and i5 each launched
without a native server target, authenticated to Lumberjacks, validated the world
descriptor, constructed the local logical server peer, queued the typed character id,
and reached the joined scene twice across a fresh-process repeat. Both clients armed
native poison in both process incarnations and recorded zero native use. AM4
reconstructed two distinct logical clients and recorded zero selected native peer,
handshake, `PeerInfo`, `ZDOData`, or routed-RPC ingress.

The four cells in `native-20260731-c7-negative-second` prove invalid enrollment,
unavailable Gateway, wrong release, and wrong descriptor/protocol all stop before
join without trying the native server. The retained record is
[`evidence/c7-steam-free-cold-join/`](evidence/c7-steam-free-cold-join/).

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
| Steam connection and packet transport | **Selected world-session boundary swapped on AM4; prior build remains on P7** | Authenticated Lumberjacks reliable/UDP lanes establish and maintain the logical world session; Steam only launches the owned game | General/unselected paths and P7 still contain the native implementation pending C8 breadth and C10 deletion | **Verified:** both C7 clients cold joined and fresh-process rejoined without `+connect` or a native server target, with poison armed and zero client native use |
| Lumberjacks reliable game session | **Swapped substrate with selected C2–C7 semantics** | Stable opaque logical peer, replaceable connection incarnation, ordered reliable control/RPC, ZDO mutation/interest/delivery/ACK, ownership lease/action/result, world descriptor, selected zone snapshot/leave, motion binding, reliable motion-resync frames, and Steam-free peer construction | Remaining direct/routed classes and general ownership/zone breadth remain outside the selected registry until C8 | **Verified:** C1 resume/replay through C7 cold-join reconstruction all used the same canonical session |
| Handshake and admission | **Selected boundary swapped on AM4; prior build still live on P7** | Enrollment verdict, release/protocol compatibility, complete world descriptor, typed character id, and logical peer construction cross Lumberjacks | Migration-only native branches remain in the artifact until C10; general breadth and P7 promotion remain | **Verified:** C7 reached scene twice per client with no native handshake or network `PeerInfo`; all four negative cells stopped before join |
| ZDO candidate selection and cadence | **Partial; C3 journal boundary swapped on AM4** | A mutation-seam journal and explicit recipient interest delivered the C3 object independently of `CreateSyncList` | Legacy/general-prefab delivery still uses `ZDOMan.Update`, `CreateSyncList`, sector query, `ShouldSend`, force-send and base priority ordering | **Verified:** C3 object had zero selected candidates across 1,198 native selection passes but reached both clients |
| ZDO outbound carriage | **Swapped for legacy redirect and C3 semantic boundary** | Selected `*` prefabs use the redirect; C3 authoritative mutation bodies, revisions and tombstones use the durable journal over C1 | C3 body capture still observes Valheim's authoritative mutation seams; semantic breadth remains | **Verified:** C4a accepted six canonical mutations, replayed WAL across Gateway restart, retained two isolated logical recipients and ended zero pending |
| ZDO inbound carriage/apply | **Partial; C3 typed boundary swapped on AM4** | C3 clients receive canonical-session frames, validate, and directly create/update/delete/revision/owner/position/deserialize on Unity `Update` | Legacy consumer still reconstructs a `ZPackage` and invokes `RPC_ZDOData`; general-prefab typed parity is not yet proven | **Verified:** C4a used only canonical carriage; both clients applied valid delta/tombstone, i5 applied late snapshot, stale/malformed rejected, network `RPC_ZDOData` zero |
| Co-presence ZDO fan-out | **Corrected and integration-proven on AM4; disabled on P7 pending promotion** | Emits native-selected revisions to the exposing recipient and any in-band observer that is behind | Candidate discovery and delivered-revision bookkeeping remain native | **Verified:** two unattended physical clients, 1,340/1,340 native-selected `Emit`, zero non-emit, and successful inventory return on both clients |
| Routed gameplay RPC (`ZRoutedRpc`) | **33 P1 methods code-admitted; aligned candidate, `UseStamina` P3, and typed ship/saddle control accepted on AM4** | One source-aligned mod/Gateway contract admits seven harness methods plus 29 P1 instance and four P1 global methods by exact name/hash, target shape, size, and extractor-pinned byte layout; exact P3 `UseStamina(Single)` is admitted for legitimate cross-owner harpoon/fishing debits; unadmitted outbound routes enter the ledger and poison blocks them. `RPC_SetConnection` is replacement-owned by the server portal cache; `RPC_TeleportPlayer` is deferred admin recall. Both deliberately stay unadmitted. Vehicle-control source verification keeps a generic `RequestControl`/`ReleaseControl`/`RequestRespons` admission prohibited; explicit ship and saddle target kinds select separate typed contracts and unknown kinds remain rejected | Not every admitted P1 method was invoked by the composition. Remaining P2/P3 classification, arbitrary untagged target and AoI/relevance breadth, containers/stations, AI/creatures, fallback deletion, and P7 remain | **Verified:** focused tests retain the exact dual-registration/non-admission guard and typed target contracts; `native-20260802-c10a-r4` completed all 49 physical actions with native totals/trips zero; exact r6 applied `UseStamina` debits in both directions; exact r27 passed the selected saddle canary; exact r28 reconfirmed the corrected ship handoff |
| Direct peer/control RPC | **Partial; one C2a pulse swapped on AM4** | One selected post-join direct pulse crosses C1's reliable lane and dispatches on Unity `Update` | Error, player/global/admin lists, reference position, disconnect, and every other `ZRpc` control class | **Verified:** `native-20260730-c2a-final` delivered exactly one typed pulse per client; both withheld copies became stale; native tripwires were registered; all 107 selected server-native attempts were suppressed before `ZRpc.Invoke`; zero native copies arrived |
| Player motion | **Selected boundary swapped on AM4; prior observe-only build remains on P7** | Authenticated numbered position/rotation/velocity frames use UDP with binary-WebSocket fallback; reliable hard resync uses C1. The logical remote player applies them while selected native transform and position writers are suppressed | General identity/prefab breadth and P7 promotion remain | **Verified:** C6 proved both directions, bounded loss/resync, and fresh-process resume; C7 removed the native join dependency |
| ZDO ownership transfer and pickup action | **Partial; selected C4 boundary swapped on AM4** | Server-originated leases bind run/world/ZDO/logical holder/epoch/expiry; Gateway validates actions; the dedicated server performs the authoritative destroy and returns inventory through Lumberjacks | General-prefab ownership/action admission remains; the cutover is gated and P7 still runs the prior path | **Verified:** `native-20260730-c4b-tenth` rejected reclaimed/wrong/expired leases, poisoned selected native owner/pickup/destroy paths, and credited exactly one Raspberry to each client |
| Ship control, authority, and replication | **Selected physical ship boundary swapped on AM4** | Explicit ship-target RPCs carry helm request/release/rudder/speed; Gateway authenticates held control and makes canonical helm release plus owner transfer atomic; the physics owner sends numbered snapshots to AM4; the server journals the canonical ship body and fans a server-originated replica to both clients | Unrelated vehicle prefabs, third-recipient relevance, fallback deletion, and P7 promotion remain separate | **Verified:** r27's exact rerun exposed a stale departed helm user on the future owner; r28 applied `canonical_helm_user=0` on both replicas before handoff and passed 19/19 checks across both real driving/observing directions with native-zero |
| Saddle control, ownership, rider attachment, and replication | **Selected physical saddle boundary swapped on AM4** | Explicit saddle-target RPCs carry control and release; Gateway authenticates the logical rider and monotonic owner epoch; the owner publishes body snapshots and rider edges; disconnect reclaim selects an exact live peer | Arbitrary existing untagged mounts, a third distant recipient, AoI enter/leave, relevance-scoped fan-out, fallback deletion, and P7 promotion remain | **Verified:** exact r27 created one run-tagged tamed Lox, drove/observed both directions, advanced owner epochs 1→5 through disconnect reclaim, held observer attachment p95/max at zero, rejected stale transfer/snapshot/rider frames, resumed both clients, destroyed exactly one target, and passed 18/18 checks with native-zero |
| World identity/bootstrap | **Selected boundary swapped on AM4** | Protocol/release, world id/epoch, seed/name, world-generation version, network time, save epoch, initial zone, typed character id, and logical scene lifecycle cross Lumberjacks | General world/zone breadth and migration fallback deletion remain C8/C10 | **Verified:** C7 cold join reached the intended scene twice per client; wrong release and descriptor/protocol stopped before scene |
| Zone/interest lifecycle | **Partial; selected run-tagged membership swapped on AM4** | Explicit enter/leave, monotonic snapshot epoch, three complete typed bodies, semantic chunk ACK, resume, complete-once, and typed release cross Lumberjacks | General-prefab/zone interest breadth, reference-position integration, and terrain generation remain Valheim; terrain is intentionally local engine work | **Verified:** both C5 clients resumed after chunk-1 socket loss, completed once, unloaded to zero, spawned none on withhold, and every selected native candidate was suppressed |
| Server save/persistence | **Native** | Gateway/event services retain their own records | Valheim world/ZDO save is still canonical game persistence | **Verified:** current architecture; not itself a transport swap |

## One boundary slice for every incomplete path

These are integration slices. Each has one payload, one direction, and a failure
mode. None requires two humans driving game windows.

| Remaining boundary | Smallest useful slice | Failure mode that makes the result legible | Estimated build + real-run cost |
| --- | --- | --- | --- |
| Container/station family | Classify the mutation and ownership shape, then run one two-client ordered inventory/station cell with poison armed | Any duplication, out-of-order mutation, wrong holder/epoch, or native fallback fails the gate | One named C10a physical gate |
| AI/creature family | Classify simulation ownership and handoff, then run one two-client creature cell through transfer/loss/reclaim with poison armed | A stalled/divergent AI, stale holder, or native fallback fails the gate | One named C10a physical gate |
| Vehicle/mount generalization and relevance | Select arbitrary existing untagged targets and prove a third distant recipient's AoI enter/leave plus relevance-scoped fan-out | Run-tag-only targeting, `Everybody` fan-out, a stale replica, or native fallback fails the gate | One named C10a physical gate |
| P7 finalization | Promote the paired candidate, re-prove, delete migration-only fallback, cut a final artifact, and re-prove | Roll back the artifact pair; never selectively reopen a native path | 2–4 days plus two bounded reloads; C10 |

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
- `native-valheim/native-20260730-c0-ledger-baseline/` — first exact P7 native-use
  baseline: 10,446 client-side calls and the native pre-`PeerInfo` stage stall.
- `native-valheim/native-20260730-c0-poison/` — poison proof: the first native
  connection boundary was blocked and all 76 observed calls were poison trips.
- `native-valheim/native-20260730-c0-clean/` — accepted C0 AM4 composition: both
  physical clients joined, moved, disconnected, relaunched, rejoined, and stopped;
  `machine-summary.json` passed with exact server/client ledgers and no writer loss.
- `native-valheim/native-20260730-c1-final/` — accepted C1 AM4 composition: both
  physical clients passed stable-id/epoch resume, exact sequence replay, one accepted
  response, the bounded no-receipt timeout, fresh Valheim process resume, and shutdown;
  `c1-machine-summary.json` passed.
- `native-valheim/native-20260730-c2a-final/` — accepted C2a AM4 composition: both
  physical clients registered the native negative-control tripwire, applied exactly one
  typed Lumberjacks direct pulse on the main thread, marked the intentionally withheld
  copy stale, relaunched, rejoined, and stopped. The server attempted and suppressed
  107/107 selected native sends before `ZRpc.Invoke`; no native copy was delivered;
  `c2a-machine-summary.json` passed.
- `native-valheim/native-20260730-c2b-final/` — accepted C2b AM4 composition: both
  physical clients completed targeted request/response, broadcast, real target-ZDO
  `RPC_ResetCloth`, intentional withhold, fresh-process reconnect, and shutdown. All
  24 selected client attempts and all 19 selected server attempts were suppressed;
  zero native copies, duplicates, or dispatch failures were recorded;
  `c2b-machine-summary.json` passed.
- `native-valheim/native-20260730-c3-sixth/` — accepted C3 AM4 composition: one
  run-tagged ZDO absent from all 1,198 native candidate selections survived a Gateway
  restart, reached late i5 by snapshot, reached both clients by valid delta and
  tombstone, rejected stale/malformed bodies before mutation, drained both isolated
  recipient queues, and entered network `RPC_ZDOData` zero times;
  `c3-machine-summary.json` passed.
- `native-valheim/native-20260730-c4a-second/` — accepted C4a AM4 composition:
  server, OMEN, and i5 each retained one distinct opaque logical peer while Gateway
  and fresh Valheim process turnover changed connection ids. Six ZDO mutations,
  interest, delivery and ACK used only the canonical C1 session; WAL replay,
  late-client snapshot, typed delta/tombstone, two interests, zero pending, cleanup,
  both intended GPUs and unattended shutdown all passed in
  `c4a-machine-summary.json`.
- `native-valheim/native-20260730-c4b-tenth/` — accepted C4 AM4 composition:
  two real Raspberry ZDOs crossed logical-peer leases, disconnect reclaim, wrong
  epoch, expiry, epoch-3 authorization, canonical destroy and authoritative result.
  Selected native ownership/inventory paths were poisoned, inventory rose exactly
  one unit on each client, both completion frames were acknowledged, both clients
  resumed and stopped, and `ownership-lease-cutover-summary.json` passed.
- `native-valheim/native-20260730-c5-final/` — accepted C5 AM4 composition:
  both clients entered from the Lumberjacks descriptor with blank native world
  fields, applied three typed membership objects, replayed chunk 1 idempotently after
  a pre-ACK socket drop, completed once, left with zero stale objects, spawned none
  when membership was withheld, and stopped on the intended GPU. AM4 suppressed all
  selected native candidates; `c5-boundary-summary.json` passed.
- `native-valheim/native-20260730-c5-fault-protocol/` and
  `native-valheim/native-20260730-c5-fault-worldgen/` — deterministic pre-scene
  rejection for the two descriptor compatibility failures.
- `native-valheim/native-20260730-c6-eighth/` — accepted C6 AM4 composition:
  both physical clients applied numbered Lumberjacks motion to the real remote
  player in both directions while selected native transform/position writers were
  suppressed. i5 held through OMEN's exact 20-frame gap, applied the reliable
  sequence-619 resync, queued its ACK, and used binary-WebSocket fallback when UDP
  was unreachable. Both clients completed fresh-process resume and stopped on the
  intended GPU; `c6-boundary-summary.json` records the caveats and hashes.
- `native-valheim/native-20260802-c10a-stamina-r6-sync1/` — accepted C10a
  `UseStamina` AM4 composition: both physical clients selected only the other live
  owner-matching player, applied the exact `50 - 1.25 = 48.75` debit on the owning
  receiver, received correlated sender receipts, resumed once, and stopped. OMEN,
  i5, and AM4 native totals/trips were zero with poison armed; compact retained
  evidence is in `evidence/c10a-usestamina-verification/`.
- `native-valheim/native-20260802-c10a-vehicle-r15-1/` — accepted C10a ship
  composition: both real clients boarded one Karve; i5 drove while OMEN owned;
  authenticated handoff made i5 the owner; OMEN then drove while i5 owned. Both
  observers received canonical server-signed ship snapshots and independently
  measured >15 m motion, rudder, and speed changes. Both clients resumed once and
  stopped; OMEN/i5/AM4 native totals and poison trips were zero; compact retained
  evidence is in `evidence/c10a-ship-physical-acceptance/`.
- `native-valheim/native-20260802-c10a-mount-r27-1/` — accepted selected C10a
  saddle composition: both real clients drove and observed one run-tagged tamed Lox;
  Gateway owner epochs advanced 1→5 through a forced disconnect/reclaim to live i5;
  stale transfer, snapshot, and rider-edge frames rejected; both attachment distributions
  were exactly zero; both clients resumed; exactly one tagged mount was destroyed; and
  all 18 machine checks and OMEN/i5/AM4 native-zero ledgers passed. Compact evidence is
  in `evidence/c10a-mount-physical-acceptance/`.
- `native-valheim/native-20260802-c10a-vehicle-r28-1/` — accepted ship handoff
  reconfirmation after r27 exposed a stale departed helm user on the future owner. r28
  applied canonical release to both replicas before transfer; both physical directions,
  both snapshot streams, both fresh-process resumes, all 19 machine checks, native-zero,
  and clean cleanup passed. Compact evidence is in
  `evidence/c10a-ship-physical-acceptance/r28-handoff-reconfirmation.json`.

## Replan recommendation

C0-C8 are complete at their retained AM4 boundaries. C9's machine/artifact run is
complete and waits only on Derek's one-word rendered-motion verdict. C10a has an
accepted 49-action paired r4 surface, source/runtime classifications for
`RPC_SetConnection` and `RPC_TeleportPlayer`, exact paired r6 physical acceptance
for both legitimate cross-owner `UseStamina` directions, exact paired r27 acceptance
for the selected saddle canary, and exact paired r28 reconfirmation for the repaired
ship handoff. The full prefab and method surface is still not promoted to “swapped.”

Vehicle-control source verification and the selected ship/saddle canaries are closed:
the shared hashes require separate typed contracts and remain generic-lane poison
tripwires. The next local gate is container/station, followed by AI/creature, then
arbitrary untagged vehicle/mount plus third-recipient AoI/relevance generalization. Close
each from source classification plus a real poison-armed receipt; do not rerun retained
C0-C8, stamina, ship, or selected saddle boundaries without contradictory evidence.
Workbench/dashboard work remains frozen until those functional local gates close.

P7 remains stopped and untouched. After the local gates, C10b has two bounded P7
reloads: promote/reprove the accepted pair, then delete migration-only fallback, cut
the final paired artifact, and reprove the named boundaries. The detailed remaining
count and order are canonical in `plan-native-network-final-cutover.md`.
