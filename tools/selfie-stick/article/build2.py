#!/usr/bin/env python3
"""Assemble part 2 of the article (framing, perspective, judgement sharpening).

Same contract as build.py: curate2.py first, then this. Writes
site/selfie-stick/part-2/index.html and its og.jpg.

  python tools/selfie-stick/article/curate2.py
  python tools/selfie-stick/article/build2.py --target pages
"""
import argparse, base64, json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

BASE_URL = "https://djcdevelopment.github.io/baseline/"
ARTICLE_URL = BASE_URL + "selfie-stick/part-2/"

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--target", choices=["pages", "artifact"], default="pages")
ap.add_argument("--images", default=os.path.join(HERE, "build", "images2.json"))
ap.add_argument("--out", default=None)
args = ap.parse_args()

if not os.path.exists(args.images):
    raise SystemExit(f"no {args.images} — run curate2.py first")

OUT = args.out or (os.path.join(REPO, "site", "selfie-stick", "part-2", "index.html")
                   if args.target == "pages"
                   else os.path.join(HERE, "build", "article2-body.html"))

imgs = json.load(open(args.images, encoding="utf-8"))
tpl = open(os.path.join(HERE, "template2.html"), encoding="utf-8").read()

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


def esc(s):
    return html.escape(str(s or ""), quote=False)


# ------------------------------------------------------------- vantage plan
def svg_vantages():
    s = [f'<svg viewBox="0 0 880 348" role="img" aria-label="Plan view of the five '
         f'vantage recipes: hall, top room and seat inside a floor band; gate and '
         f'courtyard outside">{DEFS}']
    # ---- left: inside the band
    s.append('<text class="s-lab" x="16" y="24">inside &mdash; one floor band</text>')
    s.append('<rect class="s-box" x="42" y="46" width="420" height="226" rx="3"/>')
    s.append('<text class="s-tag" x="54" y="64">the hall band</text>')
    # fire anchor
    s.append('<circle cx="240" cy="160" r="7" fill="var(--amber)"/>')
    s.append('<text class="s-sub" x="228" y="144" style="fill:var(--amber)">fire</text>')
    # hall camera at a corner
    s.append('<circle cx="428" cy="248" r="6" fill="var(--wood)"/>')
    s.append('<line class="s-hi" x1="422" y1="243" x2="252" y2="167" marker-end="url(#aw)"/>')
    s.append('<text class="s-ttl" x="352" y="264" style="fill:var(--wood)">hall</text>')
    # window + toproom (drawn inside the same rect for compactness)
    s.append('<rect x="286" y="42" width="36" height="8" fill="var(--blue)"/>')
    s.append('<text class="s-sub" x="330" y="52" style="fill:var(--blue)">window</text>')
    s.append('<circle cx="304" cy="120" r="6" fill="var(--wood)"/>')
    s.append('<line class="s-hi" x1="304" y1="113" x2="304" y2="56" marker-end="url(#aw)"/>')
    s.append('<text class="s-ttl" x="316" y="124" style="fill:var(--wood)">toproom</text>')
    s.append('<text class="s-tag" x="316" y="138">aim into the light</text>')
    # seat + table
    s.append('<rect class="s-box" x="96" y="212" width="26" height="18" rx="2" '
             'style="stroke:var(--green)"/>')
    s.append('<text class="s-sub" x="88" y="206" style="fill:var(--green)">seat</text>')
    s.append('<rect class="s-box" x="150" y="196" width="40" height="24" rx="2"/>')
    s.append('<text class="s-sub" x="152" y="190">table</text>')
    s.append('<circle cx="126" cy="218" r="6" fill="var(--wood)"/>')
    s.append('<line class="s-hi" x1="132" y1="215" x2="228" y2="184" marker-end="url(#aw)"/>')
    s.append('<text class="s-ttl" x="180" y="240" style="fill:var(--wood)">seat</text>')
    s.append('<text class="s-tag" x="180" y="254">look across the table, not at it</text>')
    s.append('<text class="s-tag" x="54" y="290">no rotation in the save &mdash; a chair aims '
             'at what it is near</text>')

    # ---- divider
    s.append('<line x1="500" y1="16" x2="500" y2="332" stroke="var(--line)" '
             'stroke-dasharray="3 4"/>')

    # ---- right: outside
    s.append('<text class="s-lab" x="524" y="24">outside &mdash; gate and court</text>')
    s.append('<rect class="s-box" x="560" y="46" width="272" height="160" rx="3"/>')
    s.append('<text class="s-tag" x="572" y="64">the build&#8217;s footprint</text>')
    # gate notch on the south wall
    s.append('<rect x="672" y="200" width="44" height="10" fill="var(--wood)"/>')
    s.append('<text class="s-sub" x="722" y="212" style="fill:var(--wood)">gate</text>')
    s.append('<circle cx="694" cy="262" r="6" fill="var(--wood)"/>')
    s.append('<line class="s-hi" x1="694" y1="255" x2="694" y2="214" marker-end="url(#aw)"/>')
    s.append('<text class="s-ttl" x="706" y="268" style="fill:var(--wood)">gate cam</text>')
    s.append('<text class="s-tag" x="706" y="282">8 m out, aimed at the hall</text>')
    # courtyard cells
    for i in range(3):
        for j in range(2):
            s.append(f'<rect x="{586 + i * 26}" y="{92 + j * 26}" width="24" height="24" '
                     f'fill="none" stroke="var(--green)" stroke-dasharray="3 2"/>')
    s.append('<text class="s-sub" x="586" y="86" style="fill:var(--green)">open sky, '
             'walled on 3 sides</text>')
    s.append('<circle cx="598" cy="130" r="6" fill="var(--wood)"/>')
    s.append('<line class="s-hi" x1="605" y1="127" x2="656" y2="108" marker-end="url(#aw)"/>')
    s.append('<text class="s-ttl" x="592" y="156" style="fill:var(--wood)">court</text>')
    s.append('<text class="s-tag" x="524" y="308">skips are loud: a build with no gates '
             'gets no gate shot</text>')
    s.append('</svg>')
    return "".join(s)


