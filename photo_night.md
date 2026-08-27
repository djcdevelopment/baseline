# Night-sky photography from a build's own rooftop — handoff

Written 2026-08-25 for a cold-context pickup. Everything below is either measured
and cited, or explicitly flagged as unknown.

---

## 1. What this is trying to do

Derek's ask, in his words: *"you want to be sitting/standing on the high ground of
your house, palace. and from there when the clouds part and the moon opens up with
the stars and you see the swaying tree tops, or just the view past terrain that
shows depth in a 2d image just thru variance."*

So: put the camera **on the roof of a player build**, at human eye height, looking
**out and up** at the moon and stars, with the roofline in the bottom of the frame
and terrain receding in the middle. Three bands:

| band | content |
| --- | --- |
| sky | the moon and the star field, above the optical axis |
| middle | treetops and ridges receding into haze, below the horizon line |
| near | the roof you are standing on, along the bottom edge |

The middle band is the point. "Depth through variance" is overlapping tonal layers,
and `depth_layers.py` already measures exactly that (`layers`, `far_mass`,
`depth_span`, `edge_frame`).

**Targeting is by light count** — Derek chose this over "tallest builds" or "gallery
favourites". A night frame pays off in proportion to the lights the builder placed.

### Why this is new

Every one of the 2,509 frames in the Era 17 gallery was composed by a planner that
stands **outside** a build and aims **down** at it. `plan_shots.py` says so in its
own comment: *"The camera is always above the aim point here, so a correct pitch is
always positive."*

That is why the runbook concluded "night is the worst light" — the sixth-slot A/B
put Clear 0.90 at median **4.792** against 5.636 for the five golden slots. **That
conclusion is an artifact.** At midnight, a camera aimed at the ground photographs
dark ground. The 14 exterior night frames are murk with no sky in them.

The counter-evidence was already in the corpus: `0629_court_night` and
`0532_court_night` are interior *courtyard* vantages that happen to look up (pitch
−20.51 and −27.97) and they are the best night frames in the set — moon, ring, star
field, lit brazier, layered rock.

---

## 2. Repo state — READ THIS FIRST

> **The skyline guard exists only on branch `lane/nightsky`.**
> `C:\work\baseline\tools\selfie-stick\plan_nightsky.py` on `main` has **no
> `sky_margin`** — it is the unguarded planner that produced photographs of a
> building's own lattice. **Do not replan from the main checkout.**

| | |
| --- | --- |
| working tree | `C:\work\baseline\.claude\worktrees\lane-nightsky` |
| branch | `lane/nightsky`, commit `89a22213` (local, **not pushed, not merged**) |
| `main` baseline | `4a6184e3` — a three-lane checkpoint made by a peer session |
| shared data | `tools/selfie-stick/out` is a **directory junction** back to the real one, so `out/era17/*` is identical from either checkout |

Shooting from `main` is safe *only* because `Start-NextRun.ps1` passes `-SkipPlan`,
so nothing replans at capture time — it copies the TSV already on disk, and that TSV
came from the guarded planner. Verify before trusting: the correct
`out/era17/nightsky.tsv` has **30 data rows, 15 distinct cluster ids, and no row for
cluster 182**.

### Three concurrent lanes

Three Claude sessions were editing `C:\work\baseline` simultaneously on 2026-08-25:
night sky (this one, `baseline-b6`), storm photography (`baseline-17`), and light
colour (`baseline-75`). `baseline-75` coordinates and **owns the capture schedule —
nobody else fires Valheim.** The guard is only `Get-Process valheim` in three
scripts, which is a TOCTOU race: two sessions can both see "not running", both
launch, and each restore the operator's BepInEx config over the other.

There is **one** installed `ComfyCameraProof.dll` and all lanes edit the same
`Plugin.cs`. Whoever builds last wins. **Announce before installing a DLL.**

---

## 3. The measurements

### 3.1 The celestial arc — exact

`comfyproof_sky` (added this session) walks `EnvMan`'s directional light through 41
times of day and dumps its vector, colour and intensity. Result: **one arc**, and
colour says which body is on it.

