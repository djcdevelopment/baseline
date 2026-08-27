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

### The occlusion check cannot see a building

Third instrument, same shape, and this one is in the mod rather than in a model.
`IsOccluded` raycasts against `LayerMask.GetMask("terrain", "static_solid",
"Default")`. Player-placed pieces are on the **`piece`** layer, and the same file
proves it: `PiecesNear`, twelve lines below, masks `("piece", "static_solid")` to
count them. So the occlusion check is blind to player builds, and returns
`occluded=false` with the lens flat against masonry.

The night-sky lane found it the expensive way: 16 frames back with
`clearance="planned"`, `occluded=false` and `pieces_near_aim` up to 30,930 --
mechanically flawless receipts -- of which four are a photograph of cluster 182's
own diamond lattice. `FindClearView` is built entirely on `IsOccluded`, so the
whole lift-and-swing recovery shares the blindness.

The docstring is honest about what it does ("a shot straight into a hillside")
and the receipt field is called `occluded`, which is not. The gap between those
two is the whole bug.

**What it does and does not touch.** Exterior orbits stand off at up to 120 m,
where the blockers are trees and hillsides -- which the mask does cover, and
demonstrably: 4% of frames needed recovery and six of eight successful lifts
landed at +40 m, which is tree-clearing behaviour. So occlusion-reject rate
remains a valid objective read for exteriors, including the settle A/B. It is
**not** usable on interiors, where the camera is inside the geometry the mask
cannot see; there the guard is `los`, computed from the world's own wall
positions. It also qualifies the batch B/E reject-count comparison above, which
was measured on first-person interiors -- whatever those rejects caught, it was
terrain and static geometry, not builds. That conclusion survives because it
rested on within-batch `los`, not on the reject counts.

**Deliberately not fixed.** Adding `"piece"` to the mask is a one-word change
that would break every exterior orbit, because an orbit aims *at* a build and
would then report its own subject as an obstruction and start lifting and
swinging away from it. The `dist * 0.85f` shortening is not nearly enough slack
for a 100 m structure. A real fix needs to distinguish the subject's own pieces
from everything else, and then the whole corpus needs re-baselining against the
new reject rate. That is a lap of its own, not a patch.

Three instruments now, three failures, one shape: `--max-los` caught what
`center_block` endorsed, `depth_score` read 0.58 on a photograph of a stone wall,
and `IsOccluded` reports clear against masonry. Every one of them was a
pixel-or-proxy measure standing in for a geometric fact the world already knew.
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

  **Correction, 2026-08-25: moving a DLL into a subfolder of `plugins/` does not park
  anything. BepInEx scans `plugins/` recursively.** Verified from `LogOutput.log` during
  a live capture, with all three DLLs sitting in `_parked-by-selfie-stick/`:

  ```
  Loading [Comfy Camera Proof 0.2.0]      Loading [ComfyNetworkSense 0.5.80]
  Loading [ComfySentinel 1.5.0]           Loading [ComfyQuestLab 0.2.0]
  Loading [ComfyControlSurface 0.6.0]     Loading [ComfyQuestRuntime 0.1.0]
  ```

  Both quest mods load and Harmony-patch the game during every capture —
  `MineRock.Damage`, `Pickable.Interact`, `Pickable.RPC_Pick` among others. Any
  conclusion in this file that rests on "the mod was parked" needs re-reading; that
  run's frames were never protected by the folder move.

  **They are clean for an unrelated reason**, which is why nobody noticed. The setting
  was renamed rather than removed — the config now reads
  `## Legacy creator-surface key; migrated into CreatorBarHotkey.` with
  `CreatorBarHotkey = F9`, and the runtime logs `Runtime ready. CreatorBar=F9`. The bar
  is **hotkey-toggled**, nothing presses F9 during an unattended run, and the camera
  mod's own bindings are the arrow keys. That is also why all 2,525 existing frames are
  clean. The unconditional bar belonged to an older `ComfyQuestRuntime`.

  To actually unload a plugin, move it **out of the `plugins/` tree entirely**, not
  into a subfolder of it.

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
toggles off anything with `m_canTurnOff`. `m_disableCoverCheck` only clears
`m_blocked`, which is the buried-under-terrain and no-headroom test.

**Corrected 2026-08-25 by the light dump: this lever is almost inert, and two of
us leaned on it.** The IL is right about what `CheckWet` does; what neither of us
checked is *how many prefabs it can reach*. Of the 43 in the light vocabulary,
exactly **one** carries `m_canTurnOff = true` — `Candle_resin`, whose light is
`intensity 2.0 x range 1.0`, the weakest emitter in the set. Sixteen have a
`Fireplace` with `m_canTurnOff = false`, so weather cannot touch them, and
**twenty-one have no `Fireplace` component at all**, so weather is irrelevant to
them. `bonfire` (range 20), `piece_groundtorch` (15), `piece_walltorch` (12) and
both fire pits (10) all stay lit straight through a thunderstorm.

This retracts a claim the colour lane published off the back of this paragraph:
that measured warm mass of **5.0% outside in a storm against 16.6% inside** was
`CheckWet` extinguishing the outdoor fires, "mechanism and measurement agreeing".
The measurement stands and the mechanism does not — `CheckWet` cannot produce an
effect that size when it reaches one candle. The inside/outside gap is real and
its cause is still open; the obvious remaining candidate is simply that an
outdoor storm frame is mostly grey sky and wet ground while an indoor one is
mostly warm material. Same error class as the 41,320-byte copy: a real
observation attributed to a mechanism that cannot generate it.

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
buildings on the same night, and a seat beside one carries 14x.

**Corrected the same day: that gradient does not show what it was read as showing.**
The storm lane asked whether it could be interiority re-expressed rather than fire
proximity. Tested by holding enclosure constant — working *within* a single vantage, so
geometry and framing are fixed and only the build's own light count varies — warm mass
does not track how many warm lights a build holds:

| vantage | warm mass | r(warm %, warm_lights) | n | t | p |
| --- | --- | --- | --- | --- | --- |
| seat | 25.1% | −0.018 | 32 | −0.10 | 0.92 |
| hall | 11.0% | +0.112 | 32 | +0.62 | 0.54 |
| gate | 4.4% | +0.278 | 33 | +1.61 | 0.12 |
| court | 2.3% | +0.393 | 32 | +2.34 | **0.026** |
| toproom | 1.8% | −0.021 | 24 | −0.10 | 0.92 |

**These are five nulls, one of them noisier than the rest.** Only `court` clears p<0.05,
and across ten tests (five vantages × two conditions) a Bonferroni threshold is 0.005,
which it does not approach. Nothing here is significant.

A first draft of this correction argued from the *ordering* — most warm mass, least
relationship — and that argument does not survive contact with the table: `seat` has the
most warm mass at r = −0.018 and `toproom` has the least at r = −0.021. Those are the
same number at opposite ends of the gradient, so the ordering is not monotonic and the
inversion was doing rhetorical work the data does not support.

**The conclusion stands on a narrower and better argument.** `hall` and `seat` are the
two vantages that *aim at fires* — `vantage_hall` scores a floor band ×1.5 for holding
one and aims at the fire centroid — and they return r = −0.018 and +0.112. A detector
pointed at the thing it is supposed to detect, correlating with nothing, is the whole
result. The gradient is not needed and should not be leaned on.

**And the null is weaker than it looks, for a reason worth stating.** `warm_lights` is a
per-*build* count while a vantage sees a fraction of the build: thirty braziers spread
over 100 m put almost none of themselves in a seat frame. The predictor is mismatched to
the measurement, so some of this null is guaranteed by construction. That is an argument
against over-reading it, not against the conclusion.

**The better test needs no new capture.** Every `storm-1a`/`1b` receipt carries
`fires_found` — Fireplaces within 80 m of the *aim point*, per shot — which is far closer
to "lights in frame" than a whole-build vocabulary count. Correlating warm mass and
`bright_warm_frac` against per-shot `fires_found` across those 90 frames tests the
instrument rather than the vocabulary. `fires_found` is itself biased — an 80 m radius
rather than a frustum, so it counts fires behind the camera — so it is a better proxy and
not a good one. The clean version is lights within the view cone, which the mod could
compute and does not.

**What this changes in practice:** `warm_frac` is a poor instrument for fire and a good
one for enclosure. For a fires-on/off comparison at fixed camera and fixed sky,
`bright_warm_frac` is the separating metric — a lit hearth at 3 m in a dark room is warm
*and* bright, while a table 0.35 m from the lens at night is warm and not bright. Its
docstring saying it is not a fire detector remains true; it detects bright warm regions,
which is a different and here more useful thing. So the rooms were not
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

**The world file is the one nobody thought of, and it failed two ways at once.**
Copying `ComfyEra17.db` to a second capture node while a capture was live produced a
destination **41,320 bytes larger than the source**. Two distinct mechanisms were in
play and it is worth keeping them apart, because only one of them looks like a failure:

1. **The source moved under the read.** Valheim rewrote the file at 07:33:45 mid-copy.
   Anything that reads `worlds_local` — a copy, a backup, a `save-tools` parse — races a
   running capture the same way.
2. **`scp` does not truncate the destination.** Writing 1,299,599,565 bytes over an
   existing 1,299,640,885-byte file leaves the last **41,320 bytes** of the old file
   in place. That arithmetic is exact, and it is the mechanism that explains the number
   observed. It is the nastier of the two: the result passes a size check, passes a
   "the transfer completed" check, and is silently wrong.

3. **Three writers, one destination.** Killed transfers do not always die. A shell that
   is killed leaves its `scp` children running, so "I killed it" is a statement about
   intent rather than about the process table — verified live: two `scp` processes were
   still reading the live world minutes after being reported dead, while a third wrote a
   frozen snapshot to the *same* destination path. Three concurrent non-truncating
   writers into one file produce interleaved garbage that passes a size check, passes a
   "transfer completed" check, and passes casual inspection.

