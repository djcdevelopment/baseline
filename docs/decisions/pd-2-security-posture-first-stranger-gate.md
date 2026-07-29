# PD-2 — Security posture & the First Stranger gate

Status: adopted 2026-07-29 (Derek). Canonical *why* for the current security posture
and the single named trigger that ends it.

## The gate, defined once

> **First Stranger: the first time a participant who is not the operator or a
> name-known friend is expected to interact with a live surface** — joining the game
> world, enrolling via `/join`, posting in the forum as an unknown, or submitting a
> substantial external PR.

Before this document, the same condition existed in several places under different
wordings ("a real external cohort", "before a real cohort window", "first substantial
external PR"). Divergent wordings of one condition is how trigger drift happens; every
doc now references the gate by name and links here.

## The pre-gate posture (decided 2026-07-29)

**Accept open direct-join with no server password** while the cohort is the operator's
own accounts plus name-known friends.

Why this is honest rather than lax:

- Everyone in the cohort is known by name; downtime or exposure coordination is a ping,
  not a product commitment.
- Nothing is joinable today regardless — the P7 VM has been stopped since 2026-07-25,
  and the local lane runs the Gateway only, no game server.
- IP redaction would be theater: the public DNS name resolves it. The ~7 public docs
  describing the server as Steam-unlisted but password-free are accurate as written,
  and stating the truth beats decorating it.

## Due at the gate

When First Stranger fires, these stop being optional (each is deliberately deferred
today, not forgotten):

- **Server password**, baked into the personalized zip by the invite flow.
- **Rate limiting on the steam-join/enroll path** (none exists today; the runbook says
  so truthfully).
- **Contributor agreement given a real review** — the instrument shipped 2026-07-29
  ([`CLA.md`](../../CLA.md), agent-drafted under delegation; see PD-1); the gate adds
  a counsel pass if contribution volume warrants it.
- **Moderation / code-of-conduct posture** for the forum.
- **Telemetry retention & deletion posture** beyond the aggregates-only v0 API.
- **Security disclosure SLA re-checked** — [`SECURITY.md`](../../SECURITY.md) is live
  (GitHub private vulnerability reporting, enabled 2026-07-29, plus the tagged
  mailbox); the gate re-validates the solo-maintainer response promise against real
  traffic.
- **Prod backup cadence re-armed** (cost runbook lever E's re-arm rule).
- **Duty-cycle courtesy upgraded** from "ping the friends" to real service hours
  (cost runbook lever C's "loud version" warning).

## Revisit triggers

- The gate itself is the revisit trigger for everything above.
- If the gate fires partially (e.g. a stranger PR arrives while the world stays
  friends-only), apply the due-list per surface, not all-or-nothing.
