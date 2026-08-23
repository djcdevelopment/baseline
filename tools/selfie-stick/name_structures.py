#!/usr/bin/env python3
"""Name each structure by looking at it, using the vision model on OMEN.

The index builder derives a label from what it can count — portals, signs,
height — which yields "major hub · 9,603". Accurate and forgettable. A vision
model looking at the same place says "Snowy Pine Haven", because it can see the
decorated tree in the snow and the heuristic never will.

Writes out/cluster-names.json, which build_valheim_index.py already prefers over
its derived label, and out/cluster-descriptions.json for the gallery caption.

Resolution is the whole trick: at 512px (the gallery thumbnail size) qwen2.5vl
answers "Valheim Fort" for everything. At 1280px it finds the Christmas tree.
Full-size 4K frames are rejected by the endpoint as too large.

Usage:
  python name_structures.py [--index out/gallery/index.json] [--limit N]
                            [--force] [--dry-run] [--model qwen2.5vl:7b]
"""
import argparse
import base64
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

OLLAMA = os.environ.get("OMEN_OLLAMA", "http://127.0.0.1:11434")
MODEL = os.environ.get("OMEN_VLM_MODEL", "qwen2.5vl:7b")
SEND_PX = 1280          # see module docstring — 512 is too small, 4K is rejected

PROMPT = """You are looking at a screenshot of a place built by a player in the game Valheim.

Reply with ONLY a JSON object, no other text:
{"name": "...", "blurb": "...", "features": ["...", "...", "..."]}

"name" is how a person would refer to this place in conversation: 2-4 words,
evocative, specific to what you can actually see. Do not use the word "Valheim".
Do not use generic words like "Fort", "Base" or "Settlement" unless nothing more
specific is visible.
"blurb" is one sentence describing the place.
"features" are up to three concrete things you can actually see — a decorated
tree, a glass dome, longships at a dock, a bridge over water. Only things that
are really in the image."""


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--index", default=os.path.join(here, "out", "gallery", "index.json"))
    p.add_argument("--thumbs", default=os.path.join(here, "out", "gallery", "thumb"))
    p.add_argument("--captures", default=(r"C:\Program Files (x86)\Steam\steamapps"
                                          r"\common\Valheim\BepInEx\config\comfy-manual-captures"))
    p.add_argument("--out", default=os.path.join(here, "out"))
    p.add_argument("--model", default=MODEL)
    p.add_argument("--limit", type=int, default=0, help="only do N structures")
    p.add_argument("--force", action="store_true", help="rename ones already named")
    p.add_argument("--dry-run", action="store_true", help="pick frames, ask nothing")
    return p.parse_args()


def frame_quality(path):
    """Rank candidate frames without a GPU: a readable photo has spread, and a
    black or blown-out one does not. Mirrors the measurement that found the old
    time-of-day presets were wasting half of every capture session."""
    from PIL import Image
    with Image.open(path) as im:
        g = im.convert("L")
        g.thumbnail((160, 90))
        px = sorted(g.getdata())
    mean = sum(px) / len(px)
    spread = px[int(len(px) * 0.9)] - px[int(len(px) * 0.1)]
    if mean < 55 or mean > 205:        # too dark or blown out to read
        return -1
    return spread


def pick_frame(rows, thumb_dir):
    """The frame most likely to show the place clearly: prefer a frame that
    shows the whole structure, then clear weather, then the highest-contrast
    readable one.

    The perspective filter matters now that a structure can carry interiors. A
    hearth-lit room is often the highest-contrast frame a build has, and it is
    the worst possible thing to hand a model that has been asked to name the
    BUILDING -- it can see a table and no roofline. Interior-only clusters fall
    back to whatever they have."""
    rows = [r for r in rows if r.get("perspective") == "drone"] or rows
    cands = [r for r in rows if r.get("environment") == "Clear"] or rows
    best, best_q = None, -1
    for r in cands:
        t = os.path.join(thumb_dir, r["id"] + ".webp")
        if not os.path.exists(t):
            continue
        q = frame_quality(t)
        if q > best_q:
            best, best_q = r, q
    return best


def full_path(row, captures):
    """The 4K original behind a thumbnail: <captures>/<run>/<variant>.png"""
    return os.path.join(captures, row["run"], row["variant"] + ".png")


def encode(path, px=SEND_PX):
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((px, px))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode(), im.size


