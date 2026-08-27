#!/usr/bin/env python3
"""Stand on the high ground of a build and look out at the night sky.

Every other planner here puts the camera outside a build and aims down at it.
plan_shots.py says so itself: "the camera is always above the aim point here, so
a correct pitch is always positive". That is why the night A/B failed -- the 14
exterior frames at time 0.90 median 4.79 and are murk. It was not the light. It
was a camera pointed at the ground at midnight.

This one composes in three bands:

    sky      the moon and the star field, above the axis
    middle   treetops and ridges receding into haze, below the horizon line
    near     the roof you are standing on, along the bottom edge

The middle band is the point. Depth in a flat image comes from tonal variance
across overlapping layers, and moonlight arriving from a low angle back-lights
ridges into separate bands. depth_layers.py measures exactly that -- layers,
far_mass, depth_span, edge_frame -- and it is nearly independent of the aesthetic
head (r = -0.117), which reads global tone and will mark every frame here down
for being dark.

WHERE THE SKY IS
----------------
Measured, not assumed. comfyproof_sky walked EnvMan's directional light through
41 times of day (tools/selfie-stick/Invoke-SkyDump.ps1). The light follows one
arc, and colour and intensity say which body is on it: warm (1.00, 0.87, 0.64)
at intensity 1.50 is the sun, from t=0.25 to t=0.75; cool (0.41, 0.49, 0.68) at
1.20 is the moon, from t=0.75 through midnight to t=0.25. Both rise due east at
0 degrees, peak due south at 45, and set due west.

That arc has a closed form, and it reproduces all 39 lit samples to 0.001 deg:

    theta(t) = 180 * frac((t - rise) / 0.5)        rise = 0.25 sun, 0.75 moon
    alt(t)   = asin(K * sin theta)                 K = sin 45 = 0.70711
    az(t)    = atan2(cos theta, -K * sin theta)

An independent check: it puts the sun at azimuth 239.7 at t=0.64, and the sky-
strip luminance regression over seven capture runs pooled to 235 +/- 25.

WHAT IT CANNOT TELL YOU
-----------------------
Where the rendered disc is, and how big. EnvMan has no moon object and no phase
field -- the dump enumerated every field and method naming a sun, a moon or a
phase and found only m_sunHorizonTransition{H,L}, m_sunFogColor and
GetSunDirection. The disc is drawn by the sky material, and 61 renderers in the
sky hierarchy are clouds, water and fog. So phase is whatever the world's day
gives us, and the disc's angular radius is unknown until a frame is measured:
--rho defaults to 0, which aims at the body's centre. sky_check.py reports the
residual between where this planner put the body and where it actually landed.

WHEN YOU CAN SHOOT
------------------
Two constraints close from opposite sides, and between them they pick the hour.

The camera only looks UP while the body is higher than the sky-fraction offset:
at the default 0.45 that is 16 degrees, so t must be past about 0.81 and before
about 0.19. And the roofline only survives in the bottom of the frame while

    elevation + atan(h_eye / R) <= fov_v / 2

so a wide terrace can take a high moon and a small turret top cannot: at 20 m of
roof the moon can be 43 degrees up, at 8 m only 37, at 4 m it has to be under 25.
A build that fails is a scheduling problem rather than a dead end -- the same
roof works an hour earlier. Structures with no workable bearing are reported and
dropped, because the alternative is a frame with no near layer in it, and that is
the sky-platform shot: 4.69 against a gallery median of 5.47.

Usage:
  python plan_nightsky.py --rooftops out/era17/rooftops.json
                          --clusters out/era17/clusters.json
                          --out out/era17/nightsky.json
"""
import argparse
import json
import math
import os
import sys

# The mod parses this TSV with a regex and no JSON parser, so a row it cannot
# read is a shot that silently never happens. plan_interiors.py already re-reads
# the file exactly the way LoadShotPlan does; reuse it rather than write a
# second, subtly different copy.
from plan_interiors import validate_tsv

# Vertical FOV, confirmed on every capture receipt ("fov": 65). The window is
# 16:9, so the horizontal half-angle is the wider constraint.
FOV_V_DEG = 65.0
ASPECT = 16.0 / 9.0
FOV_H_DEG = 2.0 * math.degrees(math.atan(
    math.tan(math.radians(FOV_V_DEG / 2.0)) * ASPECT))

# The celestial arc, measured. K is sin(45 deg): both bodies peak at 45 degrees.
ARC_K = math.sin(math.radians(45.0))
SUN_RISE_T = 0.25
MOON_RISE_T = 0.75

