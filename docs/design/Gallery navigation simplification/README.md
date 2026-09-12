# Gallery navigation simplification — the `/valheim/` menu

Design record for the era photo viewer's menu (`ComfyStewardView/tools/selfie-stick/gallery/index.html`,
live at `https://fx99.tail8e749c.ts.net/valheim/`). Two passes so far:

| Pass | Where | Date |
|---|---|---|
| **v2** — Derek's Claude Design canvas: drawer, active-chip strip, era dropdown, sort dropdown, places as a list | `Gallery Menu v2.dc.html` (export of https://claude.ai/design/p/1352762e-4175-4d64-8101-df14c35c5d6f); reference screenshots in `uploads/` | 2026-09-11 |
| **v3** — this pass: v2's structure on the Chronicler tokens, with the departures below | `v3/` (five artboards + `canvas.json`, generated from `v3/src/menu.dc.template.html` by `v3/src/build.mjs`); canvas https://claude.ai/code/artifact/28787bb5-10fa-4731-ada1-11f4a2a2e55e | 2026-09-11 |
| **Shipped** — v3 implemented in the viewer | ComfyStewardView `f5814da`, live sha `796b8a2041df` in all nine era directories (rollback `31ef8c5f6c5c`); see the runbook entry "Era viewer pass 3" in `docs/internal/RUNBOOK-chronicles-go-live-2026-09-10.md` | 2026-09-11 |

The menu had no design record before v2: the Sept 10 Chronicler skin (`8605f94`) restyled the chip wall
without redrawing it, and the Stitch canvas under `../valheim-chronicles-stitch-2026-09/` never covered the viewer.

## What v2 settled (kept in v3)

- Filters live in a **left drawer** over a scrim; the grid stays visible behind it.
- A **search box** at the top of the drawer narrows every option by text.
- **Active-filter chips** sit in the header with `×` and a `clear all`.
- **Era** is a header dropdown; **Sort** leaves the chip wall for a dropdown.
- **Places** are a scrollable list, not eighty chips; the footer is `Clear all` + a primary `Show N …`.
- `Page size` leaves the header.

## v2 → v3

| # | v2 | v3 | Why |
|---|---|---|---|
| 1 | Playfair Display / Archivo, `#12161d` surface, `#e8a33d` accent, 8–10 px radii | **Chronicler tokens** (see below): Bodoni Moda / Plus Jakarta Sans / JetBrains Mono; `#0e141c` surface, `#ffc174` primary, `#f59e0b` flame; chips 4 px, buttons and menus 6 px | The viewer must read as one product with `/chronicles/` and `/valheim/creators/`; v2's palette was placeholder drift |
| 2 | Era as a header dropdown **and** a chip row in the drawer | Header dropdown only. Items are real links to the sibling era directories, the current era is marked, the last item is `Builders across eras ›` | An era switch is navigation (a different directory, filters do not carry); the drawer is filters only |
| 3 | Header keeps only `Chronicles` | Right-aligned mono uppercase nav **CHRONICLES · BUILDERS** (emblem on Chronicles) | Echoes the front door's `GALLERY · BUILDERS · GUIDE`; Builders is the photo → creators path (Top 8, kinship, claims) |
| 4 | `sort ▾` on a non-sticky subline with the count | `sort · every build ▾` in the sticky header row, between the chip strip and ERA; the subline carries only the count | Sort stays reachable while scrolled; the header stays one row on desktop |
| 5 | One `PLACE` list with the `· 8,026` suffixes stripped | **Areas** (`near X`, 2 km neighbourhoods, key `a<id>`) and **Builds** (key `c<id>`) as two lists. Build and area rows keep the piece count as small right-hand meta. 8 rows each + `Show all N`; search narrows both; a selected row is always visible | Two things in the data (`#area=` vs `#build=` deep links). Build names collide without the count — two `Sky Island`s, two `Tree Fort`s — and the code already warns that a merged label filters both builds at once |
| 6 | `fog 74` as a chip under `HIDDEN` | Toggle row at the bottom of the drawer: `Include fog-hidden frames · 74` | It widens the set; a facet chip reads as "only fog" |
| 7 | Static counts | **Live-narrowing counts**: each option counts the rows matching the *other* facets (plus the fog rule). Zero-count options dim to 40 % and never disappear; selected values always render | Standard faceted navigation — the count becomes a promise about what a click will show |
| 8 | Chip label = bare value | `weather · Clear` and `kind · build` carry a light facet prefix; perspective, region and places show the value alone | "Clear" and "build" are ambiguous on their own |
| 9 | `Show N photographs` | `Show N builds` under `every build` (the showcase collapses to one frame per build), `Show N photographs` under every other sort. `Clear all` keeps today's `goHome()` semantics — back to the front door, showcase sort | Mirrors the wording `render()` already uses for the subline |
| 10 | Page size dropped | `per page 50 · 100 · 200` in the bottom pager, default 100 | Keeps the feature without a header input |
| 11 | Tiles redrawn 4:3 with always-on captions and `✦` | **Unchanged**: the live 1:1 cells, weather badge, score, hover caption and star | Out of scope for the menu; v2's tiles were preview scaffolding |
| 12 | — | Mobile ≤ 640 px: chip strip hidden (the Filters badge carries the count), sort icon-only, ERA name-only, BUILDERS hidden (it stays in the era menu), CHRONICLES emblem-only, drawer `min(400px, 92vw)`, grid two columns | The header must survive 390 px |
| 13 | — | `role=dialog aria-modal`; focus lands in the search on open (the `×` on mobile) and returns to Filters on close; Esc order = lightbox › open menu › non-empty search (clears) › drawer; menus close on outside click or pick; chips carry `aria-pressed` | Keyboard parity with the pointer path |

