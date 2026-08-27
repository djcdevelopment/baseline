#!/usr/bin/env python3
"""Did the night frames come out, and did the moon land where it was aimed?

The aesthetic head cannot answer this. Measured over the 2,181-frame corpus it
moves 0.62 on time and weather and about zero on anything else -- an exposure
meter and a veto, not a critic -- and it marks dark frames down on principle.
So a night pass judged by it would be reported as a failure whatever came back.

This measures the things the plan actually claimed:

  where the body landed   Fit the moon's limb, turn the pixel position back into
                          a world bearing and altitude using the receipt's own
                          yaw, pitch and fov, and compare it to where
                          plan_nightsky.py said it would be. That residual is the
                          equation validating itself. It is also the only way to
                          measure rho, the disc's angular radius, which EnvMan
                          does not know -- there is no moon object in the scene.

  did the clouds part     Count stars in the sky band. Cloud position is not a
                          setting; it is a re-roll, which is why the plan shoots
                          repeats. This is how you tell which re-roll won.

  is it a photograph      luma_mean between the black floor (a night frame with
                          no sky in it measured 6-8) and the fog ceiling (186),
                          against a gallery median of 96.

Works on the ORIGINAL PNGs, never the derived web images: the index builder crops
UI off the right edge, and a crop moves the optical centre, which would put a
silent bias straight into the angles.

Usage:
  python sky_check.py --plan out/era17/nightsky.json --run 20260825-...
"""
import argparse
import json
import math
import os
import sys
from collections import deque

RECEIPTS = (r"C:\Program Files (x86)\Steam\steamapps\common\Valheim"
            r"\BepInEx\config\shotplan-receipts.jsonl")
CAPTURES = (r"C:\Program Files (x86)\Steam\steamapps\common\Valheim"
            r"\BepInEx\config\comfy-orbit-captures")

# Downsample before doing anything: the limb is thousands of pixels across and a
# 1/8 scale keeps every bit of that while making a pure-python flood fill cheap.
SCALE = 8
# Bright and cyan. The moon and its limb glow are the only things in a Valheim
# night sky that are both.
LUMA_MIN = 90.0
CYAN_MIN = 25.0
# A disc bright enough to bloom saturates toward white and loses its blue-red
# separation entirely. Nothing else in a night sky saturates: stars are single
# pixels below the area floor, and lanterns and fires are warm, so they fail the
# circle fit rather than this threshold.
WHITE_MIN = 200.0
# A component smaller than this is a lantern, a fairy light, or guck.
MIN_AREA_FRAC = 0.005
# The ring is the reason this file is not four lines long. It is a long thin
# bright arc that merges with the limb, and a circle fitted to a nearly straight
# feature has a huge radius and a beautifully small residual -- so residual alone
# accepts it. Bounding the radius is what separates them: the moon fits at about
# 1,600 px on a 4K frame, a ring segment at tens of thousands.
# Measured, not assumed. On 20260827-085344 the moon's saturated core fits at
# r = 253 px full-res with a median residual of 0.79 against 1.58 allowed -- a
# clean fit, rejected only by the old 400 px floor. The note above saying "the
# moon fits at about 1,600 px" cannot be the disc: at a focal length of 1,695 px
# (65 deg vertical on a 2160 px frame) 1,600 px is an angular RADIUS of 43 deg,
# wider than the frame's own half-height. 253 px is 8.5 deg, which is the value
# rho had been missing. The upper bound is what separates the ring segment, and
# the circle residual is what rejects a lit tent: the two tents in that frame fit
# at 4.06 and 1.46 against tolerances of 1.37 and 1.12.
RADIUS_MIN_PX = 150.0
RADIUS_MAX_PX = 4000.0


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--plan", default=os.path.join(here, "out", "nightsky.json"))
    p.add_argument("--receipts", default=RECEIPTS)
    p.add_argument("--captures", default=CAPTURES)
    p.add_argument("--run", default="", help="only this capture run id")
    p.add_argument("--depth", default="", help="depth.json, to fold in the layer metrics")
    p.add_argument("--out", default="")
    p.add_argument("--limit", type=int, default=0)
    return p.parse_args()


