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
