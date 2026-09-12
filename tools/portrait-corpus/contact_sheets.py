r"""Contact sheets for the human pass, and the smaller evidence sheets the design record embeds.

    python tools/portrait-corpus/contact_sheets.py review --corpus <corpus> --concepts <concepts.json>
        one JPEG per concept under <corpus>/qa/, every take labelled s<N>, picked takes outlined
        gold, rejected takes outlined red with the reason. This is what picks.json is written from.
    python tools/portrait-corpus/contact_sheets.py evidence --corpus <corpus> --concepts <concepts.json>
        --out docs/design/valheim-portrait-picker-2026-09/contact-sheets
        the few sheets the record cites (one take per concept across the corpus; the takes of a
        locked and a loose concept; the seed-5/seed-11 background defects), each kept under 250 KB.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

GOLD, RED, GREY = (212, 163, 89), (220, 70, 60), (20, 20, 24)


def thumb(path: Path, side: int) -> Image.Image:
    im = Image.open(path)
    im.draft("RGB", (side * 2, side * 2))
    return im.convert("RGB").resize((side, side), Image.LANCZOS)


def sheet(items, cols: int, side: int, label_h: int = 18) -> Image.Image:
    """items: (path, label, outline_rgb_or_None). Missing/corrupt files become a grey tile."""
    rows = (len(items) + cols - 1) // cols
    S = Image.new("RGB", (cols * side, rows * (side + label_h)), GREY)
    d = ImageDraw.Draw(S)
    for i, (path, label, outline) in enumerate(items):
        x, y = (i % cols) * side, (i // cols) * (side + label_h)
        try:
            S.paste(thumb(path, side), (x, y))
        except Exception:
            d.rectangle((x, y, x + side - 1, y + side - 1), fill=(60, 30, 30))
            d.text((x + 6, y + side // 2), "corrupt", fill=(255, 200, 200))
        if outline:
            for k in range(3):
                d.rectangle((x + k, y + k, x + side - 1 - k, y + side - 1 - k), outline=outline)
        d.text((x + 4, y + side + 3), label[:40], fill=(235, 235, 235))
    return S


def save_under(S: Image.Image, path: Path, cap: int = 250_000) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    for q in (85, 78, 70, 62, 55, 48):
        S.save(path, "JPEG", quality=q, optimize=True)
        if path.stat().st_size <= cap:
            break
    return path.stat().st_size


def review(corpus: Path, concepts: list[dict]) -> None:
    out = corpus / "qa"
    out.mkdir(exist_ok=True)
    for c in concepts:
        picked = set(c["takes"]["picked"])
        rejected = {r["asset_id"]: ",".join(r["why"]) for r in c["takes"]["rejected"]}
        items = []
        for n in range(1, c["n_takes"] + 1):
            aid = f"{c['concept_id']}_s{n}"
            if aid in picked:
                items.append((corpus / "assets" / f"{aid}.png", f"s{n}  PICK", GOLD))
            elif aid in rejected:
                items.append((corpus / "assets" / f"{aid}.png", f"s{n}  {rejected[aid]}", RED))
            else:
                items.append((corpus / "assets" / f"{aid}.png", f"s{n}", None))
        S = sheet(items, 5, 220)
        S.save(out / f"contact-{c['concept_id']}.jpg", "JPEG", quality=82)
    print(f"review sheets: {len(concepts)} under {out}")


def evidence(corpus: Path, concepts: list[dict], out: Path) -> None:
    by_theme = sorted(concepts, key=lambda c: (c["theme"], c["role"], c["presentation"], c["variant"]))
    # 1-2: one picked take per concept, 48 per sheet
    per = [(corpus / "assets" / f"{c['takes']['picked'][0]}.png", c["concept_id"].replace("viking_", ""), None) for c in by_theme]
    for n, chunk in enumerate((per[:48], per[48:]), 1):
        size = save_under(sheet(chunk, 8, 150), out / f"concepts-{n}.jpg")
        print(f"concepts-{n}.jpg {size}")
    # 3: locked vs loose concept, all takes
    for tag, cid in (("locked", "viking_carpenter_f_artisan"), ("loose", "viking_furrier_f_seamstress")):
        c = next(x for x in concepts if x["concept_id"] == cid)
        items = [(corpus / "assets" / f"{cid}_s{n}.png", f"s{n}", None) for n in range(1, c["n_takes"] + 1)]
        size = save_under(sheet(items, 8, 150), out / f"takes-{tag}-{cid.replace('viking_', '')}.jpg")
        print(f"takes-{tag} {size}")
    # 4: the wolf-head takes (the case every detector failed)
    c = next(x for x in concepts if x["concept_id"] == "viking_berserker_m_wolfskin")
    picked = set(c["takes"]["picked"]); rej = {r["asset_id"] for r in c["takes"]["rejected"]}
    items = [(corpus / "assets" / f"{c['concept_id']}_s{n}.png", f"s{n}",
              GOLD if f"{c['concept_id']}_s{n}" in picked else RED if f"{c['concept_id']}_s{n}" in rej else None)
             for n in range(1, c["n_takes"] + 1)]
    size = save_under(sheet(items, 8, 150), out / "takes-wolfskin-human-pass.jpg")
    print(f"takes-wolfskin {size}")
    # 5: background defects
    defects = [(a["asset_id"], ",".join(a["why"])) for c in concepts for a in c["takes"]["rejected"] if "bg_dropped" in a["why"]]
    items = [(corpus / "assets" / f"{aid}.png", aid.replace("viking_", ""), RED) for aid, _ in defects]
    size = save_under(sheet(items, 4, 200), out / "defects-bg-dropped.jpg")
    print(f"defects {size}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["review", "evidence"])
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--concepts", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    concepts = json.loads(a.concepts.read_text(encoding="utf-8"))["concepts"]
    if a.mode == "review":
        review(a.corpus, concepts)
    else:
        evidence(a.corpus, concepts, a.out or Path("docs/design/valheim-portrait-picker-2026-09/contact-sheets"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
