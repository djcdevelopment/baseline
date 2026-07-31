# Native Valheim networking replacement landscape

**Assessed:** 2026-07-30
**Development topology:** headless dedicated server on AM4; native Windows clients on
OMEN (Tugcorp, RTX 5070) and i5 (Durracktu, Intel Iris Xe).
**Reference deployment:** P7 remains running as the production-reference server and is
unchanged; C0-C6 final-cutover acceptance is on AM4.

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
- Handshake **admission logic** is Lumberjacks-fronted, but Steam connection setup,
  ticket/password crypto, `PeerInfo`, and `AddPeer` remain vanilla.
- Routed RPC is partial on AM4: a fixed registry now carries the complete envelope
  shapes through Lumberjacks and suppresses the selected native methods. Unselected
  method hashes, most direct peer controls, general ownership/world/zone breadth, and
  the underlying Steam socket are still native or partial.
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
  stale objects, and spawned nothing when membership was withheld. The native
  handshake still carries the enclosing peer lifecycle, and general-prefab/zone breadth
  remains for C7-C8.

The shortest honest description is: **the C3 ZDO semantic boundary and selected
control/RPC classes are swapped on AM4, and C3 semantics now ride the canonical
session with process-durable logical peers; C4 also swaps one selected real ownership
and pickup boundary; C5 swaps the selected world descriptor and run-tagged
zone-membership boundary; C6 swaps selected two-player motion authority. General-prefab
semantics, connection, remaining control breadth, Steam-free cold join, native-zero
composition, and P7 promotion are not complete.**

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
unverified and deliberately locked. The enclosing native peer/scene admission remains
until C7, and general breadth/native-zero composition remain C8 work.

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
| Lumberjacks reliable game session | **Swapped substrate with selected C2–C6 semantics** | Stable opaque logical peer, replaceable connection incarnation, ordered reliable control/RPC, ZDO mutation/interest/delivery/ACK, ownership lease/action/result, world descriptor, selected zone snapshot/leave, motion binding, and reliable motion-resync frames, plus cumulative ACK, bounded replay, UDP binding, and socket resume | Remaining direct/routed classes, general ownership/zone breadth, and cold-join semantics remain outside this lane | **Verified:** C1 resume/replay, C4a logical identity, C4b lease reclaim/result, C5 interrupted membership replay, and C6 motion resync all used the same canonical session |
| Handshake and admission | **Partial; off-thread admission and C5 descriptor substitution proven on AM4, prior build still live on P7** | Admission verdict and the selected complete world descriptor cross Lumberjacks; blank native world fields are held and substituted only after descriptor validation | `ServerHandshake`/`ClientHandshake`, Steam ticket verification, password crypto, native `PeerInfo` delivery, vanilla checks on accept, and `AddPeer` | **Verified:** delayed fail-open and normal ACCEPT reached vanilla AddPeer without a main-thread HTTP stall; C5 blanked native world fields but still used the enclosing native peer lifecycle |
| ZDO candidate selection and cadence | **Partial; C3 journal boundary swapped on AM4** | A mutation-seam journal and explicit recipient interest delivered the C3 object independently of `CreateSyncList` | Legacy/general-prefab delivery still uses `ZDOMan.Update`, `CreateSyncList`, sector query, `ShouldSend`, force-send and base priority ordering | **Verified:** C3 object had zero selected candidates across 1,198 native selection passes but reached both clients |
| ZDO outbound carriage | **Swapped for legacy redirect and C3 semantic boundary** | Selected `*` prefabs use the redirect; C3 authoritative mutation bodies, revisions and tombstones use the durable journal over C1 | C3 body capture still observes Valheim's authoritative mutation seams; semantic breadth remains | **Verified:** C4a accepted six canonical mutations, replayed WAL across Gateway restart, retained two isolated logical recipients and ended zero pending |
| ZDO inbound carriage/apply | **Partial; C3 typed boundary swapped on AM4** | C3 clients receive canonical-session frames, validate, and directly create/update/delete/revision/owner/position/deserialize on Unity `Update` | Legacy consumer still reconstructs a `ZPackage` and invokes `RPC_ZDOData`; general-prefab typed parity is not yet proven | **Verified:** C4a used only canonical carriage; both clients applied valid delta/tombstone, i5 applied late snapshot, stale/malformed rejected, network `RPC_ZDOData` zero |
| Co-presence ZDO fan-out | **Corrected and integration-proven on AM4; disabled on P7 pending promotion** | Emits native-selected revisions to the exposing recipient and any in-band observer that is behind | Candidate discovery and delivered-revision bookkeeping remain native | **Verified:** two unattended physical clients, 1,340/1,340 native-selected `Emit`, zero non-emit, and successful inventory return on both clients |
| Routed gameplay RPC (`ZRoutedRpc`) | **Partial; fixed C2b registry swapped on AM4** | Full `RoutedRPCData` envelopes for the selected request, response, broadcast, target receipt, and `RPC_ResetCloth` hashes cross C1 and dispatch through `HandleRoutedRPC` on Unity `Update` | Unselected method hashes still use native `RouteRPC`/`RPC_RoutedRPC`; the fixed registry is not yet the whole gameplay surface | **Verified:** `native-20260730-c2b-final` completed both directions, broadcast, real target-ZDO dispatch, withhold, and reconnect; all 43 selected native attempts were suppressed with zero native copies, duplicates, or dispatch failures |
| Direct peer/control RPC | **Partial; one C2a pulse swapped on AM4** | One selected post-join direct pulse crosses C1's reliable lane and dispatches on Unity `Update` | Error, player/global/admin lists, reference position, disconnect, and every other `ZRpc` control class | **Verified:** `native-20260730-c2a-final` delivered exactly one typed pulse per client; both withheld copies became stale; native tripwires were registered; all 107 selected server-native attempts were suppressed before `ZRpc.Invoke`; zero native copies arrived |
| Player motion | **Selected boundary swapped on AM4; prior observe-only build remains on P7** | Authenticated numbered position/rotation/velocity frames use UDP with binary-WebSocket fallback; reliable hard resync uses C1. The real remote player applies them while the selected native transform and position writers are suppressed | Native join still creates the enclosing remote player scene instance until C7; general identity/prefab breadth and P7 promotion remain | **Verified:** `native-20260730-c6-eighth` applied both directions, suppressed 300 native writer calls in each observer probe, held a 20-frame gap without native fallback, applied reliable resync, and resumed both clients |
| ZDO ownership transfer and pickup action | **Partial; selected C4 boundary swapped on AM4** | Server-originated leases bind run/world/ZDO/logical holder/epoch/expiry; Gateway validates actions; the dedicated server performs the authoritative destroy and returns inventory through Lumberjacks | General-prefab ownership/action admission remains; the cutover is gated and P7 still runs the prior path | **Verified:** `native-20260730-c4b-tenth` rejected reclaimed/wrong/expired leases, poisoned selected native owner/pickup/destroy paths, and credited exactly one Raspberry to each client |
| World identity/bootstrap | **Partial; selected descriptor swapped on AM4** | Protocol/release, world id/epoch, seed/name, world-generation version, network time, save epoch, and initial zone cross Lumberjacks and substitute for blank native world fields | The native handshake and `PeerInfo` callback still trigger the enclosing peer/scene lifecycle; Steam-free cold join is C7 | **Verified:** both C5 clients entered the intended world from the descriptor; wrong protocol/world generation stopped before scene |
| Zone/interest lifecycle | **Partial; selected run-tagged membership swapped on AM4** | Explicit enter/leave, monotonic snapshot epoch, three complete typed bodies, semantic chunk ACK, resume, complete-once, and typed release cross Lumberjacks | General-prefab/zone interest breadth, reference-position integration, and terrain generation remain Valheim; terrain is intentionally local engine work | **Verified:** both C5 clients resumed after chunk-1 socket loss, completed once, unloaded to zero, spawned none on withhold, and every selected native candidate was suppressed |
| Server save/persistence | **Native** | Gateway/event services retain their own records | Valheim world/ZDO save is still canonical game persistence | **Verified:** current architecture; not itself a transport swap |