| | colour | intensity | window |
| --- | --- | --- | --- |
| sun | 1.00, 0.87, 0.64 | 1.50 | t 0.25 → 0.75 |
| moon | 0.41, 0.49, 0.68 | 1.20 | t 0.75 → midnight → 0.25 |

At t=0.25 and t=0.75 intensity is 0 and colour is black — the handovers. Both bodies
rise **due east at 0°**, peak **due south at 45°**, set **due west**.

Closed form, reproducing **all 39 lit samples to 0.001°**:

```
theta(t) = 180 * frac((t - rise) / 0.5)        rise = 0.25 sun, 0.75 moon
alt(t)   = asin(K * sin theta)                 K = sin 45 = 0.70711
az(t)    = atan2(cos theta, -K * sin theta)
```

Implemented as `plan_nightsky.body_direction()`, with the dump samples pinned as a
test fixture (`CelestialArcTests`) so a later "simplification" fails against the game
rather than against an opinion.

**Independent check:** it puts the sun at azimuth **239.7°** at t=0.64. The runbook
already had **235° ± 25** from regressing sky-strip luminance on camera yaw over
seven capture runs. Two instruments — one from the engine, one from pixels — inside
the error bar.

Dump lives at `out/era17/sky.json`.

### 3.2 Two negative findings

**EnvMan has no moon object and no phase field.** The dump enumerated every field and
every `Get*`/`Is*` method matching `moon|phase|sun` and found only
`m_sunHorizonTransition{H,L}`, `m_sunFogColor`, `GetSunDirection`. All 61 renderers in
the sky hierarchy are cloud, water and fog — the disc is drawn by the sky material.

Consequence: **moon phase cannot be set for a shot.** It varies by in-game day (the
two frames above are both t=0.90; one is near-full, one a thin crescent). Forcing a
phase would need the game day advanced, which mutates the save. Don't.

**The rendered disc is NOT where the light comes from.** Limb fits from two runs at
t=0.90, cameras 30° apart in yaw:

| frame | camera yaw | fitted disc azimuth |
| --- | --- | --- |
| `20260822-134535_0275_toproom_night` | 67.5 | 77.0 |
| `20260822-154944_0629_court_night` | 98.3 | 79.6 |

World-azimuth spread **19°** against camera-relative spread **51°** — that ratio is
what says it is a fixed body and not an artifact of the camera. Meanwhile the
directional light at t=0.90 is at azimuth **134.2°**.

- Use **134.2** for moonlight *on surfaces* (back-lighting, colour).
- Use **~78** to place the *disc* in frame.
- **Altitude and disc radius are NOT recoverable from limb fitting** — the same body
  measured 41.3° and 63.7° altitude, because a short arc of a huge circle trades
  centre distance against radius. `--rho` therefore defaults to 0 (aim at the centre)
  and `sky_check.py` reports the residual so a real value can be measured.

### 3.3 Camera constants — from receipts, not assumed

| | value | source |
| --- | --- | --- |
| vertical FOV | **65°** | `"fov": 65` on every receipt |
| horizontal FOV | 97.1° | 65° at 16:9 |
| lens offset above placed point | **1.65 m** | `lens_offset_m` 1.72–2.04; planned y 60.7 → lens y 62.353 |

That 1.65 m matters: the mod places the **player**, and on a roof it is the entire
margin. Plan the stance at the roof surface and let the lens ride up to it.

### 3.4 The light census

`scan_features.py`'s light vocabulary was broken. `FIRES_EXACT` held four names;
`FIRES_PREFIX` held two prefixes and counted **nothing** — `expand_pattern_sets()`
used it only to keep torches out of the wall set, and `feature_rows()` emitted
`FIRES_EXACT` alone. **80,010 placed torches and braziers matched a pattern and were
dropped on the floor.**

Hand-audited against Era 17's placed `BUILDING` rows, sorted by count, accepted by eye:

