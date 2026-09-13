# Calibrating the refine loop: the fan is a regression, and the losses are upstream

Date: 2026-09-12 (UTC). Run under test:
[`2026-09-12-era11-refine-full`](../2026-09-12-era11-refine-full/) — 84 builds, 601 frames,
one game session, 1 h 48 m. Tools:
[`tools/selfie-stick/oracle_label.py`](../../../tools/selfie-stick/oracle_label.py) (new),
[`frame_judge.py`](../../../tools/selfie-stick/frame_judge.py),
[`frame_forecast.py`](../../../tools/selfie-stick/frame_forecast.py).

## The question

The refine loop shoots the planned pose, judges it on AM4's CPU about a second after the
shutter, fans 3–5 candidate poses around it and keeps whichever scores highest on
`liveTileShare · gradMean`. In the full run it moved the camera on 77 of 84 builds and `up20`
won 50 of them, with winner `skyFraction` collapsing 0.114 → 0.016 — the score has no
composition term, so a frontal elevation can never beat a three-quarter from above. Fixing
that needs labels. This directory is the attempt to get them, and what the labels then said.

## Part 1 — the oracle seat is vacant

Pass bar, written into `oracle_label.py`'s `PASS_BAR` before any run: **GOOD/BAD tier agreement
≥ 90 %** against the 47 hand labels of
[`era11-refine-r1`](../2026-09-12-era11-refine-r1/eye-labels.json), and **zero** BAD frames
returned as GOOD.

| run | model | rubric | agreement | BAD→GOOD | GOOD→BAD |
|---|---|---|---|---|---|
| 1 | `gemini-3.5-flash` | v1 absolute | **27.0 %** | **23** | 0 |
| 2 | `gemini-3.5-flash` | v2 evidence-first | **33.3 %** | 14 | 3 |
| 3 | `gemini-3.1-pro-preview` | v2 evidence-first | **10.8 %** | 4 | 8 |

v1 is a rubber stamp — 43 of 47 frames GOOD, including seven fog-outs and four
camera-inside-a-roof frames described as "well-composed and beautifully lit". v2 removes the
priming and forces observable flags before the class; flash gets noisier, not better. **The
premium rung is worse, not better**, so this is not a spend problem. The images arrive and are
seen (every description is frame-specific).

Why: of the 24 BAD frames, `BAD-mist` 7, `BAD-roof` 4, `BAD-skyladder` 4, `BAD-ladder` 4,
`BAD-aim-water` 4, `BAD-dark-texel` 1. **Twenty of twenty-four turn on where the camera is
standing, not on the picture.** A VLM cannot recover that from a 2D crop of beams. This is the
third instrument to hit the same wall on this world, after SegFormer's ADE20K mask
(`frame_geometry.py`: "the gap is domain, not capacity") and the LAION head
(`score_frames.py`: "a veto, never to rank the good").

## Part 2 — the labels, from the only qualified judge

[`ab-pairs.json`](ab-pairs.json): the 77 builds where the loop moved the camera, as blind pairs
of the planned pose against the fan's pick — sides randomised by build key, both masters already
on disk, no shutter. Judged in about ten minutes through a keyboard-driven light table.
[`pair-verdicts.json`](pair-verdicts.json) holds all 77;
[`calibration.json`](calibration.json) holds the numbers below.

**planned pose 25 · fan's pick 18 · both 1 · neither 33**

### The loop's rule is worse than doing nothing

| rule, over the 43 pairs the eye decided | hit rate |
|---|---|
| keep the planned pose, never move | **58 %** (25/43) |
| the loop's rule — take the higher score | **42 %** (18/43) |

The loop always takes the higher score, so 42 % is its own hit rate. It spent 601 frames to
move the camera on all 77 builds, and the pose it abandoned was the better photograph 25 times
against 18.

### Every metric it maximises points the wrong way

Share of decided pairs where the frame the eye picked had MORE of the quantity:

| the loop rewards | | the eye rewards | |
|---|---|---|---|
| centralLiveShare | 40 % | skyFraction | 58 % |
| score | 42 % | lumaMean | 58 % |
| gradMean | 42 % | lumaStd | 51 % |
| liveTileShare | 44 % | | |

The eye rewards light and sky; the score rewards texture fill. They are in opposition — and
among the 37 decided pairs where the loop climbed, **the climb lost 22 to 15**.

### 43 % of builds lost both frames

33 of 77. Those are planner failures, not camera-move failures: no pose the fan could reach was
worth publishing. The loop's own veto caught junk on 2 of 84 builds, so it is missing roughly
forty points of it. The lost builds are a measurably different population — median mass radius
64 m against 50 m, median length 156 m against 120 m, and *less* vertical (H/L 0.20 against
0.31). Big, long, flat and spread out.

⚠ `Neither` was offered beside `Both worth it` and the page called it "a build where both frames
lose", so it is read here as *neither frame is worth publishing*. A softer reading ("no
meaningful difference") would weaken Part 2's planner conclusion considerably. Unconfirmed.

## Part 3 — nothing is fittable yet

Leave-one-out, ridge logistic, feature subset selected **inside** each fold:

| model | baseline | LOO | modal subset |
|---|---|---|---|
| pairwise ranker | 58 % (keep planned) | 65 % | `lumaMean`, `lumaStd` |
| lost-build gate, pre-shutter only | 57 % (all shootable) | 65 % | `p90r`, `height` |
| lost-build gate, best single feature | 57 % | 66 % | incumbent `centralLiveShare` |

Three extra frames out of 43. Directionally consistent with the counts, statistically nothing.
**The counts are the finding; the models are not.** No composition term ships on 43 decided
pairs.

## What this changes

See [`PLAN-next.md`](PLAN-next.md). In short: restrict the fan to builds whose incumbent was
vetoed (601 frames → 84, and 42 % → 58 % on the only measurement that exists), then fix the
planner's aim selection, which is where 33 of 77 were actually lost.

**Method note.** The 47 eye labels have now been spent twice as a qualification set, so a prompt
or a model tuned against them is fitted to them. Anything fitted downstream must validate
against the pair verdicts or a fresh human slice — never against those 47.

**The instrument note.** Ten minutes of pairwise judging produced more usable signal than three
vision-model runs and 601 automated frames. The light table belongs in `tools/`, not in a
scratch directory.
