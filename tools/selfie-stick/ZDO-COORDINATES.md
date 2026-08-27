# ZDO coordinates: the durable 3-D point contract

**Status: VERIFIED on ComfyEra17 snapshot 107, 2026-08-27.**

This note owns the coordinate knowledge used by selfie-stick. The short version:

- the world parser already extracts every ZDO's `x`, `y`, and `z`;
- the analytics cache already persists all three without loss;
- `scan_clusters.py` uses all three, but historically discarded its exact
  piece-to-cluster membership when its temporary DuckDB tables closed;
- `export_cluster_points.py` now preserves that membership as Parquet under the
  frozen cluster ids; and
- `plan_shots.py` can use the resulting point cloud to include actual height and
  camera-relative depth in its framing calculation.

`clusters.json` remains the compact gallery/index contract. The point artifact is
its private, regenerable 3-D companion; do not put millions of coordinates into the
JSON or publish them with the gallery.

## Coordinate truth

Valheim uses Y-up world coordinates:

| value | meaning |
|---|---|
| `x` | horizontal world axis |
| `y` | elevation; `max(y) - min(y)` is pivot-to-pivot structure height |
| `z` | the other horizontal world axis |
| `zdo_index` | row identity within one parsed snapshot; not globally stable |

Two distinctions matter:

1. **ZDO position is the prefab pivot, not its mesh boundary.** The point cloud
   captures placement exactly but may miss the outer half-extents of sparse pieces.
   Oriented prefab boxes require the geometry/rotation lane documented in
   `EXPERIMENT.md`.
2. **Photographic depth is not the Z coordinate.** Depth depends on the camera
   bearing and elevation. A point's depth is its projection onto the current
   camera-to-subject axis.

The cache source contract for clustering remains:

```sql
zdo(
  snapshot_id BIGINT,
  zdo_index INTEGER,
  prefab_hash INTEGER,
  prefab_name VARCHAR,
  category VARCHAR,
  x DOUBLE,
  y DOUBLE,
  z DOUBLE,
  creator_id BIGINT
)
```

The general scanner needs only `category, x, y, z, prefab_name, creator_id`.
The coordinate exporter additionally requires `snapshot_id`, `zdo_index`, and
`prefab_hash` so its output is attributable and auditable.

## Data flow

```text
world .db
  -> parser reads x/y/z from each ZDO header
  -> DuckDB zdo table / archived zdo.parquet
  -> scan_clusters.py builds 3-D occupied cells and connected components
  -> clusters.json keeps frozen ids and aggregate bounds
  -> export_cluster_points.py replays and reconciles exact membership
  -> cluster-zdos.parquet keeps one x/y/z row per clustered BUILDING ZDO
  -> plan_shots.py projects those rows into each proposed camera basis
  -> shotplan.json / shotplan.tsv carry the resulting camera placement
```

The direct architectural export (`building-geometry.parquet`) is broader: it
contains BUILDING plus doors, beds, signs, containers, portals, item stands, and
ballistae, with rotation. `cluster-zdos.parquet` is narrower on purpose: it stores
the exact BUILDING rows that contributed to the frozen cluster summaries.

## Artifact contract

`export_cluster_points.py` writes:

```sql
cluster_zdo(
  snapshot_id BIGINT,
  world_id VARCHAR,
  cluster_id BIGINT,
  zdo_index INTEGER,
  prefab_hash INTEGER,
  prefab_name VARCHAR,
  category VARCHAR,       -- BUILDING in this artifact
  x DOUBLE,
  y DOUBLE,
  z DOUBLE,
  creator_id BIGINT
)
```

The default filename is `cluster-zdos.parquet` beside the supplied
`clusters.json`. Since normal cluster outputs live below `out/`, it stays ignored.
It contains real build and builder locations and must remain private like
`clusters.json` itself.

The exporter refuses to write unless:

- `clusters.json` names an exact `snapshot_id`;
- the cache world and frozen world agree;
- every frozen cluster matches one replayed component by its full recorded
  piece count, center, and 3-D bounds;
- every expected piece is present;
- all `x/y/z` values are finite; and
- the completed Parquet passes a read-back count.

Replacement is atomic: `--replace` writes and validates a process-specific temporary
Parquet, then replaces the prior file. A failed reconciliation does not destroy the
last good artifact.

## Frozen cluster ids are not replay ids

Never trust the raw union-find component number from a replay. It is an enumeration
id, and DuckDB does not promise an order for the occupied-cell query. Equal-sized
components can therefore exchange numbers even when their geometry is unchanged.

