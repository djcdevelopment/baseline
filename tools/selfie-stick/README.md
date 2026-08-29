# selfie-stick

Find every player-built structure in a Valheim world, rank them as camera
subjects, and emit a shot list you can fly.

For the story of how this was built and what the data turned out to be hiding,
read [`TUTORIAL.md`](TUTORIAL.md).

For the reproducible 20-building Library of Congress HABS measured-drawing corpus,
read [`HABS-HARVESTER.md`](HABS-HARVESTER.md). That probe stops at acquisition and
normalization; it does not convert drawings into Valheim pieces or ZDOs.

For the measured-drawing → metric graph → routed Valheim candidate → portable Build
Capsule experiments, read
[`ARCHITECTURAL-ROUNDTRIP.md`](ARCHITECTURAL-ROUNDTRIP.md). The v0 slice establishes F1
massing; its earned follow-on compiles opening-aware wall bays and explicit appendage roofs
into an F2 weather shell. Both stop before live ZDO creation when the Creator Session
boundary is unsafe or unresolved.

For the automatic 20-building transfer curriculum—lesson-free controls, size/height
clustering, cumulative lesson packs, generic compilation, GPU previews, deterministic
capsules, and explicit success gates—read
[`ARCHITECTURAL-CURRICULUM.md`](ARCHITECTURAL-CURRICULUM.md). Its fixture dashboard proves
the machinery only; the real experiment fails closed when its pinned local vision model is
not available. The independent real OCR/CV audit does run without that model: its frozen
question is in [`architectural-ocr-audit-v1.json`](architectural-ocr-audit-v1.json), and
the deterministic 18-signal, per-cluster visual adjudication is in
[`architectural-ocr-review-v1.json`](architectural-ocr-review-v1.json). It admits local
dimensions as semantic constraints while explicitly denying autonomous scale authority.

For the 2026-08-27 clean-motion capture receipt, including the accepted artifact,
rejected variants, and the raw-slicer defect, read
[`MOTION-RESULTS-2026-08-27.md`](MOTION-RESULTS-2026-08-27.md).

## What it does today

`scan_clusters.py` reads ComfyStewardView's DuckDB analytics cache read-only —
no Java, no running viewer, no re-parse of the world `.db` — clusters BUILDING
ZDOs in 3-D, and writes one row per structure:

- **where**: `center_x/y/z` (the teleport target), plus the full bounding box
- **how big**: `size_x/y/z`, `footprint_m2`, `diagonal_m`, `pieces`
- **how to shoot it**: `suggested_standoff_m`, `suggested_camera_y`
- **what it is**: `distinct_prefabs`, `top_prefab`, `portals`, `beds`, `signs`,
  `containers`, `item_stands`, `interiors`
- **whose**: `top_creator_id`, `top_creator_share`, `distinct_creators`
- **where in the world**: `region` (in-world / outland), `radius_m`, `sky`
- **yours to fill in while flying**: `visited`, `verdict`, `notes`

Outputs land in `out/`: `clusters.json` (for the web app and the mod),
`clusters.csv`, and `clusters.xlsx` (filtered and frozen, ready to annotate).

## Picking up where the last session left off

One driver knows every run, which machine shoots it, what has already fired, and what
would count as it working. Run it with no arguments:

```powershell
cd tools\selfie-stick
.\Invoke-SelfieStick.ps1
```

It prints the registry: how many shots, roughly how long, the verdict that decides
whether the run worked, and a **status derived from evidence** rather than kept by
hand. That last part is the point. The queue it replaces had no notion of done, so
three of its seven rows still advertised captures that had already been shot days
earlier.

```powershell
.\Invoke-SelfieStick.ps1 -Run <name> -Preflight    # every check, fires nothing
.\Invoke-SelfieStick.ps1 -Run <name> -Plan         # plan it, then shoot it
.\Invoke-SelfieStick.ps1 -Run <name> -On am4       # override the host
```

