# selfie-stick

Find every player-built structure in a Valheim world, rank them as camera
subjects, and emit a shot list you can fly.

For the story of how this was built and what the data turned out to be hiding,
read [`TUTORIAL.md`](TUTORIAL.md).

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

Capture runs are queued as plan files, and one script knows what is waiting and how
to start it. Run it with no arguments:

```powershell
cd tools\selfie-stick
.\Start-NextRun.ps1
```

It prints each queued run — how many shots, roughly how long, what it is for and what
would count as it working — tells you whether Valheim is in the way, and gives you the
one line that starts it. `-Run <name>` fires it, then scores the frames, names any new
structures and rebuilds the gallery. It never publishes; that stays a separate act.

The era arguments are the thing worth not typing by hand. Point a run at the wrong
`clusters.json` and every frame joins to another era's cluster ids — the mislabelling
era isolation exists to prevent, and it does not announce itself.

The reasoning behind what is queued, and the measurements behind it, are in
[`docs/internal/RUNBOOK-selfie-stick-era17-series-2026-08-22.md`](../../docs/internal/RUNBOOK-selfie-stick-era17-series-2026-08-22.md).

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

The contract exists so no one is *technically* locked in. ComfyStewardView —
which built the cache used here — is proprietary, all rights reserved. If this
pipeline could only ever run on its output, a community with its own parser
would be stuck. It isn't: point any Valheim world parser at the schema above,
load it into DuckDB or SQLite, and the rest of the chain runs unchanged.

Concretely, to run this against your own server's world:

1. Parse your world `.db` with any tool that can emit ZDO position, category,
   prefab, and creator — write it to the schema above.
2. `python scan_clusters.py --db your-world.duckdb` → your structures, ranked.
3. `python make_waypoints.py --install` → the shot list, in your game.
4. Fly it with the camera mod and shoot.

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
plan_shots.py           clusters.json    ->  shotplan.tsv       6 camera positions each
Invoke-OrbitCapture.ps1 shotplan.tsv     ->  screenshots        unattended, no keyboard
build_valheim_index.py  screenshots      ->  index.json         joined back to structures
name_structures.py      screenshots      ->  cluster-names.json named by a vision model
gallery/index.html      index.json       ->  the gallery        vote / request / claim
```

Two ways to shoot:

**By hand.** Install the camera mod, run `make_waypoints.py --install`, and use the
arrow keys in game — right for the next build, left for the previous, up to capture
the current framing in 23 lights. You choose every composition.

**Unattended.** `Invoke-OrbitCapture.ps1 -Top 40` plans six angles per structure
from its bounding box, launches the game, opens the world, places and aims the
camera, waits for the world to stream in, recovers from a blocked view, shoots,
and quits. Nobody touches the keyboard.

The automated path exists because a human pays for *moving* and a machine does
not. Twenty-three frames of one viewpoint was the right trade for a person; six
viewpoints is the right trade for a machine.

## Known rough edges

- **Prefab names are hashes.** StewardView's cache does not resolve building
  pieces. A one-time in-game dump of `ZNetScene`'s prefab table would fix it
  permanently.
- **Builder IDs are not names.** 660 distinct `creator_id`s attribute cleanly,
  but turning one into a person needs the running viewer's player records.
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
