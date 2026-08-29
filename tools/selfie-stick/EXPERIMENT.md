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

## R&D lap — exact pivots are not the physical framing envelope (2026-08-27)

**Edge found:** exact per-ZDO `x/y/z` fixed height and camera-axis depth, but a pivot is
still only one point inside a prefab. Expanding the same frozen members through the
snap-verified/mesh-derived prefab extents and the already-PASSed `deg_unity` rotations
materially changes the frame.

`probe_oriented_framing.py` replayed the completed exact-XYZ coverage series: **240
frames / 48 frozen clusters / 31,087 BUILDING ZDOs**. Every point joined the independent
rotation export by `zdo_index`; prefab and x/y/z mismatches were zero, duplicate ids were
zero, and replacing every box with a zero-sized point reproduced `plan_shots.py` within
0.0000005 m. Player-planted vegetation was excluded from the architectural envelope by
the existing `sight.looks_like_vegetation()` vocabulary. `family_median` geometry was
reported but excluded from the decisive lane.

The material gate passed both ways:

| observation | result |
|---|---:|
| actual captured poses with a trusted oriented corner outside the frustum | **138 / 240 frames, 35 / 48 clusters** |
| point-to-box distance increase at least 2 m **and** 5% | **101 frames, 29 clusters** |
| largest required-distance increase | **23.690 m / 50.240%** |
| limiting geometry among the 138 clipped projections | 95 snap+mesh, 26 snap, 17 mesh |

This is not just the algebraic fact that a box is larger than its centre. In the
cluster 1906 orbit-3 overlay, the oriented hull follows the photographed platform and
crosses the bottom edge: pivot framing asks for 49.221 m and the box envelope asks for
54.427 m. Cluster 2343 is the vertical stress case: its black-marble tower is visibly
cut at the bottom, while the 8×2×8 snap-plus-mesh floor envelope moves the request from
23.709 m to 35.376 m. Cluster 713 is the clean control at 102.133 m versus 102.421 m.

The ignored output is `out/era17/framing-envelope-probe/result.json`, with three 4K
projection overlays. A six-row paired handoff is ready at
`out/era17/framing-envelope-probe/framing-envelope-rd1.tsv`: point and box variants for
2343 (vertical), 1906 (depth), and 713 (control). Its positional TSV contract re-parsed
6/6 rows, and every decimetre-rounded box pose retains the intended 1/1.15 frame margin.
It is for the other AM4 photo/gallery agent; this lap did not fire it or rebuild the
gallery.

**No promotion.** `plan_shots.py` still uses `zdo_xyz`. Oriented boxes have earned the
paired photographic probe, not production authority.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\probe_oriented_framing.py `
  --plan .\out\era17\coverage-xyz-4k-smoke.json `
  --plan .\out\era17\coverage-xyz-4k-remainder.json `
  --run-id 20260827-161109 --run-id 20260827-162027 `
  --clusters .\out\era17\clusters.json `
  --cluster-points E:\omen\steward-era17-arch\cluster-zdos.parquet `
  --building-geometry E:\omen\steward-era17-arch\building-geometry.parquet `
  --piece-geometry .\out\era17\arch\piece-geometry.json `
  --rotation-verify .\out\era17\arch\rotation-verify.json `
  --control-cluster 713 `
  --out .\out\era17\framing-envelope-probe
```

Uncertainty list: oriented boxes are massing proxies, not render meshes, and can include
buried or occluded volume that a photograph need not show. Mesh-only non-vegetation
bounds remain approximate even though family medians are excluded. These 48 clusters
were selected for creator coverage rather than randomly. Runtime recovery changed some
poses; actual-lens projection measures the landed result but does not isolate the move.
The probe measures geometric retention, not facade legibility, foliage, exposure, haze,
or taste. Only the paired AM4 photographs can say whether the extra distance improves
the picture rather than merely satisfying the envelope.

## R&D lap — world-save bytes can render as literal CSS 3-D (2026-08-27)

**Edge found:** exact ZDO geometry is enough to make a recognizable browser-native
building without SVG, canvas, WebGL, Three.js, or a network request. It is not enough to
make the complete building interactive at one six-face DOM box per piece.

`probe_css_render.py` joined all **861 / 861** frozen cluster-1820 members to the
independent rotation export by `zdo_index`, with zero prefab or x/y/z mismatches. The
already-PASSed `deg_unity` rotation receipt and prefab center offsets/extents produced 14
physical components; the main structure contains **847 pieces**. Its self-contained HTML
uses 847 positioned `.piece` groups, **5,082 CSS faces**, CSS perspective and
`matrix3d()`. Absolute world coordinates are subtracted before serialization. Six planar
prefabs needed a declared 1 cm render-only thickness so their zero-sized axis could paint.

The ignored artifact at `out/era17/css-render/pilot-1820/index.html` opens directly from
disk. Drag orbit, wheel zoom, family filters, wireframe/solid modes, and the 78.8° / 258.8°
end presets all work. The three captured views preserve the hip roof, tower, storey mass,
openings, and the different end approaches strongly enough to identify the same structure
against the GLB massing and roof-end photographs. The translucent family-coloured solid is
more legible than the minimum wireframe claim.

The same page found the browser edge rather than a data edge. In headless Edge 151 on this
workstation, the complete scene reached first paint in **176.5 ms** and contained **6,036
DOM nodes**, but a 120-frame synthetic orbit measured **311.3 ms p50 / 381.6 ms p95 / 405.3
ms max**. The lap's interactive gate was 50 ms p95, so it failed at the pilot and correctly
did not run the cluster-182 stress ladder. The frozen stress membership is 22,393 ZDOs
(22,205 with known geometry), not the older padded-bbox GLB manifest's 25,837 pieces.

**No promotion.** Literal CSS 3-D has earned use as a small, static or lightly interactive
evidence rendering. A scalable building viewer still needs a different projection or a
piece/face aggregation lap.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\probe_css_render.py
```

Uncertainty list: headless Edge can use a different compositor path from a visible,
hardware-accelerated window, so the timing edge is specifically the reproducible headless
lane. The CSS presets preserve geometry but are not pixel-registered to the game cameras.
Oriented boxes remain massing proxies rather than render meshes, and translucent faces do
not model terrain, hidden-surface removal, materials, lighting, or occlusion. The 1 cm
thickness for planar pieces is a display accommodation. Cluster 182 has 188 frozen members
without known prefab geometry, and no stress tier was sampled because the complete pilot
had already crossed the declared edge.

## R&D lap — WebGPU removes the DOM ceiling; membership is the next edge (2026-08-27)

**Clean scale sample:** no GPU edge was reached. `probe_webgpu_render.py` replaced every
CSS face with one shared unit cube and an 80-byte per-ZDO instance record. The same
cluster-local position, `deg_unity` rotation, prefab center offset, extents and family
colour now pass through WGSL into an opaque depth-tested triangle pipeline or a separate
line-list wireframe pipeline. There is no WebGL fallback, framework, GLB expansion, or
absolute world origin in the generated scene.

