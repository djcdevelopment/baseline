# article

The public write-up of the selfie-stick pipeline, published to GitHub Pages at
<https://djcdevelopment.github.io/baseline/selfie-stick/>.

The site root belongs to Baseline as a whole ([`tools/site/`](../../site/)) — this is
one tool's story and lives under its own slug.

It is an article, not a tutorial. It does not ask the reader to reproduce anything —
the BepInEx half lives outside this repo and the world cache is one person's local
machine, so a replication guide would be a promise nobody could keep. What it does is
show the photographs, explain the arithmetic that framed them, and print what each
stage of the pipeline actually emits.

## Build it

```bash
python tools/selfie-stick/article/curate.py            # reads ../out/gallery
python tools/selfie-stick/article/build.py --target pages
```

`curate.py` picks the hero, the orbit and light strips, the feature grid and the
contact sheet out of `../out/gallery/index.json`, crops the debug HUD off every frame,
re-encodes them small, and writes `build/images.json`. `build.py` inlines those plus
the fonts, the shared [`tools/site/tokens.css`](../../site/tokens.css) and the five
diagrams into `template.html`, then writes `site/selfie-stick/index.html` and its
`og.jpg`.

`--target artifact` emits body content only, for a host that owns the `<head>`.

Colours and type come from `tools/site/tokens.css`, which the landing page uses too —
edit them there, not here, or the two pages drift apart.

## What is deliberate

- **Self-contained.** One file, no CDN, no external requests, no dependency on the
  gallery host. It works as an attachment.
- **ASCII only.** Structure names carry `·` and the diagrams carry `θ`, `−` and
  arrows; every one is emitted as a numeric entity so a host serving without a
  charset cannot mojibake them.
- **No coordinates, no creator IDs.** Not in the prose, not in the captions, not in
  the code samples — those show `·····` with a visible note. `../out/` is gitignored
  for the same reason: it attributes real builds to real people.
- **The debug HUD is cropped** from every frame, top 40 px.

## Fonts

`fonts/` holds four subset faces, built from the full originals with `fonttools`:

| file | face | licence |
| --- | --- | --- |
| `body.woff2`, `bodysb.woff2` | Open Sans Regular / SemiBold | Apache-2.0 |
| `mono.woff2`, `monob.woff2` | Source Code Pro Regular / Bold | SIL OFL 1.1 |

Both licences permit redistribution and embedding, which is why these are inlined and
the Windows system faces are not. Subsetting is to printable ASCII plus the handful of
symbols the diagrams use; each file is under 11 KB. To rebuild them, subset with
`--text=` over that charset and `--flavor=woff2`.

## Regenerating after a new capture run

`site/selfie-stick/index.html` is a build output, but it is committed — it is what
Pages serves and it is the only surviving copy of the curated images once `build/` is
cleaned. Re-run both scripts and commit the result; do not hand-edit it.

The landing page's thumbnail strip is cut from the same `build/images.json`, so
re-run `python tools/site/build_landing.py` after a new capture run too.
