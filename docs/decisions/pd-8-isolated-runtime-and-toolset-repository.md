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

## Amendment — 2026-08-07: the boundary, as built and as measured

The rationale above says a separate repository *forces* environment variables, mount
roots, and endpoints to be explicit and contract-tested. On the day this was accepted it
had not yet done so, and the gap was not visible from either repository on its own.

Measured before any change (full receipt:
[isolate-boundary-verification-20260807.json](../../fieldlab/evidence/isolate-boundary-verification-20260807.json)):

- The extracted compose file was **byte-identical** to baseline's, including
  `name: comfy-valheim-lab` — the live lab's project. `AUTONOMOUS_ROOT` and `COMFY_ROOT`
  had no defaults, so an unset value rendered the world mounts as blank-rooted absolute
  paths and `docker compose` still exited 0. Bringing the "decoupled" stack up would have
  adopted the running server and recreated it against an empty world.
- `gateway_identity()` hardcoded `project: "baseline"`, and `source_root` is `/workspace`
  inside any container built from `network/mcp/Dockerfile`. **`/identity` — the endpoint
  this decision names as the contract boundary — could not distinguish the two
  repositories.** A gate that cannot fail is not a boundary.
- `contracts/api-contract.json` did not describe the code beside it: `/healthz` declared
  `status` but returns `ok`/`gateway`; `/identity` declared `port` but returns
  `listen_port`/`published_port`; transport declared `default_port: 8721`, which is
  baseline's *companion container host publish*, not the kernel default of 8720. Nothing
  read the file, so nothing noticed.
- `isolate`'s own suite was red 2/11 on paths this decision deliberately left in
  `baseline`, which blocked the AGENTS.md rule that tests pass before an image is published.

### What changed

`/identity` now reports `project` from `COMFY_MCP_PROJECT` (defaulting to `baseline`, so
every existing launcher keeps its current answer); the isolate compose runs as its own
`isolate-lab` project with defaults that resolve inside its own tree; the contract was
corrected and is now enforced by `tests/test_api_contract_conformance.py`, which fails in
both directions — a declared field the response omits, *and* a response field the contract
does not declare. `Test-WorkbenchMcpIdentity.ps1` gained `-ExpectedProject`.

Verified 2026-08-07 on OMEN: the isolate gateway attests `project: isolate` with real git
provenance on 8722, while the same check pointed at 8721 fails on `project` **first** —
a mismatch that could not have fired before this change. The live lab was untouched
throughout (container id and `StartedAt` unchanged).

### Still blocking this decision

**`isolate` has no git remote.** Step 3 of the promotion pathway above — publish versioned
container images, consume them in `baseline` — is therefore not reachable. Today `baseline`
can only rebuild the gateway from a sibling directory on the same disk, which is precisely
the coupling this decision set out to remove. Until there is a remote and a published tag,
the two repositories are duplicated source with a tested contract between them, not an
independent runtime. The compose file also remains duplicated with no drift guard; which
copy is authoritative is unresolved.

## Amendment — 2026-08-12: reconciliation completed

The remote blocker above is resolved: `isolate` now has
`https://github.com/djcdevelopment/isolate.git` as `origin`. The deploy-lane boundary
was established in commits `351aa58` and `b91adf1`; the final Baseline MCP delta was
selectively ported and pushed in isolate commit `bf925c3`.

The reconciliation used Baseline commit `593c27b` as the source delta. It ported the
bounded Quest Lab provider, its five tests, provider registration, and the container’s
explicit writable quest-root mapping. It deliberately rejected Baseline’s port-8721
contract hunk: isolate retains kernel/container port 8720 and publishes the canonical
Compose endpoint on loopback port 8722. It also retains isolate’s narrower, newer
distribution-independence guard. The alleged second tree at
`Lumberjacks/network/mcp` does not exist in any local Baseline ref or path history, so
there was nothing to reconcile from it.

Verified before removal from Baseline: 24 MCP unit tests passed; Compose rendered the
Quest Lab provider and `/lab/omen-config/comfy-quest-lab`; the port mapping remained
`127.0.0.1:8722 -> 8720`; and the canonical `comfy-gateway` image built. Isolate is now
the sole writable source authority for this runtime.