The 847-piece cluster-1820 control preserved the hip roof, tower, storeys, openings and
different end approaches seen in the CSS and photographic controls. Its 67,760-byte
instance buffer, 10,164 triangles and 13 family draw ranges started in **282.4 ms** and
held a 300-frame orbit at **16.8 ms p95**, with **0.4 ms p95** JavaScript submission.

That unlocked the only scale sample: every cluster-182 member with known prefab geometry.
The join covered **22,393 / 22,393** frozen ZDOs with zero prefab or x/y/z mismatches;
22,205 have geometry and 188 unknown hashes remain omitted. The result is **22,205 GPU
instances / 266,460 triangles / 1,776,400 bytes**. In a 1600×1000 headless Edge window
(1274×903 GPU canvas), it started in **294.7 ms** and held **16.9 ms p95**, with **0.3 ms
p95** submission, zero validation errors and no device loss. The browser granted a real
Intel `xe-lpg` adapter under the high-performance preference. Performance was flat against
the pilot within the measurement's resolution.

The ignored artifacts live under `out/era17/webgpu-render/`: two local-server scenes,
five captures and `result.json`. The stress wireframe makes the full stepped complex and
domes legible. Its opaque view also found the next edge without being asked: full frozen
membership contains 15 vegetation-like instances. `Oak1` contributes a
30.576×25.523×35.856 m mesh/LOD box and `AshlandsTree6_big` a 19.179×17.703×19.211 m box;
the oak visibly masks the centre of the solid architectural view. This is the same
vegetation-bounds problem the framing lap already identified, now exposed as scene
semantics rather than camera math or GPU capacity. It was recorded, not filtered.

**No promotion.** Instanced WebGPU has cleared the sampled rendering scale and earned a
later viewer slice. This probe does not alter the GLB viewer or claim that unfiltered
cluster membership is an architectural scene graph.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\probe_webgpu_render.py
```

Uncertainty list: `requestAdapter({powerPreference: "high-performance"})` is a hint and
did not prove one of the two Arc Pro B70 devices was selected; the exposed adapter was
Intel `xe-lpg`. Frame intervals include browser presentation and CPU submission rather
than timestamp-query GPU duration, although the granted adapter reports timestamp-query
support. The render target is the 1274×903 canvas inside the declared 1600×1000 window.
Only one pilot and one full cluster were sampled. Oriented boxes remain massing proxies;
opaque solids and one-pixel lines do not test transparency, terrain, textures, picking,
culling, mesh fidelity or a visible-window compositor. The 188 missing prefab geometries
and vegetation/LOD bounds are input omissions, not GPU failures.

## R&D lap — one numeric spatial revision reaches the live boundary (2026-08-27)

**Edge found before the live sample:** one reviewed 12-piece Godbuild now has a bounded
path from a hardware WebGPU preview and numeric Unity-world X/Y/Z/yaw controls to Quest
Lab's fixed request mailbox. The Lab side compiles the same transform into piece positions
and rotations. The browser surface, artifact pins, mailbox contract, and mod build passed;
the currently running Creator Session prevented the only live apply, so this is not a
claim that placement has landed in Valheim.

`probe_live_spatial_revision.py` is deliberately one asset rather than a catalog. It
hash-verifies the plan, manifest, blueprint, and capture; stages only the byte-identical
reviewed pair; renders the shelter through the existing 80-byte WebGPU instance path; and
exposes X, Y/height, Z, and yaw. Apply reuses `blueprint_build` with the narrow
`build_mode: at` shape. The request is machine/world/Creator-Session pinned, refuses a
busy mailbox, and waits for a receipt whose schema, request id, operation, machine, world,
session, and echoed transform all agree. Clear reuses the existing marked-build removal.

The exact-placement implementation treats the requested XYZ as the blueprint's local
bounds-minimum corner. It subtracts the captured bounds minimum, rotates each local
position by the requested whole-building yaw, and left-composes that yaw with every
authored piece quaternion. It never samples terrain or silently changes Y. Ordinary
ground and sky builds keep their prior behavior. Placement fields are rejected on every
other operation and are bounded to finite world coordinates within +/-10,500 m and yaw
within +/-3,600 degrees. Malformed build-at requests still receive a rejection receipt;
their invalid values are not re-parsed while writing it.

The prepared control is `first-portal-progression-shelter`: 12/12 pieces, blueprint SHA-256
`1c2e71857cfbf6ea08eb23b6e58256c484467a1dc22fa7e92f064ee19fcdc881`, capture SHA-256
`d9f8c8f49f15917aa3d96369e5d4c04829fa32d6c6c6327a4d8a714b4bf46798`. Headless Edge
151 granted an Intel hardware adapter and visibly submitted the 144-triangle scene with
all four live controls at `out/live-spatial-revision/browser-edge.png`. The Lab Release
build completed with zero warnings and zero errors; its DLL SHA-256 is
`3befe196d945cd348fc057cf93180c9a2ad70e8f81ea206662cde8376bad2408`.

**BLOCKED before sample; no request was sent.** Creator Session
`era17-pilgrimage-20260827-r13` owns the running `ComfyEra17` process and has the prior Lab
DLL SHA-256 `4a19455e213549d4f137d4decda632e26a581aba4a9c7be751c0de9762804377`
loaded and pinned. Loading the new code requires a clean Creator Session preparation and
Valheim restart. Replacing the DLL or stopping the process here would have crossed into the
concurrent saga++ agent's active play/build lap. The live mailbox was left empty and the
world was not mutated.

Exact rerun after the next Creator Session has prepared, installed the new Lab DLL, and
entered `ComfyEra17`:

```powershell
Set-Location C:\work\baseline
$creator = Get-Content 'C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\config\comfy-quest-creator\session.json' -Raw | ConvertFrom-Json
$built = (Get-FileHash 'C:\work\comfy-quest\network\mod\ComfyQuestLab\bin\Release\ComfyQuestLab.dll' -Algorithm SHA256).Hash
$installed = (Get-FileHash 'C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\plugins\ComfyQuestLab.dll' -Algorithm SHA256).Hash
if ($creator.state -ne 'active' -or $built -ne $installed) { throw 'Prepare and enter a new Creator Session with the spatial Lab DLL first.' }
python .\tools\selfie-stick\probe_live_spatial_revision.py `
  --plan C:\work\comfy-quest\examples\worldbuild\first-portal-progression-shelter\plan.json `
  --manifest C:\work\comfy-quest\examples\worldbuild\first-portal-progression-shelter\manifest.json `
  --blueprint C:\work\comfy-quest\examples\worldbuild\first-portal-progression-shelter\first-portal-progression-shelter.blueprint `
  --capture C:\work\comfy-quest\examples\worldbuild\first-portal-progression-shelter\first-portal-progression-shelter.capture.json `
  --lab-root 'C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\config\comfy-quest-lab' `
  --expected-machine $creator.expected_machine --expected-world-uid $creator.world_uid `
  --creator-session-id $creator.session_id --x -4539.03 --y 35.65 --z 747.481934 --yaw 37
# In the opened page, inspect the control and press Apply in Valheim exactly once.
```

