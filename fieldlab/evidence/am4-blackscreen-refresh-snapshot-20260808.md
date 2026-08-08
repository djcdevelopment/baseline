# Black screen on AM4 under `zdoRedirectPrefabs = *` — root cause (2026-08-08)

Client joins AM4, server confirms the character, client renders black. HUD:
`pieces 0 | entities 0 | zone 0:0`, `server local session, no remote server pulse`.

**Root cause (verified):** the Gateway issues a recipient's world snapshot exactly
once. When the client tears down ZNet it discards its entire *inbound* delivery
queue, but the Gateway keys pending deliveries on the **logical peer id**, which
survives the teardown. On rejoin the client's `refresh=true` re-snapshot request is
silently voided by a de-duplication guard, so the ~1230-object world snapshot is
never reissued. The client's world stays empty.

This is a latent defect from 2026-07-30 that only became visible when the server
widened to `zdoRedirectPrefabs = *` on 2026-08-07.

## The defect

`Lumberjacks/src/Game.Gateway/Valheim/ValheimZdoJournalService.cs`,
`RegisterInterest` (~line 346):

```csharp
if (changed || interest.Refresh)          // Refresh = "resend me everything"
{
    foreach (var state in _objects.Values)
    {
        if (!Matches(interest, state)) continue;
        if (HasPending(recipientId, state)) continue;   // ...silently negates it
        Enqueue(recipientId, state.Tombstone ? "tombstone" : "snapshot", ...);
```

`HasPending` (line 554) skips any object already queued for that recipient. As a
dedup for a *live* consumer that is correct. But the client sets `refresh=true`
precisely when it has thrown its inbound queue away — and the Gateway answers
"already pending, skipping." The deliveries it is deduping against are ones the
client can never receive.

Client side, `network/mod/ComfyNetworkSense/Core/Services/ZdoJournalCutoverRunner.cs`:

```csharp
public static void NotifyWorldEpochChanged(string previous, string current) {
    ...
    active.ResetClientEpochState();     // drains _clientInbound — deliveries dropped
    active.Write("world_session_epoch_changed", "client",
        "previous=" + previous + " current=" + current + " stale_deliveries_discarded=true");
}
```

`ResetClientEpochState()` (line 1368) drains `_clientInbound` and clears
`_appliedRevisions`. Nothing informs the Gateway. The recipient id is the logical
peer id (line 1336, `CanonicalEnabled()` branch) — stable across the teardown, so
the Gateway sees the same recipient with a queue it believes is still in flight.

## Why it fires on every launch

The harness join is two-phase: a character-select connection, then the real join.
The first phase registers interest and burns the snapshot; its teardown discards it.
From `comfy-network-sense/zdo-journal-cutover.jsonl`, run `native-20260808-flipped-omen`:

| time (UTC) | event | detail |
|---|---|---|
| 03:38:34.123 | `interest_registered` | **snapshot_count=1230** pending=1230 |
| 03:38:36.988 | `world_session_epoch_changed` | `current=` (empty) `stale_deliveries_discarded=true` |
| 03:40:44.215 | `interest_registered` | **snapshot_count=9** pending=1232 |
| 03:40:49.199 | `interest_registered` | **snapshot_count=1** pending=1232 |
| 03:42:56.575 | `interest_registered` | **snapshot_count=0** pending=1952 |
| 03:42:58.563 | `interest_registered` | **snapshot_count=0** pending=1944 |

1230 → 9 → 1 → 0. The world is delivered once, to a client that is about to discard
it, and never again. Only **16** journal-cutover events exist for the whole run;
healthy runs in the same file show ~42,000 `delta_applied_typed`. This run has zero.

**This is why restarting the Gateway did not help.** Clearing `_pending` (in memory)
does restore a full snapshot — but the client's own two-phase join re-arms the trap
within three seconds of the next launch. The "stale gateway zone bank" line of
inquiry was not wrong about the mechanism being stateful; it was cleaning the wrong
state at the wrong time.