So `rm` the destination first, and verify with `md5` on both ends rather than by size.
"Is anything reading the world?" belongs in the pre-flight next to "is Valheim
running?" — but the better fix is to stop the two contending at all. **Copy from a
frozen backup snapshot, never from the live world.** A `*_backup_auto-*.db` plus its
`.fwl` is a day older, which changes fuel, `lastTime` and player position and moves no
build, and cluster ids come from `clusters.json` regardless. A capture node has no
business reading a file the game is actively writing.

### Pre-flight before firing a run

1. Valheim is not running.
2. No index rebuild is in flight — the tail of `Start-NextRun.ps1` re-derives every web
   image, and a second run's rebuild collides with it.
3. Nothing is reading the **live** world file. Not "nothing is reading
   `worlds_local`" — the backups live there too, and a transfer from a frozen
   snapshot is exactly what you want. Check **command lines**, not process names:
   `Get-CimInstance Win32_Process -Filter "Name='scp.exe'"` and read what each one
   is actually copying.
4. The installed DLL carries the features the plan needs, and its `Plugin.cs` tree is
   clean at a known sha. Record that sha with the run.

`settleSeconds` lives in `BepInEx/config/com.comfy.camera-proof.cfg` and is read at
plugin `Awake`. **BepInEx rewrites that file from memory on shutdown**, so it can only
be edited with the game closed.

### The rule all four steps are instances of

**Verify state, not the report of the command that was supposed to change it.**

Every check above earned its place by catching something that had already been
reported as fine:

- Two lanes each claimed the same mod build. Reading the installed binary for the
  method names each had added showed it carried *both*, so neither claim was wrong and
  neither was sufficient. **The binary over the claim.**
- A transfer was reported killed. Two of its `scp` children were still reading the live
  world minutes later, because what died was the wrapper shell — the job-control stop
  returned success and reaped neither child. **The PID over the kill.**
- Sixteen frames came back `clearance="planned"`, `occluded=false`, `pieces_near_aim`
  up to 30,930. The moon is in zero of them, because `IsOccluded` masks `terrain`,
  `static_solid` and `Default` while placed pieces sit on the `piece` layer. A receipt
  that says the shot was clear is a statement about what the raycast could see.
  **The photograph over the receipt.**
- Three DLLs were in a folder named `_parked-by-selfie-stick`. Checking the directory
  was the right instinct and still gave the wrong answer, because the question was not
  "what is in `plugins/`" but "what did BepInEx load" — and it loads recursively. Only
  `LogOutput.log` answers that. **The loader over the directory.**

That is the same lesson this runbook already records three times from the other
direction — `--max-los` catching what `depth_score` endorsed, `depth_score` reading
0.58 on a photograph of a stone wall, and the atlas annotation layer inverted against
the IL. Guard the plan, not the pixels; and check the thing, not the report of the
thing.

## The storm A/B, the settle A/B, and a bar that burned two runs — 2026-08-25

Three runs shot through a single scheduling session: `nightsky` (30 frames),
`storm-1a` (45, settle 6) and `storm-1b` (45, settle 3). All three verified clean with
`check_overlay.py` before anything was read off them. Two earlier attempts at the storm
halves — 61 frames — were dropped, not cropped; see the creator-bar section below.

### settleSeconds 3 is safe and it is 29% faster. Adopt it.

Frame cadence had a **10.0 s floor rather than a distribution** (median and p10 both
10.0), and all of it was configured sleep. The principled floor is ~3 s: `UpdateFireplace`
ticks every 2 s and `LightLod` re-reads on a 1 s coroutine. Tested by splitting the same
30 builds **interleaved by rank** — not halved, because `twilight-1` is rank-ordered and
rank tracks build size, so first-15/last-15 would have measured subject difficulty.

| half | settle | frames | occluded | median gap | aesthetic | depth |
| --- | --- | --- | --- | --- | --- | --- |
| 1a | 6 | 45 | **0** | 10.24 s | 5.465 | 0.566 |
| 1b | 3 | 45 | **0** | **7.24 s** | 5.498 | 0.497 |

**Zero occlusion rejects in both halves** — the objective measure, and it shows no
degradation. 7.24 s against 10.24 s is the 3 s saving landing exactly where predicted,
29% off every frame in the queue.

The predicted failure mode did not appear. If 3 s missed the 2 s `UpdateFireplace` tick,
frames would look dark while `fires_lit` read correct. Measured as
`fires_found − fires_lit − fires_burning` — fires present at the shutter that the hold
pass never saw — settle 6 medians **+2** and settle 3 medians **+0**. Settle 3 has *less*
of the artefact, not more.

Nor does settle 3 under-stream the world. `fires_found` medians 23 on 1a and 12 on 1b,
which looks alarming until you remember the halves are different builds. The clean test
is within a build: how much does the count grow between the first and third shot at the
same camera? **Zero in both halves.** By shutter time the world has fully arrived at
either settle value; the 23-vs-12 gap is the buildings.

### Holding the builders' fires lit does almost nothing to the photograph

Within-build, 30 matched `storm` / `storm_dark` pairs — identical camera, sky and clock,
differing only in whether the fires were held:

| metric | median delta | mean delta | direction |
| --- | --- | --- | --- |
| `bright_warm_frac` | **+0.007** pts | +0.079 | 20/30 positive |
| `warm_frac` | +0.010 pts | +0.093 | 18/30 positive |
| `scene_v` | +0.002 | +0.010 | 18/30 positive |

Against a within-build noise scale of **5.5 points** across lighting conditions, these are
some five hundred times smaller. 20/30 positive is weakly directional (binomial p ~ 0.10)
— consistent with a real but useless effect.

**State the manipulation before reading the null.** The receipts say a build carries
~30 fires at the shutter, of which **~25.7 already burn with no intervention** and a
stable **~4.4 are genuinely dead**. So holding lights roughly four more out of thirty.
The honest claim is *lighting four more fires out of thirty does essentially nothing to
the frame*, **not** *the builders' fires do not matter*. `fires_lit` is an unweighted
count — a bonfire and a `Candle_resin` are both 1 — so if those four are the fuel-burners
they are also the largest emitters in the room and this null is surprising. The light
dump resolves it by giving `Light.intensity` per prefab; until then the effect size is
"4.4 of 30 fires, luminance weight unknown".

Two things the same receipts settled for free. `storm_flash`'s hold-time population and
its shutter population are **both 455** — identical — so the streaming gap that made the
first shot of each build undercount closes completely by the third. And the count of
genuinely dead fires is stable at 4.33 / 4.40 across variants including one that holds
and one that does not, which **exonerates the light restore**: were it failing, the
control would inherit fires lit by the previous shot and the whole A/B would compare a
lit frame to a lit frame.

### The night sky: disc found in 0 of 30, and it is not cloud

`sky_check.py` fits the moon's limb, converts it back to a world bearing through the
receipt's own yaw/pitch/fov, and compares against where the planner aimed. Across the
30 rooftop frames: **0 discs**. The diagnostic was agreed in advance — high star counts
with good luma means a clear sky and a wrong bearing, low counts mean cloud:

- stars median **149**, and **22 of 30** frames carry more than 100 (max 373)
- luma median 22.4, **16 of 30** inside the 20-186 band
- **26 of 30** held the planned stance

So the sky was open and the moon was not in frame. The planner aimed at azimuth 78, taken
from limb fits in **two frames from two runs** — and moon phase varies by in-game day and
cannot be forced. 0-of-30 at that bearing is the first real evidence against 78. What is
*not* impeached is the stance guard: the camera went where it was told, and the build that
produced the earlier lattice photographs correctly dropped out of the plan.

### The creator bar, again — and why two smart readings both got it wrong

`storm-1a` and `storm-1b` were shot twice. The first pair carried the ComfyQuest overhead
bar burned across `y 96-128`, full width: "COMFY QUEST / Nothing playing / CHECK /
EXPAND F9". 61 frames, dropped.

The runner **warned about it, correctly, at launch** — and was talked past twice, on two
independent wrong readings:

- *"The DLLs are parked, so the mod cannot draw."* False: BepInEx scans `plugins/`
  recursively and a subfolder loads (see the parking correction above).
- *"The setting was renamed to `CreatorBarHotkey`, so the bar is hotkey-summoned and
  nothing presses F9."* False: `F9` **expands** an already-drawn bar. The button in the
  contaminated frames reads `EXPAND F9`.

The real mechanism is a **bootstrap problem**. `ShowCreatorBar` lives in `[Presentation]`
and `CreatorBarHotkey` in `[Runtime]` — two keys, two sections, two jobs. BepInEx only
materialises a plugin's config defaults **when the plugin loads**, so the runner reads the
file before the key exists, correctly warns, and has nothing to switch off. The game then
writes `ShowCreatorBar = true` and the bar draws. The runner was right and powerless.

The fix is one value with the game closed, after which the runner's own quieting
mechanism takes over and prints "quest creator bar hidden for this session". **No code
change.** A queued "fix" to make the warning accept `CreatorBarHotkey` was cancelled — it
would have permanently silenced a true warning.

The config had said so all along. Line 21 of
`djcdevelopment.valheim.comfyquestruntime.cfg`, directly above the key:

> Draw the overhead creator surface. OFF hides every Runtime overlay and changes nothing
> else — quests still load, events still fire, hotkeys still work. **For unattended
> screenshot capture, where the bar otherwise burns into every frame.**

### Do not use a static-pixel test on night or storm frames

The naive version of `check_overlay.py` — fraction of pixels in the band that are
bit-identical across frames — is **confounded by darkness**, and near-black frames are
exactly what a night-and-storm programme produces:

| run | naive static % | truth |
| --- | --- | --- |
| nightsky | 4.61% | clean |
| storm-1a (first) | 5.81% | **contaminated** |
| 20260824-100400 | 0.00% | clean |

