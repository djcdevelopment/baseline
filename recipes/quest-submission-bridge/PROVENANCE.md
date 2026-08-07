# Provenance — quest-submission-bridge raw material

## Origin

This directory holds the recovered back-half raw material for the
`quest-submission-bridge` workbench tool, landed 2026-07-29.

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

The mapping rule: `recipes/quest-submission-bridge/<p>` is the blob
`ae81c83bee1a8077f15c211055dd0667ca50b469:handoffs/comfy-control-surface/<p>`.
Relative paths are preserved verbatim.

The 15 recovered files:

- QUEST.md
- PROOF.md
- bridge-consumer/README.md
- bridge-consumer/bridge_consumer.py
- bridge-consumer/review_inbox.py
- bridge-consumer/fixtures/20260701-153012-submit-proof-7f3a.json
- bridge-consumer/mikers-demo/README.md
- bridge-consumer/mikers-demo/actions.slayer-rank.json
- bridge-consumer/mikers-demo/outbox/20260701-210000-slayer-rank-thrall-demo.json
- fixtures/actions.multi.json
- fixtures/actions.single.json
- fixtures/quest-view.json
- fixtures/submission.example.json
- fixtures/trace.example.jsonl
- generate-actions-from-rank-ladder.py

To verify byte-identity, for any `<p>` above:

```
git rev-parse "HEAD:recipes/quest-submission-bridge/<p>"
```

must equal

```
git rev-parse "ae81c83bee1a8077f15c211055dd0667ca50b469:handoffs/comfy-control-surface/<p>"
```

Source blobs contain LF line endings. The `.gitattributes` in this directory
is `* -text` so the bytes stay pinned on every platform.

## What did not land, and why

The retired C# BepInEx mod `ComfyControlSurface` remains archive-only at
`github.com/djcdevelopment/comfy/tree/main/handoffs/comfy-control-surface`:
`ComfyControlSurface.cs`, `Core/` (including `SubmissionService.cs`),
`Patches/`, `Config/`, `support/`, `build-and-install.ps1`,
`inspect-proof.ps1`, `manifest.json`, `CHANGELOG.md`,
`DESIGN-PROMPT-quest-log.md`.

This exclusion is deliberate. This landing paves the path for community
claiming task QB-1 (port `bridge_consumer.py` to the live mod's quest
telemetry) without doing it. The C# mod is an optional alternative a
claimant may fetch from the archive.

Additionally, the original input recipe (rank-ladder JSON exports) for
`generate-actions-from-rank-ladder.py` was pruned and did not land. The
script is kept because `QUEST.md` references it as the extension path.

## Generated outputs

`bridge-review/` and `__pycache__/` are deliberately untracked (gitignored).
Running the demo regenerates them.

## Fixture caveat

`fixtures/quest-view.json` is the retired `ComfyControlSurface` mod's
fixture, not the live schema. The live quest-view contract for the running
`ComfyNetworkSense` mod is documented at `recipes/quest-catalogs/`
(`quest-view-schema.md`, `example-quest-view.json`).

## Recorded divergences

- `bridge-consumer/README.md` — edited 2026-08-06 (QB-1): the archive's
  `handoffs/comfy-control-surface/` paths were rewritten to this repo's
  `recipes/quest-submission-bridge/`, and an "Archived original" note was added
  pointing at the live port (`tools/quest-bridge/`, ADR 0018). This file is no
  longer byte-exact against `ae81c83`; all other recovered files remain so.

## Editing rule

Files in this directory must not be edited in place without recording the
divergence in this `PROVENANCE.md`. The moment a file is modified it stops
being byte-exact, and this record is what says so.

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
