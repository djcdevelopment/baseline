#!/usr/bin/env python3
"""Curate the image set for part 2 (framing, perspective and judgement
sharpening): crop the debug HUD, resize, re-encode, emit base64 data URIs.
No coordinates, no creator ids — same rules as part 1.

Part 2 shows failures on purpose — the throne that threw the camera, the slab
across the lens — so it reaches into superseded runs that the gallery index has
already replaced. Those renders still exist on disk because the index builder
renders every receipt before it dedups.
"""
import base64, io, json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "out", "gallery")   # gitignored: real builder coords
OUT = os.path.join(HERE, "build")
CROP = (0, 40, 1550, 900)          # drop the NetworkSense HUD strip + right widget
os.makedirs(OUT, exist_ok=True)

idx = json.load(open(os.path.join(SRC, "index.json"), encoding="utf-8"))
by_id = {i["id"]: i for i in idx["images"]}
depth = {}
dp = os.path.join(HERE, "..", "out", "depth.json")
if os.path.exists(dp):
    depth = json.load(open(dp, encoding="utf-8"))

INTERIOR = ("hall_", "toproom_", "seat_", "gate_", "court_")


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
    out = {k: rec[k] for k in ("label", "kind", "variant", "environment",
                               "time_of_day", "aesthetic", "pieces", "height_m",
                               "footprint_m2", "builders", "lens_offset_m")
           if k in rec}
    d = depth.get(rec["id"], {})
    if d:
        out["center_block"] = d.get("center_block")
        out["depth_score"] = d.get("depth_score")
    return out


def rec(image_id, width, quality, src="large"):
    global total
    uri, n = enc(image_id, width, quality, src)
    total += n
    base = by_id.get(image_id)
    if base is None:
        # superseded frame: not in the index any more, shown as a lesson.
        base = {"id": image_id, "label": "", "variant": image_id.split("_", 2)[2]}
    return {**clean(base), "src": uri}


total = 0
out = {}

# 1. Hero — Gothic Ruin's hall at sunset. The same build part 1 printed as its
# sample cluster record; this is what its inside looks like.
HERO = "20260808-031309_0051_hall_sunset"
out["hero"] = rec(HERO, 1500, 80)

# 2. Showcase — best frame per vantage kind plus the two the prose leans on.
out["show"] = [rec(i, 780, 78) for i in (
    "20260808-031309_0020_gate_storm",       # Luminous Temple, gate in the storm
    "20260808-031309_0416_court_sunset",     # Floating Dock, court at dusk
    "20260808-031309_0314_seat_storm",       # Winter Cabin, seated
    "20260808-031309_0189_toproom_sunrise",  # Pirate Haven, top room at dawn
    "20260808-024509_0439_court_night",      # battlements under stars
    "20260808-030205_0407_seat_night",       # the barrel cellar
)]

# 3. Before / after — the drone's view of Gothic Ruin, then standing in it.
out["pair"] = [rec("20260806-071848_0051_orbit3", 780, 78),
               rec("20260808-031309_0051_hall_sunrise", 780, 78)]

# 4. Conditions — the same hall, nothing moved but the sky.
out["light"] = [rec(f"20260808-031309_0051_hall_{c}", 620, 78)
                for c in ("sunrise", "sunset", "night", "storm")]

# 5. The lesson strip — three failures the receipts caught, then the fix.
out["fail"] = [rec(i, 620, 74) for i in (
    "20260808-021817_0439_seat_sunset",      # camera thrown by the throne collider
    "20260808-024509_0439_seat_sunset",      # crystal slab across the lens
    "20260808-024509_0071_seat_sunrise",     # a chair walled into a grotto
)]
out["fixed"] = rec("20260808-030205_0407_seat_night", 900, 78)

# 6. Contact sheet — the interior corpus, ranked spread.
interior = [i for i in idx["images"]
            if (i.get("variant") or "").startswith(INTERIOR) and i.get("aesthetic")]
ranked = sorted(interior, key=lambda i: -i["aesthetic"])
step = max(1, len(ranked) // 48)
out["sheet"] = []
for r in ranked[::step][:48]:
    uri, n = enc(r["id"], 150, 68, src="thumb")
    total += n
    out["sheet"].append({"src": uri, "a": round(r["aesthetic"], 2)})

json.dump(out, open(os.path.join(OUT, "images2.json"), "w", encoding="utf-8"))
print(f"  hero 1 · show {len(out['show'])} · pair 2 · light {len(out['light'])} "
      f"· fail {len(out['fail'])} + fixed · sheet {len(out['sheet'])}")
print(f"  {total/1024/1024:.2f} MB of webp -> ~{total*1.34/1024/1024:.2f} MB base64")
