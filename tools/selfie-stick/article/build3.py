#!/usr/bin/env python3
"""Assemble part 3 of the article (light).

Same contract as build.py and build2.py: curate3.py first, then this. Writes
site/selfie-stick/part-3/index.html and its og.jpg.

  python tools/selfie-stick/article/curate3.py
  python tools/selfie-stick/article/build3.py --target pages

template3.html is generated from template2's <style> block plus body3.html, so the
three parts share one stylesheet by construction rather than by discipline. Colours
and type still come from tools/site/tokens.css -- edit them there.
"""
import argparse, base64, json, math, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

BASE_URL = "https://djcdevelopment.github.io/baseline/"
ARTICLE_URL = BASE_URL + "selfie-stick/part-3/"

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--target", choices=["pages", "artifact"], default="pages")
ap.add_argument("--images", default=os.path.join(HERE, "build", "images3.json"))
ap.add_argument("--out", default=None)
args = ap.parse_args()

if not os.path.exists(args.images):
    raise SystemExit(f"no {args.images} - run curate3.py first")

OUT = args.out or (os.path.join(REPO, "site", "selfie-stick", "part-3", "index.html")
                   if args.target == "pages"
                   else os.path.join(HERE, "build", "article3-body.html"))

imgs = json.load(open(args.images, encoding="utf-8"))
tpl = open(os.path.join(HERE, "template3.html"), encoding="utf-8").read()

fonts = {}
for k in ("body", "bodysb", "mono", "monob"):
    with open(os.path.join(HERE, "fonts", k + ".woff2"), "rb") as fh:
        fonts[k] = "data:font/woff2;base64," + base64.b64encode(fh.read()).decode()

DEFS = ('<defs><marker id="a" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" '
        'markerHeight="6" orient="auto"><path d="M0 0.5 L7.5 4 L0 7.5 z" '
        'fill="var(--line2)"/></marker>'
        '<marker id="aw" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" '
        'markerHeight="6" orient="auto"><path d="M0 0.5 L7.5 4 L0 7.5 z" '
        'fill="var(--wood)"/></marker></defs>')

SUN_BEARING = 235.0


def esc(s):
    return html.escape(str(s or ""), quote=False)


