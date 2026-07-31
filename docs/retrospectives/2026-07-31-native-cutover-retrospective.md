# Native Valheim cutover retrospective — 2026-07-31

## Executive summary

This session took the Lumberjacks/Valheim lane from a promising split-repository
prototype to a substantially proven native-zero integration path. The decisive
choice was to stop trying to infer correctness from isolated unit tests and instead
drive short, real two-client probes through the actual AM4 server, OMEN client, i5
client, Gateway, world objects, portals, ownership, and reconnect boundaries.

The current result is honest and useful:

- C0 through C7 are complete, with their required replans and retained evidence.
- C8a through C8g are proven by focused integration gates.
- C8 full composition reached the post-Gateway-restart ownership sequence, but
  full24 is **not accepted**: OMEN's Player died after a reconnect invalidated the
  per-instance godmode safeguard. The run was stopped and its manifest quarantined.
- The safety fix is built and SHA-verified on OMEN and i5. A clean full C8 run still
  needs to be performed after OMEN is relaunched and confirmed ready.
- C9 rendered-feel tuning and C10 P7 promotion/fallback deletion remain ahead.

The key architectural proof is now stronger than a green harness: the native Valheim
transport is suppressed, the logical peer and typed Gateway lanes carry the intended
semantics, AoI delivery is sparse, portal dependencies are indexed, and durable ZDO
replay survives Gateway process reincarnation. The remaining work is acceptance and
polish, not a return to speculative architecture.

## Goal and plan lifecycle

The goal was to complete the native cutover roadmap C0–C10, replanning at the
mandatory C3, C5, C7, and C8 boundaries. The working plan became:

1. Establish the native-use ledger, poison gate, timing, and unattended composition
   driver (C0).
2. Prove one durable, ordered/resumable Lumberjacks session with real boundary
   evidence (C1).
3. Replace the typed direct-control pulse, then prove the full routed RPC shapes
   (C2a/C2b).
4. Replace ZDO mutation, selection, snapshot, and apply paths (C3).
5. Replace ownership and world/zone synchronization (C4/C5).
6. Move motion onto C1 and replace Steam/native cold join (C6/C7).
7. Prove the complete two-client native-zero AM4 scenario (C8).
8. Tune rendered feel only after the native pipeline is proven (C9).
9. Promote to P7, remove fallback paths, re-prove, and close the landscape (C10).

The first seven phases are now evidence-backed. The C8 plan was deliberately split
into short gates and a retained full composition run so a contract mismatch could be
found in seconds rather than after a 15–28 minute blind wait. That paid off: each
failure exposed a real lifecycle assumption, and each repair was immediately tested
against the next boundary.

## What the integration loop taught us

### 1. The Player is a lifecycle object, not a static local variable

The largest miss was treating godmode as something established once before a
teleport. A Gateway reconnect can replace or rehydrate the Player while the peer is
temporarily disconnected. The new Player then has a fresh godmode flag and can fall
from a test altitude before the next teleport action runs.

The fix is now in
[`NativeCutoverScenarioController.cs`](../../network/mod/ComfyNetworkSense/Core/Services/NativeCutoverScenarioController.cs:93):
the controller maintains the survival invariant even while `JoinedClientReady` is
false, re-arms godmode on the current Player, and rejects a dead Player instead of
continuing. This is a general lesson: rebind safety and identity-dependent state at
every session lifecycle boundary.

### 2. “Connected” is not “ready”

The external Gateway restart probe initially proved socket recovery but ownership
started before the post-reconnect world/AoI state was usable. The reliable barrier
now observes either a higher same-process resume epoch or Gateway reincarnation with
the same logical peer, then allows the next probe to establish its own readiness.

The next agent should continue to distinguish:

- transport connected;
- logical peer bound;
- world/zone loaded;
- AoI dependencies instantiated;
- target ZDO available and claimable;
- rendered Player safe and alive.

### 3. Durable state changes the fault trigger

The first restart trigger assumed the ZDO drive would contain a non-delivery mutation.
After snapshot durability was correctly implemented, later mutations were already
`delivery_only`; the trigger then never fired. The harness was corrected to accept the
correlated `drive_complete` once it had verified durable objects were present. Do not
encode a fault trigger around an implementation detail that the preceding phase is
supposed to eliminate.

