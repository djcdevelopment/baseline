# Chronicles go-live — 2026-09-10

The front door of the Valheim archive, the Chronicler skin on the two live pages, and the
4K era-17 publish all land in one window. This is the order, the gates, and the rollbacks.
Product code is in `ComfyStewardView` (`tools/chronicles/`, `tools/era-archive/web/`,
`tools/selfie-stick/`); baseline holds the FX99 front door and the era publish script.

## Lanes on FX99 (`/srv/sites/`, Caddy static-by-convention, no config change)

| Lane | Path | Deploy | Rollback |
|---|---|---|---|
| Front door | `/chronicles/` | `python tools/chronicles/deploy.py --out <built dir>` | `deploy.py --rollback <release>` |
| Era viewer page | `/valheim/index.html` + `/valheim/era*/index.html` | `python tools/selfie-stick/push_viewer.py --viewer tools/selfie-stick/gallery/index.html` | `push_viewer.py --rollback <sha12>` |
| Creators | `/valheim/creators` (symlink) | `gallery.py` → `deploy_gallery.py` | re-point the symlink to the previous `.creator-releases/<id>` (receipt records it) |
| Era photos + index | `/valheim/` root, `/valheim/<era>/` | `baseline\tools\selfie-stick\Publish-Gallery.ps1` | n/a (full replacement) |

## Order

1. **Chronicles release 1** (fonts must be live first: `creators.css` and the viewer reference
   `/chronicles/img/fonts/*.woff2` root-absolute, `font-display: swap`).
2. **Viewer push** to the root and every era dir. `push_viewer.py --verify` afterwards.
3. **Creators**: re-project, run the data gate (`python tools/era-archive/gate_creators.py --projection <dir>` in ComfyStewardView;
   must PASS: every `threads/*.json` and `directory.json` identical to the live release apart
   from `generatedAt`), then `deploy_gallery.py --revision <HEAD> --receipt <path>`.
   The deploy gate needs `tools/era-archive` + `tools/selfie-stick` clean and committed.
4. **Screenshots** (`node tools/chronicles/shoot.mjs --base https://fx99.tail8e749c.ts.net --out <dir> --crop`)
   → rebuild → **Chronicles release 2**.
5. **4K era-17 publish** (whoever runs it):

   ```powershell
   .\tools\selfie-stick\Publish-Gallery.ps1 -GalleryPath <era17 4K gallery> -EraSlug era17 -ViewerHtml C:\work\ComfyStewardView\tools\selfie-stick\gallery\index.html
   ```

   Then:

   ```powershell
   python C:\work\ComfyStewardView\tools\selfie-stick\push_viewer.py --viewer C:\work\ComfyStewardView\tools\selfie-stick\gallery\index.html --verify
   ```

   Without `-ViewerHtml` the script ships the copy beside it. That copy is kept byte-identical
   to the ComfyStewardView file by hand; the log now prints the staged viewer's SHA-256 so a
   stale page is visible in the run output.

## Verification sweep (PowerShell, plain HTTP; the in-app browser pane blocks fx99 subresources)

- `/chronicles/`, `/chronicles/guide/`, `/chronicles/build.json` → 200; `/chronicles/img/*` carries
  `Cache-Control: public, max-age=604800, immutable`; `/chronicles` → 308; `/` → 404.
- `/valheim/` and `/valheim/era{7,8,9,10,12,14,16}/` → 200, body contains `--flame` and
  `href="/chronicles/"`, no `api/valheim`.
- `/valheim/creators/` → 200, `creators.css?v=2` contains `--flame`; one thread + its
  `threads/<key>.json`; `/valheim/creators/stats/`.
- Gateway search submit lands on `/valheim/creators/?q=<name>` with the box pre-filled.
- `#build=` deep links still open in the root and in an era dir.

## Do not

- Run `infra/fx99/deploy.ps1` in this window: it stages all of `sites-enabled/` and the
  working tree is mid-change (`dmos-app.caddy` untracked, `world.caddy.proposal` parked).
- Start a HEARTH art session for the illustrated "?" card while the 4K capture holds the B70s;
  the SVG sticker ships, the illustration follows.

## What went live (2026-09-10, ~12:30 UTC)

| Lane | Release | Rollback to |
|---|---|---|
| `/chronicles/` | `20260910T123011Z-848443b80113` (release 2, with tutorial crops) | `20260910T122453Z-5833a76b6198` via `deploy.py --rollback` |
| Era viewer | sha `31ef8c5f6c5c` in `/valheim/` + era7,8,9,10,11,12,14,16 | `push_viewer.py --rollback 824d662bcce1` (era16 was `5c17abbed13d`) |
| Creators | `.creator-releases/9fd336221882-99ce9c69c3f6` | `.creator-releases/87b27edf5458-1f2d711b931f` |

Sweep (`ComfyStewardView/tools/chronicles/verify_sweep.ps1`): all clear after release 2.
Still open: the illustrated "?" card (SVG sticker ships; generate on the B70s after the
capture), and the 4K era-17 publish with `-ViewerHtml` followed by `push_viewer.py --verify`.

## Iteration 2 — "more is less" (2026-09-10, ~17:40 UTC)

Derek's read of iteration 1: the figures on the front page were noise for the visitor who lands
from a bookmark and types their own name. Shipped:

| Surface | Change | Release | Rollback to |
|---|---|---|---|
| `/chronicles/` | Front page is one question: the name box with a ranked dropdown (same matcher as the builders page, copied verbatim with a parity test; portrait tile per row; Enter on a prefix match opens the profile; `?q=` pre-fills) and one button "Browse the builds" → `/valheim/`. Stats and era row moved to the guide. | `20260910T173815Z-3f4a2b77fe0f` | `deploy.py --rollback 20260910T123011Z-848443b80113` (iteration 1) |
| `/chronicles/portraits.json` + `img/portraits/` | 48 painted portraits (12 roles × young/elder × woman/man) rendered on the B70s via HEARTH `z-image-turbo`; per-builder slot = `parseInt(key[:8],16) % 48` (tile ids are 1-based, so index 46 is `p47`). | same | same |
| Builder pages | Hero card (avatar, aliases, tier, first/latest era, counters, signature creations) above the Top 8; five path cards with the figures at the bottom. `creators.css?v=3`. | `.creator-releases/dbfbac58dbda-fc96ee6c235f` | `.creator-releases/ef064142a00a-1f889de7ad5f` (Derek's era-11 redeploy, carries iteration-1 skin) |

Verification: `tools/chronicles/smoke_front.mjs` 15/15 live (Tug → Tugcow first with tile p47 →
Enter → `/valheim/creators/5897d38e…/` → hero + eras + counters + five path cards; `?q=` deep link;
no page exceptions), `browser-smoke.mjs` passed, `verify_sweep.ps1` all clear.

Incident during the window: the omen-arc LLM rung could not reload after the art session because an
NVIDIA installer had removed `C:\Windows\System32\vulkan-1.dll` at 04:48 local; llama-server (the
llamacpp-knee build) imports `ggml-vulkan.dll` at start and died with `0xc0000135`. Fixed with an
app-local copy of the Intel driver store's `vulkan-1-64.dll` beside the binary; ArcServe serviceable
again at 10:24 local. Reinstalling the Intel driver restores the System32 copy properly.

## Iteration 3 — Kinship (2026-09-10, ~19:35 UTC)

Derek's ask: majority owners of a build can tag the people they built beside, and who you have
"camped" with over the eras is shown as a branching tree over time. Shipped on the creators lane
only (no chronicles or viewer change):

| Surface | Change | Release | Rollback to |
|---|---|---|---|
| `/valheim/creators/kinship/?builder=<key>` | New page (`web/kinship.html` + `web/kinship.js`, projected by `gallery.py` beside `stats/`). Anchor picker with the same matcher as the front door; Tree tab (era bands, trunk = anchor, one branch per co-builder, solid = shared pieces that era, dashed = legacy era with unknown shares, hairline = an era apart) and Ledger tab (50 rows a page); aside "Builds you hold" with per-build share bars and Tag controls; `#kin-tag-modal`. | `.creator-releases/af25c9fde1bd-abdc72125cf7` | `.creator-releases/dbfbac58dbda-fc96ee6c235f` (iteration 2) |
| Builder pages | "Open the kinship tree" in the hero and on the Top 8 panel; coordinator-confirmed tags render as solid `.kin-chip` chips beside the credit line. Nav gains Kinship. `creators.css?v=4`. | same | same |
| `creators.js` | Participation ledger hoisted into `StewardParticipation` (same storage key and schema, plus `kinshipTags`; "forget" clears it). `majorityOwner` (≥50 % share, else the largest known share ≥25 %; legacy owns nothing), `buildKinshipTree`, `kinshipTagRecord`, closed tag vocabulary (basemate / collab / helping-hand / visitor; mason / roof / fields / portal / defense / interior). Route guard: creators.js stands down on the kinship page. | same | same |
| `participation.json` | `gallery.py sanitize_confirmed_tags()` publishes coordinator-confirmed tags stripped to buildKey / contributorKey / builderKey / tags / confirmedAt. The coordinator file (`analysis/participation.json`) does not exist yet, so the public file is still absent (404) — pages treat it as optional. | same | same |

Rails: a tag is recorded on the device, exported in the copied payload beside the gating claim
(`kindFilter: 'kinship'`), and only becomes public when a coordinator confirms it. Tagging is gated
on "I built this" for that build; ungated buttons are `.inert` + `aria-disabled`, never `disabled`.
Bed ownership is NOT joined to builds (phase 2, separate evidence type `bed-owner-in-footprint`, a
pipeline change that fails the gate by design). Circle mode and photo-inspect tags are later phases.

Verification: gate PASS (2,682 threads identical to live, only presentation differs);
`browser-smoke.mjs` kinship leg on the live site — 12 branches, 72 strokes, 13 portraits, 50 ledger
rows, tag gate held; `smoke_front.mjs` 15/15; `verify_sweep.ps1` all clear (kinship URLs, `?v=4`,
banned words absent). Suites: era-archive 82 tests, chronicles 45, Node 48. The smoke's spatial leg
(AM4 world viewer `?era=era7` raster) timed out during this window; that lane is not part of this
release and every FX99 check passed.

Known limits: no live thread reaches a legacy era with more than one contributor (every legacy
import credits one builder), so dashed legacy segments only appear on fixtures; the tree draws the
12 closest branches and the ledger lists the rest; node labels stagger and truncate at twelve lanes.

## Design record

The Stitch canvas export the three iterations were built from is committed as text at
`docs/design/valheim-chronicles-stitch-2026-09/` (DESIGN.md, the 16 mocks as HTML, the
aspirational architecture documents under `aspirational/`, and a mock-to-shipped index).
Rendered screens stay outside git at `E:\omen\design-exports\valheim_creators_gallery\`.