# The mod places the PLAYER; the lens ends up above and slightly ahead of that
# point. Measured across the receipts: lens_offset_m 1.72-2.04, almost all of it
# vertical (planned y 60.7 -> lens y 62.353). On a roof that 1.65 m is the whole
# margin, so the stance is planned at the surface and the lens rides up to it.
EYE_STANDING_M = 1.65
EYE_SEATED_M = 1.0

# Where the parapet edge should fall: 0.6 of the way from centre to the bottom
# edge, which is the lower-third line. Expressed as the angle below the optical
# axis, because that is what the geometry produces.
EDGE_BELOW_AXIS_DEG = math.degrees(math.atan(
    0.6 * math.tan(math.radians(FOV_V_DEG / 2.0))))

# Far enough that the sight line is unambiguously sky, near enough that the
# build is still well inside the 60 m sphere the mod counts pieces in -- a zero
# count there means "world never loaded" and the shot is dropped.
AIM_DISTANCE_M = 25.0


def body_direction(t, rise=MOON_RISE_T):
    """(azimuth, altitude) of the sun or the moon at time-of-day t, in degrees."""
    theta = math.radians(180.0 * (((t - rise) / 0.5) % 1.0))
    x, y, z = math.cos(theta), ARC_K * math.sin(theta), -ARC_K * math.sin(theta)
    return math.degrees(math.atan2(x, z)) % 360.0, math.degrees(math.asin(y))


def is_night(t):
    """The moon is the lit body from 0.75 through midnight to 0.25."""
    return t >= MOON_RISE_T or t <= SUN_RISE_T


def frame_offset_deg(fraction, fov_deg):
    """Angle from the optical axis to a point at `fraction` of the half-frame."""
    return math.degrees(math.atan(fraction * math.tan(math.radians(fov_deg / 2.0))))


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rooftops", default=os.path.join(here, "out", "rooftops.json"))
    p.add_argument("--clusters", default=os.path.join(here, "out", "clusters.json"))
    p.add_argument("--names", default=os.path.join(here, "out", "cluster-names.json"))
    p.add_argument("--out", default=os.path.join(here, "out", "nightsky.json"))
    p.add_argument("--top", type=int, default=0,
                   help="only the first N structures in the rooftop scan (0 = all)")
    p.add_argument("--cluster-ids", default="",
                   help="comma-separated cluster ids, ignoring --top")
    p.add_argument("--body-azimuth", type=float, default=None,
                   help="override the bearing to frame, in degrees. The dump "
                        "gives the DIRECTIONAL LIGHT exactly, and the light is "
                        "what back-lights the ridges -- but it is not where the "
                        "rendered disc is. Two frames from different runs at "
                        "t=0.90 put the disc at azimuth 77.0 and 79.6 (2.6 deg "
                        "apart, from camera yaws 30 deg apart, so it is a fixed "
                        "body and not an artifact) while the light sits at 134.2. "
                        "Pass the disc's bearing when the disc is the subject")
    p.add_argument("--body-altitude", type=float, default=None,
                   help="override the altitude to frame. Limb fitting constrains "
                        "this badly -- the same body measured 41.3 and 63.7 in the "
                        "two frames above, because a short arc of a huge circle "
                        "trades centre distance against radius. Left alone, the "
                        "light's altitude is used and the disc rides higher than "
                        "planned; sky_check.py reports by how much")
    p.add_argument("--times", default="0.9",
                   help="comma-separated times of day. Must be night: the moon is "
                        "the lit body from 0.75 through midnight to 0.25")
    p.add_argument("--environment", default="Clear",
                   help="Clear is the only sky with stars and a visible moon")
    p.add_argument("--bearings", type=int, default=2,
                   help="how many directions to look per structure")
    p.add_argument("--repeats", type=int, default=2,
                   help="frames per bearing. Cloud position is not a setting -- "
                        "plan_shots.py measured 14 shots at identical camera and "
                        "light differing by up to 50.8 mean luma from sky drift. "
                        "'When the clouds part' is a re-roll, so take more than one")
    p.add_argument("--sky-fraction", type=float, default=0.45,
                   help="where in the upper half-frame to put the body, 0 = the "
                        "centre line, 1 = the top edge")
    p.add_argument("--rho", type=float, default=0.0,
                   help="angular RADIUS of the moon's disc in degrees, once "
                        "measured. Nonzero frames the lower limb instead of the "
                        "centre, which is what you want if the disc is as large "
                        "as the corpus suggests. 0 aims at the body's centre")
    p.add_argument("--h-eye", type=float, default=EYE_STANDING_M,
                   help=f"lens height above the roof surface (default "
                        f"{EYE_STANDING_M} standing, measured)")
    p.add_argument("--seated", action="store_true",
                   help=f"sit on the parapet instead: h-eye {EYE_SEATED_M}")
    p.add_argument("--min-lights", type=int, default=0,
                   help="skip builds with fewer weighted lights than this")
    p.add_argument("--sky-margin", type=float, default=3.0,
                   help="degrees the optical axis must clear the build's own "
                        "skyline by. The first run shot 16 frames that all came "
                        "back clearance=planned and occluded=false and not one "
                        "had sky in it: the mod raycasts against terrain, "
                        "static_solid and Default, and player pieces are on the "
                        "piece layer, so for a camera standing inside its own "
                        "build that check is blind. Guard the plan, not the pixels")
    p.add_argument("--min-above-base", type=float, default=4.0,
                   help="metres the stance must sit above the build's foundations, "
                        "so a one-storey shed is not called high ground")
    return p.parse_args()


