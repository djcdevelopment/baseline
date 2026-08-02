# Milestone plans — builder-agent briefs

## Active product build strategy

Current build boundary: the mod targets net48 and the Docker Workbench image
is its canonical/historical build workaround. It mounts Valheim read-only,
disables plugin copying, and retains a hashable artifact receipt; host SDK
MSB3644 is an expected boundary.

- [`workbench-v1-saga-strategy.md`](workbench-v1-saga-strategy.md) — the
  decision-complete, single-session Saga/Epic/Feature/Story strategy for the
  ownable Docker Workbench v1.
- [`workbench-v1-implementation-receipt.md`](workbench-v1-implementation-receipt.md) —
  execution evidence, implemented surfaces, and the remaining operator gate.
- [`workbench-v1-verification-matrix.md`](workbench-v1-verification-matrix.md) —
  requirement-by-requirement evidence status, including intentional pending gates.
- [`workbench-v1-checkpoint-scope.md`](workbench-v1-checkpoint-scope.md) —
  reviewed file scope and safe staging/roadmap handoff for the eventual checkpoint.
- [`../docs/audit/2026-08-01-mcp-endpoint-provenance-audit.md`](../docs/audit/2026-08-01-mcp-endpoint-provenance-audit.md) —
  the read-only endpoint/process/task/ledger audit that gates MCP-sensitive work.

Each file is a self-contained brief a builder agent can execute without this
conversation. Naming: `{milestone}-{n}-{feature}.md`. Milestones come from the
strategy roadmap (M1 Trust & Rhythm → M6 Projection); unlocks compound downhill,
so within a milestone, lower `n` generally blocks higher `n`.

Shared context every builder should know:

- **Execution control:** `full-roadmap-working-strategy.md` controls sequencing,
  and `remaining-human-tests.md` lists the human-only gates that agents must
  prepare around instead of rediscovering from chat history.
- **Repo layout:** `network/` (netcode docs, mod `ComfyNetworkSense`, gateway MCP
  in `network/mcp`), `Lumberjacks/` (net9 services — build in the `sdk:9.0`
  container), `fieldlab/`, `docs/`, `infra/`, `tools/`, `data/`, `recipes/`.
  The mod is net48 — the Docker Workbench image is the canonical and
  historical build workaround; mount Valheim read-only, disable plugin copy,
  and retain the artifact receipt. Host SDK MSB3644 is an expected boundary.
- **Strategy docs** (retired checkout, read-only reference):
  `C:\work\comfy\docs\adoption-strategy.md`, `positioning.md`, `governance.md`.
  The voice rules live there: never a verdict on the past; "cheaper to care";
  owner-controlled, opt-in, not surveillance.
- **Design language for netcode:** `network/telemetry-and-scores.md` (equations,
  weights, normalization) and `network/observability-and-experiments.md`
  (experiment protocols). Scores advise before they control.
- **Deployment:** P7 releases are immutable artifact promotions from this
  baseline checkout: build/verify locally, promote the pinned Gateway image to
  P7, deploy the matching server DLL, publish the client-pull package pointer,
  then install through Companion on OMEN and i5. Do not rebuild source on P7 or
  ship changed DLL bytes under an existing release id.
- **Capture is client-side:** kill/combat telemetry runs on the player's client;
  the server cannot see client-owned creatures.

| Milestone | Files |
|---|---|
| M1 Trust & Rhythm | m1-1-data-trust-note, m1-2-alpha-expectations-and-status, m1-3-weekly-rhythm-templates, m1-4-stream-ops-hygiene |
| M2 Legible Tuning | m2-1-tuning-ledger, m2-2-decision-provenance, m2-3-gm-interview-guide |
| M3 Replay & Workbooks | m3-1-replay-notebook, m3-2-tradeoff-cards, m3-3-vod-chaptering, m3-4-runnable-proofs |
| M4 Turnkey Lab | m4-1-inventory-and-gap, m4-2-compose-stack, m4-3-lab-mode-keys, m4-4-localhost-demo |
| M5 Community Scale | m5-1-support-runbook, m5-2-quest-contribution-pipeline, m5-3-gm-driven-integration, m5-4-beachhead-map |
| M6 Projection | m6-1-node-shape-contract, m6-2-signing-hardening, m6-3-peering-pilot |
