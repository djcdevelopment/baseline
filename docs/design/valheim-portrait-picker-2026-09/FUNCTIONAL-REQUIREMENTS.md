# Functional requirements — portrait picker for Chronicles builder profiles

Status: proposed 2026-09-11 · Owner: Derek · Implementation home: `ComfyStewardView`
(`tools/chronicles/` for the manifest and front door, `tools/era-archive/web/` for the
profile page and picker, `tools/era-archive/coordinate.py` for the rails). Baseline holds
this record, the catalog tooling, and the FX99 front door.

Companion documents: [README.md](README.md) (corpus analysis and categorization),
[naming-reconciliation.md](naming-reconciliation.md) (tags, labels, UI vocabulary),
[`concepts.json`](concepts.json) (the 96 portraits with attributes and curated takes),
[`tools/portrait-corpus/vocab.json`](../../../tools/portrait-corpus/vocab.json).

## Objective

Let a Chronicles builder **choose the portrait their profile wears** from a curated library,
by narrowing a few dropdowns and segmented controls until a handful of portraits remain, then
picking one and one of its takes. Today every builder wears a tile assigned by hash
(`portraitIndex = parseInt(key[:8],16) % 48` in `ComfyStewardView/tools/chronicles/src/gateway.js`);
that stays the default for everyone who never chooses.

Decisions already taken (2026-09-11, with Derek): target surface is the Chronicles builder
profile; labels are tag-only, never character names; takes are curated to a short strip per
portrait with the rest one tap away.

## Existing foundation

