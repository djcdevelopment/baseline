# Builder page v2 — one story, the weeds on demand

Design record for the builder profile (`/valheim/creators/<key>/`, e.g.
[Tugcow](https://fx99.tail8e749c.ts.net/valheim/creators/5897d38e2a065e36a6895e70a2194738/)) — the second most
visited page after the gallery. Canvas: https://claude.ai/code/artifact/e0e33680-53a5-4f44-b1a2-1ff9c88702da

**Why (Derek, 2026-09-12):** the page holds everything the archive knows about a builder, stacked in the order
the features shipped (iterations 1–5 + Release B), not the order a visitor wants them. Not coherent as a message;
the top-to-bottom flow doesn't work; too much UI spent on labels. The kinship tree and the photographs are
enough to blow minds — the rest should feel intentional and be findable, not front-loaded. The front door's
restraint took many iterations; this page needs the same discipline.

**Decisions (2026-09-12):** embed the tree on the profile; fold pair-view extras, the per-album disclaimer and
contributor line, the status lines and the claim buttons; canvas first, then implement.

## Shipped (2026-09-12)

ComfyStewardView `0ae225c` + `60d9a8b`; creators release `60d9a8b1eb50-c78bbfb23c85` (rollback
`66f3ab072b8e-4e118cdf4a07`). The second cut departs from the canvas in one place, on Derek's review of the first
cut: **sections 2 and 5 merged** — the mosaic became a carousel (viewport, thick banner of era + facts, the details
plainly under it, a rail of the photographed builds as the selector) and the album rows became a plain table of the
un-photographed builds (Era · Build · world-viewer `link` · a Details drop-down of freeform text with the claim
controls · a Feedback column of hollow star / square / X marks that fill on selection and ride the participation
payload as photo priorities). Nothing on the page collapses except those two drop-downs and the pair's Details.

## The one story

*This is Tugcow. Here is what they built. Here is who they built beside. Everything else is there if you go looking.*

| # | Section | What's on it | What leaves / folds |
|---|---|---|---|
| 1 | **Hero** | Portrait · name · aliases (when any) · one line: `Major Architect · eras 7–12 · 39 build albums · 7,386 construction pieces · 28 photographs` — the numbers keep the `.counter` cell (the MySpace wink stays; the labels go) | The `TIER / FIRST ERA / LATEST ERA` eyebrow row; "Open the kinship tree" (the tree is on the page now); the manifest button (→ Notes) |
| 2 | **The work** | The builder's best photograph from each photographed album (`photos[0]` is already aesthetic-sorted), up to 8, 4-up 16:9, era badge; click → photo viewer; "see them all in the gallery" | — (new: today the photos are the fourth thing inside each album card) |
| 3 | **Who they built beside** | The kinship tree, embedded; the Top 8 chips are its caption (same eight, same tiers); a branch or a chip opens the pair below; "Open the kinship tree" → the ledger and tagging page | The separate Top 8 card with its own h2 / sub-line / link |
| 4 | **The pair** | Collapsed: `Kinship with Loanati` · one status line · the photo · the shared-builds ledger · pair-ledger download. `▸ Details` opens the build pills, laurels, shared hearth, affinity, the facts table, the metric tiles and the piece allotment | Eleven always-open sub-sections |
| 5 | **Albums by era** | The disclaimer once, at the top. One row per build: name · pieces · share · photographed dot · 4-thumb strip · `▸`. Expanded: contributors + slept-here, world viewer / gallery links, `I built this · Not mine · Request… · Copy this build payload`. Newest era open, older eras folded | Per-card disclaimer, per-card contributor list, four buttons on every card |
| 6 | **Notes** | Name-conflict status · your claims/requests on this page · capture progress · `Download builder manifest (JSON)` | (moved from the top) |
| 7 | **Where to go next** | The five wordless figures, participation details, footer — unchanged | — |

**The label rule:** an eyebrow (`.eyebrow`: mono .72rem, .14em, uppercase, `--outline`) only where a bare value is
ambiguous. "Major Architect", "eras 7–12", "39 build albums", "34 %" and "1,908" carry their own meaning. The one
label row that earns its place is the ledger head over the album rows (Build · Pieces · Share · Photos).

## Artboards

| File | Frame | Shows |
|---|---|---|
| `Main.dc.html` | 1160 × 3620 | the whole page, pair collapsed, rows collapsed |
| `PairDetails.dc.html` | 1160 × 4200 | `Details` open on the pair; the first album row expanded |
| `Mobile.dc.html` | 390 × 5200 | phone: mosaic 2-up, chips 4×2 (portraits only), tree in a scroller, rows two-line |
| `Before.dc.html` | 1160 × 4200 | today's order as a grey-box at the same scale |

One component (`src/profile.dc.template.html`) stamped by `src/build.mjs` (which also pre-renders the tree
SVG — a template loop inside `<svg>` is foster-parented by the HTML parser); `Before.dc.html` is hand-written.
Tweak chips: `pairDetails`, `expandRow`. Copy and counts are Tugcow's live values (39 / 7,386 / 28, eras 7–12,
34 co-builders, 7 photographed albums, the era-7 pair with Loanati: 4 builds, 564 shared pieces); the tree's 12
branches are the real Top 12 by shared pieces, lanes hand-placed. Photos are gradient placeholders.

```bash
cd "docs/design/Builder page v2" && node src/build.mjs
```

## Tokens (from `ComfyStewardView/tools/era-archive/web/creators.css` `:root`)

`--surface #0e141c` page · `--surface-container-low #161c24` slabs · `--surface-container #1a2028` chips, tiles ·
`--surface-low #090f16` counter cells · `--on-surface #dde3ee` · `--parchment #d8c3ad` body · `--outline #a08e7a`
labels · `--outline-variant #534434` hairlines · `--flame #f59e0b` · `--primary #ffc174` · `--bronze #d97707` ·
`--tertiary #ffc32d` counters · `--ember rgba(245,158,11,.25)` · `--chisel rgba(255,255,255,.08)`. Slab =
`1px solid var(--outline-variant)`, radius 6, `inset 0 1px 0 rgba(255,255,255,.08)`. Counter = mono, tabular,
`.12em`, `#090f16`, `inset 0 2px 4px #000`. Bodoni Moda / Plus Jakarta Sans / JetBrains Mono, self-hosted live.

## What the implementation must keep

Ids and classes pinned by the tests and gates (`#builder-hero #hero-avatar #hero-aliases`, `#intro .counter` ≥ 3,
`#look-out` with the five `a.path` in order, `#claim-modal`, `article.album` + `.album button.primary`,
`'article.album .kin-chip'`, `.photos img`, `.photo-thumb` → `#photo-viewer-modal`, `#manifest-download`,
`.top8 button.top8-chip[aria-pressed]`, `#top8-kinship-link`, `#pair-view` + `#pair-ledger`, `#pair-tab-viewer`);
the vocabulary bans (`character`, `archetype`, `submitted`, `verified`, `alliance`, `ward`); the participation
design (claims are self-reported markers; "I built this" is the album's primary action; request gated on a built
claim; copy-payload delivery; "recorded on this device"); the pinned CSS literals; `?v=7 → ?v=8` in ten places.
The tree lifts out of `kinship.js` into a shared `kin-tree.js`; nothing in the projection data changes, so
`gate_creators.py` passes. Full plan: the session plan file of 2026-09-12 (Deliverable B).
