# Finding the art in a 9-million-object world

How we went from "teleport around and take screenshots by hand" to a ranked,
annotated shot list of every player-built structure in a Valheim world — and the
three times the data told us we were wrong along the way.

This is written as a walkthrough, not a spec. If you want the reference, read
[`README.md`](README.md). If you want to know *why* the tool looks like this,
read on.

---

## Where we started

People kept asking to see more of the builds. The way to show them was manual:
fly to somewhere dense, frame a shot, screenshot, repeat. To pick "somewhere
dense" we had one artifact — a committed `waypoints.json` at the repo root, 15
locations from Era 16, each with a piece count and often a builder name.

It was better than nothing and it had a real flaw. Look at ranks 5 through 8:

```json
{ "rank": 5, "x": -7220.7, "z": 17759.7, "pieceCount": 19744 },
{ "rank": 6, "x": -7220.7, "z": 18719.7, "pieceCount": 19744 },
{ "rank": 7, "x": -7223.3, "z": 15222.6, "pieceCount": 18492 },
{ "rank": 8, "x": -7222.2, "z": 16767.7, "pieceCount": 18489 }
```

Four entries, one x coordinate, two identical piece counts. Something was
generating near-duplicates, and we did not yet know what.

The file was produced by ranking cells of a fixed 500 m heatmap grid. A grid
cell is not a building. That is the whole problem in one sentence: **we were
ranking geography, not structures.** A grid cell can hold half a castle; a
castle can span four cells; and nothing about a cell tells you how tall the
thing in it is, which is most of what makes a screenshot worth taking.

## What already existed (check before you build)

Before writing anything we went looking, and found more standing than expected:

- **A working camera mod**, `valheim-camera-proof` — 746 lines of BepInEx C#
  with teleport, screenshot capture, weather and time-of-day forcing, and a
  hide-player toggle. It lives in the public `comfy` archive, deliberately not
  in this repo, so that a community claiming task stays claimable.
  *(That 746 is the figure as found, on 2026-07-02. The work below grew it to
  1,787 — camera boom, aim-at-target, an orbit runner and per-frame receipts.
  Anywhere else you see "746-line camera proof", it is quoting the before.)*
- **A workbench entry** for the whole pipeline (`camera-gallery`, status
  `recoverable-not-running`) that already names the gap: the flight-path mod has
  no code anywhere.
- **A parsed world**: ComfyStewardView's DuckDB analytics cache for Era 16,
  1.25 GB, already built. That save is 1.3 GB of `.db`; not re-parsing it saved
  the entire first afternoon.

The lesson that generalises: the reason the old waypoints file was weak was not
that anyone lacked skill. It was composed from two endpoints that already
existed, quickly, and it worked. Ask what the artifact was *for* before you
judge it.

## Step 1 — ask the data what it can answer

The question that decided the whole design: **is the Y coordinate stored?**

If the cache keeps only X and Z, then "how tall is this build" is unanswerable
without a re-parse, and everything downstream changes. So we surveyed the
StewardView Java sources before writing a line of Python. The answer:

```text
zdo columns: snapshot_id, zdo_index, prefab_hash, prefab_name, category,
             x, y, z, sector_x, sector_z, zone_x, zone_z,
             creator_id, owner_id, spawn_time_micros, flags
```

`y` is there. So are `creator_id` and `category`. The survey also turned up a
trap worth knowing: the in-memory `ZdoFlatStore` **discards BUILDING pieces**
after populating the heatmap, to save memory. Go through the DuckDB cache, never
the flat store.

Two consequences, both good: no Java changes, and no new REST endpoint. The
whole scan is a read-only query against a file that already exists.

```text
9,155,594 ZDOs total
3,475,009 of them BUILDING
```

## Step 2 — the first attempt, and why it was wrong

Clustering 3.4 million points with a classic algorithm like DBSCAN is not
practical at this size. But we do not need distance between every pair of
points — we need *contiguity*. So:

