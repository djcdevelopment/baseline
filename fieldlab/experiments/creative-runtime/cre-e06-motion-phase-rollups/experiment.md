# CRE-E06 - Where does client motion time and amplification accumulate?

Status: instrumentation and analyzer implemented; live result pending

## Goal

Measure the current Lumberjacks motion path by phase without writing a row per
Unity frame or changing gameplay authority.

## Objective

Use cumulative, privacy-safe counters already carried by
`telemetry-client.jsonl` and Companion captures to separate:

```text
arrival -> Update drain/coalesce -> object bind -> LateUpdate presentation
```

The same capture also records target error and displacement observed between two
Lumberjacks writes. That displacement is a detector for another transform writer
or physics step, not proof that native Valheim performed the write.

## Hypotheses

1. Arrival spacing remains close to the configured source rate during straight
   movement, while bursts appear as larger drain batches or same-ZDO coalescing.
2. Apply work grows with render frames times fresh remote entities, so
   `applied / received` is greater than one at render rates above send rate.
3. Repeated object binding is measurable but may not be the dominant part of
   `LateUpdate`.
4. If the visible glide/teleport behavior includes two transform writers,
   interframe displacement over 50 mm will occur while Lumberjacks apply is
   active. This does not identify the other writer.
5. Stale remote entries continue to be scanned after their freshness window,
   making stale-visit growth a useful bound on retained presentation work.

## Predicted outcome

For one visible remote player at the current 20 Hz source default:

| Signal | Prediction |
|---|---|
| receive interval mean | near 50 ms absent burst/loss |
| drained samples | approximately received samples, allowing capture edges |
| applies/received | approximately render FPS / 20 while snapshots stay fresh |
| bind calls | one per fresh remote visit in the current implementation |
| coalesced in drain | zero at steady state; rises when multiple samples arrive before one `Update` |
| interframe displacement | near zero if no other phase writes the transform; nonzero is attribution work, not a verdict |

## Measurement contract

Counters are cumulative in the mod and sampled at the existing telemetry cadence.
The analyzer computes restart-aware deltas between rows. Counts and totals support
capture-local means. Maxima are process-lifetime values and are reported as such;
only a maximum that increases during the capture is known to have changed in that
window.

No player identity, ZDO identity, position, velocity, or raw packet is added to the
rollup. Receive intervals use a monotonic local clock and therefore describe arrival
spacing, not one-way latency.

## Setup and procedure

The operator only needs the intended clients joined and ready. The preferred
workbench path drives capture, role selection, allow-listed movement, bundle
collection, and both client summaries:

```powershell
.\tools\i5\Start-TwoClientFeelWindow.ps1 `
  -Pattern straight_north `
  -MotionDurationSeconds 10 `
  -ApplyClient omen `
  -RoleReversal `
  -Label cre-e06 `
  -CollectPhaseSummaries
```

For an OMEN-only telemetry baseline without movement orchestration:

```powershell
.\fieldlab\scripts\Invoke-MotionPhaseCapture.ps1 `
  -DurationSeconds 60 `
  -IntervalSeconds 1 `
  -Label cre-e06-straight-run
```

The command:

1. starts the existing Companion transport-truth capture;
2. downloads `samples.jsonl` from the local Companion;
3. emits `motion-phase-summary.json`;
4. leaves raw evidence under `fieldlab/runs/motion-phase/<timestamp>/`.

To re-analyze retained JSONL without contacting Companion:

```powershell
.\fieldlab\scripts\Summarize-MotionPhaseCapture.ps1 `
  -SamplesPath <capture>\samples.jsonl `
  -OutputPath <capture>\motion-phase-summary.json
```

## Limits

- Sampling cannot reconstruct individual frame order.
- Process-lifetime maxima can predate the capture.
- Stopwatch measurements add small probe cost to receive, bind, and `LateUpdate`.
- Interframe displacement can include native presentation, physics, another mod,
  or an engine phase; it is intentionally source-agnostic.
- Live visual quality still requires a short human observation after synthetic and
  autonomous checks pass.

## Assumptions

`writeTelemetryLogs` is enabled, Companion can read the local Valheim telemetry
file, and at least two capture samples include `local_motion`.

## Known limitations and ADRs

This slice observes the existing chase-latest client overlay. It does not suppress
native Valheim movement, add velocity extrapolation, move critical mutations to
Channel 2, or authorize broader M7 network authority.

## Results

Implementation validation uses a three-row fixture to prove cumulative deltas,
derived means, lifetime-max labeling, and JSON shape. A real two-client capture is
still required for timing and visual interpretation.

## What changed in our understanding

The existing JSONL and Companion capture contracts already provide the durable
boundary needed for phase evidence. No new observer service or frame log is needed.
The remaining live step is a bounded capture, not another instrumentation build.

## Next experiment

Replay captured arrival timing against the current chase-latest presentation and a
two-snapshot interpolation candidate. Only then choose whether to cache object
binding, retire stale entries, or change presentation ownership.
