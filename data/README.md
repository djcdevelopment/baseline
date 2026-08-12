# Data

This directory preserves source artifacts and the reproducible projections made from them. It is the
repo's largest area by bytes, but most of that volume arrived in the formation session rather than
through ongoing code churn.

## Layout

- [`raw/`](raw/) contains source artifacts as received. Read [`raw/SOURCES.md`](raw/SOURCES.md) for
  provenance. Do not silently clean or overwrite these files.
- [`reference/`](reference/) contains small, curated reference structures used across recipes.
- [`processed/`](processed/) contains derived catalogs, anomaly reports, joined datasets, and the
  generated quest picker.

## Quest-picker snapshot

```text
comfy-quest release asset + manifest
  -> SHA-256 and byte-count verification
  -> processed/quest-picker.html (Baseline mirror)
```

The generator and catalog contracts moved to
[`comfy-quest/recipes/quest-catalogs/`](https://github.com/djcdevelopment/comfy-quest/tree/main/recipes/quest-catalogs).
The currently committed picker predates the first post-split release and is retained
as a historical snapshot. Refresh is BLOCKED until a signed/tagged Quest release
exists; do not regenerate it from a sibling checkout or imply it is release-backed.

The raw trackers and harvested catalogs stayed here, so the generator reads them
through `QUEST_DATA_ROOT` (pointed at this checkout) rather than an assumed
monorepo layout — verified 2026-08-12 to reproduce the committed
`processed/quest-picker.html` byte for byte. That portability is what a future
release lane needs; it does **not** make a local run an authorized refresh. The
rule above still governs what may be committed here.

Weapon source files similarly flow into the joined JSON documented under
[`../docs/datasets/`](../docs/datasets/).

Raw artifacts are evidence. Processed artifacts should be reproducible from a named
source and tool or imported from a manifest-and-hash release. When that is not
possible, document the exception beside the output.