1. Snap every building piece to a 16 m grid cell.
2. Keep cells holding at least 4 pieces (drops stray fence posts).
3. Union any two occupied cells that touch.
4. Each connected blob is one structure.

That is a union-find over ~52,000 occupied cells — instant, and it produces
organic shapes instead of grid squares. It ran, and gave 1,830 clusters. It also
gave this:

```text
   #  score   pieces     h   foot m2  centre
   9 14.603    6,331  5126     7,243  (8000, 68, 9597)
  11 14.415    7,458   115    17,866  (-9590, 58, 7998)
  12 14.415    7,458   115    17,866  (-9590, 58, 8382)
```

Two failures in one screen. A structure **5,126 metres tall**. And ranks 11 and
12 with identical piece counts and identical dimensions at different places —
the same duplicate smell as the original waypoints file.

The temptation here is to clamp the height and move on. Don't. A number that
absurd is the data telling you something true.

## Step 3 — what the data was actually saying

Two queries settled it.

```text
BUILDING y distribution:  min -4421   median 63   99th percentile 5064
```

```text
pieces by distance from world centre:
  out-of-world >12k    2,123,529
  in-world (<=10.5k)   1,184,396
  edge 10.5-12k          167,084
```

**Sixty-one percent of this world's building pieces sit outside the playable
world radius**, and a large share sit at y≈5000. Our "world" was mostly not the
world.

Next question: junk, or real? Ask what a place has, not where it is:

```text
                signs   containers  portals  beds
  in-world     38,794      119,830    6,023  1,090
  outland     155,980       33,557    2,507    685
```

685 beds. 2,507 portals. **Four times as many signs as the entire in-world
map.** Nobody signs and sleeps in corrupt data. This is a real, heavily used
region.

Then the shape of it, which is the moment it all clicked:

```text
  x=-13440  z=8462   pieces=4,057   footprint=3,020 m2
  x=-12864  z=8462   pieces=4,023   footprint=3,020 m2
  x=-12288  z=8462   pieces=4,022   footprint=3,020 m2
```

Identical footprints, near-identical piece counts, spaced **exactly 576 m
apart**. 576 = 9 × 64, and 64 m is Valheim's zone size. That is a **grid of
templated build plots** — an instanced build area outside the normal map.

Which retroactively explains the original waypoints file. Its duplicate ranks 5
and 6 at `x = -7220.7` were never a bug in that script. They were two adjacent
plots in this grid, correctly reported. The old file was sending the camera to
the plot area without anyone knowing it was a distinct place.

## Step 4 — two fixes

**The 5 km structure was our bug, not the world's.** Clustering on an x/z grid
means a sky platform at y=5000 shares a cell with whatever sits on the ground
beneath it, so union-find welds them into one "structure". The fix is to cluster
in three dimensions: add a y coordinate to the cell key and union across the
26-neighbourhood instead of the 8-neighbourhood.

```python
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dy, dz) > (0, 0, 0):   # keep one of each reciprocal pair
                offsets.append((dx, dy, dz))
```

Tallest structure after the change: 113 m. Plausible, and it matches what a
large Valheim build actually is.

**The outland gets labelled, not filtered.** It would have been easy to drop
everything past 10.5 km and ship a tidier list. That would have silently thrown
away 1,255 structures that people demonstrably built, slept in, and covered in
signs. Instead every cluster carries `region`, `radius_m`, and `sky`, and
`--region` lets you choose. Whether a templated plot is worth photographing is a
judgement about the shot, and the person framing the shot should make it.

## Step 5 — scoring, stated as a guess

Ranking "photogenic" is not a fact, so the score is deliberately simple and
written where you can see it:

```python
mass        = log10(pieces)               # a big build beats a small one
relief      = min(height, 60) / 20        # vertical drama fills a frame
variety     = min(distinct_prefabs, 60) / 30
compactness = min(pieces / footprint_m2 * 4, 2)
score = mass * 2 + relief + variety + compactness
```

