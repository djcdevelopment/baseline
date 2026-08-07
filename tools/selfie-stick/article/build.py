#!/usr/bin/env python3
"""Assemble the article: inject fonts, images and diagrams into the template.

Two targets, same body:

  --target pages     a complete standalone document (doctype, charset, viewport,
                     description, Open Graph) written to site/index.html, plus the
                     og.jpg that Discord and Slack unfurl. This is what ships.
  --target artifact  body content only, for hosts that own the <head> themselves.

Run curate.py first — it produces build/images.json from the local gallery output.

  python tools/selfie-stick/article/curate.py
  python tools/selfie-stick/article/build.py --target pages
"""
import argparse, base64, json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SITE_URL = "https://djcdevelopment.github.io/baseline/"

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--target", choices=["pages", "artifact"], default="pages")
ap.add_argument("--images", default=os.path.join(HERE, "build", "images.json"))
ap.add_argument("--out", default=None, help="defaults to site/index.html for pages")
args = ap.parse_args()

if not os.path.exists(args.images):
    raise SystemExit(f"no {args.images} — run curate.py first")

OUT = args.out or (os.path.join(REPO, "site", "index.html")
                   if args.target == "pages"
                   else os.path.join(HERE, "build", "article-body.html"))

imgs = json.load(open(args.images, encoding="utf-8"))
tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()

# The four subset faces live next to this script; they are OFL / Apache-2.0 and
# redistributable, which is why they can be inlined into a public page at all.
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
    return html.escape(s, quote=False)


# ---------------------------------------------------------------- funnel
def svg_funnel():
    st = [("3,146,002", "building pieces", "flat bag of objects\nin the save file"),
          ("1,833", "structures", "3-D connected\ncomponents"),
          ("161", "photographed", "top of the\nranked list"),
          ("1,411", "frames", "6 per structure,\n54 sessions"),
          ("60", "worth showing", "top of the\nscored list")]
    verbs = ["cluster", "rank + cut", "fly the plan", "score each frame"]
    s = [f'<svg viewBox="0 0 880 196" role="img" aria-label="Funnel from 3.1 million '
         f'building pieces down to 60 photographs worth showing">{DEFS}']
    for i, (num, lab, sub) in enumerate(st):
        x = 20 + i * 172
        s.append(f'<rect class="s-box" x="{x}" y="46" width="152" height="104" rx="3"/>')
        s.append(f'<text class="s-num" x="{x+14}" y="80">{num}</text>')
        s.append(f'<text class="s-ttl" x="{x+14}" y="100">{lab}</text>')
        for j, line in enumerate(sub.split("\n")):
            s.append(f'<text class="s-sub" x="{x+14}" y="{120+j*14}">{line}</text>')
        if i < 4:
            ax = x + 152
            s.append(f'<line class="s-arr" x1="{ax+3}" y1="98" x2="{ax+15}" y2="98" '
                     f'marker-end="url(#a)"/>')
            s.append(f'<text class="s-tag" x="{ax+9}" y="34" text-anchor="middle">'
                     f'{verbs[i]}</text>')
    s.append('<text class="s-lab" x="20" y="182">every stage discards most of the last</text>')
    s.append('</svg>')
    return "".join(s)


