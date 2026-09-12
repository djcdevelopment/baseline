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

## Addendum, later the same day: all 47 frames read, and the rule rewritten

The first pass looked at four pairs. Reading every frame of `era11-refine-r1` against the journal (23 by
eye, the rest by numbers that turned out to sort the same way; labels in
[`eye-labels.json`](../evidence/2026-09-12-era11-refine-r1/eye-labels.json)) changed the judge.

**SegFormer's "structure" mask is wrong on this world about as often as it is right.** It called the dark
twisted tower 0 % structure in two top-down frames that are among the best of the run
(`0116_detail1~o45`, `~lo12~o45`), a stone-brick tower at 42 m 3.7 % (`0129_detail1~lo12`), the snow-
covered ice shrines 8.7 % (`0295_detail2~c75`), the inside of a roof 88 % (`0295_detail2`), and gold-veined
marble 58 % foliage. As the v1 veto/guard/score it killed three of the best frames and protected the
worst. Its sky and water fractions are fine; nothing else about it now decides anything.

**The class-free numbers already journalled separate good from bad cleanly.** GOOD frames: `liveTileShare`
0.12–0.64, `lumaMean` 0.48–0.69, `lumaStd` 0.16–0.29. Roof interiors: live 0.00, `gradMean ≤ 0.0007`.
Mistlands mist: `lumaStd` 0.02–0.05. Sky ladders: `sky ≥ 0.80`, luma ≥ 0.73. Dark close-ups: luma ≤ 0.13.
The one overlap — ice and sun glare at live 0.28, the frame Derek caught live — is separated by the
receipt alone: `pieces_near_aim = 61` against ≥ 515 for every other build.

**Three of the eight "worst" builds are linear** (a beam with a hut at one end, a ladder to a sky bucket, a
rope-ladder diagonal): the box centre is the midpoint of a line — air or water. No camera move finds
structure there; the planner has to aim at an end. A fourth sits in Mistlands mist, which a forced `Clear`
does not touch (the mist is a scene object). The worst-by-`liveTileShare` sample over-selects exactly
these; in the full tier they are a minority, but the loop has to spend nothing on them.

**Moves.** `c75` twice reaches the marble's texels (blocky veins at 24–32 m) — and texel edges are high-
gradient, so the metric *rewards* pixelation. `lo12` twice found the two best whole-tower frames at 3–8°;
28° is too high for tall builds. The occlusion ladder's `lifted+26/40m` accidentally produced the two best
top-downs, so `up20` is now a deliberate move.

### v2 (`frame_judge.py`, `refine_worker.py`, same day)

Class-free judge: vetoes `aim-off-mass` (`pieces_near_aim < 200`), `flat` (`lumaStd < 0.08`), `dark`
(`lumaMean < 0.15`), `sky` (`> 0.75`), `no-texture` (`liveTileShare < 0.10`), plus the receipt's
`skipped`/`occluded`/`still_blocked`; score `liveTileShare · gradMean`; no guard. `--replay` re-decides a
journal against the labels without a reshoot: on r1, **0 of 13 GOOD frames vetoed, all 27 BAD frames
vetoed for the expected reason**, and the four fixable builds pick a GOOD frame in round 1. The worker gates
the fan on the first frame (`needs-aim`, `needs-demist`, sky → one `re-aim` only), offers `up20`, offers
`c75` once and only while under-filled, adds `re-aim` toward the live-tile centroid, and journals
requested vs placed poses.

### `era11-refine-r2` (same 8 builds, v2): 668 s, one launch, 30 shots, exit 0

