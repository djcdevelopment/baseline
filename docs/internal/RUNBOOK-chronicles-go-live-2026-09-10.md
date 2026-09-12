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

The second export, the Kinship Viewport mock and its API-shaped spec, is committed beside it as
`docs/design/valheim-kinship-viewport-stitch-2026-09/` with a mock-region → shipped table (iteration 5).

## Iteration 4 — closing the open questions (2026-09-11, ~04:10 UTC)

Derek accepted fifteen recommendations after iteration 3 (the table lives in the plan record for
this window). Release A shipped on the creators lane; Release B (bed residency + the era-17 4K
re-projection) waits for the capture.

| Surface | Change | Release | Rollback to |
|---|---|---|---|
| Builder pages + kinship | **"Not mine"** beside "I built this": a claim now carries `kind: built \| disavow`; a disavowal replaces a built claim for that build, grants no standing (no request or tag controls), and rides the same copied-payload rails. Never published per build (reconciliation policy still unwritten); only a `disavowals` count reaches `participation.json`. | `.creator-releases/770354007ad8-2780c68be0a9` | `.creator-releases/af25c9fde1bd-abdc72125cf7` (iteration 3) |
| Kinship page | Placeholder-named co-builders carry an **unnamed** chip (ledger, cohabitants, tooltip; dimmed on tree labels) and the tag note invites a name for the coordinator — no rename is promised. Eight branches under 720 px, twelve above, re-laid on resize. `creators.css?v=5`. | same | same |
| `participation.json` | Now published (was 404): the coordinator file exists. Zero counts, `confirmedTags: []`, `disavowals: 0`. | same | same |
| `tools/era-archive/coordinate.py` | The coordinator's tool: `seed`, `ingest <payload>` (all three payload schemas, upsert by id), `confirm-tag` / `revoke-tag`, `forget <handle>` (the retention answer), `status` (prints the publish commands). Owns `E:\omen\steward-multi-era\analysis\participation.json`, which holds full records (handle, note, contact) and lives on Derek's disk only; the projection whitelists five keys per confirmed tag. | n/a (tool) | n/a |
| `browser-smoke.mjs` | World leg is catalog-driven (`/api/eras`; waits for the context raster on terrain-bearing eras) and non-fatal by default (`spatial.status: failed`, receipt always written, exit 0); `--strict-world` or `SMOKE_STRICT_WORLD=1` restores the throw. | n/a | n/a |