# ---------------------------------------------------------------- data flow
def svg_flow():
    s = [f'<svg viewBox="0 0 880 452" role="img" aria-label="Pipeline across three lanes: '
         f'offline planning in Python, in-game capture in C sharp, and delivery">{DEFS}']

    lanes = [("offline &middot; python", 24, 128, "var(--blue)"),
             ("in-game &middot; bepinex c#", 172, 148, "var(--wood)"),
             ("delivery &middot; python + browser", 340, 100, "var(--green)")]
    for title, y, h, col in lanes:
        s.append(f'<rect class="s-lane" x="10" y="{y}" width="860" height="{h}" rx="4"/>')
        s.append(f'<text class="s-lab" x="22" y="{y+18}" style="fill:{col}">{title}</text>')

    def box(x, y, w, h, title, sub="", hi=False):
        st = ' style="stroke:var(--wood)"' if hi else ''
        o = [f'<rect class="s-box" x="{x}" y="{y}" width="{w}" height="{h}" rx="3"{st}/>',
             f'<text class="s-ttl" x="{x+11}" y="{y+22}">{title}</text>']
        for j, ln in enumerate(sub.split("\n")) if sub else []:
            o.append(f'<text class="s-sub" x="{x+11}" y="{y+39+j*13}">{ln}</text>')
        return "".join(o)

    def arrow(x1, y1, x2, y2, hi=False):
        c, m = ("s-hi", "aw") if hi else ("s-arr", "a")
        return (f'<line class="{c}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'marker-end="url(#{m})"/>')

    # lane 1
    s.append(box(22, 44, 150, 66, "world cache", "ComfyStewardView\nDuckDB, read-only"))
    s.append(arrow(176, 77, 196, 77))
    s.append(box(202, 44, 158, 66, "scan_clusters.py", "union-find on a\n16 m grid"))
    s.append(arrow(364, 77, 384, 77))
    s.append(box(390, 44, 140, 66, "clusters.json", "1,833 records\nbox + stats", hi=True))
    s.append(arrow(534, 77, 554, 77))
    s.append(box(560, 44, 148, 66, "plan_shots.py", "trig from the\nbounding box"))
    s.append(arrow(712, 77, 732, 77))
    s.append(box(738, 44, 122, 66, "shotplan.tsv", "6 lines per\nstructure", hi=True))

    # lane 1 -> 2
    s.append(arrow(799, 114, 799, 190, hi=True))
    s.append('<text class="s-tag" x="808" y="152">copied into</text>')
    s.append('<text class="s-tag" x="808" y="164">BepInEx/config</text>')

    # lane 2
    s.append(box(22, 192, 168, 66, "Invoke-OrbitCapture", "arms the mod,\nlaunches Steam"))
    s.append(arrow(194, 225, 214, 225))
    s.append(box(220, 192, 132, 66, "AutoBoot", "load world,\nwait for spawn"))
    s.append(arrow(356, 225, 376, 225))
    s.append(box(382, 192, 150, 66, "RunShotPlan", "teleport &rarr; aim &rarr;\nset sun + weather"))
    s.append(arrow(536, 225, 556, 225))
    s.append(box(562, 192, 138, 66, "CaptureHere", "hide chrome,\nraycast, shoot"))
    s.append(arrow(704, 225, 724, 225))
    s.append(box(730, 192, 130, 66, "png + receipt", "one jsonl line\nper frame", hi=True))
    s.append(f'<path class="s-arr" d="M 632 264 L 632 288 L 300 288 L 300 264" '
             f'marker-end="url(#a)"/>')
    s.append('<text class="s-tag" x="466" y="302" text-anchor="middle">'
             'next shot &mdash; 1,411 times, unattended</text>')

    # lane 2 -> 3
    s.append(arrow(795, 262, 795, 358, hi=True))

    # lane 3
    s.append(box(22, 360, 178, 66, "build_valheim_index.py", "join receipts to files,\n"
                                                             "resize to webp"))
    s.append(arrow(204, 393, 224, 393))
    s.append(box(230, 360, 150, 66, "score_images.py", "CLIP ViT-L/14 +\naesthetic head"))
    s.append(arrow(384, 393, 404, 393))
    s.append(box(410, 360, 140, 66, "index.json", "1,411 frames,\nranked", hi=True))
    s.append(arrow(554, 393, 574, 393))
    s.append(box(580, 360, 150, 66, "gallery", "static html,\nfilter + lightbox"))
    s.append(f'<line class="s-arr" x1="734" y1="393" x2="754" y2="393" marker-end="url(#a)"/>')
    s.append(box(760, 360, 100, 66, "a human", "picks the\nkeepers"))
    s.append('</svg>')
    return "".join(s)


# ---------------------------------------------------------------- contracts
def svg_contracts():
    cards = [
        ("clusters.json", "scan &rarr; planner", "var(--blue)",
         ["cluster_id", "center_x/y/z", "size_x/y/z", "min_y  max_y", "pieces  score",
          "distinct_creators", "region  sky"],
         "one row per structure,\nwith a true 3-D box"),
        ("shotplan.tsv", "planner &rarr; game", "var(--wood)",
         ["cluster_id  shot", "cam_x cam_y cam_z", "yaw  pitch", "env  time", "aim_x/y/z",
          "label"],
         "tab-separated on purpose:\nthe plugin has no JSON parser"),
        ("receipts.jsonl", "game &rarr; index", "var(--amber)",
         ["run  index  file", "planned {x,y,z}", "placed  {x,y,z}", "lens    {x,y,z}",
          "occluded", "pieces_near_aim", "at"],
         "asked-for vs actually-done,\nwhich is what makes it auditable"),
        ("index.json", "index &rarr; gallery", "var(--green)",
         ["id  run  variant", "aesthetic", "label  kind", "pieces  height_m", "builders",
          "published: false"],
         "everything the page needs,\nnothing it should not have"),
    ]
    s = [f'<svg viewBox="0 0 880 350" role="img" aria-label="Four file contracts and the '
         f'fields each one carries">{DEFS}']
    for i, (name, hop, col, fields, note) in enumerate(cards):
        x = 8 + i * 220
        s.append(f'<rect class="s-box" x="{x}" y="30" width="196" height="238" rx="3"/>')
        s.append(f'<rect x="{x}" y="30" width="196" height="3" rx="1.5" fill="{col}"/>')
        s.append(f'<text class="s-tag" x="{x+13}" y="52" style="fill:{col}">{hop}</text>')
        s.append(f'<text class="s-ttl" x="{x+13}" y="72">{name}</text>')
        s.append(f'<line x1="{x+13}" y1="84" x2="{x+183}" y2="84" stroke="var(--line)"/>')
        for j, f in enumerate(fields):
            s.append(f'<text class="s-sub" x="{x+13}" y="{102+j*17}" '
                     f'style="font-size:10px">{f}</text>')
        for j, ln in enumerate(note.split("\n")):
            s.append(f'<text class="s-tag" x="{x+13}" y="{232+j*13}">{ln}</text>')
        if i < 3:
            s.append(f'<line class="s-arr" x1="{x+200}" y1="149" x2="{x+214}" y2="149" '
                     f'marker-end="url(#a)"/>')
    s.append('<text class="s-lab" x="8" y="300">no shared memory &middot; no rpc &middot; '
             'no clock &mdash; every handoff is a file you can open, diff and replay</text>')
    s.append('<text class="s-sub" x="8" y="326">Different languages, different processes, '
             'no shared clock &mdash; which is why every stage re-runs on its own.</text>')
    s.append('</svg>')
    return "".join(s)


# ---------------------------------------------------------------- stack
def svg_stack():
    rows = [("delivery", "static HTML + vanilla JS", "no framework, no build step, "
             "no server &mdash; a file you can open", "var(--green)"),
            ("scoring", "PyTorch &middot; open_clip &middot; CLIP ViT-L/14 &middot; "
             "LAION aesthetic head", "already on the box for an unrelated photo library",
             "var(--violet)"),
            ("naming", "vision model over the photograph itself",
             "because the prefab table is hashes, not words", "var(--blue)"),
            ("in-game", "BepInEx 5 &middot; Harmony &middot; Unity &middot; C# net472",
             "1,787 lines &mdash; teleport, aim, sun, weather, shutter", "var(--wood)"),
            ("orchestration", "PowerShell 5.1", "arms the plugin, launches Steam, "
             "polls the receipt file", "var(--amber)"),
            ("planning", "Python 3 &middot; DuckDB &middot; stdlib math",
             "union-find clustering and secondary-school trig", "var(--blue)"),
            ("storage", "Valheim world save &rarr; ComfyStewardView DuckDB cache",
             "read-only; the world is never re-parsed or written", "var(--muted)")]
    s = [f'<svg viewBox="0 0 880 {36+len(rows)*44}" role="img" aria-label="Technology '
         f'stack from world storage up to static delivery">{DEFS}']
    for i, (lane, tech, note, col) in enumerate(rows):
        y = 10 + i * 44
        s.append(f'<rect class="s-box" x="8" y="{y}" width="864" height="38" rx="3"/>')
        s.append(f'<rect x="8" y="{y}" width="3" height="38" rx="1.5" fill="{col}"/>')
        s.append(f'<text class="s-tag" x="26" y="{y+16}" style="fill:{col}">{lane}</text>')
        s.append(f'<text class="s-sub" x="26" y="{y+31}" style="font-size:11px;'
                 f'fill:var(--ink)">{tech}</text>')
        s.append(f'<text class="s-sub" x="470" y="{y+24}">{note}</text>')
    s.append('</svg>')
    return "".join(s)


# ---------------------------------------------------------------- geometry
def svg_geom():
    s = [f'<svg viewBox="0 0 880 342" role="img" aria-label="Camera framing geometry: '
         f'elevation view showing standoff distance and field of view, and plan view '
         f'showing four bearings offset 45 degrees from the long axis">{DEFS}']
    # ---- elevation view
    s.append('<text class="s-lab" x="20" y="24">elevation &mdash; how far back</text>')
    s.append('<line x1="30" y1="256" x2="470" y2="256" stroke="var(--line2)" '
             'stroke-width="1.2"/>')
    s.append('<text class="s-tag" x="30" y="272">ground &mdash; i.e. the lowest '
             'foundation piece</text>')
    # subject box
    s.append('<rect class="s-box" x="292" y="156" width="84" height="100" rx="2" '
             'style="fill:var(--panel);stroke:var(--wood)"/>')
    s.append('<text class="s-tag" x="334" y="236" text-anchor="middle">subject</text>')
    # subject brace
    s.append('<line x1="392" y1="156" x2="392" y2="256" stroke="var(--wood)" '
             'stroke-width="1.2"/>')
    s.append('<line x1="387" y1="156" x2="397" y2="156" stroke="var(--wood)"/>')
    s.append('<line x1="387" y1="256" x2="397" y2="256" stroke="var(--wood)"/>')
    s.append('<text class="s-sub" x="402" y="200" style="fill:var(--wood)">max(size_y,</text>')
    s.append('<text class="s-sub" x="402" y="214" style="fill:var(--wood)">'
             'min(size_x,size_z))</text>')
    # camera
    s.append('<circle cx="86" cy="118" r="6" fill="var(--wood)"/>')
    s.append('<text class="s-ttl" x="72" y="104" style="fill:var(--wood)">camera</text>')
    # framing lines to top and bottom of subject
    s.append('<line x1="86" y1="118" x2="334" y2="156" stroke="var(--wood)" '
             'stroke-width="1.1" opacity=".85"/>')
    s.append('<line x1="86" y1="118" x2="334" y2="256" stroke="var(--wood)" '
             'stroke-width="1.1" opacity=".85"/>')
    s.append('<path d="M 150 128 A 66 66 0 0 1 152 168" fill="none" stroke="var(--wood)" '
             'stroke-width="1.1"/>')
    s.append('<text class="s-sub" x="176" y="126" style="fill:var(--wood)">fov_v 65&deg;</text>')
    # sight line, labelled short — the formula lives in the legend below, so nothing
    # is set at an angle across the subject box
    s.append('<line x1="86" y1="118" x2="334" y2="206" stroke="var(--line2)" '
             'stroke-width="1" stroke-dasharray="4 3"/>')
    s.append('<text class="s-sub" x="248" y="172" style="fill:var(--wood)">d</text>')
    # horizontal + elevation angle
    s.append('<line x1="86" y1="118" x2="270" y2="118" stroke="var(--line)" '
             'stroke-width="1" stroke-dasharray="3 3"/>')
    s.append('<path d="M 146 118 A 60 60 0 0 0 143 139" fill="none" stroke="var(--blue)" '
             'stroke-width="1.2"/>')
    s.append('<text class="s-sub" x="152" y="136" style="fill:var(--blue)">&theta;</text>')
    # clearance floor, kept clear of the subject box and the framing lines
    s.append('<line x1="150" y1="243" x2="286" y2="243" stroke="var(--amber)" '
             'stroke-width="1" stroke-dasharray="3 3"/>')
    s.append('<text class="s-tag" x="150" y="238" style="fill:var(--amber)">'
             'floor: base + 3 m</text>')
    # legend
    s.append('<text class="s-sub" x="30" y="292" style="fill:var(--wood)">'
             'd = (subject / 2) / tan(fov_v / 2) &times; margin</text>')
    s.append('<text class="s-sub" x="30" y="308" style="fill:var(--blue)">'
             '&theta; = max(18&deg;, min(40&deg;, 40&deg; &minus; 60&deg;&middot;size_y/width))'
             '</text>')
    s.append('<text class="s-tag" x="30" y="324">tilt down on flat things, '
             'level off on tall ones</text>')

    # ---- divider
    s.append('<line x1="506" y1="16" x2="506" y2="326" stroke="var(--line)" '
             'stroke-dasharray="3 4"/>')

    # ---- plan view
    s.append('<text class="s-lab" x="536" y="24">plan &mdash; which way round</text>')
    cx, cy, r = 700, 168, 92
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="var(--line)" '
             f'stroke-dasharray="3 4"/>')
    s.append(f'<rect class="s-box" x="{cx-62}" y="{cy-26}" width="124" height="52" rx="2" '
             f'style="stroke:var(--wood)"/>')
    s.append(f'<line x1="{cx-72}" y1="{cy}" x2="{cx+72}" y2="{cy}" stroke="var(--blue)" '
             f'stroke-width="1" stroke-dasharray="5 3"/>')
    s.append(f'<text class="s-tag" x="{cx}" y="{cy+42}" text-anchor="middle" '
             f'style="fill:var(--blue)">long axis</text>')
    d = round(r * 0.7071)
    pts = [(cx + d, cy - d, "orbit1", "45&deg;", "start"),
           (cx + d, cy + d, "orbit2", "135&deg;", "start"),
           (cx - d, cy + d, "orbit3", "225&deg;", "end"),
           (cx - d, cy - d, "orbit4", "315&deg;", "end")]
    for px, py, lab, deg, anchor in pts:
        s.append(f'<line x1="{px}" y1="{py}" x2="{cx}" y2="{cy}" stroke="var(--wood)" '
                 f'stroke-width="1" opacity=".55"/>')
        s.append(f'<circle cx="{px}" cy="{py}" r="5" fill="var(--wood)"/>')
        ox = 11 if anchor == "start" else -11
        s.append(f'<text class="s-sub" x="{px+ox}" y="{py-2}" text-anchor="{anchor}" '
                 f'style="fill:var(--wood);font-size:10px">{lab}</text>')
        s.append(f'<text class="s-tag" x="{px+ox}" y="{py+11}" text-anchor="{anchor}">'
                 f'{deg}</text>')
    s.append('<text class="s-sub" x="536" y="300">every bearing sits 45&deg; off the long '
             'axis</text>')
    s.append('<text class="s-tag" x="536" y="318">so each frame shows a long face and a '
             'short one together</text>')
    s.append('</svg>')
    return "".join(s)


