# Start here — fleet status and era map

This page prevents work from landing in the wrong repository or being mistaken for a
current operational claim. Updated 2026-08-12 after the sovereign repository split.

Status words follow [PD-4](../decisions/pd-4-evidence-standard.md): **LIVE** means a
maintained surface with current evidence, **BUILT — NOT DEPLOYED** means implementation
exists without live proof, **STOPPED** means a real lane is intentionally not running,
**BLOCKED** names a missing external prerequisite, and **HISTORICAL** is retained
evidence from an earlier state.

## Repository authority

| Repository | Status | Authority |
|---|---|---|
| [`baseline`](https://github.com/djcdevelopment/baseline) | **LIVE — hub** | Decisions, evidence archive, corpus mirrors/projections, public index, and fleet map. No active product implementation. |
| [`networksense`](https://github.com/djcdevelopment/networksense) | **LIVE — add-on source** | NetworkSense mod, telemetry/HUD behavior, tests, and mod releases. |
| [`lumberjacks-platform`](https://github.com/djcdevelopment/lumberjacks-platform) | **LIVE — platform source** | Gateway/services/Companion, roadmap/Workbench, live FieldLab harness, production compose/env templates, and P7 tooling. |
| [`comfy-quest`](https://github.com/djcdevelopment/comfy-quest) | **LIVE — add-on source** | Quest Lab/Runtime/Contracts/Studio, creator tools, pages, and zips. |
| [`sovereign-shards`](https://github.com/djcdevelopment/sovereign-shards) | **BUILT — SCAFFOLD ONLY** | Corrected founding architecture and boundary/port guards. Router/shard/sidecar/bot implementation remains planned. |
| [`isolate`](https://github.com/djcdevelopment/isolate) | **LIVE — runtime source** | MCP kernel, container/API contracts, canonical isolate-lab compose, and local runtime tools. |

Use the [repository map](../../REPO-MAP.md) for exact paths and artifact contracts.
The sealed extraction base is `split-base-20260811` at
`aceb2eb48d770885a2c4171b926867f4ee82b4a4`. Baseline history before and after that
point is an archive, not a source-reach-in mechanism.

## Operational surfaces

| Surface | Status | Current meaning |
|---|---|---|
| `https://am4.tail8e749c.ts.net/workbench` | **LIVE** | Public Community Workbench. Catalog/runtime ownership is `lumberjacks-platform`; Baseline mirrors only public catalog data for reconstruction. |
| `https://am4.tail8e749c.ts.net/roadmap` | **LIVE** | Generated platform roadmap. The append-only journal and ceremony are owned by `lumberjacks-platform`. |
| Isolate MCP compose endpoint `127.0.0.1:8722` | **LIVE, LOOPBACK** | Host publish of the isolate kernel on container port 8720. Verify authenticated `/identity`; liveness alone is not provenance. |
| P7 (`comfy-p7.duckdns.org`) | **STOPPED** | The GCP VM has been terminated since 2026-07-25. Its release/deploy/rollback tooling remains maintained by `lumberjacks-platform`. |
| AM4 Valheim capture host (`homebase`, native Linux client on the RTX 5070) | **LIVE on 1.0** | Era photography and 4K capture on Valheim 1.0 (build 25185596, `l-1.0.7`) since 2026-09-12 (`era11-detail-v5-smoke-1.0` smoke-passed). Its BepInEx plugin set is exactly the capture mod **ComfyCameraProof 0.2.4** (99,328 B, SHA-256 `fd7129befb40dba9007aa2ba860a17b68e96407771e30f03d4e5eae9e4ad28f5`, source `_retired/comfy` `handoffs/valheim-camera-proof`, commit `5ec6c45`; 0.2.2 added the MagicaCloth skip, 0.2.3 the feed mode the refine loop drives, 0.2.4 the `pose`/`runclips` console commands) plus the third-party **ComfyMods BetterServerPortals 1.9.0** (17,408 B, SHA-256 `d2e7c468620fbf94d77204dc09c5d3ac2b37a47569b5d11664c47cf818814a8e`, built 2026-09-11 from upstream `github.com/redseiko/ComfyMods` `a2b4680` against publicized 1.0 client assemblies; not on Thunderstore), both at `/home/derek/valheim/BepInEx/plugins/` and hash-pinned in `~/valheim-capture/launch-1.0-plugins.json`. The pre-1.0 BSP 1.7.0 (`1bc8b1…`, receipt `br-20260909-033145-30562f3d`) breaks `ZDOMan.Load` on 1.0 and is parked. History: [09-11](../retrospectives/2026-09-11-valheim-1.0-intro-cinematic-and-linux-prefs-path.md), [09-12 crash](../retrospectives/2026-09-12-valheim-1.0-magicacloth-spawn-crash-on-linux.md), [09-12 refine loop](../retrospectives/2026-09-12-valheim-refine-loop-slice.md). The in-session refine loop (`refine_worker.py` in ComfyStewardView, `frame_judge.py` here) ran 84 builds / 601 shots in one session on 09-12; the public `/world/` scene opens at a photo's camera and accepts shot requests; the community kit is `tools/camera-kit/`. The staging copy of BetterPortals sits at `tools/BetterPortals/` in this checkout and is gitignored; it is not Baseline code. |
| I2 Quest Studio → Runtime game proof | **OPERATOR MANUAL** | Requires the rendered OMEN client and an intentional game session; automation prepares and verifies the artifact but does not impersonate the human proof. |
| i5 peer lane | **INTERMITTENT** | The roaming laptop may be offline. One BatchMode preflight is sufficient; never retry-loop or fall back to password auth. |

## Evidence versus implementation

Baseline keeps historical `fieldlab/evidence`, retrospectives, tracked run receipts,
and experiment records so old claims remain inspectable. The scripts, scenarios,
routes, ADR working set, and new live receipts belong to `lumberjacks-platform`.
Evidence retained here does not authorize rerunning a removed implementation path.

The public corpus follows the same rule: Workbench and roadmap snapshots are pinned to
one immutable upstream commit and checked against committed provenance. They are
rebuild inputs, not writable copies of the platform authorities.

## Before changing anything

1. Find the owner in [REPO-MAP.md](../../REPO-MAP.md).
2. Work in that repository; never add a sibling path to make a local build pass.
3. Use exact packages or hash-verified release artifacts at a boundary.
4. Record technical claims using PD-4 labels and reproducible commands.
5. For Baseline-only documentation/corpus work, follow [BUILDING.md](BUILDING.md).