The candidate transform is 29.5 m from the captured character logout point. In the frozen
world extract its nearest non-terrain ZDO is 13.36 m away, while nearby authored objects
sit at Y 35.64-35.69 m; this is preflight evidence, not a terrain guarantee.

**No promotion.** Exact transform composition has earned one live receipt, not a catalog,
palette, generalized placement contract, or Creator OS integration.

Uncertainty list: no new-DLL live placement or receipt exists yet. The selected ground
height is inferred from the frozen save rather than sampled from live terrain. Bounds-min
is deterministic but may not be the eventual semantic pivot creators want. The WebGPU
objects are prefab massing proxies rather than meshes. Yaw composition compiled but has
not been visually checked in-game. Chrome 151's headless screenshot lane hung while
requesting an adapter; the same page rendered on hardware in headless Edge 151, and the
earlier visible prototype remained fast. The current world may drift before the safe
Creator Session boundary.

## R&D lap — oriented save geometry becomes an architectural SVG (2026-08-28)

**Edge crossed:** oriented prefab envelopes are sufficient for a useful vector
architectural survey sheet. The old Godbuild `preview.svg` was a top-down pivot scatter;
it discarded the height, depth, physical extent and rotation that distinguish a building.
`probe_architecture_svg.py` instead projected the already-verified oriented boxes into one
self-contained four-view plate without Valheim, meshes, canvas, WebGL, JavaScript, images,
external fonts or a network request.

The input freeze held exactly: **861 / 861** cluster-1820 members joined the independent
rotation export with zero prefab or x/y/z mismatches, all 861 had geometry, and the largest
of 14 connected components remained the known **847-piece** building. The source AABB was
39.2021 × 25.2314 × 33.5280 m. Its disagreement with the independent WebGPU control after
that control's two-decimal serialization was only 0.002121 / 0.001384 / 0.002006 m.

The resulting `out/era17/architecture-svg/cluster-1820/survey.svg` contains an
axonometric, a ridge-aligned roof plan, and bearing-labelled 78.8° / 258.8° elevations.
Each projected face retains stable `data-zdo`, `data-prefab`, and `data-family` attributes.
Opaque faces are back-face culled and globally depth-sorted; a projected polygon union
adds the strong exterior line without pretending to be exact CAD hidden-line removal.
Dimension strings report the proxy envelopes, while the title block pins the rotation
decode, geometry sources and abbreviated evidence hashes. Absolute world coordinates are
withheld.

Both gates passed:

| gate | result |
|---|---:|
| main component | **847 pieces** |
| SVG structure | **7,584 elements / 1,698,993 bytes / valid XML** |
| headless Edge 151 paint | **1,062.41 ms / 223,982-byte PNG** |
| axonometric | tower, stacked storeys, external stair and stepped roof retained |
| roof plan | ridge-aligned envelope and asymmetric appendages retained |
| 78.8° control | continuous sloping thatched hip; no wall triangle |
| 258.8° control | stone gable triangle with repeated window rows |

The paired elevations are the decisive observation. They reproduce the differential that
the AM4 photographs independently confirmed: the 78.8° end and 258.8° end cannot be
mistaken for the same architecture. Simple painter ordering did not cross its edge on this
building; no hidden-line follow-up was needed.

The ignored evidence bundle is `out/era17/architecture-svg/cluster-1820/`: `survey.svg`,
its `survey.png` browser capture, and `result.json` with full input hashes, projection
spans, face counts, gate results, visual adjudication and exact rerun command.

**No promotion.** One passed 847-piece plate earns a later replayable-shelter/catalog lap.
It does not establish automatic bearing inference, floor-plan semantics, an asset schema,
a catalog generator, Creator OS integration or CAD fidelity.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
C:\work\venvs\steward-arch\Scripts\python.exe .\probe_architecture_svg.py `
  --visual-verdict PASS `
  --visual-observation 'Axonometric preserves the tower, stacked storeys, external stair, and stepped roof mass.' `
  --visual-observation 'Roof plan exposes the ridge-aligned stepped envelope and asymmetric side appendages.' `
  --visual-observation 'The 78.8-degree elevation reads as a continuous sloping thatched hip without a wall triangle.' `
  --visual-observation 'The 258.8-degree elevation reads as a stone gable triangle with repeated window rows and cannot be mistaken for the 78.8-degree end.'
```

Uncertainty list: oriented boxes remain massing proxies rather than mesh surfaces, so
curves, carved profiles and material boundaries are simplified. Global face-depth sorting
is not exact hidden-surface removal for intersecting boxes even though no decisive error
appeared here. The roof plan is a top projection, not a semantic horizontal cut through a
floor. Dimensions describe the proxy envelope rather than snap-grid construction lengths.
Photographic controls include perspective, terrain, vegetation, lighting and materials
that the plate intentionally omits. One unusually well-evidenced building says nothing yet
about diagram legibility across small shelters, compounds, towers or vegetation-heavy
clusters.

## R&D lap — public measured drawings become a reproducible local corpus (2026-08-28)

**Edge crossed:** the Library of Congress HABS collection can be queried, filtered,
resolved to sheet-level master resources, and normalized into a byte-verifiable local
architectural corpus without authentication or hand-downloading. This lap stops at
acquisition. It does not infer drawing geometry, build a semantic graph, choose Valheim
pieces, or write ZDOs.

`habs_harvester.py` exposes three bounded operations: `search` filters the combined
HABS/HAER/HALS collection by program, building type, state/location facet, explicit
building/structure dates from item notes, and keyword; `harvest` resolves frozen or queried item IDs to drawing sheets and
their complete TIFF/JPEG/JSON-caption variant lists; `verify` rehashes every local file
and rejects missing, altered, escaping, or stale undeclared paths. The frozen
`habs-corpus.json` selection prevents collection growth or search-order drift from
silently changing the proof corpus.

The accepted corpus is **20 buildings / 69 measured sheets / 127,676,740 bytes** under
`out/loc-habs/corpus/`. Each control-number directory contains normalized
`metadata.json`, a sheet/variant `manifest.json`, and master TIFFs named by evidence-backed
role where metadata permits. The metadata retains the complete LOC item object alongside
control/call/survey identifiers, all source and resource URLs, contributors, locations,
subjects, documentation and construction dates, notes, media descriptions, repository,
and unshortened rights fields. Download records add API size, HTTP validators, actual
bytes, SHA-256, and decoded dimensions.

