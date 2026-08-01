# Comfy MCP Gateway

Local MCP gateway for Comfy Valheim mod development.

This gateway is project-owned: it runs from this repository and its Docker image
with no dependency on anything outside the checkout. It is intentionally separate
from any general-purpose MCP gateway already running on the operator's machine,
keeping its own auth header, port, ledger, caller registry, and Valheim-specific
tools.

## Endpoint

```text
http://127.0.0.1:8720/mcp
```

Dev HTTP helpers for the in-game panel:

```text
GET  http://127.0.0.1:8720/healthz
GET  http://127.0.0.1:8720/valheim/report
GET  http://127.0.0.1:8720/valheim/next-test
GET  http://127.0.0.1:8720/valheim/config-suggestion
POST http://127.0.0.1:8720/valheim/apply-profile
```

Auth header:

```text
X-Comfy-Key: comfy-dev-local
```

The future Valheim mod client should use:

```text
X-Comfy-Key: valheim-mod-local
```

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
python -m comfy_gateway.kernel.gateway
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

## Design Rules

- Localhost only.
- Dev-only; not production mod functionality.
- JSONL remains source of truth.
- Keep MCP calls command-triggered or event-triggered, never per-frame.
- Treat model output as text or suggestions; do not execute arbitrary returned actions.
- The lab motion tools are the only gameplay-adjacent mutation seam: they accept
  only named patterns, bounded durations, and the motion-apply switch, and they
  require `COMFY_AUTONOMOUS_STATE`. They are not a console or shell bridge.
