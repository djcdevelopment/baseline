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
| Operate slice | Read-only job `job-20260802-015026195-e3676b38` passed against m32. Approved install job `job-20260802-015909355-13073d0c` and rollback job `job-20260802-015911118-89a57d29` then passed with all 30 bytes exact and the original installed JSON restored. The productized drill requires an explicit switch and the host runner rechecks Windows Valheim immediately before mutation. A hands-on second legacy rollback exposed schema-0 ambiguity; current UI/API disables it and the v0 negative control returned HTTP 400 without changing bytes/state. A hands-on capture returned `no_peer_window`, proving it is not player-active evidence; current runner fails no-peer/incomplete capture jobs closed | Read-only check and live reversible install/rollback passed. Player-active transport capture remains operator-gated and pending |
| Recover slice | Support export passed privacy scanner; recreate verifier exists | Passed for export; recreate rerun after final image tag is recommended |
| No Docker socket / profile boundary | Compose profile verifier; default/Production contain only Companion while Dev/Lab services are explicitly profile-gated | Passed |
| Normal-gameplay Dev MCP absence on this workstation | ComfyNetworkSense defaults MCP off, accepts only an explicit loopback origin, performs no disabled-state health polling, and refuses UI activation without Dev/Lab config. After the clean rebuild, `ComfyGatewayBoot` remained disabled without deletion, host `8720` remained free, and HEARTH remained on `8710` | Passed |
| Bootstrap distribution | Clean-checkpoint package: 22 required files, runner/privacy/boundary/identity gates present, operator-private i5 README excluded, and whole ZIP privacy scan clean | Passed |
| Dev MCP shared surface | With `-McpPort 8721`, live Streamable HTTP exposed 45 tools including Workbench; MCP job `job-20260801-174027902-c22a7b5f` returned the same events/receipt shape as Web; the clean authenticated identity gate passed | Passed |
| Dev MCP endpoint provenance | Current clean HEAD `1456de1142658e972f9e0462d24b3f3ba143d4ce` returned `baseline.mcp.identity.v1` with `source_dirty=false` and matched project, Lab profile, image tag, published port `8721`, Workbench provider, caller registry, and Baseline ledger; immutable Dev MCP image ID is `sha256:12549a4ad59b224572ee323c2ad7767c01680a6e94f7b7febcd2cd8c1ad4e334` | Passed |
| Active gateway launcher safety | Active launchers derive their roots/interpreters and default to explicit `:8721`; stale `ComfyGatewayBoot` was disabled without deletion and its exact retired-checkout process stopped | Passed; HEARTH unchanged on `8710` |
| Historical default-port MCP evidence | Six old Comfy-ledger calls remain quarantined; Baseline ledger now contains successful identity-gated `valheim_mcp_health`, filtered `valheim_server_log_tail`, and `valheim_handshake_trace` events on `8721` | Minimum evidence rerun passed; old receipts retained only as history |
| Clean source/image attribution | Current Workbench runtime pins clean HEAD `1456de1142658e972f9e0462d24b3f3ba143d4ce`, Companion `sha256:b8ef890ee0db59417eb495830b8c2a3a7e79db4e3b82ac6e4b24c02861305d6b`, and Dev MCP `sha256:12549a4ad59b224572ee323c2ad7767c01680a6e94f7b7febcd2cd8c1ad4e334`. The sealed rendered receipt retains its own earlier source/image identity | Passed |
| Rendered AM4 + OMEN + i5 C6 role reversal | Job `job-20260802-003125748-116adca1`, run `workbench-20260802-003128-116adca1`: real clients completed the bounded C6 composition; Derek watched live and recorded `pass / followed / smooth`; cleanup/disarm completed | Passed; sealed reason `human_observation_recorded` |
| Full Lumberjacks solution | Restore/test succeeded with 0 errors; 605 tests passed (126 Contracts / 250 Simulation / 217 Gateway / 12 Companion), with the pre-existing EF dependency-conflict warning | Passed |

## Current safety posture

The active local stack is explicitly in Lab and publishes the identity-attested
Baseline Dev MCP only on loopback `8721`. Host `8720` is free; HEARTH remains
independent on `8710`. The clean machine-acceptance checkpoint is committed and
the C6 machine-plus-human receipt is sealed. The current clean runtime includes
the passed live install-to-rollback receipt, independently gates host processes,
and disables non-reversible legacy rollback. The current player bytes are exact
m31 after the hands-on legacy action; switching back to the C6-accepted m32 DLL
requires a new explicit install authorization. Player-active capture and
unfamiliar-user/mobile review remain classified follow-ons, not hidden passes.
