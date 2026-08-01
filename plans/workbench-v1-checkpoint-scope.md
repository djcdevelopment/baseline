# Workbench v1 checkpoint scope

This manifest defines the operator-authorized local checkpoint for Saga WB-1.
It remains the staging boundary: runtime state and unrelated work are excluded.

## Included implementation

| Area | Paths |
|---|---|
| Companion kernel and UI | `Lumberjacks/src/Game.Companion/Program.cs`, `Lumberjacks/src/Game.Companion/CompanionConfig.cs`, `Lumberjacks/src/Game.Companion/WorkbenchKernel.cs`, `Lumberjacks/src/Game.Companion/WorkbenchV1Page.cs` |
| Local runner and launchers | `Lumberjacks/tools/companion/Start-WorkbenchHostRunner.ps1`, `Lumberjacks/tools/companion/Start-LocalCompanion.ps1`, `Lumberjacks/tools/companion/bootstrap/Start-LumberjacksCompanion.ps1`, `tools/i5/Start-I5Companion.ps1`, `tools/i5/Sync-I5Companion.ps1`, `tools/i5/Test-I5Link.ps1` |
| Compose and distribution | `Lumberjacks/tools/companion/docker-compose.yml`, `Lumberjacks/tools/companion/New-CompanionBootstrap.ps1`, `Lumberjacks/tools/companion/Test-CompanionBootstrapPackage.ps1`, `Lumberjacks/tools/companion/README.md`, `.gitignore` |
| Verification | `Lumberjacks/tools/companion/Test-WorkbenchApi.ps1`, `Lumberjacks/tools/companion/Test-WorkbenchComposeProfiles.ps1`, `Lumberjacks/tools/companion/Test-WorkbenchRunnerOwnership.ps1`, `Lumberjacks/tools/companion/Test-WorkbenchUiContract.ps1`, `tools/workbench/Test-WorkbenchProfileBoundary.ps1`, `tools/workbench/Test-WorkbenchMcpIdentity.ps1`, `tools/workbench/Test-WorkbenchSupportExport.ps1`, `tools/workbench/Test-WorkbenchZipPrivacy.ps1` |
| Dev MCP | `.mcp.json`, `network/mcp/comfy_gateway/toolsurface/workbench.py`, `network/mcp/README.md`, `network/mcp/TOOLS.md`, `network/mcp/callers/frontier.md`, `network/mcp/callers/mcp-config-snippet.json` |
| MCP launchers and identity | `network/mcp/comfy_gateway/kernel/gateway.py`, `network/mcp/etc/start-comfy-gateway.cmd`, `network/mcp/tests/test_gateway_basics.py`, `fieldlab/scripts/start-comfy-gateway.ps1` |
| Mod Dev-MCP boundary | `network/mod/ComfyNetworkSense/ComfyNetworkSense.cs`, `network/mod/ComfyNetworkSense/ComfyNetworkSense.csproj`, `network/mod/ComfyNetworkSense/Config/PluginConfig.cs`, `network/mod/ComfyNetworkSense/Core/Services/AlphaTransportSwitches.cs`, `network/mod/ComfyNetworkSense/Core/Services/TelemetryCoordinator.cs`, `network/mod/ComfyNetworkSense/Core/Services/McpGatewayEndpoint.cs`, `network/mod/ComfyNetworkSense/Tests/McpGatewayEndpoint.Tests.csproj`, `network/mod/ComfyNetworkSense/Tests/Program.cs`, `network/mod/ComfyNetworkSense/README.md` |
| Product decisions and operating docs | `DECISIONS-PENDING.md`, `fieldlab/DECISIONS-PENDING.md`, `docs/README.md`, `docs/baseline-vision-and-boundary.md`, `docs/decisions/README.md`, `docs/decisions/pd-5-local-workbench-ownership-appliance.md`, `docs/decisions/pd-6-development-mcp-lifecycle.md`, `docs/workbench-operating-model.md`, `docs/audit/2026-08-01-workbench-product-review.md` |
| Endpoint provenance audit | `docs/audit/2026-08-01-mcp-endpoint-provenance-audit.md` |
| Workbench catalog | `Lumberjacks/docs/workbench/tools/mcp-mod-channel.md`, `Lumberjacks/docs/workbench/workbench.json`, `Lumberjacks/src/Game.Gateway/Community/workbench.html` (published separately after clean-input render) |
| Plans and evidence | `plans/README.md`, `plans/companion-workbench-reconstruction-strategy.md`, `plans/workbench-v1-saga-strategy.md`, `plans/workbench-v1-implementation-receipt.md`, `plans/workbench-v1-verification-matrix.md`, this file |

## Deliberate exclusions

- `Lumberjacks/tools/companion/dist/` packages and manifests are generated
  verification outputs, not source changes to stage.
- Docker volumes, containers, local runner tokens, browser tokens, support
  exports, and job receipts remain machine-local runtime state.
- No files under retired `C:\work\comfy` or `C:\work\lumberjacks` are used as
  implementation sources or staged for this checkpoint. A bounded read-only
  provenance audit may cite a retired path, but it does not make that checkout
  an accepted Baseline source.
- No HEARTH configuration, provider, key, or operator infrastructure belongs in
  the public Baseline bootstrap.
- No P7/GCP deployment or production-authority change is part of WB-1.

## Checkpoint sequence

1. Compare this manifest with `git diff --name-only` and
   `git ls-files --others --exclude-standard`.
2. Verify the focused and full receipts in
   [`workbench-v1-implementation-receipt.md`](workbench-v1-implementation-receipt.md).
3. Append one A7 roadmap note with verification/evidence fields, then stage the
   reviewed WB-1 paths and generated roadmap outputs. Leave preview-stamped
   `Lumberjacks/src/Game.Gateway/Community/workbench.html` unstaged.
4. Run `node scripts/roadmap.mjs check --staged` and commit the implementation
   checkpoint. Then run `npm run workbench:render` from the clean catalog input,
   verify it, and commit only the production-stamped Workbench HTML. This
   generator-required pair is one conceptual WB-1 checkpoint.
5. Run the MCP endpoint provenance verifier from the clean attributed
   checkpoint. Quarantine or rerun the historical default-port Valheim MCP
   receipts before treating MCP evidence as current.
6. Re-run the rendered pre-live source/image gate from the clean attributed
   checkpoint before any physical client run.
7. Do not close M5 until the mod-side default-off/configurable MCP boundary and
   the absence of any active host `:8720` listener are reverified.

The retired host MCP task was disabled without deletion and its audited PID
14164 was stopped. The checkpoint does not adopt its source, port, provider set,
or ledger; rollback would require an explicit operator action.
