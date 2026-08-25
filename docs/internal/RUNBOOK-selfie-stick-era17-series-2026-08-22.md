# Era 17 series two — batched capture, scoring, and what the scores said

**Started** 2026-08-22 12:53 local, unattended, operator away 6–8 h.
**Ask:** cover as much of the primary density band as the window allows, run it in
batches so each one can be scored and the next one adjusted, and mix first-person
vantages in with the drone orbits.

Coordinates and creator ids stay out of this file. The data it describes lives in
`tools/selfie-stick/out/era17/`, which is gitignored for that reason.

## What "the primary density band" resolves to

Era 17's snapshot (107) clusters into **2,204 structures**: 1,025 in-world and
1,179 outland. The outland two thirds are the templated plot grid on 576 m
spacing — real, but repetitive, and series one already sampled ten of them.

The in-world 1,025 are not one hub. They spread across **84 occupied 2 km cells**,
and the five densest cells hold only 18% of the in-world piece mass. There is no
single geographic zone to "finish", so the band is taken in **score order**, which
already carries density: the ranking heuristic's `compactness` term is
pieces per m² of footprint. Ranks 1–40 shipped in series one; this series works
down from 41.

Coverage check on ranks 41–80: they land in **65 distinct 2 km cells**, including
every one of the densest. Score order is not concentrating the camera in one
neighbourhood.

## Two defects found before the first frame

**1. Series one shipped at half resolution.** Every Era 16 run captured
3840×2160. The Era 17 pilot at 09:05 captured 3840×2028. Every run after it —
all 300 published frames — captured **1920×1080**. The `-screen-width/-screen-height/-monitor`
arguments introduced in `7a0f8373` default to 1920×1080 and pick monitor
`DisplayIndex + 1`; the 4K panel is the *primary* display, so `-DisplayIndex 1`
sent the game to the 1080p ASPEED/BMC adapter at its native size. Series two runs
`-DisplayIndex 0 -CaptureWidth 3840 -CaptureHeight 2160`, verified against the
first frames on disk: 3840×2160.

**2. The interior lane could not be pointed at Era 17.** Two independent reasons,
both fixed:

- `Invoke-InteriorCapture.ps1` predated era isolation. It hardcoded `out/interiorplan.tsv`,
  rebuilt the gallery with no `--clusters/--dest/--run`, and had none of the orbit
  runner's ComfyNetworkSense preflight. Pointed at Era 17 it would have joined the
  captures to Era 16 cluster ids — the exact mislabelling `7a0f8373` fixed for orbits —
  and would have run an era-scale portal network without the connection cache.
  It now takes the same era arguments as the orbit runner and keeps the same preflight.
- `scan_features.py` read `FROM zdo` with no snapshot filter. The Era 17 cache holds
  **nine** snapshots (Era 16 ×3, a synthetic replay ×5, Era 17). Every interior would
  have been furnished from three worlds at once. It now takes `--world-id/--snapshot-id`
  and reads through the same `selected_zdo` view `scan_clusters.py` uses.

`scan_features.py` also hard-depended on `tools/component-packets/samples/prefab-dump.json`,
which left with the sovereign split. Rather than reach into a sibling checkout, the
piece vocabulary now falls back to the cache's own `category='BUILDING'` names — a
piece list by construction, and the only names that can ever match a ZDO in this world.
The dump is still used when present.

## What the series-one scores say

Series one shipped **unscored** — no `aesthetic.json` or `depth.json` existed under
`out/era17/`, so every gallery tile carried `aesthetic: null`. All 300 frames are now
scored on both axes.

Aesthetic (LAION head, median 5.55, range 3.80–6.15):

| facet | n | median |
| --- | --- | --- |
| orbit1 | 50 | 5.63 |
| dawn | 50 | 5.62 |
| orbit2 | 50 | 5.60 |
| orbit3 | 50 | 5.59 |
| orbit4 | 48 | 5.55 |
| **weather (Misty)** | **50** | **4.95** |
| in-world | 240 | 5.59 |
| outland | 60 | 5.33 |

**The Misty slot is the worst-performing sixth of the plan** — 0.65 below every
Clear variant, a gap far larger than the spread between the four orbit angles.

It is not a composition failure. On the geometry axis the Misty frames are
*better* than the Clear ones: depth_score 0.517 vs 0.483, far_mass 0.603 vs 0.551,
edge_frame 0.667 vs 0.593, center_block 0.001 vs 0.024. The whiteout-fog veto fired
on **zero** of the 300. The aesthetic head is docking the flat, desaturated look, not
a blocked or empty frame.

The two signals are close to independent across the set: **r = −0.117** between
aesthetic and depth_score over 300 frames. `center_block > 0.45` fired on exactly one
frame — on an all-exterior set that veto is nearly inert, which is expected; it was
calibrated to catch indoor duds.

Lowest-scoring kind is `tower` (5.15 vs 5.63 for `hub`), which is worth a look at
`elevation_for()` once there is a second band to compare against.

## Batches

| # | lane | targets | frames | state |
| --- | --- | --- | --- | --- |
| A | orbit | in-world ranks 41–80 | 240 | running from 12:53 |
| B | first person | interior-rich subset, paired with orbit-shot builds | ~256 | queued |
| C | orbit | in-world ranks 81–120, sixth slot as a light A/B | 240 | queued |
| D | orbit or first person, decided on B and C's numbers | | | queued |

Each batch ends with a gallery rebuild, an aesthetic pass and a depth pass, and its
numbers land in this file before the next one is armed.

Nothing is published. The live AM4 gallery still shows series one; pushing series two
to a public host is the operator's call, not this session's.

## What the geometry knobs are and are not worth

Testing series one's Clear frames (n=200, the Misty slot excluded) against the
values `plan_shots.py` actually planned for them:

- **Camera elevation does not explain the tower penalty.** Bucketed by the
  height:width ratio `elevation_for()` keys on, medians run 5.56–5.66 with no
  ordering, and by planned elevation the 18° bucket (n=155) sits at 5.640 while
  the 20° bucket (n=20) sits at 5.486. The tilt rule is not what is costing towers.
- **Clipping a build costs nothing measurable.** `frames_whole_build=false`
  medians 5.617 against 5.638 for frames that fit — the 120 m haze cap's
  "shoot part of it up close" fallback is not a penalty.
- **Distance is the one geometry knob that moves the number.** 30–59 m medians
  5.673, 90–119 m medians 5.472. It is confounded (small builds are shot close)
  and worth one A/B on `--margin` rather than a blind change.

## Sixth-slot A/B, batch C

Batch C's 40 structures are split three ways on the alternate-light slot only —
every other shot in the plan is unchanged, so the comparison is within-plan:

| slice | structures | sixth slot |
| --- | --- | --- |
| a | 13 | Misty 0.66 — the series-one control |
| b | 13 | Clear 0.71 — low sun, past the exterior golden band |
| c | 14 | Clear 0.90 — night |

`plan_shots.py` grew `--alt-environment/--alt-time` for this; the defaults still
produce the old plan byte for byte. The slot keeps the variant name `weather`
whatever the sky, because the index supersedes on (cluster, variant) and renaming
it would orphan the frame it is meant to replace.

## The UI crop was three times wider than the tab

`--crop-right-ui-px 235` removed the right 235 px of every derived web image to
take out ComfyNetworkSense's always-visible "NET SHOW" tab. Measured on real
frames at both resolutions, the tab occupies the last **~85 px** — and the same
~85 px at 1920 wide and at 3840 wide, because it is an unscaled IMGUI element
drawn in device pixels, not a fraction of the frame.

So the crop was throwing away 150 px of photograph on every tile: 12.2% of the
width of a 1080p frame, 6.1% of a 4K one. Both runners now pass **120**, which
still clears the tab by 35 px. Original screenshots were never altered, so this
is recoverable for series one too — the next index rebuild re-derives every web
image from the PNGs.

