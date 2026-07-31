# Decisions pending — active queue

This register contains only unresolved choices that require operator judgment.
Execution belongs in runbooks, sequencing in plans, blocked work in backlogs, and
durable rationale in [`docs/decisions/`](docs/decisions/README.md).

Admission requires two currently viable alternatives with materially different
consequences, a decision owner, and a named deadline or trigger. If an existing
policy already determines the answer, it is not an open decision.

## Open

_None._

## Resolved

- [x] 2026-07-31 — **Lumberjacks RPC Admission Gaps** — resolved per-RPC by the
  [C8 breadth audit](fieldlab/C8-BREADTH-AUDIT-2026-07-31.md): the true surface is
  160 RPCs (extractor v2 found the 120 instance RPCs the gap analysis missed);
  21 superseded by design, 129 admitted-to-lane before C10 (29 P1), 9 deferred
  behind the poison tripwire. Any single row can be reopened without reopening
  the audit. (Owner: Derek)