The second acquisition was the determinism gate: **69 cached / 0 downloaded**, and the
sentinel `tn0306/drawings/section-01.tif` modification time remained byte-for-byte
unchanged. `verify --expected-buildings 20` passed 20 buildings, 69 files, 127,676,740
bytes, all hashes and all locally decoded dimensions. Visual spot checks independently
confirmed readable dimensions and the declared plan/section/elevation roles on Alfred's
Cabin, a plan/section on the Dyer barn, and plans/sections/elevations on the Banta barn.
The older Bertolet-Herbein API titles expose only
sheet ordinals, but its masters visibly resolve to a title sheet, site sheet, and
dimensioned first/second-floor plans; those files remain `drawing-NN` because visual
knowledge was not silently promoted into the remote metadata classifier.

The acquisition itself found the useful edge cases. A collection result's
`photo, print, drawing` format is not evidence that measured drawings exist; a drawing
resource is. Search resources carry integer file counts while item resources expand to
nested sheet/variant lists. Search `medium` can be absent when item detail says
`Measured Drawing(s): N`. A sheet may simultaneously be a plan and section. Old captions
may say only `sheet N of M`. Master TIFF dimensions are often zero in JSON while JPEG
dimensions are populated. Documentation dates and building dates are different fields.
Some resource group URLs are absent even when direct sheet URLs exist. LOC also
occasionally closed JSON responses early, and several item records advertised small
master sizes while serving valid 130+ MiB TIFFs. The harvester retries incomplete
responses, trusts HTTP length plus decoded-file integrity for acquisition, and preserves
rather than erases API disagreements.

Rights are carried, not summarized into a license claim. The common LOC advisory says
U.S. Government images have no known restrictions but copied-source images may be
restricted, and that distinction survives in every building directory.

Exact rerun:

```powershell
Set-Location C:\work\baseline\tools\selfie-stick
python .\habs_harvester.py harvest
python .\habs_harvester.py verify --expected-buildings 20
```

**No promotion.** A trustworthy source corpus earns a later single-sheet interpretation
probe. It does not yet earn OCR, vectorization, scale inference, a building graph, a
catalog, prefab mapping, Creator OS integration, or architectural import.

Uncertainty list: only a visual subset of the 69 sheets was adjudicated. Forty-one legacy
sheets remain deliberately role-unclassified because LOC supplies no descriptive title.
LOC search facets are derived from inconsistent catalog values; construction-date
filtering therefore excludes records without explicit building/structure-date notes rather
than guessing from documentation dates. HEAD validators plus local hashes avoid
unchanged downloads but cannot promise LOC will never replace bytes without changing
Content-Length or Last-Modified. The 20 records favor small forms but are a curated R&D
sample, not a statistically representative account of HABS holdings.

## R&D lap — one measured building reaches a portable Valheim candidate (2026-08-28)

**Partial success at the frozen safe boundary.** `probe_architectural_roundtrip.py` took
HABS `sd0401` through a content-addressed evidence bundle, three-anchor calibration,
provenance-bearing metric building graph, fidelity router, three browser comparisons,
90-piece Godbuild candidate, hardware WebGPU preview, deterministic Build Capsule, and
read-only Creator OS preflight. CSS is a projection and measuring instrument; the graph
remains authority.

The run asked for F3 inhabitable and correctly received only F1 massing. The sheets carry
enough evidence for a weather shell and much of an inhabitable plan, but the compiler does
not yet resolve secondary roof junctions, opening-aware wall segmentation, or dimensioned
interior partitions. Those omissions are named in `route.json`; none is silently filled.
Physical scale remains 1.000. Exterior wall pivots are inset by their 0.4274 m thickness so
their outer faces land on the measured footprint. The largest declared major residual is
0.057 m and the plan overlay makes residuals visible.

Revision `c2e64ee9cd262dd1a660` registered three independent plan anchors with 1.03%
spread, inside the frozen 2% gate. All graph checks passed. The candidate contains 38
`wood_floor`, 34 `woodwall`, 16 `wood_roof`, and 2 `wood_roof_45` pieces. Its blueprint
SHA-256 is `76457ef67e0b03a09e430a52c0c04cc9e36080bc93f757c06443694da22c4005`;
the capture SHA-256 is
`4db4d6748d29070c81309634621d80cad034fc3b786afbfc865947a4b4d27899`.
An isolated Quest Lab fixture hash-verified and staged that exact pair.

Headless Edge 151 used an Intel hardware adapter for the 90-instance / 1,080-triangle
WebGPU view with no validation errors, 282.2 ms startup, and 17.0 ms p95 across 30 frames.
The view deliberately shows oriented prefab envelopes rather than claiming mesh fidelity.

The deterministic 128,649-byte capsule has SHA-256
`bc94c70a3b68784f840f0b47b74f3e972492a2be4a58778cd206c47f2737a218`.
Inline base64url and a local HTTP URL independently resolved to those exact bytes and all
19 internal members passed their hashes. A `gdoc:<document-id>` text-export bridge is
implemented but remains UNVERIFIED because no shared document was supplied. The package
contains no absolute paths.

Persistence was exercised rather than asserted: the process stopped after calibration,
resumed with acquire/inventory/calibrate cached, then completed; a following full run
reused all eight immutable stages with zero network downloads. Source, building-local,
and Valheim-world coordinates remain separate.

**BLOCKED safely before live build.** The Creator Session is closed, Valheim is not
running, the built and installed Lab DLL hashes differ, and world anchor/yaw is unresolved.
No mailbox request was written and no world was mutated. Consequently there is no live
piece receipt, ZDO diff, save extraction, or round-trip CSS claim.

The next earned edge is F2: opening-aware wall bays plus the vestibule and mechanical-wing
roof junctions on this same frozen specimen. The full artifact map, resolver commands, and
coordinate contract are in `ARCHITECTURAL-ROUNDTRIP.md`.

## R&D lap — the frozen specimen earns an F2 weather shell (2026-08-28)

**Success at the frozen non-live boundary.** `probe_architectural_roundtrip_f2.py`
inherited accepted v0 revision `c2e64ee9cd262dd1a660` without reacquiring or changing its
evidence, calibration, or parent graph. The F2 charter required opening-aware exterior
wall bays, explicit main/vestibule/mechanical roof planes, a closed-shell error budget,
physical scale 1.000, no more than 256 pieces, deterministic restart/transport, and an
isolated Creator contract pass.

Revision `3d7189c1c6641f19f873` passed all 14 gates and was promoted to
`F2_WEATHER_SHELL`. Eighteen of 19 source openings compile (94.7% recall): 3 doors and 15
windows. Opening-center error and wall intrusion are both 0.000 m; the largest remaining
solid-wall gap is 0.010 m. All target-module adaptations are published. The one omission,
the vestibule east door, remains explicit because its target swing envelope exceeds the
1.378 m host wall.