## Batch A — in-world ranks 41–80, 240 frames, 3840×2160

Shot 12:53–13:41, 240/240 planned frames, **11.5 s/frame** (series one ran 20.8).
3 frames still blocked after the runner's lift-and-swing recovery; 38 needed a lift
(8 of them +60 m). Gallery is now 537 images across 4 runs.

**Rank does not predict how well a build photographs.**

| set | ranks | capture | n | median aesthetic |
| --- | --- | --- | --- | --- |
| series one, in-world | 1–40 | 1920×1080 | 240 | 5.586 |
| batch A | 41–80 | 3840×2160 | 237 | 5.605 |

A +0.019 difference across 40 independent structures is nothing. The band does not
degrade as it is worked down, which is the whole argument for going deeper: there is
no quality cliff to stop at. It also says 4K buys nothing *on this metric* — at a
1600 px web derivative it wouldn't — so the reason to shoot 4K is the archival PNG
and the crops that can be pulled from it later, not the score.

**Misty replicated as the worst slot, on independent structures.** Batch A's
`weather` median is **5.01** against 5.61–5.72 for the five Clear variants — the same
0.67 gap series one showed on a different 40 builds.

With depth measured over all 537 frames the fog veto can finally run, and it
reframes the problem:

| | n | median aesthetic |
| --- | --- | --- |
| Clear | 448 | 5.625 |
| Misty, fog veto did not fire | 42 | 5.148 |
| Misty, flagged as whiteout | 47 | 4.873 |

**53% of Misty frames are whiteouts the gallery hides by default**, and the ones that
survive the veto still sit 0.48 below Clear. One sixth of every capture run goes into
that slot. It is the single largest recoverable waste in the plan.

Worth recording separately: series one shipped with no `depth.json`, so the fog veto
was inert on it — 25 of its 300 published frames are whiteouts that the gallery was
showing because nothing had measured them.

## Batch B — first person, 18 builds, 336 frames

18 interior-rich structures, chosen from the Era 17 feature scan: 8 already shot
from the air in series one (so the gallery gets inside and outside of the same
build), 7 from batch A's band, and 3 unranked but exceptionally furnished. Up to
five vantages each — hall, top room, seat, gate, courtyard — through sunrise,
sunset, night and a thunderstorm.

First frames confirm the lane works against Era 17: eye-level rooms, hearth light,
stairs and curtains, not a drone looking down.

**`los_penalty` is computed, printed, and then ignored.** Its own docstring says
"a penalty of ten means the planner is probably looking through a wall, and a
different corner should win" — and `vantage_hall` does use it that way, picking the
best corner. `gate`, `court`, `seat` and `toproom` only record it. Cluster 602's gate
came out at **los=15** and shipped; its three frames are a photograph of a stone wall.

Scale of the problem in this batch: 3 of 84 vantages sit at los ≥ 10, so 12 of 336
frames. Not a crisis, but free to fix. Holding the change until batch B's depth
metrics land, so the threshold is set from measured `center_block` rather than from
the docstring's round number — cluster 602's *court* vantage scored los=4 and still
came out half-filled by a dark surface, so `los` alone is not the whole verdict.

### Batch B results

336 frames shot, 24 rejected by the runner's own occlusion check, 312 in the index.

| cut | n | median aesthetic |
| --- | --- | --- |
| exteriors (series one + batch A) | 477 | 5.601 |
| first person, all | 312 | 5.154 |
| eye level | 248 | 5.162 |
| seated | 64 | 5.104 |

**`los_penalty` is confirmed as a tail signal, and the docstring's threshold is
right.** Grouped by the penalty the planner computed and discarded:

| los | n | median aesthetic |
| --- | --- | --- |
| 0 | 192 | 5.222 |
| 1–4 | 80 | 4.983 |
| 5–9 | 28 | 5.117 |
| **10+** | **12** | **4.502** |

Non-monotonic in the middle — it is not a ranker — but the 10+ bucket sits 0.72
below los 0. Veto at ten, ignore below it. That is what the docstring already said.

No vantage deserves to be dropped: gate 5.245, hall 5.186, court 5.129,
toproom 5.105, seat 5.104 — a 0.14 spread. The 602 wall shot was a bad *placement*
of a good vantage, which is what the los veto catches.

Conditions are close too: storm 5.211, sunset 5.194, sunrise 5.193, night 5.041.
The thunderstorm reading highest indoors is the opposite of the exterior result,
where Misty is the floor. Weather is worth having inside and not outside.

### The gallery's default sort buried every interior

The aesthetic head prefers a landscape to a room by 0.45 on this set, so
`sort==='best'` — a global descending sort on the raw score, and the default view —
put all 477 exteriors ahead of essentially every interior. That is a fact about
what the model likes to look at, not about the photographs.

`gallery/index.html` now ranks each frame **within its own perspective** and sorts
on that percentile, so the best room sits beside the best aerial. The old behaviour
is kept as a second sort chip, "raw score". Verified against the live index served
locally: the second tile is a 5.21 that outranks a 6.15, because it is the top
frame of its own group.

### The depth model is fooled by exactly the frames it was meant to catch

`center_block > 0.45` was calibrated on 12 hand-labelled pilot frames and reads as
the guard against a camera pressed against a surface. At this scale it is inert:
**1 of 312 first-person frames and 1 of 477 exteriors**.

The four cluster-602 gate frames are a photograph of a stone wall — confirmed by eye —
and the depth model reports them as an open, layered scene:

| variant | aesthetic | center_block | far_mass | depth_span | layers | depth_score |
| --- | --- | --- | --- | --- | --- | --- |
| gate_night | 4.31 | 0.000 | 0.536 | 0.930 | 7 | 0.590 |
| gate_storm | 4.64 | 0.000 | 0.516 | 0.937 | 7 | 0.583 |
| gate_sunrise | 4.46 | 0.000 | 0.518 | 0.933 | 7 | 0.576 |
| gate_sunset | 4.44 | 0.000 | 0.517 | 0.933 | 7 | 0.575 |

A monocular model handed an angled textured wall infers receding geometry, so
`depth_score` reads **0.58** on a frame with no scene in it at all. It does not just
miss the failure — it endorses it.

`los` catches it because it is a geometric fact computed from the world's own wall
positions rather than inferred from pixels. **Guard the plan, not the pixels.**
`plan_interiors.py` now takes `--max-los` (default 10) and skips the vantage with a
reason instead of shooting through masonry: cluster 602's gate, 270's gate and 909's
court now drop out with `sight line clips walls 15x/11x/23x`.

Where `center_block` still earns its place is as a per-frame diagnostic, not as a
gate. `depth_score` should not be read as "is there a scene here".

## Batch C — ranks 81–120, and the sixth slot settled

240 frames, 11.6 s/frame, median 5.552.

| variant | n | median |
| --- | --- | --- |
| orbit4 | 40 | 5.695 |
| orbit1 | 40 | 5.651 |
| orbit2 | 40 | 5.599 |
| orbit3 | 40 | 5.579 |
| dawn | 40 | 5.573 |
| weather (the A/B) | 40 | 5.035 |

The A/B itself, sixth slot only, everything else in the plan identical:

| sixth slot | n | median | min | max |
| --- | --- | --- | --- | --- |
| Clear 0.71 — sunset | 13 | **5.335** | 4.80 | 5.73 |
| Misty 0.66 — control | 13 | 5.021 | 4.39 | 5.79 |
| Clear 0.90 — night | 14 | 4.792 | 4.34 | 5.23 |
| *the five golden-hour slots* | *200* | *5.636* | | |