| | |
| --- | --- |
| vocabulary | **43 prefabs** (`scan_features.LIGHTS`, name → weight) |
| placed lights in Era 17 | **173,541** |
| assigned to a cluster | **150,553** |
| structures with none | **456 of 2,204** |
| what the old vocabulary reached | **11,225 — 6.5%** |

Weights: 3 open flame, 2 torch/lantern, 1 small emitter. Exclusions are documented
in-source with reasons, because the next person to sweep for `torch` or `fire` will
match all of them: unlit variants (`CastleKit_groundtorch_unlit`), creature effects
(`DvergerMageFire`), crafting stations whose glow is incidental (`forge*`, `smelter`,
`charcoal_kiln`, `piece_oven`), and `crystal_wall_1x1` (translucent, not emissive;
already a window).

> **Caution:** the fire table earlier in the runbook (`Candle_resin` 34,988,
> `MountainKit_brazier` 34,015) counts **all ZDOs including dungeon-generated props**.
> Under `category='BUILDING'` those are 2,511 and 3,799. The dungeon population is
> real and is nobody's build.

**A second bug fell out of the same audit:** the feature join in `scan_features.py`
had **no category filter at all** — only the *count* queries did, which is why the
existing `test_the_scan_only_ever_reads_placed_pieces` passed while the join was wide
open. Any build whose padded box touched a Dvergr tower inherited its props. Fixed;
the test now asserts against the join itself.

A peer lane (`baseline-75`) built `LIGHT_HUE`/`hue_of()` on top of this dict. Split by
weight: warm 48.4%, green 22.5%, cyan 17.1%, blue 8.4%, purple 3.6%. **This world is
lit more by coloured flame than by fire.** `LIGHTS` is this lane's; `LIGHT_HUE` is
theirs; they compose without either altering the other.

---

## 4. The equations

Symbols: `S` stance (roof surface), `h_eye` lens height above it (1.65 standing / 1.0
seated), `R` roof half-extent along the look bearing, `e` optical-axis elevation.
Screen mapping is pinhole: a point `Δ` above the axis lands at fractional frame height
`v = tan(Δ) / tan(fov_v/2)`.

```
alt_target = alt_body - rho                          rho = 0 until the disc is measured
e          = alt_target - atan(f_sky * tan(fov_v/2)) f_sky default 0.45
pitch      = -e                                      Unity convention: + looks down

roofline stays in frame     <=>  e + atan(h_eye / R) <= fov_v / 2
parapet on the lower third  <=>  e + atan(h_eye / R) =  20.9 deg
ideal roof ahead            R*   = h_eye / tan(20.9 - e)
step back from the parapet  s    = clamp(R* - R, 0, reverse_reach - 2)

bearing freedom             |yaw - az_body| < rho + fov_h/2
aim point handed to the mod A    = lens + 25 m along the optical axis
```

### Why the aim point is 25 m up the sight line

This is the trick that lets the whole thing run on the mod **as installed, with no
capture-path change.** The runner uses `aim` for three gates and **none of them is
framing**:

1. `PiecesNear(aim, 60)` — a zero count means "world never loaded" and the shot is
   dropped. A point 25 m away keeps the build well inside that sphere.
2. `IsOccluded(lens, aim)` — pointing into open sky means recovery never fires and
   never teleports the camera off the roof.
3. `LookAngles(lens, aim)` — if recovery *does* fire, it reproduces the planned yaw
   and pitch exactly.

### When you can shoot

Two constraints close from opposite sides and between them they pick the hour:

- The camera only looks **up** while the body is above the sky-fraction offset (16° at
  `f_sky` 0.45) → **t past ~0.81 and before ~0.19**.
- The roofline only survives while `e + atan(h_eye/R) <= 32.5` → at 20 m of roof the
  moon can be 43° up, at 8 m only 37°, at 4 m it must be under 25°.

A build that fails is a **scheduling problem, not a dead end** — the same roof works an
hour earlier.

### Finding the stance

Geometry, deliberately **not** a floor-prefab vocabulary (the seats and the lights were
both written from the crafting UI against a world built from the prefab table, and both
were wrong):

