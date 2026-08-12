#!/usr/bin/env python3
"""Build site/index.html — the Baseline fleet-hub front door.

The site root is the hub's, not any one product's. Articles live under their own
slug (see tools/selfie-stick/article/build.py); this page is what a stranger reaches
first, and its copy is derived from README.md and docs/baseline-vision-and-boundary.md
rather than invented.

  python tools/site/build_landing.py

Reuses tokens.css and the article's subset fonts so the two pages are visibly one
site. The four thumbnails come from the article build, if it has been run; without
them the page still builds, just without the strip.
"""
import base64, html, io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE_URL = "https://djcdevelopment.github.io/baseline/"
ART = os.path.join(REPO, "tools", "selfie-stick", "article")
OUT = os.path.join(REPO, "site", "index.html")
AUDIENCES = os.path.join(REPO, "corpus", "audiences.json")

TITLE = "Baseline — the Valheim project fleet hub"
DESC = ("The durable repository map, decisions, evidence, public corpus, and discovery "
        "surfaces for a fleet of sovereign Valheim projects.")

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

audience_doc = json.load(open(AUDIENCES, encoding="utf-8"))
audiences = "".join(
    '<a class="role-card" href="for/{id}/"><b>{label}</b><span>{question}</span></a>'.format(
        id=html.escape(role["id"], quote=True),
        label=html.escape(role["short_label"]),
        question=html.escape(role["question"]),
    )
    for role in sorted(audience_doc["roles"], key=lambda role: role["order"])
)

for k, v in {"__TOKENS__": tokens, "__STRIP__": strip, "__AUDIENCES__": audiences,
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