| build | needs | shots | winner | eye |
|---|---|---|---|---|
| d78cf0dc (mist) | demist | 1 | — | correctly abandoned |
| a3e3c1fa (roof) | — | 8 | `detail2~c75` (out of the roof, the ice shrines) | GOOD, round 1 |
| 63ffb7cd (sky ladder) | sky | 2 | — (one `re-aim`, still sky) | correctly abandoned |
| ce24e31b | — | 8 | `detail1~o45~o45` (lit marble alcove) | ok — r1's `~o45~lo12` corner was the better photo; the score prefers texture density |
| d2b69966 (beam over water) | aim | 1 | — | correctly abandoned, 6 shots saved |
| 4db9cf55 (sea tower) | — | 9 | `detail1~o45~o45` | GOOD |
| 13f58893 (rope ladder) | sky | 2 | `detail2~aim` — the re-aim swung onto the stone platform | better; haze remains |
| 602940dd (twisted tower) | — | 7 | `detail1~up20~up20` — the top-down of the crown | GOOD |

30 shots against r1's 47 for the same eight builds, no junk winner, and the two unfixable builds now come
back as a worklist for the planner instead of as photographs.

### What this is for

Derek, on reading the review: "we accept that we're not going to get everything great. but if we're not
wasting 30–40 % useless cuts that go through the pipeline that's still a huge gain in overall throughput."
That is the bar. The veto is the product; the winner is the bonus. The number to read from the full
84-build run is round-0 incumbents vetoed ÷ 84 — the junk rate the pipeline was carrying — and every one of
those is now fixed in-session or handed back as `needs-*` instead of shipped.

## The full run (`era11-refine-full`, 06:22–08:11 UTC): 84 builds, 601 shots, one game session

Evidence: [`docs/evidence/2026-09-12-era11-refine-full/`](../evidence/2026-09-12-era11-refine-full/)
(journal of 1,415 events, `refine.json`, summary, rejects, `cameras-era11.json`).

- **1 h 48 m wall** (6,515 s), one launch, world ready at 210 s, then 244 plans fed through the mod's feed
  dir without a relaunch; 601 frames judged on the CPU (SegFormer-b0, 8 threads, ~0.7 s each); the game's
  quit took longer than the 90 s the worker waited, so `finish()` now reads the exit code after `stop_game()`.
- **The planned pose was junk for 2 of 84** (`d2b69966` aim-off-mass → `needs-aim`, no fan spent;
  `d78cf0dc` dark → the fan found `up20~lo12` at 0.014). So the pipeline was carrying a ~2 % junk rate on
  this era's detail frames, not the 30–40 % the eight-build slice suggested — that slice was chosen for its
  hard cases. On ordinary builds the loop is an improver: **77 of 84 moved (92 %)**, all in two rounds,
  6 kept the planned pose after a full fan, 1 handed back.
- **The fan's habits:** `up20` won 89 of the 147 move tokens, `o45` 40, `aim` 9, `lo12` 6, `c75` 3.
  `up20~up20` is the single most common winner path — the loop climbs, because a steeper look-down fills
  more tiles with roof and wall texture and `liveTileShare · gradMean` rewards exactly that. Those frames
  are legible photographs, not top-downs (pitch ends around 45–66°), but the score has no composition
  term, so a frontal elevation never beats a three-quarter from above. That is the next calibration item,
  not a bug in this run.
- **Candidate vetoes** (frames the fan proposed and the judge threw out): no-texture 11, dark 5, flat 3,
  occluded 2, still-blocked 2 — 23 of 517 fan shots, each one a frame that would otherwise have been
  compared on score alone.

## What landed on the back of it (Legs A–C of the plan, same day)

The 601 receipts were the corpus the plan was waiting for. In order:

