# Session Work Ledger — Isolate Container Extraction, CreatorOS Status, and AM4 Runtime Audit

Recorded 2026-09-15 UTC (2026-09-14 PDT). This ledger captures architectural decisions, cross-repository findings, and runtime investigations completed in this session across `baseline`, `isolate`, `comfy-quest`, and the AM4 fleet node.

---

## 1. Decoupled Container Runtime & Toolset (`isolate`)

### Rationale & Decision
Following user direction, the container runtime environment, MCP gateway, and developer toolset were extracted from `baseline` into a sovereign repository (`isolate` at `C:\work\isolate`):
* **Durable Decision**: Formally documented in [PD-8 — Isolated runtime and toolset repository architecture](../decisions/pd-8-isolated-runtime-and-toolset-repository.md) and indexed in [docs/decisions/README.md](../decisions/README.md).
* **Formal Contract Schema**: Published [network/mcp/contracts/api-contract.json](../../network/mcp/contracts/api-contract.json) establishing JSON Schema definitions for `/healthz`, `/identity`, and `/mcp` endpoints, along with `X-Comfy-Key` authentication headers.
* **Compose Image Decoupling**: Updated [fieldlab/autonomous/valheim-lab.compose.yml](../../fieldlab/autonomous/valheim-lab.compose.yml) to support versioned container image tags (`COMFY_GATEWAY_IMAGE`) alongside local build fallbacks.

### Standalone Repository Initialized (`C:\work\isolate`)
* **Extracted Contents**: `network/mcp` (FastAPI/MCP gateway kernel), `docker/valheim-lab.compose.yml` (Lab server, gateway, and disposable headless Steam client Compose stack), and developer toolset (`tools/i5`, `tools/am4`, `tools/workbench`, `provenance_record.py`).
* **Tooling & CI**: Added `README.md`, `AGENTS.md`, and `.github/workflows/ci.yml` for automated CI container build and test runs. Initialized Git repository and recorded root commit `ec74746`.

### Feature Matrix & Workflow Preservation
The feature matrix was verified to ensure zero workflow regression across four core capabilities:
1. **Containerized .NET Build Engine**: SDK build container images (`mcr.microsoft.com/dotnet/sdk:9.0`, `lj-workbench`) maintained in `isolate`; C# source code (`Lumberjacks/src/`) remains in `baseline` mounted at build time.
2. **Steam Auth & Mod Download**: Headless client Compose manifests (`josh5/steam-headless`) in `isolate`; OpenID callback endpoints and database models in `baseline`.
3. **GCP Live Telemetry Ingestion**: Python MCP Gateway server and telemetry aggregators in `isolate`; `ComfyNetworkSense` BepInEx mod and tunnel scripts in `baseline`.
4. **Multi-PC / 3-Account Lab Loop (OMEN, i5, AM4)**: Compose manifests and remote client deploy scripts in `isolate`; host hardware configs and Tailscale mesh mappings remain on the respective machines.

---

## 2. CreatorOS / QuestOS Evolution & Current Status

### Sovereign Cutover
Per [PD-9](../decisions/pd-9-repository-split.md) and [PD-11](../decisions/pd-11-spatial-authoring-round-trip.md), active product implementation for quest authoring and the creator loop was transitioned to sovereign repositories:
* **[`comfy-quest`](file:///C:/work/comfy-quest)**: Owns Quest Lab, Quest Runtime, Quest Contracts, Quest Studio, and **CreatorOS / Creator DM** (surfaced as **DMos**).
* **[`ComfyStewardView`](file:///C:/work/ComfyStewardView)**: Owns world snapshot analytics, multi-era spatial map authoring, and the Creator casting interface.

### Verified Creator DM Slice (Sept 8–9, 2026)
In `comfy-quest`, development closed out **CreatorOS Beta 1** (`creatoros/beta1/`) and reached **Creator DM 0.9.11 / 0.9.13-local**:
* **Slayers' Field Lodge Practice Campaign**: Immutable, data-only source for the first public-beta composition, built via `Build-CreatorOsBeta1.ps1`.
* **Zero-Restart Live Revision**: An automated integration slice ran on AM4 (`/home/derek/valheim-capture/creator-dm/runs/20260908-derek-r1`), proving that an encounter can be played, a 3rd hunt authored in Studio, replayed via DMos, revised (Draugr $\rightarrow$ Greyling), and re-engaged in Valheim **under the same game PID (1547565)** without restarting the client.
* **Prepared Handoff**: Documented in `C:\work\comfy-quest\docs\derek-walkthrough.md` and `derek-checklist.md` for a ~5-minute human seat-time review.
* **The Immediate Blocker**: After automated acceptance testing, AM4 was restored to a clean, idle state. Operator staging (deploying `release-0.9.13-local`, applying the `integration-melee` profile, and starting the campaign outside the Field Lodge) is required before human seat-time can take place.

---

## 3. AM4 Runtime Activity Audit

### Observed Activity (05:53 – 06:02 UTC / ~23:00 PDT)
During the session, temporary display activity on AM4 was observed and investigated:
* **Run Attribution**: Automated two-peer network cutover test for `ComfyNetworkSense 0.5.80` (`run_id=ns-v0.5.80-20260915-twopeer-am4`).
* **Execution**: Valheim launched on AM4 via Vulkan on the RTX 5070 with profile `Questyfour`, auto-joined the dedicated test server at `100.116.82.60:2456`, and completed a 9-minute two-peer telemetry run.
* **Clean Termination**: At 06:02:31 UTC, the test finished (`reason=client_znet_ended`), flushed its Vulkan PSO cache (`/tmp/IronGate/Valheim/vulkan_pso_cache.bin`), and cleanly terminated the process. The driving SSH session from OMEN disconnected at 06:03:02 UTC.
* **Current State**: AM4 is clean and idle, ready for CreatorOS staging when authorized.
