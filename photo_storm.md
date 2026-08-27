# Storm photography lane — handoff

Written 2026-08-25 for a cold-context agent. Everything here is measured unless
it says otherwise. Where a claim was wrong earlier in the day, the correction is
in place and the wrong version is named, because the wrong versions are how you
avoid re-deriving them.

---

## 1. What this is trying to accomplish

The **selfie-stick** is an unattended screenshot pipeline that photographs
player-built structures in a Valheim world and publishes them as a gallery. It
plans camera positions from a world scan, flies them with a BepInEx mod, scores
the frames, and builds an index.

Derek's question that started this lane:

> how can we get better storm shots? an eternally fuelled hearth/fires/torch on /selfie-stick?

Two claims sat behind it, and both turned out to be true but much narrower than
stated:

- **Storm is the best-scoring condition this project has ever measured — indoors.**
  Storm 5.211 against sunset 5.194, sunrise 5.193, night 5.041.
- **Exterior storm had never been shot at all.** Every one of the 300
  `ThunderStorm` receipts out of 4,536 was `mode: interior`. Every orbit plan
  ever flown was `Clear` + `Misty`. `Rain` had never been used in an automated
  run. So "weather is worth having inside and not outside" was an inference from
  Clear-vs-Misty, not a verdict on storm.

The hypothesis was that storms photograph badly because the builders' own
lighting is off. That is **partly true and mostly not** — see §4.

---

## 2. Where everything lives

| thing | path |
|---|---|
| Mod source | `C:\work\_retired\comfy\handoffs\valheim-camera-proof\Plugin.cs` |
| Mod project | same dir, `ComfyCameraProof.csproj` (net472) |
| Installed DLL | `C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\plugins\ComfyCameraProof.dll` |
| Build + install | `.\build-and-install.ps1` in the mod dir |
| Planner / scoring / gallery | `C:\work\baseline\tools\selfie-stick\` |
| My worktree | `C:\work\baseline\.claude\worktrees\lane-storm`, branch `lane/storm` |
| Runbook (the real record) | `docs/internal/RUNBOOK-selfie-stick-era17-series-2026-08-22.md` |
| Receipts | `<Valheim>\BepInEx\config\shotplan-receipts.jsonl` |
| Frames | `<Valheim>\BepInEx\config\comfy-orbit-captures\<runId>\` |
| Capture world | `%USERPROFILE%\AppData\LocalLow\IronGate\Valheim\worlds_local\ComfyEra17.db` |

**The mod is not in any sovereign repo.** It lives in the retired `comfy`
archive checkout, deliberately — `lumberjacks-platform/.../camera-gallery.md`
says it is "kept out of this repo on purpose, so that claiming the in-game half
stays a real, available piece of work". Editing it in place is correct. Homing
it is a separate decision nobody has made.

### Mod commits from this lane, in order

| sha | what |
|---|---|
| `b9ad766` | interior mode (pre-existing uncommitted work, committed so the rest was separable) |
| `450298a` | hold the builders' fires lit; drive the lightning flash |
| `fe82739` | guard the ZDO writes on ownership |
| `2a21147` | survey fires on **every** shot; `fires_in_view` |
| `68d8296` | widen `LightLod` on every frame; count fires at the shutter |
| `19fd460` | **light dump**; `fires_found_at_sweep`; `IsOccluded` docstring; `assembly_utils` ref |

Current installed DLL: `19fd460`, md5 `bc4ca9e447c30c4003a41101bd084cce`.

---

## 3. What was built

### 3.1 Hold the builders' fires lit

Read out of `assembly_valheim.dll` 0.221.12 with `ilspycmd`, **not** from field
names — the atlas annotation layer has been inverted before and it cost
ComfyQuestLab two rounds of watching a gallery collapse.

```
IsBurning() = !m_blocked && state == 1 && !underwater && (fuel > 0f || m_infiniteFuel)
```

and `UpdateFireplace`'s drain sits behind `IsBurning() && !m_infiniteFuel`. So
`m_infiniteFuel` is honest and on its own makes a fire burn at fuel zero.

Three levers, only one of them obvious:

- **Fuel.** `GetTimeSinceLastUpdate` reads `s_lastTime` and burns off every
  second that passed while the zone was unloaded.
- **Wet is a SEPARATE mechanism and `m_disableCoverCheck` does NOT gate it.**
  `CheckWet()` runs off its own `InvokeRepeating("CheckEnv", 4, 4)`; when
  `EnvMan.IsWet()` it swaps `m_enabledObjectHigh` for `m_enabledObjectLow` and
  toggles off anything with `m_canTurnOff`. That is the storm case exactly.
  `m_disableCoverCheck` only clears `m_blocked` (buried under terrain / no
  headroom).
- **`LightLod` culls the light before it reaches the lens.** Default
  `m_lightDistance` 40 m and `m_shadowDistance` 20 m against orbits planned to
  120 m, plus a **static** `LightLod.m_lightLimit` capping how many lights burn
  at once regardless of distance.

`m_infiniteFuel`, `m_disableCoverCheck`, `m_wet`, `m_blocked` are plain instance
fields — not synced, nothing written to the world. Only `fuel` and `state` are
ZDO-backed; both are written only when they differ, both restored, both guarded
on `ZNetView.IsOwner()`.

The mechanism was already proven in
`comfy-quest/network/mod/ComfyQuestLab/Patches/GalleryStructurePatches.cs:134-141`,
scoped to QuestLab's own gallery pieces. This is the same three lines pointed at
the builders' fires instead.

### 3.2 Driven lightning

`Thunder.DoFlash()` is private and picks a random bearing, so `DriveFlash`
replicates it against the same public `m_flashEffect` at a chosen bearing and
rotates the spawned `Light`s back at the subject — which is what makes a strike
light the scene rather than only the sky. The spawned `LightFlicker` is re-timed
to a flat hold because a real strike is shorter than the shutter is reliable at
4K. **Never exercised in anger** — no `storm_flash` result has been read yet.

### 3.3 Plan format

Two optional trailing TSV columns, absent = off, so every plan already on disk
reads unchanged:

```
cluster_id  shot  cam_x cam_y cam_z  yaw pitch  env  time  aim_x aim_y aim_z  label  mode  fires  flash
   0         1     2     3     4      5    6     7    8     9    10    11      12     13     14     15
