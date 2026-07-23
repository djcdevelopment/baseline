# Milestone plans — builder-agent briefs

Each file is a self-contained brief a builder agent can execute without this
conversation. Naming: `{milestone}-{n}-{feature}.md`. Milestones come from the
strategy roadmap (M1 Trust & Rhythm → M6 Projection); unlocks compound downhill,
so within a milestone, lower `n` generally blocks higher `n`.

Shared context every builder should know:

- **Repo layout:** `network/` (netcode docs, mod `ComfyNetworkSense`, gateway MCP
  in `network/mcp`), `Lumberjacks/` (net9 services — build in the `sdk:9.0`
  container), `fieldlab/`, `docs/`, `infra/`, `tools/`, `data/`, `recipes/`.
  The mod is net48 — build with host dotnet 8; guard `PluginOutputPath`.
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