# ------------------------------------------------------------- depth boxes
def svg_depth():
    s = [f'<svg viewBox="0 0 880 312" role="img" aria-label="A camera frame divided '
         f'into the regions the depth metrics read: an exempt bottom band, an '
         f'upper-centre blockage box, and a border framing ring">{DEFS}']
    # the frame
    s.append('<rect class="s-box" x="130" y="28" width="500" height="252" rx="3"/>')
    s.append('<text class="s-lab" x="130" y="20">one frame, as the depth map reads it</text>')
    # border ring (edge_frame zone)
    s.append('<rect x="166" y="52" width="428" height="204" fill="none" '
             'stroke="var(--blue)" stroke-dasharray="4 3"/>')
    s.append('<text class="s-sub" x="176" y="46" style="fill:var(--blue)">outside the dashes: '
             'edge_frame &mdash; near mass here frames the shot</text>')
    # bottom exempt band
    s.append('<rect x="131" y="216" width="498" height="63" '
             'fill="color-mix(in srgb,var(--amber) 14%,transparent)"/>')
    s.append('<text class="s-sub" x="146" y="252" style="fill:var(--amber)">bottom band &mdash; '
             'exempt: a table edge or barrels here is composition</text>')
    # upper-center block box
    s.append('<rect x="255" y="78" width="250" height="114" fill="none" '
             'stroke="var(--wood)" stroke-width="1.6"/>')
    s.append('<text class="s-ttl" x="268" y="100" style="fill:var(--wood)">center_block</text>')
    s.append('<text class="s-sub" x="268" y="118" style="fill:var(--wood)">near-depth pixels '
             'here =</text>')
    s.append('<text class="s-sub" x="268" y="132" style="fill:var(--wood)">a wall across '
             'the eye-line</text>')
    # legend, measured examples
    s.append('<text class="s-lab" x="668" y="60">measured</text>')
    s.append('<rect class="s-box" x="668" y="74" width="196" height="64" rx="3"/>')
    s.append('<text class="s-ttl" x="682" y="96">crystal slab</text>')
    s.append('<text class="s-sub" x="682" y="114">center_block <tspan style="fill:var(--wood);'
             'font-weight:700">0.66</tspan> &rarr; vetoed</text>')
    s.append('<rect class="s-box" x="668" y="150" width="196" height="64" rx="3"/>')
    s.append('<text class="s-ttl" x="682" y="172">barrel cellar</text>')
    s.append('<text class="s-sub" x="682" y="190">center_block <tspan style="fill:var(--green);'
             'font-weight:700">0.17</tspan> &rarr; kept</text>')
    s.append('<text class="s-tag" x="668" y="240">veto: center_block &gt; 0.45</text>')
    s.append('<text class="s-tag" x="668" y="256">fired on 2 duds, 0 keepers</text>')
    s.append('</svg>')
    return "".join(s)


