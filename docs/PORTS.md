# Port Registry

One loopback port, one owner. Claim here before binding anything new;
collisions found in code reviews trace back to this table.

| Port | Owner | Status | Authority |
|------|-------|--------|-----------|
| 8710 | HEARTH MCP gateway (lab, never ships in Baseline deliverables) | live | `docs/baseline-vision-and-boundary.md` |
| 8720 | ComfyGatewayBoot (legacy) | retired, not deleted | PD-6 |
| 8721 | Baseline Dev/Lab MCP (`comfy-gateway`) | live, reserved | PD-6 |
| 8722 | Provenance surface | reserved | PD-6 |
| 8730 | Sovereign-Shards Shard Manager Daemon | **reserved, unbuilt** | `sovereign-logical-architecture-guide.md` |
| 8080 | Lumberjacks Companion (loopback Workbench) | live | `Lumberjacks/tools/companion/README.md` |
| 47631 | Quest Lab Sheets export companion | live (on demand) | `tools/questlab-sheets/README.md` |

Rules:
- A loopback port is not a project identity — anything serving one must
  self-attest (PD-6): source root, revision, and profile via `/identity`.
- An earlier draft of the sovereign guide claimed `:8721` for the Shard
  Manager; that collided with the live Dev MCP and was corrected to `:8730`
  on 2026-08-11.
