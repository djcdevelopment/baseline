# Photographing light in Valheim — objective, method, data, and what we learned

**Status as of 2026-08-26.** Working notes for the "light colour across conditions" lane
of the selfie-stick gallery project. Written for an agent picking this up cold.

Read [`docs/internal/RUNBOOK-selfie-stick-era17-series-2026-08-22.md`](docs/internal/RUNBOOK-selfie-stick-era17-series-2026-08-22.md)
for the full chronological record — it is ~1,500 lines and it is the authority. This file
is the orientation layer: what we are trying to do, what is already answered, what the
traps are, and how to run the next thing without repeating a mistake.

---

## 1. What we are trying to accomplish

The gallery photographs **what people built** in a Valheim world (Era 17: 2,204
structures, 1,025 in-world). The open question this lane owns:

> Where is the limit at which a light **source** — a hearth, a torch, a brazier — stops
> being distinguishable from the ambient light of the weather and time of day? And does
> being inside or outside a structure change that?

Practical goal: choose the conditions that produce the best photographs, especially the
"warm and cosy indoors while a storm is outside" shot, and the approach-from-outside shot
toward a lit entrance.

**The constraint that shapes everything:** the project's aesthetic scorer (a LAION head)
reads **global tone and nothing else**. Measured across 2,181 frames it moves 0.62 on
time-and-weather and ~0 on anything structural. It is an exposure meter and a veto, not a
critic, and it marks dark frames down on principle. **Never judge a lighting change with
it.** That is why this lane exists: it needed its own instrument.

---

## 2. Where things stand

| | |
| --- | --- |
| Gallery | 2,633 frames, 17 runs, `tools/selfie-stick/out/era17/gallery/` |
| Colour measured | 2,645 frames in `out/era17/color.json` |
| Light dump | 387 prefabs + 39 environments in `out/era17/lights.json` |
| Tests | 64 passing (`pytest tests/test_selfie_stick.py`) |
| Branches | `main` current; `lane/storm` and `lane/nightsky` unmerged |

Ten commits landed 2026-08-25, `4a6184e3` … `04556553`.

---

## 3. The answer so far

### There are two separations and they do not peak together

Measured **within-quad**: 153 matched (cluster, vantage) quads = 612 frames where camera,
build and framing are identical and only the light changes.

- **`warm_lift`** (warm-pixel value minus frame value) is *brightness* separation — does
  the warm thing glow.
- **`opponent_gap`** ((R−B) of the warm lobe minus (R−B) of the cool lobe) is *colour*
  separation — are the two lights actually different colours.

| where | condition | warm % | cool % | lift | opp gap | warm hex | cool hex |
| --- | --- | --- | --- | --- | --- | --- | --- |
| inside | sunrise | 18.3 | 21.8 | 0.116 | 85.3 | `#765041` | `#182E36` |
| inside | **storm** | 16.6 | 23.9 | **0.122** | 78.2 | `#754F40` | `#1F3538` |
| inside | sunset | 16.8 | 23.0 | **0.079** | 87.6 | `#6E4A3C` | `#182E3D` |
| inside | night | 14.6 | **11.9** | 0.097 | 76.7 | `#674132` | `#111E26` |
| outside | sunrise | 8.7 | 35.4 | 0.099 | 96.2 | `#725443` | `#1B4053` |
| outside | storm | 5.0 | 33.1 | 0.117 | 74.5 | `#6E5440` | `#21393F` |
| outside | sunset | 5.9 | 46.7 | **0.078** | **104.9** | `#6D4D3E` | `#1B3B4F` |
| outside | night | 4.4 | 21.9 | **0.148** | 78.1 | `#634232` | `#0E202C` |
| drone | Clear 0.64 | 4.1 | 48.5 | 0.119 | **121.2** | `#A38B6B` | `#2C6171` |
| drone | Clear 0.32 | 2.1 | 61.2 | 0.134 | 120.8 | `#A1896A` | `#25596A` |
| drone | Clear 0.71 | **12.7** | 60.3 | **0.170** | 106.9 | `#856457` | `#153F53` |
| drone | Misty 0.66 | 1.3 | 6.2 | **0.041** | 90.2 | `#C1AE8F` | `#708C9D` |

**Findings:**