The clean night run scores closer to the contaminated run than to the clean daylight one,
and the naive test even placed 186 "static" columns at `x 1261-1474` — precisely where
`COMFY QUEST` and `Nothing playing` sit — on a patch of starless sky. `check_overlay.py`
uses per-pixel standard deviation across *varied* frames for this reason. It also cannot
validate a 2-frame smoke test at a fixed camera, where nothing in the scene changes
either: for that, crop the band and **look at it**.

The blast radius was bounded by measurement rather than assumption: `check_overlay.py`
over four earlier runs across three days reads **0.00%** on all of them, and on `nightsky`
too. Only the two first-attempt storm runs were affected.

## What the light dump said — 2026-08-25

387 light prefabs and all 39 environments, one world load, no screenshots, ~2 minutes.
`out/era17/lights.json`, from `ComfyCameraProof` at `19fd460`.

### Only one of our 43 lights can be blown out by weather

| | count | can weather extinguish it? |
| --- | --- | --- |
| `Fireplace` with `m_canTurnOff = true` | **1** (`Candle_resin`) | yes |
| `Fireplace` with `m_canTurnOff = false` | 16 | no |
| **no `Fireplace` component at all** | **21** | irrelevant |

The one reachable prefab is the weakest emitter in the vocabulary. See the retraction
above: this is why the `CheckWet` lever cannot explain the inside/outside storm gap.

The 21 with no `Fireplace` are the structural surprise. Every `MountainKit` and
`CastleKit` brazier and groundtorch, every Dvergr lantern, the Mistlands torch, the fairy
garland, `piece_Lavalantern` and `GlowingMushroom` are **pure lights** — no fuel, no
wetness, no state. They cannot go out under any condition, and they are a large share of
what this world placed.

### The fires that CAN go dark are the big ones

Light power taken as `intensity x range^2`, summed over what the 30 A/B builds actually
placed:

| | placed | share of count | share of light |
| --- | --- | --- | --- |
| fuel-burners (can go dark) | 3,595 | 33.9% | **55.4%** |
| always-on | 7,014 | 66.1% | 44.6% |

Per build the fuel-burning share of light medians **74.2%**. So the mechanism is real and
large in principle. Individually:

| prefab | intensity | range | power |
| --- | --- | --- | --- |
| `bonfire` | 2.00 | 20.0 | **800** |
| `piece_groundtorch` | 1.50 | 15.0 | 338 |
| `piece_walltorch` | 1.50 | 12.0 | 216 |
| `fire_pit` / `fire_pit_iron` | 2.00 | 10.0 | 200 |
| `hearth` | 1.50 | **3.0** | **14** |
| `Candle_resin` | 2.00 | 1.0 | **2** |

**`hearth` is a small light.** Range 3 m against a bonfire's 20 — power 14 against 800,
a factor of 57. The name has been carrying an implication the prefab does not support,
including in the name of the `hearth-1` run.

### Which resolves the fires null, and it was never a fair test

The A/B moved `bright_warm_frac` by +0.007 points. The dump says why, and it is not that
fire does not matter:

- **The weather path reaches one candle.** Clearing `m_wet` in the hold could never have
  done anything at ThunderStorm.
- **The fuel path had mostly not fired.** The receipts say ~25.7 of ~30 fires per build
  were *already burning* with no intervention, leaving ~4.4 genuinely dead.
- So the manipulation was ~4.4 fires of unknown prefab out of thirty, in a world where
  the big emitters were already alight.

The honest conclusion: **the experiment could not have detected an effect, because the
effect was not available to be produced.** That is a different result from "holding fires
does nothing", and it is the one the evidence supports.

What it does *not* settle is whether a genuinely dark build would photograph differently,
because the corpus does not contain one. The receipts do not record the prefab of a dead
fire, so which of the 4.4 they were is unknown — the cheapest fix is recording prefab
names alongside `fires_burning`.

### hearth-1 is not worth 324 frames on its current premise

The premise moved from "every fire burned to zero" to "fuel-burners only" to "a stable
~4.4 per build", and the dump adds that the single prefab the run is named after emits at
power 14. 74.2% of a build's light *could* go dark, but empirically ~85% of fires were
lit anyway. Re-scope to builds measured genuinely dark, or drop it.

### 15 of 39 environments put fires out — and three are not obviously wet

`wets_fires = m_isWet OR m_windMax >= 0.8`, computed for all 39 without shooting a frame:

`Ashlands_SeaStorm`, `Ashlands_storm` (windMax **3.00**), `Bonemass`, `Eikthyr`,
**`Heath clear`**, `LightRain`, `Mistlands_rain`, `Mistlands_thunder`, `Moder`, `Rain`,
`SnowStorm`, `SwampRain`, `ThunderStorm`, `Twilight_SnowStorm`, `nofogts`.

**`Heath clear` wets fires at `m_isWet = false`**, purely on `windMax = 0.80` — the
high-wind case predicted before the dump existed, and the reason the rule is an OR. The
two boss environments `Eikthyr` and `Moder` do the same at windMax 1.00.

Of the four this project has ever shot, only `ThunderStorm` wets fires — which matters
less than it sounds, given the one-candle reach above.

## The night lane: it was never the light, it was the camera

The series read "night is the worst light" off the sixth-slot A/B — Clear 0.90 medianed
**4.792** against 5.636 for the five golden slots, the worst of the three skies tested.
That reading is wrong, and the reason is visible in `plan_shots.py`'s own comment:

> The camera is always above the aim point here, so a correct pitch is always positive.

Every one of the 2,509 frames was composed by a planner that stands outside a build and
aims **down** at it. At midnight that is a photograph of dark ground. The 14 exterior
night frames are murk with no sky in them at all.

The counter-evidence was already in the corpus. `0629_court_night` and `0532_court_night`
are interior *courtyard* vantages that happen to look up — `pitch` −20.51 and −27.97 —
and they are the best night frames in the set: moon, ring, star field, lit brazier,
layered rock. Nothing needed inventing. What was missing was a planner that puts the lens
on a roof and aims it at the sky on purpose.

### Where the sky is, exactly

`comfyproof_sky` (new console command, and armed from `orbit-request.json` via a
`sky_times` list so it runs unattended like everything else) walked EnvMan's directional
light through 41 times of day. One arc, and colour and intensity say which body is on it:

| | colour | intensity | window |
| --- | --- | --- | --- |
| sun | 1.00, 0.87, 0.64 | 1.50 | t 0.25 → 0.75 |
| moon | 0.41, 0.49, 0.68 | 1.20 | t 0.75 → midnight → 0.25 |

Both rise due east at 0°, peak due south at **45°**, set due west. At t=0.25 and t=0.75
intensity is 0 and colour black — the handovers. The closed form reproduces **all 39 lit
samples to 0.001°**:

```
theta(t) = 180 * frac((t - rise) / 0.5)        rise = 0.25 sun, 0.75 moon
alt(t)   = asin(K * sin theta)                 K = sin 45 = 0.70711
az(t)    = atan2(cos theta, -K * sin theta)
```

Independent check: it puts the sun at **239.7°** at t=0.64, against the **235° ± 25**
this runbook already had from regressing sky-strip luminance on camera yaw over seven
runs. Two instruments, one from the engine and one from pixels, inside the error bar.

It is in `plan_nightsky.py:body_direction()` with the dump samples pinned as a test
fixture, so a later simplification fails against the game rather than against an opinion.

### Two negative findings worth as much as the positive one

**EnvMan has no moon object and no phase field.** The dump enumerated every field and
every `Get*`/`Is*` method matching `moon|phase|sun` and returned only
`m_sunHorizonTransition{H,L}`, `m_sunFogColor` and `GetSunDirection`; all 61 renderers in
the sky hierarchy are cloud, water and fog. The disc is drawn by the sky material. **Moon
phase cannot be set for a shot** — it is whatever the world's day gives, and the two
frames above prove it varies: both are t=0.90, one near-full and one a thin crescent.

**The rendered disc is not where the light comes from.** Fitting the disc's limb in
frames from different runs at t=0.90 — camera yaws 30° apart, so it cannot be an
artifact — puts it at azimuth **77.0 and 79.6**, while the light sits at **134.2**.
World-azimuth spread across detections is 19° against 51° camera-relative, which is what
says it is a fixed body. Use 134.2 for moonlight *on surfaces*; do not use it to place
the disc. Altitude and disc radius are **not** recoverable from limb fitting — the same
body measured 41.3° and 63.7° altitude, because a short arc of a huge circle trades
centre distance against radius.

### The rooftop equations

Three bands: sky above the axis, treetops and ridges in the middle, the roof you are
standing on along the bottom. Constants are measured, not assumed — `fov` is 65 on every
receipt, and the lens lands **1.65 m above the placed point** (`lens_offset_m` 1.72–2.04).

```
alt_target = alt_body - rho                     rho = 0 until the disc is measured
e          = alt_target - atan(f_sky * tan(fov_v/2))        axis elevation
pitch      = -e                                             Unity: + looks down
roofline in frame  <=>  e + atan(h_eye / R) <= fov_v / 2
parapet on the lower third  <=>  e + atan(h_eye / R) = 20.9 deg
aim point  A = lens + 25 m along the axis
```

That last line is the one that lets the whole thing run on the mod as installed. The
runner uses `aim` for three gates and none is framing: it counts pieces within 60 m of
it, raycasts to it, and recomputes yaw/pitch from it if recovery fires. A point 25 m up
the sight line keeps the build inside the piece sphere, puts the raycast into open sky,
and reproduces the planned angles exactly if recovery ever does fire.