Captures run on **OMEN** or on **AM4**, and the driver owns the difference. On OMEN it
calls `Invoke-OrbitCapture.ps1` / `Invoke-InteriorCapture.ps1`, which keep their own
launch, wait, and byte-exact config restore. On AM4 it stages the plan over ssh, calls
`run-capture.sh`, then pulls the frames and receipts back — removing the destination
first and hashing both ends, because `scp` does not truncate and a short write leaves a
stale tail that passes every size check.

It also owns the two settings that used to be edited by hand with the game closed:
`settleSeconds` (the old queue declared it on two rows and read it nowhere) and the
`light_dump` arming of `orbit-request.json`, which takes precedence over a shot plan and
will dump and quit instead of shooting.

It never publishes; that stays a separate act.

## Two ways to photograph a night

**`plan_nightsky.py` aims at the moon.** It solves where the body is from the
engine's own arc and puts it at a chosen fraction up the frame, tilting the camera
*up*. Validated: the disc sits on the directional light to within 0.2 degrees median,
and its angular radius is about 6 degrees (`--rho`, which defaulted to 0 for a long
time and biases every aim point by roughly a disc radius).

**`plan_channel.py` aims down a channel and leaves the moon out of frame.** It exists
because aiming at the moon composes the moon, which is the least interesting thing a
night frame can do. A full moon is a lamp, and a lamp is worth more raking across a
scene from off-axis than sitting in the middle of it.

```powershell
python scan_channels.py --rooftops out\era17ooftops.json --out out\era17\channels.json
python plan_channel.py  --channels out\era17\channels.json --out out\era17\channel-1.json
```

`scan_channels.py` measures, per stance and bearing, **how high the canopy stands
above the lens** and **how far the ray runs before it reaches open water**. The canopy
angle is the measurement a gap distance cannot make: from a 68 m roof a 20 m fir on
30 m ground tops out at 50 m and is not in the picture at all, while the same fir
closes the view completely from a 12 m roof. A tree's ZDO carries its pivot, which is
real ground elevation, so exactly one constant is assumed (`--tree-height`) and a
wrong value moves every angle the same way.

Open water comes from `<World>_mapTexCache`, the 2048x2048 biome PNG Valheim writes
beside the save. The runbook previously recorded that seaward direction "is not
derivable from the DuckDB cache (no terrain)" — true of the cache, false of the
machine.

`plan_channel.py` then picks the bearing by the channel, **refuses any bearing within
40 degrees of the moon** (that is the shot the other planner already takes) and any
beyond 140 (moon behind the camera, flat frontal light), and sets pitch so clear sky
fills the top sixth-to-third of the frame. Every pitch it emits is *positive* — tilted
down — which is the opposite of the night planner and the reason its frames can show
depth at all.

A useful side effect: it does not need a disc. A direct moon shot depends on phase and
cloud; a raked one needs only that the moon is up.

The era arguments are the thing worth not typing by hand. Point a run at the wrong
`clusters.json` and every frame joins to another era's cluster ids — the mislabelling
era isolation exists to prevent, and it does not announce itself.

Two of the queued runs need the light held. `plan_shots.py --fires` and
`plan_interiors.py --fires` mark every frame so the mod holds the builders' own
fires lit for the shot; `--storm-shots 3 --storm-only` emits the exterior storm
A/B (`storm`, `storm_dark`, `storm_flash`) on the hero framing and nothing else.
Both write two optional trailing TSV columns, so every plan already on disk still
reads exactly as it did.

Why it is needed is the uncomfortable part: a capture world copy loads with every
hearth, brazier and groundtorch burned to zero, because `Fireplace` catches up the
fuel that should have burned while the zone was unloaded. Every twilight and night
frame in the gallery was shot in a build whose lights were out. See the runbook
section "The lights were never on".