1. **Sunset is the limit** — lift bottoms at 0.079 inside and 0.078 outside. Ambient and
   fire share a hue, so the source has nothing to stand out from.
2. **Brightness separation peaks in the dark** (night 0.148, storm 0.122); **colour
   separation peaks in clear daylight** (121). You cannot maximise both.
3. **Storm indoors is the compromise** — near-max lift with a real cold field still present.
4. **Inside/outside is a bigger lever than weather** — warm mass runs ~3× indoors in
   *every* condition. Being under a roof is what puts a warm source and a cold field in
   one frame.
5. **Time 0.71 is the floor indoors (0.079) and near the best outdoors (0.170).** Indoors a
   low sun floods the room and the fire cannot compete; outdoors it rakes a warm facade
   against a 60% blue sky.
6. **Misty is the worst light on every axis** — lift 0.041, warm 1.3%, cool 6.2%, blown out
   at scene_v 0.735.

### The warm lobe is material, not light

Across five times of day, the directional light's own R−B swings from −68 to +160 while
the **warm lobe barely moves (R−B 47→55)**. Within-build across four conditions its median
spread is 8.0 against the cool lobe's 14.0. The warm lobe is wood, thatch and firelit
surface — whose colour does not change when the sun does. **All of `opponent_gap` comes
from the cool lobe**, i.e. from ambient/sky. Any predictor must be built on ambient
colour, not sun colour.

### Cool-lobe green/blue identifies which body is lighting the frame

| | g/b |
| --- | --- |
| engine moon (from EnvMan dump, t=0.90) | 0.722 |
| measured night cool lobe (n=164) | **0.756** |
| measured day cool lobe (n=1643) | 0.864 |

Two independent instruments 0.034 apart. Useful because **cyan Dvergr lanterns** (29,910
placed) land in the same cool lobe at g/b ≈ 1.0 — so this ratio separates "moonlit" from
"lit by its own cool lanterns" per frame.

---

## 4. Tools and data

### `tools/selfie-stick/color_layers.py` — this lane's instrument

PIL + numpy only. **No model, no GPU, no venv** (unlike `score_images.py` and
`depth_layers.py`, which need `C:\work\omen-perception\venv`). ~25 frames/s, full corpus
in ~100 s.

```bash
python color_layers.py --images out/era17/gallery/large --out out/era17/color.json
```

Incremental by default (skips measured frames); `--force` to redo, `--prefix <runid>` to
scope. Writes `{image_id: {metrics}}`.

**Metrics:** `scene_v`, `warm_frac`, `cool_frac`, `warm_hex`, `cool_hex`, `warm_v`,
`cool_v`, `warm_lift`, `opponent_gap`, `bright_warm_frac`, `bright_warm_hex`,
`ambient_hex`, `ambient_v`, `lit_frac`, `black`.

**Read the module docstring before extending it.** It records that a per-frame *light
source detector* was built twice and cut both times — it fires on sunlit grass and
correlates r = 0.02–0.09 with a build's actual warm-light count. `bright_warm_frac`
survives as a **description** (warm AND above absolute value 0.45), explicitly not a
detector. That distinction matters: for a fires-on/off comparison at fixed camera and sky
it is the *right* metric, because a lit hearth at 3 m is warm and bright while a table
0.35 m from the lens is warm and not bright.

### Data files (all under `tools/selfie-stick/out/era17/`, all gitignored)

`out/` carries real coordinates and creator ids — **it is gitignored and must stay so.**
Worktrees reach it through a directory junction (see §5).

| file | what |
| --- | --- |
| `gallery/index.json` | one row per frame: `id, run, variant, environment, time_of_day, cluster_id, perspective, aesthetic, fog, occluded, …` |
| `color.json` | this lane's metrics, keyed by `image_id` |
| `depth.json` | `depth_score, far_mass, center_block, layers, luma_mean, luma_spread` |
| `aesthetic.json` | LAION score |
| `lights.json` | **387 light prefabs + 39 environments** — see §6 |
| `sky.json` | EnvMan directional light at 41 times of day |
| `clusters.json` | frozen structure ids + bounding boxes — **the join key, never regenerate** |
| `features.json` | per-build furniture/lights/floor bands/roof grid |
| `capture-runs.json` | accepted run ids |
| `run-provenance-*.json` | DLL md5 + mod sha per run |