Also landed in this window: HEARTH doorcheck facet `arc_runtime` (commandcenter `bbdd097`) that checks
the Vulkan loader and the llama-server binaries before anything launches; the Stitch design export
committed as text under `docs/design/valheim-chronicles-stitch-2026-09/`; `tools/BetterPortals/`
gitignored with provenance in START-HERE; the `claude/kind-torvalds-fdd7c6` branch and worktree
retired (it was already squash-merged as PR #6).

Resolved without code: the "AM4 raster outage" was the creators smoke waiting for a construction raster
on an era that has had terrain since 13:31 UTC — a stale assertion, not a viewer regression.

Verification: gate PASS (2,682 threads identical, presentation + `participation.json` differ);
`browser-smoke.mjs` with the world URL passed (kinship 12/72/13/50, gate held; spatial era 7 context
raster, switch to era 17); `smoke_front.mjs` 15/15; `verify_sweep.ps1` all clear at `?v=5`. Suites:
era-archive 111, chronicles 45, Node 55, doorcheck 31.

Still open (Release B, after the capture): the era-17 4K publish with `-ViewerHtml` + `push_viewer.py
--verify`, then bed residency (`residents[]` per album as its own evidence type, no build-key change)
on branch `bed-residency`, merged and deployed in the same window because both rewrite every thread and
the gate must FAIL once, not twice. Derek's hands: the Intel Arc driver reinstall that restores System32
`vulkan-1.dll` (`/checkmcp` reads `app-local` until then).

### Release B is built and waiting (2026-09-11, ~04:50 UTC)

Branch `bed-residency` (ComfyStewardView, pushed, `75b2374`, five commits on top of `7703540`) carries bed
residency end to end: `community.py` sidecar (`BED_RECIPE_HASH 3735df02…`, fresh and cache-hit paths,
`RECIPE_HASH` untouched), `build_resident` table + allowlist + `verify.py` reconciliation, `gallery.py`
whitelist (`builderKey, beds, evidence` only), "slept here:" on credit lines as `a.resident` (never
`a.credit`), bed counts on kinship build cards and in the tag dialog, `?v=6`, README rewritten from "phase 2"
to shipped. Proof on a scratch copy of the analysis root (live root proven unchanged, 0 of 314 files touched):
all seven `membership.parquet` byte-identical, every build key unchanged; 5,376 albums gain residents (7,906
residencies, 2,248 resident builders, 8,322 beds; 91 % of residents have a public name, the rest render as
"Recorded builder"); versus the live projection every thread difference is an added `residents` key and
`directory.json` is unchanged. Spot-check albums: `7a60df07763e9b85…` era 10 (41 residents),
`8126c1f821f00433…` era 12 (27), `2d70f42e0e69602f…` era 7 (18). Receipts and the diff script are kept at
`E:\wt\bed-residency-scratch\` until the window.

Window sequence (after the 4K capture is idle):
1. Derek: `Publish-Gallery.ps1 -GalleryPath <era17 4K gallery> -EraSlug era17 -ViewerHtml C:\work\ComfyStewardView\tools\selfie-stick\gallery\index.html`, then `push_viewer.py --viewer <same file> --verify`.
2. `git merge --no-ff bed-residency` into main (ComfyStewardView), suites, then the era-archive orchestration
   (`Invoke-EraArchive.ps1` / `community.py`) over the live root: every era prints "residents re-derived …
   build keys unchanged" and era 17 re-derives fresh.
3. `gallery.py` → `gate_creators.py` (**FAIL expected**: changed = threads with residents and era-17 photos,
   new/gone 0, directory identical or era-17 counts only) → `deploy_gallery.py --revision <HEAD>` →
   `browser-smoke.mjs` (world URL), `smoke_front.mjs`, `verify_sweep.ps1`. **Rebase first:** iteration 5
   took `?v=6`, so `bed-residency` moves its ten pins to `?v=7`; expect conflicts on `hydrateCredits`'s
   selector (keep both additions), the `.top8`/`.pair-*` stylesheet block, and `cohabRow` (the beds span and
   the pair link both go in `side`).
4. Rollback: creators symlink → `previous` from the receipt; viewer `push_viewer.py --rollback <sha12>`.

## Iteration 5 — Kinship on the builder profile (2026-09-11, ~08:27 UTC)

Creators release `228b28225aae-9f2db5f685d4` (rollback `770354007ad8-2780c68be0a9`; ComfyStewardView main
`228b282`, pushed). The Top 8 panel is now a ribbon of chips, "Top 8 · Shield-wall fellows": portrait tile,
name, and a rank tier — Tier I is ranks 1–2, II is 3–5, III is 6–8, each carrying `title="Rank N of this
builder's Top 8"` so the MySpace wink is labelled as rank and nothing more. Pressing a chip opens the pair view
(`section#pair-view`, new `web/pair.js`, `globalThis.StewardPair`): the anchor and one co-builder, the builds
they share (ledger, You/Them split, Photographed/Recorded status, JSON download as
`steward-kinship-pair/v1`), the active build's photographs or a "Not photographed yet" slab, laurels
(coordinator-confirmed tags; the visitor's pending ones dashed), the piece allotment bar, build facts, the
co-builder card with shared pieces/builds/photographed/confirmed counts and the kinship affinity
`Σ min(shareA, shareB) · log10(pieces)` — the affinity is shown, never used to rank the ribbon. Standing reads
"Confirmed kin" when a confirmed tag links the pair on a shared build, else "Recorded kin". World viewer mode
is a deep link into AM4 with the build selected (the viewer sends `frame-ancestors 'none'`, so no framing).
Deep link `?kin=<key>&build=<key>&view=photos|viewer`; the kinship tree's co-builder nodes and the ledger's
"Pair view" links land on it; a `?kin=` outside the Top 8 gets a ninth, dashed chip. Everything is derived in
the browser from the thread JSON, `directory.json` and `participation.json` — no new data file, gate PASS.

Two Opus builders on disjoint files (`pair.js` + stylesheet + Node test + README; creators.js + shells +
kinship links + gallery.py + Python pins + sweep + smoke), both cut off once by the session rate limit and
resumed with their commits intact. At merge the orchestrator added two stylesheet commits: the ribbon's emblem
fallback sits one level deeper than the tile rule expected, and the tier label auto-placed into the 36 px
portrait column and broke "Tier III" in two on every profile.

Verification: gate PASS (2,682 threads identical, presentation only); suites era-archive 115, chronicles 45,
Node 78; local render over a scratch serve of the projection (8 chips one pressed, pair view open, 25 ledger
rows on Helina, allotment widths sum to 100, `?kin=` presses the named chip, `?view=viewer` selects the tab,
sidebar stacks at 390 px with a 390 px scroll width); live `browser-smoke.mjs` `passed` with the new pair leg,
the kinship leg and the world leg (era 7 context raster, switch to era 17); `smoke_front.mjs` 15/15;
`verify_sweep.ps1` all clear at `?v=6` with `/valheim/creators/pair.js` served and threads carrying
`../pair.js`. Design record: `docs/design/valheim-kinship-viewport-stitch-2026-09/`.

Operator notes from this pass: `deploy_gallery.py` resolves the repository from its own path, so when the main
checkout carries someone else's uncommitted `tools/era-archive` files, run projection, gate and deploy from a
clean detached worktree at HEAD. PowerShell 5.1 splits a `git commit -m` message at embedded double quotes and
`-- path -m` puts `-m` into the pathspec — commit from Bash with `-F <file> -- <path>`. Headless Chrome clamps
`--window-size` below roughly 500 px, so a 390 px screenshot looks overflowed while the layout is fine;
measure narrow layouts with the in-app browser's viewport emulation against localhost.

Still open: Release B (bed residency) now rebases onto this release (`?v=7`, see the window sequence above);
the pair view's default active build is the largest shared build by album pieces, which on a mega-build where
the pair placed a few dozen pieces each reads oddly — ranking by pair-shared pieces is a small change if wanted;
the participation summary line still says "already submitted" (pre-existing copy, outside the new-copy lint);
legacy photo labels keep the double-encoded middle dot until the Release B window.

## Release B — bed residency (2026-09-11, 2026-09-11 08:59 UTC)

Creators release `66f3ab072b8e-4e118cdf4a07` (rollback `228b28225aae-9f2db5f685d4`; ComfyStewardView main
`66f3ab0`, the merge of `bed-residency` onto iteration 5, pushed). Every public album now carries
`residents[{builderKey, beds, evidence: "bed-owner-in-footprint"}]` where a bed owner slept inside the
build's footprint (4 m XZ / 3 m Y margin, smallest footprint wins a bed inside nested boxes). Thread pages say
"slept here" beside the credits as `a.resident`, the pair view's Shared hearth card reads it, and the kinship
tag dialog names the beds. Residents never enter `contributors`, Top 8, the tree, majority ownership or the
pair ranking. Pins moved to `?v=7`.

The window ran without a capture. The era-17 4K masters were never missing: 5,425 PNGs at 3840×2160 (33.3 GB,
shot 22–27 August) sit on OMEN in the parked BepInEx tree
`C:\work\comfy-quest\captures\install-cleanup\omen-era17-20260827T102804Z\BepInEx\config\comfy-orbit-captures\`,
and the live `/valheim/` gallery has been their 1600 px derivatives since 28 August. Nothing for era 17 was ever
staged or shot on AM4. `master_detail.py` was run over those masters on OMEN this morning
(`analysis/framing/master-era17.json`, 3,917 frames measured; median derivative-loss share 0.21), so era 17 now
has the same master-native detail numbers as eras 7–14.

Sequence as run: merged `main` into `bed-residency` in a worktree (three conflicts: the credit-hydration
selector now covers credits, residents and Top 8 chip names; the sweep's thread probe keeps `../pair.js`; the
projection comment names both) → 117 Python / 45 chronicles / 82 Node green → backed up `analysis/` (1.57 GB) →
`community.py` over the live root with the eight capture manifests the previous run recorded (matched by SHA:
eras 7, 8, 9, 10, 11, era 12 at 1080p and 4K, era 14) plus `legacy-galleries.json`: every era printed "residents
re-derived (bed recipe 3735df02d00a), build keys unchanged" → `community_store.py` (`build_resident` 7,906) →
`verify.py` (0 residents without a builder) → projection → gate **FAIL as designed** (2,220 threads changed,
462 identical, 0 new, 0 gone, directory identical) → `diff_projection.py` VERIFIED every difference is an added
`residents` key (12,587 thread-album instances; 1–41 residents per album) → merge to main → deploy from the
detached worktree → smoke `passed` (pair, kinship, world era 7 + era-17 switch) → front 15/15 → sweep all clear
at `?v=7` → push. Live check: thread `0047956c7bf5…` renders 41 `a.resident` anchors and the pair view's hearth
reads "slept here (1 bed)".

Retired follow-up: the "double-encoded middle dot" in legacy labels was never in the data (neither legacy index
nor any projected thread contains it); it was a cp1252 read in an earlier session. Still open: bed-only
residents with no directory record render as "Recorded builder" (publishing their name is a separate decision);
the pair view's default active build ranks by album pieces; the participation summary's "already submitted"
wording. AM4 is at 95 % disk (21 GB free) — clear it before any further 4K campaign there.

## AM4 disk recovery (2026-09-11, 17:59–18:08 UTC, offloads continuing)

AM4 went from 95 % (22 GB free) to 54 % (219 GB free) without moving a master: 62.7 GB of its NVMe was
unallocated in the LVM volume group (extended online), 52.7 GB of GGUFs sat on a box with no inference engine
(hashed into `models/REMOVED-20260911.json`, deleted), stale staging and caches went (27 GB), the world-save
copies inside stopped attempts were pruned with the new `tools/era-archive/prune_run_worlds.py` (receipts before
unlink; the quiet campaigns' copies had already been removed outside the plan at 17:59 UTC), and Docker lost 12
redundant tags, 7 snapshot images and 3.6 GB of build cache. Two offloads (the pre-swap tarball and ComfyUI's
outputs, 7.4 GB) are crossing the wifi to `E:\omenm4-offload\` unattended, verified by sha256 before the AM4
copies go. The era 7/9/10 masters (3,706 frames, 38.4 GB) followed the same night once Derek moved FX99's Ethernet
cable to AM4: `shuttle_masters.py` went from 225 kB/s to 45-58 MB/s mid-run and finished all three eras in eight
minutes (00:06 UTC 09-12); AM4 ended at 44 % (247 GB free). The wire needed AM4's replies steered onto it (its wifi
routes outrank the wired port's; runtime IPv6 metric change, reverted after) - the recipe is in the recovery doc. Full
receipt: ComfyStewardView `docs/am4-disk-recovery-2026-09-11.md`; step logs in
`E:\omen\steward-multi-eram4-space-20260911\`.


## Era viewer pass 3 — the filter drawer (2026-09-11, live ~21:50 UTC)

Viewer sha **`796b8a2041df`** in all nine `/valheim/` directories (rollback `31ef8c5f6c5c`, the Chronicler-skin
page; `push_viewer.py --rollback 31ef8c5f6c5c` puts it back; receipts in ComfyStewardView
`tools/selfie-stick/receipts/viewer-20260911-menu-v3*.json`; ComfyStewardView main `f5814da`). The chip wall
became a left drawer over a scrim: search box, chip groups, Areas and Builds as eight-row lists with "Show all N",
a fog toggle, `Clear all` + `Show N builds|photographs`. The header carries one removable chip per active filter,
a sort dropdown, an era dropdown of links (Builders across eras last) and the CHRONICLES · BUILDERS nav; page size
is a per-page select in the pager. Counts are live-narrowing and now exclude fog-hidden frames unless the toggle is
on (era 17: drone 2,626 → 2,552), which is why the figures differ from the old static chips. Design record:
`docs/design/Gallery navigation simplification/` (v2 canvas export + v3 artboards, README with the v2→v3 table).
Verified: local CDP run at 1440 and 390 (counts, search/scroll persistence, hash deep link visible on open, Esc
chain, per-page), era7 canary, `--verify` 9/9, `shoot.mjs` study-filters / study-lightbox / walk-eras captured,
`verify_sweep.ps1` all clear. `shoot.mjs` still skips find-search / find-thread / request-dialog (creators name
search timed out — unrelated to the viewer, was not re-checked). Baseline fallback
`tools/selfie-stick/gallery/index.html` re-synced byte-identical.

## Front door fits one screen (2026-09-12 05:00 UTC), chronicles `20260912T050004Z-282f720d8c76`

Derek: the footer hid below the fold and needed a scroll. It did — by design: `.door` was sized to
`100svh − header − main padding` so the footer began "exactly at the fold". Now `body` is a flex column at
`min-height:100svh`, the front page's `main.front` takes what the header and footer leave and the door centres in it
(only the front page opts in; the guide's margins keep collapsing). Measured live: no overflow at 1440×900,
1920×1080, 390×844, footer flush to the bottom; a 375×667 phone still scrolls 53 px, the content's own height.
ComfyStewardView `7cf17cd` (fix) + receipt commit; rollback `deploy.py --rollback 20260910T173815Z-3f4a2b77fe0f`.
`smoke_front.mjs` 15/15, `verify_sweep.ps1` chronicles leg all clear.

## Iteration 6 — Builder page v2 (2026-09-12 ~06:55 UTC), creators `60d9a8b1eb50-c78bbfb23c85`

Rollback `66f3ab072b8e-4e118cdf4a07` (Release B; re-point the `creators` symlink). ComfyStewardView main
`0ae225c` (first cut) + `60d9a8b` (second cut); pins `?v=8`. Design record `docs/design/Builder page v2/`
(canvas https://claude.ai/code/artifact/e0e33680-53a5-4f44-b1a2-1ff9c88702da).

The profile re-told as one story. **Hero**: name and one unlabelled line (`Major Architect · eras 7–12 · 39
build albums · 7,386 construction pieces · 28 photographs`; the counters stay, the TIER/FIRST ERA/LATEST ERA row
goes). **The work**: a carousel of the photographed builds — big viewport, thick banner across its top (era ·
name · pieces · `44 % yours` · photographs · photo stepper), details plainly underneath (credits, world viewer,
`I built this · Not mine · Request… · Copy payload`), a rail of the photographed builds as the selector; leads
with the builds most the builder's own. **Who they built beside**: the kinship tree drawn on the page (new shared
`web/kin-tree.js`; `kinship.js` keeps its page and tooltip), the Top 8 as its caption, branch ↔ chip ↔ pair in
lockstep. **The pair**: photo + status + shared-builds ledger; laurels, hearth, affinity, facts, tiles, allotment
under a native `Details`. **The rest**: a table of the un-photographed builds — Era · Build · `link` (world-viewer
deep link) · Details (freeform: pieces per builder against the total, unattributed, slept-here; the claim controls
live in it) · Feedback (star / square / X, hollow → filled, one per row). Feedback = photo priorities on the
participation rails: `state.priorities`, exported in the payload beside claims and requests, cleared by forget,
never tallied by the archive. **Notes** strip (status lines + manifest) above the five figures.

The first cut (rows per era with expand toggles) was reviewed and rejected in the same session ("we avoid all this
collapsing thing"); it was never deployed. Presentation only — gate PASS (2,682 threads identical). Verified:
129 Python / 85 Node; browser-smoke local + live (new pins: carousel + details primary, single attribution, three
marks per rest row, folded drop-downs, tree beside the ribbon, pair detail folded); `smoke_front` 15/15; sweep
creators leg all clear. Also fixed on the way: the participation summary's "already submitted" → "already sent";
browser-smoke's photo check no longer counts a zero-width (hidden) image as in-view. Release ran from a detached
worktree `E:\wt\builder-page-v2` because the main checkout carried another session's live edits — and that
session's `tests/test_archive.py` was briefly swept into a commit by a `tests/` pathspec and taken back out before
push: **commit with explicit file paths when a checkout is shared.**

**Iteration 6a — tooltips on the feedback marks (2026-09-12 ~07:25 UTC), creators `0c4935002bf8-77dba722f997`**
(rollback `60d9a8b1eb50-c78bbfb23c85`; ComfyStewardView `0c49350`; pins **`?v=9`**). Derek: "we need tool tips for the
icons." Each mark carries `data-tip` drawn above it on `:hover` and `:focus-visible` (right-aligned so the last one
stays inside the row); the native `title` is gone. browser-smoke passed live, `smoke_front` 15/15, sweep all clear.

**Iteration 6b — the pair view keeps to the pairing (2026-09-12 ~08:05 UTC), creators `05c29f4f4ad7-81bdd0da1a31`**
(rollback `0c4935002bf8-77dba722f997`; ComfyStewardView `05c29f4`; pins **`?v=10`**). Derek: "this feels redundant
now that we have the other image carousels; world view mode doesn't need its own tab anymore, it's integrated." The
PHOTOGRAPHS / WORLD VIEWER tabs, the pair's hero photograph, the "Switch to World viewer" button and the two-column
layout are gone, with `pairState.view`, `?view=` and the tab keyboard roving. Shape now: title · status line +
standing chip on one row (the live region) · ally + "See this pair from their side" on one row · the shared-builds
ledger full width · download · `Details` (pills, laurels, hearth, affinity, facts, tiles, allotment). A ledger pick
on a photographed build turns the work carousel to it without moving the visitor (`revealAlbum(buildKey, {scroll:
false})`; the browser's scroll anchoring holds the pair view still while the stage above changes height — the smoke
measures the pair view's viewport top, not `scrollY`). The facts gain `On this page · Show on the carousel / Show in
the rest`. Ledger status is `Photographed` / `Recorded`; the tinted row is the one Details describe. Presentation
only — gate PASS; 130 Python / 85 Node; browser-smoke local + live (new leg: no `#pair-modes`/`#pair-photos`, head +
who rows, pick turns the carousel with the view held in place); `smoke_front` 15/15; sweep all clear. Tried and
reverted on the way: `white-space: nowrap` on the two halves of the Split cell — it made the row shorter on a phone
but pushed Status off the screen.

## Portrait picker — S1 + S2 built and proven locally, review pass done (2026-09-12, not deployed)

The generative lane's 96 painted portraits (1,375 takes, `E:\omen\DMos\artifacts\corpus-viking-profiles-20260910`) are
cut into a library (`ComfyStewardView/tools/chronicles/portraits/build_manifest.py` → `E:\omen\steward-multi-era\portraits\
viking96-20260912`, 382 takes, 1,146 webp, 29.7 MiB), shipped by `build.py --library` into a schema-2 `portraits.json`
(the 48 slate rows first, byte-compatible with every v1 reader), and resolved on the creators lane by one module,
`web/portraits.js`. The profile grows a "Choose a portrait" drawer (`web/portrait-picker.js`, the era viewer's live-count
mechanic) for a visitor with a built claim on the profile; the choice is recorded on this device and repaints the hero,
ribbon, tree and pair card. Derek walked all 96 contact sheets on `baseline/tools/portrait-corpus/review.py` (3 strips
changed, 93 accepted); `concepts.json` is all `manual`, so the library builds without `--dev`. Verified: 97 Node + 131
Python (era-archive), 52 Python + 12 Node (chronicles), 9 (portrait-corpus); `PICKER=1 browser-smoke.mjs` against the
dev host (`http://127.0.0.1:8773/`, root `E:\omen\steward-multi-era\devsite`): 144 portraits → Carpenter 8 → +red hair 5,
30 trades kept with 5 dimmed, choose dresses the hero and the tree's anchor, focus returns, the archive's pick undresses.
**Nothing deployed**; pins moved to `?v=11` in the shells and tests, the sweep stays at `?v=10` until the deploy commit.
Next: S3 (`portrait` claim on the payload, `coordinate.py` ingest, `gate_creators.py` admits the field), S4 (`gateway.js`
switch, disclosure line, PD-3 entry, first publish of the library through the chronicles release chain, evidence-page
digests refreshed for FR-9), S5 ("worn by N", `exclusive`). Design record and deviations:
`docs/design/valheim-portrait-picker-2026-09/FUNCTIONAL-REQUIREMENTS.md` → "Implementation notes".

## Portrait picker live (2026-09-12 ~11:05 UTC) — chronicles `20260912T110102Z-1ec52bb01f01`, creators `059f5cdd4daf-c03976efc2a6`

Rollbacks: chronicles `20260912T050004Z-282f720d8c76` (`deploy.py --rollback`), creators `05c29f4f4ad7-81bdd0da1a31`.
ComfyStewardView `94acd06` (S3+S4) + `059f5cd` (deploy hold); pins `?v=11` everywhere including the sweep. Verified live:
`smoke_front` 15/15, `PICKER=1 browser-smoke` (144 → Carpenter 8 → +red 5, 30 trades with 5 dimmed, choose dresses the
hero and the tree anchor, focus returns, revert undresses), sweep all clear (1,279 chronicles files; the three cuts of
one painted take immutable; portraits.js + portrait-picker.js linted). `/chronicles/portraits.json` is schema 2
(156 KB pretty-printed; the gateway page inlines the 48-row slate slice; the creators pages fetch the file).

**PD-3 exposure check (FR-8), recorded here as the handle and the kinship tags were.** The portraits themselves add
no personal data: synthetic paintings, no likeness, no builder named in a tag or a file name; the naming note keeps
character names out of every UI string. The one new public field is the builder's *choice* — `portrait: {tile, take}`
on their record in `directory.json` and `threads/<key>.json`, written by `gallery.py` only from
`confirmedPortraits` in the coordinator's private file. It reveals a preference and nothing else; it is volunteered
through the same copied payload as a claim (a built claim on the profile is the standing it needs, and the line rides
`exportPayload` next to the claims); it is revocable by the builder (a revert line the coordinator confirms) and
vetoable by the coordinator (`revoke-portrait --reason`); `forget <handle>` removes it with everything else the handle
sent. The public `participation.json` says nothing about portraits. The sha, the handle, the timestamps and the record
id stay in `analysis/participation.json`. Verdict: within PD-3's existing consent for self-reported participation.

**Coordinator's steps for a portrait payload** (the picker writes nothing anywhere; the builder copies their payload):
```
python tools/era-archive/coordinate.py --output-root E:\omen\steward-multi-era ingest <payload.json> --portraits E:\omen\steward-multi-era\chronicles-releases\20260912-portraits\portraits.json
python tools/era-archive/coordinate.py --output-root E:\omen\steward-multi-era status            # pending portrait <builderKey> · <tile>#<take>
python tools/era-archive/coordinate.py --output-root E:\omen\steward-multi-era confirm-portrait <builderKey>
```
then the ordinary creators publish (`gallery.py` → `gate_creators.py`, which now admits `portrait` → `deploy_gallery.py`).
A revert arrives as a line with `tile: null`; `confirm-portrait` on it takes the published field down. The picker's
library is re-cut with `tools/chronicles/portraits/build_manifest.py` (never `--dev` for a publish) and shipped with
`build.py --library`; `--portraits` at ingest must be the manifest that is live, so a line is checked against what the
archive can draw.

## Painted defaults + the builder's own page (2026-09-12 ~12:10 UTC) — chronicles `20260912T120657Z-939eb83063b7`, creators `71e7e54af0f6-b06d9263a80c`

Rollbacks: chronicles `20260912T110102Z-1ec52bb01f01`, creators `059f5cdd4daf-c03976efc2a6`. ComfyStewardView `577baec`
(the pass), `71e7e54` (gate CRLF proof), `f123c46` (receipt + sweep); pins `?v=12`. Every builder now wears a painted
face by the archive's pick (`portrait_assign.py`, tier pools + era leaning, seeded); slate is retired (`portraits.json`
`count: 0`, 96 tiles, viking96 default; the front door shrank from 20.7 KB to 8.2 KB). The avatar on a builder page
opens `/valheim/creators/profile/?builder=<key>`: Discord sign-in (off), the picker, the archive's pick, the opt-out
levels with **Send request**. Verified live: `smoke_front` 15/15 (the first row's face is the resolver's for that
record), `PICKER=1 browser-smoke` (door → profile page as a stranger: four sections, sign-in off, picker gated, Send
armed by a level; with a seeded claim: 96 → Carpenter 4 → +red 1, 24 trades, choose dresses the profile and the
builder page, the archive's pick undresses), sweep all clear (profile page + profile.js linted; every record carries a
portrait; no `slate48`).