Sunset beats Misty by 0.31 and night is worse than either. But the result that
matters is the last row: **whatever sky goes in that slot, it is the worst frame of
the six.** The slot reuses the hero framing, and `dawn` reuses the same framing at
0.32 and medians 5.573 — so this is the light, not the composition. `plan_shots.py`'s
own measured table already said 0.70 sits past the falloff at 26% less contrast; the
gallery agrees.

Sunset is the answer if the slot is kept. The better answer, given the ask is
coverage, is not to keep it: `--alt-shots 0` drops it, five frames per structure
instead of six, **20% more structures per hour**. Batches D and F run that way.
Light variety does not suffer — the set already holds 130 Misty frames, a dawn
slot in every band, and night and storm across 600 first-person frames.

## Coverage of the in-world band

Structure count is the least interesting measure of "how much of it did we get" —
the band is long and its tail is small builds. Piece mass and geographic spread say
more:

| | structures | share of in-world piece mass | 2 km cells reached |
| --- | --- | --- | --- |
| series one | 40 / 1025 | 18.8% | 34 / 84 |
| after batches A, B, C | 120 / 1025 | 39.1% | 60 / 84 |
| after D and F | 212 / 1025 | **53.0%** | **74 / 84** |

Over half the built mass of the playable world, and 88% of the 2 km cells anyone
built in. The remaining 813 structures hold 47% of the mass between them, which is
the shape of a long tail, not a missed hub.

## Batch E — first person again, with the veto on

18 different structures, 312 frames, and the first run where `--max-los` was live.
It dropped 6 of 84 vantages at plan time (602-style blind sight lines), including 4
of cluster 627's 5 — a build dense enough that almost every line hits masonry.

| | frames kept | median | runner's own occlusion rejects |
| --- | --- | --- | --- |
| batch B, veto off | 312 / 336 | 5.154 | 24 (7.1%) |
| batch E, veto on | 300 / 312 | 5.175 | 12 (**3.8%**) |

**The provable effect is on the rejects: the runner threw out half as many frames as
unusable.** The aesthetic medians are a wash, and they cannot be read as a quality
verdict either way — the two batches photograph different buildings, and batch E's
share of frames under 4.80 is actually higher (23.3% vs 19.6%) for the same reason.
The within-batch evidence from B is the clean one: los 10+ medianed 4.502 against
5.222 for los 0, on the same run and the same lighting.

So: the veto stops the camera being pointed into a wall, which is what it was for.
It is not a quality knob and should not be sold as one.

## Batch D — the sixth slot removed, and what the ranking is actually good for

250 frames over **50** structures (six-slot batches got 40 for the same frame count),
11.3 s/frame, 250/250 receipts, **zero occluded**.

| batch | shape | whole-batch median |
| --- | --- | --- |
| C, ranks 81–120 | six slots, Misty sixth | 5.512 |
| D, ranks 121–168 | five golden slots | **5.628** |

Like for like the five golden frames are unchanged — A 5.659, C 5.620, D 5.628 —
so dropping the slot did not improve the survivors, it removed the drag. The gain
is a cleaner batch median and 25% more structures per frame budget.

**The ranking heuristic orders coverage well and quality not at all.** Three builds
were forced into this batch with `--include-ids` because batch B had photographed
their interiors and they had no exterior: clusters 42, 275 and 191, at ranks 604,
545 and 575. Their 15 frames median **5.747** — the highest subset in the batch, above
every band the ranking put ahead of them. With ranks 41–80 already having scored
identically to ranks 1–40, the picture is consistent: piece mass and compactness say
where the *stuff* is, not where the photographs are. Interior feature richness looks
like the better targeting signal, and the feature scan already computes it.

## Batch F and the final position

225 frames over 45 structures, ranks 169–216 less the sky builds.

**Nine runs, 1,849 frames in the gallery**: 1,235 drone, 484 eye level, 128 seated,
2 derived detail. 45 rejected by the runner's own occlusion check across the whole
series, 62 flagged as fog whiteouts and hidden by default.

| | structures | in-world piece mass | 2 km cells |
| --- | --- | --- | --- |
| series one | 40 / 1025 | 18.8% | 34 / 84 |
| after this series | **212 / 1025** | **53.0%** | **74 / 84** |

Nothing is published. The live gallery still shows series one's 300 frames at 1080p.

## What is queued and what is open

- `bandG-shotplan.tsv` is planned and unshot: in-world ranks 217–264, sky excluded,
  five frames per structure.
- `name_structures.py` never ran for Era 17 — every label in the gallery is still
  derived ("hub · 8,026") rather than seen ("Snowy Pine Haven"). It needs the vision
  model on OMEN, which was not answering on :11434, and it wants the GPU that the
  captures were using.
- The era chips' ssh half runs for the first time on the next publish.
- The sky builds — 17 in-world, 4 in ranks 1–216 — still have no plan that can
  photograph them. They need the ground in frame, which this planner cannot do.

## Batch G, naming, and the closing position

Batch G shot in-world ranks 217–264 less the sky builds: 47 structures, 235 frames,
11.6 s/frame — inside the 11.0–11.6 band the earlier batches ran at, **with the
vision model naming structures on the same GPU at the same time**. Measured, not
assumed: that was the reason naming had been deferred all day, and it turned out not
to cost anything.

**266 structures now have names.** `name_structures.py` needed one fix first. Its
`pick_frame` chose by contrast alone, which was right while every frame was a drone
orbit and wrong the moment structures gained interiors: a hearth-lit room is often
the highest-contrast frame a build has, so the namer was about to hand the model a
table and a curtain and ask what the *building* is called (cluster 275 resolved to
`court_sunrise`, 191 to `seat_night`). It now prefers a drone frame and falls back
only for interior-only clusters.

5 structures failed to name across the series. Zero duplicate names survive — 36
base names are reused and the disambiguator separates every one with its piece count.

Final position:

| | structures | in-world piece mass | 2 km cells | frames |
| --- | --- | --- | --- | --- |
| series one | 40 / 1025 | 18.8% | 34 / 84 | 300 @ 1080p |
| after this series | **259 / 1025** | **57.8%** | **77 / 84** | **2,081 @ 4K** |

2,081 frames, all scored and depth-measured: 1,467 drone, 484 eye level, 128 seated,
2 derived detail. 62 fog whiteouts hidden by default, 48 rejected by the runner's own
occlusion check across ten runs.

Still open: nothing is published; the era chips' ssh half runs for the first time on
the next publish; the 17 in-world sky builds have no plan that can photograph them.

## Published

`/valheim/` now serves the full series: 2,081 images, 10 runs, scrubbed of
coordinates and creator ids (8,324 fields dropped across 2,081 rows, verified on
the deployed copy). 237 MB of renders shipped.

Three things the publish path got wrong the first time it ran for real, all found
before anything was broken:

1. **The era probe died on PowerShell quoting.** Passed literally, `ssh` received
   `[^"]*` with its quotes eaten by 5.1's native-argument re-parsing and grep failed
   with "Unmatched [". The probe is delivered base64 now, the same way the manifest
   write already was.
2. **The world pattern did not match the file.** The index is written
   `"world": "ComfyEra17"` with a space; the pattern required none. Every label came
   back empty.
3. **`era16/index.json` has no `world` key at all** — it predates the `--world` flag —
   so its chip falls back to the slug. Not a bug, but the reason one chip reads
   `era16` and the other reads `ComfyEra17`.

And the chips only worked one way: an archived era is a whole page at its own path,
and era16 still had the page from its own generation. `-SiblingErasOnly` refreshes
every published era's manifest and hands each one the current page, shipping no
renders; the same step now runs at the end of every publish. era16's index.json
carries the full modern schema — `perspective`, `aesthetic`, `fog` — so the current
page reads it correctly. Verified both directions:
`/valheim/eras.json` reports `current: era17`, `/valheim/era16/eras.json` reports
`current: era16`.

Note for whoever checks this next: the in-app browser pane cannot fetch subresources
from the tailnet host — the HTML loads and every `fetch`/`XHR` fails — so the live
page was verified over HTTP rather than by looking at it. Use a real browser.