`compactness` is the one that earns its place. Without it the top of the list
fills with sprawl — a thousand scattered fence posts across a field outrank a
dense tower, because they cover more ground. Penalising footprint-per-piece
pushes the things that actually fill a viewfinder to the top.

Every input to the score is also its own column. If you disagree with the
weighting — and you should, it is untuned — sort by `size_y` or `pieces` and
ignore it.

## What came out

```text
1,833 structures at 400+ pieces
  578 in-world
1,255 outland
```

And the top of the in-world list looks like places, not coordinates:

```text
  #  pieces    h  portals  beds  signs  containers  creators
  1  21,464  100        4     0  2,857          23         5
  2  19,817   66        2    16    242         114         5
  4  20,130   50       32     5    105         137        10
 11  19,720  113       66    21    238         357        12
```

Rank 11 has 66 portals, 21 beds, and 12 distinct builders. That is not a
structure, it is a town. The columns tell you what kind of shot to plan before
you have seen it.

## Step 6 — the part where we stopped arguing about light

With a shot list and a camera, the first real session produced 31 setups × 4
moods. The moods came from the original kit: times of day at 0.25, 0.50, 0.72,
and 0.90, labelled morning, noon, sunset, night. Nobody had ever checked them.
They looked reasonable in source.

Rather than debate which ones felt good, we measured all 124 frames — mean
luminance and a 10th-to-90th-percentile contrast spread:

```text
        variant  time   n   luminance  contrast   unusable
     noon_clear  0.50  34       114.5     140.5         2%
   sunset_clear  0.72  34        68.4      91.4        23%
  morning_clear  0.25  34        36.5      55.1        88%
    night_clear  0.90  34        21.8      30.8        97%
```

**Half of every session was being thrown away.** 0.25 is not morning, it is
pre-dawn. 0.90 is not night photography, it is a black rectangle — 33 of 34
frames unusable. Every press of the capture key spent twenty seconds producing
two keepers and two duds, and it had been doing that from the first run.

Nothing about this was visible from reading the code. The variable was named
`night_clear` and it faithfully produced night.

The fix was not taste, it was a histogram: keep every time value inside the band
that measurably produces an image, and spend the freed budget on more frames.
Setup — flying there, framing the shot — is the expensive part; another dozen
exposures from a tripod already in position costs seconds. Four moods became
twenty-three, and the settle between them doubled to 6 s because atmospherics
crossfade rather than snap, so some earlier frames had been caught mid-lerp.

Then we measured again, and revision 1 was wrong in a more interesting way:

```text
   a_clear_t33   135.3   bright daylight
   a_clear_t70    81.8
   a_clear_t72    70.5
   a_clear_t74    48.7   thin
   a_clear_t77    25.2   dead
```

Two things fell out. The dusk cliff is *steep* — usable at 0.72, gone by 0.77 —
so 0.77 was cut. And 0.33 came back at 135, full daylight, while the old 0.25
had measured 36. Sunrise happens somewhere in that gap, which meant **the entire
morning golden hour had never been sampled.** The sweep had been front-loaded
toward dusk because that is where the good shots had happened to land, and that
assumption quietly excluded half the available light. Revision 2 probes 0.26,
0.29, and 0.32 — if they come back dead, that locates the dawn edge, which is
worth as much as a good frame.

### The metric was also wrong, and that matters more

The single best image from the early sessions — a torchlit causeway at dusk, wet
stone, statue silhouetted in mist — scores as **thin** by mean luminance. It is
a dark frame. So is a black rectangle.

Mean brightness answers *"is there an image here at all"*, not *"is it any
good"*. A dark frame **with highlights** is a different animal from a dark flat
one, and no single number separates them. So the verdicts got split: trust
`DEAD` at luminance 25, because nothing is recoverable there — but treat `thin`
as *go look at it yourself*, never as *delete*.

That is the honest shape of instrumentation. It is very good at finding what is
definitively broken and unreliable at judging what is good. Use it to delete the
black rectangles, not to pick the winners.

