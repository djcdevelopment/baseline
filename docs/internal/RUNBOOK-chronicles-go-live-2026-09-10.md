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
3. **Creators**: re-project, run the data gate (`E:\wt\gate_creators.py --projection <dir>`
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