- **Poses are public artifacts (Leg A).** `import_captures.py --refine` takes each build's winner as its
  detail frame and carries `camera` (distance, elevation, bearing, fov — from the receipt's `lens`/`aim`)
  and `pose` (the absolute lens/aim/yaw/pitch) into the archive; `build_era_index.py --world-url` writes
  them to the public index; the gallery lightbox shows "camera 42 m · 20° above · bearing 225°", the
  `refined:` path, and **"open the 3D scene at this camera"** —
  `/world/scene.html?era=&build=&cameraLens=&cameraAim=&cameraFov=`. The scene resolves the build's
  bounds itself (`/api/eras` + `/api/build`), asks the package for `camera=true`, and `setExactCamera`
  places the WebGPU camera on the receipt's lens. Derek's ruling on the secrecy question the plan had
  raised: "these are end of era, public released data" — absolute coordinates are fine.
- **Pick a camera in `/world/`, get a photo back (Leg B).** "Request this shot" in the scene posts the
  fly camera to `POST /api/shot-request`; `ShotRequestLedger` converts scene-local (X-mirrored) to
  absolute, validates against the build's bounds (≤150 m outside, 4–250 m range), derives feet/yaw/pitch/
  aim in the receipts' conventions, and appends a compact `steward-shot-request/v1` line to
  `/requests/shot-requests.jsonl` (host `~/steward-world/shot-requests/`, uid 10001) plus a Discord embed.
  `refine_worker.py --prepare --requests <ledger>` turns the ledger into plans (`--rounds 0`: judge only,
  a requested pose is the photographer's choice). Live at lab release `02a3c14683be-43314ee45035`;
  the r2 winner's camera came back through the endpoint within centimetres. Two deploy lessons: the
  container's `steward` user could not write a derek-owned bind mount (500 until `chown 10001:10001`,
  now done by `deploy_world.py`), and the shared Jackson mapper pretty-prints, so the first request went
  out as 19 lines — the writer is now compact and the reader tolerant.
- **The kit (Leg C).** `tools/camera-kit/` in baseline: `Invoke-EraCapture.ps1` + `capture_kit.py`
  (stdlib, clean-room, BUSL), `make_shots.py` (winners' receipts → rows), `shots/shots-era11.tsv`
  (83 rows), `mods/NOTICE.md` + `SHA256SUMS` (DLLs not in git). The worlds are the community's own Discord
  downloads, so the kit is script + mods + shot list + links. The mod release cut and the bundle wait for
  Derek's go; the Windows proof (the i5) is not yet run.
- **Mod 0.2.4 (Leg D, first step).** `pose [name] [aimDistance]` writes the camera you are looking through
  as a TSV row + JSON line (`comfy-camera-proof-poses.jsonl`); `runclips` flies `clipplan.tsv` from the
  console. Live on AM4 (99,328 B, `fd7129be…`), proof re-stamped. Multi-waypoint clips, the in-game path
  preview, and the `/world/` path editor are still to do.

## The first requests session, and the character the game was actually playing

`era11-requests-r1` (08:35 UTC, the two ledger rows, one build) never spawned: `Loading: Done` at 171 s
as always, then `Terrain compiler could not find hmap` and `Missing location:675942648` every frame,
no `Spawned after`, the mod's `player never spawned` at 600 s. Same db, fwl and fch hashes as the run that
had just finished. The Player.log lines were the ones the full run logged at 07:54 — the game was trying
to spawn at the 84th build's last camera, `16791.4, 81.7, 2687.5`, and that position sits, byte for
byte, in `userdata/…/892970/remote/characters/questyfour.fch` — the **Steam Cloud** copy of the capture
character, which the game autosaves every 30 minutes (`Cloud Save: 52468 bytes. /characters/questyfour.fch.new`).

The decompiled 1.0.7 `SaveWithBackups` explains it: saves are grouped by file stem and the Cloud copy is
made the group's primary, so the seeded `characters_local/questyfour.fch` — the file `runtime.json` pins
and verifies — was never in the character list at all. Every AM4 session since 09-09 spawned wherever the
previous one quit; it worked until that spot was a zone whose location prefab the 1.0 client no longer
has, which `ZoneSystem` refuses to spawn, so `IsAreaReady` never came true. Steam's per-app cloud toggle
in `localconfig.vdf` did not stop the sync (Steam re-downloaded the files at the next launch), and
moving them out of `remote/` is undone the same way.

The fix is structural: the workers seed `<character>-seed.fch` (`capture_worker.seed_character()`,
ComfyStewardView `17dabef`) and ComfyCameraProof **0.2.5** (`655ede1`, `bd31cd75…`) matches
`orbit-request.character` by file stem as well as in-file name and prefers `m_fileSource == Local`,
logging `character 'Questyfour' (index 0, source Local, file questyfour-seed)`. The pinned file is now
the profile in play, and its saves land in the disposable scratch tree.

`era11-requests-r5` (09:36 UTC) then ran the two rows end to end in 286 s: world ready at 209 s, both
requested poses shot and judged (no vetoes), and the receipt's lens **0.44 m** from the requested lens,
aim 0.06 m, yaw and pitch exact — the Leg B round trip (viewer camera → ledger → shot → receipt) is
proven. Evidence: [`docs/evidence/2026-09-12-era11-requests-r5/`](../evidence/2026-09-12-era11-requests-r5/).

## Leg A checked in a browser (10:45 UTC)

The 83 refined winners are published: derivatives made on AM4 (83 masters → webp in 0.1 min),
`publish_captures` shipped 166 files / 20 MB to FX99 (`/srv/sites/valheim/era11/`, now 687 thumbs),
`build_era_index --world-url` rebuilt `index.json` from both manifests (687 photographs, 184 albums, 83 with
a pose; a refined frame sits under its planned shot's chip, so the variant row is `detail1` + `orbit1–4`,
not fourteen fan paths), and the viewer went to every era directory. Opening
`/valheim/era11/#build=002c20e689ef`, the refined frame's lightbox reads
`camera 42 m · 60° above · bearing 45° · refined: planned → up20 → up20` and its
"open the 3D scene at this camera" link lands `/world/scene.html` in fly mode, frame `gallery-exact`,
pitch −59.9°, with the big thatched house in the foreground, the long hall behind it and the small stone
structure on the left exactly where the photograph has them (at a 16:9 canvas; a narrower canvas crops
the sides since the FOV is vertical, as in Unity). Two viewer bugs fell out on the way: the refine caption
repeated the moves once per round, and every era-archive card said "NaN m tall" because those indexes
carry no height — both fixed in the viewer (`82ce74c`).

## Closing the open legs (11:00–11:20 UTC)

- **Leg B, complete.** A requests root's campaign already carries the ledger entry on each shot;
  `import_captures` now publishes `{id, at, requestedBy, note}` with the frame, the index passes it
  through under a `request` chip, and the lightbox reads "requested by Anonymous: second smoke after the
  compact-ledger release" on `ce24e31b`'s album (ComfyStewardView `1f3ac0f`; FX99 era11 = 689 photos).
  The live ledger was rewritten as one compact line per request (the container still writes to it).
- **Leg C, proven on a Windows PC.** The i5 was offline, so the proof ran on OMEN against the Steam client
  — build **25253764 (1.0.12)**, the community's own — with the kit's copy of the era11 world and three rows
  of `shots-era11.tsv` at 1920×1080: 3/3 frames in five minutes, plugins and config restored, and every
  receipt's lens, yaw and pitch **equal to AM4's to the centimetre** (`docs/evidence/2026-09-12-camera-kit-omen/`).
  Two kit changes on the way: it plays a *copy* of the character (`<name>-kit.fch`, found in
  `characters_local` or Steam's on-disk cloud folder, deleted afterwards) — the same cloud-shadow trap
  as above, and the one that would have bitten every community user with a cloud character — and
  `make_bundle.py` builds the release zip + manifest. The bundle (`camera-kit-20260912.zip`, 63 KB) and the
  mod release files (`camera-proof-v0.2.5`: DLL, manifest, SHA256SUMS, notes) are staged at
  `E:\omen\camera-kit-release\`; publishing them is the operator's call, commands in the kit README.
- **The climb, in numbers.** Winners' pitch: median 38°, 25 under 30°, 24 at 30–45°, 26 at 45–60°,
  8 at 60° or more (max 81°). Eight frames are near-top-downs; whether that is wrong is an eye
  question, so no rule changed. `refine_worker`'s status now counts builds decided (it read "601 of 84").
- Still open: Leg D past `pose`/`runclips` (multi-waypoint clips, in-game path preview, the `/world/` path
  editor, the record script) and Leg E.

