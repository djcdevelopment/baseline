"""Build a static, mobile-first gallery index from bench sidecars.

Reads <outdir>/meta/*.json -> <dest>/index.json (metadata only, no pixels).
Images are served separately as thumb/<id>.webp (256px) and img/<id>.webp (full),
so the showcase is fully decoupled from the live ComfyUI process and never 502s
while a bench run is restarting it.

Merges <dest>/stars.json (admin-flagged for print-prep) so the `starred` flag
persists across rebuilds; the live UI also refreshes it from /api/stars.

Usage (on AM4, from ~/bench):
    python3 ~/gallery/build_index.py --outdir results_full --dest ~/gallery
"""
from __future__ import annotations
import argparse, json, os, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="results_full", help="bench results dir with meta/")
    ap.add_argument("--dest", default=".", help="where to write index.json")
    args = ap.parse_args()

    metadir = os.path.join(args.outdir, "meta")
    scorepath = os.path.join(args.outdir, "scores.json")  # written by OMEN perception node
    scores = json.load(open(scorepath, encoding="utf-8")) if os.path.exists(scorepath) else {}
    starpath = os.path.join(args.dest, "stars.json")  # admin-flagged for print-prep upscale
    starred = (set(json.load(open(starpath, encoding="utf-8")).get("starred", []))
               if os.path.exists(starpath) else set())
    imgs, skipped = [], 0
    for fn in os.listdir(metadir):
        if not fn.endswith(".json"):
            continue
        p = os.path.join(metadir, fn)
        try:
            m = json.load(open(p, encoding="utf-8"))
            sc = scores.get(m["job_id"], {})
            imgs.append(dict(
                id=m["job_id"], model=m["model"], cell=m.get("cell_id"),
                style=m.get("style"), category=m["category"], length=m.get("length"),
                prompt=m["prompt"], seed=m.get("seed"), req=m.get("requester"),
                project=m.get("project"), campaign=m.get("campaign"),
                subjectType=m.get("subjectType"), subjectId=m.get("subjectId"),
                subjectLabel=m.get("subjectLabel"), artDirection=m.get("artDirection"),
                gameUse=m.get("gameUse"), qualityLane=m.get("qualityLane"),
                comparisonId=m.get("comparisonId"), registryVersion=m.get("registryVersion"),
                sourceRefs=m.get("sourceRefs", []),
                parentJobId=m.get("parentJobId"), parentRank=m.get("parentRank"),
                parentAesthetic=m.get("parentAesthetic"),
                referenceMethod=m.get("referenceMethod"),
                referenceStrength=m.get("referenceStrength"),
                t=m["metrics"]["t_total_s"], ts=round(os.path.getmtime(p)),
                aes=sc.get("aesthetic"), clip=sc.get("clip"),  # OMEN perception scores
                starred=(m["job_id"] in starred),             # admin print-prep flag
            ))
        except (json.JSONDecodeError, KeyError):
            skipped += 1  # the bench notes some sidecars were truncated by restarts

    imgs.sort(key=lambda x: x["ts"], reverse=True)  # newest first = feed order
    rated = [i for i in imgs if isinstance(i.get("aes"), (int, float))]
    featured = [i["id"] for i in sorted(rated, key=lambda x: -x["aes"])[:12]]  # top-rated strip
    idx = dict(
        generated=time.strftime("%Y-%m-%d %H:%M"),
        n=len(imgs),
        scored=len(rated),
        starred_n=sum(1 for i in imgs if i["starred"]),
        models=sorted({i["model"] for i in imgs}),
        styles=sorted({i["style"] for i in imgs if i["style"]}),
        categories=sorted({i["category"] for i in imgs}),
        requesters=sorted({i["req"] for i in imgs if i.get("req")}),
        projects=sorted({i["project"] for i in imgs if i.get("project")}),
        campaigns=sorted({i["campaign"] for i in imgs if i.get("campaign")}),
        subjectTypes=sorted({i["subjectType"] for i in imgs if i.get("subjectType")}),
        subjects=sorted({i["subjectId"] for i in imgs if i.get("subjectId")}),
        artDirections=sorted({i["artDirection"] for i in imgs if i.get("artDirection")}),
        qualityLanes=sorted({i["qualityLane"] for i in imgs if i.get("qualityLane")}),
        featured=featured,
        images=imgs,
    )
    os.makedirs(args.dest, exist_ok=True)
    dest = os.path.join(args.dest, "index.json")
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(idx, f, separators=(",", ":"))
    os.replace(tmp, dest)  # atomic: a periodic refresh never serves a half-written index
    print(f"{len(imgs)} images ({skipped} skipped, {len(rated)} scored, {idx['starred_n']} starred) -> {dest}")
    print("models:", idx["models"])
    print("featured (top-rated):", featured[:3], "...")


if __name__ == "__main__":
    main()
