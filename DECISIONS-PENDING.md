# Decisions pending — active queue

This register contains only unresolved choices that require operator judgment.
Execution belongs in runbooks, sequencing in plans, blocked work in backlogs, and
durable rationale in [`docs/decisions/`](docs/decisions/README.md).

Admission requires two currently viable alternatives with materially different
consequences, a decision owner, and a named deadline or trigger. If an existing
policy already determines the answer, it is not an open decision.

## Open

None.

## Resolved

- [x] 2026-08-02 — **Local Lab runtime provenance and canonical session boundary** — resolved by the full Baseline state-root migration; canonical-session diagnostic execution remains in the Saga, not this decision queue. See [PD-7](docs/decisions/pd-7-lab-runtime-provenance-and-session-boundary.md).

- [x] 2026-08-01 — **Legacy ComfyGatewayBoot disposition and Baseline Dev MCP port** — resolved by retiring the stale logon task and reserving explicit Dev/Lab port `8721`; the post-split canonical Isolate endpoint is recorded by [PD-6](docs/decisions/pd-6-development-mcp-lifecycle.md) and [PD-8](docs/decisions/pd-8-isolated-runtime-and-toolset-repository.md).

- [x] 2026-07-31 — **Lumberjacks RPC Admission Gaps** — resolved per-RPC by the
  [C8 breadth audit](fieldlab/C8-BREADTH-AUDIT-2026-07-31.md): the true surface is
  160 RPCs (extractor v2 found the 120 instance RPCs the gap analysis missed);
  21 superseded by design, 129 admitted-to-lane before C10 (29 P1), 9 deferred
  behind the poison tripwire. Any single row can be reopened without reopening
  the audit. (Owner: Derek)

- [ ] 2026-08-12 — **Reserve the three NuGet identifiers and issue a push key.**
  `Comfy.Quest.Contracts`, `Comfy.Transport.Contracts`, `Comfy.Quest.Studio` are
  unclaimed (404s confirm availability); the first push claims each. Add
  `NUGET_API_KEY` to `comfy-quest` and `lumberjacks-platform` only —
  `networksense` publishes GitHub Releases and needs no key. Until then the fleet
  builds from vendored local feeds and cannot be consumed by a stranger.
  (Owner: Derek; source: [SESSION-RETRO-2026-08-12](fieldlab/retro/SESSION-RETRO-2026-08-12.md))
- [ ] 2026-08-12 — **Confirm or rename `lumberjacks-platform`.** Chosen as a
  default because `djcdevelopment/Lumberjacks` is the retired public archive.
  Renaming is cheap now and gets expensive once packages and releases pin it.
  (Owner: Derek; source: [PD-9](docs/decisions/pd-9-repository-split.md))
- [ ] 2026-08-12 — **Decide whether the Steam account handles stay published.**
  `Durracktu`, `wary.fool`, and `floooooobcakes` appear in the platform's M1 plan
  and multiplayer setup doc, and in baseline's own `AGENTS.md`. Read as a
  deliberate choice and left alone; the SteamID64 beside them was redacted.
  (Owner: Derek; source: [SESSION-RETRO-2026-08-12](fieldlab/retro/SESSION-RETRO-2026-08-12.md))
- [x] 2026-08-12 — **Repository topology** — resolved as five sovereign repos with
  Baseline as the hub, per [PD-9](docs/decisions/pd-9-repository-split.md).
  (Owner: Derek)