The reasoning behind what is queued, and the measurements behind it, are in
[`docs/internal/RUNBOOK-selfie-stick-era17-series-2026-08-22.md`](../../docs/internal/RUNBOOK-selfie-stick-era17-series-2026-08-22.md).
The readable summary of what those measurements mean for *how to aim the camera* — the
technique literature, the correlations, and a ranked shot list — is
[`docs/internal/aiming-the-selfie-stick.html`](../../docs/internal/aiming-the-selfie-stick.html).

## Run it

```bash
python tools/selfie-stick/scan_clusters.py
```

Takes a couple of minutes against Era 16. Useful flags:

```bash
python tools/selfie-stick/scan_clusters.py --region in-world --top 40
```

For a multi-snapshot Steward cache, select the era explicitly and keep its
derived artifacts in their own namespace:

```powershell
python tools/selfie-stick/scan_clusters.py --db E:\omen\steward-era17\out\world-cache.duckdb `
  --world-id ComfyEra17 --out tools\selfie-stick\out\era17
```

`Invoke-OrbitCapture.ps1` accepts matching `-Clusters`, `-PlanOut`,
`-GalleryDest`, and `-DisplayIndex` arguments. It records the exact new capture
run IDs and rebuilds the gallery from only those runs, preventing cluster IDs
from another era from being joined to the new world.

The capture entrypoint requires ComfyNetworkSense 0.4.8 or newer with
`portalConnectionCacheEnabled = true`. It verifies activation in the BepInEx log so a
large portal network cannot silently fall back to Valheim's main-thread scan. It also
hides the NetworkSense HUD for the capture process and restores the operator's exact
configuration bytes afterward. The always-visible transport recovery tab is retained
in the running client so the portal/network instrumentation stays intact, then removed
from the right edge of the derived 4K web images; original screenshots are not altered.
An era may also provide `derived-frames.json` for an explicit detail crop of an accepted
orbit capture when one template has no usable sixth sightline. These rows are labeled
`source: derived` and retain their `derived_from` image ID; they never masquerade as a
new camera receipt.

| flag | default | what it does |
| --- | --- | --- |
| `--db` | the Era 16 cache | ComfyStewardView DuckDB cache path |
| `--out` | `./out` | output directory |
| `--cell` | `16` | horizontal grid size (m) for connectivity |
| `--y-cell` | `16` | vertical grid size (m) |
| `--min-cell` | `4` | pieces needed for a cell to count as occupied |
| `--min-pieces` | `400` | drop clusters smaller than this |
| `--region` | `all` | `in-world`, `outland`, or `all` |
| `--world-radius` | `10500` | playable world radius (m) |
| `--top` | `0` | keep only the top N by score (0 = all) |
| `--prefab-names` | — | JSON map of prefab hash → name, once dumped in-game |

Lower `--min-pieces` to see small builds; raise `--cell` to merge neighbouring
structures into districts.

## Requirements

`duckdb` (required) and `openpyxl` (optional — without it you still get JSON and
CSV). Both were already present on this machine.

## Reading the output

`score` is an untuned heuristic, not a measurement — its formula is in the
source and every input to it is also a column. Sort by `size_y` for towers, by
`portals` for hubs, by `pieces` for sheer mass.

`region` is labelled, never silently filtered. About two thirds of this world's
structures sit outside the 10.5 km world radius in a grid of templated build
plots spaced 576 m apart. They are real and inhabited; whether they are what you
want to photograph is your call. See the tutorial.

`top_prefab` is currently a stable hash ID rather than a name — StewardView's
cache does not resolve building-piece prefabs. A one-time in-game dump of
`ZNetScene`'s prefab table, passed via `--prefab-names`, fixes it permanently.

## Point it at your own world

Nothing here is specific to Era 16, or to Comfy, or to ComfyStewardView. The
scanner reads **two tables and six columns**. That is the whole contract:

```sql
zdo(category TEXT, x DOUBLE, y DOUBLE, z DOUBLE,
    prefab_name TEXT, creator_id BIGINT)

