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

- [ ] 2026-08-12 — **Authorize NuGet publication (no key to handle).** The two
  publish workflows now use Trusted Publishing: the job mints a GitHub OIDC token
  and trades it for a one-hour nuget.org key, so there is no secret to create,
  paste, rotate, or guard. What remains is browser-only, once: sign in at
  nuget.org → username menu → **Trusted Publishing** → add a policy per repo
  (Repository Owner `djcdevelopment`; Repository `comfy-quest` /
  `lumberjacks-platform`; Workflow File `publish-nuget.yml`; Environment blank),
  then set repository variable `NUGET_USER` to the nuget.org profile name (a
  username, not a credential) in each repo. Then tag `nuget-v0.1.0`. The policy is
  per-owner, not per-package, so the three unclaimed IDs are claimed on first push.
  **Correction:** an earlier version of this entry said the fleet "cannot be
  consumed by a stranger" without this. That was wrong — the `.nupkg` files are
  committed to each repo and CI guard G5 proves a clean checkout with an empty
  NuGet cache restores and passes. Publication buys discoverability and lets an
  outside project depend on the contracts without cloning; it does not unblock
  building. (Owner: Derek; source: [SESSION-RETRO-2026-08-12](fieldlab/retro/SESSION-RETRO-2026-08-12.md))
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
