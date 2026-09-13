# Next: turn the fan off, then fix the planner

Written 2026-09-12, on the evidence in [README.md](README.md) beside this file. Supersedes an
earlier plan that assumed the refine loop needed a better objective. Derek's 77 pair verdicts
say something stronger: **the loop is net-harmful and should stop moving the camera at all**,
and the losses it was built to fix are almost all upstream of it.

Not started. Nothing here has been implemented.

## An assumption to confirm before Step 2

`Neither` was offered beside `Both worth it`, and the light table called it "a build where both
frames lose" — so this plan reads the 33 as *neither frame is worth publishing*. If Derek meant
something softer ("no meaningful difference between these two"), Step 1 is unaffected but
Step 2's premise weakens considerably. One question, or a spot-check of five of the 33, settles
it. **Ask before starting Step 2; Step 1 does not wait on it.**

---

## Step 1 — Stop the fan. It is a regression, and the proof is already in hand.

`refine_worker.py` runs a fan of 3–5 candidate poses around every build and keeps whichever
scores highest. Restrict it to the one case where moving is strictly better than nothing: when
the incumbent is **vetoed**. The v2 `gate()` already expresses that path (`needs-aim`,
`needs-sky`, `needs-demist` with `forced_moves`) — the change is to stop fanning on builds whose
incumbent passed.

- `ComfyStewardView/tools/era-archive/refine_worker.py`: `refine_build()` fans only when
  `gate()` returned a `needs`; `--rounds` defaults to 0; the improver path becomes opt-in and is
  documented as measured-harmful.
- `baseline/tools/selfie-stick/frame_judge.py`: `score()` keeps its job as the tie-break
  *inside* a gated build's fan, and its docstring records that it is anti-correlated with the
  eye as a between-pose ranker (42 %) and must not be used as one.

**What it buys.** 601 frames become 84. The session drops from 1 h 48 m to well under an hour,
and the shutter freed is the budget Step 2 needs. Quality goes from 42 % to 58 % on the only
measurement that exists.

**Verification, with no reshoot.** Replay the 77 pairs under the new rule: it returns the
incumbent every time, which is 25 of Derek's 43 decisions against the loop's 18. Assert it in
the replay harness so a future change that re-enables the improver has to beat 25.

## Step 2 — Fix the planner, because that is where 33 of 77 were lost.

The lost builds are measurably a different population: median mass radius 64 m against 50 m,
median length 156 m against 120 m, and *less* vertical (H/L 0.20 against 0.31). Big, long, flat,
spread out. `plan_detail_shots.py` solves the camera for a target pixels-per-metre and accepts a
partial view — but it still picks **one aim point per build**, and on a 156 m sprawl that point
lands somewhere arbitrary.

So the work is in aim selection, not camera angle:

- **Aim at a mass, not at a build.** `frame_forecast.mass_radii` already computes the radii that
  detect a sprawl (`sprawlRatio = p100/p90`). Cluster the build's BUILDING ZDOs into coherent
  masses and give each its own detail shot — which is what `plan_detail_shots.py`'s own
  docstring says the answer is ("the settlement that reads as a smudge at 180 m is six legible
  buildings up close") and what it does not yet do per build.
- **Score candidate aims for free, before the shutter.** `frame_forecast.py`'s `project` /
  `coverage` / `camera_basis` already reproject a point set through a pose and return
  `bboxFill`, `occupancyFill`, `inFrameFraction`. Lift them into a `pose_forecast.py` callable
  per candidate. Per Derek's ruling, no mod change: pre-bake each build's decimated point set
  into `campaign.json` at `--prepare` time on OMEN, where duckdb lives, so AM4 stays
  dependency-free and released ComfyCameraProof 0.2.5 stays pinned.
- **Give the prior a typology.** Harvest from `deepagents-shot-director` as agreed —
  `director/positioning.py`'s `compute_pca_orientation` for orbit bearings on the build's true
  long axis, and `director/typology_classifier.py`'s typology → target elevation, aim-height
  ratio and standoff. This is now the *more* important half of that harvest, not the lesser:
  the planner is the problem, and typology is a planner-side prior. Retire
  `local_loop_controller.py`, `b70_director_agent.py`, `am4_remote_runner.py`, `run_ledger.py`
  and `promotion.py`, leaving a README that names where each piece landed.
- **Add sky and light to the planner's own objective**, since that is what the eye rewarded.
  The horizon line is exact from the pose; the sky band above the subject's projected bbox costs
  nothing to compute and needs no image.

**Verification — 33 shots, one short session.** Replan only the 33 builds that lost both frames,
shoot the new planned pose for each (~15 minutes of shutter), and put the new frame against the
old planned pose in the same light table. The instrument exists and the question is identical.
The bar: of the 33 builds where nothing was worth publishing, how many now have a frame Derek
keeps? Anything above zero is progress that 601 frames of fanning did not deliver.

## Step 3 — Grow the label set with the instrument that worked.

Ten minutes of pairwise judging produced more usable signal than three vision-model runs and
601 automated frames. Treat it as the project's measuring instrument, not a one-off:

- Generalise the light-table generator (session scratch, `scratch/ab/make_page.py`) into a
  committed tool that takes any set of frame pairs and publishes the page.
- Run it on the Step 2 reshoot, then on era 14's published frames, until n supports a fit.
- Re-run the fit when n passes roughly 150 decided pairs. Until then the in-loop rule stays the
  veto it is good at, and no composition term ships on 43 samples.

## Step 4 — Only then, the fitted critic.

Still blocked on Step 3: features from `frame_judge.Judge.measure` plus the free geometry,
labels from the pair verdicts, an ablation (geometry only → + master plane → + SegFormer →
+ CLIP) that decides whether SegFormer keeps its 585 ms of the 814. Ship as coefficients.
Validate against held-out pairs — never against the 47 eye labels, which have now been spent
twice as a qualification set.

---

## Files

**Change**
- `C:\work\ComfyStewardView\tools\era-archive\refine_worker.py` — Step 1 (`refine_build`,
  `gate`, `--rounds` default); Step 2 (`prepare*` bakes the point set into `campaign.json`)
- `C:\work\baseline\tools\selfie-stick\frame_judge.py` — record the 42 % finding on `score()`
- `C:\work\baseline\tools\selfie-stick\plan_detail_shots.py` — per-mass aims, PCA bearings,
  typology prior, sky term

**Add**
- `pose_forecast.py` — per-candidate projection, lifted from `frame_forecast.py`
- a committed light-table generator

**Landed with this evidence**
- `tools/selfie-stick/oracle_label.py` — the oracle labeller and qualification harness

**Retire**
- `deepagents-shot-director/director/{local_loop_controller,b70_director_agent,am4_remote_runner,run_ledger,promotion}.py`

## What this abandons

- **The composition term as an immediate deliverable.** n=43 does not support it. It returns at
  Step 4.
- **A vision model anywhere in the pipeline.** Qualified against and failed; recorded.
- **The premise that better camera moves were the lever.** The moves were the regression. The
  planner is the lever.