world_snapshot(source_path TEXT, parsed_at TEXT)   -- optional, labelling only
```

`category` needs the value `'BUILDING'` on player-placed pieces. `creator_id`
may be 0 or absent — you lose attribution, nothing else. `prefab_name` may be a
hash. If your parser gives you those columns, this works, and it does not care
what produced them.

`clusters.json` intentionally keeps only aggregate bounds. For exact per-piece
height and camera-relative depth, generate its private `cluster-zdos.parquet`
companion with `export_cluster_points.py`; `plan_shots.py --cluster-points ...`
then frames against every ZDO rather than a flat box. The schema, frozen-id rule,
camera math, verified Era17 receipt, and rerun commands live in
[`ZDO-COORDINATES.md`](ZDO-COORDINATES.md).

The first component-local roof-semantics lap, its frozen photographic holdout,
and the failed planner-promotion gate are recorded in
[`ROOF-SEMANTICS-RESULTS-2026-08-27.md`](ROOF-SEMANTICS-RESULTS-2026-08-27.md).
Those semantics remain report-only.

On AM4, capture resolution and physical monitor mode are deliberately separate:
Valheim uses the 3840x2160 X framebuffer while `Invoke-SelfieStick.ps1` guards the
active output at 1920x1080 before and after a run. The first 240-frame exact-point
series, its hashes, display proof, runtime recoveries, and deferred-publication
edge are recorded in
[`COVERAGE-XYZ-4K-RESULTS-2026-08-27.md`](COVERAGE-XYZ-4K-RESULTS-2026-08-27.md).

The contract exists so no one is *technically* locked in. ComfyStewardView —
which built the cache used here — is proprietary, all rights reserved. If this
pipeline could only ever run on its output, a community with its own parser
would be stuck. It isn't: point any Valheim world parser at the schema above,
load it into DuckDB or SQLite, and the rest of the chain runs unchanged.

Concretely, to run this against your own server's world:

1. Parse your world `.db` with any tool that can emit ZDO position, category,
   prefab, and creator — write it to the schema above.
2. `python scan_clusters.py --db your-world.duckdb` → your structures, ranked.
3. Optional for exact 3-D framing: `python export_cluster_points.py --db
   your-world.duckdb --clusters out/clusters.json`.
4. `python make_waypoints.py --install` → the shot list, in your game.
5. Fly it with the camera mod and shoot.

The schema contract is an anti-lock-in guarantee, not a licence workaround. The
code in this directory is governed by the repository's
[`LICENSE`](../../LICENSE) like everything else: reading, testing, and
modifying are free, and a community steward running their own server is covered
automatically by the safe harbour in [`LICENSING.md`](../../docs/legal/LICENSING.md) — go,
enjoy it, no permission needed and no royalty owed.

If instead you are packaging this as a turnkey offering, or you are a large
organisation or past the safe-harbour limits, come talk to us first
(`licensing@djcdevelopment.com`, see [`COMMERCIAL.md`](../../docs/legal/COMMERCIAL.md)).
The boundary the project draws is extraction, not success — and getting to the
point where these coordinates fall out of an opaque binary took a lot of failed
attempts that are not visible in the finished script.

## Why this exists at all

This whole directory is **reverse engineering**, and it is temporary. Every hard
part here — the hash-only prefab names, the discarded building pieces, the
unresolvable creator IDs, the 3-D clustering needed to recover structures that
the game already knows are structures — is a workaround for a save format that
was never meant to be read from outside.

Lumberjacks exposes this natively. When a build is a first-class object with a
known owner and known extents, none of this scanning is necessary; you ask.
Treat this tool as a bridge for the Valheim era, not as the architecture.

## The pieces, and what each one does

```text
scan_clusters.py        world .db cache  ->  clusters.json      structures + geometry
export_cluster_points.py cache + clusters -> cluster-zdos.parquet exact frozen membership
plan_shots.py           clusters + points -> shotplan.tsv       depth-aware camera positions
Invoke-OrbitCapture.ps1 shotplan.tsv     ->  screenshots        unattended, no keyboard
build_valheim_index.py  screenshots      ->  index.json         joined back to structures
name_structures.py      screenshots      ->  cluster-names.json named by a vision model
gallery/index.html      index.json       ->  the gallery        vote / request / claim
```

Two ways to shoot:

**By hand.** Install the camera mod, run `make_waypoints.py --install`, and use the
arrow keys in game — right for the next build, left for the previous, up to capture
the current framing in 23 lights. You choose every composition.

**Unattended.** `Invoke-OrbitCapture.ps1 -Top 40` plans six angles per structure,
using exact per-ZDO height and depth when `-ClusterPoints` is supplied and the
bounding box otherwise. It launches the game, opens the world, places and aims
the camera, waits for the world to stream in, recovers from a blocked view,
shoots, and quits. Nobody touches the keyboard.

The automated path exists because a human pays for *moving* and a machine does
not. Twenty-three frames of one viewpoint was the right trade for a person; six
viewpoints is the right trade for a machine.

## Automatic HABS CSS envelope-fit probe

`probe_architectural_css_fit.py` connects the frozen real-OCR audit to an automatic
primary-envelope candidate and a CSS evidence viewer. It reads all 20 HABS buildings,
finds labelled plan/elevation/section panels, combines complete printed scale notation
with TIFF scan DPI, binds explicit dimensions to merged dimension lines, reserves an
independent section/elevation, and publishes every promotion failure instead of completing
the building by assumption.

```powershell
Set-Location C:\work\baseline
$python = '.\tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'
& $python .\tools\selfie-stick\probe_architectural_css_fit.py run
& $python .\tools\selfie-stick\probe_architectural_css_fit.py verify
& $python .\tools\selfie-stick\probe_architectural_css_fit.py serve --port 8878
```

Revision `3899e363a8b63658dc8a` routed all 20 buildings and emitted 168 automatic
panels with 165 bound dimension candidates. `tx1037` and `ak0535` reached
`G1_UNVALIDATED`; neither predicted its held-out section within the frozen tolerances.
No building reached validated G1, and the hidden `sd0401` oracle failed after recovering
its 15.929 m width exactly. That negative result is the point of the lap: sheet calibration
and plan fitting are connected, while primary-mass selection and vertical roof/eave
semantics are now the bounded next gap. CSS is a projection and residual instrument;
`building.graph.json` remains the candidate metric authority.

### Three-building topology diagnostic

`probe_architectural_css_topology.py` inspects that bounded gap without changing the
20-building fitter. It is pinned to `sd0401`, `tx1037`, and `ak0535`; overlays candidate
structural line families, measures cross-role panel overlap, groups explicit dimension
chains, and compares mass/datum ownership. The `sd0401` candidates are sealed before its
accepted graph is loaded.

```powershell
Set-Location C:\work\baseline
$python = '.\tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'
& $python .\tools\selfie-stick\probe_architectural_css_topology.py run
& $python .\tools\selfie-stick\probe_architectural_css_topology.py verify
```

Revision `cf5c847a7f5232d38c0c` reports `ATTRIBUTION_SEPARATED` and verifies 49 hashed
artifacts. It confirms three different failures: `sd0401` panel/primary-mass ownership,
`tx1037` ceiling-versus-eave semantics, and `ak0535` floor/basement plus labeled-submass
ownership. This is diagnostic evidence only—no promotion gates or automatic corpus behavior
changed.

### Pre-CSS topology transfer v1

`probe_architectural_css_fit_v1.py` implements the locked follow-up without changing v0.
It emits `architectural-evidence-graph/v1` before the metric graph: view interiors are
disjoint, dimensions belong to explicit chains, plan masses remain separate, and vertical
labels become typed datums. The CSS stage accepts only the sealed evidence and metric graphs,
emits `architectural-css-residual/v1`, reports upstream attribution, and always leaves
`corrected_geometry` null.

The three-building development split must pass before it can be sealed; only then can the
remaining 17 buildings be exposed once.

```powershell
Set-Location C:\work\baseline
$python = '.\tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'
$repro = '.\tools\selfie-stick\out\architectural-css-fit-v1-repro'

