#!/usr/bin/env python3
"""Place cameras around each structure from its geometry, so nobody has to fly.

A human flying the camera pays most of the cost in *moving*, so the sensible trade
was 23 frames of one viewpoint varying only the light. Automated, that is backwards:
the camera can be anywhere instantly, and six photographs from six angles say far
more about a building than twenty-three of one wall.

So: six shots per structure — four orbit angles plus two light variants — placed
from the bounding box scan_clusters.py already computes.

No terrain data is needed. Valheim generates terrain from the world seed and the
save holds only objects, so no offline heightmap exists. But a cluster's min_y is
effectively ground at that build, because its lowest foundation piece rests on it.
Only the in-game runner needs a real ground query, to clamp a camera that would
otherwise land inside a hillside.

Usage:
  python plan_shots.py [--clusters out/clusters.json] [--out out/shotplan.json]
                       [--top N] [--region in-world] [--elevation 40]
                       [--max-distance 200]
"""
import argparse
import json
import math
import os
import sys

# Valheim's vertical field of view. Framing math is in vertical FOV because the
# window is 16:9 and height is the binding constraint for a tall build.
FOV_V_DEG = 65.0

# Measured golden hours. The two ramps either side of midday move 3-4x faster than
# the plateau, and every frame outside 0.29..0.77 came back too dark to use.
GOLDEN_PM = 0.70
GOLDEN_AM = 0.30
WEATHER_ALT = ("Misty", 0.66)


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--clusters", default=os.path.join(here, "out", "clusters.json"))
    p.add_argument("--names", default=os.path.join(here, "out", "cluster-names.json"))
    p.add_argument("--out", default=os.path.join(here, "out", "shotplan.json"))
    p.add_argument("--region", default="in-world", choices=["all", "in-world", "outland"])
    p.add_argument("--top", type=int, default=0, help="only the top N by score")
    p.add_argument("--elevation", type=float, default=40.0,
                   help="camera elevation above the horizontal, degrees (default 40)")
    p.add_argument("--margin", type=float, default=1.15,
                   help="frame headroom so landscape is in shot as well as building")
    p.add_argument("--max-distance", type=float, default=120.0,
                   help="haze cap. Beyond this the frame fills with atmosphere and the "
                        "build reads as a flat silhouette; better to shoot part of a big "
                        "build up close than all of it through 400 m of fog")
    p.add_argument("--min-clearance", type=float, default=3.0,
                   help="metres the camera must stay above the lowest foundation piece")
    return p.parse_args()


def orbit_azimuths(size_x, size_z):
    """Four compass bearings, offset 45 deg from the structure's long axis.

    Dead-on the narrow face of a long building is the least informative angle there
    is — you see a gable and nothing else. Offsetting by 45 puts every shot on a
    corner, showing a long face and a short one together.
    """
    long_axis_is_x = size_x >= size_z
    base = 0.0 if long_axis_is_x else 90.0
    return [(base + 45.0 + i * 90.0) % 360.0 for i in range(4)], long_axis_is_x


def elevation_for(cluster, default_deg):
    """A tower and a plaza want opposite camera heights.

    Shooting a 100 m spire from 40 deg up gives you a roof. Shooting a flat sprawling
    settlement from 15 deg gives you a fence. So tilt down on flat things and level
    off on tall ones, from the height-to-width ratio.
    """
    width = max(cluster["size_x"], cluster["size_z"], 1.0)
    ratio = cluster["size_y"] / width
    return max(18.0, min(default_deg, default_deg - 60.0 * ratio))


def camera_for(cluster, azimuth_deg, elevation_deg, margin, max_distance, clearance):
    """Where to stand, and where to look, to frame this structure from one bearing."""
    cx, cz = cluster["center_x"], cluster["center_z"]
    # Aim at the middle of the box vertically, not the median piece height: a tower's
    # mass sits above its median, and aiming low tips the whole build out of frame.
    cy = (cluster["min_y"] + cluster["max_y"]) / 2.0

    # Frame on the compact extent, not the bounding diagonal. A cluster's diagonal is
    # inflated by sprawl -- outbuildings, walls, a dock -- so framing on it pushes the
    # camera far enough back that the thing people came to see is a smudge in the middle
    # of a hazy frame. Measured on Dragon's Den: diagonal 252 m wants the camera 267 m
    # out, while its compact extent of 150 m wants 136 m. The second is the photograph.
    subject = max(cluster["size_y"],
                  min(cluster["size_x"], cluster["size_z"]),
                  8.0)
    ideal = (subject / 2.0) / math.tan(math.radians(FOV_V_DEG / 2.0)) * margin
    distance = min(ideal, max_distance)
    fits = ideal <= max_distance

    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    horiz = distance * math.cos(el)
    x = cx + horiz * math.sin(az)
    z = cz + horiz * math.cos(az)
    y = cy + distance * math.sin(el)
    y = max(y, cluster["min_y"] + clearance)

    # Look back at the aim point. Unity is Y-up, Z-forward, and its x-euler is
    # positive looking DOWN — so pitch is the negated arcsine of the unit
    # direction's y, not its arctangent. The camera is always above the aim point
    # here, so a correct pitch is always positive.
    dx, dy, dz = cx - x, cy - y, cz - z
    n = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
    yaw = math.degrees(math.atan2(dx, dz)) % 360.0
    pitch = math.degrees(-math.asin(max(-1.0, min(1.0, dy / n))))

    return {
        "azimuth_deg": round(azimuth_deg, 1),
        "camera": {"x": round(x, 1), "y": round(y, 1), "z": round(z, 1)},
        "aim": {"x": round(cx, 1), "y": round(cy, 1), "z": round(cz, 1)},
        "yaw_deg": round(yaw, 2),
        "pitch_deg": round(pitch, 2),       # Unity convention: positive looks down
        "distance_m": round(distance, 1),
        "elevation_deg": round(elevation_deg, 1),
        "frames_whole_build": fits,
    }