def load_receipts(path, run):
    rows = []
    # PowerShell wrote this file, so line one carries a UTF-8 BOM and a plain
    # json.loads on it throws. utf-8-sig is the whole fix.
    with open(path, encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if run and rec.get("run") != run:
                continue
            if rec.get("skipped"):
                continue
            rows.append(rec)
    return rows


def components(mask, h, w, min_area):
    """Connected components of a boolean grid, largest first."""
    label = [[0] * w for _ in range(h)]
    found, cur = [], 0
    for y in range(h):
        for x in range(w):
            if not mask[y][x] or label[y][x]:
                continue
            cur += 1
            cells, q = [], deque([(y, x)])
            label[y][x] = cur
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny][nx] and not label[ny][nx]:
                        label[ny][nx] = cur
                        q.append((ny, nx))
            if len(cells) >= min_area:
                found.append(cells)
    found.sort(key=len, reverse=True)
    return found


def fit_circle(points):
    """Kasa least-squares circle through (x, y) points, then one trimmed refit.

    The trim matters more than the algebra: trees cut into the limb, and a fit
    that keeps every boundary pixel is a fit to the treeline.
    """
    def once(pts):
        n = len(pts)
        sx = sy = sxx = syy = sxy = sxxx = syyy = sxyy = sxxy = 0.0
        for x, y in pts:
            sx += x; sy += y
            sxx += x * x; syy += y * y; sxy += x * y
            sxxx += x * x * x; syyy += y * y * y
            sxyy += x * y * y; sxxy += x * x * y
        a11, a12 = 2 * (sx * sx / n - sxx), 2 * (sx * sy / n - sxy)
        a21, a22 = a12, 2 * (sy * sy / n - syy)
        b1 = sx * (sxx + syy) / n - (sxxx + sxyy)
        b2 = sy * (sxx + syy) / n - (syyy + sxxy)
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-9:
            return None
        cx = (b1 * a22 - b2 * a12) / det
        cy = (a11 * b2 - a21 * b1) / det
        r = math.sqrt(max(0.0, (sxx + syy - 2 * cx * sx - 2 * cy * sy) / n
                          + cx * cx + cy * cy))
        return cx, cy, r

    fit = once(points)
    if fit is None:
        return None
    cx, cy, r = fit
    ranked = sorted(points, key=lambda p: abs(math.hypot(p[0] - cx, p[1] - cy) - r))
    keep = ranked[: max(12, int(len(ranked) * 0.7))]
    fit = once(keep) or fit
    cx, cy, r = fit
    resid = sorted(abs(math.hypot(x - cx, y - cy) - r) for x, y in keep)
    return cx, cy, r, resid[len(resid) // 2]


def find_disc(small, lum, h, w):
    """The moon, or None. Returns full-resolution centre, radius and residual."""
    # Cyan OR saturated-white. The cyan test describes a dim, unbloomed disc; a
    # bright one blooms to near-white and its blue-red collapses. Measured on
    # 0026_moon2t005y150.png the moon reads blue-red +8.3 over the blob and +4.0
    # across its brightest 500 px, against CYAN_MIN 25 -- so the moon was never
    # entering the candidate mask, and sky_check reported nan on 21 frames while
    # the disc was plainly visible in six of them.
    #
    # The gates below still have to pass: area, a circle fit under 5% residual,
    # the radius window, and brighter inside its own edge than outside. A warm
    # lantern or fire fails the circle fit; those are what this could otherwise
    # have let in.
    mask = [[lum[y][x] > LUMA_MIN
             and ((small[y][x][2] - small[y][x][0]) > CYAN_MIN
                  or lum[y][x] > WHITE_MIN)
             for x in range(w)] for y in range(h)]
    best = None
    for cells in components(mask, h, w, int(MIN_AREA_FRAC * h * w))[:4]:
        member = set(cells)
        # The outer boundary only: a cell with a non-member neighbour.
        edge = [(x, y) for y, x in cells
                if any((y + dy, x + dx) not in member
                       for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        # Boundary pixels on the frame border are where the disc leaves the
        # picture, not where it ends.
        edge = [(x, y) for x, y in edge if 0 < x < w - 1 and 0 < y < h - 1]
        if len(edge) < 40:
            continue
        fit = fit_circle(edge)
        if fit is None:
            continue
        cx, cy, r, resid = fit
        if not (RADIUS_MIN_PX / SCALE < r < RADIUS_MAX_PX / SCALE):
            continue
        if resid > 0.05 * r:
            continue
        # A disc is brighter inside its own edge than outside it; a ring is not.
        inside = ring_luma(lum, h, w, cx, cy, r * 0.85)
        outside = ring_luma(lum, h, w, cx, cy, r * 1.15)
        if inside is None or outside is None or inside < outside + 8.0:
            continue
        score = len(cells)
        if best is None or score > best[0]:
            best = (score, cx * SCALE, cy * SCALE, r * SCALE, resid * SCALE,
                    inside, outside)
    return best


def ring_luma(lum, h, w, cx, cy, r):
    """Mean luminance around a circle, over the samples that land in frame."""
    vals = []
    for k in range(72):
        a = math.radians(k * 5)
        x, y = int(cx + r * math.cos(a)), int(cy + r * math.sin(a))
        if 0 <= x < w and 0 <= y < h:
            vals.append(lum[y][x])
    return sum(vals) / len(vals) if len(vals) >= 8 else None


def to_world(px, py, width, height, yaw, pitch, fov_v):
    """Pixel -> (azimuth, altitude), in the receipt's own convention.

    Yaw is clockwise from +Z and pitch is positive looking DOWN, which is what
    plan_shots.py emits and what the mod writes back, so the axis elevation is
    -pitch.
    """
    t = math.tan(math.radians(fov_v / 2.0))
    half = height / 2.0
    u = (px - width / 2.0) / half * t
    v = (half - py) / half * t
    psi, e = math.radians(yaw), math.radians(-pitch)
    fwd = (math.sin(psi) * math.cos(e), math.sin(e), math.cos(psi) * math.cos(e))
    right = (math.cos(psi), 0.0, -math.sin(psi))
    up = (-math.sin(psi) * math.sin(e), math.cos(e), -math.cos(psi) * math.sin(e))
    d = [u * right[i] + v * up[i] + fwd[i] for i in range(3)]
    n = math.sqrt(sum(c * c for c in d)) or 1.0
    return (math.degrees(math.atan2(d[0], d[2])) % 360.0,
            math.degrees(math.asin(max(-1.0, min(1.0, d[1] / n))))), d, n


def angular_radius(px, py, r, width, height, yaw, pitch, fov_v):
    """Angle between the disc's centre and a point on its limb."""
    (_a1, _e1), d1, n1 = to_world(px, py, width, height, yaw, pitch, fov_v)
    (_a2, _e2), d2, n2 = to_world(px, py + r, width, height, yaw, pitch, fov_v)
    cos = sum(d1[i] * d2[i] for i in range(3)) / (n1 * n2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def star_count(lum, h, w, skip_disc):
    """Points of light in the sky band, which is how you tell the clouds parted.

    A star is a pixel clearly brighter than its own neighbourhood. Cloud is
    bright and smooth, so it produces almost none of them.
    """
    n = 0
    for y in range(2, h // 2):
        for x in range(2, w - 2):
            if skip_disc and skip_disc(x, y):
                continue
            v = lum[y][x]
            if v < 40:
                continue
            ring = [lum[y - 2][x], lum[y + 2][x], lum[y][x - 2], lum[y][x + 2]]
            if v > max(ring) + 20:
                n += 1
    return n


def main():
    args = parse_args()
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is required: pip install pillow")

    planned = {}
    if os.path.exists(args.plan):
        with open(args.plan, encoding="utf-8") as fh:
            for s in json.load(fh)["plan"]:
                planned[(s["cluster_id"], s["shot"])] = s

    depth = {}
    if args.depth and os.path.exists(args.depth):
        with open(args.depth, encoding="utf-8") as fh:
            depth = json.load(fh)

    rows = load_receipts(args.receipts, args.run)
    rows = [r for r in rows if (r.get("mode") or "") == "rooftop"
            or (r.get("shot") or "").startswith("moon")]
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        sys.exit("no rooftop frames in the receipts -- check --run")

    print(f"  {len(rows)} rooftop frame(s)")
    print()
    print(f"  {'file':>22} {'luma':>6} {'stars':>6} {'az':>7} {'alt':>7} "
          f"{'rho':>6} {'d_az':>6} {'d_alt':>6}")
    out, hits = [], 0
    for rec in rows:
        path = os.path.join(args.captures, rec["run"], rec["file"])
        if not os.path.exists(path):
            continue
        img = Image.open(path).convert("RGB")
        width, height = img.size
        sw, sh = width // SCALE, height // SCALE
        small_img = img.resize((sw, sh), Image.Resampling.BOX)
        px = list(small_img.getdata())
        small = [[px[y * sw + x] for x in range(sw)] for y in range(sh)]
        lum = [[0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2] for c in row]
               for row in small]
        flat = [v for row in lum for v in row]
        luma_mean = sum(flat) / len(flat)

        disc = find_disc(small, lum, sh, sw)
        entry = {"run": rec["run"], "file": rec["file"],
                 "cluster_id": rec.get("cluster_id"), "shot": rec.get("shot"),
                 "time_of_day": rec.get("time_of_day"),
                 "luma_mean": round(luma_mean, 1),
                 "clearance": rec.get("clearance"),
                 "occluded": bool(rec.get("occluded"))}

        skip = None
        if disc:
            _score, cx, cy, r, resid, inside, outside = disc
            skip = (lambda X, Y, cx=cx / SCALE, cy=cy / SCALE, r=r / SCALE:
                    (X - cx) ** 2 + (Y - cy) ** 2 < (r * 1.05) ** 2)
            fov = rec.get("fov") or 65.0
            (az, alt), _d, _n = to_world(cx, cy, width, height,
                                         rec["yaw"], rec["pitch"], fov)
            rho = angular_radius(cx, cy, r, width, height,
                                 rec["yaw"], rec["pitch"], fov)
            entry.update({"found": True, "azimuth_deg": round(az, 1),
                          "altitude_deg": round(alt, 1), "rho_deg": round(rho, 1),
                          "radius_px": round(r), "residual_px": round(resid, 1),
                          "inside_luma": round(inside, 1),
                          "outside_luma": round(outside, 1)})
            hits += 1
        else:
            entry["found"] = False

        stars = star_count(lum, sh, sw, skip)
        entry["stars"] = stars

        want = planned.get((rec.get("cluster_id"), rec.get("shot")))
        d_az = d_alt = None
        if want and disc:
            d_az = (entry["azimuth_deg"] - want["moon_azimuth_deg"] + 180) % 360 - 180
            d_alt = entry["altitude_deg"] - want["moon_altitude_deg"]
            entry["planned_azimuth_deg"] = want["moon_azimuth_deg"]
            entry["planned_altitude_deg"] = want["moon_altitude_deg"]
            entry["residual_azimuth_deg"] = round(d_az, 1)
            entry["residual_altitude_deg"] = round(d_alt, 1)

        image_id = f"{rec['run']}_{os.path.splitext(rec['file'])[0]}"
        if image_id in depth:
            for k in ("layers", "far_mass", "depth_span", "edge_frame", "depth_score"):
                if k in depth[image_id]:
                    entry[k] = depth[image_id][k]

        out.append(entry)
        print(f"  {rec['file']:>22} {luma_mean:>6.1f} {stars:>6} "
              f"{entry.get('azimuth_deg', float('nan')):>7.1f} "
              f"{entry.get('altitude_deg', float('nan')):>7.1f} "
              f"{entry.get('rho_deg', float('nan')):>6.1f} "
              f"{(d_az if d_az is not None else float('nan')):>6.1f} "
              f"{(d_alt if d_alt is not None else float('nan')):>6.1f}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)

    print()
    print(f"  disc found in {hits}/{len(out)} frame(s)")
    lit = [e for e in out if 20 <= e["luma_mean"] <= 186]
    print(f"  {len(lit)}/{len(out)} frame(s) between the black floor and the fog ceiling")
    held = [e for e in out if e.get("clearance") == "planned"]
    print(f"  {len(held)}/{len(out)} kept the planned stance (the camera stayed on the roof)")
    rhos = [e["rho_deg"] for e in out if e.get("found")]
    if rhos:
        rhos.sort()
        print(f"  rho: min {rhos[0]:.1f}  median {rhos[len(rhos) // 2]:.1f}  "
              f"max {rhos[-1]:.1f}  -- feed the median back as plan_nightsky.py --rho")
    res = [abs(e["residual_azimuth_deg"]) for e in out if "residual_azimuth_deg" in e]
    if res:
        res.sort()
        print(f"  azimuth residual vs the plan: median {res[len(res) // 2]:.1f} deg")
        print("  A small residual is the equation validating itself. A large one "
              "means the\n  rendered disc is not at the directional light, which "
              "is a real finding and\n  not a bug -- EnvMan has no moon object.")


if __name__ == "__main__":
    main()
