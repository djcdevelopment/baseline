# Recipes

Recipes turn existing community artifacts into validated, reusable outputs
without asking volunteers to change how they work. Each recipe should be
understandable enough to use, create, and repair.

The July 2026 prune removed the `rank-ladders` recipe and the `framework/`
operating-rules kit this file used to open with. Both are recoverable from git
history and from `C:\work\comfy`.

## Available recipes

### Quest catalogs

[`quest-catalogs/`](quest-catalogs/) harvests guild trackers into canonical
catalogs and anomaly reports, then renders the local quest picker. Its contracts
are [`schema.md`](quest-catalogs/schema.md) and
[`quest-view-schema.md`](quest-catalogs/quest-view-schema.md).

```powershell
python .\recipes\quest-catalogs\harvest.py
python .\recipes\quest-catalogs\validate.py .\data\processed\quest-catalog-slayers.json
python .\recipes\quest-catalogs\validate.py .\data\processed\quest-catalog-rangers.json
python .\recipes\quest-catalogs\render_quest_picker.py
```

The prune also removed the committed catalog outputs under `data/processed/`,
so the `validate.py` lines above operate on files that `harvest.py` regenerates
— run the steps in order rather than validating first. The recipe's inputs
(`data/raw/*-guild-tracker.xlsx`) and its rendered picker
([`../data/processed/quest-picker.html`](../data/processed/quest-picker.html))
are still committed.
