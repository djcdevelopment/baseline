# The architecture experiment — what can we determine about Era 17's buildings from the save alone?

2026-08-27. Question: can a CAD-style model of player-built structures be reconstructed
from ZDOs + the world save, with no screenshots and no game client — and which derived
architectural facts are trustworthy enough to enter the shot-planning lexicon?

**Answer so far: yes.** Rotation was the one missing datum (the parser skipped 12 bytes
per ZDO); with it read, position + snap-verified piece geometry gives an oriented-box
massing model whose decode is *proven by the buildings themselves* (L1) before any
photograph enters the picture (L2).

## The pipeline

```
prefab-dump.json ──► extract_geometry_lexicon.py ──► arch/piece-geometry.json
ComfyEra17.db (frozen, E:\omen\era17) ──► viewer jar --export-building-geometry
                                      ──► E:\omen\steward-era17-arch\building-geometry.parquet
clusters.json (FROZEN ids) ─┬─► verify_rotation.py ──► arch/rotation-verify.json  (L0+L1)
                            ├─► reconstruct_cluster.py ──► arch/<id>.glb / .graph.json / .arch.json
                            └─► render_compare.py + dump_depth.py ──► arch/experiment/  (L2)
Viewer: python -m http.server in out/era17/arch/, open viewer.html.
```

Decode gate: `reconstruct_cluster.py` and `render_compare.py` REFUSE to run unless
`rotation-verify.json` says PASS. The decode is imported from that file, never hardcoded.

## The validation ladder

### L0 — what the save actually carries (PASS, measured 2026-08-27)

- Export: **4,655,160 architectural ZDOs** (BUILDING 4,359,570 + container/bed/sign/
  portal/item-stand/ballista), **93.9% with the rotation flag**; 36 s parse, 61 MB parquet.
- Raw ranges: every rotation component in **[0, 360)** → the save stores **euler
  degrees** (a Vector3, not a quaternion — the 12-byte size already excluded a full quat).
- Quantization: **59.9%** of building yaws sit on the 22.5° snap-rotate grid (±0.5°);
  the same test read as radians matches only 8.4%. Units settled without geometry.
- Missing-flag-means-identity: flagless pieces aligned at **0.729** under the winning
  decode — the assumption holds.

### L1 — snap alignment: the buildings prove the decode (PASS)

Snap points (pivot-local, from the prefab dump) transformed to world space must
coincide (ε = 5 cm) for snapped neighbours under the correct decode. Key insight from
the first run: axis ORDER only shows on pieces with ≥2 non-zero euler components —
pure-yaw pieces transform identically under every order — so the discriminating metric
is the **multi-axis subset** rate, and the aggregate is the health gate.

Five pilots (714, 1775, 578, 1820, 916; 764–1,045 snap-bearing pieces each):

| hypothesis      | aggregate mean | multi-axis mean |
|-----------------|---------------:|----------------:|
| **deg_unity**   | **0.872**      | **0.805**       |
| deg_xyz         | 0.843          | 0.581           |
| deg_zxy         | 0.818          | 0.255           |
| deg_unity_neg   | 0.562          | 0.375           |
| rad_unity (control) | 0.245      | 0.020           |