Six actual roof planes replace every flat placeholder: paired 26.565-degree main slopes,
a paired 45-degree vestibule gable, and a paired inferred 26.565-degree mechanical-wing
gable. Plan coverage is 100%, both attachment junctions overlap with zero computed gap,
the main ridge error is 0.026 m, vestibule eave error is 0.083 m, maximum secondary
overhang is 0.588 m, and maximum declared weather seam is 0.045 m. The mechanical-wing
pitch remains marked as target inference rather than measured certainty.

The resulting candidate is **250 pieces / 256 allowed**. Edge 151 submitted all 250
prefab-envelope instances (3,000 triangles) to an Intel hardware WebGPU adapter with no
validation errors, 332.2 ms startup, and 17.7 ms frame p95 over 30 samples. The visual
gate caught and removed a stale F1 label before acceptance.

The isolated Quest Lab fixture accepted and hash-preserved the exact 250-piece pair. The
deterministic 143,248-byte Build Capsule contains 25 members and has SHA-256
`0630fcdec4e99c05fa38c42aacdd98d8a9c2dab40affbf8ca97240d4f83fa034`.
Inline base64url and local HTTP transports resolved byte-identically; a separate CLI
resolver/extraction test verified every member and the inherited revision receipt.

Persistence was exercised at the new compiler boundary: execution stopped after
`openings`, resumed with `inherit` and `openings` cached, then completed. The next run
cached every immutable stage; only the mutable Creator preflight was re-observed.

**BLOCKED safely before live build.** Creator Session is inactive, Valheim is not running,
the installed/built Lab DLL hashes differ, and world anchor/yaw remains unresolved. No
mailbox request was sent and no world was mutated. F3 now requires dimensioned interior
partitions and a room/traversal graph. A live build, save extraction, and XYZ/quaternion
round-trip are still a separate safe-session experiment, not implied by F2 promotion.

## R&D lap — twenty buildings become an automatic transfer curriculum (2026-08-28)

**Experiment machinery passed; architectural inference did not run.** The frozen question
is whether the accepted `sd0401` approach can transfer automatically to the other 19 HABS
buildings and improve as accepted examples accumulate. The charter fixes a hybrid-local
boundary: OCR and deterministic geometry own numbers, a digest-pinned local Qwen VLM may
propose semantics, unsupported facts remain unresolved, and no manual geometry overrides
are allowed.

`probe_architectural_curriculum.py` now executes that question as a continuous curriculum.
It first creates a lesson-free baseline for every record, clusters the 20 on log footprint
area, mean elevation height, and floor count, chooses 3–6 clusters by deterministic
silhouette, then walks outward Pareto shells while alternating footprint and vertical
growth. The fixture produced six clusters: small single-storey cabins first, then larger
cabins/houses/farmhouses, and finally 93–175 m² two-storey barns. `sd0401` remains the
explicit seed control even though the independent curriculum order begins with the smaller
`pa0119`.

Every later assessment retains both candidates. The control is lesson-free; the cumulative
candidate retrieves at most three nearest mechanically accepted examples. A candidate
that loses any previously passing deterministic gate is rejected and the baseline is
retained. Advancement is a higher A0/G1/F1/F2 level or fewer unresolved assertions.
Cluster checkpoints form a SHA-256 lesson chain. This makes “learning” falsifiable rather
than a synonym for processing records in order.

Fixture revision `3cfb9c3c83dad69af3df` exercised all 20 baselines and all 20 cumulative
builds. It produced 20 normalized evidence sets, assessments, metric graphs, generic
piece plans, three CSS views per building, WebGPU scene packages, six cumulative lesson
packs, 20 deterministic building capsules, a catalog capsule, and a linked curriculum
dashboard. The self-contained catalog is 36,497,944 bytes with SHA-256
`27f897fa9d249b8f0b899926cbed7af1b9e5929e9cf667b39a9c348ffe7230b9`; source TIFFs are
excluded, normalized PNG evidence is included, and hashes plus LOC URLs retain the master
provenance.

The fixture deliberately reports `SIMULATION_NOT_EVIDENCE`. Its synthetic proposals route
all 19 unseen records to F2 across four building types, but that count proves only routing
coverage. Baseline and cumulative candidates are intentionally equivalent: **0 advanced,
0 regressions, learning NOT_DEMONSTRATED**. No fixture number is admitted as architectural
evidence.

Persistence crossed its gate. A following unchanged run validated and reused all **40 / 40**
stage receipts with **0 OCR calls / 0 VLM calls / 0 downloads**. Verification passed all 20
assessment/control contracts, output hashes, regression fallbacks, six lesson-chain links,
20 capsule manifests, the catalog contract, and the no-TIFF duplication rule.

The rendering gate did not pass in the current environment. The largest fixture candidate,
`wa0761` at 199 generic pieces, received `requestAdapter returned null` from headless Edge
on all three isolated attempts. The browser still captured a PNG, but the receipt correctly
marks hardware/status/startup/frame gates failed rather than interpreting capture as GPU
execution. This is a mapped environment edge; earlier accepted single-building receipts
remain historical evidence, not permission to overwrite this run's failure.

The pinned real environment is otherwise ready. Pillow 12.3.0, NumPy 2.5.0, OpenCV
4.13.0.92, ONNX Runtime 1.29.0, RapidOCR 3.9.2, and scikit-learn 1.9.0 match the lock. Three
RapidOCR model files are SHA-256 pinned, all 69 source TIFF hashes pass, and an independent
OCR smoke on `sd0401` returned 99 tokens. Real revision `1434e942ff9eee95fa6e` then
**blocked before perception** because `qwen2.5vl:7b` was not available at the managed local
endpoint. No fixture fallback, alternate model, request, Valheim contact, or world mutation
occurred; verification of the blocked revision passed.

**No architectural promotion.** The infrastructure can now tell us whether transfer and
learning work, but it has not yet observed them. The next earned edges are to make the
already selected pinned VLM available without replacing the managed service, rerun the
real 20-building curriculum, and restore a headless hardware adapter for the largest-scene
gate. Blind visual adjudication comes only after those automatic gates produce real
candidates.

Exact fixture rerun:

```powershell
Set-Location C:\work\baseline
python tools\selfie-stick\probe_architectural_curriculum.py run `
  --fixture-vision `
  --out tools\selfie-stick\out\architectural-curriculum\habs-v1-fixture
python tools\selfie-stick\probe_architectural_curriculum.py verify `
  --fixture-vision `
  --out tools\selfie-stick\out\architectural-curriculum\habs-v1-fixture
```

The full workflow, outcome ladder, artifact map, and real commands are in
[`ARCHITECTURAL-CURRICULUM.md`](ARCHITECTURAL-CURRICULUM.md).

## R&D lap — the clustered real OCR lane holds water, with a named leak (2026-08-28)

