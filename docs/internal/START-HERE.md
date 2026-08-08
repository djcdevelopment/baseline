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
| `https://am4.tail8e749c.ts.net` | **LIVE** | The community-facing origin, exposed by Tailscale Funnel. Serves `/workbench`, `/community`, `/roadmap`, `/networksense`, `/events`, `/testing`, `/join`, `/health`, `/workbench/downloads/*`. **This is the only public origin.** ⚠️ **`/questlab` is a 404 in production** — the route exists in source but the running image predates it; see the image-pin note below. `/questpicker` and `/steward` appear in every page's nav bar but **no route for either exists in this repo's Gateway source** — whatever serves them lives on the AM4 host outside this repo. |
| `lj-workbench` (the container behind that origin) | ⚠️ **PINNED + UNDEFINED** | Running `lumberjacks-gateway:m31-workbench-20260729-r2` since 2026-08-01, started by a bare `docker run` — **there are no compose labels and no compose file in any repo**, so the only definition of a live public container is the container itself. Full spec captured in the header of [`tools/workbench/Publish-WorkbenchAssets.ps1`](../../tools/workbench/Publish-WorkbenchAssets.ps1). Because the image is pinned at 2026-07-29, anything added to the Gateway since then is invisible in production no matter what is published to the mount. |
| `comfy-p7.duckdns.org` | **STOPPED** | The GCP P7 VM is terminated (since 2026-07-25). Docs still referencing it as a live host are stale unless they are P7 operator runbooks, where P7 is correctly the subject. |
| `/join` on the public origin | ⚠️ **NOT OURS** | The funnel routes `/join` to an unrelated service, shadowing the Gateway's real enrollment flow. Do not link anyone here. See the `steam-join` catalog card. |

## The areas

| Area | Status | What it is |
|---|---|---|
| [`Lumberjacks/`](../../Lumberjacks/README.md) | **LIVE** (services + roadmap) | Gateway/eventlog/progression/operatorapi + the append-only public roadmap journal. **Caveat:** its *era-1 engine docs* (greenfield ADRs 0001–0020, getting-started, 90-day plans) are **HISTORICAL** — and `Lumberjacks/docs/README.md` is itself an era-1 entrance. |
| [`network/mod/ComfyNetworkSense/`](../../network/mod/ComfyNetworkSense/README.md) | **LIVE** | The BepInEx plugin: ZDO redirect, handshake, telemetry, quest tracking. |
| [`network/mod/ComfyQuestLab/`](../../network/mod/ComfyQuestLab/README.md) | **LOCAL-ONLY** | The creator-facing quest sandbox: 28 seams across 8 schools, a live console with a per-row "can a quest be bound to this?" verdict, a practice gallery, and a local quest lane (`lab_setup` / `lab_reload`). Shares the quest contract with ComfyNetworkSense by source-linking `TrackedQuest`/`QuestViewLoader`/`QuestTriggerEvaluator`, so a quest behaves identically in both. **Only a creature kill can fire a quest today** — that is the state of the shared evaluator, and making it visible is the tool's purpose. Web tome at `/questlab`; download at `/workbench/downloads/quest-lab`. |
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