def ideal_reach(elevation, h_eye):
    """How much roof should lie ahead so the parapet lands on the lower third.

    The edge sits atan(h_eye / R) below horizontal and the axis sits `elevation`
    above it, so the edge appears (elevation + that) below the axis. Solving for
    the R that makes it EDGE_BELOW_AXIS_DEG gives the distance to stand back.
    Above that elevation there is no such R -- the axis alone already carries the
    edge past the lower third -- and the answer is as much roof as you can get.
    """
    slack = EDGE_BELOW_AXIS_DEG - elevation
    if slack <= 0.5:
        return 1e6
    return h_eye / math.tan(math.radians(slack))


def bearing_gap(a, b):
    """Smallest angle between two bearings, 0..180."""
    return abs((a - b + 180.0) % 360.0 - 180.0)


def reach_at(reaches, bearing):
    """The rooftop scan measures reach every 30 degrees; take the nearest."""
    best, best_gap = None, 1e9
    for key, value in reaches.items():
        gap = bearing_gap(float(key), bearing)
        if gap < best_gap:
            best, best_gap = value, gap
    return best if best is not None else 4.0


def choose_bearings(plats, az_body, elevation, h_eye, want, sky_margin):
    """Pick the directions to look.

    Two things decide it, and the giant disc is what lets them coexist. The body
    subtends az_body +/- rho, and the frame is 97 degrees wide, so a great deal
    of the compass shows some of it -- which means the bearing can be chosen for
    the VIEW and the moon comes along anyway. Aiming within about 45 degrees of
    the body additionally back-lights the ridges, which is what turns terrain
    into separate tonal bands rather than one flat mass.

    The view test is the parapet: the roof edge sits atan(h_eye / R) below
    horizontal, so it lands (elevation + that) below the optical axis. Best is
    the bearing that puts it nearest the lower-third line; anything that pushes
    it past the bottom edge is rejected, because then the frame has no near layer
    at all and this becomes the sky-platform shot that medians 4.69.
    """
    half_v = FOV_V_DEG / 2.0
    scored = []
    for index, plat in enumerate(plats):
      reaches = plat["reach_m"]
      skylines = plat.get("skyline_deg") or {}
      for key in reaches:
        bearing = float(key)
        # Keep the body's centre inside the frame width, with margin.
        if bearing_gap(bearing, az_body) > FOV_H_DEG / 2.0 - 8.0:
            continue
        # The build's own masonry, measured from the world's own positions.
        # Nothing else in the chain can see it.
        sky = skylines.get(key, 0.0)
        if elevation < sky + sky_margin:
            continue
        reach = reach_at(reaches, bearing)
        # Step back from the parapet, which is what a photographer does. The
        # stance is the HIGHEST flat block, and on a big build that is often a
        # small turret whose edge is 4 m away -- close enough that the roofline
        # lands 31 degrees below the axis, a sliver at the very bottom of the
        # frame instead of a near layer. Backing up along the reverse bearing
        # buys forward roof one metre at a time, and the reverse reach says how
        # much there is to back onto.
        want = ideal_reach(elevation, h_eye)
        room = max(0.0, reach_at(reaches, (bearing + 180.0) % 360.0) - 2.0)
        step_back = max(0.0, min(want - reach, room)) if want > reach else 0.0
        reach += step_back
        below_axis = elevation + math.degrees(math.atan(h_eye / max(reach, 0.5)))
        if below_axis > half_v:
            continue                      # the roofline falls out of the bottom
        scored.append((abs(below_axis - EDGE_BELOW_AXIS_DEG), index, bearing,
                       reach, below_axis, step_back, sky))
    scored.sort()
    picked = []
    for _penalty, index, bearing, reach, below_axis, step_back, sky in scored:
        # Two shots down the same wall are one shot. Keep them apart.
        if any(bearing_gap(bearing, p["bearing"]) < 45.0 for p in picked):
            continue
        picked.append({"bearing": bearing, "reach_m": round(reach, 1),
                       "step_back_m": round(step_back, 1),
                       "platform": index, "skyline_deg": sky,
                       "stance": plats[index]["stance"],
                       "edge_below_axis_deg": round(below_axis, 2)})
        if len(picked) >= want:
            break
    return picked