**The real numeric lane passed as constraint evidence, not scale authority.** With the
pinned VLM still unavailable, `probe_habs_ocr_audit.py` ran the narrower frozen charter
over every one of the 69 HABS sheets using the pinned RapidOCR and OpenCV stack only.
There were no VLM calls, network requests, catalog-title numeric substitutions, Valheim
contacts, or world writes.

Final revision `017d196e9584e4c0aa98` produced 4,834 real OCR tokens, 214 strict local
dimension candidates, 227 held dimension-like strings, and 213 nearest-line CV candidates.
All 69 sheets cleared the ten-token gate, 37/69 carried strict dimensions, 67/69 carried
OCR role signals, and median token confidence was 0.9875. All six gates frozen before the
run pass, yielding `USABLE_TO_CONSTRAIN_SEMANTICS · NOT_AUTONOMOUS_SCALE_AUTHORITY`.

The pre-sort was an experimental control, not decoration. The deterministic 18-signal
board sampled three signals from each of its six routing strata. Manual comparison against
the normalized sheets found 13/15 strict values correct and all 3/3 scale-label controls
correctly held. C00, C01, C03, and C05 were 3/3; C02 had no strict parse and correctly held
all three controls; C04 was only 1/3. Its misses were a compound door dimension split into
a plausible feet-only value and an inch mark promoted to feet. A single OCR-confidence
threshold would miss both. Cluster-specific redundancy is therefore earned for the next
scale experiment.

The visual loop caught and corrected five classes of parser defect before the result was
frozen: metric scale/reference false positives, lumber-size false positives, ordinal
suffixes, a scale fragment joined to an author credit, and greedy multi-token windows that
turned local evidence into half-sheet boxes. The final join rule permits split notation
only when the dimension begins in the first token. That change made the selected evidence
regions local without reacquiring a single sheet.

Persistence held through the iterations. Each parser revision reused all 69 immutable OCR
artifacts and made zero OCR calls while recomputing derived facts and CV candidates. The
final unchanged run caches all 69 stages. The visual adjudication, exact sample hash, per-
cluster verdicts, and limitations are in
[`architectural-ocr-review-v1.json`](architectural-ocr-review-v1.json).

**No scale promotion.** A correct local measurement is not yet an envelope role. Width,
depth, and height still require cross-view role agreement or redundant dimension agreement;
C04 must take the stricter route. That is the next earned gate.

## R&D lap — automatic HABS envelope fit reaches the vertical edge (2026-08-28)

**Edge found: calibration is no longer the first missing connector; primary-mass and
vertical semantic selection are.** `probe_architectural_css_fit.py` consumed the frozen
69-sheet OCR/CV revision and swept all 20 buildings without OCR, VLM, network, download,
Creator OS, Valheim, or world activity. It automatically found 168 role-panel candidates,
bound 165 dimension candidates, calibrated panels from complete drawing-scale notation plus
the source TIFF's 400 DPI, fitted a shared metric envelope, and reserved a section or second
elevation before scoring.