Two constraints close from opposite sides and between them they pick the hour. The camera
only looks *up* while the body is above the sky-fraction offset (16° at the default), so
t must be past ~0.81 and before ~0.19. The roofline only survives while
`e + atan(h_eye/R) <= 32.5`, so a 20 m terrace takes a 43° moon and a 4 m turret top
needs it under 25°. A build that fails is a scheduling problem, not a dead end.

### The first run: mechanically perfect, and zero photographs of the sky

`20260825-072915`, 16 frames over 8 builds. Every receipt: `clearance: "planned"` (the
camera stayed exactly where it was put), `occluded: false`, `pieces_near_aim` 1,483–30,930.
**And the disc appears in 0 of 16.** Four frames of cluster 182 — "Black Tower", the
most-lit build in the world at 1,869 weighted lights — are a photograph of its own
diamond lattice.

Three faults, and only the third is about aiming:

1. **The mod's occlusion check cannot see player builds.** `IsOccluded` masks
   `terrain`, `static_solid` and `Default`; placed pieces are on the `piece` layer, which
   `PiecesNear` uses and the raycast does not. For an orbit at 120 m the blockers are
   trees and hillsides so it works; for a camera standing inside its own build it is
   blind. **Not changed** — adding `piece` to that mask would make every orbit start
   reporting its own subject as an obstruction and trigger lift-and-swing across three
   lanes. The guard belongs in the plan.
2. **A ZDO's position is the piece's pivot, not the top of its mesh.** A 2 m wall
   pivoting at 67 reaches 69, and a column-top model reading 67 puts the eye inside
   masonry and calls it sky. Measured on 182: grausten pillar arches pivot **1.35 m below
   the lens** and fill the frame. `scan_rooftops.py` now adds a 2 m piece-top allowance.
3. **A single-ray skyline threads the gaps.** The first skyline walk sampled one column
   line per bearing and reported 0.0° due east from inside a 22,393-piece tower, while
   **1,449 piece pivots sat above the eye** in that corridor. The frame is 97° wide; the
   guard now sweeps a ±15° fan at 5° steps and takes the worst, which guards the middle
   of the frame where the sky band lives and tolerates the edges — a wall at the border
   is a near layer, a wall up the middle is a wall.

With all three in, 182 reads **18.1°** of its own masonry in its clearest direction
against a planned 18.9° axis, and is dropped. Of 21 scanned builds, 5 now drop and 15
plan. This is `plan_interiors.py`'s `--max-los` lesson arriving a second time in a
different costume: **guard the plan, not the pixels.**

The scan also stopped emitting one verdict per build. The highest flat 3×3 block is not
reliably the one with sky over it, so `scan_rooftops.py` emits up to five well-separated
candidate stances, each with its own reach and skyline map, and the planner picks.

### The light vocabulary reached 6.5% of this world's lights

Targeting a night pass by light count needed `scan_features.py` to be able to count
lights. It could not. `FIRES_EXACT` held four names and `FIRES_PREFIX` held two prefixes —
and the prefix half counted **nothing**: `expand_pattern_sets()` used it only to keep
torches out of the wall set, and `feature_rows()` emitted `FIRES_EXACT` alone. So 80,010
placed torches and braziers matched a pattern and were then dropped on the floor.

Hand-audited against Era 17's placed `BUILDING` rows, sorted by placement count and
accepted by eye: **43 prefabs, 173,541 placed lights, 150,553 assigned to a cluster, 456
of 2,204 structures with none.** The old vocabulary reached **11,225 of them, 6.5%**.
Weights are 3 for an open flame, 2 for a torch or lantern, 1 for a small emitter. The
exclusions are recorded in the source with reasons, because the next person to sweep for
`torch` or `fire` will match every one of them: unlit variants
(`CastleKit_groundtorch_unlit`), creature effects (`DvergerMageFire`), crafting stations
whose glow is incidental (`forge*`, `smelter`, `charcoal_kiln`, `piece_oven`), and
`crystal_wall_1x1`, which is translucent rather than emissive and is already a window.

Note for anyone comparing against the fire table earlier in this runbook: those counts
(`Candle_resin` 34,988, `MountainKit_brazier` 34,015) are **all ZDOs including
dungeon-generated props**. Under `category='BUILDING'` they are 2,511 and 3,799. The
dungeon population is real and it is not anybody's build.

**A second bug fell out of the same audit.** The feature join in `scan_features.py` had no
category filter at all — only the *count* queries did, which is why the existing
`test_the_scan_only_ever_reads_placed_pieces` passed while the join was wide open. Any
build whose padded box touched a Dvergr tower inherited its props. Fixed, and the test now
asserts against the join itself rather than against the file.

### Open

- **Nothing has yet photographed the sky.** The guard is in and the plan is replanned; it
  has not been shot. That is the next run and it is the only thing that closes this.
- **`rho` is unmeasured.** `--rho` defaults to 0 and aims at the body's centre;
  `sky_check.py` reports the residual between where the planner put the body and where it
  landed, which is the equation validating itself and the only way to get `rho`.
- **Terrain is still unguarded at plan time.** Valheim generates it from the seed and no
  offline heightmap exists — but terrain *is* in the mod's raycast mask, so the two checks
  cover each other. Pieces and trees are guarded here; hillsides are guarded there.
- `sky_check.py` is deliberately conservative and will refuse rather than fabricate: on
  the frames it was validated against it found the one unambiguous disc and rejected the
  ring feature and a water reflection that an earlier naive sweep had happily reported as
  a moon at −21.6° altitude, below the horizon.

## One driver, and AM4 as the capture host — 2026-08-27

The three lanes were folded into `tools/selfie-stick/Invoke-SelfieStick.ps1`. OMEN
became the brain (planning, scoring, index — it has `clusters.json`, the DuckDB cache
and the perception venv) and AM4 the hands. The existing runners were kept: their
`finally` block restores the operator's BepInEx config bytes on every exit path, and
that is not worth re-deriving.

### The queue had no notion of done, and three of seven rows were lying

Matching plan row counts against receipts settled it: `twilight-1` (150 rows) is run
`20260824-100400` (150 receipts, Clear at 0.71/0.32), `creators-1` (240) is
`20260824-083226`, and `sky-probe` (70) is `20260824-094718` — 70 receipts, 14 distinct
clusters, pitch 74.0–86.2, which is the row's own description exactly. All three still
advertised themselves as waiting.

The driver derives status from `capture-runs.json` plus the receipts instead of from a
hand-kept flag. `settle` got the same treatment: it was **declared** on `storm-1a` and
`storm-1b` and read nowhere in the script, so the A/B that adopted 3 was run by editing
the mod cfg by hand.

### AM4 was one assertion away from re-shooting Era 17 at 1080p

`/etc/X11/xorg.conf` on AM4 is a symlink flipped by `sudo valheim-display
headless|monitor`, and the monitor variant pins `Virtual 1920 1080`. `run-capture.sh`
launches with `-screen-width 3840 -screen-height 2160`. **A 4K window cannot exist in a
1080p framebuffer** — Unity clamps to the screen, writes 1080p frames, and every other
check passes. That is exactly how the Era 17 series shipped at 1080p off OMEN's BMC
adapter.

`DISPLAY=:0 xrandr --fb 3840x2160` grows the framebuffer without touching the symlink;
the panel becomes a 1080p viewport panning over a 4K screen, so a human can still watch.
The driver now asserts the X screen is at least the capture size and names both remedies.
Frames came back **3840×2160**, confirmed.

Also worth recording: `xrandr --props` shows **`EDID:` empty** on that output, so X fell
back to the generic VESA ladder (1920x1080 / 1600x900 / 1280x1024 / … / 640x480) and a
fabricated 527×296 mm panel. The config comment asserting "the panel's native 1920x1080"
is describing a fallback, not the hardware.

### The staged payload reproduced the creator-bar bug by construction

`bepinex-payload.tar.gz` carries `BepInEx/plugins/_parked-by-selfie-stick/` with
`ComfyQuestRuntime.dll`, `ComfyQuestLab.dll` and `ComfyQuestContracts.dll`, and BepInEx
scans `plugins/` recursively. Its shipped quest config has **no `ShowCreatorBar` key at
all**, only `CreatorBarHotkey = F9`. A fresh AM4 install therefore starts in precisely
the state that burned 61 frames.

AM4 now has **no quest DLL under `plugins/` at any depth** — a structural guarantee
rather than a config flag, which is the right shape for a machine whose only job is to
hold a camera. Its `ComfyCameraProof.dll` was also stale (`bc66f907…` = `fe82739`,
predating the light dump and `fires_in_view`); it is now `bc4ca9e4…`, md5-verified equal
to OMEN's.

### check_overlay could not pass a night run

It reported **3.70% frozen** on a clean night capture. Of those static pixels **95.3%
were near-black**, and 61.8% of the whole frame sits below luma 16 — near-black pixels
are bit-identical whether or not anything is drawn on them. No row or column was ≥50%
static, i.e. there was no band.

The fix keeps the tool's own principle — look for the property every overlay has and no
photograph does — and sharpens it to **frozen AND lit**. Black sky is static because
nothing is there; a HUD is static because something is drawn there. `--min-luma`
(default 16) and `--ignore-right-px` (for the NetworkSense transport tab, which is
deliberately retained in the client and cropped from derived images) landed together.

A second limit is the tool's own documented one: with four frames of one roof at two
bearings it still measured 0.35% frozen-and-lit, all of it the same lit tents and fire
appearing in both frames — "too much scene to tell an overlay from a wall". So the
driver hard-fails on a **band** at any sample size, and treats a bandless percentage as
*inconclusive* when the plan has too few distinct cameras. A guard that fires on a case
it cannot judge is decoration.

### Start-NextRun's index rebuild wrote an empty gallery

`@(Get-Content capture-runs.json -Raw | ConvertFrom-Json)` yields a **one-element array
holding an `Object[]`**, because `ConvertFrom-Json` in PS 5.1 emits an array as a single
object rather than enumerating it. Every `--run` argument then collapses into one
287-character space-joined id, `run not in args.run` is true for every real run, and
`build_valheim_index` skips all of them.

