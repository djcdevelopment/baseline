# Comfy MCP Gateway

Local MCP gateway for Comfy Valheim mod development.

This gateway is intended to be project-owned: it runs from this repository and
its Docker image with no dependency on anything outside the checkout. A
loopback URL alone does not prove that ownership, however. On 2026-08-01 an
enabled legacy `ComfyGatewayBoot` task was found serving the same default port
from retired `C:\work\comfy`; see the [endpoint provenance audit](../../docs/audit/2026-08-01-mcp-endpoint-provenance-audit.md).
Do not treat a healthy `:8720` listener as Baseline evidence until its identity
contract passes. Dev/Lab launchers should use the explicit project port selected
by the Workbench migration (current working candidate `8721`).

## Endpoint

```text
http://127.0.0.1:8721/mcp  # Workbench Dev/Lab candidate; verify identity first
```

The legacy compatibility endpoint remains `http://127.0.0.1:8720/mcp` for
historical tooling and is not an accepted Baseline evidence source while its
scheduled-task owner is unresolved.

Dev HTTP helpers for the in-game panel:

```text
GET  http://127.0.0.1:${COMFY_MCP_PORT}/healthz
GET  http://127.0.0.1:${COMFY_MCP_PORT}/identity  # authenticated provenance attestation
GET  http://127.0.0.1:${COMFY_MCP_PORT}/valheim/report
GET  http://127.0.0.1:${COMFY_MCP_PORT}/valheim/next-test
GET  http://127.0.0.1:${COMFY_MCP_PORT}/valheim/config-suggestion
POST http://127.0.0.1:${COMFY_MCP_PORT}/valheim/apply-profile
```

Auth header:

```text
X-Comfy-Key: comfy-dev-local
```

The future Valheim mod client should use:

```text
X-Comfy-Key: valheim-mod-local
```

The current ComfyNetworkSense Raven/MCP helper still contains hard-coded
legacy `:8720` HTTP literals. Treat that path as a migration blocker for normal
gameplay; it must be configured or explicitly Dev/Lab-gated before the
production absence invariant is claimed.

## Setup

Create a project-local virtual environment and install the declared
dependencies. Run these from the repository root; `.venv/` is git-ignored.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r network\mcp\requirements.txt
```

Bash/WSL equivalent:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r network/mcp/requirements.txt
```

[`requirements.txt`](requirements.txt) is the single dependency declaration —
the Docker image installs from the same file, so a local venv and a built image
resolve the same versions. Python 3.12 is what the image uses.

## Run

With the venv activated, from the repository root:

```powershell
.\network\mcp\etc\start-comfy-gateway.cmd
```

That source launcher binds the explicit project `:8721` default (override with
`COMFY_MCP_PORT` only for a deliberate fixture). For a Baseline Dev/Lab
session, start the Workbench profile with the same explicit project port and
verify identity before connecting an agent:

```powershell
.\Lumberjacks\tools\companion\Start-LocalCompanion.ps1 -Profile Dev -McpPort 8721
```

`start-comfy-gateway.cmd` resolves its interpreter in this order:

1. `%COMFY_GATEWAY_PYTHON%`, if that environment variable is set -- point it at
   any `python.exe` whose environment has the requirements installed.
2. Otherwise plain `python` on `PATH`, which is the activated venv above.

There is deliberately no third, machine-specific fallback. Either interpreter
still needs the requirements installed; the environment variable only changes
which interpreter runs, not the dependency requirement.

To run the module directly instead of through the launcher:

```powershell
$env:PYTHONPATH = "$PWD\network\mcp"
python -m comfy_gateway.kernel.gateway --host 127.0.0.1 --port 8721
```

Or run it containerized, which needs no local Python at all:

```powershell
docker build -t comfy-mcp-gateway network\mcp
```

## Tests

With the venv activated, from the repository root:

```powershell
$env:PYTHONPATH = "$PWD\network\mcp"
python -m unittest discover -s network\mcp\tests
```

## Tools

- `comfy_gateway_status`: gateway identity, providers, ledger, caller.
- `local_generate`: direct local Ollama generation.
- `valheim_networksense_files`: list NetworkSense telemetry files.
- `valheim_tail_networksense`: tail a NetworkSense JSONL file.
- `valheim_tail_bepinex_log`: tail/filter BepInEx log output.
- `valheim_networksense_report`: compact recent telemetry report.
- `valheim_explain_networksense`: report plus local Ollama explanation.
- `valheim_mcp_health`: path/service health for the dev gateway.
- `valheim_swarm_clients`: list disposable lab client paths and noVNC URLs.
- `valheim_lab_motion_test`: send one bounded named motion/apply command through
  a disposable client's atomic mailbox.
- `valheim_lab_motion_status`: read that client's pending command and receipts.
- `valheim_list_sessions`: summarize known NetworkSense sessions.
- `valheim_session_bundle`: gather one session's client/server/events/benchmarks.
- `valheim_compare_clients`: compare host/client bundles for multiplayer tests.
- `valheim_suggest_next_test`: deterministic next-test suggestions.
- `valheim_suggest_config`: deterministic config suggestions; does not apply.
- `valheim_apply_config_profile`: apply a whitelisted dev config profile.
- `valheim_record_note`: append a dev note for this test session.
- `workbench_capabilities`: inspect the local Workbench registry and effective profile.
- `workbench_start_job`: start one registered Workbench job through the shared API.
- `workbench_job`: inspect a Workbench job and its durable event stream.
- `workbench_cancel_job`: cancel a queued/leased Workbench job.
- `workbench_receipt`: read a completed Workbench receipt.

## Design Rules

- Localhost only.
- Dev-only; not production mod functionality.
- Treat `comfy_gateway_status` as a required identity check: expected source
  root, revision/hash, image, profile, port, providers, caller registry, and
  ledger directory must match the active Baseline checkout.
- The authenticated `/identity` route is the machine-readable transport for
  that check; `/healthz` and a reachable port are not sufficient.
- The Workbench tools are mounted only by the Docker `dev`/`lab` profiles and use the
  same loopback-authenticated API as the browser. They do not expose a shell, Docker
  socket, HEARTH configuration, or arbitrary gameplay control.
- JSONL remains source of truth.
- Keep MCP calls command-triggered or event-triggered, never per-frame.
- Treat model output as text or suggestions; do not execute arbitrary returned actions.
- The lab motion tools are the only gameplay-adjacent mutation seam: they accept
  only named patterns, bounded durations, and the motion-apply switch, and they
  require `COMFY_AUTONOMOUS_STATE`. They are not a console or shell bridge.
