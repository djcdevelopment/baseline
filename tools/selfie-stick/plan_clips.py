"""Turn verified still framings into driven camera clips.

A photograph samples an instant. A clip samples TIME, and time is the only axis
on which a lightning strike can be COMPOSED rather than caught: the flash offset
is a column, so the strike lands on a chosen beat of a chosen move.

Derek's framing, and the reason this exists: "our timing with the lightening and
conveying a feeling vs showing a picture steps up again another level."

Every clip here starts from a framing that has already been shot as a still and
looked at, because the expensive unknown in a clip is the MOTION, not the
composition -- and reusing a proven stance keeps exactly one variable new.

Three moves, deliberately the three cheapest things that read as cinema:

  push    translate along the look direction, through the opening. The hut
          gives way to the storm. This is the doorway thesis in motion.
  pull    the same line, reversed: the world closes back into shelter.
  pan     no translation, yaw sweep. The stance is a place you are standing
          still in, looking around. It is also the control for the motion
          path itself -- if a pan reads as frozen, rotation is not reaching
          the camera even when position is.

The mod's hot loop does no IO, so nothing here can stall a frame; what this
file controls is purely geometry and timing.
"""

import argparse
import math
import os
import sys

FOV_V_DEG = 65.0


def parse_args():
    p = argparse.ArgumentParser(description="Plan driven camera clips.")
    p.add_argument("--from-plan", default="out/era17/hearthstorm-1.tsv",
                   help="a shot TSV whose framings have been shot and looked at")
    p.add_argument("--out", default="out/era17/clips-1.tsv")
    p.add_argument("--shots", default="",
                   help="comma-separated shot names to build from; default all")
    p.add_argument("--duration", type=float, default=10.0)
    p.add_argument("--push-m", type=float, default=7.0,
                   help="metres travelled along the look direction")
    p.add_argument("--pan-deg", type=float, default=45.0)
    p.add_argument("--flash-frac", type=float, default=0.6,
                   help="where in the clip the strike lands, 0-1. Late enough "
                        "that the move has established the space first")
    p.add_argument("--flash-bearing", type=float, default=-35.0,
                   help="matches the storm stills, whose flash A/B measured "
                        "+10.0 median luma against the no-flash twin")
    p.add_argument("--moves", default="push,pan",
                   help="comma-separated subset of push,pull,pan")
    return p.parse_args()


def forward(yaw_deg, pitch_deg):
    """Unit look vector. Yaw is degrees clockwise from +Z, pitch positive DOWN."""
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    horiz = math.cos(pitch)
    return (math.sin(yaw) * horiz, -math.sin(pitch), math.cos(yaw) * horiz)


def read_rows(path, wanted):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if len(f) < 13:
                continue
            name = f[1]
            if wanted and name not in wanted and f"{f[0]}_{name}" not in wanted:
                continue
            rows.append({
                "cluster": f[0], "shot": name,
                "cam": (float(f[2]), float(f[3]), float(f[4])),
                "yaw": float(f[5]), "pitch": float(f[6]),
                "env": f[7], "time": f[8],
                "label": f[12] if len(f) > 12 else f"cluster {f[0]}",
            })
    return rows


def main():
    args = parse_args()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    wanted = {s.strip() for s in args.shots.split(",") if s.strip()}
    moves = [m.strip() for m in args.moves.split(",") if m.strip()]

    rows = read_rows(args.from_plan, wanted)
    if not rows:
        sys.exit(f"no usable rows in {args.from_plan}")

    clips = []
    for r in rows:
        fx, fy, fz = forward(r["yaw"], r["pitch"])
        cx, cy, cz = r["cam"]
        # The lens rides 1.8 m over the placed point; the move is horizontal
        # along the look bearing, so height is carried unchanged and a pushed
        # camera cannot sink into the floor it started level with.
        ahead = (cx + fx * args.push_m, cy, cz + fz * args.push_m)
        back = (cx - fx * args.push_m, cy, cz - fz * args.push_m)
        flash_at = round(args.duration * args.flash_frac, 2)

        for move in moves:
            if move == "push":
                frm, to, yaw_to = (cx, cy, cz), ahead, r["yaw"]
            elif move == "pull":
                frm, to, yaw_to = ahead, (cx, cy, cz), r["yaw"]
            elif move == "pan":
                frm, to, yaw_to = (cx, cy, cz), (cx, cy, cz), r["yaw"] + args.pan_deg
            else:
                continue
            clips.append({
                "name": f"{int(r['cluster']):04d}_{r['shot']}_{move}",
                "label": r["label"], "env": r["env"], "time": r["time"],
                "dur": args.duration, "ease": "smooth",
                "flash_at": flash_at, "flash_bearing": args.flash_bearing,
                "from": frm, "to": to,
                "yaw_from": r["yaw"], "pitch_from": r["pitch"],
                "yaw_to": yaw_to, "pitch_to": r["pitch"],
            })

    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# clip\tlabel\tenv\ttime\tdur_s\tease\tflash_at\tflash_bearing\t"
                 "x0\ty0\tz0\tyaw0\tpitch0\tx1\ty1\tz1\tyaw1\tpitch1\n")
        for c in clips:
            f0, t0 = c["from"], c["to"]
            fh.write(
                f"{c['name']}\t{c['label']}\t{c['env']}\t{c['time']}\t"
                f"{c['dur']}\t{c['ease']}\t{c['flash_at']}\t{c['flash_bearing']}\t"
                f"{f0[0]:.1f}\t{f0[1]:.2f}\t{f0[2]:.1f}\t"
                f"{c['yaw_from']:.2f}\t{c['pitch_from']:.2f}\t"
                f"{t0[0]:.1f}\t{t0[1]:.2f}\t{t0[2]:.1f}\t"
                f"{c['yaw_to']:.2f}\t{c['pitch_to']:.2f}\n")

    # Re-read the way the mod's LoadClipPlan does: 18 tab-separated columns,
    # floats where floats are expected. A row this drops is a row it drops.
    ok = bad = 0
    with open(args.out, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if len(f) < 18:
                bad += 1
                continue
            try:
                for i in (3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17):
                    float(f[i])
                ok += 1
            except ValueError:
                bad += 1

    total = sum(c["dur"] for c in clips)
    print(f"  {len(rows)} framing(s) x {len(moves)} move(s) -> {len(clips)} clip(s), "
          f"{total:.0f}s of footage")
    print(f"  flash at {args.flash_frac:.0%} of each clip, bearing {args.flash_bearing:.0f}")
    print(f"  {args.out}")
    print(f"  validation: {ok} row(s) parse as LoadClipPlan parses, {bad} would drop")
    if bad:
        sys.exit("some rows would be dropped by the mod -- fix before arming")


if __name__ == "__main__":
    main()
