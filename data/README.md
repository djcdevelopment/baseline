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
raw/<guild>.xlsx  --harvest.py-->  processed/quest-catalog-*.json
                  --render_quest_picker.py-->  processed/quest-picker.html
                  --pin + verifier-->  attributable published bytes
```

The generator and catalog contracts live in
[`comfy-quest/recipes/quest-catalogs/`](https://github.com/djcdevelopment/comfy-quest/tree/main/recipes/quest-catalogs)
because they also ship to creators in the quest-picker zip. The inputs stayed
here, so the renderer reads them through `QUEST_DATA_ROOT` pointed at this
checkout.

**Refreshing the picker.** Run `harvest.py` for the changed guild, then
`render_quest_picker.py`, then regenerate `processed/quest-picker-pin.json` and
commit all of it together. `python tools/questpicker/verify_picker_pin.py` must
pass, and `--rerender` (with `QUEST_GENERATOR_ROOT` set) is the strong check that
the pinned generator reproduces the committed bytes exactly.

**Publishing the picker.** `tools/questpicker/Publish-QuestPickerToAM4.ps1` puts
the refresh on the live surface: it re-runs the verifier, installs the page
hash-verified at AM4's `/srv/lumberjacks/roadmap/quest-picker.html`, and demands
the served `X-QuestPicker-Sha256` equal the pin's recorded hash. The Gateway
re-reads the mounted file on change, so publishing is one file copy — no image
build, no restart. This script is the only writer of that file; the workbench
asset publisher in lumberjacks-platform deliberately does not ship
quest-picker.html (its sample clobbered the real page 2026-08-12 → 2026-08-17).

**What is actually forbidden** is an *unattributable* page: committing bytes whose
producing generator revision and input catalogs are not recorded in the pin. That
was the real risk behind the earlier "wait for a signed release" rule — a release
asset was one way to buy attribution, but a circular one here, since the inputs
originate in this repo. The pin buys the same property directly, and its tests
fail when the page or a catalog drifts. Superseded 2026-08-12; see
[SESSION-RETRO-2026-08-12](../fieldlab/retro/SESSION-RETRO-2026-08-12.md).

Weapon source files similarly flow into the joined JSON documented under
[`../docs/datasets/`](../docs/datasets/).

Raw artifacts are evidence. Processed artifacts should be reproducible from a named
source and tool or imported from a manifest-and-hash release. When that is not
possible, document the exception beside the output.