## Step 7 — taking the human out of the loop

Everything so far assumed a person at the keyboard: fly there, frame it, press a
key. That works, and it does not scale past one operator with an evening free.

Automating it changed which trade was correct. A human pays for *moving*, so 23
frames of one viewpoint varying only the light was sensible. A machine pays
nothing to move, and six photographs from six angles say far more about a
building than twenty-three of one wall. The count went down and the information
went up.

### Nothing in the repository can type into the console

The first design died immediately. The mod exposes `runplan` as a console
command, and there is no `SendInput`, `SendKeys` or `keybd_event` anywhere in
this codebase — the existing lab harness drives the game entirely through
files and in-process handlers, deliberately. So an unattended run cannot be a
sequence of typed commands.

The mod arms itself from a file instead. `orbit-request.json` exists → it picks
the character, opens the named local world, waits for the player, shoots the
plan, quits. Process exit becomes the completion signal, which is more honest
than a timer.

Two routes were rejected on evidence rather than taste. The approved plan called
for a local dedicated server, but no server binary is installed on this machine.
And the existing `Invoke-NativeValheimClient.ps1` writes a request that makes
another plugin auto-join a *server*, which would race this mod for the main
menu, and it has no path for loading a local world at all. Single-player turned
out to be both simpler and faster: ZDOs stream off disk with no network between
the camera and the world.

### Five runs, five faults, and no single instrument found them all

Each run changed exactly one variable.

| run | changed | fault it exposed | found by |
| --- | --- | --- | --- |
| 1 | baseline | framing on the bbox diagonal | comparing two numbers |
| 2 | reframe | camera inside a tree | opening the image |
| 3 | light | none (+34% contrast) | a histogram |
| 4 | occlusion recovery | `occluded:true` with `clearance:planned` | two fields contradicting |
| 5 | recovery timing | none — prediction held | the receipt |

**Framing on the bounding diagonal is wrong for anything that sprawls.** A
cluster's diagonal is inflated by outbuildings and walls. Dragon's Den measures
252 m corner to corner but its compact extent is 150 m, so framing on the
diagonal pushed the camera 267 m out to fit a fence and left the tower a smudge
in fog. Framing on `max(height, narrower horizontal)` fixed it.

**The light values were wrong and the data to prove it already existed.** The
planner shot at 0.70 because that *sounds* like golden hour. The 207-frame sweep
from Step 6 — run hours earlier, in this same repo — says 0.70 carries 26% less
contrast than 0.64. Measuring twice and reasoning from a plausible story anyway
is a failure mode worth naming.

### The two failures that argue for both kinds of instrument

**A camera inside a tree is invisible to every metric.** `pieces_near_aim` was
24,695 on that frame — the *highest* of the run — because a tree is geometry.
Luminance and contrast both looked healthy. Only opening the image found it.

**A timing bug is invisible in the image and screams in the data.** Run 4
produced a receipt with `occluded: true` and `clearance: planned`. Those cannot
both be true: same raycast, same two points. They ran either side of the world
streaming in — the clearance check happened at placement, before the trees
existed, so it honestly reported a clear view for a camera about to be buried in
a canopy. A raycast can only hit colliders that exist.

That second one is the more valuable failure, because it scales. Nobody will
open every frame of 480, but a field that contradicts itself still shouts. It is
also the argument for recording `lifted+16m` rather than a boolean: a bare
`occluded: true` would have read as a known-hard case and shipped.

### What the receipts bought

When run 1 came back hazy and small, the receipts said `lens_offset 1.3 m`,
`fov 65`, `occluded 0`, `pieces 16k–31k`. That is: the boom collapsed correctly,
the game's field of view matches what the planner assumes, nothing was blocking,
and the world had fully streamed in before every shutter. The capture was
provably sound, so the fault was provably in the plan.

Without that, the obvious move is to start tuning the runner — the half that was
already working.

## What is still open

