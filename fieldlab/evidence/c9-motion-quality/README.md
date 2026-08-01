# C9 motion quality — partial boundary, machine evidence only

**Status:** open. The machine half of C9's acceptance is retained here. The rendered
observer clip is **not** produced; see "What this does not prove".

**Source:** the retained C8 acceptance pair `native-20260731-c8-full44` and
`native-20260731-c8-full45`, on the frozen build (mod SHA-256
`765090d17981235209deec2d9718221eda4230aa27b2a99998f99ffeac08c28f`, source commit
`c0db122`). No new run was needed for any claim below; every number comes from
receipts those two accepted runs already produced.

The machine-readable result is [`c9-motion-quality-summary.json`](c9-motion-quality-summary.json),
regenerable with `fieldlab/scripts/Write-C9MotionQualitySummary.py`.

## What this proves

Against C9's four acceptance criteria, measured across both runs and both clients:

- **No hidden native correction.** `native_fallback=true` appears zero times in any
  client's motion receipts in either run.
- **No unexplained hard correction.** All 16–17 corrections per client per run map to
  a commanded action — `teleport_to`, `portal_roundtrip`, `zone_cross`,
  `zone_membership_resume`, `gateway_restart_resume`, or the injected motion gap.
  Attribution deliberately considers **both** clients' timelines: a correction lands on
  the *remote* player, so an observer sitting in its own `wait` is routinely explained
  by the peer's concurrent action, not its own.
- **Divergence is transient, never persistent.** Every `target_rejected` burst repeats a
  *single* sequence number and clears within 0.501 s at the longest. There is no run in
  which target error stays elevated across sequences.
- **Recovery from injected loss is bounded.** Hold recovery is 0.4–1.7 s in the ordinary
  case; the longest is 10.866 s, and every recovery beyond ~9 s sits inside a deliberate
  interruption (the Gateway restart, or a portal leg).
- **No apply-attributable wall-clock hitch, on both clients.** Every frame hitch in both windows is
  Valheim's own lifecycle — `Starting respawn` (6.7 s, twice per run, once per session),
  `Starting music menu`, `Sending PlayFab login request`, `ZNET START`, character-file
  load. None is explained by a Lumberjacks section.

  Attribution here is by **magnitude, not containment**. The perf probe calls
  `UpdateFrame` at the top of `ComfyNetworkSense.Update`, so *every* hitch row is written
  inside that section by construction and describes the *previous* frame; containment
  would flag everything. A Lumberjacks section is only credited with a long frame when it
  accounts for at least half of it. Under that rule, zero hitches are apply-attributable.

## What is visible but bounded

Each legitimate teleport produces a **freeze-then-snap on the observing client**: the far
target is refused every frame by the 30 m fail-closed correction guard for roughly half a
second, until the reliable teleport announcement lands and the resync applies. Errors seen
this way range from 72 m (zone cross) to 4.9 km (portal). This is correct fail-closed
behaviour and never falls back to native — but it is the artefact a `smooth`/`rough`
verdict would most likely react to, and it is why the clip still matters.

## Resolved — the once-per-session stall is vanilla's own world pregeneration

An earlier revision of this document recorded a multi-second once-per-session stall as an
unresolved finding "in `LumberjacksMotionRunner.Update`", and flagged the absence of a frame
hitch inside it as an anomaly. **Both of those were wrong.** The corrected account:

**It is not the motion runner.** `ComfyNetworkSense.cs:301` opens a single perf section named
`ComfyNetworkSense.LumberjacksMotionRunner.Update` that in fact wraps **eight** cutover
runners and names only the last. The motion runner is provably inert here — its `ShouldRun()`
requires `Player.m_localPlayer`, which does not exist before respawn.

**The cost is Valheim's own.** It is `WorldGenerator.Initialize(world)` — river/lake
pregeneration (`FindLakes`, `PlaceRivers`, `PlaceStreams`) — called synchronously on the main
thread from `LogicalPeerCutoverRunner.ConstructPeer`
([LogicalPeerCutoverRunner.cs:238](../../../network/mod/ComfyNetworkSense/Core/Services/LogicalPeerCutoverRunner.cs:238)).

