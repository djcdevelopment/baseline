# Recipes

Recipes turn existing community artifacts into validated, reusable outputs
without asking volunteers to change how they work. Each recipe should be
understandable enough to use, create, and repair.

The July 2026 prune removed the `rank-ladders` recipe and the `framework/`
operating-rules kit this file used to open with. Both are recoverable from git
history (last present at pre-prune ref `57654fd`) and from the public archive
at [`github.com/djcdevelopment/comfy`](https://github.com/djcdevelopment/comfy).

## Available recipes

### Quest catalogs — moved

[`comfy-quest/recipes/quest-catalogs/`](https://github.com/djcdevelopment/comfy-quest/tree/main/recipes/quest-catalogs)
harvests guild trackers into canonical
catalogs and anomaly reports, then renders the local quest picker. Its contracts
are [`schema.md`](https://github.com/djcdevelopment/comfy-quest/blob/main/recipes/quest-catalogs/schema.md)
and [`quest-view-schema.md`](https://github.com/djcdevelopment/comfy-quest/blob/main/recipes/quest-catalogs/quest-view-schema.md).

```powershell
cd C:\path\to\comfy-quest
python .\recipes\quest-catalogs\harvest.py
python .\recipes\quest-catalogs\validate.py .\data\processed\quest-catalog-slayers.json
python .\recipes\quest-catalogs\validate.py .\data\processed\quest-catalog-rangers.json
python .\recipes\quest-catalogs\render_quest_picker.py
```

Baseline keeps source data and a rendered picker snapshot for provenance. The
post-split handoff back into Baseline is a tagged Quest release plus manifest, byte
count, and SHA-256 digest—not a source-tree reach-in.

### Quest submission bridge (raw material)

[`quest-submission-bridge/`](quest-submission-bridge/) is the recovered,
unwired back half of the Quest Submission → Review Bridge workbench tool:
`bridge_consumer.py` and `review_inbox.py`, their fixtures, and the original
`QUEST.md` / `PROOF.md` briefs, byte-exact from the public comfy archive.
Provenance, license boundary, and the file-by-file mapping are in
[`PROVENANCE.md`](quest-submission-bridge/PROVENANCE.md). It runs against its
own fixtures today and is not wired to the live mod — that port is claiming
task QB-1 on the workbench.

```powershell
python .\recipes\quest-submission-bridge\bridge-consumer\bridge_consumer.py .\recipes\quest-submission-bridge\bridge-consumer\mikers-demo
python .\recipes\quest-submission-bridge\bridge-consumer\review_inbox.py .\recipes\quest-submission-bridge\bridge-consumer\mikers-demo list
```

The `bridge-review/` output folder those commands create is deliberately
untracked.

### Camera gallery (raw material)

[`camera-gallery/`](camera-gallery/) is the recovered raw material of the
Camera Flythrough → Gallery Pipeline workbench tool: segment 1's working
waypoint extractor, the segment 2–4 briefs, segment 4's `video_to_gallery.py`,
and two sample fixtures, byte-exact from the public comfy archive. Provenance,
license boundary, segment status, and the privacy note on the samples are in
[`PROVENANCE.md`](camera-gallery/PROVENANCE.md). Segment 3 — the flight-path
mod itself — has no code anywhere and is the real gap; reviving segment 1 is
claiming task CG-1 on the workbench.

```powershell
python .\recipes\camera-gallery\video_to_gallery.py flythrough.mp4 .\recipes\camera-gallery\timeline.sample.json --dry-run --duration 60
```

The dry run prints what it would cut without needing a real video or ffmpeg.
