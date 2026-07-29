# Provenance — camera-gallery raw material

## Origin

This directory holds the recovered raw material for the `camera-gallery`
workbench tool, landed 2026-07-29.

Every file here, except this `PROVENANCE.md` and `.gitattributes`, is a
byte-exact copy from the public comfy archive repository
(`github.com/djcdevelopment/comfy`) at commit
`ae81c83bee1a8077f15c211055dd0667ca50b469` (retrieved 2026-07-29).

These same bytes were part of this repository itself until the 2026-07-21
prune commit `d75ffb2` ("Prune 279 of 1045 tracked files after a
Gemini-backed audit"). The last baseline ref that contains them is `57654fd`
(which equals `d75ffb2^`). The archive tree `handoffs/` at `ae81c83` is
tree-identical to baseline's `57654fd:handoffs` (tree
`5d7b29bcd5d31b89a8b06785af11a8eb1de9743b`), so the archive HEAD and the
pre-prune baseline state are the same source.

## Mapping and byte-identity

The mapping rule: `recipes/camera-gallery/<basename>` is the blob
`ae81c83bee1a8077f15c211055dd0667ca50b469:handoffs/<basename>`.

The 9 recovered files:

- segment-1-emit-waypoints.py
- segment-1-waypoints-from-world.md
- segment-2-get-into-the-world.md
- segment-3-flight-path-mod.md
- segment-4-runner.md
- segment-4-video-to-gallery.md
- video_to_gallery.py
- timeline.sample.json
- waypoints.sample.json

To verify byte-identity, for any `<basename>` above:

```
git rev-parse "HEAD:recipes/camera-gallery/<basename>"
```

must equal

```
git rev-parse "ae81c83bee1a8077f15c211055dd0667ca50b469:handoffs/<basename>"
```

Source blobs contain LF line endings. The `.gitattributes` in this directory
is `* -text` so the bytes stay pinned on every platform.

## What did not land, and why

`valheim-camera-proof/` (a 746-line working BepInEx proof-of-concept plugin,
C#) and `handoffs/README.md` (the archive tree's own index) remain
archive-only at `github.com/djcdevelopment/comfy/tree/main/handoffs/`.

This exclusion is deliberate. This landing paves the path for community
claiming task CG-1 (revive segment 1 against ComfyStewardView and produce a
`waypoints.sample.json` from a current build) without doing it. The
proof-of-concept kit is fetched from the archive by whoever takes segment 3.

## Segment status

- Segment 1 is working code: a 69-line stdlib Python script driving
  ComfyStewardView's API.
- Segments 2, 3, and 4 briefs are specifications, not code.
- Segment 3 (the actual flight-path mod) has no code anywhere and is the
  real gap.
- `video_to_gallery.py` is real segment-4 code with a no-ffmpeg dry-run
  mode.

## Privacy

`timeline.sample.json` and `waypoints.sample.json` attribute real
coordinates and real builder names from an Era 16 world. These exact bytes
are already public in the comfy archive; landing them here adds no new
exposure. Do not extend them with new player data, and read the
camera-gallery workbench one-pager's privacy section before publishing any
gallery.

## Editing rule

Files in this directory must not be edited in place without recording the
divergence in this `PROVENANCE.md`. One exception is defined by CG-1 itself:
a future `waypoints.sample.json` regenerated against a current
ComfyStewardView build replaces the archived sample — record the replacement
here when it happens.

## Original license (MIT)

These files originate in the comfy repository under the MIT License. The
surrounding baseline repository is public source (BSL 1.1); these copies
retain their original MIT terms, reproduced verbatim below.

```
MIT License

Copyright (c) 2026 Comfy contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