**It is not a regression.** Vanilla does exactly the same thing at the same point:
`ZNet.RPC_PeerInfo` calls `WorldGenerator.Initialize(m_world)` immediately before setting
`ConnectionStatus.Connected` (decompiled `ZNet.cs:304`), which is the sequence `ConstructPeer`
reproduces at lines 238–240. The Steam-free cold join **pays vanilla's join cost rather than
adding one.**

Corroborated 8/8 by an independent clock — every section end matches a
`logical_peer_constructed` receipt to ~1 ms, and the announce→constructed gap matches the
section elapsed within ~20 ms:

| Client | Section elapsed | Announce→constructed gap |
| --- | --- | --- |
| OMEN | 1878.4, 1861.8, 1867.1, 1863.2 ms | 1.899, 1.867, 1.878, 1.873 s |
| i5 | 2256.6, 2459.3, 2241.1, 2460.4 ms | 2.250, 2.526, 2.268, 2.525 s |

**There was no missing hitch.** Both `perf-hitches.jsonl` and `perf-sections.jsonl` stamp
`timestamp_utc` at *completion*, so spans must be reconstructed backwards from their duration.
Done that way, the section and the large `Starting respawn` frame **start at the same instant**
in all eight occurrences (delta +0.03 ms to +0.77 ms), and the section is 26–28 % of that frame
(6.7 s on OMEN, 8.5–9.5 s on the i5). The stall was always inside a hitch that had been
recorded correctly; the earlier analysis compared the hitch's *end* against the section's span.

Bearing on C9: **none.** This is one-time cold-join cost, before the player spawns, on a path
that has nothing to do with motion apply.

## Still open

- **The perf section label misattributes cost — fixed in source, not yet in the build.** The
  single section that reported seven other runners' time under the motion runner's name is now
  eight per-runner sections inside an honestly named `ComfyNetworkSense.CutoverRunners.Update`
  roll-up. That is a source change only: the C9 build freeze holds, the deployed artifact is
  still mod SHA-256 `765090d1…` from `c0db122`, and **every number in this document was measured
  under the old single-section label**. The new labels first appear in whatever build C10a cuts;
  from that build on, `ComfyNetworkSense.LumberjacksMotionRunner.Update` rows mean the motion
  runner alone and are not comparable to the same-named rows in the C8/C9 receipts.

## What this does not prove

- **No rendered observer clip exists**, so no subjective verdict has been taken. C9's
  `smooth`/`rough`/`mixed` question is still unanswered.
- Motion windows in the C8 composition are 6 s each — long enough for a binary authority
  proof, short for judging rendered quality. The C9 scenario
  (`fieldlab/scenarios/native-20260801-c9-motion1.json`) widens them to 24 s.
- Nothing here revisits C0–C8 architecture, and nothing here bears on the C10 gates.

## Capture lane, built and proven

Ready for the outstanding run:

- `fieldlab/scripts/Invoke-MotionClipCapture.ps1` — bounded per-client screen capture.
  An ssh session lands in a non-interactive desktop and gdigrab fails there with
  `error 5`, so the i5 path reuses the interactive scheduled-task idiom the native client
  harness already relies on. Capture is proven on **both** machines; OMEN encodes through
  `h264_qsv` (NVENC is unusable — the installed driver predates ffmpeg 8.1.2's required
  API), with an automatic `libx264` fallback.
- `fieldlab/scripts/Build-MotionQualityClip.py` — trims each whole-run recording to that
  client's observer window using its own scenario receipts, burns in a telemetry readout
  built from its own motion receipts, and stacks the two panels. Proven end to end against
  full45's retained telemetry.
- Each panel is trimmed and annotated against **its own machine's clock**. No
  cross-machine simultaneity is claimed, and none is needed: the two direction/role
  combinations are sequential in the scenario, so the panels are two independent,
  internally consistent views.