def main():
    args = parse_args()
    if not os.path.exists(args.clusters):
        sys.exit(f"no clusters at {args.clusters} — run scan_clusters.py first")
    with open(args.clusters, encoding="utf-8") as fh:
        doc = json.load(fh)
    names = {}
    if os.path.exists(args.names):
        with open(args.names, encoding="utf-8") as fh:
            names = json.load(fh)

    clusters = [c for c in doc["clusters"]
                if args.region == "all" or c["region"] == args.region]
    clusters.sort(key=lambda c: -c["score"])
    if args.top:
        clusters = clusters[: args.top]

    shots, clipped = [], 0
    for c in clusters:
        azimuths, long_x = orbit_azimuths(c["size_x"], c["size_z"])
        elev = elevation_for(c, args.elevation)
        cams = [camera_for(c, a, elev, args.margin,
                           args.max_distance, args.min_clearance) for a in azimuths]
        if not cams[0]["frames_whole_build"]:
            clipped += 1

        # The broadest silhouette: looking along the short axis shows the long face.
        hero = 0 if long_x else 1

        label = names.get(str(c["cluster_id"])) or f"cluster {c['cluster_id']}"
        base = {"cluster_id": c["cluster_id"], "label": label,
                "pieces": c["pieces"], "height_m": c["size_y"], "region": c["region"]}

        for i, cam in enumerate(cams):
            shots.append({**base, "shot": f"orbit{i + 1}", **cam,
                          "environment": "Clear", "time_of_day": GOLDEN_PM})
        shots.append({**base, "shot": "dawn", **cams[hero],
                      "environment": "Clear", "time_of_day": GOLDEN_AM})
        shots.append({**base, "shot": "weather", **cams[hero],
                      "environment": WEATHER_ALT[0], "time_of_day": WEATHER_ALT[1]})

    out = {
        "generated_from": "plan_shots.py",
        "world": doc.get("world"),
        "structures": len(clusters),
        "shots": len(shots),
        "settings": {"elevation_deg": args.elevation, "fov_v_deg": FOV_V_DEG,
                     "margin": args.margin, "max_distance_m": args.max_distance,
                     "min_clearance_m": args.min_clearance},
        "plan": shots,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, args.out)

    # The mod reads this, not the JSON. It has no JSON parser — it scrapes with
    # regex — and one flat line per shot is far harder to misparse than nested
    # objects. Same data, ordered, comment lines start with '#'.
    tsv = os.path.splitext(args.out)[0] + ".tsv"
    with open(tsv + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# cluster_id\tshot\tcam_x\tcam_y\tcam_z\tyaw\tpitch\tenv\ttime\t"
                 "aim_x\taim_y\taim_z\tlabel\n")
        for s in shots:
            c, a = s["camera"], s["aim"]
            fh.write(f"{s['cluster_id']}\t{s['shot']}\t{c['x']}\t{c['y']}\t{c['z']}\t"
                     f"{s['yaw_deg']}\t{s['pitch_deg']}\t{s['environment']}\t"
                     f"{s['time_of_day']}\t{a['x']}\t{a['y']}\t{a['z']}\t"
                     f"{s['label'].replace(chr(9), ' ')}\n")
    os.replace(tsv + ".tmp", tsv)

    print(f"  {len(clusters)} structures -> {len(shots)} shots")
    print(f"  {args.out}")
    print(f"  {tsv}  (this is the one the mod reads)")
    if clipped:
        print(f"  {clipped} structure(s) too big to frame whole inside the "
              f"{args.max_distance:g} m haze cap — shot closer, partial frame")


if __name__ == "__main__":
    main()
