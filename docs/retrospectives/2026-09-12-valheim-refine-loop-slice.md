# The refine loop: shoot, judge on the CPU, move the camera, shoot again — in one session

Date: 2026-09-12 (UTC). Host: AM4 (`homebase`, Ubuntu, RTX 5070, Valheim 1.0 build 25185596).
Repos touched: `_retired/comfy` `handoffs/valheim-camera-proof` (ComfyCameraProof **0.2.3**, commit
`44ba27f`), ComfyStewardView `tools/era-archive` (`capture_worker.py` extraction, new `refine_worker.py`),
baseline `tools/selfie-stick/frame_judge.py` (new). Receipts: [`docs/evidence/2026-09-12-era11-refine-r1/`](../evidence/2026-09-12-era11-refine-r1/)
(the journal, `refine.json`, the summary table); masters and logs on AM4 under `~/valheim-capture/era11-refine-r1/`.

## The ask

Derek, 09-11: "if analyze the shots while the camera is still there we can adapt and get a higher quality
shot that might take 5-10x as long to photograph but saves the file movement and processing, website,
fact regen scripts, etc that are downstream that we're brute forcing thru" — and "for such a tiny sample
size we should be able to simply run it on AM4's CPU". The paired same-build compare had already been
proven decisive (13.9× structure, orbit vs detail); SegFormer-b0 had been timed on AM4's CPU; then the 1.0
client ate the session and nothing of the loop was built.

## What was built

- **Mod feed mode.** `orbit-request.json` gains `feed_dir` and `feed_idle_seconds`. After the initial
  plan (header-only here) the mod keeps the loaded world and the pinned rig and runs every `*.tsv` that
  lands in the feed dir, in name order, renaming each `.done`; a `STOP` file or the idle timeout ends the
  session with the usual teardown and quit. Receipts carry a `plan` field. `RunShotPlan` became a loader
  plus `RunShotRows(rows, planName, finalize)`; `ArmRig`/`FinalizeRig` hold boom/chrome/player across
  plans. The 3-minute world load is paid once per session.
- **`refine_worker.py`** (subclass of the campaign `Worker`; `attempt()` was split into
  `prepare_scratch` / `launch_game` / `collect_logs` so both can share them). Launches once, then per
  build: feed the planned pose → judge → feed a fan of three poses (`o45` orbit +45°, `lo12` elevation
  −12°, `c75` distance ×0.75; pure trig from the receipt's `lens`/`aim`, the inverse of
  `plan_shots.camera_for`) → judge each → paired compare → if a candidate wins, one more fan around it.
  Every launch, plan, judgement and decision is a line in `refine-journal.jsonl`.
- **`frame_judge.py`**: `master_detail`'s tile math on the native 4K luma plus `frame_geometry`'s
  SegFormer mask metrics on the 1600 px plane (the corpus plane), on the CPU, weights from the local HF
  cache. Vetoes from the receipt (`skipped`, `occluded`, `still_blocked`, `pieces_near_aim 0`) and the
  image (dead, whiteout, no structure); score `subjectEdgeDensity · √structureFraction`; a structure
  guard against candidates that lose the subject. Every threshold is in one dict.

## The slice (`era11-refine-r1`, 05:23–05:35 UTC)

Sample: the eight worst-framed era11 detail frames by v1 `liveTileShare` (0.000–0.153), shot from their
v5-plan poses on the 1.0 client.

| what | measured |
|---|---|
| Launches / game pids | **1** (`Orbit auto-boot` once; `Feed: watching` → 21 × `Feed: plan … done` → `Feed: STOP`) |
| World ready | 205 s after launch |
| Plans fed / shots / masters | 21 / 47 / 47 (21 distinct run ids) |
| Cadence | 1-row plans 10–22 s (teleport), 3-row fans 22–28 s → **7–9 s per shot** |
| Judge | model load 2.4 s (cached); per 4K frame **470–590 ms model, 640–800 ms total**, `device: cpu`, 8 threads |
| Wall time | **727.8 s** launch → exit, `exit code 0`, no `Caught fatal signal`, `OnApplicationQuit` at 05:34:47 |
| Builds moved off the planned pose | 5 of 8 |

Against the campaign's own numbers: a full re-shoot costs ~3.5 min launch + 11 s/shot and then derivatives,
shuttle over the AM4 link, `frame_geometry` on the B70 and a hand-paired table before anyone knows whether
the new pose was better. Here the verdict arrives ~1 s after the shutter and the next pose is on the feed
7 s later.

