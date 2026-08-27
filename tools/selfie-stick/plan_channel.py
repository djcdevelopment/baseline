#!/usr/bin/env python3
"""Shoot down the channel, with the moon off to one side.

plan_nightsky.py aims the camera AT the moon, which composes the moon as the
subject. Derek's rule, and the reason this file exists:

    "aiming at the moon itself is boring, using the lighting of a full moon at
     that angle... is creative"

    "see 'down' a channel to get the depth of vision from ground construction out
     into the sea, and it need not be a direct moon shot, but just solid stars
     caught in the top 1/3 to 1/6 of the shot"

So three things change, and they are the whole file:

1. THE BEARING IS CHOSEN BY THE CHANNEL, not by the body. scan_channels.py
   measures, per bearing, how high the canopy stands above the lens and how far
   the ray runs before it reaches open water. The best bearing is the one you can
   see furthest down.

2. THE MOON IS A LIGHT, and it is required to be OFF-AXIS. A bearing within
   --min-moon-offset of the moon is refused outright, however good its channel:
   that is the shot the night lane was already taking. The preferred band is
   side-on, where the light rakes across the near roofline and the water instead
   of flattening them.

   This also decouples the shot from the moon's phase and from cloud, which is
   the practical win. A direct moon shot needs a disc; a raked one needs only
   that the moon is up.

3. THE PITCH IS SET BY THE SKY BAND, not by the body's altitude. The horizon --
   canopy where trees stand above the lens, sea level where they do not -- is
   placed so that clear sky occupies the top --sky-band of the frame. At the
   default 0.25 that puts the skyline a quarter of the way down from the top and
   leaves three quarters for construction, terrain and water.

The geometry, with the frame's vertical half-angle as fov_v/2 and a point at
angle D above the optical axis landing at fractional height v = tan D / tan(fov_v/2)
where v runs -1 at the bottom edge to +1 at the top:

    skyline sits at            v_sky = 1 - 2 * sky_band
    optical axis elevation     e = theta_skyline - atan(v_sky * tan(fov_v/2))
    pitch                      = -e            (Unity: positive pitch looks down)

For a sea horizon seen from a high roof theta_skyline is slightly NEGATIVE -- the
water is below you -- so e comes out negative and the camera tilts down, which is
correct and is the opposite of what the night planner does.

The aim point handed to the mod is 25 m up the sight line, for the same three
reasons plan_nightsky documents: PiecesNear(aim, 60) must not read zero, IsOccluded
must not fire recovery, and LookAngles must reproduce the planned yaw and pitch if
it does.

Usage:
  python plan_channel.py --channels out/era17/channels.json \
      --clusters out/era17/clusters.json --names out/era17/cluster-names.json \
      --out out/era17/channel-1.json
"""
import argparse
import json
import math
import os
import sys

FOV_V = 65.0
FOV_H = 97.11
EYE_STANDING_M = 1.65
AIM_DISTANCE_M = 25.0
K = math.sin(math.radians(45.0))


def body_direction(t):
    """(azimuth, altitude) of the lit body at time-of-day t, in degrees.

    Same closed form as plan_nightsky, and it is not a guess: measured against the
    rendered disc on 2026-08-27 the azimuth residual is mean -0.01 deg (|max| 1.7)
    and the altitude mean -0.62 (|max| 2.3), over eleven discs across two runs.
    """
    rise = 0.75 if (t >= 0.75 or t < 0.25) else 0.25
    theta = math.radians(180.0 * (((t - rise) / 0.5) % 1.0))
    alt = math.degrees(math.asin(K * math.sin(theta)))
    az = math.degrees(math.atan2(math.cos(theta), -K * math.sin(theta))) % 360.0
    return az, alt