1. Bin pieces into 2 m columns; `top(x,z)` = max y in the column.
2. A **platform** is a 3×3 block whose column tops sit within 1.0 m (a 45° roof climbs
   2 m per cell and fails on the first comparison; a terrace cannot fail).
3. Rank by height, then by **edge exposure** — the count of the surrounding ring that is
   ≥1.5 m lower or empty. That parapet is what puts a near layer against the border,
   which is what `edge_frame` rewards.
4. Emit **up to five well-separated candidates**, each with its own reach and skyline
   map. The highest flat block is not reliably the one with sky over it.

---

## 5. How to execute

Working directory: `C:\work\baseline\.claude\worktrees\lane-nightsky\tools\selfie-stick`

```powershell
# 0. Measure the sky (only needed once per game version). Launches Valheim,
#    dumps, quits. ~3 min. Writes out/era17/sky.json.
.\Invoke-SkyDump.ps1 -Out .\out\era17\sky.json

# 1. Light census + rooftop stances. Read-only against the DuckDB cache. ~3 min.
python scan_rooftops.py --db "E:\omen\steward-era17\out\world-cache.duckdb" `
  --world-id ComfyEra17 --clusters out/era17/clusters.json `
  --out out/era17/rooftops.json --top 24

# 2. Plan. --body-azimuth 78 frames the DISC; omit it to frame the LIGHT (134.2).
python plan_nightsky.py --rooftops out/era17/rooftops.json `
  --clusters out/era17/clusters.json --names out/era17/cluster-names.json `
  --out out/era17/nightsky.json --body-azimuth 78

# 3. Shoot. HAND THIS TO baseline-75 — it owns the capture schedule.
.\Start-NextRun.ps1 -Run nightsky

# 4. Verdict. NOT the aesthetic score.
python sky_check.py --plan out/era17/nightsky.json --run <run-id> `
  --depth out/era17/depth.json --out out/era17/skycheck.json