### 4. Observation windows need minimum duration plus a correlated recovery

The gap observer could start after recovery had already happened, or end before the
resync arrived. A fixed sleep was not an observation. The working rule is now:

> wait at least the requested sample duration, then finish only after the correlated
> recovery is observed or the explicit action deadline expires.

This pattern generalizes to every asynchronous probe.

### 5. Queue-full is often transient, not a semantic failure

World-zone entry during Gateway restart hit a queue-full condition. Treating that as
terminal made the test fail on capacity timing rather than behavior. Retryable
resource pressure should remain bounded and correlated to the action deadline;
malformed contracts and wrong epochs should still fail immediately.

### 6. AoI and portals need dependency evidence

The dual-channel design is valuable precisely because it avoids sending every world
update to every player. The accepted gates demonstrate sparse sector delivery,
targeted dependencies, and portal roundtrips on both OMEN and i5. AM4 currently loads
the portal index (4,472 links observed) and spawner relationships (85,439 observed).
The next optimization is to measure initial-load cost and prioritize portal-linked
dependencies asynchronously; do not invent a second portal architecture before the
measurements say it is needed.

## Common mistakes and practical tips

- Do not trust a green unit test as a contract proof. Use a short real client/server
  probe with synthetic data, then retain the receipt and the negative control.
- Do not wait 15 minutes for the first useful signal. Put a fast typed pulse or
  single-object probe before every long composition action.
- Do not treat a reconnect, relaunch, or Player recreation as a continuation of the
  old object graph. Rebind identity, safety flags, AoI interest, and target objects.
- Do not use the vanilla `god`/`fly` console commands on a dedicated-server client;
  they are cheat-gated. The safe command is `network_sense_godfly on`, and the
  automation calls the Player API directly.
- Keep old scenario files and run directories. They are evidence, not disposable
  scratch. When an invalid run must be stopped, quarantine the manifest and retain
  receipts.
- Use the repository root only. `C:\work\comfy` and `C:\work\lumberjacks` are stale
  retired checkouts and can silently produce false confidence.
- Treat i5 offline as normal. Run `tools/i5/Test-I5Link.ps1` once, report offline,
  and stop; never retry-loop or fall back to passwords.
- After changing `fieldlab/`, `network/`, or `infra/gcp/p7/`, append the living
  Lumberjacks roadmap note and regenerate/check the staged HTML in the same commit.
- Keep the AM4 server restart budget in mind. The server has already loaded the large
  world successfully; prefer local loops and client-side probes before another
  restart.

## Handoff for the next agent

Start by confirming OMEN is relaunched, alive, and on the patched DLL. If manual
recovery is needed, run `network_sense_godfly on` before any teleport. Do not resume
the quarantined full24 manifest.

The exact client build currently verified on OMEN and i5 is:

`E6634AF7912AD4B5882310D15DD3E7C97E4BF31CB542B1675BB5FF410E589AAE`

The invalid run is
`fieldlab/runs/native-valheim/native-20260731-c8-full24`; its receipts are retained,
but it must not be promoted to acceptance. Earlier focused gates, especially the
two-client portal gate and the Gateway-restart WAL proof, are valid evidence.

Next actions, in order:

1. Confirm the patched DLL on both clients and that no native-cutover manifest is
   active.
2. Generate a fresh C8 full scenario (do not overwrite full17–full24).
3. Run it with seconds-scale polling. Verify continuous godmode receipts across the
   disconnect interval, then verify ownership, zone, portal, and final rejoin.
4. Retain the full composition, lifecycle, Gateway journal, save-integrity, poison,
   and coverage summaries. Mark C8 complete only after the clean full run passes.
5. Perform the mandatory post-C8 replan. C9 should measure rendered feel on the
   proven native motion path; it should not reopen C0–C8 architecture without new
   evidence.
6. At C10, sync the exact final DLL to AM4/OMEN/i5, remove fallback paths only after
   the replacement evidence is retained, run the short gates again, then perform the
   final P7 acceptance.

The project is in a good place: the hard part is now making the final evidence
repeatable and honest. Preserve the fast feedback loop, especially around lifecycle
boundaries, and the remaining work should be controlled engineering rather than
face-first discovery.
