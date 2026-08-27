# Roof semantics R&D - 2026-08-27

**Status: VERIFIED gate failure. Planner promotion is BLOCKED until a new model
passes an independent holdout.**

This receipt records the first end-to-end roof-semantics lap made possible by the
exact `x/y/z` cluster membership documented in
[`ZDO-COORDINATES.md`](ZDO-COORDINATES.md). The component-local model ran,
produced deterministic private architecture records, and then failed its frozen
photographic holdout. That is the result of the lap: roof semantics remain a
report-only experiment, and `plan_shots.py` does not emit roofline shots.

The private evidence directory is:

```text
C:\work\baseline\tools\selfie-stick\out\era17\roof-semantics-20260827
```

It is ignored because its JSON companions contain world-space bounds. No exact
world coordinate is duplicated in this tracked receipt.

## Probe and stop condition

The bounded question was whether component-local roof-plane assemblies could
replace cluster-wide yaw counting strongly enough to guide a camera toward a
ridge. The preregistered promotion gate was:

- at least 16/20 semantic points across ten independently framed clusters;
- zero clear photographic contradictions; and
- at least eight ridge-bearing hits within 15 degrees.

Any failed condition meant report-only output and no planner integration. The
gate failed all three conditions, so the lap stopped there.

## Frozen provenance

The run used ComfyEra17 snapshot 107 and the already-published cluster ids in
`out/era17/clusters.json`. `scan_clusters.py` was not rerun, and no component was
renumbered.

| input | bytes | SHA-256 |
|---|---:|---|
| `building-geometry.parquet` | 61,250,175 | `45d8642551ca904fbba0ddfe51f15294977ad3087fc530d5a41c86d99558691b` |
| `cluster-zdos.parquet` | 37,258,753 | `3055aefd0b192ecdd75d734dd2ae92db0c3ec6238cc728ca2ee29d1ec9580910` |
| `piece-geometry.json` | 394,911 | `74ecc5e164766defa5553251aaa8bb8115d2e8f7d1d7cebb5826917b350bd86c` |
| `rotation-verify.json` | 6,174 | `034f5adcb888d5c56603a520d4c8d4a7332974c2a2731d4127d258bbe774f872` |
| `clusters.json` | 2,228,707 | `3793ec99b3e674a59f2816b08b53984144a8b6969be17b65c17d27702eccc92f` |

The geometry exporter checkout was read-only during this lap. Its base revision
was `a5358e23e39ef705d0ddc9e557704d76a6da4d4a`, but that checkout also contained
uncommitted parser/exporter work. Therefore the 40-character revision identifies
the base, while the byte counts and artifact hashes above identify the actual
inputs. The base revision alone is not claimed as a published artifact authority.

The exact-member gate joins rotation rows by `zdo_index` and rejects a run when
snapshot/world metadata, frozen piece count, prefab identity, category, or any
`x/y/z` value disagrees. Here `y` is elevation. As in the coordinate contract,
photographic depth is the projection of `x/y/z` onto the camera axis, never the
raw `z` column.

## Edge found in the old heuristic

**VERIFIED:** replaying the prior cluster-global yaw heuristic on the raw rotation
artifact reproduced its four calibration outputs:

| cluster | old dominant label |
|---:|---|
| 578 | hip |
| 916 | gable |
| 1775 | gable |
| 1820 | hip |

Cluster 1820 exposed the numerical edge. Recomputing from the rounded graph JSON
appeared to yield a gable, while the archived tool operating on raw rotations
reproducibly yielded a hip. Values close to half-angle bins moved across the
boundary when rounded. Cluster-wide yaw counting therefore mixed detached roofs
and depended on a numerically unstable representation; rounded graph JSON is not
a valid source for recalculating that semantic.

## Component-local vertical slice

`roof_semantics.py` writes schema `selfie-stick-architecture/v2` with model
`roof-plane-assemblies/v1`. It:

1. consumes only exact frozen BUILDING members;
2. reconstructs raw Unity rotations using the verified `deg_unity` decode;
3. builds deterministic 5 cm snap-connected structural components and roof
   assemblies, with narrowly bounded 20 cm singleton absorption;
4. derives upward roof-plane normals from prefab snap planes rather than yaw
   counts; and