```

Fixed context: world `ComfyEra17`, character `tugcorp`, snapshot **107**, cache
`E:\omen\steward-era17\out\world-cache.duckdb`. Capture rate ~11.5 s/frame.
Receipts: `...\Valheim\BepInEx\config\shotplan-receipts.jsonl`. Originals:
`...\BepInEx\config\comfy-orbit-captures\<run-id>\`.

### What counts as it working

**Never the aesthetic head.** Measured over the 2,181-frame corpus it moves 0.62 on
time/weather and ~0 on everything else — an exposure meter and a veto, not a critic —
and it marks dark frames down on principle.

| check | bar |
| --- | --- |
| `clearance == "planned"` | every row — the camera stayed on the roof |
| disc found | **> 0 of 30** (the first run scored 0 of 16) |
| residual vs planned bearing | small = the equation validating itself |
| `luma_mean` | between 20 (black floor: a sky-less night frame measured 6–8) and 186 (fog ceiling); gallery median 96 |
| star count | how you tell which cloud re-roll won |
| `layers`, `edge_frame` | "depth through variance", stated as a measurement |

A 0-of-N result is **a result**. Do not re-run on the hypothesis that maybe it passes.
The discriminator is built in: 0 found with **high** star counts and good luma means
clear sky and a wrong bearing; 0 found with **low** star counts means cloud. Those want
different answers.

---

## 6. What happened, and what it cost

### Run `20260825-072915` — mechanically flawless, photographically empty

16 frames over 8 builds. Every receipt: `clearance: "planned"`, `occluded: false`,
`pieces_near_aim` 1,483–30,930. **The moon is in zero of them.** Four frames of cluster
182 — "Black Tower", the most-lit build in the world at 1,869 weighted lights — are a
photograph of its own diamond lattice.

One frame (`0310_moon1`, luma 70.7, 220 stars) is genuinely beautiful — lantern-laden
canopy, glowing arches, wet stone. It still has no sky in it.

Three causes:

**(a) The mod's occlusion check cannot see player builds.** `IsOccluded` masks
`terrain`, `static_solid` and `Default`. Placed pieces are on the **`piece`** layer,
which `PiecesNear` uses and the raycast does not. For an orbit at 120 m the blockers are
trees and hillsides so it has always worked; for a camera inside its own build it is
blind and returns `false` with the lens against masonry.

> **Deliberately NOT fixed.** Adding `piece` to that mask would make every orbit report
> its own subject as an obstruction and fire lift-and-swing across three lanes. That is
> a re-baseline, not a one-word change. Scope agreed with `baseline-75`: storm-1a/1b
> unaffected (tree/hillside blockers are covered); hearth-1 affected (324 interior
> frames); and the runbook's "the runner threw out half as many frames as unusable"
> (batch B vs E) needs qualifying — its conclusion survives on the within-batch `los`
> numbers, which were always the clean evidence.

**(b) A ZDO's position is the piece's PIVOT, not the top of its mesh.** A 2 m wall
pivoting at 67 reaches 69; a column-top model reading 67 puts the eye inside masonry and
calls it sky. On cluster 182, grausten pillar arches pivot **1.35 m below the lens** and
fill the frame. Now carries a **2 m piece-top allowance**.

**(c) The skyline check was a single ray and threaded the gaps between pillars.** It
reported **0.0° due east** from inside a 22,393-piece tower while **1,449 piece pivots
sat above the eye** in that corridor. The frame is 97° wide. Now a **±15° fan at 5°
steps**, taking the worst — guarding the middle of the frame where the sky band lives
and tolerating the edges (a wall at the border is a near layer; a wall up the middle is
a wall).

With all three in, cluster 182 reads **18.1°** of its own masonry in its clearest
direction against a planned 18.9° axis, and is dropped. Of 21 scanned builds, **5 drop
and 15 plan**, each drop reported with a reason.

---

## 7. Lessons

1. **Guard the plan, not the pixels.** This is now the *third* time this project has
   landed on it from a different instrument: `--max-los` caught sight lines that
   `depth_score` endorsed; `depth_score` read 0.58 on a photograph of a stone wall; and
   now `IsOccluded` reports clear against masonry. A geometric fact computed from the
   world's own positions beats anything inferred from the render.

2. **A perfect receipt is not a photograph.** 16/16 `clearance=planned`,
   `occluded=false`, and not one frame of the subject. Acceptance criteria have to
   measure the thing you wanted, not the thing the machine can easily report.

3. **ZDO positions are pivots.** Anything reasoning about heights, clearances or
   silhouettes from raw ZDO y is short by up to a piece height.

4. **Prefab vocabularies written from the crafting UI are wrong in this world.** Seats
   were, fires were. The world builds from the prefab table. Enumerate
   `category='BUILDING'` names by placement count and audit by eye. A pattern sweep is
   not a substitute: `fire` matches `DvergerMageFire`, `torch` matches
   `*_groundtorch_unlit`, and a previous `-table-` sweep swallowed `UnstableLavaRock`.

5. **A negative finding is worth as much as a positive one.** "EnvMan has no moon object
   and no phase field" stops someone spending a day trying to set a phase for a shot.

6. **Cloud position is a re-roll, not a setting.** `plan_shots.py` had already measured
   14 shots at identical camera and light differing by up to 50.8 mean luma from sky
   drift. "When the clouds part" is achieved by repeats + selection — and repeats must
   carry **distinct variant names**, because the index supersedes on
   `(cluster, variant, environment, time_of_day)` and same-named repeats retire each
   other. That is how 150 golden frames were quietly replaced on 2026-08-24.

7. **Give new frame types their own gallery `perspective`.** The gallery ranks within
   perspective; without a `rooftop` bucket every night frame loses a raw-score fight
   with a golden-hour aerial by construction.

### Environment gotchas that cost real time here

- **Long bash heredocs get truncated** by this harness (`unexpected EOF while looking
  for matching '`). Anything over ~100 lines: write it with the file tool, or splice
  from a scratchpad file.