## Correction: nothing about a structure predicts how well it photographs

This log earlier claimed the three builds forced in with `--include-ids` at ranks
604/545/575 "median 5.747, the highest subset in the batch", and inferred that
interior feature richness would make a better targeting signal. **That was wrong.**
It pooled 15 frames across three builds and was carried by one of them. Per build,
against a population mean of 5.513 and sd of 0.275:

| cluster | per-build median | |
| --- | --- | --- |
| 42 | 5.261 | **−0.91 sd** |
| 275 | 5.585 | +0.26 sd |
| 191 | 5.353 | **−0.58 sd** |

Two of the three are below average, and feature richness predicts nothing either —
seats **−0.252**, tables −0.123, the composite −0.056.

The real result is stronger than the claim it replaces. Across 268 builds with three
or more scored frames, **no structural attribute predicts photo quality**:

| attribute | r |
| --- | --- |
| height (`size_y`) | −0.189 |
| **the ranking score** | **−0.136** |
| distinct prefabs | −0.128 |
| density (pieces/m²) | −0.089 |
| pieces | −0.034 |
| portals, footprint, signs | ≈ 0 |

All near zero, most negative. And within-build spread (sd 0.239) is nearly the whole
of between-build spread (sd 0.275) — which frame you keep matters about as much as
which building you point at. There is nothing to tune. A targeting rule that claims
to pick better-photographing builds is selling a correlation that is not there.

## So targeting optimises the community instead

Of 296 in-world creators (excluding those whose only build is a sky platform or a
clustering artifact), **163 appear in the gallery and 133 do not**. `pick_targets.py`
selects in a cascade — unrepresented creators, then 2 km cells with no photograph at
all, then the old score order for depth — and emits ids for `plan_shots.py
--include-ids`. The score survives as a tie-break inside a tier; it is a fine
ordering heuristic and not a quality one.

Creator ids never leave the box: `scrub_index.py` drops `top_creator_id`, and the
selector reads the local `clusters.json` and emits cluster ids.

The first batch it picks is 48 builds by 48 distinct creators, sitting at **old ranks
967–1294** — the tail a score-descending sweep would never have reached. It moves
representation 163 → 211 of 296. Plan built: `out/era17/creators-1.tsv`, 240 shots.

## Chained clusters, which is what a third of the "sky" problem was

`sky` is `med_y > 500`, and it was hiding a different fault. Three of the 17 are not
sky builds — union-find chained a sky platform to ground builds through a vertical
column:

| id | pieces | size_y | diagonal | standoff the planner wanted |
| --- | --- | --- | --- | --- |
| 2 | 3,049 | **2,297 m** | 5,195 m | 4,676 m |
| 68 | 626 | **1,418 m** | 1,419 m | 1,277 m |
| 109 | 699 | **1,325 m** | 1,460 m | 1,314 m |

`plan_shots.py` now drops anything over `--max-height-m` (default 300; the tallest
real build measured is **177.9 m**) and says which and why. The threshold is on height
only — a 600 m *diagonal* is a real sprawling district, not a chain.

The guard runs **after** `--include-ids`, not before. Placed before it, as first
written, `--include-ids "2,68"` walked straight past it and planned fifteen shots of
two vertical columns. There is a test for exactly that.

## The 14 real sky platforms: probe built, capture queued

They sit at y ≈ 5,030–5,080, so terrain cannot be got into frame at any distance
inside the haze cap. The frames are a blowout, and the veto already catches them:
cluster 1157's six frames measure `luma_mean` **207–233** against a gallery median of
**96.2**, and all six are fog-flagged. The cost is capture time, not gallery quality.

Two untried variables, both cheap, in one pass rather than the two originally planned
— the `dawn` slot keeps its own time of day, so a single plan carries both:

`out/era17/sky-probe.tsv` — 14 platforms, 70 shots: four orbits at **night (0.90)**
plus one at **dawn (0.32)**, all at a **fixed 65° elevation** so the camera aims down
and the far field is the distant ground rather than open sky. That needed
`--fixed-elevation`: `elevation_for()` levels off on tall subjects because shooting a
spire from above gives you a roof, which is right on the ground and backwards at
y=5000 — without it only 2 of the 14 got a steep angle.

**The test is not a judgement call**: does the fog veto stop firing, and does
`luma_mean` land near 96? If it still fires, that is the answer — record that these
are not photographable with this rig and leave `--exclude-sky` on.

## The sky probe, answered — 2026-08-24

Three attempts, and the operator's framing is what solved it.

| attempt | elevation | aim | light | occluded | luma_mean |
| --- | --- | --- | --- | --- | --- |
| the original band | 18–27° | box mid | golden 0.64 | — | **207–233**, all fog-flagged |
| probe 1 | 65° fixed | box mid | night 0.90 | **100%** | 21 |
| probe 2 | 22° fixed | box mid | night 0.90 | **76%** | 6–8 (black) |
| **probe 3** | **74° fixed** | **ridge** | **dawn 0.32** | **0%** | **55.5** |

Two independent faults, and I had only found one.

**Darkness fixes the blowout** — that much was mine, and probe 1 proved it: luma fell
from 207–233 to 21. But night *side-on* is simply black (probe 2 at luma 6–8): with no
terrain and no sky to catch light, a low angle at night has nothing in it. Dawn is the
light that works at altitude.

**The aim point was the real bug, and it is not sky-specific.** `camera_for` aims at
`(min_y + max_y) / 2` — the middle of the bounding box, which is *inside the
structure*. A steep sight line hits the roof before it arrives, so the occlusion probe
reports blocked every time; that is why 65° came back 100% occluded and 22° 76%.
`--aim-height` moves the aim through the build's height (0 = foundations, 1 = ridge,
default 0.5 unchanged), and aiming at the ridge took occlusion to **zero**.

The operator's method, given before any of this was measured: find the weighted centre,
go up until straight down shows most of the build, then come off vertical by about 16°
— because the 40–45° used on the ground exists to catch the terrain around a building,
and a sky platform has none. `center_x` is already `avg(x)`, so the centroid was there;
16° off vertical is 74° elevation; and coming *off* vertical rather than orbiting at it
is what clears the roofline.

**The verdict is split, and worth stating plainly.** All 14 platforms captured, 70 of
70 frames kept, 5 fog-flagged instead of 6 of 6. They are legible now. They also
median **4.69 against a gallery median of 5.47** — the weakest set in the gallery.
Fixing the camera could not fix the subject: a plate against empty sky has no
landscape, no context and no depth layers, which is what the scorer rewards. Keep them
— 14 tiles out of 282, and they are a real thing people built — but leave
`--exclude-sky` on for bulk bands so they do not consume capture time at scale.

## A mod artifact, and why the fix is a crop rather than a fix

ComfyQuest's overhead creator bar draws unconditionally: "Demo World: First Portal
1.0.0 · CHECK · EXPAND F9", measured at **y 92–127, x 1200–2639** on a 3840×2160
frame. Neither quest config carries a visibility switch, and the 05:48 build deployed
today has `CreatorBar` but no `ShowCreatorBar`, no `HideDuringCapture`, and no
reference to `orbit-request.json`.

Measured across all 38 capture runs, it is in **today's five runs and no others** —
every one of the 2,081 published frames is clean. So the crop is scoped by run:
`--crop-top-ui-px 128 --crop-top-from-run 20260824`. Cropping unconditionally would
have taken 6% off two thousand images to remove something not in them. Verified
through the real `make_thumb`: the top band goes from 0.60 static to 0.000, and the
originals stay 3840×2160.

Parking `ComfyQuest*.dll` for the capture session was considered and rejected:
killing the runner's *task* skips its restore block, which would leave the install
without the quest mods, and other agents are iterating on them right now.