# --------------------------------------------------------------- the sun method
def svg_sun():
    """Left: the four bearings around one build, and where the sun turned out to be.
    Right: the same data as brightness against bearing, with the fitted peak."""
    s = [f'<svg viewBox="0 0 880 330" role="img" aria-label="Left, a plan view of '
         f'four camera bearings around one building with the sun to the south west. '
         f'Right, sky brightness plotted against camera bearing, peaking at 235 '
         f'degrees">{DEFS}']
    cx, cy, r = 196, 178, 104

    s.append('<text class="s-lab" x="16" y="26">what the camera did</text>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" class="s-lane"/>')
    s.append(f'<rect class="s-box" x="{cx-34}" y="{cy-26}" width="68" height="52" rx="3"/>')
    s.append(f'<text class="s-tag" x="{cx}" y="{cy+4}" text-anchor="middle">one build</text>')

    # the four orbit bearings; the camera looks IN, so the label sits outside
    for b in (45, 135, 225, 315):
        a = math.radians(b)
        px, py = cx + r * math.sin(a), cy - r * math.cos(a)
        ix, iy = cx + 42 * math.sin(a), cy - 42 * math.cos(a)
        s.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="5" fill="var(--line2)"/>')
        s.append(f'<line class="s-arr" x1="{px:.0f}" y1="{py:.0f}" x2="{ix:.0f}" '
                 f'y2="{iy:.0f}" marker-end="url(#a)"/>')
        lx, ly = cx + (r + 26) * math.sin(a), cy - (r + 26) * math.cos(a)
        s.append(f'<text class="s-tag" x="{lx:.0f}" y="{ly+3:.0f}" '
                 f'text-anchor="middle">{b}&#176;</text>')

    # the recovered sun
    a = math.radians(SUN_BEARING)
    sx, sy = cx + (r + 52) * math.sin(a), cy - (r + 52) * math.cos(a)
    s.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="13" fill="none" '
             f'stroke="var(--wood)" stroke-width="1.6"/>')
    for k in range(8):
        t = math.radians(k * 45)
        s.append(f'<line x1="{sx + 17*math.cos(t):.0f}" y1="{sy + 17*math.sin(t):.0f}" '
                 f'x2="{sx + 23*math.cos(t):.0f}" y2="{sy + 23*math.sin(t):.0f}" '
                 f'stroke="var(--wood)" stroke-width="1.4"/>')
    s.append(f'<text class="s-tag" x="{sx:.0f}" y="{sy+40:.0f}" text-anchor="middle" '
             f'fill="var(--wood)">sun, 235&#176;</text>')

    # ---- right: brightness against bearing
    ox, oy, ow, oh = 470, 74, 380, 168
    s.append('<text class="s-lab" x="470" y="26">what the sky strip measured</text>')
    s.append(f'<rect class="s-box" x="{ox}" y="{oy}" width="{ow}" height="{oh}" rx="3"/>')
    s.append(f'<line class="s-lane" x1="{ox}" y1="{oy+oh/2:.0f}" x2="{ox+ow}" '
             f'y2="{oy+oh/2:.0f}"/>')
    pts = []
    for i in range(0, 361, 5):
        y = oy + oh / 2 - (oh / 2 - 18) * math.cos(math.radians(i - SUN_BEARING))
        pts.append(f"{ox + ow*i/360:.1f},{y:.1f}")
    s.append(f'<polyline class="s-hi" fill="none" points="{" ".join(pts)}"/>')
    px = ox + ow * SUN_BEARING / 360
    s.append(f'<line x1="{px:.0f}" y1="{oy+8}" x2="{px:.0f}" y2="{oy+oh-8}" '
             f'stroke="var(--wood)" stroke-width="1" stroke-dasharray="3 4"/>')
    for b in (0, 90, 180, 270, 360):
        s.append(f'<text class="s-tag" x="{ox + ow*b/360:.0f}" y="{oy+oh+18}" '
                 f'text-anchor="middle">{b}&#176;</text>')
    s.append(f'<text class="s-sub" x="{ox}" y="{oy+oh+40}">camera bearing &#8594; '
             f'brightest sky at 235&#176;, and that is the sun</text>')

    s.append('<text class="s-sub" x="16" y="300">Top 18% of the frame only. Whole-frame '
             'brightness is dominated by the building and fits nothing.</text>')
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------- the verdict
def svg_verdict():
    """Golden minus twilight, best frame per build, thirty builds."""
    ab = json.load(open(os.path.join(HERE, "build", "ab3.json"), encoding="utf-8"))
    w, h, ox, oy = 800, 160, 52, 44
    hi, lo = 0.70, -0.25
    slot = w / len(ab)
    zero = oy + h * (hi / (hi - lo))
    s = [f'<svg viewBox="0 0 880 268" role="img" aria-label="Thirty bars showing the '
         f'score difference between the golden and twilight frame of each build. '
         f'Twenty-nine are positive.">{DEFS}']
    s.append('<text class="s-lab" x="16" y="26">golden &#8722; twilight, best frame per build</text>')
    s.append(f'<line class="s-lane" x1="{ox}" y1="{zero:.0f}" x2="{ox+w}" y2="{zero:.0f}"/>')
    for i, r in enumerate(ab):
        x = ox + i * slot + 2
        bh = h * abs(r["d"]) / (hi - lo)
        y = zero - bh if r["d"] > 0 else zero
        fill = "var(--wood)" if r["d"] > 0 else "var(--blue)"
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{slot-4:.1f}" '
                 f'height="{bh:.1f}" rx="2" fill="{fill}"/>')
    s.append(f'<text class="s-tag" x="{ox-10}" y="{zero+4:.0f}" text-anchor="end">0</text>')
    s.append(f'<text class="s-tag" x="{ox-10}" y="{oy+6}" text-anchor="end">+0.7</text>')
    top, bot = ab[0], ab[-1]
    s.append(f'<text class="s-sub" x="{ox+4}" y="{zero - h*top["d"]/(hi-lo) - 10:.0f}">'
             f'{esc(top["n"])} &#43;{top["d"]}</text>')
    s.append(f'<text class="s-sub" x="{ox+w:.0f}" y="{zero + h*abs(bot["d"])/(hi-lo) + 20:.0f}" '
             f'text-anchor="end" fill="var(--blue)">{esc(bot["n"])} {bot["d"]}</text>')
    s.append('<text class="s-sub" x="16" y="248">One build in thirty reads better at dusk. '
             'It is the photograph at the top of this page.</text>')
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------- tiles
def tile(rec, note=""):
    lab = esc(rec.get("label", ""))
    sc = rec.get("aesthetic")
    right = note or (f'{sc:.2f}' if isinstance(sc, (int, float)) else "")
    return (f'<div class="tile"><img class="shot" src="{rec["src"]}" alt="{lab}">'
            f'<div class="lab"><b>{lab}</b><span class="n">{right}</span></div></div>')