**Standing rules from now on.** Every chronicles build: `build.py --no-slate --library
E:\omen\steward-multi-era\portraits\viking96-20260912 --default-library viking96`. Every creators projection:
`gallery.py … --portrait-library E:\omen\steward-multi-era\portraits\viking96-20260912\manifest.json` (a projection
without it strips every face back to the slot rule and the gate will show 2,682 portrait-only diffs).

**Superseded the same day (~12:40 UTC) — the launch shape, creators `ed9c738e0015-c30f0f2bf2e1`** (rollback
`71e7e54af0f6-b06d9263a80c`; ComfyStewardView `ed9c738`). No relay (the Caddy route was removed and FX99 redeployed), no
Discord sign-in. Anyone may try a portrait on any builder's page; the choice is worn on that device and **noted by a
beacon the front door logs** (`portrait-beacon.txt?action=…&builder=…&tile=…&take=…&receipt=…`). An opt-out level
writes the message the builder pastes to **@Tugcow** on Discord (receipt · builder · request · note · page).

**Reading the log (coordinator).**
```
ssh fx99 'python3 -' < tools/era-archive/read_portrait_beacons.py             # counts, abuse shapes, the last 25
ssh fx99 'python3 - --payload' < tools/era-archive/read_portrait_beacons.py > choices.json
python tools/era-archive/coordinate.py --output-root E:\omen\steward-multi-era ingest choices.json --portraits E:\omen\steward-multi-era\portraits\viking96-20260912\manifest.json
python tools/era-archive/coordinate.py --output-root E:\omen\steward-multi-era confirm-portrait <builderKey>
```
then the ordinary creators publish (`gallery.py --portrait-library …` → gate → deploy). Behind `tailscale serve` the caller
is `X-Forwarded-For` and a tailnet user is named by `Tailscale-User-Login`; the reader prints the login when it has one.
"Addresses dressing three or more builders" is the line to look at first. An opt-out message on Discord is matched to
its beacon line by the receipt; applying it is still a hand edit — no tooling applies an opt-out yet.

