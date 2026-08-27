#!/usr/bin/env python3
"""One-cluster R&D slice: footprint orientation -> facade-aware camera plan.

This is deliberately not a new general planner.  It holds cluster 1820, light,
framing, and distance fixed and emits three frames:

* the nearest bearing today's axis-aligned bbox planner would choose;
* a camera normal to the footprint's long face;
* the opposite long face.

The resulting A/B/C says whether the one L3 fact that survived contact with
photographs changes the actual picture.  Promote it into plan_shots.py only if
the capture earns that change.
"""
import json
import math
import os

from shapely.geometry import Polygon

from plan_shots import camera_for, elevation_for, orbit_azimuths, validate_tsv
from terrain import TerrainEdits, TerrainGrid


HERE = os.path.dirname(os.path.abspath(__file__))
ERA = os.path.join(HERE, "out", "era17")
ARCH = os.path.join(ERA, "arch")
OUT = os.path.join(ERA, "facade-probe", "facade-1820.json")
CLUSTER_ID = 1820


def angular_distance(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def main():
    with open(os.path.join(ERA, "clusters.json"), encoding="utf-8") as fh:
        clusters_doc = json.load(fh)
    cluster = next(c for c in clusters_doc["clusters"]
                   if c["cluster_id"] == CLUSTER_ID)

    with open(os.path.join(ARCH, f"{CLUSTER_ID}.arch.json"), encoding="utf-8") as fh:
        arch = json.load(fh)
    polygon = Polygon(arch["footprint"]["main_polygon_xz"])
    rectangle = list(polygon.minimum_rotated_rectangle.exterior.coords)[:4]
    edges = []
    for i, start in enumerate(rectangle):
        end = rectangle[(i + 1) % 4]
        dx, dz = end[0] - start[0], end[1] - start[1]
        edges.append({
            "length_m": math.hypot(dx, dz),
            "bearing_deg": math.degrees(math.atan2(dx, dz)) % 180.0,
        })
    major = max(edges, key=lambda edge: edge["length_m"])
    major_bearing = major["bearing_deg"]

    # A long facade faces perpendicular to the footprint's major axis.
    broad = (major_bearing + 90.0) % 360.0
    opposite = (broad + 180.0) % 360.0
    bbox_bearings, _ = orbit_azimuths(cluster["size_x"], cluster["size_z"])
    control = min(bbox_bearings, key=lambda b: angular_distance(b, broad))

    elevation = elevation_for(cluster, 40.0)
    terrain = TerrainGrid.load()
    edits_path = os.path.join(ERA, "terrain-edits.npz")
    if os.path.exists(edits_path):
        terrain.edits = TerrainEdits.load(edits_path)
        terrain.source = "worldgen-cache+edits"
    bearings = [
        ("facade_bbox_control", control, "axis-aligned bbox corner nearest the broad facade"),
        ("facade_broad", broad, "normal to the footprint's long face"),
        ("facade_broad_opposite", opposite, "normal to the opposite long face"),
    ]
    shots = []
    for name, bearing, intent in bearings:
        cam = camera_for(cluster, bearing, elevation, 1.15, 120.0, 3.0, 0.5)
        camera, aim = cam["camera"], cam["aim"]
        ground_y, ground_layer = terrain.ground_y_detail(camera["x"], camera["z"])
        # The existing 1820 control receipt measured a 1.721 m lens offset.  Sample
        # only the first 80% of the ray: the last fifth is supposed to intersect
        # the building/terrain at the aim point and is not a camera obstruction.
        lens_y = camera["y"] + 1.721
        clearances = []
        for i in range(41):
            t = i / 50.0
            x = camera["x"] + (aim["x"] - camera["x"]) * t
            z = camera["z"] + (aim["z"] - camera["z"]) * t
            ray_y = lens_y + (aim["y"] - lens_y) * t
            clearances.append(ray_y - terrain.ground_y_detail(x, z)[0])
        shots.append({
            "cluster_id": CLUSTER_ID,
            "label": f"cluster {CLUSTER_ID} facade probe",
            "pieces": cluster["pieces"],
            "height_m": cluster["size_y"],
            "region": cluster["region"],
            "shot": name,
            "intent": intent,
            **cam,
            "environment": "Clear",
            "time_of_day": 0.64,
            "fires": False,
            "flash": None,
            "terrain_preflight": {
                "source": terrain.source,
                "ground_at_camera_y": round(ground_y, 2),
                "ground_layer": ground_layer,
                "planned_lens_clearance_m": round(lens_y - ground_y, 2),
                "min_los_clearance_first_80pct_m": round(min(clearances), 2),
            },
        })

    out = {
        "generated_from": "probe_facade_orbit.py",
        "world": clusters_doc.get("world", "ComfyEra17"),
        "structures": 1,
        "shots": len(shots),
        "probe": "Does the ZDO-derived dominant footprint orientation improve exterior framing over the axis-aligned bbox orbit?",
        "settings": {
            "cluster_id": CLUSTER_ID,
            "footprint_major_bearing_deg": round(major_bearing, 2),
            "footprint_rectangle_xz": [[round(x, 2), round(z, 2)] for x, z in rectangle],
            "bbox_bearings_deg": bbox_bearings,
            "bbox_control_bearing_deg": round(control, 2),
            "broad_facade_bearing_deg": round(broad, 2),
            "opposite_facade_bearing_deg": round(opposite, 2),
            "elevation_deg": round(elevation, 2),
            "margin": 1.15,
            "max_distance_m": 120.0,
            "aim_height": 0.5,
            "measured_lens_offset_m": 1.721,
            "terrain_source": terrain.source,
        },
        "plan": shots,
        "limitations": [
            "One cluster only; this is a vertical slice, not planner policy.",
            "The minimum rotated rectangle describes the dominant mass and can be biased by attached wings.",
            "Terrain preflight includes the frozen edits layer but not building self-occlusion.",
            "The worldgen height cache is a 12 m grid and remains approximate between edited vertices.",
            "A capture is required; this plan alone cannot say whether the facade-aware frame is better."
        ],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)

    tsv = os.path.splitext(OUT)[0] + ".tsv"
    with open(tsv, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# cluster_id\tshot\tcam_x\tcam_y\tcam_z\tyaw\tpitch\tenv\ttime\t"
                 "aim_x\taim_y\taim_z\tlabel\tmode\tfires\tflash\n")
        for shot in shots:
            camera, aim = shot["camera"], shot["aim"]
            fh.write(
                f"{shot['cluster_id']}\t{shot['shot']}\t"
                f"{camera['x']}\t{camera['y']}\t{camera['z']}\t"
                f"{shot['yaw_deg']}\t{shot['pitch_deg']}\t"
                f"{shot['environment']}\t{shot['time_of_day']}\t"
                f"{aim['x']}\t{aim['y']}\t{aim['z']}\t{shot['label']}\t\t0\t\n")

    ok, bad = validate_tsv(tsv)
    print(json.dumps({
        "plan": OUT,
        "tsv": tsv,
        "major_bearing_deg": round(major_bearing, 2),
        "bearings_deg": {shot["shot"]: shot["azimuth_deg"] for shot in shots},
        "camera_positions": {shot["shot"]: shot["camera"] for shot in shots},
        "tsv_rows_ok": ok,
        "tsv_rows_dropped": bad,
        "limitations": out["limitations"],
    }, indent=1))


if __name__ == "__main__":
    main()