# ---------------------------------------------------------------- tiles
def tile(rec, alt):
    env = rec.get("environment", "")
    return (f'<figure class="tile"><div class="shot">'
            f'<img src="{rec["src"]}" alt="{esc(alt)}" loading="lazy"></div>'
            f'<div class="lab"><b>{esc(rec.get("label", ""))}</b>'
            f'<span class="n">{rec["aesthetic"]:.2f}</span></div></figure>')


def tiles(key, alt_fmt):
    return "".join(tile(r, alt_fmt.format(**r)) for r in imgs[key])


ALT = "A player-built Valheim structure photographed from a planned camera position"

feature = "".join(
    f'<figure class="tile"><div class="shot"><img src="{r["src"]}" '
    f'alt="{esc(r.get("label", "") or ALT)} — {ALT.lower()}" loading="lazy"></div>'
    f'<div class="lab"><b>{esc(r.get("label", ""))}</b>'
    f'<span class="n">{r["aesthetic"]:.2f}</span></div></figure>'
    for r in imgs["feature"])

orbit = "".join(
    f'<figure class="tile"><div class="shot"><img src="{r["src"]}" '
    f'alt="The same structure seen from bearing {r["variant"]}" loading="lazy"></div>'
    f'<div class="lab"><b>{r["variant"]}</b>'
    f'<span class="n">{r["aesthetic"]:.2f}</span></div></figure>'
    for r in imgs["orbit"])

