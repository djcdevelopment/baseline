# Start here — what's live, what's paused, what's history

One page, one purpose: stop you from acting on the wrong era. Every area below is tagged
**LIVE** (running or actively maintained), **BUILT — not deployed**, **STOPPED** (real, but not
running right now), **PAUSED** (hard hold with a written resume path), **COCKPIT** (operator
session state, not durable docs), or **HISTORICAL** (kept honestly, describes a past era).
Updated 2026-08-06.

If you're a newcomer rather than an agent or contributor, you want
[`README.md`](../../README.md) instead — it has three doors, one per audience. This page is
the era map, not a welcome.

## The public surface

| Origin | Status | Notes |
|---|---|---|
| `https://am4.tail8e749c.ts.net` | **LIVE** | The community-facing origin. Serves `/workbench`, `/community`, `/roadmap`, `/questlab`, `/networksense`, `/events`, `/testing`, `/data-and-trust`, `/join`, `/health`, `/workbench/downloads/*`. **This is the only public origin.** `/questpicker` and `/steward` are **separate containers** (`am4demo-questpicker` on :9021, `comfy-steward-view` on :7080) reached by their own Funnel routes — not the Gateway, and nothing in this repo can deploy them. |
| **Adding a public route** | ⚠️ **THREE STEPS, and the third is invisible from this repo** | Funnel sends `/` to **Caddy on :8190**, which forwards a **deliberate allowlist** of paths to the Gateway on :4000; anything unmatched gets an honest 404 rather than a proxy fall-through, because `/ops/*` must never be funneled. So a new route needs (1) a Gateway image cut, (2) a deploy via `isolate`'s `tools/am4/Deploy-GatewayImage.ps1`, and (3) **its path added to the `@public` list in `/etc/caddy/Caddyfile` on the AM4 host**, then `systemctl reload caddy`. `/questlab` answered correctly inside the container for twelve minutes on 2026-08-08 while the origin still returned 404. That Caddyfile is host-only config and carries bcrypt credentials, so it is deliberately not mirrored into any repo — only the mechanism is documented. |
| `lj-workbench` (the container behind that origin) | ⚠️ **PINNED** | Running `lumberjacks-gateway:m31-workbench-20260729-r2` since 2026-08-01, started by a bare `docker run` — **no compose labels and no compose file in any repo**, so until 2026-08-08 the only definition of a live public container was the container itself. Now captured twice: the spec in the header of [`tools/workbench/Publish-WorkbenchAssets.ps1`](../../tools/workbench/Publish-WorkbenchAssets.ps1), and as executable defaults in `isolate`'s `tools/am4/Deploy-GatewayImage.ps1`. Because the image is pinned at 2026-07-29, anything added to the Gateway since then is invisible in production no matter what is published to the mount — a tome or route change needs a **cut + deploy**, not a publish. |
| Gateway deploy lane for AM4 | **LIVE, in `isolate`** | `New-GatewayReleaseCut.ps1` here builds and gates the image; `isolate`'s `tools/am4/Deploy-GatewayImage.ps1` ships it, recreates the container, proves `/health` `/workbench` `/questlab` over HTTP, and rolls back on failure. **`Promote-GatewayImage.ps1` cannot serve AM4** — it targets P7's compose root, environment file and container name, and that VM is terminated. Per PD-8, deployment tooling lives in `isolate`. |
| `comfy-p7.duckdns.org` | **STOPPED** | The GCP P7 VM is terminated (since 2026-07-25). Docs still referencing it as a live host are stale unless they are P7 operator runbooks, where P7 is correctly the subject. |
| `/join` on the public origin | ⚠️ **NOT OURS** | The funnel routes `/join` to an unrelated service, shadowing the Gateway's real enrollment flow. Do not link anyone here. See the `steam-join` catalog card. |

## The areas