pair_html = []
for p in imgs["pairs"]:
    pair_html.append('<div class="grid2">'
                     + tile(p["golden"], "golden 0.64")
                     + tile(p["twilight"], "twilight 0.71")
                     + '</div>')
PAIRS = '<div style="display:flex;flex-direction:column;gap:1.1rem">' + "".join(pair_html) + '</div>'

STRIP = "".join(tile(r, f'{r.get("environment","")} {r.get("time_of_day","")}')
                for r in imgs["strip"])
NIGHT = "".join(tile(r) for r in imgs["night"])

h = imgs["hero"]
hero_cap = (f'<b>{esc(h.get("label",""))}</b> &middot; twilight '
            f'{h.get("time_of_day","")} &middot; aesthetic {h.get("aesthetic",0):.2f} '
            f'&middot; the one build of thirty that reads better at dusk')

TOKENS = open(os.path.join(REPO, "tools", "site", "tokens.css"), encoding="utf-8").read()
c = imgs["counts"]

rep = {
    "__TOKENS__": TOKENS,
    "__FONT_BODY__": fonts["body"], "__FONT_BODYSB__": fonts["bodysb"],
    "__FONT_MONO__": fonts["mono"], "__FONT_MONOB__": fonts["monob"],
    "__HERO_SRC__": h["src"], "__HERO_CAP__": hero_cap,
    "__PAIR_TILES__": PAIRS, "__STRIP_TILES__": STRIP, "__NIGHT_TILES__": NIGHT,
    "__STRIP_LABEL__": esc(imgs.get("strip_label", "One build")),
    "__SVG_SUN__": svg_sun(), "__SVG_VERDICT__": svg_verdict(),
    "__COUNT_TW__": f'{c["twilight"]:,}', "__COUNT_GO__": f'{c["golden"]:,}',
    "__COUNT_ALL__": f'{c["images"]:,}',
}
for k, v in rep.items():
    if k not in tpl:
        raise SystemExit(f"placeholder {k} missing from template3")
    tpl = tpl.replace(k, v)

TITLE = "The light they built for"
DESC = ("The selfie-stick pipeline had shot every exterior at the same hour without "
        "ever testing it. Recovering the sun's bearing from the photographs, what the "
        "judging model can and cannot see, and why dusk earns its place. Part 3.")

if args.target == "pages":
    tpl = tpl.replace(f"<title>{TITLE}</title>\n", "", 1)
    tpl = (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{TITLE}</title>\n'
        f'<meta name="description" content="{DESC}">\n'
        '<meta name="author" content="Derek Ciula">\n'
        f'<link rel="canonical" href="{ARTICLE_URL}">\n'
        '<meta property="og:type" content="article">\n'
        f'<meta property="og:title" content="{TITLE}">\n'
        f'<meta property="og:description" content="{DESC}">\n'
        '<meta property="og:site_name" content="Baseline">\n'
        f'<meta property="og:url" content="{ARTICLE_URL}">\n'
        f'<meta property="og:image" content="{ARTICLE_URL}og.jpg">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<style>*{box-sizing:border-box}</style>\n'
        '</head>\n<body>\n' + tpl + '\n</body>\n</html>\n')

tpl = tpl.encode("ascii", "xmlcharrefreplace").decode("ascii")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="ascii").write(tpl)
print(f"  {OUT}  {len(tpl)/1024/1024:.2f} MB  ascii={tpl.isascii()}")

if args.target == "pages":
    import io as _io
    from PIL import Image
    raw = base64.b64decode(imgs["hero"]["src"].split(",", 1)[1])
    im = Image.open(_io.BytesIO(raw)).convert("RGB")
    im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
    top = max(0, (im.height - 630) // 2)
    im = im.crop((0, top, 1200, top + 630))
    og = os.path.join(os.path.dirname(OUT), "og.jpg")
    im.save(og, "JPEG", quality=86, optimize=True, progressive=True)
    print(f"  {og}  {os.path.getsize(og)//1024} KB")