The capture runners do **not** share this: they `foreach` over the raw result, which
enumerates correctly and yields all 18 ids. It is the `@()` wrapper around the pipeline
that breaks it. The driver reads the manifest through one helper and asserts the index
never loses frames across a rebuild.

### The disc IS the light, and the 78-degree bearing was a bad fit

The lane's §3.2 finding -- "the rendered disc is NOT where the light comes from",
with the disc limb-fitted at azimuth ~78 against a directional light at 134.2 at
t=0.90 -- is **wrong**, and the same section says why it was fragile: limb fitting a
short arc of a huge circle trades centre distance against radius, and the same body
measured 41.3 and 63.7 degrees of altitude. The azimuth fit was no better than the
altitude fit.

Run `20260827-085344` measured the disc directly instead. Twenty-one frames, one roof,
yaw swept 30-210 in 30-degree steps across five times. Six frames put a disc-sized
saturated blob above the horizon; converting each blob centroid to a world bearing
through the pinhole (focal length from the 65-degree vertical FOV, rotated by the
frame's own yaw and elevation) and comparing against the arc equations:

| t | disc az | light az | d az | disc alt | light alt | d alt |
|---|---|---|---|---|---|---|
| 0.90 | 134.3 | 134.2 | +0.1 | 35.1 | 34.9 | +0.2 |
| 0.90 | 135.3 | 134.2 | +1.1 | 33.6 | 34.9 | -1.3 |
| 0.95 | 153.6 | 155.3 | -1.7 | 42.6 | 42.3 | +0.3 |
| 0.95 | 155.9 | 155.3 | +0.6 | 40.0 | 42.3 | -2.3 |
| 0.05 | 205.0 | 204.7 | +0.3 | 42.1 | 42.3 | -0.2 |
| 0.05 | 204.3 | 204.7 | -0.4 | 41.7 | 42.3 | -0.6 |

**Azimuth residual mean -0.01 degrees, |max| 1.7. Altitude mean -0.62, |max| 2.3.**
`rho` is 0. The disc sits on the directional light, and `plan_nightsky`'s own equations
were already pointing the camera at the moon.

So the 0-of-30 was not a mystery about where the moon renders. The run set
`--body-azimuth 78` and therefore aimed **56 degrees away from it**. The correct plan
is the DEFAULT one: omit `--body-azimuth` entirely. Deleting an argument is the whole
fix.

### sky_check could not see the moon, and the 0-of-30 was its fault

Two gates, each tuned against a reference the disc does not match.

**The cyan mask.** Candidates needed `(blue - red) > 25`. A moon bright enough to
bloom saturates toward white: on `0026_moon2t005y150.png` it reads blue-red **+8.3**
across the blob and **+4.0** across its brightest 500 px. The disc was never entering
the candidate set at all. The test is right for a dim, unbloomed disc and wrong for a
bright one, so it is now cyan **OR** near-saturated-white. Every later gate is
unchanged, and the circle residual still does the discriminating: the two lit tents in
that same frame fit at 4.06 and 1.46 against tolerances of 1.37 and 1.12.

**The radius floor.** `RADIUS_MIN_PX` was 400. The moon's core fits at **253 px**
full-res with a median residual of **0.79 against 1.58 allowed** -- a clean fit thrown
away on the floor. The source note claiming "the moon fits at about 1,600 px on a 4K
frame" cannot be describing the disc: at a focal length of 1,695 px (65 deg vertical
over 2,160 px) 1,600 px is an angular *radius* of 43 degrees, wider than the frame's
own half-height. Floor lowered to 150.

What that recovers is the point. Re-run against **the original run
`20260825-075415`** -- the one that reported 0 of 30 and blocked the lane:

| frame | t | disc az | light az | d az | rho |
|---|---|---|---|---|---|
| 1135_moon1 | 0.90 | 135.2 | 134.2 | +0.98 | 6.5 |
| 1135_moon1_r2 | 0.90 | 135.3 | 134.2 | +1.08 | 6.7 |
| 0273_moon1 | 0.90 | 135.1 | 134.2 | +0.88 | 6.4 |
| 0273_moon1_r2 | 0.90 | 135.1 | 134.2 | +0.88 | 6.5 |
| 0061_moon1 | 0.90 | 134.9 | 134.2 | +0.68 | 6.2 |
| 0061_moon1_r2 | 0.90 | 134.9 | 134.2 | +0.68 | 6.1 |

**Six discs, three builds, azimuth residual mean +0.86 deg (|max| 1.08).** `rho`
median **6.45 deg** -- a value that had defaulted to 0 since this lane began, now
measured twice independently (6.45 here, 5.5 on `20260827-085344`).

**The moon was in the lane's own frames all along.** The 56-degree aiming error from
`--body-azimuth 78` is real and worth fixing, because it puts the moon at the frame
edge instead of composed -- but it is not what produced the zero. A measurement
failure was read as a photographic one, and the lane spent its remaining effort on the
bearing.

Two things follow for anyone reading a 0 from this tool. First, its own note --
"deliberately conservative, expect false negatives" -- was accurate and was still not
cautious enough: a false negative here was indistinguishable from a real result and
was acted on as one. Second, its printed line "a large azimuth residual means the
rendered disc is not at the directional light, which is a real finding and not a bug"
is a trap when the plan carried a forced `--body-azimuth`, because the residual is
computed against the plan's stored bearing, not against the equations. On the
ephemeris sweep it prints 85 deg while the true residual is 0.3.

The remaining limitation is unfixed and known: only 6 of 30 and 2 of 21 are found,
because a disc clipped by the frame border loses the interior edge pixels a limb fit
needs. Falling back to a saturated-blob centroid would find the rest -- that is all
the manual measurement above used.

### The night lane closes: residual 0.2 degrees, rho about 6

`nightsky-2` (run `20260827-090252`, 22 frames over 11 builds on AM4) is the same
plan as the original with **one argument deleted**: no `--body-azimuth`, so the camera
is aimed by the arc equations alone.

| frame | d az | d alt | rho |
|---|---|---|---|
| 0013_moon1_r2 | -0.0 | -0.6 | 5.8 |
| 0211_moon1_r2 | +0.6 | -0.2 | 5.8 |
| 0042_moon1 | -0.1 | +0.1 | 6.4 |
| 0042_moon1_r2 | -0.7 | +0.2 | 6.2 |
| 0448_moon1 | +0.2 | -0.3 | 5.5 |

**Median azimuth residual 0.2 degrees**, every frame inside +/-0.7, altitude inside
+/-0.6. This is the first time sky_check's own success condition -- "a small residual
is the equation validating itself" -- has actually been met. 20 of 22 kept the planned
stance.

`rho` now has three independent measurements: **6.45** (original run 20260825-075415
re-measured, n=6), **5.5** (ephemeris sweep 20260827-085344, n=2) and **5.8**
(here, n=5). Call it **6 degrees** and feed it back as `--rho`; it has been 0 until now,
which biases every aim point by roughly a disc radius.

Detection is still 5 of 22 rather than 22 of 22, and the cause is known and unfixed: a
disc clipped by the frame border loses the interior edge pixels a limb fit needs. The
frames are fine; the measurement is conservative. Do not read that ratio as a
photographic result -- that is the mistake this whole section exists to record.

### The channel lane, and a prefab vocabulary wrong for the third time

Derek's composition rule, which is not the one plan_nightsky implements: "aiming at
the moon itself is boring, using the lighting of a full moon at that angle... is
creative", and "see down a channel to get the depth of vision from ground
construction out into the sea... just solid stars caught in the top 1/3 to 1/6".

`scan_channels.py` + `plan_channel.py` implement it. Bearing is chosen by the
channel, the moon is required 40-140 degrees off-axis, and pitch places the skyline
so clear sky fills the top sixth-to-third. Every emitted pitch is positive -- tilted
DOWN -- which is why the existing night frames cannot show this composition at all:
all of them are aimed above the horizon, so the depth is off the bottom of the frame.

**Open water is derivable after all.** The colour lane recorded that seaward
direction "is not derivable from the DuckDB cache (no terrain)". True of the cache,
false of the machine: Valheim writes `<World>_mapTexCache` beside the save, a
2048x2048 PNG of biome colours with Ocean at #333333. The mapping was solved rather
than assumed -- 10 m/px centred on 1024, from the world disc measuring 1005 px in
half-width and centring on column 1023.0 -- and the row direction fixed by a
physical prior: under it Mountain pixels carry a mean build min_y of 127.9 m against
64.8 on land, and flipped they come out lowest, which terrain cannot do.

**The tree vocabulary was wrong, and it was wrong the same way as the last two.**
The first `TALL_TREES` was written from knowledge of Valheim rather than from this
world's placement counts. It missed `YggaShoot_small1` -- the **fourth most placed
vegetation prefab in Era 17 at 472,679** -- plus `YggaShoot1/2/3` at about 143,000
each. Cluster 26 has seven of them 24 m from its stance with pivots 8 m below the
lens, the planner called that bearing open, and the frame it shot
(`0026_chan1t005y150.png`) is solid foliage: 6.1% sky in the top third against 14.9%
green.

Rebuilt from counts across EVERY category and audited by eye, it drops cluster 26
from 7 open bearings to 2 and removes exactly the bearing that failed. Two details
worth keeping:

- **Category must not be filtered.** People plant trees. `Birch1` appears 38,464
  times as BUILDING against 25,762 as UNKNOWN; `FirTree` 21,989 times.
- **The sweep needs auditing, again.** The pattern `%fir%` matched `FireFlies` and
  `fire_pit`, and `%tree%` matched `ashwood_decowall_tree`, which is a decorative
  wall. This is the same failure as the `-table-` sweep that swallowed
  `UnstableLavaRock`.