- **Prefab names are hashes.** The cache stores `hash:538325542`, not
  `wood_wall`. StewardView's own backlog lists this as unresolved. We tried
  resolving them offline against `classification.json` and got 0 of 20 — that
  file holds 617 *item* names and no building pieces. The fix is a one-time
  in-game dump of `ZNetScene`'s prefab table, joined thereafter. Until then
  "dominant material" is a stable ID, not a word.
- **Builder names are IDs.** 660 distinct `creator_id`s on building pieces, none
  zero, so attribution works — but turning an ID into a name needs the player
  records that live in the running viewer, not the cache.
- **Dense forest still eats the camera.** The occlusion raycast at capture time
  catches a wall between the lens and the aim point. It does not catch a pine
  branch across a third of the frame, and no amount of standoff fixes a tree
  that is closer than the building.
- **No metric can judge a photograph.** The aesthetic head sorts competently and
  is confidently wrong at the edges. It makes a 1,411-frame pile reviewable; it
  is not a critic, and the top of its ranking is not the best picture.
- **Nothing here is packaged.** The planning half is in this repo, the mod is in
  the `comfy` archive, and the world cache and model weights are on one machine.
  Someone else cannot run this tonight, and that is the honest gap.

*The camera used to be the open item here — "the mod teleports and shoots; it
has no boom, orbit, or aim-at-target." That closed on 2026-08-06: `SetCameraBoom`,
`TryAim` and `RunShotPlan` all shipped, which is what Step 7 above is describing.*

## The reason this is worth writing down

None of the above is about one Valheim world. Every community that has run a
server for a few years is sitting on the same thing: a multi-gigabyte file
containing years of other people's craftsmanship, which nobody can see because
walking around stopped being a way to find out what is in there.

The pipeline that fixes that turned out to need **two tables and six columns** —
position, category, prefab, creator. Anything that can produce them can run this
whole chain, which is the difference between a gallery of our world and a tool
for anyone's. If you steward a community server, that safe harbour is yours
automatically; run it on your world and show people what they built.

But read the shape of the work above before treating it as free. Every step is
a workaround: prefab names are hashes because the format does not carry them,
building pieces had to come from a side cache because the main store throws them
away, and structures had to be *reconstructed* by union-find because a save file
does not record that a castle is a castle. That took several wrong turns —
a 5,126 m building and a world that was 61% somewhere else — before it produced
a shot list.

That is the real point: **this is reverse engineering, and it is temporary.**
Lumberjacks carries builds as first-class objects with known owners and known
extents. Ask it what exists and it tells you; no clustering, no hash tables, no
inferring ownership from where someone left a bed. Everything in this tutorial
is a bridge for the Valheim era.

So: fork it, run it on your world, that is what the contract is for. If you want
to build a business on it turnkey, come have a conversation first — the boundary
the project draws is extraction, not success.

## Five things worth stealing

1. **Ask the schema before designing.** One question — "is y stored?" — decided
   whether this was an afternoon of Python or a week of Java.
2. **An absurd number is a finding.** A 5,126 m building and a 61%
   out-of-bounds rate both looked like bugs to clamp. One was our bug, one was
   the most interesting fact about the world. Clamping would have hidden both.
3. **Label, don't filter.** Every filter you apply silently is a judgement you
   made on someone else's behalf. Ship the column and the flag.
4. **Measure the output, not the code.** The bad presets were invisible in
   source — correctly named, plausibly valued, quietly wasting half of every
   session. One histogram over 124 files found in a minute what reading would
   never have shown. Whenever a pipeline produces artifacts, the artifacts are
   the test data.
5. **Know what your metric cannot see.** The same measurement that correctly
   condemned the black frames also condemned the best photograph in the set.
   Instrument to find what is definitively broken; keep a human in the loop for
   what is good. A metric confident about quality is usually measuring
   something else.

## Privacy

Cluster records attribute real coordinates to real builders, and a gallery shows
other people's homes up close. That is the point of the tool and the reason to
be deliberate with it: ask before publishing shots of a world you do not own.