# Label straight off the record's own time_of_day so the caption can never drift
# from the frame it sits under.
light = "".join(
    f'<figure class="tile"><div class="shot"><img src="{r["src"]}" '
    f'alt="The same structure at {r["variant"].split("_")[0]}" loading="lazy"></div>'
    f'<div class="lab"><b>{r["variant"].split("_")[0]} &middot; '
    f'{r["time_of_day"]:.2f}</b>'
    f'<span class="n">{r["aesthetic"]:.2f}</span></div></figure>'
    for r in imgs["light"])

sheet = "".join(f'<img src="{r["src"]}" alt="" loading="lazy">' for r in imgs["sheet"])

STATS = [("3,146,002", "building pieces scanned"), ("1,833", "structures found"),
         ("161", "structures photographed"), ("1,411", "frames captured"),
         ("54", "unattended sessions"), ("0", "shots framed by hand")]
stats = "".join(f'<div class="stat"><span class="v">{v}</span>'
                f'<span class="k">{k}</span></div>' for v, k in STATS)

h = imgs["hero"]
# The naming step already suffixes big labels with their piece count, so strip it
# rather than print the same number twice in one line.
hero_name = esc(h["label"]).split(" · ")[0]
hero_cap = (f'{hero_name} &middot; {h["pieces"]:,} pieces &middot; '
            f'{h["builders"]} builder{"s" if h["builders"] != 1 else ""} &middot; '
            f'bearing orbit1 &middot; time of day {h["time_of_day"]} &middot; '
            f'aesthetic {h["aesthetic"]:.2f}')

