# Comfy MCP Tools

Source of truth: `contracts/commands.json`.

Endpoint rule: do not infer project ownership from `127.0.0.1:8720` or a green
`/healthz`. The legacy Comfy task currently occupies that port from the retired
checkout. Use the explicit Workbench Dev/Lab port and verify the authenticated
`/identity` route (or `Test-WorkbenchMcpIdentity.ps1`) plus
`comfy_gateway_status` (source root, revision/hash, image, profile, port,
providers, caller registry, and ledger) before accepting a result. See the
[provenance audit](../../docs/audit/2026-08-01-mcp-endpoint-provenance-audit.md).

Primary tools for agents:

- `valheim_mcp_health`: verify gateway paths and local services.
- `valheim_networksense_files`: list telemetry files.
- `valheim_networksense_report`: compact deterministic report from recent samples.
- `valheim_authoritative_status`: inspect the rendered mod's direct Gateway poll/apply/ack state.
- `valheim_explain_networksense`: report plus local Ollama explanation.
- `valheim_list_sessions`: find session IDs.
- `valheim_session_bundle`: collect one session for handoff or comparison.
- `valheim_compare_clients`: compare host/client bundles for multiplayer tests.
- `valheim_suggest_next_test`: recommend the next practical in-game test.
- `valheim_suggest_config`: recommend config changes without applying them.
- `valheim_apply_config_profile`: apply whitelisted config profiles only.
- `workbench_capabilities`: read the effective local Workbench registry.
- `workbench_start_job`: start one registered Workbench job through the shared API.
- `workbench_job`: inspect a Workbench job and its durable events.
- `workbench_cancel_job`: cancel a queued/leased Workbench job.
- `workbench_receipt`: read a completed Workbench receipt.
- `valheim_record_note`: append a dev note.

Rules:

- Prefer deterministic report tools before calling Ollama.
- Treat suggestions as suggestions. Do not apply config or code changes without an explicit user request.
- After `valheim_apply_config_profile`, tell the user to run `network_sense_reload_config` in-game.
- Keep this gateway localhost-only.
- The Workbench provider is Dev/Lab-only and calls the same loopback API as the browser;
  it is never a gameplay or arbitrary-command bridge.
- Do not ask collaborators to run MCP unless they are explicitly debugging.