Raw PNGs live **outside the repo**:
`C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\config\comfy-orbit-captures\<runid>\`
Receipts (one JSON per shot): `…\BepInEx\config\shotplan-receipts.jsonl`

### The shared light vocabulary

`scan_features.py` holds `LIGHTS` (43 prefabs → weight, owned by the night-sky lane) and
`LIGHT_HUE` (this lane — what each light *emits*). `hue_of(name)` defaults to `warm`.

**Era 17 is 51.6% coloured light by weight** — warm 48.4%, green 22.5%, cyan 17.1%, blue
8.4%, purple 3.6%. This world is lit more by coloured flame than by fire. Per build the
split varies wildly (one build is 1,560 cool against 339 warm).

---

## 5. How to execute a capture

### Serialisation

Only one Valheim can run. The only in-script guard is `Get-Process valheim`, which is a
**TOCTOU race** — two sessions can both see "not running" and both launch, each restoring
the other's BepInEx config. **One session owns the schedule and nobody else fires.**

### Pre-flight — all four, every time

1. **Valheim is not running.**
2. **No index rebuild in flight.** `Invoke-OrbitCapture` step 5 re-derives *every* web
   image (~2,600, ~15 min). Two rebuilds collide. Check for `.webp` writes in the last 45 s.
3. **Nothing is reading the LIVE world file.** Not "nothing is reading `worlds_local`" —
   backups live there too and copying from a frozen snapshot is the *fix*. Check command
   lines: `Get-CimInstance Win32_Process -Filter "Name='scp.exe'"`.
4. **DLL provenance.** Verify the installed `ComfyCameraProof.dll` md5 and that
   `Plugin.cs` is clean at a known sha in `C:\work\_retired\comfy\handoffs\valheim-camera-proof\`.
   Record it in `run-provenance-<run>.json`.

Then **check the frames afterwards** with `check_overlay.py` (§7).

### Firing

```powershell
cd C:\work\baseline\tools\selfie-stick
.\Start-NextRun.ps1                      # shows the queue
.\Start-NextRun.ps1 -Run <name>          # fires it, then scores + rebuilds
.\Start-NextRun.ps1 -Run <name> -SkipFollowUp   # capture only
```

Use `-SkipFollowUp` for back-to-back runs and do **one** combined scoring pass at the end
— every metric is per-frame and keyed by `image_id`, so it costs nothing analytically and
saves a whole index rebuild. The tail is longer than the capture.

Queue rows live in the `$queue` array in `Start-NextRun.ps1`. Adding a run is a row.

### The light dump (no screenshots, ~2 min)

Write `BepInEx/config/orbit-request.json`:

```json
{"world":"ComfyEra17","character":"tugcorp","quit_when_done":true,"light_dump":true}
```

then launch `steam.exe -applaunch 892970 -console`, wait for
`BepInEx/config/comfy-camera-proof-lights.json`. **Gate on the file being newer than
launch time**, not on its existence — a stale dump reads as a successful run that never
happened. Park `comfy-network-sense/native-autotest-request.json` first or NetworkSense
fights for the menu. Console equivalent: `comfyproof_lights`.

### Settings

- `settleSeconds` in `BepInEx/config/com.comfy.camera-proof.cfg`. **BepInEx rewrites that
  file from memory on shutdown — edit only with the game closed.**
- **`settleSeconds = 3` is adopted**: zero occlusion rejects in both halves of a 90-frame
  A/B, median frame gap 7.24 s against 10.24 s, **29% faster**. Currently sitting at 6;
  set it to 3.

---

## 6. What the light dump says

`out/era17/lights.json` — 387 prefabs, 39 environments, from `ComfyCameraProof` at
`19fd460`.

### Only one of our 43 lights can be blown out by weather

| | count |
| --- | --- |
| `Fireplace` with `m_canTurnOff = true` | **1** (`Candle_resin`, the weakest emitter) |
| `Fireplace` with `m_canTurnOff = false` | 16 |
| **no `Fireplace` at all** | **21** |

The 21 with no `Fireplace` — every MountainKit/CastleKit brazier and groundtorch, every
Dvergr lantern, the Mistlands torch, the fairy garland, `piece_Lavalantern`,
`GlowingMushroom` — are **pure lights**. No fuel, no wetness, no state. They cannot go out.

### The fires that CAN go dark are the big ones

Power ≈ `intensity × range²`:

| prefab | intensity | range | power |
| --- | --- | --- | --- |
| `bonfire` | 2.00 | 20.0 | **800** |
| `piece_groundtorch` | 1.50 | 15.0 | 338 |
| `piece_walltorch` | 1.50 | 12.0 | 216 |
| `fire_pit` / `fire_pit_iron` | 2.00 | 10.0 | 200 |
| `hearth` | 1.50 | **3.0** | **14** |
| `Candle_resin` | 2.00 | 1.0 | **2** |

Fuel-burners are 33.9% of placed lights but **55.4% of the light**; per build the median
fuel-burning share of light is **74.2%**.

**`hearth` is a small light** — power 14 against a bonfire's 800. The name has been
carrying an implication the prefab does not support.

### 15 of 39 environments put fires out

`wets_fires = m_isWet OR m_windMax >= 0.8`:
`Ashlands_SeaStorm`, `Ashlands_storm` (windMax **3.00**), `Bonemass`, `Eikthyr`,
**`Heath clear`**, `LightRain`, `Mistlands_rain`, `Mistlands_thunder`, `Moder`, `Rain`,
`SnowStorm`, `SwampRain`, `ThunderStorm`, `Twilight_SnowStorm`, `nofogts`.

**`Heath clear` wets fires at `m_isWet = false`** on wind alone — which is why the rule is
an OR. Of the four environments this project has ever shot (Clear, Misty, ThunderStorm,
Twilight_Clear), only ThunderStorm wets fires.

**The game ships 39 environments and the project shoots four.** `Twilight_Clear`,
`Twilight_Snow` and `Twilight_SnowStorm` have never been used — the twilight work has been
*synthesising* twilight by forcing Clear and setting the clock to 0.71. `nofogts` reads as
a no-fog debug environment and is worth a probe against the whiteout problem.

---

## 7. Lessons learned — read this before trusting anything

### The rule everything reduces to

**Verify state, not the report of the command that was supposed to change it.**

Every check in the pre-flight earned its place by catching something already reported fine:

- **The binary over the claim.** Two lanes each claimed the same mod build; reading the
  installed DLL for the method names each had added showed it carried *both*.
- **The PID over the kill.** A transfer was reported killed; two `scp` children were still
  reading the live world minutes later, because the job stop reaped only the wrapper shell
  and returned success.
- **The photograph over the receipt.** 16 frames came back `clearance="planned"`,
  `occluded=false`, `pieces_near_aim` up to 30,930 — and the moon is in zero of them.
- **The loader over the directory.** Three DLLs sat in a folder named
  `_parked-by-selfie-stick`; checking the directory was the right instinct and gave the
  wrong answer, because BepInEx scans `plugins/` **recursively** and only `LogOutput.log`
  says what actually loaded.

### `occluded=false` is blind to player builds

`IsOccluded` masks `terrain`, `static_solid` and `Default`. Placed pieces are on the
`piece` layer — twelve lines away in the same file, `PiecesNear` uses it correctly. So the
check returns clear with the lens against masonry, and **`FindClearView` inherits the same
blindness** through every lift rung and swing bearing.

Exterior orbits at standoff are fine (blockers are trees and hillsides, which *are* in the
mask). Interior work is not. **Do not add `piece` to that mask** — every orbit would
report its own subject as an obstruction and fire lift-and-swing on every frame. It needs
a re-baseline, not a one-word change.

This is the third instrument in this project to fail the same way: `--max-los` caught what
`depth_score` endorsed, `depth_score` read 0.58 on a photograph of a stone wall, and now
this. **Guard the plan, not the pixels.**

### Parking a plugin into a subfolder parks nothing

BepInEx scans `plugins/` recursively. To actually unload a plugin, move it **out of the
`plugins/` tree entirely**. As of 2026-08-26 the old `ComfyQuestRuntime` still sits in
`_parked-by-selfie-stick/` and **has no `ShowCreatorBar` gate at all** — see §8.

### The creator bar, and a warning that was right

61 frames were burned with the ComfyQuest overhead bar across `y 96–128`. The runner
**warned correctly at launch** and was talked past twice on two independent wrong readings
("the DLLs are parked"; "the setting was renamed to a hotkey — F9 *expands* an
already-drawn bar, it does not summon it").

Real mechanism: a **bootstrap problem**. `ShowCreatorBar` lives in `[Presentation]`,
`CreatorBarHotkey` in `[Runtime]` — two keys, two jobs. BepInEx materialises a plugin's
config defaults **only when the plugin loads**, so the runner reads the file before the key
exists, warns correctly, and has nothing to switch off. The fix is one value with the game
closed; the runner then prints *"quest creator bar hidden for this session"*.

A queued "fix" to make that warning accept `CreatorBarHotkey` was **cancelled** — it would
have permanently silenced a true warning.

### Do not use a static-pixel test on night or storm frames

Fraction of bit-identical pixels in a band is **confounded by darkness**:

| run | naive static % | truth |
| --- | --- | --- |
| nightsky | 4.61% | clean |
| storm (contaminated) | 5.81% | **contaminated** |
| daylight run | 0.00% | clean |

The clean night run scores closer to the contaminated one than to the clean daylight one.
Use `check_overlay.py`, which takes per-pixel standard deviation across **varied** frames:

```bash
python check_overlay.py --images "<capture-root>\<runid>"
```

It also **cannot validate a 2-frame smoke test at a fixed camera** — nothing in the scene
changes there either. For that, crop the band and *look at it*.

### The world file is shared mutable state and it failed two ways

Copying `ComfyEra17.db` (1.3 GB) to a second machine during a capture produced a
destination **41,320 bytes larger** than the source. Two mechanisms:

1. Valheim rewrote the source mid-read.
2. **`scp` does not truncate the destination** — 1,299,599,565 bytes over an existing
   1,299,640,885-byte file leaves exactly 41,320 bytes of stale tail. That arithmetic is
   exact, and it is the nastier one: it passes a size check, passes "transfer completed",
   and is silently wrong.

A third mode appeared live: **killed transfers do not always die**, and three concurrent
non-truncating writers into one destination produce interleaved garbage. `rm` the
destination first, verify with `md5` on both ends, and **copy from a frozen
`*_backup_auto-*.db` snapshot, never from the live world.**

### Statistics discipline

Two of this lane's own claims were published and retracted the same day:

- An argument from an "inversion" (most warm mass, least relationship) died because
  `seat` at r = −0.018 and `toproom` at r = −0.021 are **the same number at opposite ends
  of the gradient**. Not monotonic; the ordering carried no weight.
- Five correlations were reported with no significance. Only one reached p < 0.05 (0.026)
  and across ten tests Bonferroni wants 0.005. **Five nulls, one noisier than the rest.**

Also: a predictor mismatched to the measurement guarantees part of its own null.
`warm_lights` is a per-*build* count while a vantage sees a fraction of the build — thirty
braziers over 100 m put almost none of themselves in a seat frame. The better predictor is
per-shot `fires_found` / `fires_in_view` from the receipts.

### Attribute effects to mechanisms that can produce them

Twice, a real observation was credited to a cause that could not generate it: the
41,320 bytes to the mid-read tear, and the inside/outside storm gap to `CheckWet`. The IL
for `CheckWet` was read correctly; nobody checked **how many prefabs it reaches** — one
candle. The 5.0%-vs-16.6% warm-mass gap is real and **its cause is still open**. The
plausible remaining explanation is simply that an outdoor storm frame is mostly grey sky
and wet ground while an indoor one is mostly warm material.

### State the manipulation before reading a null

The fires A/B moved `bright_warm_frac` by a median of **+0.007 points** across 30
within-build pairs, against a **5.5-point** within-build noise scale. But:

- the weather path reaches one candle, so clearing `m_wet` could do nothing;
- ~25.7 of ~30 fires per build were **already burning** with no intervention, leaving
  ~4.4 genuinely dead;
- `fires_lit` is an **unweighted count** — a bonfire and a `Candle_resin` are both 1.

So the honest result is **"the experiment could not produce the effect"**, not "holding
fires does nothing". The corpus contains no genuinely dark build to test the real question
against, and receipts do not record the *prefab* of a dead fire — the cheapest fix is
recording prefab names alongside `fires_burning`.

---

## 8. Open work

### Immediate hazards (2026-08-26)

1. **`orbit-request.json` is still armed with `light_dump: true`.** A scripted run
   overwrites it, but launching Valheim to *play* will trigger a dump and quit.
2. **The creator-bar protection is gone.** `ComfyQuestRuntime.dll` was rebuilt 2026-08-26
   22:04 and BepInEx rewrote its config from the new build's declarations, dropping
   `ShowCreatorBar = false`. The new binary *has* the gate; the **old copy in
   `_parked-by-selfie-stick/` does not**, and it still loads. **Move those DLLs out of
   `plugins/` entirely before the next capture, and verify frames with
   `check_overlay.py` afterwards.**
3. **`settleSeconds` is 6.** Set it to 3 (adopted, 29% faster) with the game closed.

### Queued and open

- **`lane/storm` and `lane/nightsky` are unmerged.** `main` still carries the *unguarded*
  night planner — `plan_nightsky.py` on `main` has no `sky_margin` and would re-emit the
  build that produced lattice photographs. Shooting an existing TSV is safe
  (`Start-NextRun` passes `-SkipPlan`); **replanning from `main` is not.**
- **`hearth-1` (324 frames) should be re-scoped or dropped.** Its premise went from "every
  fire was out" → "fuel-burners only" → "~4.4 per build", and the prefab it is named after
  emits at power 14. Re-scope to builds *measured* genuinely dark, or drop it.
- **Night sky: disc found in 0 of 30.** Diagnosed as clear sky + wrong bearing, not cloud —
  stars median 149 with 22/30 frames above 100, and 26/30 held the planned stance. The
  planner aimed at azimuth 78 from limb fits in **two frames from two runs**, and moon
  phase varies by in-game day and cannot be forced. Needs a real bearing before re-shooting.
- **Predicted `opponent_gap` per environment.** `lights.json` carries `m_ambColor*` and the
  fog colours for all 39. Since the cool lobe does all the work (§3), a predictor built on
  ambient could rank all 39 on paper. **Shoot the predicted best AND worst** — a test that
  can only confirm is not a test. Prior validation is weak: r = +0.55 on n = 5.
- **`LIGHT_HUE` should be replaced with measured `Light.color`** from `lights.json`. The 17
  hand assignments were made from names and one was already wrong —
  `piece_FairylightGarland` renders as **blue** point lights, caught only by looking at a
  frame. Names are not evidence about colour.
- **The `approach` vantage** — up the steps from the sea toward a lit gate — is unclaimed.
  452 of 1,025 in-world builds sit at `min_y` 28–34 (Valheim sea level is 30). Seaward
  direction is not derivable from the DuckDB cache (no terrain); the cheap proxy is
  radially outward from world centre, which is wrong on lakes, inlets and the inside of a
  bay.
- **AM4 as a second capture node** is built and staged (Ubuntu 26.04, RTX 5070, headless GPU
  X server verified at 3840×2160, scripts installed, world copied from a frozen snapshot).
  **Blocked on a Steam login only the operator can perform.** It makes the capture race
  per-host rather than global.

### The other two lanes

| lane | owns | branch |
| --- | --- | --- |
| **storm** | `--fires` levers, storm/storm_dark/storm_flash, `Plugin.cs`, TSV cols 13/14/15 | `lane/storm` |
| **night sky** | rooftop vantages, `scan_rooftops.py`, `plan_nightsky.py`, `sky_check.py`, the `LIGHTS` vocabulary | `lane/nightsky` |
| **colour** (this one) | `color_layers.py`, `LIGHT_HUE`, the capture schedule | `main` |

Shared and needing a named owner: `scan_features.py` vocabulary (night sky), the TSV
positional contract (storm), `Plugin.cs` and the installed DLL (rotating, serialised
through the scheduler), `Start-NextRun.ps1` queue and `out/era17/` (scheduler).

The mod source is **outside baseline**, at
`C:\work\_retired\comfy\handoffs\valheim-camera-proof\Plugin.cs` — a single ~115 KB file
in a retired archive repo, edited by two lanes. Build it in a throwaway copy first; that
practice caught two compile-time errors before an unfreeze window.