# The recorded default output is already sealed; reproduce only into a fresh output root.
& $python .\tools\selfie-stick\probe_architectural_css_fit_v1.py develop --seal --out $repro
& $python .\tools\selfie-stick\probe_architectural_css_fit_v1.py blind --out $repro
& $python .\tools\selfie-stick\probe_architectural_css_fit_v1.py verify --out $repro
& $python .\tools\selfie-stick\probe_architectural_css_fit_v1.py serve --port 8879 --out $repro
```

Revision `da9fb53b6e49c3718ea3` passed all seven development checks: `sd0401` recovered
15.928975 × 4.333875 m and a 3.302 m ridge with zero cross-role view overlap; `tx1037`
kept ceiling separate from eave; and `ak0535` kept LOG CABIN and ADDITION separate without
adopting the basement width. The sealed blind result was **0 validated G1, 13 A0-triaged,
4 held; `INSUFFICIENT_AUTOMATIC_EVIDENCE`**. Both negative controls remained unpromoted.
This v1 result must not be tuned: the blind set showed that complete scale notation rarely
survives ownership into the selected primary plan, 14 buildings still lack a selectable
two-axis primary mass, and 16 lack both typed eave and ridge evidence. A new experiment needs
a new development/holdout design; these 17 are no longer blind.

The unchanged blind rerun validates all 17 receipts with zero evidence reads, topology runs,
CSS runs, OCR/VLM calls, network requests, downloads, or world work. Verification passes all
20 artifact sets.

### Pre-CSS causal repair v2

`probe_architectural_css_fit_v2.py` implements the next upstream experiment without tuning or
reusing the revealed v1 holdout as blind evidence. The old 20 buildings are development data;
`habs-corpus-v2-holdout.json` freezes eight new LOC buildings (27 sheets, seven states, four
building types) as the external holdout. LOC advertised 25,859,916 bytes for those masters,
but the integrity-checked downloads total 726,848,012 bytes. The local OCR/CV audit is frozen
at revision `b1743fa5580583635f51`: 1,109 tokens, 47 strict dimensions, 76 held near-misses,
47 CV candidates, and zero OCR-stage network or VLM calls.

The v2 evidence graph adds line-owned dimension axes, compatible scale consensus with distinct
origins, closed-loop x/z scale anchors, topology-corroborated missing-axis extents, and paired
ridge/eave topology. CSS still hashes the completed metric graph, performs zero discovery,
and leaves `corrected_geometry` null.

Development revision `2c3595654934efe9a5ad` is valid but deliberately **not sealed**. Against
the 17 revealed v1 failures, selected primary masses improved from 3 to 8, honest scale
consensus reached 6, and calibrated paired roof datums reached 7. Both development negative
controls stayed unpromoted. The regression checks still recover exact `sd0401` geometry,
preserve `tx1037` ceiling semantics, and keep the `ak0535` LOG CABIN/ADDITION split.

The composition gate remains the stop: 0 of the 17 failure-cohort buildings reached validated
G1 because the mass, scale, roof pair, and independent CSS view do not yet coexist on the same
building. `tx1037` reaches G1 and `ak0535` reaches G1-unvalidated, but both are known regression
controls. Development acceptance therefore reports `FAIL`; `blind` was never run and all eight
fresh buildings remain unexposed to the fitter.

```powershell
Set-Location C:\work\baseline
$python = '.\tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'