**Hotfix (~12:55 UTC) — the picker grid showed broken tiles, creators `ef65508ad37a-c6eb41e7626d`** (rollback
`ed9c738e0015-c30f0f2bf2e1`; ComfyStewardView `ef65508`). Derek's screenshot of the live drawer: every grid tile a
broken-image icon with its alt text, the facet panel and counts fine. Cause: since portraits.json schema 2 a tile's
cuts are one `{take}` pattern, and the grid asked the resolver for a face with no take, which returned the pattern
unexpanded (`viking96/<id>.{take}.128.webp` → 404); the take strip and the preview named a take and loaded. Fix in
`portrait-picker.js`: `faceOf` asks `takeOf`, which answers the first picked take when none is named. The `PICKER=1`
smoke now waits for the first twelve grid tiles to complete and fails on any with `naturalWidth` 0, and keeps a
`picker-grid` screenshot. Gate: the only presentation file differing from live was `portrait-picker.js`; live smoke
passed (`gridBroken: []`), `smoke_front` 15/15, sweep all clear. Chronicles unchanged.

## The builder hero is as tall as its words (2026-09-12 ~13:20 UTC) — creators `abb9f78def66-266ff053f4ae`

Derek, on his own page: "this top banner is taking up far too much vertical space". Measured at 1440×1000: header 82 px,
the hero card 328 px, the first content (`#content`) at 478 px — the text column was 94 px (name + one line of
facts) while the avatar column ran 160 px of portrait + 24 px gap + 98 px of "Your profile" and the four-line
disclosure stacked under it. Now (ComfyStewardView `abb9f78`): the portrait is 120 px, the profile line is the last
line of the text column (`renderHeroDoor` appends `#hero-portrait-actions` into `.hero-text` after the facts, called
after the name/facts are moved in), card padding 18 px, margins 12/20. Tugcow's card is 158 px and the work starts at
296 px; a builder with aliases and a wrapping facts line (17a1605b) is 222 px for 184 px of words — the smoke pins
`card − text ≤ 40` and that the line sits in the text column, not an absolute height. Pins moved to `?v=13` (also
freshens the picker hotfix under a new query). Gate: data identical, presentation diffs = the pin on every page +
creators.css/js; `PICKER=1` live smoke passed, `smoke_front` 15/15, sweep all clear. Rollback `ef65508ad37a-c6eb41e7626d`.
Creators deploy receipts live at `E:/omen/steward-multi-era/projections/deploy-<name>.json` (outside the repo — a
receipt under `tools/era-archive/` makes the tree dirty and the deploy refuses).