The dimension-line merger crossed the first mechanical break: ticks and printed values had
split overall dimensions into short Hough segments. After merging only close collinear
fragments, `tx1037` obtained three mutually compatible primary-plan anchors (1:48 plus
46'-11" and 48'-10") and fitted a 14.8844 m by 9.840949 m plan envelope. `ak0535` independently
reached the same pre-holdout state. Those two are `G1_UNVALIDATED`, not promotions.

The held-out views stopped both. `tx1037` predicted ridge/eave at 3.922/2.054 m; its unseen
section measured 3.163/2.358 m from calibrated linework, and its held ceiling dimension was
2.927 m. Errors were 0.30–0.87 m, beyond both 0.25 m and 3%. `ak0535` missed its section by
2.69–3.53 m. The post-seal `sd0401` oracle recovered width exactly at 15.928975 m but selected
10.6426 m of compound/adjacent linework as depth instead of the 4.333875 m primary body, then
misread eave/ridge ordering and roof class. Result: **0 validated G1, 2 G1-unvalidated,
14 A0-triaged, 4 held; `INSUFFICIENT_AUTOMATIC_EVIDENCE`.** This is a useful negative result,
not a converter claim.

### Can't answer why

| UTC phase | Visible symptom | Evidence preserved | Why still unknown | Bounded next investigation |
|---|---|---|---|---|
| 2026-08-28 held-out scoring | Calibrated plan width holds while depth, eave, ridge, and sometimes roof class drift | 20 assessments, 168 panel crops, automatic pre-oracle seal, accepted-oracle comparison, per-gate residuals, CSS catalog | OCR-erased connected components can still join appendages, dimension lines, grade, poche, or adjacent views; the current evidence cannot attribute each error to outline selection versus baseline/eave semantics | On `sd0401`, `tx1037`, and `ak0535` only, compare candidate structural-line families and explicit dimension-chain topology before changing any corpus gate |

Exact rerun:

```powershell
Set-Location C:\work\baseline
$python = '.\tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'
& $python .\tools\selfie-stick\probe_architectural_css_fit.py run
& $python .\tools\selfie-stick\probe_architectural_css_fit.py verify
& $python .\tools\selfie-stick\probe_architectural_css_fit.py serve --port 8878
```

Uncertainty list: automatic title seeds over-segment some sheets; connected linework is not
yet a primary-mass selector; scale notation and DPI calibrate pixels but do not label which
outline owns them; the CSS shape score is similarity-aligned and non-authoritative; floor
count may be an explicit inference from one observed plan level; appendages, openings,
interiors, and complex roofs were not fitted; no browser performance claim, prefab routing,
Creator OS exchange, Valheim placement, or ZDO generation was sampled. The unchanged rerun
cached all 20 buildings with zero evidence reads and zero fit, OCR, VLM, network, download,
or world work; verification passed.

## R&D lap — three-building topology probe separates the attribution (2026-08-28)

**Edge found: the three visible misses are no longer one undifferentiated connected-component
problem. They are ownership errors at three different joins: panel/view partitioning,
dimension-chain ownership, and vertical datum semantics.**
`probe_architectural_css_topology.py` was kept to the prescribed `sd0401`, `tx1037`, and
`ak0535` slice. It reused the sealed `3899e363a8b63658dc8a` assessments and frozen real OCR,
clustered the actual Hough line families, rendered 39 diagnostic overlays, grouped explicit
dimension chains, and linked dimension intervals to nearby mass/datum labels. It made zero
new OCR, VLM, network, download, Creator OS, Valheim, or world calls.

The candidate evidence was sealed before the accepted `sd0401` graph was opened for this lap.
After that reveal, three independently surviving candidates matched the accepted primary
graph exactly: **15.928975 m width, 4.333875 m depth, and 3.302 m ridge**, each with 0 m
residual. The useful change is not another tuned threshold; it is knowing which connector
owned each prior failure:

| Building | Current wrong ownership | Topology evidence | Attribution |
|---|---|---|---|
| `sd0401` | The held “section” geometry and the north elevation were allowed to share linework; the plan used the 34'-11" compound depth | Cross-role crop overlap is **0.719356** of the smaller panel; the plan chain retains the exact **14'-2 5/8"** main-body band; width/depth/ridge all pass the post-seal oracle | **Panel partition + primary-mass selection** |
| `tx1037` | `CEILING | 9'-7 1/4"` was converted into an `eave_height_m` held-out check | Strict absolute `ROOF EDGE` values survive at 1.6764, 2.2352, and 2.26695 m; a damaged but unambiguous ridge token yields a probe-only 3.18135 m candidate; ceiling and eave are explicitly different datums | **Ceiling/eave semantic conflation**; the reported 0.873 m eave failure is invalid |
| `ak0535` | The floor-plan fit adopted the basement overall **35'-11"** as width and the held section used the basement-bearing component as its vertical envelope | Floor-plan topology labels **LOG CABIN 20'-8" × 16'-5"** and the **ADDITION** separately; floor/basement panel overlap is **0.566**; section C retains distinct ridge, ceiling, first-floor, and basement stacks | **Panel ownership + labeled submass loss + wrong baseline family** |

Result: **`ATTRIBUTION_SEPARATED`**, immutable revision
`cf5c847a7f5232d38c0c`, 49 hashed artifacts, verification `PASS`. The structural overlays are
not a new geometry authority; they make the line-family competition inspectable. Repaired
near-miss dimensions are explicitly marked `REPAIRED_PROBE_ONLY` and did not alter the frozen
strict parser or any promotion gate.

Exact rerun:

```powershell
Set-Location C:\work\baseline
$python = '.\tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'
& $python .\tools\selfie-stick\probe_architectural_css_topology.py run
& $python .\tools\selfie-stick\probe_architectural_css_topology.py verify
```

**Next boundary:** only after Derek locks this result, revise panel partitioning,
dimension-chain ownership, and the baseline/eave/ridge vocabulary. Do not tune the 20-building
promotion thresholds from these three examples, and do not promote any graph from this
diagnostic lap.

## R&D lap - v3 automatic cross-sheet registration stops at correspondence (2026-08-28)

**Result: acquisition risk is now bounded and plan/vertical metric spans can compose, but
the frozen automatic correspondence gate does not survive OCR across different sheets.**

The replacement holdout was frozen before raster download: eight buildings, 29 sheets,
seven states, four building types, and two metadata-sparse controls. The new HEAD-only plan
uses actual HTTP sizes rather than unreliable LOC API sizes. It rejected `mt0670` at
829,478,514 bytes against the 805,306,368 building limit, then froze a passing 123,099,962-byte
plan. Exact-plan harvesting and full SHA-256/image verification passed. Local OCR revision
`315ba9abcf599f639fa7` passed all six evidence gates and cached all 29 sheets with zero OCR
calls on rerun.

The unchanged v2 diagnostic baseline over the original 20 plus retired eight is revision
`7331f32e25b034d03d70`. V3 revision `5333d5eaed593d7607e4` emits 127 frame hypotheses and
preserves all 165 cross-sheet candidates. Registration requires independent plan and vertical
calibration, different sheets, one exact shared section marker, one compatible metric span,
one matching floor/grade origin, and one cut-line axis. Exactly one candidate must pass; there
are no weights, proximity tie-breaks, manual hints, or equal-scale assumptions. A distinct
calibrated vertical view is reserved before candidate construction and CSS remains read-only.

All v2 regression and retained-capability checks pass: exact `sd0401` dimensions, typed
`tx1037` ceilings, separate `ak0535` masses, 8 selected primary masses, 6 scale consensuses,
7 calibrated roof pairs, and both negative controls held. The scientific gate fails only at
validated G1 (0 actual, 2 required). `tn0304` and `tn0305` each pass five of seven registration
gates and have cross-sheet metric-span errors of 0.129833 m and 0.247305 m respectively, but
neither cross-sheet elevation has an exact section marker or matching origin. Their marked
sections are on the same sheet as the plan and cannot be admitted without violating the frozen
gate.

Development is unsealed, artifact verification reports `PASS / BLOCKED_AT_DEVELOPMENT_GATE`,
and no replacement building was processed by the fitter. The cached v3 rerun executes zero
evidence, topology, or CSS work. The next bounded experiment is upstream plan cut-line recovery:
detect section bubbles and their cut axis geometrically, anchor them to OCR labels, and test on
the current 28 without looking at replacement-fit results.

## R&D lap — pre-CSS topology passes development and fails blind transfer (2026-08-28)

**Result: deterministic ownership fixes the three diagnosed joins, but does not yet transfer
to the untouched 17-building split.** The locked follow-up is
`probe_architectural_css_fit_v1.py`, with frozen charter
`architectural-css-fit-v1.json` and contracts
`architectural-css-fit-schemas-v1.json`. It preserves the 69-sheet OCR revision, v0 promotion
tolerances, and no-manual/no-VLM/no-network boundary. It changes the dataflow instead:

```text
OCR/CV evidence
  -> disjoint view interiors
  -> owned dimension chains and mass hypotheses
  -> typed vertical datum graph
  -> architectural-building-graph/v1
  -> read-only architectural-css-residual/v1
```

CSS performs no panel discovery, dimension binding, mass selection, datum repair, or corrected
geometry. Its residual artifact pins the input graph hash, emits metric and shape errors with
one of `panel_ownership`, `dimension_chain`, `mass_ambiguity`, `datum_semantics`, or
`cross_view_geometry`, and keeps `corrected_geometry: null`.

The three-building development evidence was sealed before the accepted `sd0401` values were
scored. All seven checks passed:

| Development check | Result |
|---|---|
| `sd0401` primary dimensions | **15.928975 × 4.333875 m**, exact post-seal match |
| `sd0401` typed ridge | **3.302 m**, exact post-seal match |
| Cross-role view overlap | **0** |
| `tx1037` ceiling vocabulary | both surviving ceiling nodes remain `ceiling`; neither is scored as eave |
| `ak0535` mass ownership | LOG CABIN and ADDITION remain distinct |
| `ak0535` primary width | **6.2992 m**, not the basement's 10.9474 m |

That froze revision `da9fb53b6e49c3718ea3`. The remaining 17 were then exposed once. None
reached `G1_METRIC_GRAPH`: 13 routed `A0_TRIAGED` and four routed `HELD`; `tn0305` and
`il0180` correctly remained unpromoted. The scientific answer is therefore
**`INSUFFICIENT_AUTOMATIC_EVIDENCE`**, not `TRANSFER_OBSERVED`.

The blind gate distribution identifies the next upstream edge without authorizing a same-run
repair:

| Failed gate across 17 blind buildings | Count |
|---|---:|
| independent scale anchors / spread | 17 |
| numeric and plausible primary envelope | 17 |
| typed eave and ridge | 16 |
| selected closed primary mass with two-axis dimensions | 14 |
| opposed-slope gable topology | 5 |
| independent held-out view | 3 |

The first causal failures are not CSS residual tuning. They are scale-notation ownership into
the selected plan, sparse two-axis mass closure, and missing paired eave/ridge datums. The
aggregate sealed evidence contains 168 disjoint views, 319 observed dimension candidates,
150 chains, 57 mass hypotheses, 98 typed datums, and 32 cross-view registrations. Six damaged
facts earned `TOPOLOGY_CORROBORATED`; none became a sole scale anchor. The manifest covers 294
files (14,713,373 bytes), and verification passes all 20 building artifact sets.

Exact cached rerun:

```powershell
Set-Location C:\work\baseline
$python = '.\tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'
& $python .\tools\selfie-stick\probe_architectural_css_fit_v1.py blind
& $python .\tools\selfie-stick\probe_architectural_css_fit_v1.py verify
```

Expected receipt: revision `da9fb53b6e49c3718ea3`, 17 cached, zero executed/evidence/topology/
CSS work, result `INSUFFICIENT_AUTOMATIC_EVIDENCE`, verification `PASS`. No OCR, VLM,
network, download, Creator OS, Valheim, ZDO, or world activity occurred.

The first post-blind rerun exposed one persistence-only defect: the completed runner tried to
write different executed/cached counters into immutable `index.json` after all 17 receipts had
already validated. No evidence, topology, CSS, or route changed. The source now short-circuits
a completed blind seal, validates every receipt, and writes mutable cache counters only to the
root report. The locked scientific revision and its automatic seals were not rewritten; a
fresh reproduction therefore uses a fresh output root and obtains a new content address.

**Next boundary:** do not tune v1 from its revealed 17. They are diagnostic evidence for a
new charter, not a reusable blind set. The next experiment should freeze a fresh holdout and
focus upstream on transferring complete scale notation to a disjoint plan owner, closing a
two-axis primary mass without label-specific exceptions, and requiring paired typed eave/ridge
evidence before CSS. Do not admit learned topology patterns or reintroduce the VLM until a new
deterministic transfer gate passes.

## R&D lap — v2 causal repairs improve upstream evidence but fail to compose (2026-08-28)

**Result: the individual pre-CSS connectors improved substantially, but no building in the
revealed v1 failure cohort yet carries all of them through CSS at once. The fresh eight-building
fitter holdout was therefore not exposed.**

The successor experiment is frozen in `architectural-css-fit-v2.json` and implemented by
`probe_architectural_css_fit_v2.py`. It uses all 20 original buildings as development data,
including the now-revealed 17, and reserves a new eight-building LOC set as blind. The new
selection was made from metadata only, excludes every v1 ID, spans seven states and four
building types, and contains 27 drawing sheets. LOC's API advertised 25,859,916 master bytes;
the integrity-checked TIFF downloads actually total 726,848,012 bytes, a 28.1× underestimate
that must be treated as an acquisition-planning hazard.

The holdout OCR/CV lane ran locally before fitter development and was then pinned at revision
`b1743fa5580583635f51`. It completed all 27 sheets with 1,109 tokens, 47 strict dimensions,
76 held near-misses, 47 CV anchor candidates, 0.991 median token confidence, no VLM calls, and
no network activity during OCR. This is frozen input production, not fitter blind exposure;
none of its sheets, tokens, or routes were used to tune v2.

V2 moves four causal repairs ahead of CSS:

1. Dimension axes prefer an owned nearby cardinal line and retain token-shape orientation only
   as a held fallback.
2. Scale anchors are independently derived from complete notation, strict dimension-line spans,
   or compatible x/z spans on one closed primary loop; cloned values do not count as distinct
   origins.
3. A missing mass axis may use a repaired OCR number only when that number is line-owned,
   orthogonal to a strict axis, plausible, and corroborated by the same closed plan loop. It is
   explicitly reported as topology-corroborated and can never anchor scale.
4. Geometric ridge/eave datums are created as one opposed-slope pair. Their numeric calibration
   must come from evidence independent of the roof topology. CSS receives the completed graph,
   hashes it, enumerates only its two sealed principal projections, performs zero discovery, and
   leaves `corrected_geometry: null`.

The final development revision is `2c3595654934efe9a5ad`. All original regression controls
still pass: `sd0401` remains exactly 15.928975 × 4.333875 m with a 3.302 m ridge and zero view
overlap; `tx1037` ceiling nodes remain ceiling; and `ak0535` preserves LOG CABIN/ADDITION while
selecting 6.2992 m instead of the basement width. Both development negative controls remain
unpromoted.

| Frozen v1 failure cohort metric (17 buildings) | v1 | v2 | Development requirement |
|---|---:|---:|---:|
| selected closed two-axis primary mass | 3 | **8** | 8 |
| compatible independent scale consensus | 0 | **6** | 4 |
| calibrated paired roof datums | 1 | **7** | 4 |
| validated G1 | 0 | **0** | 2 |

Across all 20 development buildings, `tx1037` now reaches `G1_METRIC_GRAPH`, `ak0535` reaches
`G1_UNVALIDATED`, 14 route A0, and four remain held. Those two improved routes are known
regression controls, however, so they cannot satisfy the frozen failure-cohort transfer check.
Development acceptance is `FAIL`, no `DEVELOPMENT_LOCK.json` exists, and the eight-building
fit phase has **zero exposure**. Artifact integrity verification independently reports `PASS`
and `BLOCKED_AT_DEVELOPMENT_GATE` across 20 building receipts, 291 manifest files, and
15,434,863 bytes.

The important negative result is compositional. The development graphs contain 168 views,
319 dimension bindings, 156 chains, 57 mass hypotheses, 245 datums, 49 roof pairs, and 21
selected scale anchors. Mass ownership, scale consensus, and roof calibration now survive in
isolation, but often on different sheets or different buildings. No deterministic cross-sheet
registration currently proves that a plan mass and a vertical roof pair use the same building
frame. CSS is correctly refusing those partial graphs.

Exact cached diagnosis and verification:

```powershell
Set-Location C:\work\baseline
$python = '.\tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'
& $python .\tools\selfie-stick\probe_architectural_css_fit_v2.py develop
& $python .\tools\selfie-stick\probe_architectural_css_fit_v2.py verify
```

The development command exits nonzero because the scientific gate remains unmet; verification
still passes artifact integrity and confirms zero blind exposure. Do not run `blind`, lower the
two-G1 requirement, or inspect the fresh set to tune v2. The next earned R&D question is whether
explicit cross-sheet frame registration can join an already-owned plan mass to an already-
calibrated vertical roof pair without inventing geometry.