## One boundary slice for every incomplete path

These are integration slices. Each has one payload, one direction, and a failure
mode. None requires two humans driving game windows.

| Remaining boundary | Smallest useful slice | Failure mode that makes the result legible | Estimated build + real-run cost |
| --- | --- | --- | --- |
| Steam transport | Put one allow-listed control message through a Lumberjacks client transport while deliberately suppressing its native socket send; prove receipt and response on a joined client | Gateway remains healthy but the native copy is absent; no response means the new transport did not cross | 2-3 days; foundational |
| Handshake completion | Configure one Lumberjacks-only rejection for an otherwise admissible seeded client, observe the exact client error, remove it, then autojoin successfully | Dead/unparseable authority must produce the configured strict result without freezing the server | 1 day after off-thread decision plumbing |
| C3 ZDO semantic breadth | Canonical carriage is complete; now exercise pickup/ownership plus zone-membership prefab semantics before removing the legacy consumer | Restart Gateway/client mid-delivery; the logical recipient resumes from WAL with no `RPC_ZDOData` fallback or duplicate mutation | 1-2 days folded into remaining C4-C5 |
| Remaining routed gameplay RPC | Inventory runtime method hashes by semantic class, add typed codecs/handlers to the fixed registry, and delete the native selected-method fallback as each class crosses | Withhold one member of each newly selected class and require deterministic stale/fail-closed behavior with no native copy | 1-2 days, folded into the C3-C7 burn-down |
| Remaining direct peer/control RPCs | Extend C2a's fixed typed dispatch to player/global/admin lists, reference position, error, and disconnect classes, suppressing each matching native invocation only in cutover mode | Withhold each selected Lumberjacks class and require bounded stale/fail-closed behavior rather than a native copy | 1-2 days, folded into C2b/C7 |
| Ownership breadth | Expand C4's admitted lease/action contract from the run-tagged Raspberry to every ownership-bearing prefab/action found by the native-use ledger, then delete the selected-only gate | An unadmitted owner or pickup method must trip poison rather than fall back to Valheim | 1–2 days folded into C5–C8 |
| Steam-free world bootstrap | Start C1 without `+connect`, create the minimal logical Valheim peer with no `ZSteamSocket`, consume C5's descriptor, and remain in-world for 60 seconds before expanding the adapter | Unavailable Gateway, invalid enrollment/release, or wrong descriptor must fail closed and never try the native server | 4–7 days; C7 and the highest remaining architecture risk |
| General zone/interest breadth | Compose C5 membership with the real C8 zone-crossing/pickup/ownership scenario under native poison, then remove selected-only gates | Any unadmitted prefab or stale membership must trip poison/reopen C5 rather than fall back to native selection | 1–2 days folded into C8 |

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