5. classifies each local assembly, preserving confidence and uncertainty codes.

The four shaped-on calibration cases all emitted a gable as their dominant roof:

| cluster | assemblies | dominant result | ridge bearing | confidence | output SHA-256 |
|---:|---:|---|---:|---:|---|
| 578 | 6 | gable | 146.25 | 0.524 | `ed777c6bfa94b79853b376491540aecb7a38c193cafb4d817e477e346477a94f` |
| 916 | 8 | gable | 90.00 | 0.737 | `3e9e94aba885db4376a648f8c06329864e4d60b26e54425a5d9fe7d565322b1c` |
| 1775 | 9 | gable, multiple axes | unavailable | 0.510 | `9d9d3ed5d8226a3d6670217d4fe8b1c0e99e98ad2622f1f1bb9707d255efb842` |
| 1820 | 11 | gable, attached planes | 78.75 | 0.471 | `f03d37a6f9e707ef9dbc4fce5703c6997ea191f7c61a54d802fa2b23a51eaac5` |

Two complete reruns produced byte-identical architecture files and manifests.
The final manifest SHA-256 is
`c471971830bc2faabfb6fe30fff7970401507c411d9c615e36966156c144c035`.
The same dependency-free implementation also reproduced all forty earlier
candidate architecture files byte for byte.

These calibration cases shaped the model and are not independent validation.

## Frozen holdout

Pass one selected forty candidates before inspecting model output. Eligibility
required 400-3,000 frozen BUILDING pieces, at least twenty known roof pieces, at
least two clean orbit variants, and exclusion of the four calibration ids. Rows
were ordered by ascending SHA-256 of `107:<cluster_id>`.

Pass two took the first five simple and first five compound model outputs in that
already-frozen order. The two adjudication frames per cluster were fixed from the
gallery independently of the semantic output.

| stratum | frozen cluster ids |
|---|---|
| simple | 2432, 2658, 2939, 1626, 446 |
| compound | 2094, 2072, 1810, 1003, 372 |

The selection rerun reproduced both manifests byte for byte:

| private artifact | SHA-256 |
|---|---|
| `holdout-candidates.json` | `60c4016745b4d2f62e66006feb91b9b6ee15b751c78505f5750141e8e8691c29` |
| `holdout.json` | `d522aa6c90b91b456e76daf548c068304a61e6144a0ee04a258d80001d27013c` |

## Photographic adjudication

The score rubric awarded 2 when both frozen views supported the dominant shape,
1 for partial or ambiguous support, and 0 for contradiction or insufficient roof
visibility.

| cluster | stratum | prediction | visibility | score | observation |
|---:|---|---|---|---:|---|
| 2432 | simple | gable | clear | 2 | continuous paired slopes and a visible gable end |
| 2658 | simple | gable | clear | 2 | repeated gable ends visible in both views |
| 2939 | simple | hip | clear | 2 | dominant thatch roof slopes around the visible perimeter |
| 1626 | simple | gable | clear | 2 | multiple triangular gable ends are visible |
| 446 | simple | complex | unavailable | 0 | canopy hides nearly all of the elevated roof |
| 2094 | compound | hip | clear | 0 | contradicted by an unambiguous triangular gable end |
| 2072 | compound | hip | clear | 2 | dominant lower roof wraps down all visible sides |
| 1810 | compound | gable | clear | 2 | several connected gable ends are visible |
| 1003 | compound | hip | unavailable | 0 | canopy, distance, and partial occlusion prevent adjudication |
| 372 | compound | gable | unavailable | 0 | distance and a particle/fog volume hide the topology |

Result: **12/20**. Cluster 2094 is the clear contradiction. No frozen view
supported an independent ridge-bearing measurement, so the ridge gate had zero
adjudicated bearings rather than eight hits.

| gate | required | actual | verdict |
|---|---:|---:|---|
| semantic score | at least 16/20 | 12/20 | FAIL |
| clear contradictions | 0 | 1 | FAIL |
| ridge hits within 15 degrees | at least 8 | 0 of 0 adjudicated | FAIL |

The manual judgment artifact SHA-256 is
`53b573a7b34b2ca0cac181ea1d08fd7581dedf7bd913e6a073cdbf8888e87ee7`.
The deterministic validation receipt SHA-256 is
`4b4a6dac9ea1fc34301cb07d6fc12f960ba1f84c8b3fe5eaed78f99dc19fbaef`.