## Why `*` exposed it and the scoped redirect did not

Under the known-good scoped redirect (`Player,Pickable_Mushroom,Mushroom`,
`native-20260807-rung3-twoclient`) the world arrived over Valheim's native ZDO path
and the lane carried only players and mushrooms. Losing the lane snapshot cost you
mushrooms. Under `*` the lane snapshot **is** the world, so the same lost snapshot
is a black screen. The 08-07 widening did not introduce the bug — it removed the
native delivery that was masking it.

## What was working (ruled out as cause, verified)

These all succeeded and should not be re-investigated:

- **Server publish.** Journal live: 2466 mutations, 1233 durable objects, hundreds of
  distinct prefabs. `*` is genuinely redirecting everything.
- **World/zone cutover.** `native_blank_world_payload_observed` → `peer_info_world_substituted
  source=lumberjacks` → `world_bootstrap_applied_typed start_location=StartTemple
  global_keys=8 location_icons=10`. The descriptor lane is healthy.
- **Client cutover legs.** Armed via `native-autotest-request.json`
  (`ArtifactStage` defaults to `candidate`, so `-Enable*Cutover` reach the mod).
  `world-zone-cutover.jsonl` and `zdo-journal-cutover.jsonl` both written during the run.
  The boot line `Effective cutover mode at boot: native` reports `lumberjacksCutoverMode`
  only — a telemetry declaration, not a functional gate.
- **Authoritative consumer.** ~1481 envelopes applied, and `applied` is verified, not
  optimistic: `ZdoAuthoritativeConsumerRunner.Apply` invokes `RPC_ZDOData` then reads the
  ZDO back from `ZDOMan` and throws if absent. This is a *separate* subsystem from the
  journal cutover runner and its health masked the empty world.
- **`repl policy=tiered sent=0 ... bandPop near=0`.** Red herring. That line is
  `Game.Simulation/Tick/TickMetrics.cs` — the Lumberjacks *sim* observer model, an
  unrelated lane from the Valheim ZDO journal.
- **run_id partitioning.** Producer stamps `native-20260808-i5-configbootstrap`, consumer
  registers `native-20260808-flipped-omen`. Cosmetic: `Record()` re-stamps each delivery
  with the interest's RunId, so run_id is a label, not a delivery filter.

## Fix

The semantically correct place is the Gateway: `refresh` must mean refresh. A recipient
asking for one is declaring its inbound queue gone, so its pending deliveries are
unreachable and must be replaced, not deduped against.

```csharp
if (changed || interest.Refresh)
{
    // A refresh is the recipient declaring it discarded its inbound queue
    // (ResetClientEpochState on a ZNet teardown). Its pending deliveries are
    // unreachable, so drop them before re-snapshotting; otherwise HasPending
    // dedups against deliveries the client can never receive.
    if (interest.Refresh) _pending.Remove(recipientId);
    foreach (var state in _objects.Values)
    ...
```

`_nextSequence` is per-recipient and monotonic, tracked independently of `_pending`
(line 544), so re-enqueued deliveries get fresh higher sequences — no ack collision
with the discarded ones.

**Not yet tested.** Applying it requires rebuilding the Gateway image and recomposing
with both `docker-compose.yml` and `docker-compose.enrollment-lab.yml` (omitting the
second drops `LUMBERJACKS_ENROLLMENT_PATH` and empties `/api/v0/enrollment`).

A defensible second change, independent of the first: the client should not register
journal interest during the character-select connection, only after the real join. That
removes the burn-then-discard cycle at its source rather than repairing it after.

## Fix applied and verified live — 2026-08-08

The proposed change was applied verbatim to `RegisterInterest`, cut as Gateway image
`m7-c10b-20260808-r43` (admitting the frozen mod `m7-c10b-20260807-r42`), deployed to
OMEN, and proved with a real client join.