def ask(model, b64, timeout=180):
    body = json.dumps({"model": model, "prompt": PROMPT, "images": [b64],
                       "stream": False, "keep_alive": "10m",
                       "options": {"temperature": 0.3}}).encode()
    req = urllib.request.Request(OLLAMA + "/api/generate", body,
                                 {"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["response"]


def extract(text):
    """Pull a JSON object out of model prose. Never assume it obeyed the format."""
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def clean_name(n):
    n = re.sub(r"\s+", " ", str(n or "")).strip().strip('"').strip()
    n = re.sub(r"^(the\s+)?valheim\s+", "", n, flags=re.I)
    return n[:40]


def main():
    args = parse_args()
    if not os.path.exists(args.index):
        sys.exit(f"no index at {args.index} — run build_valheim_index.py first")
    with open(args.index, encoding="utf-8") as fh:
        rows = json.load(fh)["images"]

    by_cluster = {}
    for r in rows:
        if r.get("cluster_id") is not None:
            by_cluster.setdefault(r["cluster_id"], []).append(r)

    names_path = os.path.join(args.out, "cluster-names.json")
    desc_path = os.path.join(args.out, "cluster-descriptions.json")
    names = json.load(open(names_path, encoding="utf-8")) if os.path.exists(names_path) else {}
    descs = json.load(open(desc_path, encoding="utf-8")) if os.path.exists(desc_path) else {}

    todo = [c for c in by_cluster if args.force or str(c) not in names]
    todo.sort(key=lambda c: -len(by_cluster[c]))
    if args.limit:
        todo = todo[: args.limit]

    print(f"  {len(by_cluster)} structures photographed, {len(todo)} to name")

    ok = fail = 0
    for i, cid in enumerate(todo, 1):
        group = by_cluster[cid]
        row = pick_frame(group, args.thumbs)
        if not row:
            print(f"  [{i}/{len(todo)}] cluster {cid}: no readable frame — skipped")
            fail += 1
            continue
        src = full_path(row, args.captures)
        if not os.path.exists(src):
            src = os.path.join(args.thumbs, row["id"] + ".webp")   # fall back to the thumb
        if args.dry_run:
            print(f"  [{i}/{len(todo)}] cluster {cid}: would send {os.path.basename(src)}")
            continue

        t0 = time.time()
        try:
            b64, size = encode(src)
            raw = ask(args.model, b64)
        except (urllib.error.URLError, OSError) as exc:
            print(f"  [{i}/{len(todo)}] cluster {cid}: {exc}")
            fail += 1
            continue
        obj = extract(raw)
        if not obj or not obj.get("name"):
            print(f"  [{i}/{len(todo)}] cluster {cid}: unparseable reply — skipped")
            fail += 1
            continue

        name = clean_name(obj["name"])
        names[str(cid)] = name
        descs[str(cid)] = {"name": name,
                           "blurb": str(obj.get("blurb") or "")[:280],
                           "features": [str(f)[:60] for f in (obj.get("features") or [])][:3],
                           "from_image": row["id"],
                           "pieces": row.get("pieces")}
        ok += 1
        print(f"  [{i}/{len(todo)}] {name}  ({row.get('pieces', 0):,} pieces, "
              f"{time.time() - t0:.1f}s)")

    # The model names each place in isolation, so two harbours both come back as
    # "Waterfront Haven". Left alone they collapse into one filter chip and two
    # different builds look like one. Disambiguate the collisions only.
    def norm(nm):
        base = nm.split(" · ")[0].replace("'", "").casefold()
        return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") else w
                        for w in base.split())

    seen = {}
    for cid, nm in names.items():
        seen.setdefault(norm(nm), []).append(cid)
    for key, ids in seen.items():
        if len(ids) < 2:
            continue
        for cid in ids:
            pieces = (descs.get(cid) or {}).get("pieces")
            if pieces and " · " not in names[cid]:
                names[cid] = f"{names[cid]} · {pieces:,}"
                if cid in descs:
                    descs[cid]["name"] = names[cid]
        print(f"  disambiguated {len(ids)} structures sharing \"{names[ids[0]].split(' · ')[0]}\"")

    for path, data in ((names_path, names), (desc_path, descs)):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

    print(f"\n  named {ok}, failed {fail}")
    print(f"  {names_path}")
    print("  rerun build_valheim_index.py to pick the names up")


if __name__ == "__main__":
    main()