| piece | where | what it gives us |
|---|---|---|
| slate48 portrait library | `ComfyStewardView/tools/chronicles/portraits/`, `assets/portraits/manifest.json`, served as `/chronicles/portraits.json` + `img/portraits/pNN.webp` (+ `.128.webp`) | the manifest shape (`tiles[{id, seed, tags[], sourceSha256, …}]`, `rejected[]`), the `?v=` cache-buster convention, the emblem fallback when the manifest is absent |
| portrait consumers | front-door name dropdown rows (`gateway.js`), hero card / Top 8 chips / kinship nodes / pair card (`era-archive/web/creators.js` `readPortraits()` ≈ l.696, `kinship.js`, `pair.js`) | five places that draw a builder's tile from one manifest and one index rule |
| claim rails | local ledger (`StewardParticipation`), the copied JSON payload, `coordinate.py`, `participation.json` (private) → `directory.json` / `threads/<key>.json` (public, static behind Caddy) | how a builder asserts something about themselves without an endpoint; the coordinator confirms and publishes |
| publish gate | `Publish-Gallery.ps1` scrub check; creators-lane `gate_creators.py` (threads/directory byte-identical to live apart from `generatedAt`) | where a new public field must be admitted deliberately |
| filter drawer with live counts | `baseline/tools/selfie-stick/gallery/index.html` (`FACETS` l.346, count mask l.509–533), design record `docs/design/Gallery navigation simplification/README.md` | the narrowing mechanic: one pass computes, per option, how many rows a click would leave given everything else selected; zero-count options dim, never vanish |
| FX99 static serving | `infra/fx99/Caddyfile`: `/<slug>/(thumb|large|img)/` immutable 7-day cache, `*.json` no-cache | where the cuts go |
| this corpus | `E:\omen\DMos\artifacts\corpus-viking-profiles-20260910\` + `concepts.json` | 96 portraits, 384 curated takes, tags on every portrait, a bust crop on every take, reject reasons on the 17 unusable files |
| privacy policy | `docs/decisions/pd-3-public-community-data.md`, `docs/legal/STEWARDSHIP.md` | a new public dataset needs its own consent and exposure check |

## Scope

In: the portrait library manifest (v2, both libraries), the image cuts and their serving,
the picker on the profile page, the `portrait` claim on the rails, the resolver every
consumer uses, curation and moderation, the privacy check, provenance.

Out (non-goals for this record): generating or re-rendering portraits (the DMos lane owns
that; the catalog tells it which seeds to redo); builder-uploaded images; portraits for DMos
DM/player seats; changing the hash default for builders who never choose; any endpoint
— the rails stay the copied payload until the four preconditions in the Chronicles design
record hold.

## Requirements

### FR-1 One manifest, two libraries

`/chronicles/portraits.json` becomes schema 2 and carries both libraries. Consumers that
only know schema 1 must keep working on the slate48 half.

```json
{
  "schema": 2, "generatedAt": "…",
  "libraries": {
    "slate48":  {"label": "Slate", "framing": "bust", "default": true},
    "viking96": {"label": "Viking", "framing": "waist-up", "default": false}
  },
  "facets": [ {"tag": "role", "label": "Trade", "kind": "dropdown"}, … ],
  "tiles": [
    {"id": "slate48/p01", "library": "slate48",
     "tags": {"role": "stonemason", "presentation": "woman", "age": "young"},
     "takes": [{"id": "s1", "v": "…", "sha": "…"}],
     "cuts": {"bust128": "img/portraits/slate48/p01.128.webp", "bust512": "…"} },
    {"id": "viking96/carpenter_f_artisan", "library": "viking96",
     "tags": {"role": "carpenter", "presentation": "woman", "theme": "builders", "age": "adult",
              "hair": "red", "mood": "proud", "setting": "workshop", "palette": "golden", "kit": "civilian"},
     "chips": ["companion:none"],
     "takes": [{"id": "s4", "v": "…", "sha": "…", "facing": "left"}, {"id": "s1", …}, …],
     "cuts": {"bust128": "img/portraits/viking96/carpenter_f_artisan.{take}.128.webp",
              "bust256": "…{take}.256.webp", "wide768": "…{take}.wide.webp"} }
  ],
  "aliases": {"role": {"joiner": "carpenter"}}
}
```

- `tiles[].takes` lists **only** `concepts.json` `takes.picked`, in strip order. Rejected takes
  are not in the manifest and their files are not published.
- `facets` is copied from `vocab.json` `facets.order`; the picker reads labels from here.
- `tags` values are vocabulary tokens; the UI label for a token comes from `vocab.json`
  (`role[tag].label`, else the token sentence-cased).
- Acceptance: a schema-1 reader given the schema-2 file renders the same 48 slate tiles;
  `test_portraits.py` grows a schema-2 fixture; every `takes[].id` in the manifest is in
  `concepts.json` `takes.picked` and none is in `takes.rejected`.

### FR-2 Cuts and serving

Per picked take, three files, content-addressed by the source sha and carried with `?v=`:

| cut | size | from | used by |
|---|---|---|---|
| `bust128` | 128² webp | the catalog's `bust_crop` `[x, y, side]` on the 1024² source | name dropdown rows, Top 8 chips, kinship nodes, pair card, picker grid |
| `bust256` | 256² webp | same crop | picker take strip, hero card on phones |
| `wide768` | 768² webp | the whole frame | hero card, picker preview |

- Files land under `/chronicles/img/portraits/viking96/` (immutable cache per the Caddyfile);
  the manifest is no-cache. Expected footprint for 384 takes: ≈ 384 × (6 + 20 + 90) KB ≈ 45 MB
  — INFERRED from typical webp ratios; measure on the first build and record it.
- The cut step runs in ComfyStewardView from `concepts.json` + `catalog.json` + the corpus on
  E:\ (the corpus is input, never copied into a repo). A take whose `bust_crop` is the
  composition default is cut the same way; the `face_small` advisory on a take demotes it in
  strip order but does not block it.
- Acceptance: for a sample of 12 takes across 12 concepts the bust cut shows the whole head
  with room above (a human check against the sheet); every referenced cut returns 200 with the
  immutable cache header; no cut exists for any rejected take.

### FR-3 The picker

Reachable from the hero card of a builder profile **the viewer has claimed in this browser**
(a claim on the local ledger for that key; confirmation by the coordinator is not required to
preview or to put the choice in the payload). Opens as a drawer (`min(400px, 92vw)` on phones,
a side panel on desktop), same scrim and `role=dialog aria-modal` as the era viewer's.

Controls, in this order, labels from `vocab.json` `facets.order`:

| control | kind | options |
|---|---|---|
| Trade | dropdown | the union of both libraries' roles, aliases folded (31 entries), each with a live count |
| Presentation | segmented | woman · man |
| Age | segmented | young · adult · elder |
| Mood | segmented | warm · calm · proud · stern · fierce |
| Hair | dropdown | blonde · red · brown · dark · grey · hidden |
| Setting | dropdown | the 14 setting tokens |
| Palette | dropdown | the 7 palette tokens |
| Kit | segmented | civilian · armoured · robed |
| Theme | dropdown | builders · trades · warriors & mystics · hunters & reavers · lore & hearth |

- **Live counts** use the era viewer's mask: for each option, the number of tiles that would
  remain if it were selected given every *other* facet's selection. Zero-count options dim to
  40 % and stay; the selected value always renders. A slate48 tile has no `hair`/`mood`/… tag
  and is counted as matching "any" on facets it lacks — so narrowing on a viking-only facet
  never dims the slate tiles into oblivion by accident; it simply does not narrow them.
- Header: one removable chip per active selection + **Clear all**; a result line "N portraits".
- Results: a grid of `bust128` tiles (first picked take), sorted Trade → Presentation, each with
  its Trade label and, when present, a small chip (companion, magic, face paint). Never a name.
- Selecting a tile opens the **take strip**: the picked takes as `bust256`, "more takes"
  reveals the rest of the picked list (never the rejected). Selecting a take shows the
  **preview**: the real hero card with `wide768` and a 128 px dropdown-row mock beside it, so
  the builder sees both cuts they are choosing.
- Actions: **Choose** · **Use the archive's pick** (reverts to the hash slot) · **Surprise me**
  (a random tile from the current narrowing, then a random picked take). Keyboard: every
  control tabbable, chips `aria-pressed`, Escape closes, focus returns to the hero card.
- Acceptance: with nothing selected the count reads 144 portraits (96 + 48); selecting
  Trade=Carpenter reads 8 (4 viking carpenters + 4 slate joiners via the alias); adding
  Hair=red reads 5 — `viking96/carpenter_f_artisan` plus the 4 slate joiners, which have no
  hair tag and therefore still match; adding Presentation=woman reads 3; no string in the
  picker matches `/character|archetype|seed|gender/i`; the drawer passes the viewer's
  `browser-smoke.mjs` leg on a phone viewport.

### FR-4 Persisting the choice on the rails

A new claim kind on the local ledger and in the copied payload:

```json
{"kind": "portrait", "builder": "<key>", "tile": "viking96/carpenter_f_artisan", "take": "s4",
 "sha": "<source sha256 of the take>", "chosenAt": "<iso>"}