rep = {
    "__FONT_BODY__": fonts["body"], "__FONT_BODYSB__": fonts["bodysb"],
    "__FONT_MONO__": fonts["mono"], "__FONT_MONOB__": fonts["monob"],
    "__HERO_SRC__": h["src"], "__HERO_CAP__": hero_cap,
    "__FEATURE_TILES__": feature, "__ORBIT_TILES__": orbit, "__LIGHT_TILES__": light,
    "__SHEET__": sheet, "__STATS__": stats,
    "__SVG_FUNNEL__": svg_funnel(), "__SVG_FLOW__": svg_flow(),
    "__SVG_CONTRACTS__": svg_contracts(), "__SVG_STACK__": svg_stack(),
    "__SVG_GEOM__": svg_geom(),
}
for k, v in rep.items():
    if k not in tpl:
        raise SystemExit(f"placeholder {k} missing from template")
    tpl = tpl.replace(k, v)

TITLE = "Photographing a world nobody had time to look at"
DESC = ("Three million Valheim building pieces, 1,833 structures, and 1,411 photographs "
        "framed entirely by arithmetic. How the selfie-stick pipeline works, and what "
        "it found.")

if args.target == "pages":
    # The body carries its own <title> for hosts that own the <head>; in a standalone
    # document that tag belongs upstairs, so lift it rather than emit two.
    tpl = tpl.replace(f"<title>{TITLE}</title>\n", "", 1)
    tpl = (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{TITLE}</title>\n'
        f'<meta name="description" content="{DESC}">\n'
        '<meta name="author" content="Derek Ciula">\n'
        '<meta property="og:type" content="article">\n'
        f'<meta property="og:title" content="{TITLE}">\n'
        f'<meta property="og:description" content="{DESC}">\n'
        f'<meta property="og:url" content="{SITE_URL}">\n'
        f'<meta property="og:image" content="{SITE_URL}og.jpg">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<style>*{box-sizing:border-box}</style>\n'
        '</head>\n<body>\n' + tpl + '\n</body>\n</html>\n')

# Emit pure ASCII regardless of target. Structure names carry U+00B7 and the diagrams
# carry theta, arrows and minus; a host that serves this without a charset would render
# those as mojibake, and the artifact target cannot declare one.
tpl = tpl.encode("ascii", "xmlcharrefreplace").decode("ascii")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="ascii").write(tpl)
print(f"  {OUT}  {len(tpl)/1024/1024:.2f} MB  ascii={tpl.isascii()}")

if args.target == "pages":
    # Link unfurls need a real file at an absolute URL, so the hero is re-cut to the
    # 1.91:1 that Discord, Slack and Twitter all crop to anyway.
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

    # Pages runs Jekyll by default, which ignores files and dirs beginning with _
    # and can rewrite what it does serve. Opt out.
    nj = os.path.join(os.path.dirname(OUT), ".nojekyll")
    open(nj, "w").close()
    print(f"  {nj}")
