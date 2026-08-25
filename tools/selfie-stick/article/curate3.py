#!/usr/bin/env python3
"""Curate the image set for part 3 (light): crop the debug HUD, resize, re-encode,
emit base64 data URIs. No coordinates, no creator ids -- same rules as parts 1 and 2.

Part 3 is about one variable, so almost every figure here is a matched pair or a
strip: the same build, the same camera, the same bearing, and only the sky changed.
That constrains the selection more than the earlier parts -- a frame is only useful
if its twin exists.
"""
import base64, io, json, os
from collections import defaultdict
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "out", "era17", "gallery")   # gitignored: real coords
OUT = os.path.join(HERE, "build")
os.makedirs(OUT, exist_ok=True)

# The renders already have the right-edge widget removed by the index builder; this
# drops the top strip where a HUD would sit on anything shot before 2026-08-24.
CROP_TOP = 40

idx = json.load(open(os.path.join(SRC, "index.json"), encoding="utf-8"))
by_id = {i["id"]: i for i in idx["images"]}
total = 0


def enc(image_id, width, quality):
    global total
    im = Image.open(os.path.join(SRC, "large", image_id + ".webp")).convert("RGB")
    im = im.crop((0, CROP_TOP, im.width, im.height))
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    b = buf.getvalue()
    total += len(b)
    return "data:image/webp;base64," + base64.b64encode(b).decode()


def clean(rec):
    """Only the fields safe to publish -- no x/y/z, no top_creator_id."""
    return {k: rec[k] for k in ("label", "variant", "environment", "time_of_day",
                                "aesthetic", "pieces", "height_m", "builders")
            if k in rec}


def pack(image_id, width, quality=80):
    out = clean(by_id[image_id])
    out["src"] = enc(image_id, width, quality)
    return out


def tod(i):
    v = i.get("time_of_day")
    return round(float(v), 2) if v is not None else None


orbit = [i for i in idx["images"] if str(i.get("variant", "")).startswith("orbit")]

# ---------------------------------------------------------------- matched pairs
# Same cluster, same bearing, golden against twilight. The whole article rests on
# these, so they are picked by the golden frame's score and carried as a unit.
g = {(i["cluster_id"], i["variant"]): i for i in orbit if tod(i) == 0.64}
t = {(i["cluster_id"], i["variant"]): i for i in orbit if tod(i) == 0.71}
both = sorted(set(g) & set(t), key=lambda k: -float(g[k].get("aesthetic") or 0))
seen, pairs = set(), []
for k in both:
    if k[0] in seen:
        continue                      # one bearing per build, for variety
    seen.add(k[0])
    pairs.append({"golden": pack(g[k]["id"], 760), "twilight": pack(t[k]["id"], 760)})
    if len(pairs) == 3:
        break

# ---------------------------------------------------------------- the hero
# Pier Haven: the single build of thirty where twilight beat golden. The exception
# is the right way into an article whose verdict is that daylight usually wins.
hero_id = max((i for i in orbit if tod(i) == 0.71 and i.get("aesthetic")),
              key=lambda i: float(i["aesthetic"]))["id"]
hero = pack(hero_id, 1600, 82)

# ---------------------------------------------------------------- the light strip
# One build through every sky, from ONE bearing. The dawn and weather slots re-use
# the hero camera rather than an orbit bearing, so matching on variant name would
# quietly mix two viewpoints into a figure whose entire claim is that only the sky
# changed. Match on the yaw in the capture receipts instead, which is exact.
RECEIPTS = r"C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\config\shotplan-receipts.jsonl"
yaw = {}
if os.path.exists(RECEIPTS):
    for line in io.open(RECEIPTS, encoding="utf-8-sig"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        # early receipts predate the yaw field; a frame without one simply cannot
        # join this figure, which is the correct outcome rather than a guess
        if r.get("yaw") is None or not r.get("file"):
            continue
        yaw[f"{r['run']}_{os.path.splitext(r['file'])[0]}"] = round(float(r["yaw"]), 1)

bybearing = defaultdict(lambda: defaultdict(dict))
for i in idx["images"]:
    v, y = tod(i), yaw.get(i["id"])
    if v is None or y is None or i.get("cluster_id") is None:
        continue
    bybearing[(i["cluster_id"], y)][v] = i
(cid, bearing), got = max(
    bybearing.items(),
    key=lambda kv: (len(kv[1]), sum(float(x.get("aesthetic") or 0) for x in kv[1].values())))
strip = [pack(got[v]["id"], 420) for v in sorted(got)]

# ---------------------------------------------------------------- lit at dusk
# What the article is actually arguing: somebody lit these for themselves.
night = [pack(i["id"], 620) for i in sorted(
    (i for i in idx["images"]
     if tod(i) in (0.71, 0.9) and i.get("aesthetic")),
    key=lambda i: -float(i["aesthetic"]))[:4]]

# ---------------------------------------------------------------- the verdict
# Best golden frame against best twilight frame, per build. Best-of rather than
# median because that is how the gallery actually presents a build: one frame wins
# the tile, and the question is which light produced it.
bg, bt = defaultdict(list), defaultdict(list)
for i in orbit:
    a = i.get("aesthetic")
    if a is None or i.get("cluster_id") is None:
        continue
    if tod(i) == 0.64:
        bg[i["cluster_id"]].append((float(a), i["label"]))
    elif tod(i) == 0.71:
        bt[i["cluster_id"]].append((float(a), i["label"]))
ab = []
for k in sorted(set(bg) & set(bt)):
    gmax, name = max(bg[k])
    tmax, _ = max(bt[k])
    # the disambiguation suffix is noise in a chart label
    name = name.split(" ·")[0].split(" —")[0].strip()[:20]
    ab.append({"n": name, "g": round(gmax, 3), "t": round(tmax, 3),
               "d": round(gmax - tmax, 3)})
ab.sort(key=lambda r: -r["d"])
json.dump(ab, open(os.path.join(OUT, "ab3.json"), "w", encoding="utf-8"))
print(f"  verdict   {len(ab)} builds, golden wins {sum(1 for r in ab if r['d'] > 0)}")

doc = {"hero": hero, "pairs": pairs, "strip": strip, "night": night,
       "strip_label": by_id[got[sorted(got)[0]]["id"]].get("label", ""),
       "counts": {"images": len(idx["images"]),
                  "twilight": sum(1 for i in idx["images"] if tod(i) == 0.71),
                  "golden": sum(1 for i in idx["images"] if tod(i) == 0.64)}}
p = os.path.join(OUT, "images3.json")
json.dump(doc, open(p, "w", encoding="utf-8"))
print(f"  hero      {hero.get('label','')}  ({hero.get('aesthetic')})")
print(f"  pairs     {len(pairs)}")
print(f"  strip     cluster {cid} through {len(strip)} skies")
print(f"  night     {len(night)}")
print(f"  {p}  {total/1024/1024:.2f} MB of webp")
