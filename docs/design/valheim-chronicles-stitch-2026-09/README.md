# Valheim Chronicles — Stitch design export (September 2026)

The design record behind the public archive at `https://fx99.tail8e749c.ts.net/chronicles/`,
`/valheim/` and `/valheim/creators/`. Exported from a Stitch canvas on 2026-09-10; the
canvas itself is the working surface, this directory is the committed record. The product
implementation lives in ComfyStewardView (`tools/chronicles/`, `tools/era-archive/web/`);
its `creators.css` token block cites `DESIGN.md` here.

Screens as PNGs are not committed (28 MB); they are kept outside git at
`E:\omen\design-exports\valheim_creators_gallery\<mock>\screen.png` on OMEN.

## What is here

| Path | What it is |
|---|---|
| `DESIGN.md` | The Chronicler Archive design system: surfaces, flame/primary/bronze/tertiary, parchment and outline tokens, radii 4/6/8, Bodoni Moda / Plus Jakarta Sans / JetBrains Mono. The shipped CSS follows it. |
| `stitch-table-of-contents.md` | The canvas's own manifest: `SCREEN_n` ids, intended routes, and the aspirational architecture narrative. Read it as intent, not as a description of what runs. |
| `live-creators-page-extract-2026-09.md` | A text scrape of the live `/valheim/creators/` page the mocks were drawn against. |
| `mocks/*.html` | The 16 Stitch screens as static HTML (Tailwind play CDN + Google Fonts, none of which ship). |
| `aspirational/` | CQRS blueprint, FastAPI/Next.js route spec, NumPy kinship engine, pydantic models, TypeScript SDK, React dashboard. **None of this is built.** The archive is static JSON behind Caddy; claims, requests and kinship tags ride a local ledger and a copied payload by design (see `ComfyStewardView/docs/era-archive/creator-participation-design.md`). |

## Mock → what shipped

| Mock | Shipped as | Decision |
|---|---|---|
| `valheim_chronicles_visual_gateway_character_archive` | `/chronicles/` front door, iteration 1 (six wordless persona slabs + search + "Enter Gallery"), then iteration 2 reduced it to the name box with autocomplete and one "Browse the builds" button | Wordless cards; never "character"/"archetype" in UI text; "more is less" |
| `prologue_archival_codex_*` (three) | `/chronicles/guide/` sections per path; the "?" card opened the guide in iteration 1 | Illustrated "?" card closed (iteration 4, #11) |
| `across_the_eras_builders_directory` | `/valheim/creators/` directory (skin, era ribbon, sort, stats link) | — |
| `ibocain_*`, `tugcow_*`, `reina_borg_*`, `ditseey_*` (profile runestones) | Builder pages: hero card, retro counters, real Top 8, portrait from the 48-tile library, five path cards at the bottom | "MySpace for Vikings" wink |
| Yggdrasil Kinship (pasted mock, iteration 3) | `/valheim/creators/kinship/?builder=<key>`: Tree + Ledger, tags on the claim rails | Circle mode not built (#8); photo-inspect tags not built, `disavow` claim kind instead (#9) |
| `claim_build_attribution_cryptographic_payload` | The existing local-ledger claim flow and copied payload; no signatures | No endpoint until the four preconditions hold |
| `archival_survey_dispatch_discord_webhook_ticket_nexus` | Not built; photo requests ride the same copied-payload path | Coordinator tool `coordinate.py` (iteration 4, #3) replaces the webhook idea |
| `chronological_eras_timeline_world_claims` | Not built as a page; the era row lives on the guide and the era ribbon on the directory | — |
| `thorgaar_the_mason_album_piece_inspector` | Not built ("Core wood > 25" needs a public per-build prefab census, #10) | Closed |
| `persona_happy_paths_taxonomy_flow_matrix` | Persona → entry-point map used to route the front-door cards | — |
| `the_comfy_valheim_archive_emblem` | The inline SVG emblem on every shell header | — |

Decision numbers refer to the iteration 4 table in the go-live runbook,
`docs/internal/RUNBOOK-chronicles-go-live-2026-09-10.md`.
