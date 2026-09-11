# Valheim Chronicles — Kinship Viewport (Stitch export, September 2026)

The second design drop for the public archive: a "Kinship Viewport" on the builder profile,
drawn with a design agent after the kinship tree shipped. This directory is the committed
record; the token sheet is the same `DESIGN.md` as the first export and lives in
[`../valheim-chronicles-stitch-2026-09/DESIGN.md`](../valheim-chronicles-stitch-2026-09/DESIGN.md).
The rendered screen stays outside git at `E:\omen\design-exports\kinship_phase2\screen.png`.

| Path | What it is |
|---|---|
| `kinship-viewport-mock.html` | The Stitch screen as static HTML (Tailwind play CDN, Google Fonts, Material Symbols — none ship). |
| `kinship-viewport-spec.md` | The agent's "dual-mode" specification: a React/FastAPI/WebSocket contract with a `GET /api/v1/kinship/viewport` payload, a log-weighted kinship score, and a "zero-trust" hash badge. Read the *payload shape* as intent; the transport is not built — the archive is static JSON behind Caddy by design. |

## What shipped from it (iteration 5, 2026-09-11)

The mock is a **pair view**: the profile's builder and one co-builder, their shared builds, the
split of pieces on the active one, its photographs, and the pair's standing. All of it is derived in
the browser from the thread JSON, `directory.json` and `participation.json` the archive already
publishes (`tools/era-archive/web/pair.js` in ComfyStewardView).

| Mock region | Shipped as | Data |
|---|---|---|
| "Shield-Wall Fellows (8 Bonds)" ribbon | The Top 8 restyled as a ribbon of chips; rank tiers I/II/III labelled as rank (a MySpace-style wink) | `computeTopEight`, unchanged ranking |
| Photographic Chronicle | Photographs mode: the active shared build's photograph, laurels (coordinator-confirmed tags), shared hearth (bed residency, once Release B lands), kinship affinity, build facts | album photos, confirmed tags, residents, shares |
| Architectural Blueprint & Codex | World viewer mode: a deep link into AM4's viewer with the build selected (the viewer refuses framing), plus the piece allotment bar | `worldUrl`, contributors |
| Allied Master Builder dossier | Co-builder card: portrait, name, tier, affinity, metrics, reverse pair link | directory record |
| Joint Monument Ledger | Shared builds ledger with the You/Them split and a JSON download | shared albums |
| "Alliance: Verified" | "Confirmed kin" when a confirmed tag links the pair, else "Recorded kin" | `participation.json` |
| Skaldic verse, comfort rating, integrity score, achievements, ward keys, crypto badge, presence dot, "Sync Device", material census, CAD pins | Not built — no data behind any of them | — |

The spec's kinship score `Σ min(shareA, shareB) · log10(pieces)` is shown as the pair's **kinship
affinity**; it does not rank the ribbon, which keeps the live shared-pieces order.
