# Start here — what's live, what's paused, what's history

One page, one purpose: stop you from acting on the wrong era. Every area below is tagged
**LIVE** (running or actively maintained), **BUILT — not deployed**, **PAUSED** (hard hold
with a written resume path), **COCKPIT** (operator session state, not durable docs), or
**HISTORICAL** (kept honestly, describes a past era). Updated 2026-07-29.

## The areas

| Area | Status | What it is |
|---|---|---|
| [`infra/gcp/p7/`](infra/gcp/p7/README.md) | **LIVE** | The deployed GCP VM: Valheim server + five Lumberjacks services, image-digest-pinned, admitted release `m30-rolecontrol-20260723-r1`. Deploys go release-cut → promote; never `terraform apply` from here. |
| [`network/mod/ComfyNetworkSense/`](network/mod/ComfyNetworkSense/README.md) | **LIVE** | The BepInEx plugin running on that server and its clients: ZDO redirect, handshake, telemetry, quest tracking. |
| [`Lumberjacks/`](Lumberjacks/README.md) | **LIVE** (services + roadmap) | Gateway/eventlog/progression/operatorapi + the append-only public roadmap journal. **Caveat:** its *era-1 engine docs* (greenfield ADRs 0001–0020, getting-started, 90-day plans) are **HISTORICAL** — bannered as such. |
| [`Lumberjacks/docs/workbench/`](Lumberjacks/docs/workbench/) + `/workbench` routes | **BUILT — not deployed** | The Community Workbench: public catalog of 7 runnable tools, ownership ladder, cold-start kits. Ships in one gated deploy batch (see `DEREK-BATCH-1.md`). |
| [`fieldlab/`](fieldlab/NETCODE-MAP.md) | **PAUSED** | The netcode-replacement R&D program. Hard hold at a green machine-state: [`fieldlab/PINNED-networking-lane-2026-07.md`](fieldlab/PINNED-networking-lane-2026-07.md) — no human Steam test is scheduled; that doc is the only resume path. The ADR track and `NETCODE-MAP.md` remain the program's canon. |
| [`recipes/quest-catalogs/`](recipes/README.md) | **LIVE** | The quest picker + absorption engine (Python, self-contained). Byte-identical copy in the public comfy archive. |
| [`tools/workbench/`](tools/workbench/) | **LIVE** | Toolkit for the catalog: privacy-gated zip builder, publish script, announcement drafter, feedback distiller. |
| [`tools/i5/`](tools/i5/README.md), [`tools/wave0/`](tools/wave0/) | **PAUSED** with the lane | Two-client test lanes; wave0's human gates are pinned. |
| [`network/`](network/README.md) (docs) | **LIVE** (notes) | Shareable multiplayer-architecture research notes + the localhost MCP dev gateway (`network/mcp/` — Baseline's own tool, *not* HEARTH). |
| `HANDOFF-2026-07-29.md` · `DEREK-BATCH-1.md` · `DECISIONS-PENDING.md` · `plans/` | **COCKPIT** | Operator session state: cold-pickup, decision queue, working plans. Read for context; don't treat as product docs. |
| `docs/audit/` | **COCKPIT** (uncommitted) | Independent review memos, deliberately held for operator sign-off. |
| [comfy](https://github.com/djcdevelopment/comfy) · [Lumberjacks](https://github.com/djcdevelopment/Lumberjacks) (GitHub) | **HISTORICAL** | Public archives of the pre-merge repos; the recovery source for everything pruned in July 2026. Local checkouts of both are retired. |
| [ComfyStewardView](https://github.com/djcdevelopment/ComfyStewardView) | **LIVE**, separate repo | World-file (.db) extractor + heatmap viewer. Its own (proprietary) license — see the Workbench catalog entry. |

## Reading order for a newcomer

1. [`README.md`](README.md) — what this repo is and how it came to be (merge + prune).
2. This page — which era each area belongs to.
3. [`docs/baseline-vision-and-boundary.md`](docs/baseline-vision-and-boundary.md) — what
   Baseline is *for*, and the hard product boundary (HEARTH/Mechnet never ships in it).
4. [`GLOSSARY.md`](GLOSSARY.md) — the project's terms, including the three different
   things called "workbench".
5. [`BUILDING.md`](BUILDING.md) — the two build environments and the commit ceremony that
   will otherwise fail you.
6. [`CONTRIBUTING.md`](CONTRIBUTING.md) — current contribution posture (read it before
   opening a PR; it is honest about what is not accepted yet).
7. Then the area you came for, via the table above.

## One warning that outranks the rest

`main` is force-pushed by background automation (see `AGENTS.md`). Long-lived branches and
forks rot fast. If that surprises you, read `AGENTS.md` before touching anything.
