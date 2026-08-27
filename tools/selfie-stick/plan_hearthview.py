"""Stand in your own warm hall and look out the gate at the moonlit world.

Derek's brief, verbatim: "let you see the long shadows in your own warm hut
while you look out into the mountain and moonscape." Nothing in the corpus does
this. plan_interiors.py stands inside and looks at the room; plan_nightsky.py
stands on the roof and composes the moon; plan_channel.py stands on the roof
and looks down the channel. This one stands in the hall, a few metres back from
the gate, and looks OUT through the opening -- warm firelit interior along the
frame's edges, cold moonlit terrain receding through the doorway.

Three rules, all inherited from measurements already paid for:

1. THE MOON IS A LIGHT, NOT A SUBJECT (the channel lane's rule). The outward
   bearing is fixed by the architecture -- hall centre through the gate -- so
   the only free variable is the CLOCK. For each gate bearing this planner
   scans the moon's whole window with the arc equations (measured to 0.001 deg,
   CelestialArcTests) and picks the time of night when the moon stands 40-140
   degrees off-axis: raking light, long shadows, never a disc in the middle of
   the frame.

2. LOW MOON, LONG SHADOWS. Altitude is confined to [8, 22] degrees and scored
   toward 14. At 42 degrees (t = 0.95) shadows pool under things; at 12 they
   run across the terrain. This is the whole reason the shot needs a planner --
   a fixed capture hour can never put a low moon behind every gate.

3. WARM NEEDS COLD IN THE SAME FRAME (the colour lane's result: warm mass runs
   ~3x indoors, and brightness separation peaks in the dark). The builders' own
   fires are held lit (TSV fires column, the storm lane's lever), the stance is
   the hall side of the gate, and the aim drops ~7 degrees below the lens so
   the horizon sits in the upper third: terrain and its shadows fill the
   middle band, sky takes the top.

The verdict for these frames is color_layers (warm_lift, opponent_gap) plus
depth_layers (layers, far_mass) -- NOT the aesthetic head, which marks dark
frames down on principle, and NOT sky_check, which would go looking for a disc
that rule 1 deliberately keeps off-axis.
"""

import argparse
import json
import math
import os
import sys

from plan_interiors import (EYE_STAND, LENS_OFFSET, look, los_penalty,
                            validate_tsv)
from plan_nightsky import body_direction


def parse_args():
    p = argparse.ArgumentParser(
        description="Plan hall-looking-out-the-gate night shots.")
    p.add_argument("--features", default="out/era17/features.json")
    p.add_argument("--out", default="out/era17/hearthview-1.json")
    p.add_argument("--top", type=int, default=14,
                   help="builds to plan, walked in feature-scan rank order")
    p.add_argument("--cluster-ids", default="",
                   help="comma-separated allow-list; overrides --top")
    p.add_argument("--min-fires", type=int, default=1,
                   help="a hall with no fire has no warm side to photograph")
    p.add_argument("--min-offset", type=float, default=40.0)
    p.add_argument("--max-offset", type=float, default=140.0)
    p.add_argument("--alt-lo", type=float, default=8.0)
    p.add_argument("--alt-hi", type=float, default=22.0)
    p.add_argument("--alt-ideal", type=float, default=14.0,
                   help="shadow length is the objective; 14 deg doubles it "
                        "against the 24 deg the night lane shot at")
    p.add_argument("--inside-m", default="4.0,3.0,5.5,2.5",
                   help="stance distances inside the gate to try, in order, "
                        "stepping when a wall bites")
    p.add_argument("--aim-dist", type=float, default=28.0,
                   help="metres past the gate to place the aim point")
    p.add_argument("--aim-y-offset", type=float, default=0.8,
                   help="aim height relative to the opening's pivot. The first "
                        "probe used -2.0 and the mod's occlusion receipt said "
                        "the sight line dug into rising terrain on 11 of 22 "
                        "rows; +0.8 is ~2 deg below the lens instead of ~7")
    p.add_argument("--max-los", type=int, default=2,
                   help="drop a stance whose line to the gate clips walls "
                        "more than this (advisory grid, same as interiors)")
    p.add_argument("--environment", default="Clear",
                   help="the only sky with stars and a visible moon")
    return p.parse_args()


