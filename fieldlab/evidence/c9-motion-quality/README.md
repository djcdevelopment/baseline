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
- **No apply-attributable wall-clock hitch (OMEN).** Every frame hitch in both windows is
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

## Open finding — not resolved

`LumberjacksMotionRunner.Update` blocks for **~1.87 s exactly once per game session**,
about 4.8 s before Valheim logs `Starting respawn`, and never during steady motion.
Reproduced 4/4 across both runs with under 20 ms variance (1878.4, 1861.8, 1867.1,
1863.2 ms).

It sits on the session/transport **setup** path, not the motion apply path (apply runs in
`LateUpdate`). Two candidates remain open: the synchronous `udp.Connect(host, port)`
hostname resolution at `LumberjacksMotionRunner.cs:517`, and the legacy motion-lane
teardown when the canonical session takes over. **Which one is unproven** — and notably no
frame hitch is recorded inside those 1.87 s spans, which is itself unexplained. Resolving
it needs one instrumented run with a lowered `sectionWarnThresholdMs`, not another guess.

## What this does not prove

- **No rendered observer clip exists**, so no subjective verdict has been taken. C9's
  `smooth`/`rough`/`mixed` question is still unanswered.
- **Frame timing on the i5 is unmeasured, not clean.** The orchestrator never collected
  `perf-hitches.jsonl`/`perf-sections.jsonl` (now fixed), and the i5 lane went offline
  before the existing files could be lifted. Hitch attribution above is OMEN only.
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