**Unit level.** Three regression tests added at
`Lumberjacks/tests/Game.Gateway.Tests/ValheimZdoJournalRefreshTests.cs`. Mutation-tested
rather than merely run — with the one-line fix commented out, 2 of the 3 fail
(`Expected: 50, Actual: 0` on the re-snapshot, and `re-snapshot reused sequence 1;
highest discarded was 10` on the sequence check). The third,
`UnchangedInterestWithoutRefreshStillDedupsAgainstALiveQueue`, passes either way by
design: it guards against the fix widening into "every registration re-sends
everything". Full gateway suite 247/247.

*Testing note worth keeping:* the full suite first reported 2 red immediately after the
mutated file was restored. That was a stale build, not a regression — `Copy-Item`
preserves the backup's original mtime, which was older than the DLL compiled during the
mutation run, so MSBuild judged the tree up to date and reused the mutated binary.
Touching the source and rebuilding gave 247/247. Any incremental result in this repo
taken straight after a file restore should be distrusted.

**Live level.** Client `native-20260808-flipped-omen`, six cutover legs armed on both
sides, AM4 at `lumberjacks-primary` with `zdoRedirectPrefabs = *` — i.e. the exact
configuration that produced the black screen.

| | broken run 03:38-03:42 | r43 run 04:27 |
|---|---|---|
| `interest_registered` snapshot_count | 1230 → 9 → 1 → 0 → 0 | 1233, then 8 for a different zone set |
| `canonical_delivery_progress` | none | `banked=1024 inbound=962 delivery_seq=1024` |
| client HUD | `pieces 0 \| entities 0 \| zone 0:0` | `pieces 667 \| zone 34:-1` |
| client state | black screen, `server local session, no remote server pulse` | Black Forest rendered; terrain, runestones, vegetation, minimap |
| client log | stalled | `Starting music blackforest`, then `TERRAIN_COMP awake` across zones 34,-2 and 34,0 |

The second registration returning 8 rather than a full re-issue is not the defect
recurring: that call is `zone=34,-1 radius_zones=2`, a different zone set from the
first, so 8 matching objects is the correct answer. `refresh=true` is confirmed present
in the client's `canonical_interest_queued` detail, so the fixed path is the one being
exercised.

**Not yet covered:** the HUD reports `entities 0` and `connection Mixed / owner Maybe`
with a single client in world. Whether those are expected for a solo occupant under
`*` is unverified. Two-client behaviour is also untested — i5 was not joined for this
run, so nothing here speaks to remote-player motion, which is what C9 needs.

## Separate finding — Gateway is not the r42 pair image

The posture doc claims "Gateway: r42 pair image on OMEN." The running container
`lumberjacks-local-gateway-1` is `lumberjacks-local-gateway:latest`
(`sha256:5d0588cc…`, built **2026-08-02**). The r42 image
`lumberjacks-gateway:m7-c10b-20260807-r42` (`sha256:4329c502…`, built 2026-08-07)
exists on the host but is not deployed. Server and both client mods are r42.

This is **not** the root cause — `ValheimZdoJournalService.cs` has not changed since
2026-08-02, so the source analysed above is what the deployed binary runs. But the
pair claim in the posture record is inaccurate and should be corrected or the image
promoted.

## Correction to the repo record

`fieldlab/evidence/am4-full-cutover-posture-20260807.md` says the OMEN client is armed
by installing the personalized pack config. That config
(`Comfy-P7-Mods-waryfool-r42.zip`) ships **every cutover leg `false`**, sets only
`zdoAuthoritativeConsumerEnabled = true` and the window id, and is a 595-line schema
that predates `lumberjacksCutoverMode` entirely (the live cfg is 751 lines). The
harness's `Enable-LabSessionConfig` does not write any `*CutoverEnabled` key either.

So the doc's central claim — "Launch Valheim normally on either machine — no harness,
no arming" — does not hold: a normal launch produces a client with every cutover leg
off against a server that suppresses all native ZDO traffic. Arming currently depends
on the ephemeral `native-autotest-request.json`, which expires in 15 minutes and is
deleted on join. That is a real gap, separate from the black screen, and it means the
lab is not in fact playable without the harness today.