def angular_diff(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--channels", default=os.path.join(here, "out", "era17", "channels.json"))
    p.add_argument("--clusters", default=os.path.join(here, "out", "era17", "clusters.json"))
    p.add_argument("--names", default=os.path.join(here, "out", "era17", "cluster-names.json"))
    p.add_argument("--out", default=os.path.join(here, "out", "era17", "channel-1.json"))
    p.add_argument("--times", default="0.85,0.95,0.05",
                   help="night times of day; the moon is the lit body from 0.75 to 0.25")
    p.add_argument("--environment", default="Clear")
    p.add_argument("--sky-band", type=float, default=0.25,
                   help="fraction of frame height above the skyline. Derek's range is "
                        "1/6 to 1/3, so 0.17 to 0.33; 0.25 sits in the middle")
    p.add_argument("--min-moon-offset", type=float, default=40.0,
                   help="refuse a bearing closer than this to the moon -- that is the "
                        "direct moon shot this file exists to avoid")
    p.add_argument("--max-moon-offset", type=float, default=140.0,
                   help="beyond this the moon is behind the camera and lights the scene "
                        "flat and frontally, which is as dull as pointing at it")
    p.add_argument("--min-moon-altitude", type=float, default=12.0,
                   help="below this the moon is too low to light anything")
    p.add_argument("--shots", type=int, default=2, help="bearings per build per time")
    p.add_argument("--prefer-sea", action="store_true", default=True,
                   help="rank a bearing that reaches open water above one that does not")
    p.add_argument("--no-prefer-sea", dest="prefer_sea", action="store_false")
    p.add_argument("--min-run-m", type=float, default=250.0,
                   help="a bearing whose view closes sooner than this is not a channel")
    p.add_argument("--top", type=int, default=0)
    p.add_argument("--cluster-ids", default="")
    p.add_argument("--tree-height", type=float, default=20.0,
                   help="must match what scan_channels.py used")
    return p.parse_args()


def channel_score(bear, prefer_sea, min_run_m):
    """How much frame this bearing is worth. Higher is better; None refuses it."""
    canopy = bear.get("canopy_deg")
    first = bear.get("first_tree_m")
    sea_at = bear.get("sea_at_m")
    sea_run = bear.get("sea_run_m") or 0.0

    # A canopy standing above the lens is a wall, not a view. Two degrees of
    # tolerance: a crown just breaking the lens plane reads as a near layer along
    # the bottom edge, which is what edge_frame rewards, not an obstruction.
    if canopy is not None and canopy > 2.0:
        return None, "canopy %.1f deg above the lens" % canopy

    run = first if first is not None else min_run_m * 4.0
    if run < min_run_m:
        return None, "view closes at %.0f m" % run

    score = min(run, 1200.0) / 1200.0
    if prefer_sea and sea_at is not None:
        # Water is the depth cue the whole composition is built on: ground
        # construction, then terrain, then open water to the horizon.
        score += 1.0 + min(sea_run, 800.0) / 800.0
    return score, None


def main():
    args = parse_args()
    with open(args.channels, encoding="utf-8-sig") as fh:
        chan = json.load(fh)
    names = {}
    if os.path.exists(args.names):
        with open(args.names, encoding="utf-8-sig") as fh:
            names = json.load(fh)

    times = [float(t) for t in args.times.split(",") if t.strip()]
    for t in times:
        if 0.25 <= t < 0.75:
            sys.exit(f"{t} is daylight - the moon is the lit body only from 0.75 to 0.25")

    builds = chan["structures"]
    if args.cluster_ids:
        want = {int(c) for c in args.cluster_ids.split(",") if c.strip()}
        builds = [b for b in builds if b["cluster_id"] in want]
    builds.sort(key=lambda b: -(b.get("lights") or 0))
    if args.top:
        builds = builds[:args.top]

    v_sky = 1.0 - 2.0 * args.sky_band
    tan_half_v = math.tan(math.radians(FOV_V / 2.0))
    print(f"  fov {FOV_V:g} v / {FOV_H:g} h,  sky band {args.sky_band:.2f} "
          f"(skyline at v={v_sky:+.2f})")
    for t in times:
        az, alt = body_direction(t)
        print(f"  t={t:g}: moon azimuth {az:.1f}, altitude {alt:.1f}")

    plan, dropped = [], []
    for b in builds:
        cid = b["cluster_id"]
        label = names.get(str(cid)) or f"cluster {cid}"
        st = b["stance"]
        eye = {"x": st["x"], "y": st["y"] + EYE_STANDING_M, "z": st["z"]}

        took_any = False
        for t in times:
            m_az, m_alt = body_direction(t)
            if m_alt < args.min_moon_altitude:
                dropped.append((cid, f"t={t:g}: moon only {m_alt:.1f} deg up"))
                continue

            ranked = []
            for key, bear in b["bearings"].items():
                bng = float(key)
                off = angular_diff(bng, m_az)
                if off < args.min_moon_offset:
                    continue            # this is the direct moon shot
                if off > args.max_moon_offset:
                    continue            # moon behind the camera, flat frontal light
                sc, _why = channel_score(bear, args.prefer_sea, args.min_run_m)
                if sc is None:
                    continue
                # Prefer the middle of the raking band: fully side-on light shows
                # form, which is the entire point of using the moon as a lamp.
                rake = 1.0 - abs(off - 90.0) / 90.0
                ranked.append((sc + 0.6 * rake, bng, bear, off))
            ranked.sort(key=lambda r: -r[0])

            picked, used = [], []
            for sc, bng, bear, off in ranked:
                # Two bearings 15 deg apart are the same photograph.
                if any(angular_diff(bng, u) < 45.0 for u in used):
                    continue
                picked.append((sc, bng, bear, off))
                used.append(bng)
                if len(picked) >= args.shots:
                    break

            if not picked:
                dropped.append((cid, f"t={t:g}: no bearing both open and off-axis"))
                continue

            for i, (sc, bng, bear, off) in enumerate(picked, start=1):
                canopy = bear.get("canopy_deg")
                # The skyline is the canopy when it stands above the lens, and the
                # water/ground line when it does not. Both are angles at the lens.
                theta = canopy if (canopy is not None and canopy > 0) else 0.0
                if bear.get("sea_at_m"):
                    theta = min(theta, -math.degrees(math.atan2(
                        max(eye["y"] - 30.0, 1.0), bear["sea_at_m"])))
                e = theta - math.degrees(math.atan(v_sky * tan_half_v))
                pitch = -e

                br = math.radians(bng)
                er = math.radians(e)
                aim = {
                    "x": round(eye["x"] + math.sin(br) * math.cos(er) * AIM_DISTANCE_M, 1),
                    "y": round(eye["y"] + math.sin(er) * AIM_DISTANCE_M, 1),
                    "z": round(eye["z"] + math.cos(br) * math.cos(er) * AIM_DISTANCE_M, 1),
                }
                # The variant carries bearing AND time: the index supersedes on
                # (cluster, variant, environment, time_of_day), so two frames of
                # the same name retire each other instead of joining.
                variant = f"chan{i}t{str(t).replace('.', '')}y{int(bng)}"
                plan.append({
                    "cluster_id": cid, "label": label, "shot": variant,
                    "camera": {"x": st["x"], "y": st["y"], "z": st["z"]},
                    "lens": eye, "aim": aim,
                    "yaw_deg": round(bng, 1), "pitch_deg": round(pitch, 2),
                    "elevation_deg": round(e, 2),
                    "environment": args.environment, "time_of_day": t,
                    "moon_azimuth_deg": round(m_az, 2),
                    "moon_altitude_deg": round(m_alt, 2),
                    "moon_offset_deg": round(off, 1),
                    "skyline_deg": round(theta, 2),
                    "sky_band": args.sky_band,
                    "canopy_deg": canopy,
                    "first_tree_m": bear.get("first_tree_m"),
                    "sea_at_m": bear.get("sea_at_m"),
                    "sea_run_m": bear.get("sea_run_m"),
                    "channel_score": round(sc, 3),
                    "mode": "rooftop",
                })
                took_any = True
        if not took_any:
            dropped.append((cid, "no time of day produced a shot"))

    if dropped:
        print(f"\n  {len(dropped)} refusal(s):")
        for cid, why in dropped[:14]:
            print(f"    cluster {cid:>5}: {why}")
        if len(dropped) > 14:
            print(f"    ... and {len(dropped) - 14} more")

    tsv = os.path.splitext(args.out)[0] + ".tsv"
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(tsv, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# cluster_id\tshot\tcam_x\tcam_y\tcam_z\tyaw\tpitch\tenv\ttime\t"
                 "aim_x\taim_y\taim_z\tlabel\tmode\n")
        for s in plan:
            fh.write(f"{s['cluster_id']}\t{s['shot']}\t"
                     f"{s['camera']['x']}\t{s['camera']['y']}\t{s['camera']['z']}\t"
                     f"{s['yaw_deg']}\t{s['pitch_deg']}\t{s['environment']}\t"
                     f"{s['time_of_day']}\t{s['aim']['x']}\t{s['aim']['y']}\t{s['aim']['z']}\t"
                     f"{s['label'].replace(chr(9), ' ')}\t{s['mode']}\n")

    doc = {
        "generated_from": "plan_channel.py",
        "world": chan.get("world"),
        "structures": len({s["cluster_id"] for s in plan}),
        "shots": len(plan),
        "settings": {
            "fov_v_deg": FOV_V, "fov_h_deg": FOV_H, "h_eye_m": EYE_STANDING_M,
            "sky_band": args.sky_band, "times": times,
            "environment": args.environment,
            "min_moon_offset_deg": args.min_moon_offset,
            "max_moon_offset_deg": args.max_moon_offset,
            "min_run_m": args.min_run_m, "prefer_sea": args.prefer_sea,
            "tree_height_m_ASSUMED": args.tree_height,
            "aim_distance_m": AIM_DISTANCE_M,
        },
        "plan": plan,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    print(f"\n  {doc['structures']} structure(s) -> {len(plan)} shots")
    print(f"  {args.out}")
    print(f"  {tsv}  (this is the one the mod reads)")


if __name__ == "__main__":
    main()
