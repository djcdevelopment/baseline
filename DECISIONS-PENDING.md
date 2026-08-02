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

- [x] 2026-08-01 — **Legacy ComfyGatewayBoot disposition and Baseline Dev MCP port** — resolved by retiring the stale logon task and reserving explicit Dev/Lab port `8721`; see [PD-6](docs/decisions/pd-6-development-mcp-lifecycle.md).

- [x] 2026-07-31 — **Lumberjacks RPC Admission Gaps** — resolved per-RPC by the
  [C8 breadth audit](fieldlab/C8-BREADTH-AUDIT-2026-07-31.md): the true surface is
  160 RPCs (extractor v2 found the 120 instance RPCs the gap analysis missed);
  21 superseded by design, 129 admitted-to-lane before C10 (29 P1), 9 deferred
  behind the poison tripwire. Any single row can be reopened without reopening
  the audit. (Owner: Derek)