# Cached development diagnosis; exits nonzero because the scientific gate is unmet.
& $python .\tools\selfie-stick\probe_architectural_css_fit_v2.py develop

# Artifact integrity passes while reporting BLOCKED_AT_DEVELOPMENT_GATE.
& $python .\tools\selfie-stick\probe_architectural_css_fit_v2.py verify

# Verify the untouched holdout's local OCR evidence contract.
& $python .\tools\selfie-stick\probe_habs_ocr_audit.py verify `
  --charter .\tools\selfie-stick\architectural-ocr-audit-v2-holdout.json `
  --source-charter .\tools\selfie-stick\architectural-curriculum-v2-holdout-source.json `
  --selection .\tools\selfie-stick\habs-corpus-v2-holdout.json `
  --corpus .\tools\selfie-stick\out\loc-habs-v2-holdout\corpus `
  --out .\tools\selfie-stick\out\architectural-curriculum\real-ocr-audit-v2-holdout
```

Do not run v2 `blind`, lower the frozen two-G1 development threshold, or inspect the fresh
holdout to tune the fitter. The next earned connector is cross-sheet composition: prove that a
selected plan mass and a calibrated vertical roof pair describe the same building frame before
CSS is asked to validate it.

### Automatic frame registration v3

V3 implements that connector in `probe_architectural_css_fit_v3.py` while preserving every
v2 source and artifact. A new HTTP-sized acquisition plan froze eight replacement buildings
(29 sheets, seven states, four types, two metadata-sparse controls) at 123,099,962 bytes before
OCR. Its verified local OCR revision is `315ba9abcf599f639fa7`.