- **The worktree is checked out CRLF while hand-copied files are LF.** A multi-line
  Python search string written with `\n` silently matches nothing. There is a helper at
  `<scratchpad>/patch.py` that normalises in memory and restores the original
  convention on write.
- **`shotplan-receipts.jsonl` carries a UTF-8 BOM.** `json.loads` on line 1 throws
  unless the reader opens with `encoding="utf-8-sig"`.
- **Never `2>&1` a native exe in PowerShell 5.1** — it wraps stderr lines in
  ErrorRecords and sets `$?` false on a successful exit.

---

## 8. Files

On `lane/nightsky` @ `89a22213`:

| file | what |
| --- | --- |
| `tools/selfie-stick/scan_rooftops.py` | **new** — light census + rooftop stances, reach and skyline maps |
| `tools/selfie-stick/plan_nightsky.py` | **new** — the equations; emits the 14-column TSV, `mode=rooftop` |
| `tools/selfie-stick/sky_check.py` | **new** — disc fit, bearing residual, star count, luma band |
| `tools/selfie-stick/Invoke-SkyDump.ps1` | **new** — unattended sky measurement |
| `tools/selfie-stick/scan_features.py` | `LIGHTS` (43 prefabs), `lights` count, `BUILDING` filter on the feature join |
| `tools/selfie-stick/plan_interiors.py` | `validate_tsv` gained `mode=`; default unchanged |
| `tools/selfie-stick/build_valheim_index.py` | `perspective_of` gained a `rooftop` bucket for `moon*` |
| `tools/selfie-stick/Start-NextRun.ps1` | one queue row, `nightsky` |
| `tests/test_selfie_stick.py` | `CelestialArcTests`, `NightSkyPlanTests`, `LightVocabularyTests` |
| `docs/internal/RUNBOOK-...-2026-08-22.md` | night-lane section appended |

Mod source is **outside baseline**:
`C:\work\_retired\comfy\handoffs\valheim-camera-proof\Plugin.cs`, built and installed
with `build-and-install.ps1`. The installed DLL was byte-identical to that tree's build
output before this session, so it is genuinely the source of record despite living in an
archive. Additions this session: the `comfyproof_sky` console command and
`ReadSkyTimes()`, so `orbit-request.json` can carry `"sky_times": [...]` and the mod
runs a measurement pass instead of a shot plan. Neither changes capture behaviour.
A peer lane's `WidenLightLod` is in the same file; both are in the installed binary and
**neither lane has a clean before/after for the other's change.**

`python -m pytest tests/test_selfie_stick.py -q` → **66 passed**.

---

## 9. Open

1. **Nothing has photographed the sky yet.** The guard is in, the 30-shot plan is
   validated and handed to `baseline-75`. That run is the only thing that closes this.
2. **`rho` is unmeasured.** Defaults to 0 (aim at the body's centre). `sky_check.py`
   reports the residual, which is both the equation validating itself and the only route
   to a real value.
3. **The disc's ephemeris is one data point.** Azimuth ~78 is measured only at t=0.90,
   from two frames. Its altitude and radius are not reliably measurable by limb fitting.
   If the disc must be placed precisely at other times, that needs a deliberate image
   survey — a fixed stance sweeping time with a fixed upward aim.
4. **Terrain is unguarded at plan time.** Valheim generates it from the seed and no
   offline heightmap exists. Terrain *is* in the mod's raycast mask, so the two checks
   cover each other: pieces and trees here, hillsides there.
5. **`environment=Clear` is a hardcoded assumption**, on the reasoning that it is the
   only sky with stars and a visible moon. **Untested.** The game ships **39
   environments** including three unused `Twilight_*` ones and a `nofogts`. A peer lane
   is walking `EnvSetup` for all 39; the field that matters here is whatever drives the
   star field.
6. **`sky_check.py` is deliberately conservative** and refuses rather than fabricates.
   Validated against known frames it found the one unambiguous disc and rejected both the
   ring feature and a water reflection that an earlier naive sweep had reported as a moon
   at −21.6° altitude — below the horizon. Expect false negatives, not false positives.