## Replan recommendation

Do not start the motion tuning or transpiling lab yet. C0-C6 are complete at their
retained AM4 boundaries. C3/C4a prove durable ZDO selection, canonical carriage and
typed apply without selected native selection or network `RPC_ZDOData`; C4 proves
logical-peer lease/action authority and exactly-once inventory for one real pickup
per client; C5 proves selected descriptor substitution and resumable run-tagged
membership with native selection suppressed; C6 proves selected binary motion
authority, native-writer suppression, bounded hold, and reliable resync. The full
prefab and method surface is still not promoted to “swapped.”

C7's early falsifier passed in `native-20260731-c7-fourth`. After the canonical
Lumberjacks session and descriptor were ready, both physical clients closed their
selected native `ZSteamSocket`, held the live scene for at least 60 seconds with zero
native funnel delta, exercised thousands of suppressed native socket/RPC calls, and
reported no native fallback. Both then completed the manifest's fresh-process resume.
This removes the feared “engine requires a continuously live native socket” branch;
it does not prove cold join because native `+connect`, handshake, and peer construction
still preceded quarantine.

Continue C7 by starting C1 from the request manifest, reconstructing the minimal
logical peer/session from C1/C2/C5 without `+connect`, and reaching character scene
entry with native poison armed. Invalid enrollment/release, unavailable Gateway, and
wrong descriptor must fail closed without trying the native server. Do not introduce
an opaque packet tunnel. The mandatory C7 replan follows that real cold-join receipt.
Keep the remaining **7–16 focused engineering day** estimate until that replan; only
after the native poison gate reaches zero does motion tuning measure the system
intended to ship.
