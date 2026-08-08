#!/usr/bin/env python3
"""Curate a self-contained image set for the article: crop the debug HUD,
resize, re-encode, emit base64 data URIs. No coordinates, no creator ids."""
import base64, io, json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "out", "gallery")   # gitignored: real builder coords
OUT = os.path.join(HERE, "build")
CROP = (0, 40, 1550, 900)          # drop the NetworkSense HUD strip + right widget
os.makedirs(OUT, exist_ok=True)

idx = json.load(open(os.path.join(SRC, "index.json"), encoding="utf-8"))
# Part 1 is the exterior story; the interior variants belong to part 2's curator
# (curate2.py) and must not drift into these picks as the corpus grows.
INTERIOR = ("hall_", "toproom_", "seat_", "gate_", "court_")
imgs = [i for i in idx["images"] if i.get("aesthetic")
        and not (i.get("variant") or "").startswith(INTERIOR)]
by_id = {i["id"]: i for i in imgs}
by_cv = {}
for i in imgs:
    by_cv[(i["cluster_id"], i["variant"])] = i


def enc(image_id, width, quality, src="large"):
    p = os.path.join(SRC, src, image_id + ".webp")
    im = Image.open(p).convert("RGB")
    if im.size == (1600, 900):
        im = im.crop(CROP)
    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    b = buf.getvalue()
    return "data:image/webp;base64," + base64.b64encode(b).decode(), len(b)


def clean(rec):
    """Only the fields safe to publish — no x/y/z, no top_creator_id."""
    return {k: rec[k] for k in ("label", "kind", "variant", "environment",
                                "time_of_day", "aesthetic", "pieces", "height_m",
                                "footprint_m2", "builders", "cluster_rank",
                                "score", "shot_distance_m", "lens_offset_m",
                                "pieces_near_aim") if k in rec}


out, total = {}, 0

# 1. Hero — highest-scoring frame in the corpus
HERO = "20260806-071848_0439_orbit1"
uri, n = enc(HERO, 1500, 80); total += n
out["hero"] = {**clean(by_id[HERO]), "src": uri}

# 2. Orbit strip — the same hero build from all four planned bearings
orbit = []
for v in ("orbit1", "orbit2", "orbit3", "orbit4"):
    r = by_cv[(439, v)]
    uri, n = enc(r["id"], 620, 78); total += n
    orbit.append({**clean(r), "src": uri})
out["orbit"] = orbit

# 3. Light strip — one build, four times of day (the golden-hour finding)
light = []
for v in ("morning_clear", "noon_clear", "sunset_clear", "night_clear"):
    r = by_cv[(71, v)]
    uri, n = enc(r["id"], 620, 78); total += n
    light.append({**clean(r), "src": uri})
out["light"] = light

# 4. Feature grid — best frame per cluster, distinct clusters, diverse kinds
used_c, feat = {439, 71}, []
for r in sorted(imgs, key=lambda i: -i["aesthetic"]):
    if r["cluster_id"] in used_c:
        continue
    used_c.add(r["cluster_id"])
    uri, n = enc(r["id"], 780, 78); total += n
    feat.append({**clean(r), "src": uri})
    if len(feat) == 6:
        break
out["feature"] = feat

# 5. Contact sheet — spread across the whole ranked corpus to show volume
ranked = sorted(imgs, key=lambda i: -i["aesthetic"])
step = max(1, len(ranked) // 60)
sheet = []
for r in ranked[::step][:60]:
    uri, n = enc(r["id"], 150, 68, src="thumb"); total += n
    sheet.append({"src": uri, "a": round(r["aesthetic"], 2)})
out["sheet"] = sheet

json.dump(out, open(os.path.join(OUT, "images.json"), "w", encoding="utf-8"))
print(f"  hero 1 · orbit {len(orbit)} · light {len(light)} · feature {len(feat)} "
      f"· sheet {len(sheet)}")
print(f"  {total/1024/1024:.2f} MB of webp -> ~{total*1.34/1024/1024:.2f} MB base64")