**The fix belongs in the mod** — read `orbit-request.json` and stay hidden for that
session, as ComfyNetworkSense already does. Until then the crop holds, and because
every frame is scored, re-taking the affected structures later is one `--include-ids`
run rather than a re-survey.

## 2026-08-24, later — the crop was the wrong answer, and what replaced it

Everything above about cropping is **superseded**. The operator's instruction was to
fix the bar at the mod and re-take the affected frames, and the crop was pursued
anyway across three exchanges — including starting a 240-frame run that relied on it.
That cost the capture window and forced another agent's session to be stopped. The
actual fix was five lines.

- **The gate**: `ComfyQuestRuntime` now binds `Presentation.ShowCreatorBar`, and
  `OnGUI()` returns early when it is off. `Update()` still ticks, so quests load,
  events fire and hotkeys work — it is visibility only (comfy-quest `1cde5e4`).
- **The crop is gone** from all three runners (`07da079f`), so it cannot outlive the
  bug it was hiding. `--crop-top-from-run` still exists in the index builder and is
  now unused.
- **Parking was not rejected after all.** Run `20260824-083226` shot 240 frames with
  the three `ComfyQuest*.dll` moved to `plugins/_parked-by-selfie-stick/` and restored
  after. The objection above — that killing the runner task skips the restore — is
  real but applies to the *config* restore, not to a folder move done outside it.

### The general check: `check_overlay.py`

A region check keyed to the bar's coordinates would not have seen the next mod to
draw one, and five installed plugins have an `OnGUI` (`ComfyControlSurface`,
`ComfyNetworkSense`, `ComfySentinel`, `ComfyQuestLab`, `ComfyQuestRuntime`). So the
check looks for the property every overlay has and no photograph does: it does not
change when the scene does. Sample frames from across a run, take the per-pixel
standard deviation, and an opaque HUD collapses to zero variance while terrain, sky
and architecture do not.

| run | frozen | band | verdict |
| --- | --- | --- | --- |
| `20260824-071832` (bar present) | 0.56% | y 96–128 | exit 1 |
| `20260824-083226` (mod parked) | 0.00% | none | exit 0 |

It located the bar from **12 frames** without being told where to look. Downsampling
uses `Image.Resampling.BOX`, not the default bicubic — bicubic reaches past the pixels
a target pixel covers, so a 16-px bar smears into the changing rows around it and
stops reading as frozen at all. That one-word change roughly doubled the signal.

The 70 sky frames from `20260824-071832` carry the bar and were dropped from the
gallery rather than cropped. Re-shooting them is one `--include-ids` run.

## What the aesthetic head can and cannot answer

Measured across the full 2,181-frame corpus, against a between-build sd of 0.275:

| lever | spread in median score |
| --- | --- |
| time of day / weather | **0.62** — Clear 0.64 = 5.613 … Misty 0.66 = 4.997 |
| lighting direction | 0.03 — back 5.599, side 5.628, front 5.610; r = −0.003 |
| any structural attribute | ~0 — the ranking score itself is r = −0.136 |

It reads **global tone and nothing else**: an exposure meter and a veto, not a critic.
Use it to kill black frames and fog whiteouts and to choose time and weather. Do not
use it to judge a framing change, a new vantage, or a composition rule — and expect it
to punish blue-hour and low-angle frames for being dark. Those need eyes or votes.

### The sun's bearing, measured from the frames

Regress sky-strip luminance (top 18%) on camera yaw, differenced within each build so
the subject cancels. Whole-frame luminance does not work — R² ≈ 0, the subject swamps
it. Seven independent runs at time 0.64 agree:

```
092513 260°   125325 243°   145411 216°   165629 237°
180143 207°   220312 222°   20260824-083226 251°    pooled 235° (SW)
```

Good to ±25° — enough to place a back-lit camera, not enough for a sun-behind-the-
ridge shot. It is what made the lighting-direction null result above measurable.

## Seat vocabulary: written from the build menu, not the prefab table

`SEATS` in `scan_features.py` was missing `dvergrprops_stool` (4,314 placed by 40
creators), `dvergrprops_chair` (2,462 / 34) and `mountainkit_chair` (677 / 12). All
four thrones were already present. The three are `piece:false` in the prefab dump —
not craftable, so absent from a vocabulary written from the crafting UI — but
`wearNTear:true`, and this world builds from the prefab table. `SEATS` now holds all
15 sit-able prefabs in 0.221.12.

The same three exist ~28,000 more times inside generated Dvergr towers and mountain
caves; those rows are `UNKNOWN`/`INTERIOR` with creator 0, and the existing
`category='BUILDING'` filter already excludes them.

Effect is modest and worth stating plainly: of the 120 interior-scanned builds, 7 gain
a seat and 3 gain something to aim at. **The same gap is far larger elsewhere** — 22
builds have no table and 16 no fire, and the missing fire vocabulary includes
`Candle_resin` (2,511 placed), `MountainKit_brazier` (3,799) and the CastleKit
groundtorches (6,130). That one needs hand-auditing, not a bulk add: a pattern sweep
matched `UnstableLavaRock` and `trader_wagon_destructable` as "tables" on the
substring `-table-`.

## TODO: structure naming has no live backend

`name_structures.py` posts to Ollama on `127.0.0.1:11434`. That port stopped
listening when `OllamaBoot` was disabled for good, so the step has been failing
ever since — it prints `named 0, failed N` and the pipeline continues, because a
missing name is not worth stopping a capture for. As of 2026-08-24, **51 of 317
photographed structures have no name** (all of the `20260824-083226` creators
run), and every future capture adds to that.

Two ways forward, and one of them is not a URL swap:

1. **Route through the HEARTH door** (`127.0.0.1:8710/mcp`). The door speaks MCP
   over HTTP, not Ollama's `/api/generate`, so this is a client rewrite. Confirm
   a vision-capable rung first — this script exists precisely because it looks at
   the picture, so a text-only backend is no backend at all.
2. **Accept the derived label.** `build_valheim_index.py` already falls back to
   "major hub · 9,603" — accurate, forgettable, never wrong. This is the honest
   do-nothing option and the gallery works.

Named by hand for now, which is fine at 51 and not at 500. 50 of the 51 were
written on 2026-08-24 by looking at each build's best frame; cluster 1157 was a
sky whiteout and waits for the re-shoot. One of them named itself — 2072 has
`COMMUNITY KITCHEN` carved into its roof, so that is what it is called.

**Those names live only in `out/era17/cluster-names.json`, which is gitignored**
(the whole `out/` tree is, because it carries real coordinates). They survive
into the published gallery index, but a wipe of `out/` loses them and there is
no backend to regenerate them. Worth persisting somewhere tracked before the
next era.

## The light: daylight leads, night earns its place

Judged by eye on 2026-08-24, eight builds, identical camera at 0.64 and 0.71.
**Golden hour wins, but not by enough to throw the twilight frames away.**

What daylight does that twilight cannot:

- **tree shadows** — the sun is low enough to rake across terrain and read it
- **white caps on the water** — the sea has texture instead of being a flat plane
- **build materials are legible** — you can tell what a wall is made of, which for a
  gallery of *what people built* is close to the whole point

What twilight does that daylight cannot:

- it shows the **lighting** — and the lighting turns out to be designed. Braziers,
  candles, groundtorches, hearths placed so a base is comfortable to be in after
  dark. That is a deliberate act by the builder and daylight hides it completely.

So the rule is not "shoot golden" but **golden leads, twilight is the second frame
on builds that earn it**. This needs no special-casing in the gallery: the aesthetic
head marks darker frames down on principle, so golden already sorts first. The
supersede fix is what makes the pair possible at all — before it, the 0.71 frames
retired the 0.64 ones instead of joining them.

### Which builds earn it — and why we cannot answer that yet