# ------------------------------------------------------------- tiles
def tile(rec_, label, n=None):
    n_html = f'<span class="n">{n}</span>' if n is not None else ""
    return (f'<figure class="tile"><div class="shot">'
            f'<img src="{rec_["src"]}" alt="{esc(label)}" loading="lazy"></div>'
            f'<div class="lab"><b>{esc(label)}</b>{n_html}</div></figure>')


show = "".join(
    tile(r, f'{r.get("label", "")} &middot; {r.get("variant", "")}'.strip(" &middot; "),
         f'{r["aesthetic"]:.2f}' if r.get("aesthetic") else None)
    for r in imgs["show"])

pair_labels = ["from the air &middot; part one&#8217;s framing",
               "from the hall floor &middot; sunrise"]
pair = "".join(tile(r, lab, f'{r["aesthetic"]:.2f}' if r.get("aesthetic") else None)
               for r, lab in zip(imgs["pair"], pair_labels))

light = "".join(
    tile(r, f'{r["variant"].split("_")[1]} &middot; {r["time_of_day"]:.2f}',
         f'{r["aesthetic"]:.2f}' if r.get("aesthetic") else None)
    for r in imgs["light"])

fail_labels = ["thrown 17 m by the throne", "slab &middot; center_block 0.66",
               "walled into a grotto"]
fail = "".join(tile(r, lab) for r, lab in zip(imgs["fail"], fail_labels))

sheet = "".join(f'<img src="{r["src"]}" alt="" loading="lazy">' for r in imgs["sheet"])

STATS = [("436 / 436", "frames planned / captured"), ("25", "structures entered"),
         ("109", "vantages derived"), ("3", "pilot iterations first"),
         ("36 / 36", "labelled pairs the filter got right"),
         ("8.0 &times; 80", "what the judge said, every time")]
stats = "".join(f'<div class="stat"><span class="v">{v}</span>'
                f'<span class="k">{k}</span></div>' for v, k in STATS)

h = imgs["hero"]
hero_name = esc(h.get("label", "")).split(" · ")[0]
hero_cap = (f'{hero_name} &middot; {h.get("pieces", 0):,} pieces &middot; hall vantage '
            f'&middot; sunset {h.get("time_of_day", "")} &middot; '
            f'aesthetic {h.get("aesthetic", 0):.2f}')

fx = imgs["fixed"]
fixed_cap = (f'<b>{esc(fx.get("label", ""))}</b> &middot; {esc(fx.get("variant", ""))} '
             f'&middot; aesthetic {fx.get("aesthetic", 0):.2f}')

TOKENS = open(os.path.join(REPO, "tools", "site", "tokens.css"), encoding="utf-8").read()

rep = {
    "__TOKENS__": TOKENS,
    "__FONT_BODY__": fonts["body"], "__FONT_BODYSB__": fonts["bodysb"],
    "__FONT_MONO__": fonts["mono"], "__FONT_MONOB__": fonts["monob"],
    "__HERO_SRC__": h["src"], "__HERO_CAP__": hero_cap,
    "__SHOW_TILES__": show, "__PAIR_TILES__": pair, "__LIGHT_TILES__": light,
    "__FAIL_TILES__": fail,
    "__FIXED_SRC__": fx["src"], "__FIXED_CAP__": fixed_cap,
    "__SHEET__": sheet, "__STATS__": stats,
    "__SVG_VANTAGES__": svg_vantages(), "__SVG_DEPTH__": svg_depth(),
}
for k, v in rep.items():
    if k not in tpl:
        raise SystemExit(f"placeholder {k} missing from template2")
    tpl = tpl.replace(k, v)

TITLE = "Standing where the builders stood"
DESC = ("The selfie-stick pipeline goes indoors: five vantage recipes computed from a "
        "save file's furniture, four skies over every hall, and the measurements that "
        "taught the judging what a wall is. Part 2 of the series.")

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
        f'<meta property="og:site_name" content="Baseline">\n'
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
    import io
    from PIL import Image
    raw = base64.b64decode(imgs["hero"]["src"].split(",", 1)[1])
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
    top = max(0, (im.height - 630) // 2)
    im = im.crop((0, top, 1200, top + 630))
    og = os.path.join(os.path.dirname(OUT), "og.jpg")
    im.save(og, "JPEG", quality=86, optimize=True, progressive=True)
    print(f"  {og}  {os.path.getsize(og)//1024} KB")