def wrap180(a):
    return (a + 180.0) % 360.0 - 180.0


def moon_times(bearing, args):
    """Best time of night per side (moon right of axis, moon left of axis).

    Returns up to two (t, offset, altitude) tuples. The two sides are genuinely
    different photographs -- the shadows run the other way across the terrain --
    so both are kept when the moon's arc offers both.
    """
    best = {}
    t = 0.755
    while True:
        az, alt = body_direction(t)
        if args.alt_lo <= alt <= args.alt_hi:
            off = wrap180(az - bearing)
            if args.min_offset <= abs(off) <= args.max_offset:
                side = "r" if off > 0 else "l"
                score = 0.6 * abs(abs(off) - 90.0) + abs(alt - args.alt_ideal)
                if side not in best or score < best[side][0]:
                    best[side] = (score, round(t % 1.0, 3), round(off, 1),
                                  round(alt, 1))
        t += 0.002
        if t >= 1.245:               # 0.755 -> 0.999 wraps into 0.0 -> 0.245
            break
    return [(v[1], v[2], v[3], side) for side, v in sorted(best.items())]


def main():
    args = parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)

    with open(args.features, encoding="utf-8") as fh:
        fdoc = json.load(fh)
    clusters = fdoc["clusters"]

    if args.cluster_ids:
        keep = {c.strip() for c in args.cluster_ids.split(",") if c.strip()}
        picked = [(cid, f) for cid, f in clusters.items() if cid in keep]
    else:
        ranked = sorted(clusters.items(), key=lambda kv: kv[1]["rank"])
        picked = ranked
    inside_steps = [float(d) for d in args.inside_m.split(",")]

    shots, notes, planned = [], {}, 0
    for cid, f in picked:
        if not args.cluster_ids and planned >= args.top:
            break
        label = f.get("label") or f"cluster {cid}"

        def skip(reason):
            notes[cid] = {"label": label, "skipped": reason}
            print(f"  {cid:>5} {label[:34]:<34} skipped: {reason}")

        if len(f.get("fires") or []) < args.min_fires:
            skip("no fires -- no warm side to stand in")
            continue
        bands = f.get("floor_bands") or []
        if not bands:
            skip("no floor bands")
            continue
        hall = max(bands, key=lambda b: b["count"])

        openings = [g for g in (f.get("gates") or [])
                    if abs(g["y"] - hall["y"]) <= 3.0]
        kind = "gate"
        if not openings:
            openings = [g for g in (f.get("doors") or [])
                        if abs(g["y"] - hall["y"]) <= 3.0]
            kind = "door"
        if not openings:
            skip("no gate or door on the hall level")
            continue

        # A torch-lit opening beats a far one: the first probe's receipts put
        # fires_in_view at 0-7, so the warm side must be REQUIRED into frame,
        # not hoped for (vantage_gate learned the same -- its one unlit pick
        # was a black frame at every hour). Among lit openings, farthest from
        # the hall centre frames the longest indoor run.
        def hall_dist(g):
            return math.hypot(g["x"] - hall["cx"], g["z"] - hall["cz"])

        def lit(g):
            return any(abs(g["y"] - p["y"]) <= 4
                       and math.hypot(g["x"] - p["x"], g["z"] - p["z"]) <= 8
                       for p in f["fires"])
        g = max(openings, key=lambda o: (lit(o), hall_dist(o)))
        if hall_dist(g) < 2.0:
            skip("the opening sits on the hall centre; no outward axis")
            continue

        ox = (g["x"] - hall["cx"]) / hall_dist(g)     # outward unit vector
        oz = (g["z"] - hall["cz"]) / hall_dist(g)
        bearing = math.degrees(math.atan2(ox, oz)) % 360.0

        times = moon_times(bearing, args)
        if not times:
            skip(f"moon never rakes bearing {bearing:.0f} at "
                 f"{args.alt_lo:.0f}-{args.alt_hi:.0f} deg altitude")
            continue

        walls = f.get("walls") or []
        player_y = g["y"] + (EYE_STAND - LENS_OFFSET)
        lens_y = player_y + LENS_OFFSET
        cam = None
        for d in inside_steps:
            cand = (g["x"] - ox * d, player_y, g["z"] - oz * d)
            bitten = any(abs(wy - lens_y) <= 2.0
                         and (wx - cand[0]) ** 2 + (wz - cand[2]) ** 2 <= 0.8 ** 2
                         for wx, wy, wz in walls)
            if bitten:
                continue
            lens = (cand[0], lens_y, cand[2])
            los = los_penalty(lens, (g["x"], g["y"] + 1.5, g["z"]), walls)
            if los <= args.max_los:
                cam, stance_d = cand, d
                break
        if cam is None:
            skip("every stance inside the opening bites a wall or "
                 "looks through one")
            continue

        lens = (cam[0], lens_y, cam[2])
        aim = (g["x"] + ox * args.aim_dist, g["y"] + args.aim_y_offset,
               g["z"] + oz * args.aim_dist)
        yaw, pitch, dist = look(lens, aim)

        notes[cid] = {
            "label": label, "opening": f"{kind}:{g['name']}",
            "bearing": round(bearing, 1), "stance_inside_m": stance_d,
            "times": [{"t": t, "moon_offset": off, "moon_alt": alt,
                       "side": side} for t, off, alt, side in times],
        }
        print(f"  {cid:>5} {label[:34]:<34} {kind} at {bearing:5.1f} deg, "
              + ", ".join(f"t={t} ({side} {off:+.0f} alt {alt:.0f})"
                          for t, off, alt, side in times))

        for i, (t, off, alt, side) in enumerate(times, start=1):
            shots.append({
                "cluster_id": int(cid), "label": label,
                "shot": f"hearth{side}t{str(t).replace('0.', '')}",
                "camera": {"x": round(cam[0], 1), "y": round(cam[1], 2),
                           "z": round(cam[2], 1)},
                "aim": {"x": round(aim[0], 1), "y": round(aim[1], 2),
                        "z": round(aim[2], 1)},
                "yaw_deg": yaw, "pitch_deg": pitch,
                "distance_m": round(dist, 1),
                "environment": args.environment, "time_of_day": t,
                "mode": "interior", "fires": 1,
                "moon_offset_deg": off, "moon_alt_deg": alt,
            })
        planned += 1

    if not shots:
        sys.exit("no build produced a shot; every candidate was skipped")

    out = {
        "generated_from": "plan_hearthview.py",
        "world": fdoc.get("world"),
        "structures": planned,
        "shots": len(shots),
        "settings": {
            "eye_stand_m": EYE_STAND, "lens_offset_m": LENS_OFFSET,
            "moon_offset_deg": [args.min_offset, args.max_offset],
            "moon_alt_deg": [args.alt_lo, args.alt_hi, args.alt_ideal],
            "aim_dist_m": args.aim_dist, "environment": args.environment,
        },
        "vantages": notes,
        "plan": shots,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, args.out)

    # Same contract as plan_interiors.py: 16 columns, mode + fires, no flash.
    tsv = os.path.splitext(args.out)[0] + ".tsv"
    with open(tsv + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# cluster_id\tshot\tcam_x\tcam_y\tcam_z\tyaw\tpitch\tenv\t"
                 "time\taim_x\taim_y\taim_z\tlabel\tmode\tfires\tflash\n")
        for s in shots:
            c_, a = s["camera"], s["aim"]
            fh.write(f"{s['cluster_id']}\t{s['shot']}\t{c_['x']}\t{c_['y']}\t"
                     f"{c_['z']}\t{s['yaw_deg']}\t{s['pitch_deg']}\t"
                     f"{s['environment']}\t{s['time_of_day']}\t{a['x']}\t"
                     f"{a['y']}\t{a['z']}\t{s['label'].replace(chr(9), ' ')}\t"
                     f"{s['mode']}\t1\t\n")
    os.replace(tsv + ".tmp", tsv)

    ok, bad = validate_tsv(tsv)
    print()
    print(f"  {planned} structure(s) -> {len(shots)} shots")
    print(f"  {args.out}")
    print(f"  {tsv}  (this is the one the mod reads)")
    print(f"  TSV validation: {ok} row(s) parse the way LoadShotPlan parses, "
          f"{bad} would drop")
    if bad:
        sys.exit("some rows would be dropped by the mod's parser -- "
                 "fix before arming")


if __name__ == "__main__":
    main()