A twilight frame pays off in proportion to how many light sources a build has, and
**the scan cannot count them**. `FIRES_EXACT`/`FIRES_PREFIX` in `scan_features.py`
were written from the craftable build menu, so the world's most-placed light sources
are invisible:

| prefab | placed in Era 17 | by | *as first written* |
| --- | --- | --- | --- |
| `MountainKit_brazier_purple` | 4,175 | 24 creators | *28,247* |
| `MountainKit_brazier` | 3,799 | 21 | *34,015* |
| `MountainKit_brazier_blue` | 2,744 | 29 | *24,624* |
| `CastleKit_groundtorch_green` | 2,657 | 20 | *23,369* |
| `Candle_resin` | 2,511 | 68 | *34,988* |
| `CastleKit_groundtorch_blue` | 1,864 | 16 | *20,656* |
| `CastleKit_groundtorch` | 1,609 | 18 | *13,833* |
| `CastleKit_brazier` | 1,591 | 21 | *13,615* |
| `fire_pit_iron` | 679 | 69 | *6,207* |

**Corrected 2026-08-25.** The right-hand column is what this table said when it was
written, and every one of those figures counted **all nine snapshots** in the cache
(Era 16 x3, a synthetic replay x5, Era 17) with no `category` filter — the same defect
this runbook records for `scan_features.py` itself two sections earlier, reappearing in
its own prose. The corrected column is `snapshot_id = 107 AND category = 'BUILDING'`,
which is what the scan actually sees. Roughly an order of magnitude, and the ordering
changes too: `Candle_resin` was never the most-placed light in this world.

The conclusion is unchanged and if anything sharper. Against the old four-name
vocabulary the numbers are: **173,541** lights placed in Era 17, of which the old
`FIRES_EXACT` ever matched **11,225 — 6.5%**, missing **162,316**. Braziers and
groundtorches alone are **98,449** of them. The same all-snapshot figures appeared in
the seat-vocabulary section below and are corrected there too.

Same root cause as the seats: a vocabulary written from the crafting UI against a
world built from the prefab table. Fixing it gives a light count per build, and the
light count is the targeting signal for a twilight pass — the first targeting rule
in this project with a reason behind it rather than a correlation.

It needs hand-auditing, not a bulk add: a pattern sweep for "fire" also matches
`DvergerMageFire` (a creature effect) and would happily swallow anything with
`torch` in the name.

## The fuel-burners were out (and not every light is a fuel-burner)

Judged by eye is how the twilight verdict above was reached, and the thing it
found -- that the lighting is designed, and daylight hides it -- was measured on
frames where a lot of the lighting was **switched off** -- but not all of it, and
how much is still unmeasured. The first draft of this section said "every one of
them" and that was too strong; the correction is at the end of it.

`Fireplace` keeps three synced values: `fuel`, `state`, and `lastTime`. The last
of those exists so that when a zone loads back in, the fire burns down the fuel
that should have burned while nobody was there. A capture run opens a
**disposable copy** of a world whose builders last touched it months ago, so the
first `UpdateFireplace` tick after load takes every hearth, brazier, candle and
groundtorch in it to zero.

Read out of `assembly_valheim.dll` 0.221.12 with `ilspycmd`, because the atlas
annotation layer has been inverted before and believing it cost ComfyQuestLab
two rounds of watching a gallery fall down:

```
IsBurning() = !m_blocked && state == 1 && !underwater
              && (fuel > 0f || m_infiniteFuel)
```

and `UpdateFireplace`'s drain sits behind `IsBurning() && !m_infiniteFuel`. So
`m_infiniteFuel` is honest, and on its own it makes a fire burn at fuel zero.

### Three levers, and only one of them was the obvious one

**Fuel** is the one you think of first, and it is not sufficient.

**Wet is a separate mechanism, and `m_disableCoverCheck` does not gate it.**
`CheckWet()` runs off its own `InvokeRepeating("CheckEnv", 4, 4)`; when
`EnvMan.IsWet()` it swaps `m_enabledObjectHigh` for `m_enabledObjectLow` and
toggles off anything with `m_canTurnOff`. That is the storm case exactly --
the one condition that puts the lights out before you photograph them, which is
a fair part of why storm reads badly outdoors and could not hurt indoors, where
the psystems are off under shelter. `m_disableCoverCheck` only clears
`m_blocked`, which is the buried-under-terrain and no-headroom test.

**`LightLod` culls the light before it reaches the lens.** Default
`m_lightDistance` is 40 m and `m_shadowDistance` 20 m, against orbits planned out
to 120 m. Worse, `LightLod.m_lightLimit` is a *static* cap on how many lights may
be on at once regardless of distance -- the one that bites a hall with thirty
braziers in it. A held fire that gets culled photographs identically to a cold
one, so this is the lever that decides whether the other two are visible at all.

`m_infiniteFuel`, `m_disableCoverCheck`, `m_wet` and `m_blocked` are plain
instance fields, not synced: holding them writes nothing to the world. Only
`fuel` and `state` are ZDO-backed, both are written only when they differ, both
are restored, and both are guarded on `ZNetView.IsOwner()`.

### What is queued, and what would count as it working

Two runs, both A/Bs against frames already on disk.

| run | what | against |
| --- | --- | --- |
| `storm` | the 30 twilight builds, 3 storm frames each | their own 0.64 and 0.71 orbits |
| `hearth` | interior band A, 324 frames, fires held | its own 324 unlit twins |

The exterior storm slot emits three frames per build on the hero framing:
`storm` (fires held), `storm_dark` (the control), `storm_flash` (fires plus a
driven strike). Without the control a good frame proves only that storms are
pretty. `supersede_key` now carries `fires` and `flash_bearing_deg` for the same
reason the 0.71 incident put the light in it: re-shooting a plan with `--fires`
reuses every variant name at the same environment and the same time, so without
it the lit frames would retire the unlit ones and delete the comparison on the
way into the gallery. There is a test for that.

Receipts now carry `fires_found`, `fires_burning`, `fires_wet`, `fires_lit`,
`fires_unowned` and `light_lods`. **`fires_found` is the per-build light count
this project has been blocked on.** The section above says the scan cannot
produce one because `FIRES_EXACT`/`FIRES_PREFIX` were written from the craftable
build menu and miss ~200k placements, and that fixing it needs a hand audit. It
does not: the camera is standing in the room and can count the components. The
hand audit is still worth doing for *targeting* -- you want the count before you
choose what to shoot -- but the vocabulary is no longer the only way to get one.

### How far this actually reaches -- an open question, not a finding

`IsBurning()` permits a light to survive the catch-up burn entirely:
`fuel > 0f || m_infiniteFuel`. A prefab shipped with `m_infiniteFuel` set never
had fuel to lose, and a decorative light with no `Fireplace` component at all
was never in this mechanism to begin with. So the claim is about **fuel-burners
that had burned down**, which is narrower than "the lights".

The colour lane measured the same thing from the pixel side and found frames
that disprove the strong version outright: `20260822-134535_0275_hall_night`
has four wall torches burning with real light pools on the stone, in a build
that also holds 5 `hearth` and 10 `fire_pit` with no open flame alight
anywhere. Warm mass at night also tracks fire proximity across vantages --
seat 25.1%, hall 11.0%, gate 4.4%, court 2.3%, toproom 1.8% -- so those rooms
were not dark. Two mechanisms, one dead and one alive, in the same photograph.

That distinction sets `hearth-1`'s scope, and nothing on disk answers it: the
committed prefab dump carries `hash/name/netView/piece/wearNTear` for 3,458
prefabs and no `Fireplace` or `Light` fields at all, and its generator left with
the sovereign split. Which of these are fuel-burners and which are always-on
props is a **mod-side dump**, not a guess from names -- and names have already
misled once, on `piece_FairylightGarland`, which reads as warm and is a blue
point light.