| Area | Status | What it is |
|---|---|---|
| [`Lumberjacks/`](../../Lumberjacks/README.md) | **LIVE** (services + roadmap) | Gateway/eventlog/progression/operatorapi + the append-only public roadmap journal. **Caveat:** its *era-1 engine docs* (greenfield ADRs 0001–0020, getting-started, 90-day plans) are **HISTORICAL** — and `Lumberjacks/docs/README.md` is itself an era-1 entrance. |
| [`network/mod/ComfyNetworkSense/`](../../network/mod/ComfyNetworkSense/README.md) | **LIVE** | The BepInEx plugin: ZDO redirect, handshake, telemetry, quest tracking. |
| [`network/mod/ComfyQuestLab/`](../../network/mod/ComfyQuestLab/README.md) | **LOCAL-ONLY** | The creator-facing quest sandbox: all 86 practical atlas signatures are explicitly patched, all 57 creator-safe signatures route to 34 stable bindable events, and 4 query/cheat signatures stay disabled. Includes a zoomable interactive event grid, compact Gallery v2 profiles/comparisons, backward-compatible local quest files, and bounded `all-schools` / `creator-events` prepare-run-reset-report-export suites. Shares `TrackedQuest`, `QuestEvent`, `QuestViewLoader`, `QuestEventCatalog`, and `QuestTriggerEvaluator` with ComfyNetworkSense by source-link. Exact-r4 live evidence passed 8/8 schools and 8/8 example quests with zero same-action doubles; final r8 presentation/course re-witness remains. Web tome at `/questlab`; download at `/workbench/downloads/quest-lab`. |
| [`Lumberjacks/docs/workbench/`](../../Lumberjacks/docs/workbench/) + `/workbench` routes | **LIVE** | The Community Workbench: public catalog of 8 tools, ownership ladder, cold-start kits. Deployed and publicly reachable on the AM4 origin. |
| [`fieldlab/`](../../fieldlab/NETCODE-MAP.md) | **LIVE** | The netcode-replacement R&D program. **The 2026-07-28 hard hold was superseded on 07-30 and the lane reopened** — `PINNED-networking-lane-2026-07.md` is marked SUPERSEDED. Work continued through 08-05 (r42 Gateway session-plane fix cut, `b206c31`; ADR 0017 accepted). Still true: no human Steam two-client test has passed, and C10b has no green receipt. |
| [`infra/gcp/p7/`](../../infra/gcp/p7/README.md) | **STOPPED** (tooling LIVE) | The release/deploy/rollback pipeline is real and maintained; the VM it targets is terminated. Deploys go release-cut → promote; never `terraform apply` from here — a plan would destroy the VM and 4 live resources. |
| [`recipes/quest-catalogs/`](../../recipes/README.md) | **LIVE** | The quest picker + absorption engine (Python, self-contained). |
| [`tools/workbench/`](../../tools/workbench/) | **LIVE** | Toolkit for the catalog: privacy-gated zip builder, publish script, announcement drafter, feedback distiller. `Publish-WorkbenchAssets.ps1` defaults to `homebase:/srv/lumberjacks/roadmap` (the AM4 host) — the comfy-p7 default was fixed 2026-08-06. It carries `workbench.html`, `questlab.html`, `tools.json` and every catalog zip, each verified by SHA-256 remote-side. |
| [`tools/selfie-stick/`](../../tools/selfie-stick/README.md) | **LIVE** | World-save structure scanner → ranked camera shot list. The revived front half of the `camera-gallery` piece. |
| [`tools/i5/`](../../tools/i5/README.md), [`tools/wave0/`](../../tools/wave0/) | **PAUSED** | Two-client test lanes; wave0's human gates are pinned. |
| [`network/`](../../network/README.md) (docs) | **LIVE** (notes) | Multiplayer-architecture research notes + the localhost MCP dev gateway (`network/mcp/` — Baseline's own tool). |
| `docs/internal/HANDOFF-2026-07-29.md` · `DEREK-BATCH-1.md` · `DECISIONS-PENDING.md` · `plans/` | **COCKPIT** | Operator session state: cold-pickup, decision queue, working plans. Read for context; don't treat as product docs. **HANDOFF-2026-07-29 predates the 07-30 lane reopen and still says PAUSED.** |
| [`docs/audit/`](../audit/) | **COCKPIT** | Independent review memos. |
| [comfy](https://github.com/djcdevelopment/comfy) · [Lumberjacks](https://github.com/djcdevelopment/Lumberjacks) (GitHub) | **HISTORICAL** | Public archives of the pre-merge repos; the recovery source for everything pruned in July 2026. Local checkouts of both are retired. |
| [ComfyStewardView](https://github.com/djcdevelopment/ComfyStewardView) | **LIVE**, separate repo | World-file (.db) extractor + heatmap viewer. Its own (proprietary) license. |

## Two warnings that outrank the rest

`main` is force-pushed by background automation (see [`AGENTS.md`](../../AGENTS.md)), and that
automation also lands commits on its own. Long-lived branches and forks rot fast. Pull
`--ff-only` before every push.

**There is no CI.** The only automated enforcement in this repo is an opt-in git hook
(`git config core.hooksPath .githooks`) which gates the roadmap journal and the workbench
render contract — *not* the test suites. A green working tree is not a green build.
