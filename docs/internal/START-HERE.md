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
