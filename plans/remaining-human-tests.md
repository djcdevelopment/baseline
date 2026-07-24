# Remaining Human Test Register

Status: active  
Last reviewed: 2026-07-24  
Controlling strategy: `plans/full-roadmap-working-strategy.md`

This register exists to keep Derek out of file-transfer, deployment, log-gathering,
and command-running loops. Agents should do every machine-verifiable preflight first,
then ask for only the specific human observation or external relationship that cannot
be derived from receipts.

## Current immediate gate

| ID | Scope | Human action | Agent-owned prep | Evidence that closes it |
|---|---|---|---|---|
| H0-1 | Wave 0 two-client join | Join OMEN and i5 to P7 with the two owned player accounts. | Keep P7, OMEN, and i5 aligned; run `tools\wave0\Test-Wave0Prelive.ps1`; wait with `tools\wave0\Wait-Wave0LiveGate.ps1`. | P7 peer count reaches at least 2 in the live-gate receipt. |
| H0-2 | Wave 0 first direction | Watch both screens during the bounded OMEN-apply/i5-observe movement. | Set role split, start capture, send bounded motion, write immutable receipt and observation worksheet. | `Add-Wave0VisualObservation.ps1` sidecar records visual result and movement quality. |
| H0-3 | Wave 0 role reversal | Watch both screens during the bounded i5-apply/OMEN-observe movement. | Repeat live gate with `-DesiredApplyClient i5`. | Second annotated receipt shows the result follows role selection, not machine/account identity. |
| H0-4 | Wave 0 subjective quality | Classify straight and stutter movement as smooth, glidey, teleporting, mixed, or not observed. | Capture transport and local telemetry bundles from both machines. | `Seal-Wave0VisualEvidence.ps1` produces a sealed visual index, or `Suggest-Wave0DefectPacket.ps1` produces a named defect path. |

If any H0 item fails or remains inconclusive, do not advance into Wave 1. Retain a
named Wave 0 defect packet instead.

## Later human gates by wave

| ID | Wave | Human action | Why it cannot be fully mocked | Agent-owned prep before asking |
|---|---:|---|---|---|
| H1-1 | 1 | Complete a clean Windows tester onboarding path using Steam/OpenID and Companion. | Steam consent, browser trust prompts, anti-download warnings, and user confidence are real UX/security behavior. | Publish immutable package, verify bootstrap manifest, run install/rollback/uninstall smoke with local fixtures, ensure no secrets are exposed in UI/logs. |
| H1-2 | 1 | Confirm admission denial messages are actionable for expired, revoked, incompatible, or full-capacity states. | The important output is whether the tester understands what happened without operator translation. | Generate all denial fixtures, test fail-closed behavior, verify capability split and trusted-proxy handling in automated tests. |
| H2-1 | 2 | Judge whether decision traces explain a real dropped/deferred/prioritized event well enough to debug from the dashboard. | Human comprehension of a trace is not captured by schema validation. | Produce synthetic drop/defer/reprioritize receipts, validate append-only JSONL schema, and link every dashboard row to source event IDs. |
| H3-1 | 3 | Run dense-zone sustained movement with two real clients. | Native Valheim rendering, ownership, smoothing, and player perception are client-side and visual. | Pass N=2 synthetic recipient isolation, capture client/server telemetry, and predeclare quality/latency limits. |
| H3-2 | 3 | Run stutter-step movement with two real clients. | The artifact is perceptual and depends on actual Valheim input/render timing. | Same as H3-1, plus isolate straight-vs-stutter pattern receipts. |
| H3-3 | 3 | Force WebSocket fallback and judge whether play remains understandable. | Network degradation acceptability is subjective and player-facing. | Prove UDP/WebSocket switch telemetry, collect before/after captures, and provide rollback switch. |
| H3-4 | 3 | Disconnect/rejoin, Gateway restart, server restart/save-load canary. | Real Steam session recovery and Valheim world continuity must be observed on real clients. | Mock reconnect/takeover/WAL replay first; snapshot world and publish rollback path. |
| H3-5 | 3 | One trusted non-developer external canary. | External trust, installation friction, Discord/social support, and survey quality cannot be simulated locally. | Complete Companion-only package, redacted diagnostics, participation receipt, uninstall path, and support runbook. |
| H4-1 | 4 | Decide whether replay/tuning tradeoff cards match the observed quality issues. | Tuning is a product judgment after seeing live defects. | Build offline replay over sealed packets and generate one card per tuning knob. |
| H4-2 | 4 | Validate a clean-machine local lab story. | "Turnkey" means an actual new environment can follow it without prior repo memory. | Provide Compose stack, lab-only generated keys, and automated local Gateway/dashboard proof. |
| H4-3 | 4 | GM/developer contribution dry run. | The contribution workflow depends on another builder's mental model. | Prepare signed quest pipeline, smoke tests, templates, and diagnostics-first support path. |
| H4-4 | 4 | 2-4 player and then 5-8 player invited soak. | Synthetic clients qualify code paths but do not prove social/player capacity or subjective quality. | Predeclare resource limits, run synthetic N=10, verify dashboards, capture per-participant receipts. |
| H4-5 | 4 | Accept or reject the first peer-node aggregate UX. | Cross-node trust labels and stale/tampered data warnings need operator/product judgment. | Implement signed read-only aggregate exchange, fail-closed validation, and tamper/stale fixtures. |

## Agent rules before requesting human time

1. Run the latest relevant unattended gate and keep the receipt path.
2. Verify release/package identities on P7, OMEN, and i5 when the test touches Valheim.
3. Confirm rollback or stop path exists before movement, restart, or install tests.
4. Produce an expected-result grid before the human action starts.
5. Ask for one observation at a time, using allowed values where possible.
6. Convert the observation into an append-only sidecar or named defect packet immediately.

## Current "when Derek returns" packet

Use:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Test-Wave0Prelive.ps1 -OutputDirectory captures\wave0-prelive-current
```

Then follow the generated return packet:

```text
captures\wave0-prelive-current\return-packet\packet.md
```

