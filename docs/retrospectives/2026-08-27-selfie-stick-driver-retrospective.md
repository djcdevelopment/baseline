# Selfie-stick driver and the channel lane — retrospective 2026-08-27

## Executive summary

Three concurrent photography lanes (storm, night sky, colour) ended 2026-08-25 with three
handoff documents and no single way to run any of them. This session collapsed that into
one driver, `tools/selfie-stick/Invoke-SelfieStick.ps1`, moved capture onto AM4 as a second
node, and then used the working pipeline to answer the night lane's blocking question.

Landed on `main` as `04556553..9d9c148a`, 13 commits, 2,594 insertions across 13 files.
Tests went 64 → 75.

The most valuable output was not the driver. It was discovering that **the night lane was
never blocked**: its "disc found in 0 of 30" was a measurement failure, and the moon is
present in six of its own frames. Two gates inside `sky_check.py` — a cyan colour test a
bloomed moon cannot pass, and a radius floor tuned against a fit that implied a 43-degree
angular radius — hid it. That is the fourth instrument in this project to be believed over
the photograph, and the third prefab vocabulary written from outside this world to be wrong
inside it.

Four capture runs, 105 frames, all on AM4 at 3840x2160, all pulled back md5-verified with
zero duplicated receipts.

## What shipped

### One driver

`Invoke-SelfieStick.ps1` owns the run registry, the merged pre-flight, `settleSeconds`, DLL
provenance, dispatch to either host, the AM4 pull-back, provenance writing, and the scoring
tail. It deliberately does **not** own the launch/wait/verify of a local capture:
`Invoke-OrbitCapture.ps1` and `Invoke-InteriorCapture.ps1` keep that, including the `finally`
block that restores operator config bytes on every exit path, and AM4 keeps `run-capture.sh`.

Three things it owns that nothing owned before:

- **Status derived from evidence.** The old queue had no notion of done, so three of its
  seven rows still advertised captures shot on 08-24 (`creators-1` is `20260824-083226`,
  `twilight-1` is `20260824-100400`, `sky-probe` is `20260824-094718` — 70 receipts, 14
  clusters, pitch 74.0-86.2, which is that row's own description). Status now unions seeded
  history with the `run-provenance-<name>.json` the driver writes itself, so the mapping
  closes rather than needing a human to edit source after every capture.
- **`settleSeconds`.** It was *declared* on `storm-1a`/`storm-1b` and read nowhere; the A/B
  that adopted 3 was run by hand-editing the mod cfg.
- **The AM4 leg end to end.** None of it existed — `run-capture.sh` printed `RUN` ids and
  nothing fetched them. The destination is removed before every copy and both ends hashed,
  because `scp` does not truncate.

`Start-NextRun.ps1` is superseded and carries a banner naming its three defects.

### The channel lane

`scan_channels.py` and `plan_channel.py` implement a composition rule the night planner
cannot express: choose the bearing by the **channel**, keep the moon 40-140 degrees
off-axis so it rakes rather than sits in frame, and set pitch so clear sky fills the top
sixth-to-third. Every pitch it emits is positive — tilted *down* — which is why no existing
night frame could show this: all of them are aimed above the horizon.

Open water comes from `<World>_mapTexCache`, the 2048x2048 biome PNG Valheim writes beside
the save. The mapping was solved rather than assumed (10 m/px centred on 1024, row direction
fixed by Mountain pixels carrying mean build `min_y` 127.9 m against 64.8 on land).

Nine tests guard the composition rules, and the first two are the reason the file exists: no
shot may point within the minimum offset of the moon, and none may put it behind the camera.

## What the evidence says

| claim | measurement |
| --- | --- |
| the rendered disc sits on the directional light | azimuth residual mean **-0.01 deg** (\|max\| 1.7), altitude mean **-0.62** (\|max\| 2.3), 11 discs across two runs |
| the night plan aims correctly with no bearing argument | `nightsky-2` median azimuth residual **0.2 deg**, every frame inside ±0.7, altitude inside ±0.6 |
| the moon's angular radius | **rho ≈ 6 deg** — 6.45, 5.5 and 5.8 from three independent runs. It had defaulted to 0 since the lane began, biasing every aim point by about a disc radius |
| the channel rule composes | **46 of 58** frames have a top third over 40% sky and under 12% foliage; moon offset median **93 deg** |
| the AM4 leg is sound | 105 frames at 3840x2160, md5 verified both ends, receipts merged with **zero** duplicated `(run, file)` pairs across 4,700+ lines |

## What was wrong

Seven things reported fine and were not. Six were pre-existing; one was mine.

1. **`sky_check` could not see the moon.** The candidate mask required `(blue - red) > 25`;
   a bloomed moon reads **+8.3**, and +4.0 across its brightest 500 px. The radius floor was
   400 px against a clean 253 px fit. Fixed, it recovers **6 discs from the original 30-frame
   run** at azimuth residual mean +0.86.
2. **"The rendered disc is NOT where the light comes from"** — the night lane's §3.2 finding,
   and the basis for `--body-azimuth 78`. It came from limb fits on two frames, and that same
   section already flagged limb fitting as unreliable (the same body measured 41.3 and 63.7
   degrees of altitude).
3. **AM4's X server was pinned to `Virtual 1920 1080`** while `run-capture.sh` asks for
   3840x2160. Unity clamps to the screen, so every capture would have been 1080p with every
   check passing — the same silent downgrade that shipped the whole Era 17 series off OMEN's
   BMC adapter. Its EDID also reads empty, so the config comment describing "the panel's
   native 1920x1080" is describing a VESA fallback, not the hardware.
4. **The staged BepInEx payload reproduced the creator-bar bug by construction** — it ships
   `_parked-by-selfie-stick/` with three quest DLLs, and BepInEx scans `plugins/` recursively.
   Its quest config has no `ShowCreatorBar` key at all. A fresh AM4 install starts in exactly
   the state that burned 61 frames. It also shipped a stale mod (`bc66f907`, predating the
   light dump) and `settleSeconds = 6`.
5. **`check_overlay` could never pass a night run.** It read 3.70% frozen on a clean one;
   95.3% of those pixels were near-black, and 61.8% of a night frame sits below luma 16.
6. **`Start-NextRun`'s index rebuild wrote an empty gallery.** `@()` around a
   `ConvertFrom-Json` pipeline yields a one-element array holding an `Object[]`, so all 18
   run ids collapse into one 287-character `--run` matching nothing. The capture runners
   `foreach` over the raw result and are unaffected.
7. **My own tree vocabulary was wrong** — written from knowledge of Valheim rather than this
   world's placement counts. It missed `YggaShoot_small1`, the **fourth most placed vegetation
   prefab in Era 17 at 472,679**, plus `YggaShoot1/2/3`. Cluster 26 has seven of them 24 m
   from its stance; the planner called that bearing open and shot solid foliage.

I also told Derek mid-session that the original run "aimed 56 degrees off, so the moon
genuinely wasn't in those frames." The aim error is real; the conclusion was not. The moon
was there. I corrected it in the same session, but it was asserted before it was checked.

## What is open

- **The gallery index has not been rebuilt.** All four runs used `-SkipFollowUp` because OMEN
  was busy — each rebuild re-derives ~2,600 web images twice. 105 frames sit on disk with
  receipts merged and are not in the gallery.
- **Frame selection is not a real measurement.** The proxy used to rank the 58 channel frames
  ("blue-dominant equals sky") scored a giant cyan Yggdrasil glow as 100% sky. The geometry
  is validated; the ranking is not.
- **`sky_check` still finds only 5-6 of 20-30.** A disc clipped by the frame border loses the
  interior edge pixels a limb fit needs. A saturated-blob centroid fallback would find the
  rest — that is all the manual measurement in this session used.
- **`rho ≈ 6` is measured but not fed back** into any plan.
- **`run-capture.sh` warns on the wrong thing** — it tests for the quest *config file*, not
  for a loadable quest DLL. On AM4 the log shows only four plugins load and none is
  ComfyQuestRuntime, so the warning is a false alarm. Not silenced; it needs to test the
  loader, not the directory.
- **Four cluster-182 frames remain in the gallery** — two from `20260825-072915`, which are
  the diamond-lattice photographs the `sky_margin` guard was built to prevent. They score
  5.40 and 5.44 because the aesthetic head reads global tone.
- **`am4-smoke` still reads queued**, correctly: its run threw at the overlay gate before
  provenance was written.

## Lessons

**A conservative instrument's false negative is indistinguishable from a result.**
`sky_check.py` documented itself as "deliberately conservative — expect false negatives, not
false positives", and that was accurate and still not enough. A lane read one as a finding and
spent its remaining effort on the wrong variable. An instrument that can refuse should say
*why* it refused, not emit `nan`.

**The photograph settled it again, and it took four attempts to reach for it.** Statistics
said 3.70% frozen; the picture said dark sky. Statistics said 0 of 21 discs; the picture had
the moon in the corner. This is now the fourth instrument in this project to be believed over
the frame — after `--max-los`, `depth_score`, and `IsOccluded`.

**A guard that cannot fail is decoration; so is one that cannot pass.** `check_overlay` on a
night run and the overlay gate on a four-frame smoke test were both in the second category.
The fix was not to loosen the threshold but to measure the property that actually separates
the cases — frozen *and lit*, and a band rather than a percentage.

**Prefab vocabularies written from outside this world are wrong inside it.** Seats, lights,
and now trees. The rule that works is: enumerate by placement count across **every** category,
and audit by eye. Category must not be filtered — people plant trees, and `Birch1` appears
38,464 times as BUILDING against 25,762 as UNKNOWN. And the sweep itself needs auditing:
`%fir%` matches `FireFlies` and `fire_pit`, exactly as a `-table-` sweep once swallowed
`UnstableLavaRock`.

**Isolate the guessed number.** The canopy heights are the only assumed values in
`scan_channels.py`, and they sit on real data — a tree's ZDO pivot is ground elevation. One
`--tree-scale` knob recalibrates all of them against a single frame with a visible treeline.
Nothing else in the file rests on having guessed a prefab's size right.

**"Not derivable" was a statement about one cache, not about the machine.** Seaward direction
was recorded as underivable because it is absent from the DuckDB analytics cache. It is
sitting next to the save as a PNG.

## Provenance

Runs this session, all on AM4, all 3840x2160, all `check_overlay` clean:

| run | plan | frames |
| --- | --- | --- |
| `20260827-084611` | am4-smoke | 4 |
| `20260827-085344` | night-ephemeris | 21 |
| `20260827-090252` | nightsky-2 | 22 |
| `20260827-092614` | channel-1 | 58 |

Mod `ComfyCameraProof.dll` md5 `bc4ca9e447c30c4003a41101bd084cce` (`19fd460`), identical on
both hosts and verified per run. Before this session that binary had never produced a receipt.