The Era17 export observed 92 changed enumeration ids on one replay and 186 on an
immediate repeat. All 2,204 components still matched the frozen geometry, and the
reconciled Parquet was byte-identical both times. This is why the exporter matches
geometry first and remaps to the ids already published in `clusters.json`.

Do not regenerate `out/<era>/clusters.json` merely to obtain the point artifact.
Gallery frames, names, scores, features, and receipts already join on those frozen
ids. Export the point companion against them.

## Camera-space framing

For an orbit bearing `a` and elevation `e`, `plan_shots.py` constructs three
orthogonal camera-space axes:

```text
back  = (sin(a) cos(e),  sin(e),  cos(a) cos(e))
right = (cos(a),         0,      -sin(a))
up    = back x right
```

For each ZDO position relative to the aim point:

```text
image_x = dot(relative_position, right)
image_y = dot(relative_position, up)
depth   = dot(relative_position, back)
```

With vertical FOV 65 degrees, 16:9 horizontal FOV approximately 97.1 degrees,
and framing margin `m`, camera distance `D` must satisfy every point:

```text
D >= depth + m * max(
  abs(image_x) / tan(horizontal_fov / 2),
  abs(image_y) / tan(vertical_fov / 2)
)
```

Taking the maximum over all points makes front-to-back depth consume camera distance
instead of treating the subject as a flat rectangle. Each JSON shot records:

- `geometry_source: "zdo_xyz"`;
- `geometry_points`;
- `zdo_height_m`;
- `zdo_projected_width_m`;
- `zdo_projected_height_m`; and
- `zdo_depth_m` for that bearing.

If no point artifact is supplied or found beside `clusters.json`, the planner keeps
the prior `cluster_bbox` calculation. That fallback is deliberate so older eras and
community-produced cluster files remain usable.

## Runbook

From `tools/selfie-stick`:

```powershell
python .\export_cluster_points.py `
  --db <world-cache.duckdb> `
  --clusters .\out\<era>\clusters.json `
  --out <private-scratch>\cluster-zdos.parquet

python .\plan_shots.py `
  --clusters .\out\<era>\clusters.json `
  --cluster-points <private-scratch>\cluster-zdos.parquet `
  --top 40 `
  --out .\out\<era>\shotplan.json
```

The capture wrapper exposes the same input:

```powershell
.\Invoke-OrbitCapture.ps1 `
  -Clusters .\out\<era>\clusters.json `
  -ClusterPoints <private-scratch>\cluster-zdos.parquet `
  -Top 40
```

If `cluster-zdos.parquet` sits beside `clusters.json`, `plan_shots.py` discovers it
automatically. Passing `--cluster-points` is preferable in receipts because it makes
the source explicit.

## Verified Era17 receipt

Source: `ComfyEra17`, snapshot 107.

| check | result |
|---|---:|
| architectural rows in direct geometry export | 4,655,160 |
| direct-export x/y/z mismatches vs cache | 0 |
| clustered BUILDING rows persisted | 3,513,410 |
| frozen clusters represented | 2,204 |
| artifact bytes | 37,258,753 |
| coordinate mismatches vs source cache | 0 |
| identity mismatches vs source cache | 0 |
| missing source rows | 0 |
| per-cluster membership mismatches | 0 |

SHA-256:

```text
3055AEFD0B192ECDD75D734DD2AE92DB0C3EC6238CC728CA2EE29D1EC9580910
```

Vertical-slice result, cluster 1820:

| bearing | bbox distance | point distance | ZDO depth |
|---:|---:|---:|---:|
| 45 degrees | 31.0 m | 35.7 m | 39.9 m |
| 135 degrees | 31.0 m | 35.8 m | 44.0 m |
| 225 degrees | 31.0 m | 46.9 m | 35.2 m |
| 315 degrees | 31.0 m | 34.5 m | 36.3 m |

The structure's ZDO height was 25.0 m. All five generated TSV rows re-parsed under
the camera mod's positional contract.

## Remaining limits

- Point framing knows pivot placement, not full prefab extents. The oriented-box
  geometry lane can eventually provide a mesh-corner framing mode.
- Orbit bearings are still selected from the axis-aligned cluster shape. The
  facade-orientation experiment is recorded separately and has not earned automatic
  planner promotion.
- Offline coordinates do not replace terrain clearance. The runtime may still lift
  and repitch a camera when terrain or vegetation blocks it.
- The current artifact covers clustered BUILDING rows. Interior landmarks and other
  architectural categories remain in `building-geometry.parquet`, not this contract.
- Coordinate artifacts are derived and private. Preserve the command, snapshot id,
  byte count, and hash; do not commit the Parquet itself.
