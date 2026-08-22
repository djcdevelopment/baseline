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