## Planner consequence

**BLOCKED:** `plan_shots.py` may continue to consume exact point coordinates for
height, projected width/height, and camera-axis depth. It may not consume
`roof-plane-assemblies/v1`, select a ridge-facing hero view, or emit a roofline
shot. A future model must pass a newly frozen independent holdout before that
integration is reconsidered.

## Exact rerun

From `C:\work\baseline`:

```powershell
python .\tools\selfie-stick\roof_semantics.py `
  --cluster-ids 578,916,1775,1820 `
  --parquet E:\omen\steward-era17-arch\building-geometry.parquet `
  --cluster-points E:\omen\steward-era17-arch\cluster-zdos.parquet `
  --out .\tools\selfie-stick\out\era17\roof-semantics-20260827\calibration-rerun `
  --source-revision a5358e23e39ef705d0ddc9e557704d76a6da4d4a

python .\tools\selfie-stick\select_roof_holdout.py `
  --cluster-points E:\omen\steward-era17-arch\cluster-zdos.parquet `
  --out .\tools\selfie-stick\out\era17\roof-semantics-20260827\holdout-candidates-rerun.json

$candidateDoc = Get-Content `
  .\tools\selfie-stick\out\era17\roof-semantics-20260827\holdout-candidates-rerun.json `
  -Raw | ConvertFrom-Json
$candidateIds = $candidateDoc.candidates.cluster_id -join ','

python .\tools\selfie-stick\roof_semantics.py `
  --cluster-ids $candidateIds `
  --parquet E:\omen\steward-era17-arch\building-geometry.parquet `
  --cluster-points E:\omen\steward-era17-arch\cluster-zdos.parquet `
  --out .\tools\selfie-stick\out\era17\roof-semantics-20260827\candidate-model-rerun `
  --source-revision a5358e23e39ef705d0ddc9e557704d76a6da4d4a

python .\tools\selfie-stick\select_roof_holdout.py `
  --cluster-points E:\omen\steward-era17-arch\cluster-zdos.parquet `
  --candidates .\tools\selfie-stick\out\era17\roof-semantics-20260827\holdout-candidates-rerun.json `
  --architecture-dir .\tools\selfie-stick\out\era17\roof-semantics-20260827\candidate-model-rerun `
  --out .\tools\selfie-stick\out\era17\roof-semantics-20260827\holdout-rerun.json

python .\tools\selfie-stick\score_roof_holdout.py `
  --holdout .\tools\selfie-stick\out\era17\roof-semantics-20260827\holdout-rerun.json `
  --judgments .\tools\selfie-stick\out\era17\roof-semantics-20260827\holdout-judgments.json `
  --out .\tools\selfie-stick\out\era17\roof-semantics-20260827\roof-model-validation-rerun.json
```

The forty ids come from the frozen candidate manifest; they are not re-derived by
rerunning `scan_clusters.py`.

## Edge and next bounded question

The edge is now concrete: slope-normal modes can call a long gable a hip when
outer-corner panels close the assembly. Cluster 2094 demonstrates it clearly.
The next single-variable diagnostic lap should compare roof-boundary or wall-support
evidence at the gable termination in cluster 2094 against the supported hip in
cluster 2072. If that signal survives, freeze a new independent holdout before
changing the promotion verdict.

Improving capture observability is a separate later lap. Mixing new camera
selection with a topology change would make it impossible to tell which variable
changed the score.

## Uncertainty retained

- Only four shaped-on calibration clusters and ten holdout clusters were sampled.
- Three of ten frozen examples could not be adjudicated from their selected views.
- No independent ridge bearing was measurable, so ridge accuracy remains UNVERIFIED.
- Plane area comes from prefab snap planes and oriented-box extents, not render
  meshes.
- Connectivity uses 5 cm snap coincidence plus a bounded 20 cm singleton rule.
- The direct geometry artifact includes rotations and broader architectural
  categories, but this lap modeled only exact frozen BUILDING membership.
- The exporter checkout was dirty; artifact hashes, not its base revision alone,
  bind the evidence.
- No roof semantic reached planner or capture execution.