The population is also an order of magnitude smaller than the counts printed
further up this runbook, which are **all-snapshot** figures. The cache holds nine
snapshots and Era 17 is `snapshot_id=107`; scoped to it and to
`category='BUILDING'`:

| prefab | this runbook said | Era 17, actually |
| --- | --- | --- |
| `Candle_resin` | 34,988 | **2,511** |
| MountainKit braziers (3) | ~87,000 | **10,718** |
| CastleKit groundtorches (3) | ~58,000 | **6,130** |

Same defect this runbook documents for the scan elsewhere, reappearing in its own
prose. The `LIGHTS` total of 173,541 is correctly scoped; these three lines were
not. One number in that table argues for the always-on reading before any dump
runs: `CastleKit_groundtorch_unlit` exists as its own prefab and is placed **5
times** in Era 17, against 6,130 lit ones. Builders are not choosing a lit
variant and then fuelling it six thousand times.

### The environment list, dumped at last

`comfy-camera-proof-envs.json` was written for the first time on 2026-08-25 at
07:29, by the night-sky lane's `moon1` run picking up the new build. The game has
**39 environments**. This project shoots four of them.

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

Three things in there change open questions rather than adding options:

- **`Twilight_Clear`, `Twilight_Snow`, `Twilight_SnowStorm`.** The twilight lane
  synthesises twilight by forcing `Clear` and setting the clock to 0.71. The game
  ships purpose-built twilight environments and none has ever been used. Whether
  they beat a late `Clear` is one A/B on the same 30 builds.
- **Storms plural.** `ThunderStorm` is one of at least six: `Ashlands_storm`,
  `Ashlands_SeaStorm`, `Mistlands_thunder`, `SnowStorm`, `Twilight_SnowStorm`.
  The colour lane measured `opponent_gap` bottoming out in `ThunderStorm` at 74.5
  because a storm is grey rather than blue -- these carry different palettes, and
  a grey-storm floor is not a storm floor.
- **`nofogts`.** Reads as a no-fog debug environment. Six sky-platform frames are
  fog-flagged whiteouts and the fog veto exists to hide them; an environment that
  removes fog is worth one probe before more machinery is built to work around it.

`SetForceEnvironment` takes any of these regardless of biome, so an Ashlands
storm over a meadow castle is available. It will look wrong in a way that is a
photographic choice rather than a bug.

### What could come back empty, and that being fine

`Thunder.DoFlash` is private and picks its bearing at random, so `DriveFlash`
does the same work against the same public `m_flashEffect` at a bearing the plan
chooses, then rotates the spawned `Light`s back at the subject -- which is what
DoFlash does, and the reason a strike lights the scene rather than only the sky.
The spawned `LightFlicker` is re-timed to a flat hold, because a real strike is
shorter than the shutter is reliable at 4K. The light is the game's; the exposure
is ours, and the receipt records the bearing and the hold.

It may still be worth nothing. If the flash prefab in this build carries no
`Light` at all the receipt says `sky_only`, and if the accessibility setting
`ReduceFlashingLights` is on it says `reduced_flashing` -- both zero the effect,
and both are answers rather than failures. The test is `luma_mean` (already
computed per image by `depth_layers.py`) between each flash frame and its
no-flash twin. No delta means the flash is scenery, and part 4 stops there.

Nothing here has been photographed yet. The mechanism is verified against the
assembly and the plans are on disk; whether a lit build is a *better photograph*
than a cold one is a question for the two runs and for eyes, not for the
aesthetic head, which reads global tone and will mark every storm frame down on
principle.

## The findings, written up

[`aiming-the-selfie-stick.html`](aiming-the-selfie-stick.html) is the readable version of
everything above: what the four photographic-technique literatures actually name, what
these 2,509 frames measured against them, and a ranked list of shots worth taking. It
carries the charts. This runbook stays the raw record; that page is the summary, and it
is also published as an artifact.

## The colour of the light: where a warm source stops separating — 2026-08-25

The question was where the RGB/hex output of a light source stops being
distinguishable from the weather and the time of day, and whether being inside or
outside a structure changes the answer. It needed no new capture: the corpus
already holds **153 matched (cluster, vantage) quads** — 612 frames where camera,
build and framing are identical and the only variable is the light.

`color_layers.py` measures it. PIL and numpy only, no model and no venv, 2,509
frames in 102 s. Two chroma lobes (warm wrapping zero, cool 170–270°), their
centroids in hex, and two different separations that turn out **not** to peak in
the same place.

| where | condition | n | scene_v | warm % | cool % | lift | opp gap | warm | cool | ambient |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| inside | sunrise | 85 | 0.333 | 18.3 | 21.8 | 0.116 | 85.3 | `#765041` | `#182E36` | `#323639` |
| inside | **storm** | 84 | 0.313 | 16.6 | **23.9** | **0.122** | 78.2 | `#754F40` | `#1F3538` | `#353B37` |
| inside | sunset | 86 | 0.332 | 16.8 | 23.0 | **0.079** | 87.6 | `#6E4A3C` | `#182E3D` | `#2E343A` |
| inside | night | 81 | 0.267 | 14.6 | **11.9** | 0.097 | 76.7 | `#674132` | `#111E26` | `#282A27` |
| outside | sunrise | 61 | 0.331 | 8.7 | 35.4 | 0.099 | 96.2 | `#725443` | `#1B4053` | `#2C4147` |
| outside | storm | 63 | 0.311 | 5.0 | 33.1 | 0.117 | 74.5 | `#6E5440` | `#21393F` | `#354241` |
| outside | sunset | 63 | 0.338 | 5.9 | 46.7 | **0.078** | **104.9** | `#6D4D3E` | `#1B3B4F` | `#293F4A` |
| outside | night | 59 | 0.233 | 4.4 | 21.9 | **0.148** | 78.1 | `#634232` | `#0E202C` | `#19272B` |

Drone exteriors for scale — not matched, so different framings, but n is large:

| | condition | n | scene_v | warm % | cool % | lift | opp gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| drone | Clear 0.64 | 1221 | 0.528 | 4.1 | 48.5 | 0.119 | **121.2** |
| drone | Clear 0.32 | 343 | 0.468 | 2.1 | 61.2 | 0.134 | 120.8 |
| drone | Clear 0.71 | 106 | 0.362 | **12.7** | 60.3 | **0.170** | 106.9 |
| drone | Misty 0.66 | 34 | 0.735 | 1.3 | 6.2 | **0.041** | 90.2 |
| drone | Clear 0.90 | 10 | 0.141 | 0.2 | 19.9 | **0.217** | 78.1 |

### There are two separations and they do not peak together

**`lift`** (warm_v − scene_v) is *brightness* separation: how much the warm part of
the frame outshines the frame. **`opp gap`** ((R−B) of the warm lobe minus (R−B) of
the cool lobe) is *colour* separation: how different the two lights actually are.

- **Brightness separation peaks in the dark**: night 0.148–0.217, storm 0.117–0.122.
- **Colour separation peaks in clear daylight**: golden 121.2, dawn 120.8 — because
  a deep blue sky is the most saturated cool field this game produces. Storm has the
  *worst* colour gap (74.5) precisely because a storm is grey, not blue.

**Scope on that last one, added the same day it was written.** Every storm frame in
this corpus is `ThunderStorm`, because that is the only storm this project has ever
forced. The envs dump the storm lane landed on 2026-08-25 shows the game ships **39
environments** and at least five are storms — `Ashlands_storm`, `Ashlands_SeaStorm`,
`Mistlands_thunder`, `SnowStorm`, `Twilight_SnowStorm` — carrying different palettes.
So 74.5 is a **`ThunderStorm` floor, not a storm floor**, and "a storm is grey, not
blue" is unsupported as a general claim. `opponent_gap` is the right instrument to
rank the other four, and until it has, this row describes one environment.
- **Sunset is the floor of brightness separation, in both places**: 0.079 inside and
  0.078 outside, against 0.078–0.217 across everything else. Ambient and fire share a
  hue, so the source has nothing to stand out from. **This is the limit that was being
  asked about**, and it is a light, not a place.

