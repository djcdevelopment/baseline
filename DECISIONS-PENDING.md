# Decisions pending — active queue

This register contains only unresolved choices that require operator judgment.
Execution belongs in runbooks, sequencing in plans, blocked work in backlogs, and
durable rationale in [`docs/decisions/`](docs/decisions/README.md).

Admission requires two currently viable alternatives with materially different
consequences, a decision owner, and a named deadline or trigger. If an existing
policy already determines the answer, it is not an open decision.

## Open

- **Lumberjacks RPC Admission Gaps**: The synthetic baseline gap analysis identified 18 missing `RoutedRPCs` and 21 missing `DirectRPCs` (bypassing Lumberjacks admission control). 
  - *Alternatives*: (1) Whitelist them in `MessageRouter.cs` and pipe them through `ComfyNetworkSense` (incurs more dev effort but full coverage). (2) Continue ignoring them if they are non-critical to ZDO and gameplay telemetry.
  - *Deadline/Trigger*: Evaluate before the next C8 protocol freeze.
  - *Owner*: Derek