The pinned v2 diagnostic baseline over the 28 development buildings is
`7331f32e25b034d03d70`. V3 development revision `5333d5eaed593d7607e4` preserves all
165 automatic candidates and all regression checks, but the gate remains **FAIL**: the original
failure cohort retains 8 selected masses, 6 scale consensuses, and 7 calibrated roof pairs,
yet produces 0/2 validated G1. No different-sheet plan/vertical candidate shares an exact OCR
section marker and a matching floor/grade origin. `tn0304` and `tn0305` each pass the other five
gates, including compatible metric span, which sharply localizes the next upstream gap.

No development lock or blind artifact exists. Do not seal, run `blind`, reinterpret elevation
direction labels as section markers, or lower the gate. See
`HANDOFF-AUTOMATIC-CSS-FIT-V3-2026-08-28.md` for exact cached commands and the next diagnostic.

## Known rough edges

- **A ZDO coordinate is a prefab pivot, not a mesh corner.** Point-cloud framing
  captures placement depth but can under-frame the outer half-extents of a sparse
  piece. See [`ZDO-COORDINATES.md`](ZDO-COORDINATES.md).
- **Prefab names are hashes.** StewardView's cache does not resolve building
  pieces. A one-time in-game dump of `ZNetScene`'s prefab table would fix it
  permanently.
- **Builder IDs are not names.** 660 distinct `creator_id`s attribute cleanly,
  but turning one into a person needs the running viewer's player records.
- **A held fire that gets culled looks exactly like a cold one.** `LightLod`
  drops light at 40 m and shadow at 20 m, and its static `m_lightLimit` caps how
  many lights burn at once no matter the distance. The capture widens both for
  the shot; if a storm frame still comes back dark, check `light_lods` in the
  receipt before blaming the weather.
- **No metric here can judge a photograph.** Luminance and contrast find black
  frames and empty frames; they called the best hand-shot image of the first
  session "thin". Ranking is what the gallery votes are for.
- **Dense forest still beats the camera occasionally.** The runner lifts and then
  swings to clear foliage, and records which; `still_blocked` in the receipts
  means it tried everything and shot anyway.

## Licensing

The camera mod is a revival of `valheim-camera-proof` from the public `comfy`
archive, where it is MIT. A copy landed in this repository falls under BSL 1.1
instead. It stays a separate BepInEx plugin — nothing here belongs in
ComfyNetworkSense.