def main():
    args = parse_args()
    if not os.path.exists(args.rooftops):
        sys.exit(f"no rooftops at {args.rooftops} - run scan_rooftops.py first")
    with open(args.rooftops, encoding="utf-8") as fh:
        roof_doc = json.load(fh)
    with open(args.clusters, encoding="utf-8") as fh:
        clusters = {c["cluster_id"]: c for c in json.load(fh)["clusters"]}
    names = {}
    if os.path.exists(args.names):
        with open(args.names, encoding="utf-8") as fh:
            names = json.load(fh)

    times = [float(t) for t in args.times.split(",") if t.strip()]
    day = [t for t in times if not is_night(t)]
    if day:
        sys.exit(f"{day} is daylight - the moon is the lit body only from 0.75 "
                 f"through midnight to 0.25, and this planner has nothing to "
                 f"point at in the day")

    h_eye = EYE_SEATED_M if args.seated else args.h_eye
    structures = roof_doc["structures"]
    want_ids = {int(i) for i in args.cluster_ids.split(",") if i.strip()}
    if want_ids:
        structures = [s for s in structures if s["cluster_id"] in want_ids]
    else:
        structures = [s for s in structures
                      if s["lights"] >= args.min_lights
                      and s["above_base_m"] >= args.min_above_base]
        if args.top:
            structures = structures[: args.top]

    print(f"  fov {FOV_V_DEG:g} v / {FOV_H_DEG:.1f} h,  eye {h_eye:g} m above the roof")
    for t in times:
        az, alt = body_direction(t)
        print(f"  t={t:g}: moonlight from azimuth {az:.1f}, altitude {alt:.1f}")
    if args.body_azimuth is not None or args.body_altitude is not None:
        print(f"  framing on azimuth "
              f"{args.body_azimuth if args.body_azimuth is not None else 'light'}, "
              f"altitude "
              f"{args.body_altitude if args.body_altitude is not None else 'light'} "
              f"(the disc, not the light)")

    shots, dropped = [], []
    for s in structures:
        cid = s["cluster_id"]
        cluster = clusters.get(cid)
        if cluster is None:
            dropped.append((cid, "not in this era's clusters.json"))
            continue
        label = names.get(str(cid)) or f"cluster {cid}"
        # Several candidate stances per build, because the highest flat block is
        # not reliably the one with sky over it. A rooftops.json without them
        # degrades to the single stance and no skyline guard, which is the old
        # behaviour stated rather than hidden.
        plats = s.get("platforms_detail") or [{
            "stance": s["stance"], "reach_m": s["reach_m"], "skyline_deg": {}}]

        made = 0
        for t in times:
            az_body, alt_body = body_direction(t)
            if args.body_azimuth is not None:
                az_body = args.body_azimuth % 360.0
            if args.body_altitude is not None:
                alt_body = args.body_altitude
            # Frame the lower limb once rho is known; the centre until then.
            alt_target = alt_body - args.rho
            elevation = alt_target - frame_offset_deg(args.sky_fraction, FOV_V_DEG)
            picked = choose_bearings(plats, az_body, elevation, h_eye,
                                     args.bearings, args.sky_margin)
            if not picked:
                continue
            for i, pick in enumerate(picked, start=1):
                for r in range(1, args.repeats + 1):
                    # Repeats must be distinct VARIANTS, not repeated rows: the
                    # index supersedes on (cluster, variant, environment, time),
                    # so a second frame under the same name retires the first
                    # instead of joining it. That is the bug that quietly
                    # replaced 150 golden frames on 2026-08-24.
                    variant = f"moon{i}" if r == 1 else f"moon{i}_r{r}"
                    if len(times) > 1:
                        variant = f"moon{i}t{str(t).replace('.', '')}" \
                                  + ("" if r == 1 else f"_r{r}")
                    yaw = pick["bearing"]
                    pitch = -elevation
                    # The step-back is a real move, not just a number in the
                    # receipt: stand back along the reverse bearing so there is
                    # roof between the lens and the drop.
                    back = pick["step_back_m"]
                    ar_back = math.radians(yaw)
                    stance = pick["stance"]
                    stand = {"x": round(stance["x"] - back * math.sin(ar_back), 1),
                             "y": stance["y"],
                             "z": round(stance["z"] - back * math.cos(ar_back), 1)}
                    eye = {"x": stand["x"], "y": round(stand["y"] + h_eye, 2),
                           "z": stand["z"]}
                    # Aim along the optical axis, NOT at the build. The mod uses
                    # `aim` for three gates and none of them is framing: it counts
                    # pieces near it, raycasts to it, and recomputes yaw/pitch
                    # from it if recovery fires. A point 25 m up the sight line
                    # keeps the build inside the piece sphere, puts the raycast
                    # into open sky so FindClearView never teleports the camera
                    # off the roof, and reproduces this exact aim if it ever does.
                    ar = math.radians(yaw)
                    er = math.radians(elevation)
                    aim = {
                        "x": round(eye["x"] + AIM_DISTANCE_M * math.sin(ar) * math.cos(er), 1),
                        "y": round(eye["y"] + AIM_DISTANCE_M * math.sin(er), 1),
                        "z": round(eye["z"] + AIM_DISTANCE_M * math.cos(ar) * math.cos(er), 1),
                    }
                    shots.append({
                        "cluster_id": cid, "label": label, "shot": variant,
                        "camera": stand, "lens": eye, "aim": aim,
                        "yaw_deg": round(yaw, 2), "pitch_deg": round(pitch, 2),
                        "elevation_deg": round(elevation, 2),
                        "environment": args.environment, "time_of_day": t,
                        "moon_azimuth_deg": round(az_body, 2),
                        "moon_altitude_deg": round(alt_body, 2),
                        "reach_m": pick["reach_m"],
                        "step_back_m": pick["step_back_m"],
                        "platform": pick["platform"],
                        "skyline_deg": pick["skyline_deg"],
                        "edge_below_axis_deg": pick["edge_below_axis_deg"],
                        "lights": s["lights"], "above_base_m": s["above_base_m"],
                        "region": s.get("region", cluster.get("region")),
                        "mode": "rooftop",
                    })
                    made += 1
        if not made:
            dropped.append((cid, "no stance has open sky toward the moon with "
                                 "the roofline still in frame"))

    if dropped:
        print()
        print(f"  {len(dropped)} structure(s) dropped:")
        for cid, why in dropped[:10]:
            print(f"    cluster {cid}: {why}")

    out = {
        "generated_from": "plan_nightsky.py",
        "world": roof_doc.get("world"),
        "structures": len(structures) - len(dropped),
        "shots": len(shots),
        "settings": {
            "fov_v_deg": FOV_V_DEG, "fov_h_deg": round(FOV_H_DEG, 2),
            "h_eye_m": h_eye, "sky_fraction": args.sky_fraction, "rho_deg": args.rho,
            "times": times, "environment": args.environment,
            "bearings": args.bearings, "repeats": args.repeats,
            "sky_margin_deg": args.sky_margin,
            "aim_distance_m": AIM_DISTANCE_M,
            "edge_below_axis_deg": round(EDGE_BELOW_AXIS_DEG, 2),
        },
        "plan": shots,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, args.out)

    # Same 14-column contract plan_interiors.py writes, mode last. The mod has no
    # JSON parser -- it scrapes with a regex -- so one flat line per shot.
    tsv = os.path.splitext(args.out)[0] + ".tsv"
    with open(tsv + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# cluster_id\tshot\tcam_x\tcam_y\tcam_z\tyaw\tpitch\tenv\ttime\t"
                 "aim_x\taim_y\taim_z\tlabel\tmode\n")
        for s in shots:
            c, a = s["camera"], s["aim"]
            fh.write(f"{s['cluster_id']}\t{s['shot']}\t{c['x']}\t{c['y']}\t{c['z']}\t"
                     f"{s['yaw_deg']}\t{s['pitch_deg']}\t{s['environment']}\t"
                     f"{s['time_of_day']}\t{a['x']}\t{a['y']}\t{a['z']}\t"
                     f"{s['label'].replace(chr(9), ' ')}\t{s['mode']}\n")
    os.replace(tsv + ".tmp", tsv)

    ok, bad = validate_tsv(tsv, mode="rooftop")
    print()
    print(f"  TSV validation: {ok} row(s) parse the way LoadShotPlan parses, "
          f"{bad} would drop")
    if bad:
        sys.exit("some rows would be dropped by the mod's parser - fix before arming")
    print(f"  {out['structures']} structure(s) -> {len(shots)} shots")
    print(f"  {args.out}")
    print(f"  {tsv}  (this is the one the mod reads)")


if __name__ == "__main__":
    main()