## What the judge decided, and what the eye says

| build | planned | rounds | winner | inc → win score | verdict by eye |
|---|---|---|---|---|---|
| ce24e31b | detail1 | 2 | `detail1~o45~lo12` | 0.0103 → **0.0288** | **Right.** Planned frame is a shaded flat marble wall; the winner is the sun-lit corner with the veining lit and the white walkway in frame. `liveTileShare` 0.10 → 0.64. |
| 4db9cf55 | detail1 | 2 | `detail1~c75~c75` | 0.0063 → 0.0111 | **Defensible.** Sea tower in context → the wall fills the frame and the iron-grate windows are legible with light through them. More detail, less silhouette — the detail tier's stated trade. |
| 602940dd | detail1 | 2 | `detail1~lo12~lo12` | 0.0115 → 0.0182 | Not eyeballed; edge 0.013 → 0.023, sky 0.10 → 0.37. |
| d78cf0dc | detail3 | 2 | `detail3~lo12` | vetoed → 0.0032 | Sky-chained build: the planned frame is 72 % sky, 0 % structure. `lo12` finds 7.6 % structure; still 92 % sky. Elevation is the wrong lever for a build whose mass is above the aim. |
| a3e3c1fa | detail2 | 2 | `detail2~lo12` (see below) | 0.0007 → 0.0010 | **Wrong — a rule bug.** The planned frame is the camera *inside a roof* (orange planes, nothing else). `detail2~lo12~c75` is a frozen-north scene (ice shrines on snow, a dragon skeleton, a fire-lit hall) and scored 0.0092 — the guard rejected it. |
| d2b69966 | detail1 | 1 | incumbent | 0.0025 | No candidate cleared the guard. Bright/foggy frame (luma 0.72). |
| 63ffb7cd | detail2 | 1 | incumbent (vetoed) | — | 98 % sky in every pose. The aim is in the sky; no camera move fixes an aim. |
| 13f58893 | detail2 | 1 | incumbent | 0.0045 | 83 % sky, 5 % structure; candidates no better. Same disease. |

**The wall bug.** SegFormer labels the inside of a roof as ~90 % "structure" with no edges at all, so
the structure guard (`candidate.structureFraction ≥ 0.8 × incumbent's`) protected exactly the worst
frame in the set and rejected every candidate that got out of the roof. Fix, in `frame_judge.py`: a
`wall` veto — `structureFraction > 0.8 and subjectEdgeDensity < 0.003`. On this run the four wall
frames sit at 0.0007–0.0015 edge density and every real frame is ≥ 0.0048; replaying the journal under
the corrected rule flags exactly those four (all in `a3e3c1fa`) and changes exactly one decision:
`a3e3c1fa` round 1 → `detail2~c75` (out of the roof, structure 0.087, `liveTileShare` 0.46). The other
seven decisions are unchanged. This is the point of journalling every number: the rule was re-litigated
from receipts without a reshoot.

## What is settled

- The mechanism works end to end on the 1.0 client: one launch, plans fed while the rig is pinned, the
  judge on the CPU under a second per frame, decisions with receipts, clean exit on STOP.
- The paired compare inside a build is a real photographer for framing: it found the lit corner, it
  found the legible grate, and where it was wrong the journal said why within minutes.
- Sky-chained builds (aim above the mass, 3 of 8 in this worst-of sample) are not a camera problem; they
  are an aim problem. The fan needs an aim move (descend to the mass at or below the box centre, the
  planner's `grounded` idea, but decided from the frame) before elevation and distance mean anything.
- Cost: ≤ 7 shots per build at 7–9 s each ≈ 1 min per build after a 3.5 min load. Eighty-four builds
  would be ~1.5 h in one session.

## Still open

- Run the corrected rule over all 84 era11 detail builds and keep the winners as the detail tier's frames
  (the journal's `winnerFile` per build is what `import_captures` would take).
- Add an aim move to the fan for the sky-chained case; add a `luma`-based whiteout veto that fires
  earlier than 0.95 for fog (`d2b69966` at 0.72 was probably fog, not sun).
- The r2 fan only looks around the r1 winner; a candidate that lost r1 to the guard is never revisited.
- `status.completedShots` counts candidates (47 against `targetShots` 8) — cosmetic.
- Steward's 1.0 epoch: nothing here is comparable with the v1/v2 numbers except the sample choice.