```

`plan_shots.py` gained `--fires`, `--storm-shots {0..3}`, `--storm-only`,
`--storm-environment`, `--storm-time`, `--flash-bearing`, `--cluster-ids`, and a
`validate_tsv()` that re-parses the way the mod's `LoadShotPlan` does.

### 3.4 Receipt fields added

`fires`, `fires_found`, `fires_found_at_sweep`, `fires_in_view`,
`fires_burning`, `fires_wet`, `fires_lit`, `fires_unowned`, `light_lods`,
`flash`, `flash_bearing_deg`, `flash_hold_s`.

**Read the timing carefully.** `fires_found` and `fires_in_view` are measured at
the **shutter**. `fires_burning`, `fires_wet`, `fires_lit`, `fires_unowned` are
measured at **hold time**, before the settle wait, because they describe the
pre-intervention state. `fires_found_at_sweep` exists so the hold-time
population has a denominator. Dividing a hold-time numerator by a shutter-time
denominator gave 39.6% where the truth was 73.5%.

### 3.5 Light dump — built, committed, NEVER RUN

Fire it by writing to `<Valheim>\BepInEx\config\orbit-request.json`:

```json
{"world":"ComfyEra17","character":"tugcorp","quit_when_done":true,"light_dump":true}
```

Takes precedence over `sky_times` and over a shot plan. Walks `ZNetScene`,
writes `<Valheim>\BepInEx\config\comfy-camera-proof-lights.json`, quits. One
world load, ~2 min, no screenshots. Console equivalent: `comfyproof_lights`.

Emits per light prefab: `Fireplace`'s `m_infiniteFuel`, `m_canTurnOff`,
`m_canRefill`, `m_disableCoverCheck`, `m_lowWetOverHalf`, the three fuel
scalars, `m_coverCheckOffset`, `m_fuelItem`; every child `Light`'s type, colour,
intensity, range, shadows; `LightLod` distances; plus the statics.

Emits per environment, **all 39**: every colour, every fog density, every
gameplay bool, `m_windMin/Max`, `m_sunAngle`, the light intensities,
`m_psystemsOutsideOnly`, and a computed `wets_fires` = `m_isWet || m_windMax >= 0.8f`.

**This is the highest-value thing outstanding.** See §6.

---

## 4. The data

### 4.1 There are 39 environments. This project shoots 4.

`comfy-camera-proof-envs.json` had **never been written** before today — the
command existed and had never run. The four names in use (`Clear`, `Misty`,
`Rain`, `ThunderStorm`) were hand-picked from a console help string.

```
Ashlands_ashrain  Ashlands_ashrain_clear  Ashlands_CinderRain  Ashlands_meteorshower
Ashlands_misty    Ashlands_SeaStorm       Ashlands_storm       Bonemass
Caves             CavesHildir             Clear                Crypt
CryptHildir       Darklands_dark          DeepForest Mist      Eikthyr
Fader             GDKing                  Ghosts               GoblinKing
Heath clear       InfectedMine            LightRain            Mistlands_clear
Mistlands_rain    Mistlands_thunder       Misty                Moder
nofogts           Queen                   Rain                 Snow
SnowStorm         SunkenCrypt             SwampRain            ThunderStorm
Twilight_Clear    Twilight_Snow           Twilight_SnowStorm
```

Three of these change open questions rather than adding options:

- **`Twilight_Clear`, `Twilight_Snow`, `Twilight_SnowStorm`.** The twilight lane
  *synthesises* twilight by forcing `Clear` and setting the clock to 0.71. The
  game ships purpose-built twilight environments and none has ever been used.
- **Storms plural.** `ThunderStorm` is one of at least six. The colour lane's
  "a storm is grey, not blue" (`opponent_gap` floor 74.5) is a **one-storm**
  measurement.
- **`nofogts`.** Reads as a no-fog debug environment, against six fog-flagged
  whiteout frames and a veto built to hide them.

`SetForceEnvironment` takes any of these regardless of biome.

### 4.2 The fires were mostly already lit

Per build, at the shutter, averaged over 45 frames:

| | count |
|---|---|
| fires found near subject | ~30.3 |
| in the camera frustum | ~28.3 |
| **already burning, untouched** | **~25.7 (85%)** |
| **genuinely dead** | **~4.4** |

The dead count is stable at **4.33 / 4.40 / 4.6** across three variants at three
streaming depths, one of which holds fires and two of which don't.

Two things follow:

1. **The restore works.** If `ReleaseHeldLight` were failing, `storm_dark` at
   index 1 would inherit fires lit by `storm` at index 0 and its dead count
   would collapse toward zero. It doesn't. This is the *first evidence* for the
   restore — previously it was only reasoning.
2. **The premise narrowed three times.** "Every fire is out" → "fuel-burners
   only" → "a stable ~4.4 per build". Few is not the same as unimportant.

### 4.3 The fires A/B is a null

30 within-build pairs, identical camera, sky, clock; only the fires differ.

| metric | median delta | positive |
|---|---|---|
| `bright_warm_frac` | +0.007 pts | 20/30 |
| `warm_frac` | +0.010 pts | 18/30 |
| `scene_v` | +0.002 | 18/30 |

Against a **5.5-point** within-build noise scale, that is ~500× below noise.
20/30 positive is binomial p ≈ 0.10.

**State it as:** "lighting four more fires out of thirty does essentially nothing
to the frame." **NOT** as "the builders' fires do not matter." `fires_lit` is an
unweighted count — a bonfire and a `Candle_resin` are both 1. Whether this null
is boring or surprising depends entirely on which of those the 4.4 dead fires
are, and **only the light dump answers that**.

### 4.4 Settle 3 is safe and 29% faster — adopted

The 10.0 s/frame floor decomposed as: 1.5 (stable player) + ~2.0 (world-settle
poll) + **6.0 (`settleSeconds`)** + 1.0 (post-capture) = 10.5 s. p10 = p50 =
10.0 across 4,536 receipts meant it was configured sleep, not physics.

| half | settle | occluded | median gap | aesthetic | depth |
|---|---|---|---|---|---|
| storm-1a | 6 | 0 | 10.24 s | 5.465 | 0.566 |
| storm-1b | 3 | 0 | 7.24 s | 5.498 | 0.497 |

Zero occlusion rejects in both halves — the objective measure agreed **in
advance**. `settleSeconds` lives in
`<Valheim>\BepInEx\config\com.comfy.camera-proof.cfg` and must be edited **with
the game closed**, or BepInEx rewrites it from memory on shutdown.

**A prediction of mine failed and should stay on the record.** I said settle 3
would show fires arriving after the hold pass. Measured as
`fires_found − fires_lit − fires_burning`: settle 6 medians **+2**, settle 3
medians **+0**. The short wait had *less* lag. I would have bet the other way.

The split was **interleaved by rank**, not cut in half — `twilight-1` is written
in rank order and rank tracks size and how well a build photographs, so
first-15/last-15 would have handed settle 6 the better subjects and the A/B
would have measured subject difficulty.

---

## 5. How to execute

```powershell
cd C:\work\baseline\tools\selfie-stick
.\Start-NextRun.ps1                      # shows the queue
.\Start-NextRun.ps1 -Run storm-1a        # fires one
```

Generate a storm A/B plan:

```powershell
python plan_shots.py --clusters out/era17/clusters.json --names out/era17/cluster-names.json `
  --out out/era17/storm-1a.json --cluster-ids "116,323,..." --storm-shots 3 --storm-only
```

