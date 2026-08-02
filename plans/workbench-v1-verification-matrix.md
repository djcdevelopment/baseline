# Workbench v1 verification matrix

This matrix is the evidence-oriented companion to the Saga and implementation
receipt. `Passed` means the current checkout has direct evidence; `Pending` or
`Operator-gated` is intentionally not a completion claim.

| Requirement | Current evidence | Status |
|---|---|---|
| Fresh install starts Explore and cannot activate Dev/Lab before claim | Disposable current-image fixture with `LUMBERJACKS_WORKBENCH_PROFILE=Dev` returned `claimed=false`, `effective_profile=Explore`, and `build=profile_not_eligible` | Passed |
| Claimed installation persists through recreate | Final-image Lab receipt `job-20260801-175033646-fa1db4d7` preserved installation `wb-4285b4fd66f442e598886b861ed1bd44`, claim, and volume | Passed |
| Typed capabilities and deterministic eligibility | `Test-WorkbenchApi.ps1`; 11 registered capabilities; target/profile/input rejection | Passed |
| Durable jobs, events, receipts, artifacts | API contract plus rebuilt Docker build/support receipts | Passed |
| Runner authentication and ownership | API contract, authenticated heartbeat, leased-runner binding, and current fixture `job-20260802-015005516-d0741770`: stale runner HTTP 404, owning lease renewal, exact child exit-code propagation (`0` and `7`), and no external operation | Passed |
| Browser mutation boundary | API contract rejects missing token and cross-site Origin/Sec-Fetch-Site | Passed |
| Standard/Advanced presentation does not grant authority | Registry eligibility is server-side; UI toggle only changes presentation labels/details, with generic Story topology labels and physical names only in Advanced | Passed by design/API shape; unfamiliar-user visual usability remains manual |
| Unified shell and compatibility routes | `Test-WorkbenchUiContract.ps1` proves `/`, `/workbench`, and `/companion` return UTF-8 HTML with no mojibake; six intent sections, responsive viewport, privacy, evidence, observation, Gateway topology, and the first-visit safe path are present. The no-coaching newcomer protocol is ready | Passed structurally; mobile/novice visual observation pending |
| Explore slice | Synchronous inspect/evidence jobs and topology projection | Passed |
| Build slice | Rebuilt Lab `build.mod.release` receipt; read-only Valheim mount, no host SDK, no plugin copy | Passed |
| Operate slice | Existing v0 check/install/rollback/capture adapters are wired. Current clean Lab job `job-20260802-015026195-e3676b38` passed with `mod_manifest_read` against local candidate `m32-workbench-20260802-r1`. A fresh byte preflight matched all 30 live OMEN payload entries with zero different, missing, or unsafe entries. Install/rollback now has full-package preflight, a single-operation gate, atomic per-file replacement, automatic restore on failure, created-file cleanup, and prior-release restoration; 11 isolated Companion tests pass. Topology truthfully showed Local Gateway ready and P7 excluded | Read-only check, no-difference preflight, and automated reversible-update contract passed; live install/rollback and player-active transport capture remain operator-gated because they affect or depend on player-facing state |
| Recover slice | Support export passed privacy scanner; recreate verifier exists | Passed for export; recreate rerun after final image tag is recommended |
| No Docker socket / profile boundary | Compose profile verifier; default/Production contain only Companion while Dev/Lab services are explicitly profile-gated | Passed |
| Normal-gameplay Dev MCP absence on this workstation | ComfyNetworkSense defaults MCP off, accepts only an explicit loopback origin, performs no disabled-state health polling, and refuses UI activation without Dev/Lab config. After the clean rebuild, `ComfyGatewayBoot` remained disabled without deletion, host `8720` remained free, and HEARTH remained on `8710` | Passed |
| Bootstrap distribution | Clean-checkpoint package: 22 required files, runner/privacy/boundary/identity gates present, operator-private i5 README excluded, and whole ZIP privacy scan clean | Passed |
| Dev MCP shared surface | With `-McpPort 8721`, live Streamable HTTP exposed 45 tools including Workbench; MCP job `job-20260801-174027902-c22a7b5f` returned the same events/receipt shape as Web; the clean authenticated identity gate passed | Passed |
| Dev MCP endpoint provenance | Current clean HEAD `0526c69e7522590b21b8760cc3eb91b126749e3a` returned `baseline.mcp.identity.v1` with `source_dirty=false` and matched project, Lab profile, image tag, published port `8721`, Workbench provider, caller registry, and Baseline ledger; immutable Dev MCP image ID is `sha256:22b3c8f842d1d4ff1fabc12b38e65a5552471a876ec02025539fb8607f09aa91` | Passed |
| Active gateway launcher safety | Active launchers derive their roots/interpreters and default to explicit `:8721`; stale `ComfyGatewayBoot` was disabled without deletion and its exact retired-checkout process stopped | Passed; HEARTH unchanged on `8710` |
| Historical default-port MCP evidence | Six old Comfy-ledger calls remain quarantined; Baseline ledger now contains successful identity-gated `valheim_mcp_health`, filtered `valheim_server_log_tail`, and `valheim_handshake_trace` events on `8721` | Minimum evidence rerun passed; old receipts retained only as history |
| Clean source/image attribution | Current Workbench runtime pins clean HEAD `0526c69e7522590b21b8760cc3eb91b126749e3a`, Companion `sha256:08bc0f389f85ba825452c6d3a2b50452cbc76bb814599cc87e977a3a89acbcec`, and Dev MCP `sha256:22b3c8f842d1d4ff1fabc12b38e65a5552471a876ec02025539fb8607f09aa91`. The sealed rendered receipt retains its own earlier source/image identity | Passed |
| Rendered AM4 + OMEN + i5 C6 role reversal | Job `job-20260802-003125748-116adca1`, run `workbench-20260802-003128-116adca1`: real clients completed the bounded C6 composition; Derek watched live and recorded `pass / followed / smooth`; cleanup/disarm completed | Passed; sealed reason `human_observation_recorded` |
| Full Lumberjacks solution | Restore/test succeeded with 0 errors; 604 tests passed (126 Contracts / 250 Simulation / 217 Gateway / 11 Companion), with the pre-existing EF dependency-conflict warning | Passed |

## Current safety posture

The active local stack is explicitly in Lab and publishes the identity-attested
Baseline Dev MCP only on loopback `8721`. Host `8720` is free; HEARTH remains
independent on `8710`. The clean machine-acceptance checkpoint is committed and
the C6 machine-plus-human receipt is sealed. The current clean runtime passes the
local read-only Operate check and 30-file exact-match preflight; reversible-update
behavior is covered by isolated tests. Player-impacting install/rollback,
player-active capture, and unfamiliar-user/mobile review remain classified
follow-ons, not hidden passes.
