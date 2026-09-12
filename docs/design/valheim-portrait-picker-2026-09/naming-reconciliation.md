# Naming reconciliation — Viking portrait corpus

The corpus carries three naming layers that disagree in places: the filename slug
(`viking_<archetype>_<f|m>_<variant>_s<N>`), the receipt's `discipline` label, and a fictional
`character_name` per concept. This note fixes which layer is the tag, which is the label, and
what the picker may say out loud. Source: [`concepts.json`](concepts.json), built from
`receipts.ndjson` by `tools/portrait-corpus/build_catalog.py`; vocabulary in
[`tools/portrait-corpus/vocab.json`](../../../tools/portrait-corpus/vocab.json).

## 1. Tag = slug, label = curated

The **tag** a picker filters on is the filename archetype, unchanged — it is what every
asset id, receipt and contact sheet already says, and it never has to be translated back.
The **label** a picker shows is curated once, here. Nine receipt labels diverge from their
slug; two of those (`jarl`→"Guild Master", `jeweler`→"Artisan") are outright misleading for a
Viking-themed picker, so the label follows the slug's meaning, not the receipt.

| tag (slug) | receipt `discipline` | picker label | note |
|---|---|---|---|
| `architect` | Architect | Architect | |
| `berserker` | Berserker | Berserker | |
| `blacksmith` | Blacksmith | Blacksmith | overlaps slate48 `blacksmith` |
| `brewer` | Mead Brewer | Brewer | overlaps slate48 `brewer` |
| `carpenter` | Carpenter | Carpenter | slate48 has `joiner` — a different tag, same trade; the Trade menu shows both libraries' tiles under "Carpenter" by an alias in the v2 manifest, not by renaming either |
| `fortifier` | Fortifier | Fortifier | |
| `frost` | Frost-Runner | Frost-runner | |
| `furrier` | Furrier | Furrier | |
| `harbor` | Harbor Engineer | Harbour-wright | "engineer" is the one anachronism in the receipt labels |
| `hunter` | Hunter | Hunter | overlaps slate48 `hunter` |
| `jarl` | **Guild Master** | Jarl | receipt label is a builder-community term, not the character |
| `jeweler` | **Artisan** | Jeweller | receipt label is too generic to filter on |
| `lawspeaker` | Law-Speaker | Law-speaker | |
| `miner` | Miner | Miner | |
| `reaver` | Sea-Reaver | Sea-reaver | |
| `seer` | Runecaster | Runecaster | slug and label differ; the receipt label reads better and is kept |
| `shaman` | Shaman | Shaman | |
| `shieldmaiden` | Shieldmaiden | Shield-bearer | the corpus has two men under this slug (`defender`, `sentinel`); a presentation-neutral label lets the Trade menu stay one entry |
| `shipwright` | Shipwright | Shipwright | overlaps slate48 `shipwright` |
| `skald` | Skald | Skald | |
| `smelter` | Smelter | Smelter | |
| `stonemason` | Stonemason | Stonemason | overlaps slate48 `stonemason` |
| `varangian` | Varangian Guard | Varangian | |
| `whaler` | Whaler | Whaler | |

Slate48's other roles (`thatcher`, `fisher`, `farmer`, `beekeeper`, `surveyor`, `hearthkeeper`)
have no viking96 counterpart; `surveyor` is close to `architect_f_surveyor` but stays its own
tag. The Trade menu in a two-library manifest therefore has 24 + 7 = 31 entries, of which 5
are shared and one is aliased (joiner/carpenter).

## 2. Themes

The five receipt `batch` strings become a `theme` tag (they are the generation runs, and they
double as a coarse mood-of-trade grouping the picker can offer as a single dropdown):

| tag | receipt batch | concepts |
|---|---|---|
| `builders` | Viking Builder Profiles | 48 |
| `trades` | Viking Northern Trades | 20 |
| `warriors-mystics` | Viking Warriors & Mystics | 12 |
| `hunters-reavers` | Viking Hunters & Reavers | 8 |
| `lore-hearth` | Viking Lore & Hearth | 8 |

## 3. Character names: catalog-only

Every concept carries a fictional name ("Astrid the Beam-Carver", "Chieftain Harek the
Harbor-Lord"). Per the decision taken 2026-09-11, **names never appear as the label a builder
wears** — the Chronicles principle is no "character"/"archetype" language in UI text, and the
slate48 rule is "nothing here names a builder". The names stay in `concepts.json` as flavour
for the catalog and the coordinator.

For the record, they would not have survived as labels anyway: 15 first names are shared
across concepts, so the given name alone does not identify a tile —
Astrid, Brand, Einar, Gudrun, Harald, Hervor, Inga, "Jarl" (as a title), Kari, Knut, Ragna,
Sigrid, Thyra, Torstein, Yrsa. Einar and Brand each appear three times.

One name looked mangled on the console ("Sei�-Kona") and is not: the receipt holds `ð`
(U+00F0, "Seið-Kona"); a cp1252 console prints it as `?`. No receipt was edited, and the
catalog builder no longer carries a "repair" for it.

## 4. What the picker says

| concept | UI word | never |
|---|---|---|
| filter axis `role` | **Trade** | archetype, discipline, class |
| filter axis `presentation` | **Presentation** (woman / man) | gender |
| `age`, `mood`, `hair`, `setting`, `palette`, `kit`, `theme` | those words | — |
| a concept (96) | a **portrait** | character, concept, persona |
| a seed (14–15 per portrait) | a **take** | seed, variant, sample |
| the strip of curated takes | **takes** | seeds |
| the slate48 hash default | **the archive's pick** | random, fallback |

Every UI string in the functional requirements is checked against the "never" column;
`vocab.json` carries the facet labels so the implementation reads them rather than
re-inventing them.

## 5. Asset and manifest ids

- `asset_id` stays the receipt's (`viking_<slug>_s<N>`) — it is the sha-verified name of a file.
- A served tile in the v2 manifest is `viking96/<concept slug without the viking_ prefix>`
  (e.g. `viking96/carpenter_f_artisan`), and a take is `<tile>#s<N>`. The slate48 library keeps
  `p01`–`p48` under `slate48/`.
- Two asset ids share one corrupt blob (`carpenter_m_veteran_s1`, `miner_m_prospector_s1`,
  identical sha256, both 355 s in the receipts). They keep their ids, carry `reject: ["corrupt"]`,
  and are the two seeds the DMos lane would re-render if it ever wanted 15 takes there.