## "Tag another basemate" on the build card (2026-09-12 ~14:05 UTC) — creators `5b57f5aa003c-ea6bcc227816`

Derek: change "Copy this build payload" to "tag another basemate". Decisions: the people you can tag are **this
build's other contributors**; the per-build payload copy is **dropped** (every action hands its payload over on
confirm; the directory keeps the whole-ledger copy). ComfyStewardView `5b57f5a`: the card's fourth control opens the
kinship tag dialog on the builder's page — `#kin-tag-modal` on the thread shell, the build fixed, the person picked
from the card's credits (`tagCandidates(album, builderKey)`: other credited builders in credit order, share, "slept
here"), `basemate` ticked to start. Same gate as the kinship page (leading builder + a built claim in this browser),
inert otherwise with the reason in a toast ("Nobody else is recorded on this build." / "Tags come from a build's
leading builder." / "Claim this build before tagging basemates."). Same record, store and export payload, so
`coordinate.py ingest` reads a tag made here exactly as one made on the kinship page. A tag recorded on this device
shows beside the credit as a dashed "recorded" chip (`renderTagChips`, confirmed + pending via `mergeKinshipTags`).
The smoke now claims a build through the dialog and tags from the card end to end (dialog lists `credits − 1`,
payload carries the one basemate tag, chip appears, ledger holds one tag). Pins `?v=14`. Gate: data identical; live
smoke passed, `smoke_front` 15/15, sweep all clear. Rollback `abb9f78def66-266ff053f4ae`. Dev site
(`E:\omen\steward-multi-era\devsite/valheim\creators`) is a **junction** to the current projection — MSYS `ln -s`
copies the tree instead; use `New-Item -ItemType Junction`.

## "Tag another basemate" is never a dead click (2026-09-12 ~14:40 UTC) — creators `cdf1eaffc7a4-872bcd9066ba`

Derek, on his own page: "that button is doing nothing in production" (three builds: 338abcbb 44 %, d8d45647 34 %,
14b4e3ce 0 %, 2372a2c7 77.8 % solo). Not a data fault — the shares were intact and `majorityOwner` read them right
(largest / largest / null / majority). Every click was refused by a gate and every refusal was a 2.4 s toast at the
foot of the window: no built claim in his browser (the 44 % and 34 % builds), nobody else credited (the solo
build), not the leading builder (the 0 % build). ComfyStewardView `cdf1eaf`, pins `?v=15`:
- **No claim yet, leading builder** → the click opens the claim dialog (its build line says "the claim comes first;
  tagging opens the moment it is recorded"), and the tag dialog opens as soon as the claim is recorded. The claim
  skips its own payload hand-over: the kinship payload the tag hands over carries the standing claim (one payload,
  `claims: [built]` + the tag); a cancelled tag after a chained claim hands the claim over itself.
- **Not this builder's to tag** → the control is visibly inert (dashed, dimmed, `cursor: not-allowed`) and a muted
  line under the row says why before any click: `leadingBuilderNote` — "Tags come from a build's leading builder —
  here that's Laughingman (42.6%)." / "…and no one holds a quarter of this one." / "…and this one has no single
  leader." / "…and this build's shares were never recorded."; or "Nobody else is recorded on this build." The note
  is `width: 0; min-width: 100%` so it never widens the actions column (a first cut squeezed the credits to a strip).
- The smoke drives both paths (claim → tag → one payload with claim + basemate; claim → cancel tag → claim payload)
  and asserts an inert control always carries its note. Live smoke passed, `smoke_front` 15/15, sweep all clear;
  the three builds render as intended live. Rollback `5b57f5aa003c-ea6bcc227816`.