```

- **Use the archive's pick** writes `{"kind": "portrait", "builder": "<key>", "tile": null}` —
  an explicit revert that the coordinator can see, not a deleted line.
- `coordinate.py` validates on ingest: the tile exists in the current manifest, the take is in
  its `takes[]`, the sha matches the catalog; a failing line is reported back, not dropped
  silently. On confirmation it writes `"portrait": {"tile", "take", "v"}` into the builder's
  record in `directory.json` and `threads/<key>.json`. `participation.json` keeps the full
  line with `chosenAt`.
- The creators-lane data gate admits the `portrait` field: threads/directory must be
  byte-identical to live **apart from `generatedAt` and `portrait`**.
- Nothing about the choice is sent anywhere by the browser; the payload is the handoff, as it
  is for handles, requests and kinship tags. `StewardParticipation.save()` failing keeps the
  same toast as today ("copy the payload before leaving").
- Acceptance: `coordinate.py` fixture round-trip (choose → payload → ingest → directory.json
  carries `portrait`); an invalid tile id is reported and not written; a revert line clears the
  field; the gate rejects a publish whose only difference is not one of the two admitted fields.

### FR-5 One resolver for every consumer

`portraitFor(builder, manifest)` in `gateway.js` (shared by `creators.js`, `kinship.js`,
`pair.js`) replaces direct `portraitIndex` calls:

1. `builder.portrait` present and its tile+take exist in the manifest → that take's cuts;
2. else → `slate48` tile at `portraitIndex(key, 48)` (today's behaviour, unchanged);
3. no manifest → the archive emblem (unchanged).

Consumers ask the resolver for a cut by role (`bust128`, `bust256`, `wide768`), never build a
path. Acceptance: the five consumers render a chosen builder with the chosen take, an
unchosen builder with today's tile, and a builder whose chosen tile was later removed from
the manifest with today's tile (no broken image); `browser-smoke.mjs` kinship leg still
counts 13 portraits on the live fixture.

### FR-6 Uniqueness

Default: **a portrait may be worn by any number of builders.** The picker shows "worn by N"
on a tile when N > 0, computed from `directory.json`, so a builder can pick an unclaimed one if
they care. The coordinator has a per-library flag `exclusive: true` that makes ingest refuse a
tile already worn (first confirmed claim wins) — off by default, and turning it on does not
unseat anyone already wearing a shared tile.

Rejected alternative: exclusivity by default. 96 portraits against a directory of several
hundred builders would make the picker a race and the hash default the common case, which
defeats the feature.

Acceptance: two fixture builders confirmed on the same tile both render it and the picker
shows "worn by 2"; with `exclusive: true` the second ingest is refused with a message naming
the tile, and the first builder is unaffected.

### FR-7 Curation and moderation

- Only `concepts.json` `takes.picked` reach the manifest. A portrait whose takes are still
  `source: auto` may be built and previewed on a dev host but **must not be published**
  until it has been through the contact-sheet pass and `picks.json` records it. (README
  Finding 3: no automated face gate is trustworthy on this art.)
- The coordinator may veto a confirmed choice (writes a revert line with a reason into
  `participation.json`) or replace the manifest's picks; both are ordinary re-publishes.
- Rejected takes (17 today) are never cut, never served, and their reasons stay in the
  catalog for the DMos lane.
- Acceptance: a CI check in ComfyStewardView fails the manifest build if any tile's source
  concept has `takes.source == "auto"` and the build is not marked `--dev`.

### FR-8 Privacy and consent

- The portraits are synthetic: no photograph, no likeness of a player, no builder named in
  any tag or file. The library itself adds no personal data.
- The **choice** is a new public field on a builder's record. Per PD-3 that needs its own
  exposure check before the first publish: it reveals nothing beyond a preference, it is
  volunteered through the same claim dialog as the handle, and it is revocable (revert line).
  Record that check in the go-live runbook entry, as the handle and kinship tags were.
- The profile carries one disclosure line near the portrait: "Portraits are painted by the
  archive's own models; builders choose theirs."
- Acceptance: the scrub check in `Publish-Gallery.ps1` still passes (no new field leaks
  coordinates or creator ids); the runbook entry cites this section.

### FR-9 Provenance

- Every manifest take carries `sha` (the source PNG's sha256 from the receipts) and the
  build carries `sourceReceipts` (sha256 + byte count of `receipts.ndjson`) and
  `sourceConcepts` (sha256 of `concepts.json`), so a served cut can be traced to a job id.
- The evidence page in baseline pins today's digests
  ([docs/evidence/2026-09-11-viking-portrait-corpus.md](../../evidence/2026-09-11-viking-portrait-corpus.md));
  the ComfyStewardView release receipt for the first manifest publish must quote them.
- Acceptance: for any served take, `manifest.tiles[].takes[].sha` equals the receipt's sha256
  for that asset id (a fixture test over `concepts.json`); the release receipt's
  `sourceReceipts.sha256` equals the evidence page's.

### FR-10 Coexistence and migration

- slate48 remains the default library (hash slot); viking96 is opt-in by choice.
- A later switch of the default to viking96 (or to a merged 144-tile slot) is a manifest flag
  plus a new `portraitIndex` count — no data migration, because chosen portraits are stored by
  tile id, not by slot.
- Removing a tile from the manifest (a future re-curation) must keep the resolver's fallback
  path (FR-5 step 2) rather than break profiles.
- Acceptance: flipping `libraries.viking96.default` to true in a fixture manifest changes what
  an unchosen builder wears and changes nothing for a chosen one; deleting a chosen tile from
  the fixture manifest renders that builder with the slate default and logs nothing to the
  console.

### FR-11 Performance and accessibility

- The picker's first paint needs the manifest (INFERRED ≈ 60 KB, ≈ 12 KB gzipped for 144
  tiles + 432 takes) and the visible `bust128` tiles; everything else is lazy.
- Tiles carry `alt` built from tags ("Carpenter, woman, red hair, workshop"), never names.
- Counts recompute in under 5 ms for 144 tiles on a phone (the era viewer does 3,400 rows in
  under 1 ms).
- Acceptance: Lighthouse accessibility ≥ 95 on the profile page with the drawer open; keyboard
  walkthrough recorded in the runbook.

## Contracts the implementation must keep

- `/chronicles/portraits.json` stays the single manifest URL; `?v=` on every image path.
- `portraitIndex(key, count)` keeps its signature and result for `count = 48`.
- The era viewer's drawer contracts (`.panel`, `.ck`, `aria-pressed`, `Clear all`, dimmed
  zero-counts) are reused, not re-implemented, so `shoot.mjs` studies still apply.
- Claim lines are append-only on the ledger; a revert is a line, not a deletion.
- UI vocabulary per [naming-reconciliation.md §4](naming-reconciliation.md).

## Delivery slices (each a vertical slice in ComfyStewardView)

| slice | delivers | proves |
|---|---|---|
| S1 | schema-2 manifest builder (`portraits/build_manifest.py`) + cuts from `concepts.json`/`catalog.json` + `portraitFor` resolver with fallback; no UI | FR-1, FR-2, FR-5, FR-9 on fixtures; live site unchanged |
| S2 | picker drawer on the profile page reading/writing the local ledger; preview only | FR-3, FR-11 on a dev host |
| S3 | `portrait` claim kind in the payload; `coordinate.py` ingest + validation; data gate admits the field | FR-4, FR-7 veto path |
| S4 | five consumers switch to the resolver; disclosure line; runbook entry with the PD-3 check | FR-5, FR-8 live |
| S5 | "worn by N", exclusivity flag, CI check on `takes.source` | FR-6, FR-7 |

Precondition for S4's publish: the 95 portraits still marked `source: auto` have been through
the contact-sheet pass (README Finding 3). That pass is a human afternoon with
`qa/contact-<concept>.jpg`; it is the one step this record cannot automate away.

## Open questions

None admitted to `DECISIONS-PENDING.md`: the three choices that had two viable answers
(target surface, naming, take curation) were taken on 2026-09-11 and are recorded at the top.
Two things to confirm during S1 rather than decide now: the measured footprint of the cuts
(FR-2) and whether a merged 144-slot default is wanted at all (FR-10).

## Implementation notes — S1 + S2 built, the review pass done (2026-09-12)

**Review pass.** `tools/portrait-corpus/review.py` + `review.html` (this record's companion tool): a local
page that walks the 96 concepts, shows every take as the exact 128-px bust the archive serves (the PNG
positioned by the catalog's `bust_crop`) beside the 256, with pick / reject / reason controls and one-key
accept. Derek walked all 96 sheets on it: three strips changed (wolfskin, `architect_m_master` re-ordered,
`fortifier_m_trenchmaker` cut to two takes with three rejected as "no human face"), the other 93 accepted
as they stood. `picks.json` now records all 96 (per concept `pick[]`, `reject[]`, `why`, plus `reasons{}`
and `reviewed_at`, which `build_catalog.py` ignores); `concepts.json` is re-catalogued with every
`takes.source: manual` (382 picked takes; 11 rejected by eye). The FR-7 precondition is met.

**S1** (ComfyStewardView): `tools/chronicles/portraits/build_manifest.py` cuts the library tree
(`chronicles-portrait-library/v1`); `build.py --library DIR` ships it and writes `portraits.json` schema 2;
`tools/era-archive/web/portraits.js` is the one resolver, and the four creators-lane consumers (hero,
ribbon, tree, pair card) switched to it now — behaviour identical for an unchosen builder, pinned by test.
`gateway.js` waits for S4. Deviations from this record, each deliberate:
- The first `count` tiles of the v2 document are the slate rows exactly as v1 shipped them (short ids
  `p01`, `tags` list kept, `tagMap` object added) so a v1 reader keeps working; a chosen tile is addressed
  as `<library>/<id>`. Library tiles spell each cut once with `{take}` where the take id goes, instead of
  three paths per take (the document is ~156 KB pretty-printed rather than ~225 KB; the gateway page
  inlines only the default-library slice).
- `v` is the stamp of the cut's own bytes (slate precedent), not of the source sha: a re-cut re-busts
  the immutable cache.
- Measured footprint (FR-2): 382 takes × 3 cuts = 1,146 files, 29.7 MiB — under the 45 MB estimate.
- The Trade menu has 30 entries, not 31: 24 painted + 12 slate − 5 shared − the joiner alias.
- The hero avatar (a 160-px square) wears the bust cut, not `wide768`; `wide768` is the picker's preview.
- The era viewer's drawer mechanic is ported into `web/portrait-picker.js` (the viewer keeps its script
  inline), with the contracts kept by name (`.panel`, `.grp`, `.ck[aria-pressed]`, `.ck.zero`, `Clear all`).
- The picker's entry ("Choose a portrait", under the hero avatar) needs both standing on the profile and a
  manifest with `libraries`, so a routine creators deploy against the live v1 manifest shows nothing.

**S2** (preview mode): the choice lands on this device's ledger (`state.portraits`, a revert is a record
with `tile: null`, never a deletion), every face on the page repaints through the resolver, the hero says
"Portrait recorded on this device". It does not ride the copied payload until S3 (`coordinate.py`
validation, the data gate admitting `portrait`). Gates: `portraits.logic.test.js`, `picker.logic.test.js`
(the acceptance numbers 144 → 8 → 5 → 3 over the real tags), `test_build_manifest.py`, the shell pins, and a
`PICKER=1` leg in `browser-smoke.mjs` that seeds a claim, walks the drawer, chooses, and reverts.

**Not published.** Nothing deployed in this pass. The library tree is at
`E:\omen\steward-multi-era\portraits\viking96-20260912` (built without `--dev`, so publishable once S3/S4 land);
a dev host at `E:\omen\steward-multi-era\devsite` serves the projection + a local chronicles build with it.
The evidence page's digests for `catalog.json` and `concepts.json` predate the re-catalogue and need
refreshing before the first release receipt quotes them (FR-9).

## Implementation notes — S3 + S4 live (2026-09-12, ComfyStewardView `94acd06` + `059f5cd`)

**S3.** `exportPayload` carries `portraits[]` and the build payload `portrait`; the hero's note grows
"Copy your payload". `coordinate.py ingest --portraits <portraits.json>` (required when the payload carries a
choice) checks every line against the manifest — tile present, take in the strip, sha the take's — and reports the
refused ones by id without filing them; `confirm-portrait <builderKey>` publishes the latest choice or confirms a
revert; `revoke-portrait --reason` is the veto (FR-7); `forget` takes a handle's choices; `status` lists what is
pending. `gallery.py` writes **`portrait: {tile, take}`** onto the builder's record (directory.json + thread) — not
`{tile, take, v}` as FR-4 wrote: `v` is the manifest's, so a re-cut never leaves a stale buster in a record.
`gate_creators.py` admits `portrait` beside `generatedAt`. The resolver gained a published table
(`StewardPortraits.setPublished`) filled from the thread and directory.json; order is device → published → slot.

**S4.** The front door's rows ask the same resolver: `build.py` ships `web/portraits.js` hashed beside `gateway.js`
(the resolver is one file in the repo, used by both lanes) and `gateway.js` fetches the full `portraits.json` once,
only when directory.json shows somebody has chosen (the page still inlines the slate slice). The disclosure line
(FR-8) sits under the avatar for every visitor; the picker control shows only with standing. The sweep checks the
libraries, one painted take's three cuts (immutable), and the two scripts (linted). Published: chronicles
`20260912T110102Z-1ec52bb01f01` (rollback `20260912T050004Z-282f720d8c76`), creators `059f5cdd4daf-c03976efc2a6`
(rollback `05c29f4f4ad7-81bdd0da1a31`), `?v=11`. `PICKER=1 browser-smoke.mjs` passes against FX99; `smoke_front`
15/15; sweep all clear. No portrait has been confirmed yet — the coordinator's first `confirm-portrait` will be the
first `portrait` field on a public record (the PD-3 check is recorded in the go-live runbook).

**S5 (not built):** "worn by N" and the `exclusive` flag.

## Implementation notes — painted defaults, the profile page, opt-out receipts (2026-09-12, ComfyStewardView `577baec`…`f123c46`)

Derek's review of the first live pass: the slate faces "are really not great". Decisions the same day: **slate48 is
retired**; **viking96 is the only library and the default**, assigned per builder from what the archive knows;
the avatar opens the **builder's own page**; opt-outs are **a request with a receipt** for now; own-image upload
deferred. This supersedes FR-10's "slate48 remains the default" and the non-goal "changing the hash default".

- **The archive's pick** (`tools/era-archive/portrait_assign.py`, `gallery.py --portrait-library`): a pure function of
  the builder key and the library, salt `portrait-v1`. Tier pools — Megabuilder: jarl, architect, fortifier, harbor,
  stonemason · Major Architect: architect, carpenter, stonemason, shipwright, fortifier, harbor · Established Builder:
  carpenter, blacksmith, miner, smelter, jeweler, shipwright, stonemason · Homesteader: brewer, furrier, hunter,
  carpenter, skald, frost, whaler · Explorer: hunter, reaver, frost, varangian, skald, shaman, seer, shieldmaiden,
  berserker. Four eras or a first era ≤ 8 leans senior (`master`, `chieftain`, `highbuilder`, `dockmaster`,
  `veteran`… or an elder face); one era ≥ 14 leans young; presentation is a seeded coin; the take a seeded pick.
  Written onto every record as `portrait: {tile, take, by: "archive"}`; a confirmed choice is `by: "builder"`.
  directory.json grew from 965 KB to 1.31 MB pretty-printed (Caddy gzips); accepted for an auditable, flicker-free
  default. `gate_creators.py` proves a portrait-only thread from the live receipt (CRLF-aware) — 2,682 proved, 0 fetched.
- **Slate retired**: `build.py --no-slate --default-library viking96`; `portraits.json` now `count: 0`, 96 tiles,
  `libraries: {viking96: {default: true}}` (135 KB); the gateway inlines nothing and fetches the document on the same
  idle tick as the directory. The slate tree stays in the repo, unshipped.
- **Your profile** (`/valheim/creators/profile/?builder=<key>`; `web/profile.html` + `profile.js`; `noindex`): the
  face and the wide frame, Discord sign-in (implicit grant, `identify`; off until `<meta name="discord-client-id">`
  is set; the key rides in `state`; the token is used once for `users/@me`), the picker (enabled with a Discord
  identity or a built claim on the builder), "Use the archive's pick" (a revert now steps aside for the published
  face rather than the slot), **Send my choice**, and the opt-out levels *Keep the pictures, drop my name* / *Erase
  every reference to me and don't use my builds in any process* with a note and **Send request**. The thread page's
  avatar is the door; the hero keeps the disclosure line and a "Your profile" link; the picker left the thread page.
- **The relay** (`POST /valheim/creators/relay?wait=true`, `baseline/infra/fx99/sites-enabled/creators-relay.caddy`):
  one Discord embed (builder, request, Discord identity or "unsigned", receipt `r-<yyyymmdd>-<8 hex>`), no mentions,
  `payload.json` attached (the export payload `ingest --portraits` reads). The webhook lives in the caddy unit's
  environment on FX99 (`CREATORS_RELAY_WEBHOOK=<id>/<token>`), never in git. Guards: same-origin fetches only, a
  256 KB body cap, Discord's own rate limit, a private channel, rotate on abuse, delete the file to close the route.
  Deployed; the variable is **not yet set**, so the route answers 404 and the page falls back to the copied payload.
- **Not built**: coordinator tooling for opt-outs (the receipt is the process for now), the suppress list every
  process reads, a Discord-id ↔ builder allowlist, own-image upload, S5.

## Implementation notes — the launch shape (2026-09-12 ~12:40 UTC, ComfyStewardView `ed9c738`)

Derek, for release the same day: no relay, no sign-in; **anyone may try a portrait on any builder's page**; a choice
must go through a query string so the front door logs it and obvious abuse can be watched; an opt-out simply
generates a message the builder pastes to him on Discord (**@Tugcow**). The relay route and the Discord OAuth
section from the previous notes are gone (the Caddy file was removed and FX99 redeployed).

- **The beacon** (`profile.js` → `GET portrait-beacon.txt?action=choose|revert|optout&builder=<key>[&tile=&take=]
  [&level=]&receipt=r-<yyyymmdd>-<8 hex>`): the front door's access log is the record — archive tokens only, never
  the note or a name. `tools/era-archive/read_portrait_beacons.py` reads it back (`ssh fx99 'python3 -' <
  read_portrait_beacons.py`): counts, the two abuse shapes (one address dressing three or more builders; one builder
  dressed from two or more addresses — the caller is `X-Forwarded-For` behind `tailscale serve`, and a tailnet user
  is named by `Tailscale-User-Login`), the last N notes; `--payload` prints the latest choice per builder in the
  export shape `coordinate.py ingest --portraits` reads, so publishing a choice is: read → ingest → `confirm-portrait`
  → project. The address bar also carries `?portrait=&take=` after a choice (a reload keeps the face; not a log line).
- **The message** (`requestMessage`): `@Tugcow — a request from the Valheim Chronicles archive` / `Receipt:` /
  `Builder: <name> (<key>)` / `Request: <level>` / `Note:` / `Page:`, in a read-only box with **Copy message**; the
  request stays on the device ledger (`state.optOuts`, `exportPayload.optOuts[]`) and its level is noted by beacon.
- Verified live: `PICKER=1 browser-smoke` (a stranger opens the picker; both beacons show in resource timing and in
  FX99's log; the message names the coordinator, the receipt and the key), sweep all clear, `read_portrait_beacons.py`
  on FX99 lists the smoke's own three notes with the tailnet login. Creators release `ed9c738e0015-c30f0f2bf2e1`
  (rollback `71e7e54af0f6-b06d9263a80c`); chronicles unchanged (`20260912T120657Z-939eb83063b7`).
