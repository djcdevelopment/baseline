# site

Sources for the public GitHub Pages site at <https://djcdevelopment.github.io/baseline/>.

The site root is **Baseline as a whole** — what a stranger reaches first. Individual
tools and write-ups live under their own slug beneath it, never at `/`.

| | |
| --- | --- |
| `landing.html` | template for the front door |
| `build_landing.py` | builds `site/index.html` |
| `tokens.css` | **shared** colour and type tokens for every page under `site/` |
| `../../corpus/audiences.json` | shared audience vocabulary used to build the front-door lenses |

```bash
python tools/site/build_landing.py
python tools/corpus/build.py
```

## Where the copy comes from

The landing copy is derived from [`README.md`](../../README.md) and
[`docs/baseline-vision-and-boundary.md`](../../docs/baseline-vision-and-boundary.md),
which is the canonical product statement. **Change those first, then mirror here** —
this page is a rendering of the position, not a second place to invent one.

Two rules it inherits from the boundary doc:

- Nothing HEARTH or Mechnet appears here. No operator-fleet endpoints, keys, or
  `C:\work\commandcenter` paths. This page is community-facing.
- Every capability claim says what the thing does *today*. The "what is not open yet"
  section is load-bearing, not a disclaimer to trim.

## tokens.css is the single source

Both this page and `tools/selfie-stick/article/build.py` inline `tokens.css` at build
time, so the two cannot drift. The palette is lifted from the Community Workbench so
the public site reads as one surface with the tool that already exists. Edit colours
there and rebuild both:

```bash
python tools/site/build_landing.py
python tools/selfie-stick/article/build.py --target pages
```

## What is published

`.github/workflows/pages.yml` uploads `site/` and nothing else, so `docs/`,
`handoffs/` and `fieldlab/` stay off the web even though they are readable on GitHub.
`site/.nojekyll` stops Pages running Jekyll over the output.

Pages under `site/` are self-contained: fonts, images and styles are inlined, no CDN,
no external requests. Output is pure ASCII so a host serving without a charset cannot
mojibake it.

The audience pages, explorer, update page, RSS/JSON feeds, and machine index are built
by `tools/corpus/build.py`. They are projections, not editorial sources; see
[`corpus/README.md`](../../corpus/README.md) for the reconstruction contract.