## Tokens (from `../valheim-chronicles-stitch-2026-09/DESIGN.md`, already in the viewer's `:root`)

| Role | Value | Where it lands |
|---|---|---|
| surface | `#0e141c` | page, drawer, header at 92 % + blur |
| surface-container | `#1a2028` | buttons, chips, menus, drawer footer |
| surface-container-lowest | `#090f16` | search input |
| on-surface / on-surface-variant | `#dde3ee` / `#d8c3ad` | text / labels, muted counts |
| outline / warm outline | `#2f353e` / `#534434` | rules / menu and drawer edges |
| primary / primary-container / secondary-container | `#ffc174` / `#f59e0b` / `#d97707` | active text / open state, primary button, fills / hover borders |
| on-primary-fixed | `#2a1700` | text on flame |
| display / body / mono | Bodoni Moda / Plus Jakarta Sans / JetBrains Mono | era name, drawer title / rows / labels, chips, counts |

Exact control values are lifted from the live stylesheet: `.filt` 8 × 13 px at 6 px radius with the
`rgba(217,119,6,.5)` border and inset highlight; `.ck` 5 × 11 px at 4 px radius, mono 12 px, `.04em`;
facet labels mono 11 px uppercase `.06em`. The canvas loads the faces from Google Fonts; the live page
keeps its self-hosted `@font-face` block (`/chronicles/img/fonts/`).

## The artboards

| File | Frame | Shows |
|---|---|---|
| `Main.dc.html` | 1440 × 900 | header with two filters active, subline, grid, pager |
| `Drawer.dc.html` | 1440 × 900 | the drawer open over the same page |
| `Menus.dc.html` | 1440 × 520 | era and sort menus open (both at once for review only — in the UI opening one closes the other) |
| `Mobile.dc.html` | 390 × 844 | the header collapsed |
| `MobileDrawer.dc.html` | 390 × 844 | the drawer at 92 vw |

All five are one component; the tweak chips above each artboard (`drawerOpen`, `eraMenu`, `sortMenu`,
`seedChips`, `placesShown`) are the only differences. Counts and names are the live era-17 values;
the filtered figures (41 builds / 312 photographs / 412 setups) are illustrative.

Rebuild after editing the template:

```bash
cd "docs/design/Gallery navigation simplification/v3" && node src/build.mjs
```

## Contracts the implementation must keep

`#expbtn`, `.panel`, `.ck` and `.cell` (driven by `ComfyStewardView/tools/chronicles/shoot.mjs`
`study-filters` / `study-lightbox` / `walk-eras`); `#build=` / `#area=` hash routing (`applyHash`);
`goHome()`; root-absolute hrefs (the page is copied into nine directories); the self-hosted glyph
subsets (`×` `›` `▾` are in; `→` and `✓` are not — draw the check).
