# PD-8 — Isolated runtime and toolset repository architecture

- Status: Accepted
- Owner: Derek
- Trigger: Maturity of local Lab containerization and gateway contract boundaries
- Date: 2026-08-07

## Decision to make

Extract the container runtime environment (MCP gateway, lab compose definitions, and associated developer toolset) into a dedicated repository (`isolate`), establishing formal contract boundaries between containerized infrastructure and the `baseline` game repository.

## Evidence & Rationale

1. **Contract Boundary Exposure**: In `baseline`, local container builds rely on implicit host directory paths (`C:\work\baseline\network\mcp`). Extracting these components into `isolate` forces environment variables, volume mount roots, HTTP/REST endpoints (`/identity`, `/healthz`, `/mcp`), and caller registries to be explicitly specified and contract-tested.
2. **Decoupled Development Lifecycle**: Testing the Python MCP gateway (`network/mcp`) and container build logic should not require building C# / BepInEx assemblies or checking out the full game asset tree.
3. **Clean Promotion Pathway**: Features and tools are developed, refined, and contract-tested in `isolate`, then merged or referenced in `baseline` via published container image tags (e.g. `ghcr.io/community-valheim-tools/comfy-gateway:v1.x`) and standard JSON schema contracts.

## Viable Alternatives

1. **Decoupled `isolate` Repository (Accepted)**: Standalone repository containing `network/mcp`, `docker/`, and `tools/`. `baseline` consumes versioned container releases and contract definitions.
2. **In-Tree Monorepo (`baseline` only)**: Retain container files in `baseline`. Replaced because path assumptions and live bind-mount cache issues on Docker Desktop obscure contract boundaries.

## Required Contract Boundaries

- **Transport / Auth**: REST endpoints require explicit `X-Comfy-Key` header authentication (`comfy-dev-local` or `valheim-mod-local`).
- **Endpoints**:
  - `GET /healthz` - Liveness check
  - `GET /identity` - Authenticated runtime provenance attestation
  - `POST /mcp` - FastMCP JSON-RPC tool invocation endpoint
- **Container Images**: Decoupled from host builds via published tags (`comfy-gateway`, `valheim-lab`).

## Feature Matrix & Workflow Partitioning

| Workflow / Feature Set | What Moves to `isolate` (Tooling & Containers) | What Remains in `baseline` (Game & Mod Sources) |
|---|---|---|
| **.NET SDK / Build Engine** | SDK build container images (`lj-workbench`, `mcr.microsoft.com/dotnet/sdk:9.0`), build scripts | C# mod source code (`Lumberjacks/src/`), solution files, BepInEx plugin sources |
| **Steam Auth & Mod Download** | Headless Steam client containers (`josh5/steam-headless`), compose stack configs | Gateway OpenID callback logic, database schemas, modpack ZIP archives |
| **GCP Live Telemetry Ingestion** | Python MCP Gateway server (`network/mcp`), telemetry aggregators, REST/MCP endpoints | `ComfyNetworkSense` BepInEx mod, GCP tunnel launcher scripts (`start-gateway-tunnel.ps1`) |
| **Multi-PC Local Lab (OMEN, i5, AM4)** | Disposable client compose manifests (`valheim-lab.compose.yml`), remote deploy tools (`tools/i5`, `tools/am4`) | Host PC environment configs (`OMEN_VALHEIM_DIR`), Tailscale IPs, local game client installations |