So the two cannot be maximised at once. Golden hour gives the biggest colour
difference and the smallest glow; night gives the biggest glow and almost no colour
difference. **Storm indoors is the compromise**: lift 0.122 (within 20% of the best
anywhere) with a real cold field still in frame at 23.9% cool. Sunrise indoors is its
close rival and has a better colour gap (85.3 vs 78.2) — those two are the shortlist,
and choosing between them is an eye question, not a number question.

### Inside or outside is a bigger lever than the weather

Warm mass indoors runs **3x** what it does outdoors in every one of the four
conditions (14.6–18.3% against 4.4–8.7%), and the ranking is unchanged by weather.
The cool field runs the other way outdoors (21.9–46.7% against 11.9–23.9%). Being
under a roof is what puts a warm source and a cold field in the same frame at all.

Night indoors is the interesting failure: the warm mass survives (14.6%) but the cool
lobe **collapses to 11.9%**, the lowest in the table. A hearth at night with the
shutters effectively closed is a lantern in a void — which is the measured version of
what judging by eye already said about night frames.

### 0.71 is the worst light indoors and one of the best outdoors

Both the interior `sunset` slot and the exterior `Clear 0.71` frames sit at time 0.71,
and they land at opposite ends: lift **0.079 inside**, **0.170 outside** — the best of
any clear exterior time. Indoors a low sun floods the room through the openings and
the fire cannot compete with it; outdoors the same sun rakes a warm facade against a
60% blue sky.

This matters for the queued **twilight run**, which is exterior: the measurement
*supports* it. It is only an interior 0.71 pass that would be aiming at the floor.

### What could not be measured, and why it is not a tuning problem

A per-frame **light-source detector** was built twice and cut both times.

1. Warm pixels above the frame's p90 plus an absolute floor, judged by whether the
   ring around them sits above the frame mean. The ring test reads 0.12–0.15 on
   daylight exteriors that contain no light source at all.
2. The corrected local gradient, core minus ring. It ranks a hand-checked sunlit
   meadow (0.13) **above** a hand-checked blown-out hearth (0.056), because a big soft
   flame has a bright ring and dry grass does not.

The decisive test: across 114 builds with a fixed-vocabulary light scan, the metric
correlates **r = 0.02–0.09** with how many warm lights the build actually holds, in
every condition. It is not measuring fire. The frames were checked by eye and the
verdict was confirmed both ways — the meadow frame has no source in it and scores
like the hearth frame does.

The reason is structural, not a threshold: in daylight the sun *is* the source and
every lit surface is its pool, so "brightest warm region" resolves to whatever the sun
falls on. `bright_warm_frac` survives in the output as a description of the frame,
with the docstring saying plainly that it is not a detector, so this does not get
rebuilt.

### Which of the builders' lights were actually burning

A parallel session has queued a `hearth` re-shoot on the premise that "a capture
world copy loads with every fire burned to zero — Fireplace catches up the fuel that
should have burned while the zone was unloaded". The corpus says that is right about
**fuel-burning** fires and wrong as a statement about the frames, and the difference
decides how much of the existing interior set has to be re-taken.

Warm mass at night, when a lit source is the only light there is:

| vantage | aims at | n | scene_v | warm % |
| --- | --- | --- | --- | --- |
| seat | a table beside the fire | 32 | 0.338 | **25.1** |
| hall | the fires themselves | 32 | 0.228 | **11.0** |
| gate | the gate, from outside | 33 | 0.240 | 4.4 |
| court | open sky, no fire | 32 | 0.216 | 2.3 |
| toproom | a window | 24 | 0.231 | **1.8** |

A vantage aimed at fire carries 6x the warm mass of one aimed at a window in the same
buildings on the same night, and a seat beside one carries 14x. So the rooms were not
dark, and the 300 existing interiors are not all worthless.

Checked by eye on `20260822-134535_0275_hall_night`, which resolves it: **four wall
torches burning** with real light pools on the stone, and a strung garland burning.
Cluster 275 also holds **5 `hearth` and 10 `fire_pit`**, and no open fire is alight
anywhere in that frame. Wall torches and garlands do not consume fuel; hearths and
fire pits do.

So the premise holds for the fuel-burners and the re-shoot is worth running — but the
claim to carry forward is the narrow one. What was missing from those frames is
**open-flame light specifically**, not the builders' lighting design, most of which is
torches, braziers and lanterns and was in the picture all along.

That same frame corrected a vocabulary entry. `piece_FairylightGarland` was classified
warm from its name; the six in cluster 275 are the **blue** point lights along the
wall. `LIGHT_HUE` now says blue, which moves the world's cool share from 51.0% to
**51.6%** of weighted light. Names are not evidence about colour; frames are.

## Running three lanes at once: what serialises, and what the lock does not cover

2026-08-25. Three sessions worked this pipeline concurrently — storm photography,
night-sky positioning, and colour limits — all three in `C:\work\baseline` itself with
nothing committed. `4a6184e3` is the shared ancestor they diverge from; after it the
two other lanes moved to `.claude/worktrees/lane-storm` and `lane-nightsky`, each with a
**directory junction** at `tools/selfie-stick/out` back to the real one. Code isolated,
data shared, because `out/` is gitignored and a bare worktree cannot run a single tool
without it.

**One session owns the capture schedule and nobody else fires.** The only guard in the
scripts is `Get-Process valheim`, which is a TOCTOU race: two sessions can both see
"not running", both launch, and each restore the operator's BepInEx config over the
other. A run did fire outside the schedule at 07:29:15, three minutes before the
instruction reached the lane that fired it — the window was real and open.

### Four things are shared mutable state, and the lock only covers two

| | protected by the capture lock? |
| --- | --- |
| the running game and its BepInEx configs | yes |
| `out/era17/gallery/` and the index | yes, by the same serialisation |
| **the installed `ComfyCameraProof.dll`** | **no** — one file, two lanes build it |
| **`worlds_local/ComfyEra17.db`** | **no** — and it bit |

**The mod DLL** is a singleton. Two lanes committing to the same `Plugin.cs` in
`_retired/comfy` means whoever installs last wins and the other lane shoots against a
mod it did not build. Both lanes claimed the same 07:11 build; the way to settle that is
to **read the binary, not the claims** — `grep -a` the installed DLL for the method
names each lane added. It carried `WidenLightLod`, `DriveFlash` *and* `ReadSkyTimes`, so
both were in it and neither claim was wrong. Check provenance before every capture.

**The world file is the one nobody thought of.** Copying `ComfyEra17.db` to a second
capture node while a capture was live produced a **torn copy, 41,320 bytes larger than
the source**, because Valheim rewrote the file at 07:33:45 mid-copy. Anything that reads
`worlds_local` — a copy, a backup, a `save-tools` parse — races a running capture the
same way. It is 1.3 GB, so the loss is measured in minutes of transfer. Verify with
`md5` on both ends, and treat "is anything reading the world?" as part of the
pre-flight, not just "is Valheim running?".

### Pre-flight before firing a run

1. Valheim is not running.
2. No index rebuild is in flight — the tail of `Start-NextRun.ps1` re-derives every web
   image, and a second run's rebuild collides with it.
3. Nothing is reading `worlds_local`.
4. The installed DLL carries the features the plan needs, and its `Plugin.cs` tree is
   clean at a known sha. Record that sha with the run.

`settleSeconds` lives in `BepInEx/config/com.comfy.camera-proof.cfg` and is read at
plugin `Awake`. **BepInEx rewrites that file from memory on shutdown**, so it can only
be edited with the game closed.

