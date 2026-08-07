#!/usr/bin/env python3
"""Build site/index.html — the Baseline front door.

The site root is the platform's, not any one tool's. Articles live under their own
slug (see tools/selfie-stick/article/build.py); this page is what a stranger reaches
first, and its copy is derived from README.md and docs/baseline-vision-and-boundary.md
rather than invented.

  python tools/site/build_landing.py

Reuses tokens.css and the article's subset fonts so the two pages are visibly one
site. The four thumbnails come from the article build, if it has been run; without
them the page still builds, just without the strip.
"""
import base64, io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE_URL = "https://djcdevelopment.github.io/baseline/"
ART = os.path.join(REPO, "tools", "selfie-stick", "article")
OUT = os.path.join(REPO, "site", "index.html")

TITLE = "Baseline — a toolkit to build a Valheim community on"
DESC = ("Identity, telemetry and testing as first-class parts of a Valheim server "
        "stack instead of afterthoughts. Tools you can run on your own machine "
        "tonight, and honest notes about what is not ready.")

tpl = open(os.path.join(HERE, "landing.html"), encoding="utf-8").read()
tokens = open(os.path.join(HERE, "tokens.css"), encoding="utf-8").read()

fonts = {}
for k in ("body", "bodysb", "mono", "monob"):
    with open(os.path.join(ART, "fonts", k + ".woff2"), "rb") as fh:
        fonts[k] = "data:font/woff2;base64," + base64.b64encode(fh.read()).decode()

# A small, honest sample of the article's own output. Falls back to nothing rather
# than failing the whole page, since the landing copy does not depend on it.
strip = ""
imgs_path = os.path.join(ART, "build", "images.json")
if os.path.exists(imgs_path):
    from PIL import Image
    imgs = json.load(open(imgs_path, encoding="utf-8"))
    picks = [imgs["hero"]] + imgs["feature"][:3]
    out = []
    for r in picks:
        raw = base64.b64decode(r["src"].split(",", 1)[1])
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im = im.resize((320, round(im.height * 320 / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=74, method=6)
        uri = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
        out.append(f'<img src="{uri}" alt="" loading="lazy">')
    strip = "".join(out)
else:
    print("  ! no article images.json — building without the thumbnail strip")

for k, v in {"__TOKENS__": tokens, "__STRIP__": strip,
             "__FONT_BODY__": fonts["body"], "__FONT_BODYSB__": fonts["bodysb"],
             "__FONT_MONO__": fonts["mono"], "__FONT_MONOB__": fonts["monob"]}.items():
    if k not in tpl:
        raise SystemExit(f"placeholder {k} missing from landing.html")
    tpl = tpl.replace(k, v)

doc = ('<!doctype html>\n<html lang="en">\n<head>\n'
       '<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
       f'<title>{TITLE}</title>\n'
       f'<meta name="description" content="{DESC}">\n'
       '<meta name="author" content="Derek Ciula">\n'
       f'<link rel="canonical" href="{BASE_URL}">\n'
       '<meta property="og:type" content="website">\n'
       '<meta property="og:site_name" content="Baseline">\n'
       f'<meta property="og:title" content="{TITLE}">\n'
       f'<meta property="og:description" content="{DESC}">\n'
       f'<meta property="og:url" content="{BASE_URL}">\n'
       '<meta name="twitter:card" content="summary">\n'
       '<style>*{box-sizing:border-box}</style>\n'
       '</head>\n<body>\n' + tpl + '\n</body>\n</html>\n')

# Pure ASCII, so a host serving without a charset cannot mojibake the dashes,
# arrows and middots.
doc = doc.encode("ascii", "xmlcharrefreplace").decode("ascii")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="ascii").write(doc)
print(f"  {OUT}  {len(doc)/1024:.0f} KB  ascii={doc.isascii()}")