Three variants per build on the hero framing: `storm` (fires held), `storm_dark`
(control, fires off), `storm_flash` (fires + driven strike at −35°).

**Pre-flight before any capture** (the coordinating session's, earned the hard way):

1. Valheim not running — verify **by process**, not by a stop returning success.
2. No index rebuild in flight (it re-derives ~2,600 web images, ~15 min).
3. Nothing reading the **live** world file.
4. DLL provenance verified at a known sha.

**Do not judge these frames by the aesthetic head.** It reads global tone:
time/weather moves the median 0.62 while lighting direction moves 0.03 and
structure ~0. Every storm frame is dark and it marks them all down. The VLM
tiebreak (`judge_frames.py`) is also down — it posts to Ollama on 11434, which
stopped listening when `OllamaBoot` was disabled.

### AM4 as a second capture node — one step from done

Steam allows one account per machine, so parallel capture needs **machines**.
AM4 (`homebase` in `~/.ssh/config`, `am4.tail8e749c.ts.net`) is Ubuntu 26.04,
Ryzen 9 5900X, **RTX 5070 that was sitting at 0%**. It had no Steam and no
Valheim, contrary to assumption.

Built and verified:

- `valheim-xorg.service` — headless GPU X on `:0`, enabled, survives reboot,
  renders as `NVIDIA GeForce RTX 5070/PCIe/SSE2`, OpenGL 4.6, 3840×2160 virtual
  screen. `xhost +SI:localuser:derek` only — never `xhost +`, this box is the
  public origin.
- `~/valheim-capture/run-capture.sh` — the Linux sibling of
  `Invoke-OrbitCapture.ps1`.
- `~/valheim-capture/install-mods.sh` — unpacks OMEN's exact BepInEx tree.
- `~/valheim-capture/bepinex-payload.tar.gz` — 2.2 MB, staged.
- World copied and **md5-verified** from a frozen backup.

**Blocked on one step an agent must not do** — entering a Steam password:

```bash
/usr/games/steamcmd +@sSteamCmdForcePlatformType linux +force_install_dir /home/derek/valheim +login YOUR_ACCOUNT +app_update 892970 validate +quit
~/valheim-capture/install-mods.sh
```

Valheim has a **native Linux client** (`valheim.x86_64`, `oslist
"windows,macos,linux"`) — no Proton. Launch via `./start_game_bepinex.sh`
**directly**, never through Steam: with Steam launch options Unix doorstop often
fails to load plugins silently, and an unattended runner cannot notice.

---

## 6. What is open

| item | why it matters |
|---|---|
| **Run the light dump** | Highest value outstanding. Decides whether the 4.4 dead fires are hearths/bonfires or dead candles, which is the only thing that makes §4.3's null interpretable. Also weights `fires_lit`, names which of 39 environments wet fires, and gives the colour lane a predicted `opponent_gap` before shooting. |
| `hearth-1` (324 interior frames) | Queued but **scope depends on the dump**. Do not fire it first. |
| `storm_flash` | Built, never read. May be worth nothing — if the flash prefab carries no `Light` the receipt says `sky_only`. Test is `luma_mean` against the no-flash twin. |
| Twilight environments | The twilight lane has been synthesising twilight for its whole existence. One A/B on the same 30 builds. |
| Five unshot storms | `opponent_gap` floor of 74.5 is a one-storm measurement. |
| `IsOccluded` real fix | See §7. Needs a re-baseline, not a patch. |
| Corpus-wide: creator bar | 61 frames dropped. Older runs verified clean, but nobody has audited *every* run. |
| Homing the mod | It lives in a retired archive checkout. |

---

## 7. Known traps

**`IsOccluded` cannot see player builds.** It masks `terrain`, `static_solid`,
`Default`; placed pieces are on `piece`, which `PiecesNear` twenty lines below
uses to count them. It returns `occluded=false` with the lens flat against
masonry, and `FindClearView` — early return, five lift rungs, every swing
bearing — inherits the blindness. **Left deliberately unfixed:** adding `"piece"`
makes every exterior orbit report its own subject as an obstruction and climb
away from it. Valid for exteriors (trees and hillsides *are* in the mask);
useless for interiors, where the guard is `los`.

**Parking a plugin into a subfolder parks nothing.** BepInEx scans `plugins/`
recursively. `_parked-by-selfie-stick/` still loads. To actually unload, move it
**out** of the plugins tree.

**The creator bar burns into frames, and the runner's warning is TRUE.** The
switch is `ShowCreatorBar` in `[Presentation]` of
`djcdevelopment.valheim.comfyquestruntime.cfg`. `CreatorBarHotkey = F9` in
`[Runtime]` is a *different key* that **expands** an already-drawn bar. The
runner's warning fires because BepInEx materialises a plugin's config defaults
on load, so the runner reads the file *before* the key exists — right and
powerless on a first load. **Do not silence it.** If anything, make it fail
louder.

**A static-pixel test is confounded by darkness.** Fraction of pixels identical
across frames gave nightsky **4.61%** (clean) against storm-1a **5.81%**
(contaminated) and an older clean run **0.00%**. Near-black pixels are
bit-identical whether or not anything is drawn on them. Use
`tools/selfie-stick/check_overlay.py`. It also cannot validate a 2-frame smoke
test at a fixed camera, because nothing in the scene changes there.

**`scp` does not truncate.** Copying a smaller file over a larger existing one
leaves a stale tail — 41,320 bytes, passing both a size check and a
"transfer completed" check. `rm` the destination first.

**The world file is shared mutable state.** A capture rewrites
`ComfyEra17.db` mid-read and tears any concurrent copy. AM4 now reads a frozen
`_backup_auto-*` snapshot instead: a capture node has no business reading a file
the game is actively writing.

**`Version` is `internal`** — use `Application.version`. **`GetStableHashCode`**
is on `StringExtensionMethods` in **`assembly_utils.dll`**, not
`assembly_valheim`.

**Bash heredocs here mangle backslashes.** `\\t` collapses, `\v` becomes a
vertical tab. Write patch scripts with the Write tool instead. Also
`str.splitlines()` splits on `\v`, which shreds a line you're trying to repair.

---

## 8. Lessons

**Verify state, not the report of the command that was meant to change it.**
This is the whole day in one line, and it recurred in five distinct forms:

| the report | the reality | what settled it |
|---|---|---|
| atlas annotation says "disables" | the IL says the opposite | `ilspycmd` |
| `TaskStop` returned success | three `scp` children still writing | `Win32_Process` |
| directory says `_parked-` | loader says `Loading [ComfyQuestLab]` | `LogOutput.log` |
| config comment says "migrated" | `ShowCreatorBar` is live in another section | **the actual frame** |
| exit code 0 on a transfer | 41 KB stale tail | md5 both ends |

The escalation is always one artifact further down than the one you reach for.
The directory was the *right instinct* and still gave the wrong answer, because
the question was never "what is in `plugins/`" but "what did BepInEx load".

**The two errors that got through were caught by Derek putting a frame on the
screen.** Two sessions produced two independent, confident, wrong theories for
why the creator bar was harmless. The fastest instrument available all morning
was looking at the picture. The mod author had also written the answer in plain
words in a config comment we had both already read.

**Trial-build in a throwaway copy.** Pasting the light dump into a scratch copy
of the project and building it there killed two API guesses at compile time
instead of during a window when everyone was waiting.

**Match your denominators in time.** `fires_burning` at hold time over
`fires_found` at shutter time gave 39.6% where the truth was 73.5%.

**Don't pre-judge which fields to dump.** Emitting only what the current model
wants means re-running when the model changes. It is also literally how this
project came to shoot 4 environments out of 39.

**Ship the effect size with the unit.** "A 14% increase" was a statement about
fire *count* dressed as a statement about *light*.

**Design the control to differ in one thing.** `WidenLightLod` originally ran
only when holding did, so the control was "fires off AND lights culled" against
"fires on AND lights widened" — two variables, the second being the very
hypothesis the experiment existed to separate from the first.

**A two-frame smoke test is worth 45.** It found three defects it was not built
to find, one of which would have invalidated the experiment.

**Negative results were the most valuable output of the day.** The fires null,
the enclosure result that killed the colour lane's prior, and my failed settle-3
prediction all cost less than the positive results and constrained more.

---

## 9. Coordination note

Three sessions worked `C:\work\baseline` concurrently: storm (this one),
night-sky, and colour limits. One session acted as scheduler and owned all
captures, because the only guard is `Get-Process valheim` in three scripts — a
TOCTOU race where two sessions both see "not running", both launch, and each
restores the operator's BepInEx config over the other. There is also exactly one
installed `ComfyCameraProof.dll`; whoever installs last wins.

Isolated worktrees under `.claude/worktrees/` with a junction at
`tools/selfie-stick/out` back to the shared data directory — code isolated, data
shared. Never `git stash` in this repo: stashes are repo-global and one has
already reverted another agent's `git mv` renames.

**Do not fire a capture without asking whoever owns the schedule.**