**Winner: `deg_unity` — R = Ry(y)·Rx(x)·Rz(z), degrees** (Unity's Z-then-X-then-Y),
margin +0.223 over the runner-up (gate 0.20), aggregate ≥ 0.78 on every pilot.
Non-matching snaps are dominated by terrain-conforming placement (the 5–20 cm
near-miss histogram in each `<id>.graph.json`), not decode error.

### L2 — render vs photograph (PASS on the meaningful stratum; 69 frames, 5 clusters)

Model rendered from the exact shotplan pose (numpy z-buffer, native LH coords, FOV_V
65°) against the captured frame's Depth Anything map.

| stratum | frames | depth ordering | silhouette IoU |
|---|---:|---:|---:|
| all | 69 | 0.774 | 0.448 |
| **subject fills frame (render cov ≥ 0.30)** | **51** | **0.773** | **0.560** |
| distant (cov < 0.30) | 18 | 0.777 | 0.133 |

**IoU 0.560 clears the 0.50 bar** where the subject actually fills the frame. The
distant stratum's 0.133 is a metric artifact, not model error: the IoU denominator is
*all* photo foreground, so terrain and canopy count against a model that legitimately
occupies 13% of the image. Depth ordering is stable at ~0.77 across every stratum —
just under the 0.80 target, and plausibly limited by the model having no terrain
(sampled pixel pairs compare box-only geometry against a photo containing ground).

**The overlays are the real evidence** (`experiment/<id>_overlay.png`, red = rendered
silhouette edge). `20260822-165629_1820_orbit3` traces the roof ridge, both gable
slopes, the wall plane, the rooftop structure and a detached outbuilding — from ZDOs
alone, no photograph consulted. Where scores are poor the overlay shows why:
`20260822-220312_1775_orbit1` is a build shot through a forest canopy, so the model is
right and the *photograph* is leaves.

**Camera-y convention, measured not assumed**: scoring every frame both ways,
**62 of 69 preferred planned-y + `lens_offset_m`** — the capture rig adds the lens
offset. That is a reusable fact about the rig, obtained for free.

Failure decoding:

| symptom | indicts |
|---|---|
| horizontal shift, consistent per orbit | yaw convention |
| vertical shift | pitch sign / lens offset / effective FOV |
| scale mismatch | aspect-derived FOV_H or extents units |
| exploded pieces | decode (re-examine L1) |
| uniformly sunk/floating | pivot y-offset (family defaults) |
| good silhouette, bad ordering | interior geometry only — facade facts still usable |

Interior-lane frames (hall/seat/court/gate/toproom variants) ride along in the frame
set; split them from exterior orbits when reading the means — occlusion makes them
strictly harder.

### L3 — do the derived doors exist where the model says? (first pass done)

`check_openings.py` projects every model-derived door/gate into each photographed
frame it should be visible in, and annotates the image (`<id>_doors.png`; green =
outward normal points back at the camera, orange = facing away).

Over 63 frames / 338 door sightings on 5 clusters:

- **in-frame rate 0.787** — a door the model expects the camera to see lands inside
  the image four times in five. This is a *floor*, not a ceiling: "expected visible"
  only tests in-front-and-within-90 m, so doors hidden behind the building's own far
  wall are counted as misses.
- **facing agreement 0.639** of in-frame doors have their outward normal pointing back
  toward the camera — consistent with orbit shots seeing a mix of near and far facades.

Remaining for a full L3: human/VLM adjudication of storey count, roof shape and
footprint orientation per cluster (**≥ 8/10 = lexicon-grade**), using the annotated
frames plus `viewer.html`. Room hints stay report-only — cluster 578's largest "room"
comes back 5,259 m², which is the grid leaking through an open side, and that is
exactly the kind of claim the ladder is meant to catch before a planner trusts it.

## What the model already determines (pilot reconstructions)

| cluster | pieces | storeys | openings | roof | snap edges (orphans) |
|--------:|-------:|--------:|---------:|------|----------------------|
| 578  | 1,488  | 4 | 27  | hip   | 3,472 (21) |
| 714  | 1,455  | 4 | 145 | gable | 2,198 (41) |
| 916  | 1,422  | 6 | 35  | gable | 3,014 (33) |
| 1775 | 1,106  | 2 | 4   | gable | 3,743 (3)  |
| 1820 | 902    | 4 | 62  | hip   | 2,346 (12) |
| 275  | 5,630  | 5 | 41  | gable | 17,633 (36) |
| 182  | 25,649 | 5 | 1,356 | (no roof-named pieces) | 72,367 (883) |

Per cluster: storey y-levels, footprint polygon + area, roof ridge bearing, every
door/gate/window with a facing normal and an exterior-side vote, room-candidate areas
per storey. All in `<id>.arch.json`, keyed to frozen cluster ids.

## Lessons the run itself taught

1. **`meshBoundsApprox` lies wherever a prefab scales a unit mesh** (dump reads
   sharedMesh bounds without the transform): blackmarble_2x2x2 — a true 2×2×2, snaps
   at all eight ±1 corners — reports ~[1,1,1]; wood_floor/wood_beam/wood_door carry a
   literal placeholder. **Snap extents are the ground truth** on snap-bearing axes;
   bounds fill in only where they agree (75 prefabs corrected). The fourth instance of
   the project's oldest lesson: geometry from outside the world is wrong in it.
2. **Pivots sit at the piece center** for core construction (snap sets symmetric about
   the origin), not at the base — the "raise by half height" default survives only for
   snapless furniture, and stays calibratable.
3. The wood wall's prefab is `woodwall`, not `wood_wall`. Vocabulary by placement
   counts, as always.

## Planner unlocks (follow-up, keyed on lexicon-grade facts only)

| fact | unlock | integration |
|---|---|---|
| footprint + facade normals | facade-aware orbit bearings; skip blank walls | plan_shots.py reads `arch/<id>.arch.json` when present |
| door facing | doorway-framed shots, entrance approaches | plan_shots.py new shot type |
| roof ridge + pitch | roofline silhouettes perpendicular to the ridge, low sun | plan_shots.py / plan_hearthview.py |
| storeys + rooms + box set | interior sightlines with wall-clip ray tests | plan_interiors.py |
| window facings × lights.json | lit-window night exteriors | plan_hearthview.py |

Contract: planners load arch.json lazily by frozen cluster id and degrade to today's
bbox behaviour when absent — zero breaking change.

## Reproduction

```powershell
# 1. lexicon (any python with duckdb)
python extract_geometry_lexicon.py
# 2. rotation export (vendored JDK; ~40 s)
#    in C:\work\ComfyStewardView: mvn package, then
java -Xmx4g -jar viewer\target\world-viewer-1.0.0.jar E:\omen\era17\ComfyEra17.db `
  --export-building-geometry E:\omen\steward-era17-arch\building-geometry.parquet --no-browser
# 3-5. decode, models, L2 (steward-arch venv: numpy scipy trimesh shapely duckdb pillow)
C:\work\venvs\steward-arch\Scripts\python.exe verify_rotation.py
C:\work\venvs\steward-arch\Scripts\python.exe reconstruct_cluster.py
C:\work\venvs\steward-arch\Scripts\python.exe render_compare.py --cluster-ids 1775,916,1820,182,275 --emit-ids-only
C:\work\omen-perception\venv\Scripts\python.exe dump_depth.py --ids-file out\era17\arch\l2-frame-ids.txt
C:\work\venvs\steward-arch\Scripts\python.exe render_compare.py --cluster-ids 1775,916,1820,182,275
C:\work\venvs\steward-arch\Scripts\python.exe check_openings.py --cluster-ids 1775,916,1820,182,275
# look at the models
cd out\era17\arch; python -m http.server 8931   # then open viewer.html
```

The rotation parquet is regenerable scratch (delete `E:\omen\steward-era17-arch` when
done; the export rebuilds it in ~40 s). Never re-run scan_clusters into out/era17 —
cluster ids are frozen. The plan's original scratch target was D:\; this machine has
no D: drive, so E:\omen (2.5 TB free) carries it instead — same not-on-C: intent.

## R&D lap — L3 semantic trust gate (2026-08-27)

**Edge found:** oriented-box massing fidelity does not imply semantic architectural
fidelity. Five photographed clusters were scored from two mechanically selected exterior
bearings each (`2` supported, `1` ambiguous/partial, `0` contradicted or unavailable;
lexicon-grade = at least 8/10):

| derived fact | score | disposition |
|---|---:|---|
| **dominant footprint orientation** | **9/10** | **lexicon-grade** |
| storey count | 5/10 | report-only |
| roof shape + ridge | 5/10 | report-only |
| opening position + facing | 5/10 | report-only |

The failures are useful and concrete. Cluster 916's six floor-pivot levels are terrain and
separate-building elevation bands across a low compound, not six stacked storeys. Cluster
1820 is visibly gabled but classified `hip`. Cluster 1775's camera-facing gate projections
land on roof planes, showing why L3's earlier 0.787 *in-frame* rate is not an accuracy rate:
that check has no building self-occlusion and never asks whether a marker coincides with a
physical opening. The massing overlays remain good; the semantic labels are the surface that
failed contact.

Planner consequence: only footprint/facade-aware orbit bearing is unlocked by this lap.
Doorway-framed shots, roof-class-specific silhouettes, and storey-aware interior planning stay
gated. The per-cluster evidence, selected frame IDs, rubric, and machine-readable uncertainty
list are in `out/era17/arch/experiment/l3-adjudication.json`.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\render_compare.py --cluster-ids 182,275,916,1775,1820
C:\work\venvs\steward-arch\Scripts\python.exe .\check_openings.py --cluster-ids 182,275,916,1775,1820 --max-annotated 100
```

Uncertainty list: this is five clusters and two exterior views per fact, not an Era-wide
sample; weather, vegetation, distance, terrain, and self-occlusion made some observations
unanswerable; no interiors or true plan views were sampled; the footprint pass covers dominant
orientation/massing, not exact area, concavity, or disjoint parts; the roof vocabulary is coarse
and missing for cluster 182; rooms were deliberately excluded. The rerender also confirmed that
`render_compare.py` is a serial NumPy software z-buffer that leaves most CPU/GPU capacity idle;
that performance edge was recorded, not chased in this lap.

## R&D lap — footprint-normal facade orbit (2026-08-27)

**Edge found, but the photographic question remains open:** bearing and runtime terrain
clearance are coupled. The one L3 fact that survived — dominant footprint orientation — was
connected all the way into a real AM4 capture for cluster 1820. Its minimum rotated rectangle
has a `79.13°` major axis, so the slice compared today's nearest bbox corner (`135°`) with the
two long-face normals (`169.1°`, `349.1°`). Three 4K frames were captured as run
`20260827-134534` and pulled back with per-file MD5 agreement.

The connection is real: both derived bearings reached the long sides. The `169.1°` side became
a roof-and-boulder close-up; the `349.1°` side showed more building width and the lower entrance.
The existing instruments scored them as follows:

| frame | aesthetic | depth | layers |
|---|---:|---:|---:|
| bbox control | **5.635** | **0.550** | 5 |
| broad facade | 5.336 | 0.462 | 3 |
| opposite facade | 5.612 | 0.406 | 5 |

Those numbers are **not a clean A/B**. The capture receipt says the bbox control was
`lifted+8m` from planned y=74.5 to y=82.5 and repitched from 18° to 30.772°; both derived
views remained at y=74.5 / 18°. The runtime changed two variables only for the control.
No planner integration is earned from this sample. The full record is
`out/era17/facade-probe/result.json`.

### Can't answer why

| UTC phase | Player-visible symptom | Evidence preserved | Why still unknown | Bounded next investigation |
|---|---|---|---|---|
| 2026-08-27 13:45 capture | Bbox scores best; near facade worst; opposite facade reveals more architecture but has lower depth | 3 hash-verified 4K frames, plan, terrain preflight, receipts with planned/placed/lens poses, aesthetic + depth JSON | Runtime lifted and repitched only the control, so bearing is not isolated | Repeat at one common actual lens height with recomputed pitch, or use a flat-terrain cluster where all placements remain planned |

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\probe_facade_orbit.py
ssh homebase 'rm -f /home/derek/valheim-capture/plans/facade-1820-rd1.tsv'
scp .\out\era17\facade-probe\facade-1820.tsv homebase:/home/derek/valheim-capture/plans/facade-1820-rd1.tsv
ssh homebase "/home/derek/valheim-capture/run-capture.sh --plan '/home/derek/valheim-capture/plans/facade-1820-rd1.tsv' --world 'ComfyEra17' --character 'tugcorp' --timeout 60 --width 3840 --height 2160"
```

Uncertainty list (from the probe plus the live receipt): one cluster only; the minimum
rotated rectangle can be biased by attached wings; terrain includes the frozen edits layer but
the 12 m worldgen grid remains approximate; building self-occlusion is not pre-cleared; the
runtime lift made the comparison non-normalized; aesthetic/depth do not directly measure
architectural legibility; AM4's current ComfyQuestRuntime left a small common UI element at the
right edge. No second capture was attempted in this lap.

## R&D lap — durable per-ZDO coordinates in the planner (2026-08-27)

**Edge crossed:** the parser/cache had always retained `x/y/z`, but `scan_clusters.py`
discarded exact per-piece membership when its temporary DuckDB tables closed. The planners then
had only an axis-aligned cluster box. `export_cluster_points.py` now replays the scan, reconciles
every component to the **frozen** cluster id by its full recorded geometry, and persists
`snapshot_id, world_id, cluster_id, zdo_index, prefab, x, y, z, creator_id` to Parquet.

Era17 result: **3,513,410 BUILDING ZDOs / 2,204 clusters**, 37,258,753 bytes, SHA-256
`3055AEFD0B192ECDD75D734DD2AE92DB0C3EC6238CC728CA2EE29D1EC9580910`. Full joins found
zero x/y/z mismatches, zero identity mismatches, zero missing source rows, and zero per-cluster
piece-count mismatches. The replay also exposed why the reconciliation is mandatory: **92**
enumeration ids moved on the first export and **186** on an immediate repeat even though all
2,204 geometries matched; the reconciled Parquet hash stayed identical.

`plan_shots.py --cluster-points ...` consumes the rows. For every bearing it projects all ZDOs
onto the camera's right/up/depth basis and solves the FOV distance inequality per point. Thus
height and front-to-back depth are inputs, not labels carried beside the old bbox calculation.
Cluster 1820's four prior 31.0 m bbox distances became **35.7, 35.8, 46.9, 34.5 m**; the
artifact reports 25.0 m world height and 35.2–44.0 m camera-axis depth by bearing. The generated
TSV re-parsed 5/5 rows through the mod's positional contract.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
python .\export_cluster_points.py --db E:\omen\steward-era17\out\world-cache.duckdb `
  --clusters .\out\era17\clusters.json `
  --out E:\omen\steward-era17-arch\cluster-zdos.parquet --replace
python .\plan_shots.py --clusters .\out\era17\clusters.json --cluster-ids 1820 `
  --cluster-points E:\omen\steward-era17-arch\cluster-zdos.parquet `
  --alt-shots 0 --out E:\omen\codex-zdo-coords-lap\shotplan-zdo.json
```

Uncertainty list: ZDO positions are prefab pivots, not mesh corners, so the solver has exact
placement depth but can under-frame the outer half-extents of sparse pieces; the four orbit
bearings are still bbox-derived; terrain clearance can still lift and repitch a runtime camera;
only the existing TSV parser contract, not a new in-game capture, was exercised in this lap.

## R&D lap — is the cluster the wrong unit of architectural analysis? (2026-08-27)

**Edge found: segmentation separates two classes of semantic failure that L3 could not
distinguish.** L3 scored storey count, roof shape and opening facing at 5/10 and could
only say they failed. The hypothesis here was that the frozen 16 m occupancy cluster is
not one building, so every semantic label is averaged over a compound. Splitting each
cluster into physically connected structures — contact = snap-point coincidence within
5 cm OR oriented-box overlap (separating-axis test, 5 cm inflation) — confirms that for
one failure and refutes it for another:

- **Cluster 916's storey count is a unit-of-analysis error.** Segmentation fixes it.
- **Cluster 1820's roof class is not.** It survives segmentation intact, so it is a
  genuine defect in the yaw-histogram roof classifier.

Knowing which of the two a failure is tells you whether to fix the unit or the classifier.
That is the whole value of the lap.

Membership came from the verified `cluster-zdos.parquet` (exact frozen BUILDING
membership) joined to `building-geometry.parquet` (rotation) on `zdo_index`. The join was
verified before use: 3,219 rows across the three clusters, every x/y/z and prefab name
matching, 2,933 carrying rotation.

| cluster | pieces | components | ≥20 pieces | whole-cluster label | after segmentation |
|---:|---:|---:|---:|---|---|
| 916 | 1,160 | 15 | 2 | 6 storeys, gable | **#0** 721 pcs, 15.2 m, 4 storeys, gable (182 roof pcs); **#1** 419 pcs, 20.3 m, 3 storeys, **no roof** |
| 1820 | 861 | 14 | 1 | 4 storeys, hip | **#0** 847 pcs — identical answer, no split |
| 1775 | 1,069 | 21 | 3 | 2 storeys, gable | **#0** 903 pcs, 11.5 m, 2 storeys, gable; **#1** 78 pcs outbuilding, 1 storey; **#2** 25 pcs, flat |

Tails: 20 pieces (1.7%) for 916, 14 (1.6%) for 1820, 63 (5.9%) for 1775.

The 916 split is physically real, not a missed connector: centroid separation **21.6 m**,
closest pivot-to-pivot gap **5.49 m**, and component #1's bounding box *surrounds* #0's
(xz overlap 34.5 × 30.5 m). #0 has two creators (618 / 103 pieces); #1 has exactly one
(419). #1 spans 64 m horizontally over 20 m of elevation with no roof pieces at all —
statistically it reads as terracing or perimeter works wrapped around the roofed building,
which is exactly the "elevation bands across a low compound" L3 recorded by eye.

Incidental: exact frozen membership is **tighter** than the padded-bbox + nearest-centre
guess `reconstruct_cluster.py` still uses — 916 is 1,191 rows exact vs 1,453 guessed. The
reconstruction lane should migrate to the frozen artifact.

**No planner promotion is earned.** Storey count and roof class stay report-only.
Segmentation is a diagnostic result, not a validated re-labelling: the per-structure
storey counts were not themselves adjudicated against photographs.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\segment_buildings.py --cluster-ids 916,1820,1775
```

Uncertainty list: three clusters only, all previously photographed and non-representative.
The per-structure storey and roof labels were not adjudicated against photographs in this
lap — only the whole-versus-split comparison was made. The contact test uses approximate
snap-derived prefab extents and a 5 cm inflation, so both over-merging and under-merging
are possible and untested. Component #1 of 916 was interpreted as terracing from its
statistics, not confirmed visually. Only BUILDING rows participate, so doors, containers
and portals present in `building-geometry.parquet` were excluded from connectivity. The
tail components (1.6–5.9% of pieces) were not examined. Segmentation was not run across
all 2,204 clusters, so its cost and failure modes at scale are unknown.

## R&D lap — roof geometry is intrinsic to the prefab, not to the ZDO transform (2026-08-27)

**Edge found: the old roof classifier was structurally blind, and the corrected geometry
is exactly recoverable — but fixing it moves the failure up a level rather than closing
it.** The prior lap showed 1820's roof error survives structural segmentation, so it is a
classifier defect. This lap says what the defect is.

1. **For most roof pieces the rotation transform carries no pitch at all.** Tilt of each
   roof piece's transformed local up-vector away from vertical: cluster 1820 has **116 of
   151** roof pieces at zero tilt, 1775 has **159 of 159**, 916 has **149 of 182**. The
   slope is baked into the prefab *mesh*; the ZDO rotation only says which way the piece is
   turned. Any classifier reading pitch from the transform cannot see roof shape — and the
   old one read yaw, reduced modulo 180°, which additionally collapses a gable's two
   opposing slopes into one bin.
2. **The intrinsic slope is exactly recoverable from the prefab's own snap geometry**,
   already vendored in `prefab-dump.json`. Centroid of highest snaps minus centroid of
   lowest snaps gives the local downhill vector and the pitch. Verified: `wood_roof_45` →
   downhill local +z at **45.000°**; `darkwood_roof_45` the same; `wood_roof` → **26.565°**;
   `wood_roof_top_45` → correctly no slope (ridge cap). **30 of 37** roof prefabs placed in
   Era17 have a derivable slope.
3. **Concrete defect exposed by (2): the 26° roof prefab is named `wood_roof`** — no "26"
   in the name — so the substring pitch classifier files all **41,790** Era17 placements of
   it as `other`.
4. **Refutation: fixing per-piece geometry does not by itself produce a correct
   building-level label.** Rotating each derived downhill vector into world space and
   histogramming bearings, 1820 yields dominant opposing bearings **157.5° (42 pieces)** and
   **337.5° (39 pieces)** — exactly 180° apart, the gable pair — but also secondary
   concentrations at 0.0° (18), 67.5° (19) and 90.0° (16), so the aggregate classifies
   `complex`, not `gable`. Clusters 1775 and 916 both classify `hip` under the new method.
5. **A photograph explains the spread and undermines the recorded ground truth.** Frame
   `20260822-165629_1820_orbit3` shows 1820 as a large stone building carrying a main roof
   mass, **plus a separate wooden rooftop pavilion with its own roof at a different
   orientation**, plus a detached outbuilding in frame. The L3 note "visibly gabled but
   classified hip" was describing only the main mass. The rendered massing silhouette traces
   the building cleanly in that same overlay, so the L2 massing result is unaffected.
6. **The failure moved up one level, it did not disappear.** Just as "one building per
   cluster" was too coarse, **"one roof shape per building" is too coarse** for player
   builds with wings, dormers and rooftop structures. Roof-section segmentation is the
   suspected next unit and was **not** attempted in this lap.

**No promotion.** Roof shape stays report-only; no planner change is earned. The corrected
slope derivation was run as a probe and has **not** been written into
`reconstruct_cluster.py`.

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
# probe run inline against segment_buildings.load_pieces + piece-geometry.json snap points
```

### Can't answer why

| UTC phase | Player-visible symptom | Evidence preserved | Why still unknown | Bounded next investigation |
|---|---|---|---|---|
| 2026-08-27 roof adjudication | New classifier says `complex` for 1820, the L3 record says "visibly gabled", the old classifier said `hip` | Per-piece downhill-bearing histogram, tilt distributions, frame `20260822-165629_1820_orbit3` and its silhouette overlay | The recorded truth and the classifier describe different scopes (main mass vs whole cluster), and a single oblique frame cannot separate a hipped end from a gable end | Segment roof sections and adjudicate the MAIN mass only, against a frame taken along the derived ridge bearing |

Uncertainty list: three clusters only. Pitch recovery was verified on four named prefabs,
not all 30. The 7 roof prefabs without derivable slope were not examined. The
high-snap/low-snap centroid method assumes a single planar slope per piece and was not
tested on curved or compound roof prefabs. No roof-section segmentation was attempted.
Building-level labels for 1775 and 916 have no photographic adjudication at all. The probe
was not run beyond these clusters, so scale behaviour is unknown.

## R&D lap — the roof plane is the right unit; the blocker was vocabulary, not data (2026-08-27)

**Edge found: grouping roof pieces into coplanar adjacent sections resolves a standing
human-vs-machine contradiction, and shows the ZDO data carried the exact geometry all
along — the limit was the label set.**

`roof_sections.py` groups sloped roof pieces into coplanar, co-oriented, spatially
adjacent sections (surface normals within 15°, plane offsets within 0.75 m, centres
within 4 m), then classifies the largest structural component by its distinct plane
orientations. The section geometry comes out crisp:

| cluster | main structure | sloped roof pieces | dominant planes |
|---:|---:|---:|---|
| 1820 | 847 pcs | 149 (19 sections) | **78.8°** (29 pcs), **348.8°** (28), **168.7°** (23) — all pitch 45.0, y ≈ 69.7–70.0 |
| 1775 | 903 pcs | 136 | **0° / 90° / 180° / 270°** exactly — all pitch 45.0, 30 / 24 / 19 / 15 pcs |
| 916 | 721 pcs | 182 | **180° and 360°** (opposing) plus **270°** |

For 1820, 168.7° and 348.8° are 180° apart — a gable pair — and 78.8° is perpendicular to
them, an end slope. A further 9 sections (39 pieces) sit above the main mass, several at
pitch 26.6° rather than 45.0°: rooftop structures.

**Two self-inflicted bugs, found and fixed in this lap:**

1. Section share was measured against the **total** of all sections. On a fragmented roof
   a long tail inflates the denominator until only the single largest plane clears the
   bar — which reported cluster 916's four-orientation roof as a **`shed`**. Fixed by
   measuring share against the largest section (30% threshold).
2. The classifier counted **sections** rather than distinct plane **orientations**, so two
   disconnected patches of one plane counted twice. Fixed by merging strong sections whose
   bearings agree within 25°.

With those fixed, **adding one vocabulary term — `half-hip` (a gable pair plus one hipped
end) — resolved the contradiction.** Cluster 1820 classifies half-hip: 168.7°/348.8° are
the gable pair the human adjudicator saw, and 78.8° is the hipped end that made the old
classifier say `hip`. Both prior labels were partially right; neither vocabulary could
express the actual roof. 916 is also half-hip; 1775 is a clean four-plane hip.

Photographic adjudication, precisely:

- **1820 — supported.** Frame `20260822-165629_1820_orbit3` shows a large gable face toward
  the camera and a slope descending across the right-hand end.
- **1775 — plausible, NOT confirmed.** Frame `20260822-220312_1775_orbit3` shows a thatched
  longhouse whose near planes match the model, but the far end is not visible in that view,
  so a four-plane hip cannot be distinguished from a gable with one hipped end.
- **916 — not adjudicated.**

**Consequence worth acting on: for shot planning the categorical label may be unnecessary.**
What a planner needs is plane bearings and pitches, and those are exact. Cluster 1820's
ridge runs perpendicular to its gable pair at ≈ **78.8°**, which is also its hipped-end
bearing. A roofline silhouette shot wants that number, not the word "half-hip".

**No promotion.** Roof class stays report-only; `roof_sections.py` is a probe and is not
wired into `reconstruct_cluster.py`. The main-mass height-band separation used an arbitrary
4 m window and changed no label, so it earned nothing.

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\roof_sections.py --cluster-ids 1820,1775,916
```

Uncertainty list: three clusters, one photographically supported, one unconfirmed, one
unadjudicated. The thresholds (15°, 0.75 m, 4 m, 30%, 25°) were chosen by hand and never
swept. The `half-hip` term was added **after** seeing these same clusters, so it has not
been tested on held-out buildings. Mixed pitches within one roof (45.0° and 26.6° both
present in 1820) were observed but not interpreted — possibly a gambrel profile, possibly
just the rooftop structures. Only the largest structural component per cluster was
examined. No run across all 2,204 clusters, so vocabulary coverage across the world is
unknown.

## R&D lap — the existing frame corpus cannot adjudicate roof topology (2026-08-27)

**Clean sample, mostly negative: the discriminating view for roof class is structurally
absent from 2,633 existing frames, and the one cluster it could be tested on passed.**

Design first, so this is a test and not a story. Roof class is only decidable from an
**end-on elevation** — camera along the ridge axis, low pitch. A plain gable shows a
vertical wall triangle at the end; a hipped end shows a sloping roof plane; a half-hip
shows one of each. An oblique orbit shows two planes and hides the ends, which is why
every previous roof adjudication was ambiguous. Predictions for seven never-inspected
clusters were written to `out/era17/arch/heldout-predictions.json` **before** any frame
was opened — necessary because `half-hip` was fitted post-hoc last lap.

A frame with camera yaw *Y* views the facade whose outward normal points toward *Y+180*.
Applying that, the corpus fails three ways:

1. **Orbit yaws are fixed at 45/135/225/315.** A four-corner orbit is end-on only when a
   building's ridge happens to align with a diagonal. Clusters 1820, 1775 and 916 have
   *only* those four yaws — no end-on frame exists for any of them.
2. **The off-diagonal yaws are interior-lane frames** (hall, seat, court, toproom), where
   the camera is inside the building. `source` is `orbit` for 2,631 of 2,633 rows and does
   not separate the lanes; filtering on camera-outside-the-footprint does. That cut the
   apparent free coverage from 8 end-views to **3**.
3. **Terrain and vegetation destroy what remains.** All three exterior end-views of cluster
   372 are unusable: `orbit1` and `dawn` have the camera jammed against a rock with the
   build a distant speck, `orbit3` is screened by birches with the camera clipping terrain.

Adjudicated: **1 of 7**.

| cluster | predicted | frame | verdict |
|---:|---|---|---|
| 705 | **gable** (planes 326.3° / 146.2°) | `20260822-145411_0705_orbit4` | **SUPPORTED** — rooftop shelter shows a clear ridge with two slopes (one thatched, one open rafters) terminating in a triangular end with no roof plane |
| 372 | hip (0/90/180/270 → ends 45/225) | 3 exterior frames | **unadjudicable** — all occluded |
| 310, 729, 42, 195 | gable / hip / gable / shed | — | **no exterior end-view exists** |

One supported prediction is weak evidence, but it is honest evidence, and it is the first
roof label in this project confirmed against the view that can actually falsify it.

**Consequence for the capture ask:** all six frames for 1820 / 1775 / 916 are genuinely
required — none can be substituted from disk. The plan must also carry a **terrain
clearance pre-check at the planned pose**, because occlusion is what killed cluster 372,
and because the earlier facade probe showed the runtime silently lifts and repitches a
blocked camera, which would break the very comparison the shot exists to make.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\roof_sections.py --cluster-ids 372,705,310,729,42,195
# coverage check + adjudication were run inline against index.json + load_shotplans
```

Uncertainty list: one adjudicated cluster, one end, one judge (me), no second opinion and
no VLM cross-check. The 705 frame is at pitch 22.2° rather than the 5–15° an elevation
shot wants, so the end is foreshortened; its far end is not visible, so a half-hip with the
hipped end away from camera is not excluded. The roof judged is a rooftop shelter on a
stone keep, not the keep itself, so it is a small part of the structure. Occlusion was
assessed by eye, not measured. The pre-registered predictions for 310, 729, 42 and 195
remain untested and stay on file for the next capture window.

## R&D lap — the end-on capture: half-hip CONFIRMED, occlusion is the real bottleneck (2026-08-27)

**Edge crossed: the differential prediction held.** Cluster 1820 was predicted `half-hip`
— a roof PLANE at the 78.8° end and a wall TRIANGLE at the 258.8° end — and both frames
show exactly that. The prediction was written to `roof-end-predictions.json` before the
capture existed, and it is a prediction no symmetric error can fake: the two ends must
differ, in a named direction.

Capture: AM4 run **20260827-165844**, plan `roof-ends-rd1.tsv`, 16/16 shots, ComfyEra17 /
tugcorp, 3840×2160, elevation 10° with `aim_height 0.85` (an architectural elevation, not
a drone view). Frames pulled to `out/era17/arch/roofends/`.

| cluster | predicted | end 1 | end 2 | verdict |
|---:|---|---|---|---|
| **1820** | half-hip | thatched **sloping hip plane** rising to the ridge | **vertical stone wall**, gable profile, window rows | **CONFIRMED, both ends** |
| **42** (held-out) | gable | apex with two descending roof edges over a **vertical triangular wall** | camera in a boulder gap, building out of frame | **SUPPORTED, one end** |
| 1775 | hip | no gable triangle visible — consistent, but oblique and part-blocked | fully blocked by trees | weak, inconclusive |
| 916 | half-hip | roof too distant to score (see below) | camera against a tree trunk | not adjudicated |
| 310 (held-out) | gable | **camera inside a tree** | oblique, roof cropped in corner | not adjudicated |
| 372 (held-out) | hip | **camera inside a boulder** — the same failure as its archive frames | not examined | not adjudicated |
| 729 (held-out) | hip | a **tower**, heavily backlit | not examined | vocabulary mismatch |
| 195 (held-out) | shed | not examined | a **tower** with no ridged roof | label vacuous |

**1820 resolves the standing contradiction.** The human adjudicator wrote "visibly gabled"
and the old classifier said "hip"; the building has a thatched hipped end at 78.8° and a
stone gable end at 258.8°. Both observers were looking at the same building from different
sides and each was half right.

**Incidental confirmation of an earlier lap.** Cluster 916's frame shows a walled, terraced
compound wrapping around a smaller roofed building — the 419-piece, 64 m, roofless
component #1 that the segmentation lap interpreted as "terracing or perimeter works" from
statistics alone and explicitly flagged as visually unconfirmed. It is now confirmed.

**The real bottleneck is occlusion, not geometry.** Roughly 6 of 13 examined frames were
lost to vegetation or boulders. The terrain preflight cleared every one of them: cluster
372 reported **44.5 m** line-of-sight clearance and put the camera inside a rock; 310
reported 24.5 m and put it inside a tree. The preflight models ground on the 12 m worldgen
grid plus the frozen edits layer, and models **neither vegetation nor boulders**, which are
exactly what stands between a low camera and a building. A low elevation makes this worse,
and a low elevation is precisely what the shot requires.

**Two vocabulary limits surfaced.** Towers (729, 195) receive labels that are topologically
defensible — four 45° planes really is a pyramidal cap, one plane really is all 195 has —
but semantically empty, because gable/hip presumes a ridged longhouse. And framing on the
cluster bounding box is wrong for roof adjudication: on compound clusters like 916 it
centres the whole compound and leaves the building that owns the roof far away.

**Promotion earned: none, but the class of evidence changed.** `half-hip` on 1820 is now
supported by the view that could have falsified it, and a held-out `gable` (42) survived
one end. That is 1 strong plus 1 held-out partial out of 8 clusters — not the ≥8/10 the
lexicon-grade rubric wants. Roof class stays report-only.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\plan_roof_ends.py
scp .\out\era17\arch\roof-ends.tsv homebase:/home/derek/valheim-capture/plans/roof-ends-rd1.tsv
ssh homebase "/home/derek/valheim-capture/run-capture.sh --plan '/home/derek/valheim-capture/plans/roof-ends-rd1.tsv' --world 'ComfyEra17' --character 'tugcorp' --timeout 60 --width 3840 --height 2160"
```

### Can't answer why

| UTC phase | Player-visible symptom | Evidence preserved | Why still unknown | Bounded next investigation |
|---|---|---|---|---|
| 2026-08-27 17:00 capture | Cameras land inside trees and boulders on bearings the preflight scored as 24–44 m clear | 16 frames, `roof-end-predictions.json` with per-shot terrain preflight, run receipt 20260827-165844 | The clearance model covers ground only; vegetation and boulder ZDOs are never consulted, and both are in `building-geometry.parquet` and the cache already | Add a vegetation/boulder occlusion probe from ZDO positions along the sight ray, then re-shoot 310, 372, 1775 and 916 |

Uncertainty list: 3 of 16 frames (372 end 2, 729 end 2, 195 end 1) were never examined.
One judge, no second opinion, no VLM cross-check. 1820 is in-sample — the term was fitted
on it — so its confirmation is weaker evidence than a held-out pass, and the only held-out
adjudication that survived is a single end of cluster 42. The unexamined and blocked frames
mean five pre-registered predictions (310, 372, 729, 195, and 916's roof) remain open. The
capture used one time of day and one weather; backlighting alone cost 729. Frames were
judged by eye at 1200 px, not at native 4K.

## R&D lap — the sight-line probe, and the world it was aimed at (2026-08-27)

**Edge found, and it is not the one this lap set out to find: the world AM4 photographs
is not the world the analytics cache describes.**

`sight.py` is built — one shared line-of-sight primitive replacing three partial probes
(`scan_channels`' horizontal tree corridor, `scan_rooftops`' build-local skyline fan, and
the terrain-clearance loop duplicated verbatim in `probe_facade_orbit` and
`plan_roof_ends`). It models vegetation and rock as bodies on their pivots, tests whether
the camera stands inside one, and tests whether one intersects the ray over its first 80%.

`validate_sight.py` retrodicts run 20260827-165844 — the 16 frames already on disk, five
labelled blocked and three labelled clear.

**Result: caught 2/5 blocked, passed 3/3 clear, 0 false alarms. GATE FAIL.**

The two catches are real and both came from the camera-inside test: `0372_roofend1` —
*camera is inside cliff_mistlands2*, and `0916_roofend2` — *camera is inside Beech1*.
Both match what those frames plainly show, and neither the terrain preflight (which
reported 24–44 m clear) nor the in-game probe (`occluded: false` on **all 16**) caught
either.

### Why the other three miss

Not a tuning problem. Diagnosing `0310_roofend1` and `1775_roofend2` piece by piece:
**every occluder within 25 m is 12–26 m BELOW the sight line.** Lens at y=68.2, nearest
tree tops at 42–56. Geometrically that ray is wide open — yet the frame is full of
foliage.

That contradiction has one cheap explanation, and it checks out:

| world | bytes | modified |
|---|---:|---|
| AM4 capture world `~/.config/unity3d/.../worlds_local/ComfyEra17.db` | 1,299,444,160 | **2026-08-27 17:02** |
| Cache source for snapshot 107, `E:\omen\era17\ComfyEra17.db` | 1,308,887,950 | **2026-08-22 07:54** |

**Different files, 9.4 MB apart, five days apart** — and the capture client rewrites its
own world every time it runs. Every offline camera position in this project is computed
against a snapshot the capture host has since diverged from. Buildings are stable enough
that the 1820 massing overlays still landed; vegetation, which is planted, cleared and
regrown, is exactly the thing that would drift.

This reframes the lap-8 conclusion. The occlusion probe was worth building and its
geometry is sound where the data is sound. But the frames it cannot explain are evidence
about the **pipeline**, not about the probe.

### The tuning history is itself the evidence

Three passes, each principled, none of which moved the misses:

| change | effect |
|---|---|
| `max(vocabulary, meshBounds)` for height | caught 4/5 — but gave Oak1 a 17.9 m radius and **falsely refused `1820_roofend2`**, a frame that plainly shows the building |
| canopy radius derived from height instead of bounds | false alarm gone, back to 2/5 |
| conifer 0.22 vs broadleaf 0.50 radius ratios | no change at all |

A model that swings between 2/5 and 4/5 on parameter choice, while the false alarm it
creates is a frame with a *verified* result, is not converging on the world. It is
fitting noise in a world it cannot see. **Tuning stopped here deliberately**, at n=8.

### Kept regardless — three facts that outlived the lap

1. **`meshBoundsApprox` is unreliable for vegetation in both directions.** FirTree reads
   5.45 m (real: 18 m, the unit-mesh bug that made blackmarble_2x2x2 report 1×1×1), while
   Oak1 and Beech1 read 25–30 m tall and ~36 m **wide** — a sway/LOD volume, not a tree.
   No single rule repairs both; `TALL_TREES` decides height, radius is derived.
2. **Vegetation hides under category BUILDING** — 13,641 trees in Era17, because players
   plant them. A `category IN ('UNKNOWN','NATURE')` filter silently misses them, including
   a Pinetree_01 2.7 m from one camera. Match vegetation by name across every category.
3. **The in-game occlusion probe is blind in practice, not just in theory.** `Plugin.cs`
   documents that it excludes the `piece` layer; measured, it returned `occluded: false`
   for all 16 frames including two where the camera stood inside a cliff and a beech.

### Can't answer why

| UTC phase | Player-visible symptom | Evidence preserved | Why still unknown | Bounded next investigation |
|---|---|---|---|---|
| 2026-08-27 17:00 capture | Frames full of foliage on sight lines the cache says are clear by 12–26 m of vertical margin | 16 frames, receipts with placed poses, `sight-validation.json`, per-occluder along/cross/top dump, the two world files' sizes and mtimes | The capture world and the analysis snapshot are different files five days apart, so it cannot be told whether the probe is wrong or the data is stale | Parse AM4's live `ComfyEra17.db` into a scratch cache on E:, re-run `validate_sight.py` against it, and compare. If the misses become catches, the probe is sound and the pipeline has a world-drift problem worth fixing at the source. |

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\sight.py --audit
C:\work\venvs\steward-arch\Scripts\python.exe .\validate_sight.py --corridor 0.75
```

**No promotion.** `plan_roof_ends.py` was NOT switched to the new gate: gating captures on
a probe that scores 2/5 against stale geometry would refuse good shots for invented
reasons. `sight.py` and `validate_sight.py` stand as the instrument; the world-drift
question decides whether it is trustworthy.

Uncertainty list: eight labelled frames, one judge, labels assigned by eye in lap 8 and
not re-checked here. `0042_roofend2` is counted as blocked but is a 137 m shot whose
failure may be framing distance rather than occlusion — it would be the first label to
re-examine. Canopy geometry (0.35 base fraction, 0.22/0.50 radius ratios, 0.6 m trunk) is
invented from physical reasoning, not measured against anything. The probe has never been
run against a world file that matches the frames. Rock heights come from bounds and were
never audited the way `TALL_TREES` was. Building self-occlusion is still not modelled at
all.

## R&D lap — world drift is real and is NOT the cause (2026-08-27)

**Lap 9's headline is refuted by its own bounded next investigation.** The capture world
and the analysis snapshot really are different files, and it makes no difference to any
frame in the labelled set.

AM4's live `ComfyEra17.db` was parsed in place — `--export-all-categories`, a new flag on
the viewer jar, run inside the `steward-world` image so 152 MB of parquet crossed the
network instead of 1.3 GB of world. 8,920,810 ZDOs.

The two worlds differ substantially:

| category | snapshot 107 (Aug 22) | AM4 live (Aug 27) | delta |
|---|---:|---:|---:|
| UNKNOWN (vegetation, rock) | 3,495,842 | 3,792,286 | **+296,444** |
| DROPPED_ITEM | 311,740 | 1,858 | **−309,882** |
| BUILDING | 4,359,570 | 4,355,874 | −3,696 |

Vegetation regrew, loot despawned. And on the eight labelled sight lines it changes
**nothing**: both sources return identical verdicts on all eight frames, down to the same
36 occluders in 1775's corridor. Drift is real, worth knowing, and was the wrong suspect.

### What the misses actually were

Height and radius needed **opposite** sources, and conflating them is what made the probe
oscillate between 2/5 and 4/5:

| quantity | source | why |
|---|---|---|
| height | `max(vocabulary, meshBounds)` | Beech1 tops out at 56 m under the 14 m vocabulary and 72 m under its 30.5 m bounds; a lens at 68.2 m is *outside* the first and *inside* the second |
| radius | derived from height (conifer 0.22 / broadleaf 0.50, cap 9 m) | bounds widths are sway/LOD volumes — Oak1 reads 36 m across, and using it refused a frame that plainly shows the building |

With that split: **3/5 blocked caught, 3/3 clear passed, 0 false alarms**, identical from
both worlds. 0310 and 1775 are now caught for the right reason.

### The label I nearly talked myself out of

The model said every occluder near 0310 was 12–26 m below the sight line, which made the
"blocked" label look wrong. A native-resolution crop settled it: the lens is **embedded in
leaves**, branches within centimetres. The label was right and the model was wrong, and
the mechanism was precisely the understated tree height above. Checking the frame instead
of trusting the model is what turned this lap around.

### Remaining two misses, honestly

- **0916_roofend2** is marginal, not wrong: its beech sits 9–10.7 m away against a derived
  9 m canopy radius. Real beech canopies are about that size, so this frame lands on the
  boundary of a parameter that no measurement in this project pins down.
- **0042_roofend2** is a 137 m shot whose subject bbox projects fully on-screen at
  220–244 m. That is a framing/distance failure wearing occlusion's clothes, and it is the
  label to re-examine first, not the probe.

**No promotion.** The gate is 5/5 and this is 3/5, so `plan_roof_ends.py` keeps its old
preflight. What has changed is that the instrument now fails for two identified reasons
rather than for unknown ones.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\validate_sight.py --corridor 0.75
C:\work\venvs\steward-arch\Scripts\python.exe .\validate_sight.py --corridor 0.75 `
  --occluders E:\omen\steward-era17-arch\live-geometry.parquet
```

Rebuilding the live export (needs the jar and a `steward-world` image on AM4):

```powershell
scp .\viewer\target\world-viewer-1.0.0.jar homebase:/tmp/world-viewer.jar
ssh homebase "docker run --rm --entrypoint java -v /home/derek/.config/unity3d/IronGate/Valheim/worlds_local:/world:ro -v /tmp:/out steward-world:0445fe2-20260824194013-dirty -Xmx4g -jar /out/world-viewer.jar /world/ComfyEra17.db --export-building-geometry /out/live-geometry.parquet --export-all-categories --no-browser"
```

Uncertainty list: still eight frames and one judge. The canopy constants (0.35 base
fraction, 0.22/0.50 radius ratios, 9 m cap, 0.6 m trunk) are physical reasoning, not
measurement, and 0916 shows the result is sensitive to them at the margin. Rock heights
come from bounds and have never been audited the way `TALL_TREES` was. Building
self-occlusion is still not modelled. The live export is a second snapshot, not a live
feed — AM4 rewrites that world on every capture, so it was already stale when it was read.
Whether drift matters on *other* sight lines is untested; all that is shown is that it does
not matter on these eight.