The heights above each pivot remain the only guessed numbers, isolated in one dict
with a single `--tree-scale` knob, because the pivot elevation itself is real data.

**Result of the first run (20260827-092614, 58 frames):** 46 of 58 have a top third
that is over 40% sky and under 12% foliage, and check_overlay is clean at 0.00%. The
band structure works. What does NOT yet work is *selecting* the good ones: the quick
"blue-dominant equals sky" proxy used to rank them scored a frame of a giant cyan
Yggdrasil glow as 100% sky. Ranking these frames needs a real measurement, which is
the same lesson as everywhere else here -- guard the plan with geometry, and judge
the frame with something that measures the thing you wanted.

---

## 2026-08-27, second night: R&D laps on AM4 (1080p probe protocol)

R&D mode: probes shoot at 1920x1080 (`run-capture.sh --width 1920 --height 1080`)
for speed and disk; a keeper is re-shot at 4K by re-running its plan rows, which
re-rolls its sky anyway. All runs this night on AM4; OMEN untouchable (benchmark
window) and its era17 capture tree parked by the creator lane at
`C:\work\comfy-quest\captures\install-cleanup\omen-era17-20260827T102804Z\`.

**storm_flash read (no new capture; runs 20260825-091907/094829).** The lever
that was built and never read WORKS: luma_mean vs the no-flash twin median
+10.0, mean +11.2, 26/30 builds positive (max +39.1), against the storm_dark
control at median -0.7. Receipts: 50 shots armed, bearing -35, hold 1.2 s. Of
the two storm levers, holding fires is a null and the driven flash is real.
Open: a bearing/hold sweep, and the 4 negative builds (587, 629, 1160, 1927).

**nightsky-3 (20260827-104128, 48 frames, 4K).** Derek's verdict by eye, frame
confirmed: the moon-aimed planner composes discs and its own foreground (a trunk
mid-frame on cluster 26 at rho 6). Genre retired as a default; frames kept as
selection stock. The rho feedback worked mechanically; the composition is the
problem, not the aim.

**channel-1b (20260827-105152, 48 frames, 4K, shot names suffixed `b`).**
Cloud re-roll of the committed channel-1 plan. Eyeballed cluster 13 chan1-y300
against its morning twin: identical roof-dominated framing under two different
skies -- the dome fills the middle band, no water run in frame. The 46/58
composition claim was scored by the blue-dominant proxy that reads teal haze as
sky; the channel guard constrains the FAR field (canopy, ray run) and nothing
constrains the NEAR field (the stance's own roof under a pitch-down axis). Same
family as the night lane photographing its own lattice. Next lap: a near-field
clause in scan_channels, and eyeball the morning run's proxy-best frames.

**hearthview-1 (20260827-110128, 22 frames, 1080p) -- NEW GENRE PROBE.**
plan_hearthview.py: stand in the hall a few metres inside the gate, fires held,
look out the opening; per-bearing the CLOCK is solved so the moon rakes 40-140
deg off-axis at 8-22 deg altitude (long shadows). Every stance held
(clearance=planned, placed==planned 22/22). Three edges, all from receipts plus
three frames:

1. **Openable state is invisible to the plan and unactuated by the mod.**
   cluster 440's darkwood_gate is CLOSED in frame; the plan cannot know and the
   mod cannot open it. Fix candidates: a door lever shaped exactly like
   HoldFiresLit (owner-guarded ZDO write, restore after), or filter openings to
   always-open prefabs.
2. **aim_y = gate - 2 m digs into rising terrain: occluded on 11 of 22 rows**
   (the raycast cannot see the closed piece-layer doors, so occluded=true here
   means GROUND). hearthview-2 raises the aim to gate + 0.8.
3. **The warm side must be required, not hoped for: fires_in_view 0-7.** The
   lever mostly worked (142 lit across the run; the sweep-zero was one row,
   0195, a streaming race, 1 of 22) but no rule put a fire between lens and
   gate. hearthview-2 prefers torch-lit openings (vantage_gate's lit() rule).

One frame (0504_hearthrt805) inverted the brief by accident -- down the hall
toward the blazing hearth with the cold night bleeding in at the open door --
and is the best warm/cool frame of the night. The genre is real; the doors are
the blocking edge.

Re-run the slice:
  ssh homebase '~/valheim-capture/run-capture.sh --plan ~/valheim-capture/plans/hearthview-2.tsv --width 1920 --height 1080'

Not sampled this night: Twilight_Clear (twilight-2.tsv staged, unfired); whether
any opening prefab in features.json stands open by default; terrain past the
door (no offline heightmap -- the occluded receipt is the only instrument);
channel morning frames beyond cluster 13; the 1080p-vs-4K effect on the colour
metrics (ratios, assumed resolution-independent, unverified).

### The instakill lap: god mode was on, and the rig died anyway

Derek, watching AM4's panel during hearthview-2: "i'm getting instakilled.
might want to make sure godmode is on." It was on -- and that is the lap.

Instrumented `SetInvulnerable` (mod commit `1600fa4` in the comfy archive) to
read back god/ghost/fly after setting and to WARN when reflection finds
nothing; the old version could miss both lookups silently. The readback said
`god now True, ghost now True` -- and the rig still died, twice, in a 2-shot
probe at cluster 504. Chronology from LogOutput: placed at the stance before
the build streamed in, the rig fell (no floor), and because zone streaming
follows the player the falling rig dragged the load target down with it --
`world never arrived (0 pieces) -- shot skipped` -- until the fall ended in a
void death god mode does not cover.

Fix: debug-fly, NetworkSense's own route-teleport safeguard, via the direct
`Player.ToggleDebugFly()` API (console `fly` is cheat-gated client-side).
Re-probe at the same stance: `god/ghost/fly True`, ZERO deaths, and the
previously-empty zone arrived at 492 pieces -- fly killed the fall AND
anchored the stream, fixing the "world never arrived" skip as the same bug.
Installed on AM4 only (OMEN's plugins belong to the creator lane tonight);
md5 6e32a2d3ecc3a025ef9907bf3f199450. Rooftop/orbit runs never tripped this; ground stances do.

Two side finds: AM4's capture character is `durracktu` (tugcorp's .fch never
made the trip; auto-boot picked what exists), and `plan_interiors.validate_tsv`
returns `(ok, bad)` -- earlier tonight it was read backwards, and a
PowerShell-BOM'd TSV makes it miscount the header as a bad row (the mod's own
`File.ReadAllLines` strips the BOM and is unaffected).

### hearthview-2 rerun with the immortal rig (20260827-112856, 22 frames, 1080p)

Zero deaths, zero "world never arrived", terrain occlusion 11 -> 7 after the
aim raise. Composition readout by eye: the hall-level "gate" is often an
INTERIOR partition, not an exterior doorway -- 270 stands in a banner corridor
against a fire-bloomed pillar, 612 faces decorative lattice, 524 frames a
shrine tableau through open doors (a keeper as a photograph, still inward).
0504 remains the proof the brief composes: hall run, burning hearth in the
sight line, sea-and-sky slot beyond. Next lap: an exterior-ness guard -- count
pieces in a cone BEYOND the opening along the outward ray (few = it leads
outside, many = it leads to another room), from the same features/walls data
the wall-bite check already reads. Doors that are shut stay the other open
edge (door lever, shaped like the fires lever).

### hearthstorm-1: the cozy thesis lands on first contact

Derek: "nothing makes a house or a hut or a leanto feel more cozy than a
hearth/fire against a raging storm." Every storm frame ever shot was at
t=0.58; the storm x clock x interior-doorway cross had never been run.

- twilight-2 = `20260827-113624` (120 @ 1080p) -- first use of the game's own
  Twilight_Clear in project history. Caveat found mid-lap: AM4 deliberately
  runs Derek's blur-on look (depth of field etc.) while the whole OMEN corpus
  is blur-off, so the cross-node A/B against 20260824-100400 carries the
  post-effect stack as a second variable. twilight-2c (same rows, env Clear,
  shot names suffixed `c`) re-shoots the synthesized twin ON AM4 so the
  twilight A/B becomes single-variable.
- hearthstorm-1 = `20260827-115700` (22 @ 1080p): hearthview-2 geometry, env
  ThunderStorm, fires held, driven flash -35 on every row; the l/r moon sides
  are moot under cloud so they became the two clocks -- `stormnight` (t~0.2/0.8)
  and `stormtwil` (0.71, the first storm-twilight ever).

By eye: `0504_stormtwil` caught the flash mid-hold -- violet sky through both
openings, lit rain streaks, storm fog rolling through the hall, the longfire
holding orange against all of it. `0524_stormnight` shows the other use of the
same lever: the strike as a door-edge RIM LIGHT on the shrine tableau. Neither
image resembles anything in the 2,633-frame corpus. The genre stack that
produced them: doorway framing (hearthview) + lit-opening rule + held fires +
driven flash + clock as a free variable + Derek's deliberate DOF look on AM4.

### Terrain is no longer "not derivable": tools/selfie-stick/terrain.py

Every lane in this project has recorded the same gap -- "no offline heightmap",
"seaward is not derivable", aim lines digging into rising ground, occlusion
receipts as the only instrument. A subagent lap closed it.

The `<World>_heightTexCache` beside the save is a plain 2048x2048 RGBA8 PNG.
Byte-guessing failed; the encoding came from decompiling `Minimap` out of
`assembly_valheim.dll` and reading the codec both ways:

    height_m = ((R << 8) + G) / 127.5

big-endian 16-bit fixed point, absolute world metres, 0-510, negative worldgen
heights clamped to 0 (deep ocean reads exactly 0.0), B=0/A=255 padding. It is
pristine `WorldGenerator.GetBiomeHeight` -- no player terraforming in it.

Georef, from `GenerateWorldMap`'s own loop: `col = (x-6)/12 + 1024`,
`row = 1023 - (z-6)/12`. **12 m/px, north-up, half-texel offset.**

> **`scan_channels.py`'s mapTexCache georef is WRONG and so is its ocean test.**
> Pinned against 824 build anchors: correlation **+0.941** under the decompiled
> mapping against **+0.01** under scan_channels' (10 m/px, +z down). And the
> decompiled `GetPixelColor` says Ocean is **WHITE**; scan_channels' `0x333333`
> "ocean" is a dark LAND biome averaging 38.3 m of worldgen height. Its
> `sea_at_m` / `sea_run_m` outputs inherit both errors. Not modified by that lap
> -- the channel lane owns the fix. NOTE the near-field roof problem logged
> above is SEPARATE: cluster 13's chosen bearing 30 profiles as 600 m of
> unbroken water under the new instrument, so that bearing was right anyway.

Validation (`out/era17/terrain-validation.md`): 245,075 flood-fill-isolated
ocean pixels, **100.000%** below y=30; structure residual (min_y - ground)
median **-2.86 m** (pivots bury slightly below grade), |resid| median 3.11,
p90 9.04, 94.7% within 15 m; worst outliers are all water-sited stilt builds,
coherent rather than mapping error. Cluster 440's hearthview gate: ground 32.19
against floor ~33.8, with open water 50 m east -- that doorway really does face
the sea.

Source 2 landed too: a byte-exact walk of the frozen backup's packed ZDO stream
(formats from decompiled `ZDOMan.Load`/`ZDO.Load`/`TerrainComp`, 8,922,012 ZDOs
traversed without desync) pulled **22,039 `_TerrainCompiler` zones ->
2,864,118 terraformed vertices** into `out/era17/terrain-edits.npz`. Residuals
improve with the layer on (edited-anchor median 3.27 -> 2.70) and a
transposed-axis control scores worse, which is what pins vertex order. Every
query reports which layer answered it; the extractor refuses the live
`ComfyEra17.db` by name.

    python terrain.py --probe -5758.8,-1547.9
    python terrain.py --profile -6258.8,-1547.9 -5258.8,-1547.9 --steps 200 \
        --edits out/era17/terrain-edits.npz --png out/era17/terrain-profile.png

### R&D lap: clean 2 m motion at cluster 504 (2026-08-27)

**VERIFIED:** one 1080p capture proves the motion path without operator chrome.
The session-scoped wrapper changed NetworkSense `isModEnabled` from `true` to
`false`, retained `portalConnectionCacheEnabled = true`, and restored both the
NetworkSense config and pre-existing `orbit-request.json` byte-for-byte on exit.
The NetworkSense config SHA-256 was
`217c14758239bb89b06926db0b49f28b9070f122a0e2e088059fcd340bce66c7`
before and after; the request SHA-256 was
`c25bff61ecc3cbda1d6d215879d903eb25183b517f4e7bd8bbb2bf569f4c5cc1`
before and after. The game was idle after the run. The log independently records
`Portal connection cache enabled; interval=5s.` during the capture.

Run `20260827-133124` produced
`/home/derek/valheim-capture/clips/20260827-133124/0504_stormtwil_push2m_clean.mp4`:
26,004,367 bytes, SHA-256
`3c084114876095fa151579123696b94bf4a9a283c111bc2f0334e1ddcb538f65`,
1920x1080, 513 decoded frames (`nb_frames` metadata says 609), average frame
rate `36540/611` (~59.8 fps), duration 8.555013 s. Its receipt records an 8.002
s wall-clock move from
`(4677.3, 36.27, -6784.2)` to `(4677.7, 36.27, -6782.2)`, fixed yaw/pitch
`12.69/1.61`, `ThunderStorm`, time 0.71, and no driven flash (`flash_at=-1`).
Full-resolution frames at 0.5, 4.25, and 8.0 s show no `NET SHOW`, title bar,
desktop, cursor, or crosshair. Door, pillar, fire, and floor parallax visibly
advance across those frames while the hearth and storm opening remain composed.

**Edge found; lap stopped:** the cyan Creator HQ portal is only a glow near the
midpoint but enters strongly at the right edge by 8.0 s. This is cleaner than the
earlier 7 m push, but the endpoint is not yet a keeper. The next bounded probe is
either a roughly 1.25 m push or a slight left yaw bias, not both at once.

Exact rerun from an operator shell:

    ssh homebase '~/valheim-capture/run-clips-clean-lap.sh ~/valheim-capture/plans/clips-clean-1.tsv'

The AM4 staging inputs are `clips-clean-1.tsv` (236 bytes, SHA-256
`b449925d4b83454408362cf804a0aa59ed6a1f380bc1de8f373fe460ed13eaef`)
and `run-clips-clean-lap.sh` (3,179 bytes, SHA-256
`34ac3eedb8f54860c1cedfbbd6036cb6c14cd1acf564dc5f49d2eafd31e1a758`).
They are reproducibility staging, not an authoritative product implementation.

Uncertainty intentionally left for the next lap: this is one move on one build,
at 1080p only; natural storm variation was uncontrolled; no driven flash or 4K
pass was attempted; camera motion was verified by frame inspection rather than
an automated image-space metric; and the pre-existing orbit request remains
armed because this lap did not create it.

#### Follow-up lap: distance-only 1.25 m probe

**VERIFIED:** run `20260827-133955` changed only the endpoint distance, from the
2 m plan's `(4677.7, 36.27, -6782.2)` to `(4677.55, 36.27, -6782.97)`; clock,
weather, duration, easing, start, yaw, pitch, flash posture, capture size, and
operator-chrome suppression were held fixed. The plan was 241 bytes with
SHA-256 `e2eabe7d0ec90e371ee374b5611b49b250aaa772e749b385f253e671933d6c8e`.

The resulting
`/home/derek/valheim-capture/clips/20260827-133955/0504_stormtwil_push125cm_clean.mp4`
is 21,343,540 bytes with SHA-256
`1160ea36dd4ceefae0967d0aa681a1ef53a44029f1866e9bd003c7f6cc06a3d8`;
it is 1920x1080 at 60 fps, 513 decoded frames (`nb_frames` metadata says 617),
duration 8.563021 s. The receipt records 8.001 s wall time, 2,218 game-update
frames at 277.21 fps, and no driven flash. NetworkSense stayed visually absent,
portal-cache activation was logged, both operator-state hashes restored exactly,
and Valheim was idle afterward.

Full-resolution 0.5, 4.25, and 8.0 s frames verify motion and a smaller endpoint
advance than the 2 m control. The shorter move reduces the visible portal ring,
but does not remove the endpoint distraction: a cyan pulse and its floor cast
remain beside the near right-hand door. Natural portal/storm animation prevents
brightness from being a controlled A/B, but the static door and ring geometry
show that the two endpoint positions are distinct.

**Edge found; distance lap stopped:** shortening translation alone cannot clean
the right edge without making the already-subtle move still smaller. The next
one-variable probe holds the 1.25 m path and biases both yaw endpoints 3 degrees
left (`12.69 -> 9.69`) to move the hearth toward center and the portal outward.

#### Follow-up lap: 3-degree left-yaw probe

**VERIFIED:** run `20260827-134827` held the 1.25 m plan fixed and changed only
both yaw endpoints from `12.69` to `9.69`. The 248-byte plan SHA-256 is
`a70cd4b97ffdc06a86d6c0d12d50f7a5c7ad55818b0b8d47865ba199668c16eb`.
The resulting
`/home/derek/valheim-capture/clips/20260827-134827/0504_stormtwil_push125cm_yawleft3_clean.mp4`
is 25,834,095 bytes with SHA-256
`a6d0730f178fdabd89d4c55ead3ade61271d2ae4a1dc2562066de9e9562286bb`;
it is 1920x1080, average frame rate `11340/191` (~59.4 fps), 512 decoded frames,
and duration 8.610026 s. Its receipt records 8.001 s wall time, 2,137 game-update
frames at 267.09 fps, and yaw `[9.69, 9.69]`. Portal-cache activation, exact
operator-state restoration, and post-run game idle were verified again.

Frames at 0.5, 4.25, and 8.0 s confirm the expected direction: compared with the
zero-bias 1.25 m clip, the right-hand door and portal move outward and the hearth
moves toward center. The endpoint still catches a saturated cyan portal pulse,
however, so 3 degrees is directionally useful but not enough separation.

**Edge found; yaw lap stopped:** preserve the 1.25 m move and advance exactly one
more 3-degree left-yaw step (`9.69 -> 6.69`). This tests whether the portal can
leave the action-safe frame before the left foreground becomes intrusive.

#### Follow-up lap: 6-degree yaw bracket and publish-safe cut

**VERIFIED:** run `20260827-135453` held the 1.25 m path fixed and changed only
both yaw endpoints from `9.69` to `6.69`. Its 248-byte plan has SHA-256
`59bb4609be9fd67bb9eb66020159908dd4df53bd8a1f1c5c086f0a9abbc585e9`.
The raw sliced artifact
`0504_stormtwil_push125cm_yawleft6_clean.mp4` is 25,078,078 bytes with SHA-256
`24dd7765fa490218c96edd9337c22eb6fcb7aaf6e85b333b6d487c7dd3e8bef5`.
Its receipt records 8.002 s wall time, 2,139 game-update frames at 267.32 fps,
and yaw `[6.69, 6.69]`. Portal-cache activation, exact operator-state restoration,
and post-run game idle were verified again.

The second yaw step again moves the portal and right-hand door outward and moves
the hearth toward center. It also establishes the other side of the composition
bracket: the blue hanging banner becomes prominent at left. The result is more
balanced than the zero-bias clip, but it does not make the portal disappear; a
natural cyan pulse remains visible near the endpoint.

A one-frame-per-second contact sheet exposed a separate publish blocker missed by
start/mid/end inspection: the raw slice returns to normal gameplay with HUD and
minimap in its final fraction of a second. The transition begins between 8.1 and
8.2 s. The AM4 staging runner deliberately slices from 0.25 s before the receipt
start through 0.25 s after its end (`dur = wall_s + 0.5`) using stream copy, so
the post-roll outlives the driven-camera state. Its discontinuous timestamps also
made a copy-only 8.10 s trim report an invalid 11.95 s result; that attempt was
rejected.

The raw capture was preserved. A deterministic publish cut normalized the first
486 decoded frames onto a fresh 60 fps timeline:

    ffmpeg -hide_banner -loglevel error -y -i 0504_stormtwil_push125cm_yawleft6_clean.mp4 \
      -vf "select='lt(n,486)',setpts=N/(60*TB)" -frames:v 486 -an \
      -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -r 60 \
      -movflags +faststart 0504_stormtwil_push125cm_yawleft6_publish.mp4

**Publish artifact:**
`/home/derek/valheim-capture/clips/20260827-135453/0504_stormtwil_push125cm_yawleft6_publish.mp4`
is 9,211,189 bytes with SHA-256
`f20c47ab4a40cb0aad6ee3d4ac173e517c938b67b43cbc5ebcc04fee9f723d47`.
Both local and AM4 `ffprobe -count_frames` report 1920x1080, 60/1 fps, exactly
486 decoded frames, and exactly 8.100000 s. The first frame, final frame, and
full-sequence contact sheet contain no NetworkSense text, title bar, desktop,
cursor, crosshair, HUD, or minimap. `freezedetect=n=-60dB:d=0.5` emits no
`freeze_start`, and the frame sequence visibly advances.

Exact capture rerun used by this lap:

    ssh homebase '~/valheim-capture/run-clips-clean-lap.sh ~/valheim-capture/plans/clips-clean-125cm-yawleft6.tsv'

**Edge found; publish lap stopped:** the one clean motion deliverable now exists,
but the staging runner's raw per-receipt products are not publication-safe until
their tail policy and timestamps are normalized. That runner is not authoritative
Baseline product code, so this lap records the defect instead of migrating it into
the hub. Remaining uncertainty: one 1080p build/weather realization, natural
lightning and portal animation, a second-generation CRF 16 encode, visual rather
than automated chrome detection, no audio, no driven flash, and no 4K pass.

### Video: driven camera clips (20260827-123029, 4 clips, 1080p60)

Derek: "i think that same hardware could be leveraged for this only we create
little fly by scripts, then our timing with the lightening and conveying a
feeling vs showing a picture steps up again another level."

Built: `clipplan.tsv` (18 positional columns: start pose, end pose, duration,
easing, flash offset, flash bearing) armed by `"clips": true` in
orbit-request.json; `plan_clips.py` generates it from framings that have
already been shot and looked at; `run-clips.sh` records the session with
x11grab + h264_nvenc on AM4's 5070 and slices afterwards from the UTC stamps
the mod writes per clip. Mod commit `6450278`.

**The hot loop does no IO** -- Derek's constraint, and the same trap as the
raw-socket POST that froze a main thread for ten seconds. A Unity coroutine is
on the main thread, so log lines, receipts, environment/clock and world waits
all sit outside the motion loop. Motion moves the PLAYER with debug-fly on
rather than taking over the camera; the boom is already 0 for stills.

**Results, all four clips: `moving`.** 2384/2281/1056/943 frames over 10.00s
(the game renders at 94-238 fps; the recording is 60). Durations 10.00-10.01
against 10.00 planned. The C9 failure -- perfect receipts over frozen panels --
did not repeat, and freezedetect is the gate that would have caught it.

Two things the first take taught:

1. **x11grab captured the DESKTOP, not the game.** The window sits at `+1+18`
   under openbox, so a `:0+0,0` grab of 1920x1080 caught the title bar and a
   strip of desktop. The stills never had this because the mod captures Unity's
   own framebuffer. `run-clips.sh` now measures the window with `xwininfo` and
   grabs its exact rectangle -- which means the recorder must start AFTER the
   window exists, which is safe because the first clip is a minute away.
2. **A bright object in frame is not evidence of the flash.** The cyan blaze
   filling half of 0504's push is a PORTAL ("CREATOR HQ" on the sign beside
   it), present at t=5.0 before the strike was due.

**The driven flash did not fire visibly, and that is the open edge.** Per-frame
`signalstats` YAVG across the scheduled window is smooth -- 78.3 at t=6.00
drifting to 80.3 by 6.35, no spike -- while a genuine 34 -> 89.6 spike sits at
t=1.3 and decays over ~1.5s, which is ambient ThunderStorm lightning (that
environment fires its own strikes; a luma spike alone cannot attribute one).
`DriveFlash`'s return value is DISCARDED in the clip path -- the still path
records it in the receipt. Log it before theorising further.

Re-run the slice:
  ssh homebase '~/valheim-capture/run-clips.sh --plan ~/valheim-capture/plans/clips-1.tsv --width 1920 --height 1080 --fps 60'

Not sampled: whether the push's dark-interior -> bright-exterior ramp (YAVG 34
-> 80 over the move) reads as intentional or as exposure drift; audio (none
captured, and the panel has no audio device); 4K clip cost; whether a longer
flash hold than 0.35 s reads better at 60 fps; any move but push and pan.

## The showcase round -- four launches, two new genres, and the flash says "ok" (2026-08-27, late)

Derek freed AM4 for ~2 hours (the B70 benchmark owns OMEN; every frame and every
encode ran on the 5070). Four game launches: 4K re-shoot of the proven geometry
(RUN 20260827-230926, 8/8), a 1080p probe of nine candidate gates plus five
hover-channel rows (RUN 20260827-231431, 14/14), the merged 4K keepers
(RUN 20260827-232224, 6/6), and clips (20260827-233012, 3/3 moving).

**The exterior guard failed its truth set on both signals, and that is the
result.** Pre-registered expectations: 270/612 reject, 504/524 pass, 440 pass
despite its closed leaf. Measured (near [2,10] m cone count / far [2,30] m /
water-reach along the outward ray):

    504  15/23   w10    exterior (the proof shot)
    440  58/152  w20    exterior -- its own building stands seaward of the gate
    270  67/68   w-     dud
    524  35/36   w10    inward (sits over water anyway)
    612   0/0    w10    dud -- the lattice is FLUSH, inside the 2 m dead zone

No threshold separates {504,440} from {270,524,612}; water-reach fails the same
way. A zero cone is NOT evidence of exterior -- 445 read 0/0 and opened into a
monster pen, 518 read 0/1 and opened into a crystal room. The probe run stayed
the classifier. One pattern emerged at n=1, recorded not hardened: 474 -- the
only candidate with BOTH a sparse cone AND far water (5/15 w100) -- was the only
true window of the nine.

**474 is the first true hearthview since 504.** Open double doors under an arch,
torch on stone right, starlit meadow and flower hedge beyond -- and its
ThunderStorm t=0.71 variant is the hero of the round: violet rain sheeting past
the arch, warm torchlight inside. **627 found a genre nobody planned: the storm
alley.** Its hall-level "gate" put the stance OUTSIDE, between two buildings --
lantern glow raking a timber wall, snowy path leading back, lit rain overhead.
Wrong per the plan, right as a photograph.

**All five hover-channel rows are one clean null.** A 600 m water lane at night
with no anchor in frame is not a photograph; advancing past the roof edge
removed the anchor entirely, and the lateral-anchor row missed the silhouette
too. If the lane idea returns, it returns in daylight or with a lit foreground.

**4K clips are geometrically impossible on this X setup.** The window sits at
+1+18 in an exactly 3840x2160 framebuffer, so a full-4K grab runs off-screen and
ffmpeg refuses at startup. (The failed launch's game never armed clips -- the
harness's cleanup trap restored orbit-request.json before the mod's boot settle
read it. No ghost receipts.) The 1080p60 fallback ran clean: 243/235/102 fps
effective slices, all three freezedetect-moving at 10.00 s.

**The driven flash fires in clips.** With the return finally logged, all three
clips report `flash at 6.00s -> ok`, and the push clip's YAVG trace shows a
structured event at the drive time: dip 82 -> 75.7 at 6.0-6.1, ramp to a 90.7
plateau at ~7.0, decay by 7.4 -- the same +10 magnitude the stills measured.
The earlier no-show now reads as "may never have fired at all" (its return was
discarded). Driven-vs-ambient attribution still needs a control clip
(flash_at=-1, same env and clock).

Also confirmed: ComfyQuestRuntime burns a small green chip into the right edge
of every frame -- the harness warns exactly this at launch. Park its DLL for
future runs, or crop at publish.

Re-run the slices:
  ssh homebase '~/valheim-capture/run-capture.sh --plan /home/derek/valheim-capture/plans/showcase-4k.tsv --width 3840 --height 2160'
  ssh homebase '~/valheim-capture/run-capture.sh --plan /home/derek/valheim-capture/plans/probe-gates-hover.tsv --width 1920 --height 1080'
  ssh homebase '~/valheim-capture/run-capture.sh --plan /home/derek/valheim-capture/plans/keepers-4k.tsv --width 3840 --height 2160'
  ssh homebase '~/valheim-capture/run-clips.sh --plan /home/derek/valheim-capture/plans/clips-showcase.tsv --width 1920 --height 1080 --fps 60'
  python plan_hearthview.py --cluster-ids 504,524,270,612,440 --cluster-points "E:/omen/steward-era17-arch/cluster-zdos.parquet" --out out/era17/guard-validate.json

Not sampled: a flash control clip; second time-variants at 474/627; the hover
lane in daylight; the 602/195 probe frames (shot, never reviewed); whether an
undecorated window or a wider framebuffer unlocks 4K clips; flash holds beyond
0.35 s; the 1080p-vs-4K effect on colour metrics.
